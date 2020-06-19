"""Contains functionality for validating FMUs using built-in and third-part checkers."""

import subprocess
from enum import Enum
from pathlib import Path
from typing import List
from traceback import format_exc

from fmpy import simulate_fmu

from pyfmu.builder.utils import (
    system_identifier,
    has_java,
    TemporaryFMUArchive,
)
from pyfmu.resources import Resources
from pyfmu.types import AnyPath


class FMI_Versions(Enum):
    FMI2 = "fmi2"
    FMI3 = "fmi3"


class ValidationResult:
    """
    Represents the result of validating an FMU with different validation techniques.
    """

    def __init__(self):
        self.validation_tools = {}

    def set_result_for(self, tool: str, valid: bool, message=""):
        self.validation_tools[tool] = {"valid": valid, "message": message}

    def get_result_for(self, tool: str):
        return self.validation_tools[tool]

    def __getitem__(self, key: str):
        return self.validation_tools[key]

    def get_report(self) -> str:
        report = """
Results of validation:\n
"""
        for tool_name, res in self.validation_tools.items():
            report += f"=============== {tool_name} ==============="
            report += "\n" + res["message"] + "\n"

        return report

    @property
    def valid(self) -> bool:
        """Check whether errors were detected in the FMU by any of the tools.

        Returns:
            bool -- true if no errors, false otherwise
        """
        ss = {s["valid"] for s in self.validation_tools.values()}
        return False not in ss


def validate_fmu(path_to_fmu: AnyPath, tools: List[str]) -> ValidationResult:
    """Validate an FMU using the specified tools. The FMU may either be an achive or a folder.

    Tools:
        - FMPy: simulation engine based on Python
        - fmuCheck: TODO
        - VDMCheck: model description checker

    In the case where the FMU is not already and archive and the tool requires this, it will be compressed
    to a temporary folder. The file is automatically removed afterwards.

    The result of the validation is an object containing the output of the invidual validation tools for
    the given FMU.

    For example a FMU archive may be validated as::

        >>> res = validate_fmu("Adder.fmu", use_fmucheck=True)
        >>> res.valid
        True
        >>> res = validate_fmu("invalid.fmu", use_fmucheck=True)
        >>> res.valid
        False
        >>> res["fmucheck"]
        ...

    Arguments:
        path_to_fmu {str} -- Path to a FMU archive or directory

    Keyword Arguments:
        use_fmpy {bool} -- validate using FMPy (default: {True})
        use_fmucheck {bool} -- validate using FMI Compliance Checker (default: {False})
        use_vdmcheck {bool} -- validate using VDMCheck (default: {False})

    Raises:
        ImportError: [description]

    Returns:
        ValidationResult -- structure containing the result of the validation
    """

    tools = [t.lower() for t in tools]
    tool_to_func = {
        "fmpy": _validate_fmpy,
        "fmucheck": _validate_fmiComplianceChecker,
        "vdmcheck": _validate_vdmcheck,
        "maestro_v1": _validate_maestro_v1,
    }

    unrecognized_tools = [t for t in tools if t not in tool_to_func.keys()]

    if len(unrecognized_tools) != 0:
        raise ValueError(
            f"""One or more of the specified tools could not be used to validate the FMU.
        The following tools were not recognized: {unrecognized_tools}"""
        )

    val_results = ValidationResult()
    path_to_fmu = Path(path_to_fmu)

    for t in tools:
        f = tool_to_func[t]
        try:
            f(path_to_fmu, val_results)
        except Exception as e:
            val_results.set_result_for(
                t,
                False,
                f"Validation failed an exception was thrown in Python:\n{format_exc()}",
            )

    return val_results


def validate_project(project) -> bool:
    """Validate a project to ensure that it is consistent.

    Arguments:
        project {PyfmuProject} -- The project that is validated

    Returns:
        bool -- [description]
    """
    # TODO add validation
    return True


def validate_modelDescription(
    modelDescription: str,
    use_fmucheck=False,
    use_vdmcheck=False,
    vdmcheck_version=FMI_Versions.FMI2,
) -> ValidationResult:

    if True not in {use_fmucheck, use_vdmcheck}:
        raise ValueError("arguments must specifiy at least one verification tool")

    results = ValidationResult()

    if use_vdmcheck:
        _validate_vdmcheck(modelDescription, results, vdmcheck_version)

    if use_fmucheck:
        raise NotImplementedError()

    return results


def _validate_vdmcheck(
    path_to_fmu: AnyPath,
    validation_results: ValidationResult,
    fmi_version=FMI_Versions.FMI2,
) -> None:
    """Validate a FMUs model description using VDMCheck.

    This tool requires that Java is installed in the systems path.

    Arguments:
        path_to_fmu {AnyPath} -- path to a FMU archive or directory
        validation_results {ValidationResult} -- structure into which the results are appended

    Keyword Arguments:
        fmi_version {FMI_Versions} -- FMI version implemented by the FMU (default: {FMI_Versions.FMI2})
    """

    path_to_fmu = Path(path_to_fmu)

    if not has_java():
        raise RuntimeError(
            "Unable to perform validation using VDMCheck, java was not found in the systems path."
        )

    fmi_to_jar = {
        FMI_Versions.FMI2: Resources.get().VDMCheck2_jar,
        FMI_Versions.FMI3: Resources.get().VDMCheck3_jar,
    }

    if fmi_version not in fmi_to_jar:
        raise RuntimeError(
            f"Unable to perform validation using VDMCheck. Unsupported FMI version: {fmi_version}, supported versions are: {fmi_to_jar.keys()}"
        )

    with TemporaryFMUArchive(path_to_fmu) as p:

        jar_path = str(fmi_to_jar[fmi_version].resolve())

        result = subprocess.run(["java", "-jar", jar_path, str(p)], capture_output=True)

    def _vdmcheck_no_errors(results):
        stdout_contains_no_error = b"no errors found" in results.stdout.lower()
        stderr_is_empty = results.stderr == b""
        error_code_ok = results.returncode == 0
        return stdout_contains_no_error and stderr_is_empty and error_code_ok

    # convert output
    isValid = _vdmcheck_no_errors(result)
    validation_results.set_result_for("vdmcheck", isValid, str(result.stdout))


def _validate_maestro_v1(
    path_to_fmu: AnyPath, validation_results: ValidationResult,
) -> None:
    """Validate a FMUs model description using VDMCheck.

    This tool requires that Java is installed in the systems path.

    Arguments:
        path_to_fmu {AnyPath} -- path to a FMU archive or directory
        validation_results {ValidationResult} -- structure into which the results are appended

    Keyword Arguments:
        fmi_version {FMI_Versions} -- FMI version implemented by the FMU (default: {FMI_Versions.FMI2})
    """

    path_to_fmu = Path(path_to_fmu)

    if not has_java():
        raise RuntimeError(
            "Unable to perform validation using Maestro 1, java was not found in the systems path."
        )

    with TemporaryFMUArchive(path_to_fmu) as p:

        jar_path = str(Resources.get().maestro_v1)

        results = subprocess.run(
            ["java", "-jar", jar_path, "-l", str(p)], capture_output=True
        )

    message = f"""
============= stdout ===============
{results.stdout.decode()}
============= stderr ===============
{results.stderr.decode()}"""

    validation_results.set_result_for("maestro_v1", results.returncode == 0, message)


def _validate_fmiComplianceChecker(
    path_to_fmu: AnyPath, validation_results: ValidationResult
) -> None:
    """Verify the a FMU using the command line tool fmuCheck referred to as 'FMU Compliance Checker' by modelica.

    Supported platforms are linux64, win64 and darwin64

    Arguments:
        path_to_fmu {AnyPath} -- path to a FMU archive or directory
        validation_results {ValidationResult} -- structure into which the results are appended

    Raises:
        RuntimeError: raised if the current host system is not supported
    """

    path_to_fmu = Path(path_to_fmu)

    platform_to_executable = {
        "linux64": Resources.get().fmuCheck_linux64,
        "darwin64": Resources.get().fmuCheck_linux64,
        "win64": Resources.get().fmuCheck_win64,
    }

    system = system_identifier()
    if system not in platform_to_executable:
        raise RuntimeError(
            f"FMI compliance checker is not supported on the host platform: {system}"
        )

    executable = str(platform_to_executable[system])

    with TemporaryFMUArchive(path_to_fmu) as archive:
        results = subprocess.run([executable, str(archive)], capture_output=True)

        message = f""" FMI Compliance Checker:
        ============= stdout ===============
        {results.stdout}
        ============= stderr ===============
        {results.stderr}
        """

        validation_results.set_result_for("fmucheck", results.returncode == 0, message)


def _validate_fmpy(path_to_fmu: AnyPath, validation_results: ValidationResult) -> None:
    """Validate an FMU using FMPy, by loading performing a simulation.

    The nature of this simulation is left up to FMPy's implementation.

    Arguments:
        path_to_fmu {AnyPath} -- path to FMU archive or directory
        validation_results {ValidationResult} -- structure into which the results are appended
    """
    try:
        simulate_fmu(str(path_to_fmu))
        validation_results.set_result_for("fmpy", True)
    except Exception as e:
        validation_results.set_result_for("fmpy", False, str(e))
