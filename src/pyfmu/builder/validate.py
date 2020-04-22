import subprocess
from enum import Enum
from pathlib import Path
from tempfile import mkdtemp, tempdir

from fmpy import simulate_fmu

from pyfmu.builder.utils import rm, system_identifier, has_java, compress
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

    @property
    def valid(self) -> bool:
        """Check whether errors were detected in the FMU by any of the tools.

        Returns:
            bool -- true if no errors, false otherwise
        """
        ss = {s["valid"] for s in self.validation_tools.values()}
        return False not in ss


def validate_fmu(
    path_to_fmu: AnyPath, use_fmpy=True, use_fmucheck=False, use_vdmcheck=False
) -> ValidationResult:
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

    path_to_fmu = Path(path_to_fmu)

    val_results = ValidationResult()

    if use_fmpy:
        _validate_fmpy(path_to_fmu, val_results)

    if use_fmucheck:
        _validate_fmiComplianceChecker(path_to_fmu, val_results)

    if use_vdmcheck:
        _validate_vdmcheck()

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
    modelDescription: str,
    validation_results: ValidationResult,
    fmi_version=FMI_Versions.FMI2,
):
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

    if not has_java():
        raise RuntimeError(
            "Unable to perform validation using VDMCheck, java was not found in the systems path."
        )

    fmi_to_jar = {
        fmi_version.FMI2: Resources.get().VDMCheck2_jar,
        fmi_version.FMI3: Resources.get().VDMCheck3_jar,
    }

    if fmi_version not in fmi_to_jar:
        raise RuntimeError(
            f"Unable to perform validation using VDMCheck. Unsupported FMI version: {fmi_version}, supported versions are: {fmi_to_jar.keys()}"
        )

    jar_path = str(fmi_to_jar[fmi_version].resolve())
    # Run VDMCheck
    result = subprocess.run(
        ["java", "-Dfile.encoding=UTF-8", "-jar", jar_path, "-x", modelDescription],
        capture_output=True,
    )

    def _vdmcheck_no_errors(results):
        stdout_contains_no_error = b"no errors found" in results.stdout.lower()
        stderr_is_empty = results.stderr == b""
        error_code_ok = results.returncode == 0
        return stdout_contains_no_error and stderr_is_empty and error_code_ok

    # convert output
    isValid = _vdmcheck_no_errors(result)
    validation_results.set_result_for("vdmcheck", isValid, result.stdout)


def _validate_fmiComplianceChecker(
    path_to_fmu: AnyPath, validation_results: ValidationResult
) -> None:
    """Verify the a FMU using the command line tool fmuCheck referred to as 'FMU Compliance Checker' by modelica.

    Supported platforms are linux64, win64 and darwin64

    Arguments:
        path_to_fmu {AnyPath} -- path to a FMU archive or directory.
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

    results = None

    should_cleanup_fmu = False

    """fmuCheck expects a zip-archive. In case the path points to a directory
    we compress the directory."""
    if path_to_fmu.is_dir():
        archive_directory = Path(mkdtemp()) / "fmu_under_test"
        path_to_archive = compress(path_to_fmu, archive_directory, extension="fmu")
        should_cleanup_fmu = True
    else:
        path_to_archive = path_to_fmu

    try:
        assert path_to_archive.is_file()
        results = subprocess.run([executable, str(path_to_fmu)], capture_output=True)
        validation_results.set_result_for(
            "fmuCheck", results.stderr == 0, results.stderr
        )
    except Exception as e:
        validation_results.set_result_for("fmuCheck", False, str(e))
    finally:
        if should_cleanup_fmu:
            rm(path_to_fmu)


def _validate_fmpy(path_to_fmu: AnyPath, validation_results: ValidationResult) -> None:
    """Validate an FMU using FMPy, by loading performing a simulation.
    
    The nature of this simulation is left up to FMPy's implementation.

    Arguments:
        path_to_fmu {AnyPath} -- path to FMU archive or directory
        validation_results {ValidationResult} -- structure into which the results are appended
    """
    try:
        simulate_fmu(path_to_fmu)
        validation_results.set_result_for("fmpy", True)
    except Exception as e:
        validation_results.set_result_for("fmpy", False, str(e))
