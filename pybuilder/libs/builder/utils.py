from zipfile import ZipFile, ZIP_DEFLATED
import os
from os.path import dirname, isdir, isfile, join, normpath
from pathlib import Path

def builder_basepath() -> str:
    """gets the path to the builder's root
    
    Returns:
        str -- path to root
    """
    return normpath(join(dirname(__file__),"..",".."))

def zipdir(inDir: str, outDir: str):

    if(not isdir(inDir)):
        raise ValueError("Input path does not correspond to a directory!")

    with ZipFile(outDir, 'w', ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(inDir):
            for file in files:
                p = os.path.relpath(os.path.join(root, file),
                                    os.path.join(inDir, '..'))
                zf.write(p)


if __name__ == "__main__":

    from os.path import join, dirname

    inPath = join(dirname(__file__), "test")
    outpath = join(dirname(__file__), "out.zip")

    zipdir(inPath, outpath)


def _resources_path() -> Path:
    """Returns the path the the resource folder. 

    This is expected to be placed relative to this file ../../resources

    Returns:
        Path -- path to the resources folder
    """
    return Path(__file__).parent.parent.parent / 'resources'