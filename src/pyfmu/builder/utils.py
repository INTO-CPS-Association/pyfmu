"""Contains utility functions used throughout the library"""

import os
import platform
import subprocess
from typing import Optional
from os.path import dirname, isdir, join
from pathlib import Path
from shutil import make_archive, unpack_archive, move, rmtree
from tempfile import mkdtemp
from zipfile import is_zipfile, ZipFile, ZIP_DEFLATED

from pyfmu.types import AnyPath


def zipdir(inDir: str, outDir: str):

    if not isdir(inDir):
        raise ValueError("Input path does not correspond to a directory!")

    with ZipFile(outDir, "w", ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(inDir):
            for file in files:
                p = os.path.relpath(os.path.join(root, file), os.path.join(inDir, ".."))
                zf.write(p)


def rm(path: AnyPath):
    """Delete a file or a directory

    Arguments:
        p {Path} -- path to a directory or a file
    """
    path = Path(path)

    if path.is_dir():
        rmtree(path)
        assert not path.is_dir()
    elif path.is_file() or path.is_symlink():
        path.unlink()
        assert not path.is_file()
    else:
        raise ValueError("path neither specifies a file, symlink nor a directory.")


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

        if not input_directory.is_absolute():
            input_directory = Path.cwd() / input_directory

        if not input_directory.is_dir():
            raise ValueError(
                f"input directory: {input_directory} does not appear to be a directory"
            )

        if output_directory is None:
            output_directory = input_directory
        else:
            output_directory = Path(output_directory)

        root_dir = str(input_directory)
        base_name = str(output_directory)

        archive_path = Path(
            make_archive(base_name=base_name, format=format, root_dir=root_dir)
        )
        assert archive_path.is_file()

        if extension is not None:
            renamed_name = f"{archive_path.stem}.{extension}"
            renamed_archive = archive_path.parent / renamed_name

            assert not renamed_archive.exists()
            move(str(archive_path), renamed_archive)
            assert not archive_path.is_file()
            assert renamed_archive.exists()

            return renamed_archive

        return archive_path

    except Exception as e:
        raise Exception(
            f"Unable to compress the archive, an exception was thrown : {e}"
        )
        raise e


def decompress(
    input_archive: AnyPath, output_directory: AnyPath, format: Optional[str] = None,
) -> None:
    """Extract archive to specified directory

    Arguments:
        input_archive {AnyPath} -- archive to extract
        output_directory {AnyPath} -- directory into which the files are extracted

    Keyword Arguments:
        format {str} -- specifies the decompression format. If unspecified infer from archive extension (default: {None})
    """
    unpack_archive(str(input_archive), str(output_directory), format=format)


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


def is_fmu_archive(path_to_archive: AnyPath) -> bool:
    """Check if path points to FMU archive.

    For example::

     >>> is_fmu_archive("myfmu.fmu")
     True
     >>> is_fmu_arcive("myfmu")
     False
     >>> is_fmu_archive("test.txt")
     False

    Note that this function only does superficial checks of the FMU
    and does not guarantee the correctness of the FMU.

    Arguments:
        path_to_archive {AnyPath} -- path to a FMU archive

    Returns:
        bool -- true if the path refers to a FMU archive, false otherwise
    """
    path_to_archive = Path(path_to_archive)

    if not is_zipfile(path_to_archive):
        return False

    td = Path(mkdtemp())

    decompress(path_to_archive, td, format="zip")
    is_archive = is_fmu_directory(td)
    rm(td)

    return is_archive


def is_fmu_directory(path_to_directory: AnyPath) -> bool:
    """Check if path points to extracted FMU.

    For example::

     >>> is_fmu_archive("myfmu.fmu")
     False
     >>> is_fmu_arcive("myfmu")
     True
     >>> is_fmu_archive("test.txt")
     False

    Note that this function only does superficial checks of the FMU
    and does not guarantee the correctness of the FMU.

    Arguments:
        path_to_archive {AnyPath} -- path to a extracted FMU

    Returns:
        bool -- true if the path refers to a extracted FMU, false otherwise
    """
    path_to_directory = Path(path_to_directory)
    model_description_path = path_to_directory / "modelDescription.xml"
    return model_description_path.is_file()


class TemporaryFMUArchive:
    def __init__(self, path_to_fmu: AnyPath):
        """Creates a temporary FMU archive if the path points to an extracted FMU, otherwise
        do nothing.

        In case an archive is created it is automatically removed.

        For example:

         >>> with TemporaryFMUArchive("myfmu.fmu") as p: # do nothing
         ...    pass
         >>> with TemporaryFMUArchive("myfmu") as p: # compress as {tmpname}.fmu
         ...    pass


        Arguments:
            path_to_fmu {AnyPath} -- [description]

        Raises:
            ValueError: [description]
        """
        self.should_cleanup = False
        path_to_fmu = Path(path_to_fmu)

        if is_fmu_archive(path_to_fmu):
            self.path_to_fmu = path_to_fmu
        elif is_fmu_directory(path_to_fmu):

            td = Path(mkdtemp())
            self.path_to_fmu = compress(path_to_fmu, td, extension="fmu")
            self.should_cleanup = True
        else:
            raise ValueError(
                "The specified path does not appear to be a FMU archive or directory."
            )

    def __enter__(self) -> Path:
        return self.path_to_fmu

    def __exit__(self, type, value, traceback):
        if self.should_cleanup:
            assert is_fmu_archive(self.path_to_fmu)
            rm(self.path_to_fmu)
            assert not self.path_to_fmu.is_file()


if __name__ == "__main__":

    inPath = join(dirname(__file__), "test")
    outpath = join(dirname(__file__), "out.zip")

    zipdir(inPath, outpath)
