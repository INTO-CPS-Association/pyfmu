from zipfile import ZipFile, ZIP_DEFLATED
import os
from os.path import dirname, isdir, isfile, join, normpath
from pathlib import Path
import subprocess

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

def has_java():
    """Checks if java is available in the system's path.
    
    Returns:
        [bool] -- true if java is available, otherwise false.
    """
    try:
        subprocess.run(['java','-v'])
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
