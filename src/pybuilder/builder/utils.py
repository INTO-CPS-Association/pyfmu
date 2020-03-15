from zipfile import ZipFile, ZIP_DEFLATED
import os
from os.path import dirname, isdir, isfile, join, normpath
from pathlib import Path


def zipdir(inDir: str, outDir: str):

    if(not isdir(inDir)):
        raise ValueError("Input path does not correspond to a directory!")

    with ZipFile(outDir, 'w', ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(inDir):
            for file in files:
                p = os.path.relpath(os.path.join(root, file),
                                    os.path.join(inDir, '..'))
                zf.write(p)


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


if __name__ == "__main__":

    from os.path import join, dirname

    inPath = join(dirname(__file__), "test")
    outpath = join(dirname(__file__), "out.zip")

    zipdir(inPath, outpath)
