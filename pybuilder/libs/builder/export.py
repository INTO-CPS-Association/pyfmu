from os.path import join, curdir, dirname, splitext, basename, isdir, realpath, normpath, exists, splitext, relpath
from os import makedirs, listdir, rename
import importlib
import json
from logging import debug, info, warning, error
import json

from shutil import copyfile, copytree, rmtree, make_archive, move, copy
import sys
from distutils.dir_util import copy_tree
from pathlib import Path

import logging

from .configure import read_configuration
from .utils import _resources_path
from .modelDescription import extract_model_description_v2
from .utils import builder_basepath
from .validate import validate_project
from .generate import PyfmuProject

_log = logging.getLogger(__name__)

_exists_ok = True






class PyfmuArchive():
    """Object representation of exported Python FMU.
    """

    def __init__(self,
                 root: Path = None,
                 resources_dir: Path =  None,
                 slave_configuration_path : Path = None,
                 binaries_dir : Path = None,
                 main_script_path : Path = None,
                 model_description: Path = None,
                 model_description_path : Path = None,
                 main_script: Path = None,
                 main_class : Path = None,
                 pyfmu_dir : Path = None
    ):
        """Creates an object representation of the exported Python FMU.

        Arguments:
            model_description {str} -- The model description of the exported FMU.
        """
        self.model_description = model_description

        self.main_script = main_script
        self.main_class = main_class
        self.slave_configuration = None

        # paths
        self.root = root
        self.resources_dir = resources_dir
        self.slave_configuration_path = slave_configuration_path
        self.main_script_path = main_script_path
        self.model_description_path = model_description_path
        self.binaries_dir = binaries_dir
        self.pyfmu_dir = pyfmu_dir


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


def _copy_pyfmu_lib_to_archive(archive: PyfmuArchive, project: PyfmuProject = None) -> PyfmuArchive:
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
        raise RuntimeError(
            f'Failed to copy the library to the archive. {err_msg}')

    archive_lib_dir = archive.root / 'resources' / 'pyfmu'

    copytree(lib_path, archive_lib_dir)

    archive.pyfmu_dir = archive_lib_dir

    return archive

def _copy_binaries_to_archive(archive: PyfmuArchive) -> PyfmuArchive:
    
    binaries_path = _resources_path() / 'wrapper' / 'binaries'


    archive_binaries_path = archive.root / 'binaries'


    #makedirs(archive_binaries_path)
    copytree(binaries_path,archive_binaries_path)

    archive.binaries_dir = archive_binaries_path

    return archive

def _copy_sources_to_archive(project: PyfmuProject, archive: PyfmuArchive) -> PyfmuArchive:
    """Copies the source files of the project into the archive.

    Note that that a distinction is made between source files and the pyfmu library. 

    In this case source files refer to files written by the developer.

    NOTE: Currently this only copies main script.

    Arguments:
        project {PyfmuProject} -- [description]
        archive {PyfmuArchive} -- [description]
    """

    main_script_found = project.main_script_path.is_file()

    if(not main_script_found):
        raise RuntimeError(
            f'main script: {project.main_script} was not found inside project: {project.root}')

    archive_main_script_path = archive.root / 'resources' / archive.main_script

    # make directories and copy source files

    if(not archive_main_script_path.parent.is_dir()):
        makedirs(archive_main_script_path.parent)
    
    copyfile(project.main_script_path,archive_main_script_path)

    archive.main_script_path = archive_main_script_path

def _write_modelDescription_to_archive(project : PyfmuProject, archive : PyfmuArchive) -> PyfmuArchive:
    
    instance = _instantiate_main_class(archive.main_script_path, archive.main_class)
    md = extract_model_description_v2(instance)

    archive_model_description_path = archive.root / 'modelDescription.xml'
    
    with open(archive_model_description_path,'w') as f:
        f.write(md)

    archive.model_description = md
    archive.model_description_path = archive_model_description_path

def _write_slaveConfiguration_to_archive(project : PyfmuProject, archive : PyfmuArchive) -> PyfmuArchive:
    
    archive_slave_configuration_path = archive.root / 'resources' / 'slave_configuration.json'

    # currently project and slave configuration contains same info
    slave_configuration  = project.project_configuration

    makedirs(archive_slave_configuration_path.parent)

    with open(archive_slave_configuration_path,'w') as f:
        json.dump(slave_configuration,f)

    archive.slave_configuration_path = archive_slave_configuration_path
    archive.slave_configuration = slave_configuration
    archive.main_class = slave_configuration['main_class']
    archive.main_script = slave_configuration['main_script']

    return PyfmuArchive



def _compress(archive_path: str):
    extension = "zip"
    make_archive(archive_path, 'zip', archive_path)
    rename(f"{archive_path}.{extension}", f"{archive_path}.fmu")

def _generate_model_description(main_script_path: str, main_class: str) -> str:

    instance = _instantiate_main_class(main_script_path, main_class)
    md = extract_model_description_v2(instance)

    return md


def _generate_slave_config(project: PyfmuProject):
    """Generate a slave configuration file for the project

    Note: Currently there is no difference between the project.json and slave_configuration.json files.
    The difference 

    Arguments:
        project {PyfmuProject} -- [description]

    Returns:
        [type] -- Dict
    """
    return project.project_configuration


def _instantiate_main_class(main_script_path: str, main_class: str):
    module = import_by_source(main_script_path)

    main_class_ctor = getattr(module, main_class)

    if(main_class_ctor is None or not callable(main_class_ctor)):
        raise RuntimeError(
            f"Failed to generate model description. The specified file {main_script_path} does not define any callable attribute named {main_class}.")

    try:
        main_class_instance = main_class_ctor()
    except Exception as e:
        raise RuntimeError(
            f"Failed generating model description, The construtor of the main class threw an exception. Ensure that the script defines a parameterless constructor. Error message was: {repr(e)}") from e

    return main_class_instance


def _validate_model_description(md: str) -> bool:
    return True


def export_project(project: PyfmuProject, outputPath: Path, overwrite=False, store_compressed : bool = True) -> PyfmuArchive:

    is_valid_project = validate_project(project)

    if(not is_valid_project):
        raise RuntimeError(
            'The specified project can not be exported due to errors in the project.')

    if(overwrite and exists(outputPath)):
        rmtree(outputPath, ignore_errors=True)

    # create object representation of the project being exported
    # The purpose of this is to encapsulate path related stuff
    archive = PyfmuArchive(
        
        binaries_dir = outputPath / 'binaries',
        model_description_path = outputPath / 'modelDescription.xml',
        root=outputPath,
        resources_dir = outputPath / 'resources',
        slave_configuration_path = outputPath / 'resources' / 'slave_configuration.json'
    )

    # read slave configuration
    _write_slaveConfiguration_to_archive(project,archive)

    # copy source files to archive
    _copy_sources_to_archive(project, archive)
    
    # copy pyfmu lib to archive, a fresh copy from resources is always used.
    _copy_pyfmu_lib_to_archive(archive)

    _copy_binaries_to_archive(archive)

    # generate model description and write
    _write_modelDescription_to_archive(project,archive)


       
    return archive


def export_project_bak(project_path: str, archive_path: str, compress: bool = False, overwrite=True, store_uncompressed=True, store_compressed=True) -> PyfmuArchive:
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
        raise FileNotFoundError(
            "the project path does not correspond to Python FMU project")

    working_dir = builder_basepath()

    if(not overwrite and exists(archive_path)):
        raise FileExistsError(
            "Failed to export project. The a file or directory with a path identical to the output already exists. If you wish to overwrite this file or folder please specifiy the --overwrite flag")

    archive_model_description_path = join(archive_path, 'modelDescription.xml')
    project_config_path = join(project_path, 'project.json')
    project_config = read_configuration(project_config_path)

    main_class = project_config['main_class']
    main_script = project_config['main_script']

    builder_resources_path = join(working_dir, "resources")
    project_main_script_path = join(project_path, "resources", main_script)

    if(overwrite and exists(archive_path)):
        rmtree(archive_path, ignore_errors=True)

    _resources_to_archive(project_path, builder_resources_path, archive_path)

    md = _generate_model_description(
        project_main_script_path, main_class, archive_model_description_path)

    _generate_slave_config(archive_path, main_script, main_class)

    _log.info(f"Successfully exported {basename(archive_path)}")

    archive = PyfmuArchive(root=archive_path, model_description=md)

    return archive
