from typing import Optional, List, Tuple, Dict, Set
from collections import defaultdict

from pyfmu.fmi2.exception import Fmi2InvalidVariableError
from pyfmu.fmi2.types import (
    Fmi2Variability_T,
    Fmi2Causality_T,
    Fmi2Initial_T,
    Fmi2DataType_T,
    Fmi2Value_T,
)

# dictionaries defining valid combinations of variability and causality, see fmi2 p.49
_vc_combinations = defaultdict(dict)


def validate_(
    data_type: Fmi2DataType_T,
    causality: Fmi2Causality_T = None,
    variability: Fmi2Variability_T = None,
    initial: Fmi2Initial_T = None,
    start: Fmi2Value_T = None,
) -> Tuple[
    Fmi2DataType_T, Fmi2Causality_T, Fmi2Variability_T, Fmi2Initial_T, Fmi2Value_T
]:
    """Infer missing attributes of a FMI scalar variable using the rules specified in the FMI2 specification.

    The function will raise an exception if any of the existing information does not adhere
    to the specification.


    Args:
        preliminary_variable: scalar variable containing the preliminary information.

        use_non_standard_defaults: use sensible start values, that are not covered by the FMI2 specification,
        the following rules are applied:
            real: 0.0
            integer: 0
            boolean: False
            string: ""
    """

    return (data_type, causality, variability, Fmi2Initial, start)


def _should_define_initial(causality: Fmi2Causality_T) -> bool:
    """ Whether or not the variable is allowed to define initial.

    FMI2 specification states:
    "It is not allowed to provide a value for initial if causality = "input" or "independent" p.48
    """
    return causality not in {"input", "independent"}


def _validate_initial(
    variability: Fmi2Variability_T, causality: Fmi2Causality_T, initial: Fmi2Initial_T
) -> Optional[str]:

    if _should_define_initial(causality) and initial is None:
        return f"an initial value MUST be specified for causality: {causality}"
    elif not _should_define_initial(causality) and initial is not None:
        return f"an initial MUST NOT be specified for causality: {causality}"
    elif _should_define_initial(causality) and initial not in _get_possible_initial(
        variability, causality
    ):
        return f"invalid initial specified for causality: {causality} and variability: {variability}"
    else:
        return None


def _get_possible_initial(
    variability: Fmi2Variability_T, causality: Fmi2Causality_T
) -> List[Fmi2Initial_T]:
    """ Returns the set of initial types that are valid for the combination of specific variability and causality.
    """
    if not _validate_causality_variability(causality, variability):
        raise Exception(
            f"Combinations of variability: {variability} and causality: {causality} is not allowed!"
        )

    return _vc_combinations[variability][causality]["initial"]["possible"]


def _validate_causality_variability(
    causality: Fmi2Causality_T, variability: Fmi2Variability_T
) -> bool:
    return (causality, variability) in _causality_and_variability_to_initial


def _validate_start_value(
    data_type: Fmi2DataType_T,
    causality: Fmi2Causality_T,
    initial: Fmi2Initial_T,
    variability: Fmi2Variability_T,
    start: Fmi2Value_T,
) -> Optional[str]:

    must_be_defined = _should_define_start(variability, causality, initial)
    is_defined = start is not None

    if must_be_defined ^ is_defined:
        s = "must be defined" if not is_defined else "may not be defined"
        return f"Start values {s} for this combination of variability: {variability}, causality: {causality} and initial: {initial}"

    if must_be_defined:

        fmi2type_to_type = {
            "real": float,
            "integer": int,
            "boolean": bool,
            "string": str,
        }

        if fmi2type_to_type[data_type] is not type(start):
            return f"The type of the start value: {start}, does not match the specified data type: {data_type}."

    return None


def _should_define_start(
    variability: Fmi2Variability_T, causality: Fmi2Causality_T, initial: Fmi2Initial_T
) -> bool:
    """Returns true if the combination requires that a start value is defined, otherwise false.

    For reference check the FMI2 specification p.54 for a description of which combination are allowed.
    """
    # see fmi2 spec p.56
    must_define_start = (
        initial in {"exact", "approx"}
        or causality in {"input", "parameter"}
        or variability in {"constant"}
    )

    can_not_define_start = initial == "calculated" or causality == "independent"

    assert must_define_start != can_not_define_start, "MUST be mutually exclusive"

    return must_define_start
