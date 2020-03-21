import subprocess
from enum import Enum
import platform
import logging
from tempfile import mkdtemp
import os
from os.path import realpath, join
from pathlib import Path

from pyfmu.resources import Resources
from pyfmu.builder import cd, has_java, has_fmpy


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


def validate(fmu_archive: str, use_fmpy: bool = True, use_fmucheck: bool = False, use_vdmcheck: bool = False):

    if(use_fmpy and not has_fmpy()):
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
        raise NotImplementedError()

    return results


def _validate_vdmcheck(modelDescription: str, validation_results: ValidationResult, fmi_version=FMI_Versions.FMI2):
    """Validate the model description using the VDMCheck tool.

    Arguments:
        modelDescription {str} -- textual representation of the model description.

    Keyword Arguments:
        fmi_version {FMI_Versions} -- [description] (default: {FMI_Versions.FMI2})

    Raises:
        ValueError: Raised if an the fmi_version is unknown or if the tool does not support validation thereof.

    Notes:
        VDMCheck is implemented in Java, as such it requires java to be available in the path.
    """

    if(not has_java()):
        raise RuntimeError(
            'Unable to perform validation using VDMCheck, java was not found in the systems path.')

    fmi_to_jar = {
        fmi_version.FMI2: Resources.get().VDMCheck2_jar,
        fmi_version.FMI3: Resources.get().VDMCheck3_jar
    }

    if(fmi_version not in fmi_to_jar):
        raise RuntimeError(
            f'Unable to perform validation using VDMCheck. Unsupported FMI version: {fmi_version}, supported versions are: {fmi_to_jar.keys()}')

    jar_path = str(fmi_to_jar[fmi_version].resolve())
    # Run VDMCheck
    result = subprocess.run(
        ['java', '-jar', jar_path, '-x', modelDescription], capture_output=True)

    def _vdmcheck_no_errors(results):
        stdout_contains_no_error = b'no errors found' in results.stdout.lower()
        stderr_is_empty = results.stderr == b''
        error_code_ok = results.returncode == 0
        return stdout_contains_no_error and stderr_is_empty and error_code_ok

    # convert output
    isValid = _vdmcheck_no_errors(result)
    validation_results.set_result_for('vdmcheck', isValid, result.stdout)
