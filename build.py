"""Script for building the C++ code and copying it to the resources
"""
import subprocess
from pathlib import Path
import os
import logging
import sys
from shutil import copy

from pybuilder.resources.resources import Resources

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
l = logging.getLogger(__file__)


def FMI2_binary_directory_from_hostname() -> Path:
    """Returns the name of the binaries subfolder. This can either be:
    win32,win64,linux32,linux64,darwin32,darwin64

    Returns
    -------
    Path
        Path to the FMI2 binaries folder matching the current host
    """
    sys = platform.system()

    # convert to FMI2 system name scheme
    pySys_to_FmiSys = {
        "Windows": "win",
        "Linux": "linux",
        "Darwin": "darwin"
    }
    sys = pySys_to_FmiSys[sys]

    # arch will be either "32bit" or "64bit"
    arch, _ = platform.architecture()

    # stip bit part away
    arch = arch[:2]

    # merge parts to form: windows64, linux64
    identifier = (sys + arch).lower()
    return identifier


def _getLibraryNameForHost() -> str:
    sys = platform.system()
    if(sys == 'Windows'):
        return 'libpyfmu.dll'
    else:
        raise NotImplementedError()


def copy():

    bin_name = _getLibraryNameForHost()

    binary_path = Path(__file__).parent / 'build' / \
        'bin' / bin_name

    resources_dir = Resources.get().binaries_dir / \
        FMI2_binary_directory_from_hostname() / bin_name

    try:
        os.makedirs(resources_dir, exist_ok=True)
        copy(build_dir, resources_dir)
    except Exception as e:
        raise RuntimeError("Failed to copy binaries into the resources") from e


def build():
    """ Builds project using CMake.

    The approach is as follows:
    1. if no build folder exists create this.
    2. change directory into build folder.
    3. do cmake configure inside this folder
    4. do cmake build inside this folder.
    """

    build_dir = Path(__file__).parent / 'build'
    l.log(logging.DEBUG, f'Preparing build to folder {build_dir}')

    # Create build folder and configure CMake
    if(not build_dir.is_dir()):

        l.log(logging.DEBUG, 'Build folder does not exists, creating')

        try:
            os.makedirs(build_dir)

        except Exception as e:
            raise RuntimeError('Failed to create build folder') from e

    os.chdir(build_dir)

    # Cmake configure
    try:
        res = subprocess.run(['cmake', '..', '-DCMAKE_BUILD_TYPE=RELEASE'])

        if(res.returncode != 0):
            raise RuntimeError(
                'CMake configure was called, but returned error code different than 0.')

    except Exception as e:
        raise RuntimeError(f'Calling CMake configure failed.') from e

    # CMake build
    try:
        l.log(logging.DEBUG, 'Building project')
        res = subprocess.run(
            ['cmake', '--build', '.', '--config', 'Release'], shell=True)

        if(res.returncode != 0):
            raise RuntimeError(
                'CMake build was called, but returned error code different than 0.')

    except Exception as e:
        raise RuntimeError(
            'Failed to build CMake project, exception was thrown') from e


if __name__ == "__main__":

    l.log(logging.DEBUG, 'Building project')
    try:
        build()
    except Exception as e:
        l.log(logging.ERROR,
              'Failed building PyFMU, an exception was thrown:\n{e}')

    l.log(logging.DEBUG, 'Copying build binaries to resource folder')
    try:
        copy()
        test = 10
    except Exception as e:
        l.log(logging.ERROR,
              f'Failed copying the results of the built into the resources directory, an exception was thrown:\n{e}')
