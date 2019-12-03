from os.path import join, curdir, dirname, splitext, basename, isdir, realpath, normpath, exists, splitext
from os import makedirs, listdir, rename
import importlib
import json
from logging import debug, info, warning, error

from shutil import copyfile, copytree, rmtree
import sys
from distutils.dir_util import copy_tree

from shutil import make_archive, move, copy, make_archive

import logging

from .configure import read_configuration

_log = logging.getLogger(__name__)


class PathDefintions:
    def __init__(self, base_dir: str, outdir: str, archive_name: str, script_name: str, class_name: str):
        self.base_dir = base_dir
        self.archieve_name = archive_name
        self.archive_path = join(base_dir, outdir, archive_name)
        self.archive_zipped_path = self.archive_path
        self.binaries_src = join(base_dir, "resources", "wrapper", "binaries")
        self.binaries_dst = join(self.archive_path, "binaries")
        self.modelDescription_path = join(
            self.archive_path, 'modelDescription.xml')

        self.resources_dst = join(self.archive_path, "resources")
        self.sources_dst = join(self.archive_path, "source")
        self.sources_src = join(base_dir, "source")

        self.script_name = script_name
        self.script_path = join(self.sources_src, script_name)
        self.class_name = class_name


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


def extract_model_description_from_script(pd: PathDefintions):

    module_name = splitext(pd.script_name)[0]

    module = import_by_source(module_name, pd.script_path)

    fmu_ctor = getattr(module, pd.class_name)

    fmu = fmu_ctor()

    model_description = fmu.__define__()

    return model_description


def create_export_folders(pd: PathDefintions) -> None:

    makedirs(pd.binaries_dst, exist_ok=True)
    makedirs(pd.resources_dst, exist_ok=True)
    makedirs(pd.sources_dst, exist_ok=True)


def copy_binaries_to_archive(pd: PathDefintions) -> None:

    copy_tree(pd.binaries_src, pd.binaries_dst)


def copy_resources_to_archive(pd: PathDefintions) -> None:

    pass


def copy_sources_to_archive(pd: PathDefintions) -> None:
    copy_tree(pd.sources_src, pd.sources_dst)


def generate_classname_hint_for_library(pd: PathDefintions) -> None:
    """Generates a small configuration file in which defines what python class will be instantiated by the shared library.
    """
    txtPath = join(pd.sources_dst, "slavemodule.txt")

    with open(txtPath, 'w') as f:
        f.write(pd.class_name)


def write_model_description_to_archive(pd: PathDefintions, model_description: str) -> None:

    with open(pd.modelDescription_path, 'w') as f:
        f.write(model_description)


def zip_archive(pd: PathDefintions) -> None:

    make_archive(pd.archive_zipped_path, 'zip', pd.archive_path)

    outOld = pd.archive_path + ".zip"
    outNew = pd.archive_path + ".fmu"

    move(outOld, outNew)


_exists_ok = True


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


def _copy_source_files_to_archive(project_dir, builder_resources_dir, archive_dir):

    # copy binaries / python wrapper into archive
    builder_binaries_dir = join(builder_resources_dir, "wrapper", "binaries")
    archive_binaries_dir = join(archive_dir, "binaries")
    copytree(builder_binaries_dir, archive_binaries_dir)

    # copy source files into archive
    project_resources_dir = join(project_dir, "resources")
    archive_resources_dir = join(archive_dir, "resources")
    copytree(project_resources_dir, archive_resources_dir)


def _compress(archive_path: str):
    extension = "zip"
    make_archive(archive_path, 'zip', archive_path)
    rename(f"{archive_path}.{extension}", f"{archive_path}.fmu")


def _generate_model_description(main_script_path: str, main_class: str) -> str:
    

    module = import_by_source(main_script_path)

    main_class_ctor = getattr(module, main_class)
    
    if(main_class_ctor is None or not callable(main_class_ctor)):
        raise RuntimeError(f"Failed to generate model description. The specified file {main_script_path} does not define any callable attribute named {main_class}.")

    try:
        main_class_instance = main_class_ctor()
    except:
        raise RuntimeError("Failed generating model description, The construtor of the main class threw an exception. Ensure that the script defines a parameterless constructor")
    

    if(hasattr(main_class_instance,'__define__')):
        raise RuntimeError(f"Failed generating model description. The main class {main_class} does not define a method named property __define__()")
    
    try:
        md = main_class_instance.__define__()
    except:
        raise RuntimeError(f"Failed generating model description. The call to __define__() of the main class raised an exception")
    

    return md


def _validate_model_description(md: str) -> bool:
    return True


def export_project(working_dir: str, project_path: str, archive_path: str, compress: bool = False, overwrite=True, store_uncompressed=True, store_compressed=True):

    if(not overwrite and exists(archive_path)):
        raise FileExistsError(
            "Failed to export project. The a file or directory with a path identical to the output already exists. If you wish to overwrite this file or folder please specifiy the --overwrite flag")
    
    
    project_config_path = join(project_path,'project.json')
    project_config = read_configuration(project_config_path)
    main_class = project_config['main_class']
    main_script = project_config['main_script']


    builder_resources_path = join(working_dir, "resources")
    project_main_script_path = join(project_path,"resources",main_script)

    if(overwrite and exists(archive_path)):
        rmtree(archive_path, ignore_errors=True)

    
    _copy_source_files_to_archive(
        project_path, builder_resources_path, archive_path)

    md = _generate_model_description(project_main_script_path, main_class)


    if(store_compressed):
        pass

    if(not store_compressed):
        rmtree(archive_path, ignore_errors=True)

    _log.info(f"Successfully exported {basename(archive_path)}")
