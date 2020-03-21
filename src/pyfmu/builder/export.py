from distutils.dir_util import copy_tree
from logging import debug, info, warning, error
from os import makedirs, listdir, rename
from os.path import join, curdir, dirname, splitext, basename, isdir, realpath, normpath, exists, splitext, relpath
from pathlib import Path
from shutil import copyfile, copytree, rmtree, make_archive, move, copy
import importlib
import json
import json
import logging
import sys

from pyfmu.builder import read_configuration,extract_model_description_v2,validate_project,PyfmuProject
from pyfmu.resources import Resources

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
                 wrapper_win64 : Path = None,
                 wrapper_linux64: Path = None,
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
        self.wrapper_win64 = wrapper_win64
        self.wrapper_linux64 = wrapper_linux64
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
        
        lib_path = Resources.get().pyfmu_dir
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
    """Copies the binaries to the archive.
    
    Arguments:
        archive {PyfmuArchive} -- The archive being exported
    
    Returns:
        PyfmuArchive -- The archive being exported
    """

    binaries_path = Resources.get().binaries_dir


    archive_binaries_path = archive.root / 'binaries'

    copytree(binaries_path,archive_binaries_path)

    # paths
    archive.binaries_dir = archive_binaries_path
    archive.wrapper_win64 = archive.binaries_dir / 'win64' / 'pyfmu.dll'
    archive.wrapper_linux64 = archive.binaries_dir / 'linux64' / 'pyfmu.so'

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
    """Exports a pyfmu project as an FMU to the specified output path.
    
    Arguments:
        project {PyfmuProject} -- A PyfmuProject or the path to a project. 
        outputPath {Path} -- The path to which the FMU is exported.
    
    Keyword Arguments:
        store_compressed {bool} -- compress the exported FMU (default: {True})
    
    Raises:
        RuntimeError: [description]
    
    Returns:
        PyfmuArchive -- An object representing the exported FMU.
    

    """
    isProject = isinstance(project, PyfmuProject)
    if(not isProject):

        try:
            project = PyfmuProject.from_existing(Path(project))
        except Exception as e:
            raise ValueError('Could not load the specified project. The path project argument appears to be neither a project or the path to a project') from e
        
    try:
        outputPath = Path(outputPath)
    except Exception as e:
        raise(ValueError('The output path does not appear to be a valid path, please ensure that it is correct.'))

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

    _copy_binaries_to_archive(archive)

    # generate model description and write
    _write_modelDescription_to_archive(project,archive)


       
    return archive

