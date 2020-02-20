from os.path import join, curdir, dirname, splitext, basename, isdir, realpath, normpath, exists, splitext, relpath
from os import makedirs, listdir, rename
import importlib
import json
from logging import debug, info, warning, error

from shutil import copyfile, copytree, rmtree, make_archive, move, copy
import sys
from distutils.dir_util import copy_tree
from pathlib import Path

import logging

from .configure import read_configuration
from .modelDescription import extract_model_description_v2
from .utils import builder_basepath


_log = logging.getLogger(__name__)

_exists_ok = True

def _resources_path() -> Path:
    """Returns the path the the resource folder. 
    
    This is expected to be placed relative to this file ../../resources
    
    Returns:
        Path -- path to the resources folder
    """
    return Path(__file__).parent.parent.parent / 'resources'

class PyfmuProject():
    """Object representing an pyfmu project.
    """
    
    def __init__(self, root : Path, main_script : str, main_class : str):

        self.root = root
        self.main_script = main_script
        self.main_class = main_class

    @staticmethod
    def from_existing(p : Path):
        """Instantiates an object representation based on an existing project
        
        Arguments:
            p {Path} -- path to the root of the project
        """
        p = Path(p)

        # Verify that path points to a valid pyfmu project.

        # 1. Should be directory        
        if(not Path.is_dir):
            raise ValueError('Specified path does not point to a directory, ensure that the path is correct.')
        
        # 2. Should contain a 'project.json' in the root
        has_project_json = (p / 'project.json').is_file()

        if(not has_project_json):
            raise ValueError('The directory does not contain a "project.json" file.')

        with open(p/'project.json') as f:
            project_json = json.load(f)

        # 2+ TODO validate using json schema
        main_script = project_json['main_script']
        main_class = project_json['main_class']

        # 3. Should contain resources folder
        has_resources = (p / 'resources').is_dir()

        if(not has_resources):
            raise ValueError('The directory does not contain a resource folder.')
        
        # 4. main script should exist inside resources.
        has_main_script = (p / 'resources' / main_script).is_file()

        if(not has_main_script):
            raise ValueError(f'The main python script: {main_script} could not be found in the resources folder. Ensure that the "project.json" defines the correct script.')

        # 5. TODO main class should be defined by main script


        project = PyfmuProject(p,main_script=main_script,main_class=main_class)

        return project

    @property
    def main_script_path(self):
        if(self.main_script == None):
            return None
        
        else:
            return self.root / 'resources' / self.main_script

class PyfmuArchive():
    """Object representation of exported Python FMU.
    """

    def __init__(self, root : Path, model_description : str):
        """Creates an object representation of the exported Python FMU.
        
        Arguments:
            model_description {str} -- The model description of the exported FMU.
        """
        self.model_description = model_description
        self.root = root

def import_by_source(path: str):
    """Loads a python module using its name and the path to the python source script.

    Arguments:
        path {str} -- path to the module

    Returns:
        module -- module loaded from the source file.
    """

    module = splitext(basename(path))[0]

    sys.path.append(dirname(path))

    spec = importlib.util.spec_from_file_location(module, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    sys.path.pop()

    return module

def _available_export_platforms():
    return ["Win64", "Linux64"]

def _create_archive_directories(archive_path, exist_ok=True):

    archive_resources_path = join(archive_path, "resources")

    platforms = _available_export_platforms()

    binary_dirs = [join(archive_path, "binaries", p) for p in platforms]
    binary_dirs = []

    try:
        makedirs(archive_resources_path, exist_ok=exist_ok)

        for d in binary_dirs:
            makedirs(d, exist_ok=exist_ok)

    except Exception as e:
        raise RuntimeError("Failed to create archive directories")

def _resources_to_archive(project_dir, builder_resources_dir, archive_dir):

    # TODO ensure that binaries actually exist

    # copy binaries / python wrapper into archive
    builder_binaries_dir = join(builder_resources_dir, "wrapper", "binaries")
    archive_binaries_dir = join(archive_dir, "binaries")
    copytree(builder_binaries_dir, archive_binaries_dir)

    # copy source files into archive
    project_resources_dir = join(project_dir, "resources")
    archive_resources_dir = join(archive_dir, "resources")
    copytree(project_resources_dir, archive_resources_dir)

def _copy_pyfmu_lib_to_archive(archive : PyfmuArchive, project : PyfmuProject = None):
    """ Copies the Python library into the archive.
    
    If a project is not specified a 'clean' copy from the resources folder is used. 
    Otherwise, if a project is specified the library is copied from this folder instead.
    
    Arguments:
        archive {PyfmuArchive} -- The FMU
    
    Keyword Arguments:
        project {PyfmuProject} -- If specified, the potentially modified pyfmu library instead of one from the resources. (default: {None})
    """
    
    copy_from_resources = project is None

    if(copy_from_resources):        
        lib_path = _resources_path() / 'pyfmu'
        err_msg = 'No directory named pyfmu was found in the resources directory, likely this has been deleted.'

    else:
        lib_path = project.root / 'resources' / 'pyfmu'
        err_msg = "No directory named pyfmu was found in the projects resources. If the intention is to copy the 'local' library, ensure that is is present in the resources folder of the project. Otherwise, to use a clean copy omit specifying the project."

    lib_exists = lib_path.is_dir()

    if(not lib_exists):
            raise RuntimeError(f'Failed to copy the library to the archive. {err_msg}')

    copytree(lib_path, archive.root / 'resources' / 'pyfmu')

def _copy_sources_to_archive(project : PyfmuProject, archive: PyfmuArchive):
    """Copies the source files of the project into the archive.

    Note that that a distinction is made between source files and the pyfmu library. 
    
    In this case source files refer to files written by the developer.

    NOTE: Currently this only copies main script.
    
    Arguments:
        project {PyfmuProject} -- [description]
        archive {PyfmuArchive} -- [description]
    """
    p_msp = project.root /'resources' / project.main_script
    
    main_script_found = p_msp.is_file()

    if(not main_script_found):
        raise RuntimeError(f'main script: {project.main_script} was not found inside project: {project.root}')
    
    a_msp = archive.root /'resources' / project.main_script

    makedirs(a_msp.parent)

    copyfile(p_msp,a_msp)



def _compress(archive_path: str):
    extension = "zip"
    make_archive(archive_path, 'zip', archive_path)
    rename(f"{archive_path}.{extension}", f"{archive_path}.fmu")

def _generate_model_description(main_script_path: str, main_class: str, model_description_path: str) -> str:
    

    instance = _instantiate_main_class(main_script_path,main_class)
    md = extract_model_description_v2(instance)

    with open(model_description_path,'w') as f:
        f.write(md)
    
    return md

def _generate_slave_config(archive_path: str, main_script_path : str, main_class : str):
    """Generates a configuration file which is used by the FMU to locate the specific Python script and class which it must instantiate.
    
    Arguments:
        archive_path {str} -- Path to the root of the archive
        main_script_path {str} -- Path to the main script defined relative to the 'resources' folder.
        main_class {str} -- Name of the main class

    Examples:
        >>_generate_slave_config('somedir/adder','adder.py','Adder')
    """
    

    config_path = join(archive_path,'resources','slave_configuration.json')

    with open(config_path,'w') as f:
        json.dump({
            "main_script" : main_script_path,
            "main_class" : main_class
        },f,indent=4)

def _instantiate_main_class(main_script_path: str, main_class : str):
    module = import_by_source(main_script_path)

    main_class_ctor = getattr(module, main_class)
    
    if(main_class_ctor is None or not callable(main_class_ctor)):
        raise RuntimeError(f"Failed to generate model description. The specified file {main_script_path} does not define any callable attribute named {main_class}.")

    try:
        main_class_instance = main_class_ctor()
    except Exception as e:
        raise RuntimeError(f"Failed generating model description, The construtor of the main class threw an exception. Ensure that the script defines a parameterless constructor. Error message was: {repr(e)}") from e

    return main_class_instance
    
def _validate_model_description(md: str) -> bool:
    return True

def export_project(project_path: str, archive_path: str, compress: bool = False, overwrite=True, store_uncompressed=True, store_compressed=True) -> PyfmuArchive:
    """Exports a pyfmu project as an fmu archive
    
    Arguments:
        project_path {str} -- path to the project
        archive_path {str} -- output path
    
    Keyword Arguments:
        compress {bool} -- Whether or not to compress the archive. (default: {False})
        overwrite {bool} -- Determines if the method is allowed to overwrite an exisiting file (default: {True})
        store_uncompressed {bool} -- [description] (default: {True})
        store_compressed {bool} -- [description] (default: {True})
    
    Raises:
        FileNotFoundError: [description]
        FileExistsError: [description]
    
    Returns:
        PyfmuArchive -- [description]
    """

    if(not isdir(project_path)):
        raise FileNotFoundError("the project path does not correspond to Python FMU project")

    working_dir = builder_basepath()

    if(not overwrite and exists(archive_path)):
        raise FileExistsError(
            "Failed to export project. The a file or directory with a path identical to the output already exists. If you wish to overwrite this file or folder please specifiy the --overwrite flag")
    
    
    archive_model_description_path = join(archive_path,'modelDescription.xml')
    project_config_path = join(project_path,'project.json')
    project_config = read_configuration(project_config_path)
    
    main_class = project_config['main_class']
    main_script = project_config['main_script']



    builder_resources_path = join(working_dir, "resources")
    project_main_script_path = join(project_path,"resources",main_script)

    if(overwrite and exists(archive_path)):
        rmtree(archive_path, ignore_errors=True)

    
    _resources_to_archive(
        project_path, builder_resources_path, archive_path)

    md = _generate_model_description(project_main_script_path, main_class, archive_model_description_path)

    

    _generate_slave_config(archive_path, main_script, main_class)

    _log.info(f"Successfully exported {basename(archive_path)}")

    archive = PyfmuArchive(root = archive_path, model_description = md)

    return archive

