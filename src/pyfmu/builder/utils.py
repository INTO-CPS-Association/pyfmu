from zipfile import ZipFile, ZIP_DEFLATED
from shutil import make_archive, copytree, move, rmtree
from tempfile import mkdtemp
from pathlib import Path
import os
from os.path import dirname, isdir, isfile, join, normpath
import subprocess
import platform


def zipdir(inDir: str, outDir: str):

    if(not isdir(inDir)):
        raise ValueError("Input path does not correspond to a directory!")

    with ZipFile(outDir, 'w', ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(inDir):
            for file in files:
                p = os.path.relpath(os.path.join(root, file),
                                    os.path.join(inDir, '..'))
                zf.write(p)


def rm(path):
    """Delete a file or a directory

    Arguments:
        p {Path} -- path to a directory or a file
    """

    if(platform.system() == "Windows"):
        print("TODO FIX RM ON WINDOWS!")
        return

    try:
        path = Path(path)

        if(path.is_dir()):
            rmtree(path)
        elif(path.is_file()):
            path.unlink()
        else:
            raise ValueError('path neither specifies a file nor a directory.')

    except Exception as e:
        raise RuntimeError(
            f'Unable to remove file/directory: {path} and error was raised: {e}')


def compress(
        in_dir,
        out_dir=None,
        fmt='zip',
        extension: str = None):
    """Compresses

    Arguments:
        in_dir {[type]} -- the directory to compress

    Keyword Arguments:
        out_dir {[type]} -- output archive (default: {None})
    """

    try:

        root_dir = in_dir
        base_dir = in_dir.name
        base_name = Path(mkdtemp()) / base_dir

        name_of_archive = (base_name.parent).resolve() / f'{base_dir}.{fmt}'

        assert(not name_of_archive.exists())
        make_archive(
            base_name=base_name,
            format=fmt,
            root_dir=root_dir
        )
        assert(name_of_archive.exists())

        if(extension is not None):
            renamed_name = name_of_archive.name.split('.')[0] + '.' + extension
            renamed_archive = name_of_archive.parent / renamed_name

            assert(not renamed_archive.exists())
            assert(name_of_archive.exists())
            move(name_of_archive, renamed_archive)
            assert(not name_of_archive.exists())
            assert(renamed_archive.exists())

            return renamed_archive

    except Exception as e:
        raise Exception(
            f'Unable to compress the archive, an exception was thrown : {e}')
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


def has_java():
    """Checks if java is available in the system's path.

    Returns:
        [bool] -- true if java is available, otherwise false.
    """
    try:
        subprocess.run(['java', '-v'])
    except Exception:
        return False

    return True


def has_fmpy() -> bool:
    """Checks if FMPy is available

    Returns:
        bool -- true if FMPy is available, otherwise false.
    """
    try:
        import fmpy
    except:
        return False

    return True


if __name__ == "__main__":

    from os.path import join, dirname

    inPath = join(dirname(__file__), "test")
    outpath = join(dirname(__file__), "out.zip")

    zipdir(inPath, outpath)
