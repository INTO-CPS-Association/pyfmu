import platform
import argparse
import logging
from pathlib import Path
import sys
from shutil import copy

from pybuilder.resources.resources import Resources

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


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Copies the wrapper binary into the resources of the tool depending on the architecture.')
    parser.add_argument('binary_path', type=str)

    args = parser.parse_args()

    p = args.binary_path

    outdir = Resources.get().binaries_dir / FMI2_binary_directory_from_hostname()

    l.log(logging.DEBUG, f'Copying: {args.binary_path} to: {outdir}')

    copy(p, outdir)
