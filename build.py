"""Script for building the C++ code and copying it to the resources
"""
import argparse
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from shutil import copy

from tqdm import tqdm

from tests.utils.example_finder import (
    get_all_examples,
    get_example_directory,
    get_example_project,
)
from pyfmu.builder import export_project
from pyfmu.resources import Resources


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__file__)


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def FMI2_binary_directory_from_hostname() -> str:
    """Returns the name of the binaries subfolder. This can either be:
    win32,win64,linux32,linux64,darwin32,darwin64

    Returns
    -------
    Path
        Path to the FMI2 binaries folder matching the current host
    """
    sys = platform.system()

    # convert to FMI2 system name scheme
    pySys_to_FmiSys = {"Windows": "win", "Linux": "linux", "Darwin": "darwin"}
    sys = pySys_to_FmiSys[sys]

    # arch will be either "32bit" or "64bit"
    arch, _ = platform.architecture()

    # stip bit part away
    arch = arch[:2]

    # merge parts to form: windows64, linux64
    identifier = (sys + arch).lower()
    return identifier


def _get_input_binary_path_for_host() -> Path:
    """Returns the path to the compiled binaries for the host.
    The names of the binaries produced by CMake varies based on whether its an .dll or .so platform.

    Returns:
        Path -- Path to the pyfmu library in the build folder.

    Examples:

    """

    sys = platform.system()

    build_path = Path(__file__).parent.resolve() / "build"

    if sys == "Windows":
        return build_path / "pyfmu.dll"
    elif sys == "Linux":
        return build_path / "pyfmu.so"
    else:
        raise NotImplementedError(f"Not supported for platform {sys}")


def _get_output_binary_path_for_host() -> Path:
    """Returns the path to the subdirectory of the resources used by the pyfmu command line tool.

    The binaries for different platforms are stored in individual folders.
    Note that a FMU is distributed with binaries for all platforms it may run on.
    For example when exporting on windows a wrapper for Windows, Linux and MacOS will be included.

    Returns:
        Path -- Path to the resources folder matching the host

    Examples:

    Windows:
    src/pyfmu/resources/wrapper/win64/pyfmu.dll

    Linux:
    src/pyfmu/resources/wrapper/linux64/pyfmu.so
    """

    sys = platform.system()

    wrapper_dir = Resources.get().binaries_dir
    if sys == "Windows":
        return wrapper_dir / "win64" / "pyfmu.dll"
    elif sys == "Linux":
        return wrapper_dir / "linux64" / "pyfmu.so"
    else:
        raise NotImplementedError(f"Not implmented for {sys}")


def copy_binaries():

    binary_in = _get_input_binary_path_for_host()

    logger.info(f"Looking for compiled binary at path: {binary_in}")

    binary_out = _get_output_binary_path_for_host()

    logger.info("Binaries were found.")

    os.makedirs(binary_out.parent, exist_ok=True)

    if binary_out.is_file():
        os.remove(binary_out)

    copy(binary_in, binary_out)


def build(debug_build: bool):
    """ Builds project using CMake.

    The approach is as follows:
    1. if no build folder exists create this.
    2. change directory into build folder.
    3. do cmake configure inside this folder
    4. do cmake build inside this folder.
    """

    p = platform.system()

    build_dir = Path(__file__).parent / "build"
    logger.log(logging.DEBUG, f"Preparing build to folder {build_dir}")

    # Create build folder and configure CMake
    if not build_dir.is_dir():

        logger.log(logging.DEBUG, "Build folder does not exists, creating")

        try:
            os.makedirs(build_dir)

        except Exception as e:
            raise RuntimeError("Failed to create build folder") from e

    # Do the following:
    # 1. cd into build
    # 2. configure cmake
    # 3. build
    # 4. cd back to original folder
    with cd(build_dir):
        # Cmake configure

        # see https://cmake.org/cmake/help/v3.17/variable/CMAKE_BUILD_TYPE.html
        # https://cmake.org/cmake/help/v3.17/variable/CMAKE_CONFIGURATION_TYPES.html
        if debug_build:
            cmake_configure_type_arg = "-DCMAKE_BUILD_TYPE=DEBUG"
            cmake_build_type_arg = "debug"
        else:
            cmake_configure_type_arg = "-DCMAKE_BUILD_TYPE=RELEASE"
            cmake_build_type_arg = "release"

        try:
            res = subprocess.run(["cmake", "..", cmake_configure_type_arg])

            if res.returncode != 0:
                raise RuntimeError(
                    "CMake configure was called, but returned error code different than 0."
                )

        except Exception as e:
            raise RuntimeError(f"Calling CMake configure failed.") from e

        # CMake build
        try:
            logger.log(logging.DEBUG, "Building project")

            if p == "Windows":
                res = subprocess.run(
                    ["cmake", "--build", ".", "--config", cmake_build_type_arg]
                )
            else:
                res = subprocess.run(["cmake", "--build", "."])

            if res.returncode != 0:
                raise RuntimeError(
                    "CMake build was called, but returned error code different than 0."
                )

        except Exception as e:
            raise RuntimeError(
                "Failed to build CMake project, exception was thrown"
            ) from e


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Script to ease the process of build the wrapper and updating the resources of PyFMU"
    )

    parser.add_argument(
        "--update_wrapper",
        "-u",
        action="store_true",
        help="Overwrite the existing wrapper library with the newly built one.",
    )

    parser.add_argument(
        "--export_examples",
        "-e",
        action="store_true",
        help="Exports all example projects as FMUs with the built wrapper.",
    )

    parser.add_argument(
        "--debug-build",
        "-d",
        action="store_true",
        dest="debug_build",
        help="Builds PyFMU as a debug build.",
    )

    args = parser.parse_args()

    logger.log(logging.DEBUG, "Building project.")
    try:
        build(debug_build=args.debug_build)
    except Exception as e:
        logger.log(
            logging.ERROR, f"Failed building PyFMU, an exception was thrown:\n{e}"
        )
        sys.exit(-1)

    logger.info("Succesfully build project.")

    should_update_wrapper = args.update_wrapper or args.export_examples

    if should_update_wrapper:

        binary_in = _get_input_binary_path_for_host()
        binary_out = _get_output_binary_path_for_host()

        logger.info(
            f"Copying binaries from build folder {binary_in} to resource folder {binary_out}"
        )

        os.makedirs(binary_out.parent, exist_ok=True)

        if binary_out.is_file():
            os.remove(binary_out)

        copy(binary_in, binary_out)

        logger.info(f"Binaries were sucessfully copied to resources {binary_out}.")

    if args.export_examples:

        logger.info(f"Exporting examples {get_all_examples()}")

        for name in tqdm(get_all_examples(), desc="exported"):

            project = get_example_project(name)

            export_project(
                project_or_path=project,
                output_path=get_example_directory() / "exported" / name,
                compress=False,
            )
