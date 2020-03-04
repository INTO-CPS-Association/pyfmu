"""Script for building the C++ code and copying it to the resources
"""
import subprocess
from pathlib import Path
import os
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
l = logging.getLogger(__file__)


def FMI2_binary_directory_from_hostname():
    """Returns the name of the binaries subfolder. This can either be:
    win32,win64,linux32,linux64,darwin32,darwin64

    Returns
    -------
    [type]
        [description]
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


def copy():
    pass


def build():

    build_dir = Path(__file__).parent / 'build'
    l.log(logging.DEBUG, f'Preparing build to folder {build_dir}')

    # Create build folder and configure CMake
    if(not build_dir.is_dir()):
        l.log(logging.DEBUG,
              'Build directory does not exist, creating and configuring using CMake')
        try:
            os.makedirs(build_dir)
            subprocess.run(['cmake', '--build', '.', '--config', 'release'])
        except Exception as e:
            l.log(
                logging.ERROR, f'Failed to create and configure cmake build folder at: {build_dir} due to:\n{e}')

    os.chdir(build_dir)

    # Build project
    try:
        return = subprocess.run(['cmake', '..', '-DCMAKE_BUILD_TYPE=RELEASE'])
    except Exception as e:
        pass


if __name__ == "__main__":

    build()
