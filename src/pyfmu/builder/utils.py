"""Contains utility functions used throughout the library"""

import os
import platform
import subprocess
from os.path import basename, dirname, isdir, join
from pathlib import Path
from shutil import make_archive, move, rmtree
from tempfile import mkdtemp
from zipfile import ZIP_DEFLATED, ZipFile

from pyfmu.types import AnyPath


def zipdir(inDir: str, outDir: str):

    if not isdir(inDir):
        raise ValueError("Input path does not correspond to a directory!")

    with ZipFile(outDir, "w", ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(inDir):
            for file in files:
                p = os.path.relpath(os.path.join(root, file), os.path.join(inDir, ".."))
                zf.write(p)


def rm(path):
    """Delete a file or a directory

    Arguments:
        p {Path} -- path to a directory or a file
    """

    if platform.system() == "Windows":
        print("TODO FIX RM ON WINDOWS!")
        return

    try:
        path = Path(path)

        if path.is_dir():
            rmtree(path)
        elif path.is_file():
            path.unlink()
        else:
            raise ValueError("path neither specifies a file nor a directory.")

    except Exception as e:
        raise RuntimeError(
            f"Unable to remove file/directory: {path} and error was raised: {e}"
        )


def compress(
    input_directory: AnyPath,
    output_directory: AnyPath = None,
    format="zip",
    extension: str = None,
) -> Path:
    """Compress files within a directory to the specified output directory.

    Examples:

     >>> compress("mydir") # mydir.zip
     >>> compress("mydir","archive") # archive.zip
     >>> compress("mydir","archive.zip") # archive.zip.zip
     >>> compress("mydir","myfmu",extension="fmu") # myfmu.fmu

    Arguments:
        input_directory {AnyPath} -- directory containing files to compress

    Keyword Arguments:
        output_directory {AnyPath} -- output directory. (default: {None})
        format {str} -- compression type used to create the archive (default: {"zip"})
        extension {str} -- if specified replace the default extension (default: {None})

    Returns:
        Path -- path to the archive
    """

    try:
        input_directory = Path(input_directory)

        if not input_directory.is_dir():
            raise ValueError(
                f"input directory: {input_directory} does not appear to be a directory"
            )

        if output_directory is None:
            output_directory = input_directory
        else:
            output_directory = Path(output_directory)

        root_dir = input_directory
        base_dir = input_directory
        base_name = str(output_directory)

        archive_path = Path(
            make_archive(
                base_name=base_name, base_dir=base_dir, format=format, root_dir=root_dir
            )
        )
        assert archive_path.is_file()

        if extension is not None:
            renamed_name = f"{archive_path.stem}.{extension}"
            renamed_archive = archive_path.parent / renamed_name

            assert not renamed_archive.exists()
            move(str(archive_path), renamed_archive)
            assert not output_directory.exists()
            assert renamed_archive.exists()

            return renamed_archive

        return archive_path

    except Exception as e:
        raise Exception(
            f"Unable to compress the archive, an exception was thrown : {e}"
        )
        raise e


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def has_java() -> bool:
    """Checks if java is available in the system's path.

    Returns:
        [bool] -- true if java is available, otherwise false.
    """
    try:
        subprocess.run(["java", "-v"])
    except Exception:
        return False

    return True


def has_fmpy() -> bool:
    """Checks if FMPy is available

    Returns:
        bool -- true if FMPy is available, otherwise false.
    """
    try:
        import fmpy  # noqa: F401
    except Exception:
        return False

    return True


def system_identifier() -> str:
    """Returns an identifier consisting of the platform and it architecture.

    Possible values are: win32, win64, linux32, linux64, darwin32, darwin64

    Returns:
        str -- hostsystem identifier
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


if __name__ == "__main__":

    inPath = join(dirname(__file__), "test")
    outpath = join(dirname(__file__), "out.zip")

    zipdir(inPath, outpath)
