import subprocess
from enum import Enum
import platform
import logging
from tempfile import mkdtemp
import os
from os.path import realpath, join
from pathlib import Path

from pybuilder.resources.resources import Resources
from pybuilder.builder.utils import cd


class FMI_Versions(Enum):
    FMI2 = "fmi2"
    FMI3 = "fmi3"


class ValidationResult():
    """
    Represents the result of validating an FMU with different validation techniques.
    """

    def __init__(self):
        self.validation_tools = {}

    def set_result_for(self, tool: str, valid: bool, message=""):
        self.validation_tools[tool] = {"valid": valid, "message": message}

    def get_result_for(self, tool: str):
        return self.validation_tools[tool]

    @property
    def valid(self):
        ss = {s['valid'] for s in self.validation_tools.values()}
        return False not in ss


def _has_fmpy() -> bool:
    try:
        import fmpy
    except:
        return False

    return True


def validate(fmu_archive: str, use_fmpy: bool = True, use_fmucheck: bool = False, use_vdmcheck: bool = False):

    if(use_fmpy and not _has_fmpy()):
        raise ImportError(
            "Cannot validate exported module using fmpy, the module could not be loaded. Ensure that the package is installed.")

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


def validate_project(project) -> bool:
    """Validate a project to ensure that it is consistent.

    Arguments:
        project {PyfmuProject} -- The project that is validated

    Returns:
        bool -- [description]
    """
    # TODO add validation
    return True


def validate_modelDescription(modelDescription: str, use_fmucheck=False, use_vdmcheck=False, vdmcheck_version=FMI_Versions.FMI2) -> ValidationResult:

    if(True not in {use_fmucheck, use_vdmcheck}):
        raise ValueError(
            "arguments must specifiy at least one verification tool")

    results = ValidationResult()

    if(use_vdmcheck):
        _validate_vdmcheck(modelDescription, results, vdmcheck_version)

    if(use_fmucheck):
        pass

    return results


def _vdmcheck_no_errors(results):
    """ Returns true if VDMCheck finds has found no errors.
    """
    stdout_contains_no_error = b'no errors found' in results.stdout.lower()
    stderr_is_empty = results.stderr == b''
    error_code_ok = results.returncode == 0
    return stdout_contains_no_error and stderr_is_empty and error_code_ok


def _validate_vdmcheck(modelDescription: str, validation_results: ValidationResult, fmi_version=FMI_Versions.FMI2):
    """Validate the model description using the VDMCheck tool.

    Arguments:
        modelDescription {str} -- textual representation of the model description.

    Keyword Arguments:
        fmi_version {FMI_Versions} -- [description] (default: {FMI_Versions.FMI2})

    Raises:
        ValueError: Raised if an the fmi_version is unknown or if the tool does not support validation thereof.
    """

    p = platform.system()

    system_and_fmi_to_script = {
        'Windows': {
            FMI_Versions.FMI2: Resources.get().vdmcheck_fmi2_ps,
            FMI_Versions.FMI3: Resources.get().vdmcheck_fmi3_ps,
        },
        'Linux': {
            FMI_Versions.FMI2: Resources.get().vdmcheck_fmi2_sh,
            FMI_Versions.FMI3: Resources.get().vdmcheck_fmi3_sh,
        },
        'Solaris': {
            FMI_Versions.FMI2: Resources.get().vdmcheck_fmi2_sh,
            FMI_Versions.FMI3: Resources.get().vdmcheck_fmi3_sh,
        },
        'Darwin': {
            FMI_Versions.FMI2: Resources.get().vdmcheck_fmi2_sh,
            FMI_Versions.FMI3: Resources.get().vdmcheck_fmi3_sh,
        },

    }

    if(p not in system_and_fmi_to_script):
        raise RuntimeError(
            f'Unable to perform validation using VDMCheck, the operating system {p}, is not supported')

    supported_versions = system_and_fmi_to_script[p]

    if(fmi_version not in supported_versions):
        raise RuntimeError(
            f'Unable to perform validation using VDMCheck, validation is only supported for FMI versions: {supported_versions}')

    # At the time of writing the checker can only be invoked on a file and not directly on a string.
    # Until this is introduced we simply store this in temp file

    tmpdir = Path(mkdtemp())
    md_path = str((tmpdir / 'modelDescription.xml').resolve())
    script_path = system_and_fmi_to_script[p][fmi_version]

    try:
        with open(md_path, 'w') as f:
            f.write(modelDescription)

        # If on windows use powershell, otherwise use bash script

        # Also we need to change working dir path of VDMCheck
        wd = script_path.parent
        with cd(script_path.parent):

            use_powershell = p in {'Windows'}
            if(use_powershell):

                result = subprocess.run(
                    ['powershell.exe', str(script_path.resolve()), '-fmu', md_path], capture_output=True)
            else:
                result = subprocess.run(
                    [script_path, md_path], capture_output=True)

    except Exception as e:
        raise RuntimeError(
            f'Failed performing validation using VDMCheck, invoking the validation program threw and exception: {e}') from e

    finally:
        # TODO delete tmp dir
        pass

    isValid = _vdmcheck_no_errors(result)

    validation_results.set_result_for('vdmcheck', isValid, result.stdout)
