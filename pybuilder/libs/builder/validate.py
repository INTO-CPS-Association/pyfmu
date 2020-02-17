import subprocess
from enum import Enum
import platform
import logging
from tempfile import NamedTemporaryFile
from os.path import realpath, join
from pathlib import Path

def _has_fmpy() -> bool:
    try:
        import fmpy
    except:
        return False
    
    return True

def validate(fmu_archive: str, use_fmpy: bool = True, use_fmucheck: bool = False, use_vdmcheck: bool = False):

    if(use_fmpy and not _has_fmpy()):
        raise ImportError("Cannot validate exported module using fmpy, the module could not be loaded. Ensure that the package is installed.")

    valid = True

    if(use_fmpy):
        from fmpy import dump, simulate_fmu

        dump(fmu_archive)

        try:
            res = simulate_fmu(fmu_archive)
        except Exception as e:
            valid = False
            return repr(e)

    return None



class FMI_Versions(Enum):
    FMI2 = "fmi2"
    FMI3 = "fmi3"




def _validate_vdmcheck(modelDescription : str, fmi_version = FMI_Versions.FMI2):

    p = platform.system()

    bash_systems = {
        'Linux',
        'Solaris',
        'Darwin',
        "" # system could not be determined
    }

    powershell_systems = {
        'Windows'
    }

    
    script_name = "DDMCheck2"

    if(p in bash_systems):
        script_name += '.sh'

    # we assume that 
    elif(p in powershell_systems):
        script_name = "ps1"
        
    

    # At the time of writing the checker can only be invoked on a file and not directly on a string.
    # Until this is introduced we simply store this in temp file
    with NamedTemporaryFile("modelDescription.xml",'rw') as f:
        f.write(modelDescription)
        
        md_path = join(realpath(f.name), script_name)

        subprocess.call([md_path, script_path])
    

    
    

    