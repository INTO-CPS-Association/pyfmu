from os.path import join, curdir, dirname, splitext, basename, isdir
from os import makedirs, listdir
import importlib
import json
from logging import debug, info, warning, error

from shutil import copyfile
import sys
from distutils.dir_util import copy_tree

from shutil import make_archive, move


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


def import_by_source(module, path):
    """Loads a python module using its name and the path to the python source script.

    Arguments:
        module {str} -- name of the module
        path {str} -- path to the module

    Returns:
        module -- module loaded from the source file.
    """

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


if __name__ == "__main__":

    base_dir = dirname(__file__)

    config_path = join(base_dir, "configuration.json")

    info("Running Python2FMU\n")

    debug(f"Looking for configuration at: {config_path}\n")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except:
        raise RuntimeError(
            f"Failed to locate a configuration file, expected location is: {config_path}\n")

    info(f"Configuration Loaded\n")

    try:
        class_name = config['sources']["class_name"]
        outdir = config['export']['outdir']
        script_name = config['sources']["script"]
        archive_name = config['export']['archive_name']
        class_name = config['sources']['class_name']
    except:
        raise RuntimeError(
            "Configuration file does not declare the necessary values, ensure that configuration file is well formed.\n")

    pd = PathDefintions(base_dir, outdir, archive_name,
                        script_name, class_name)

    model_description = extract_model_description_from_script(pd)
    try:
        model_description = extract_model_description_from_script(pd)
    except:
        raise RuntimeError(
            f"Model description could not be extracted from python script. Ensure that script is valid and class name supplied in the configuration matches the one declared in the python script.\n")

    print("Model description extracted!\n")

    print(model_description)

    create_export_folders(pd)

    write_model_description_to_archive(pd, model_description)

    copy_binaries_to_archive(pd)

    copy_resources_to_archive(pd)

    copy_sources_to_archive(pd)

    generate_classname_hint_for_library(pd)

    zip_archive(pd)

    #delete_nonZipped_archive(outdir, archive_name)
