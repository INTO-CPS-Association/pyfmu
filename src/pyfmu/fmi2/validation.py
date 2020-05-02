from typing import Optional, List, Tuple
from collections import defaultdict

from pyfmu.fmi2.types import (
    Fmi2Variability,
    Fmi2Causality,
    Fmi2Initial,
    Fmi2DataTypes,
    Fmi2Variable,
)

# dictionaries defining valid combinations of variability and causality, see fmi2 p.49
_vc_combinations = defaultdict(dict)


_a_error = """The combinations “constant / parameter”, “constant / calculatedParameter” and “constant /
input” do not make sense, since parameters and inputs are set from the environment,
whereas a constant has always a value.
"""

_b_error = """The combinations “discrete / parameter”, “discrete / calculatedParameter”, “continuous /
parameter” and continuous / calculatedParameter do not make sense, since causality =
“parameter” and “calculatedParameter” define variables that do not depend on time, whereas
“discrete” and “continuous” define variables where the values can change during simulation.
"""

_c_error = "For an “independent” variable only variability = “continuous” makes sense."

_d_error = """A fixed or tunable “input” has exactly the same properties as a fixed or tunable parameter.
For simplicity, only fixed and tunable parameters shall be defined.
"""

_e_error = """A fixed or tunable “output” has exactly the same properties as a fixed or tunable
calculatedParameter. For simplicity, only fixed and tunable calculatedParameters shall be
defined.
"""

_A_initial = {"default": Fmi2Initial.exact, "possible": {Fmi2Initial.exact}}
_B_initial = {
    "default": Fmi2Initial.calculated,
    "possible": {Fmi2Initial.approx, Fmi2Initial.calculated},
}
_C_initial = {
    "default": Fmi2Initial.calculated,
    "possible": {Fmi2Initial.exact, Fmi2Initial.approx, Fmi2Initial.calculated},
}


_D_initial = {"default": None, "possible": {None}}
_E_initial = {"default": None, "possible": {None}}

_vc_combinations[Fmi2Variability.constant][Fmi2Causality.parameter] = {"err": _a_error}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.calculatedParameter] = {
    "err": _a_error
}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.input] = {"err": _a_error}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.output] = {
    "err": None,
    "initial": _A_initial,
}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.local] = {
    "err": None,
    "initial": _A_initial,
}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.independent] = {
    "err": _c_error
}


_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.parameter] = {
    "err": None,
    "initial": _A_initial,
}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.calculatedParameter] = {
    "err": None,
    "initial": _B_initial,
}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.input] = {"err": _d_error}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.output] = {"err": _e_error}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.local] = {
    "err": None,
    "initial": _B_initial,
}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.independent] = {"err": _c_error}

_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.parameter] = {
    "err": None,
    "initial": _A_initial,
}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.calculatedParameter] = {
    "err": None,
    "initial": _B_initial,
}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.input] = {"err": _d_error}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.output] = {"err": _e_error}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.local] = {
    "err": None,
    "initial": _B_initial,
}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.independent] = {"err": _c_error}


_vc_combinations[Fmi2Variability.discrete][Fmi2Causality.parameter] = {"err": _b_error}
_vc_combinations[Fmi2Variability.discrete][Fmi2Causality.calculatedParameter] = {
    "err": _b_error
}
_vc_combinations[Fmi2Variability.discrete][Fmi2Causality.input] = {
    "err": None,
    "initial": _D_initial,
}
_vc_combinations[Fmi2Variability.discrete][Fmi2Causality.output] = {
    "err": None,
    "initial": _C_initial,
}
_vc_combinations[Fmi2Variability.discrete][Fmi2Causality.local] = {
    "err": None,
    "initial": _C_initial,
}
_vc_combinations[Fmi2Variability.discrete][Fmi2Causality.independent] = {
    "err": _c_error
}

_vc_combinations[Fmi2Variability.continuous][Fmi2Causality.parameter] = {
    "err": _b_error
}
_vc_combinations[Fmi2Variability.continuous][Fmi2Causality.calculatedParameter] = {
    "err": _b_error
}
_vc_combinations[Fmi2Variability.continuous][Fmi2Causality.input] = {
    "err": None,
    "initial": _D_initial,
}
_vc_combinations[Fmi2Variability.continuous][Fmi2Causality.output] = {
    "err": None,
    "initial": _C_initial,
}
_vc_combinations[Fmi2Variability.continuous][Fmi2Causality.local] = {
    "err": None,
    "initial": _C_initial,
}
_vc_combinations[Fmi2Variability.continuous][Fmi2Causality.independent] = {
    "err": None,
    "initial": _D_initial,
}


# class Fmi2ScalarVariable:
#     def __init__(
#         self,
#         name: str,
#         data_type: Fmi2DataTypes,
#         initial: Fmi2Initial = None,
#         causality=Fmi2Causality.local,
#         variability=Fmi2Variability.continuous,
#         start=Fmi2Variable,
#         description: str = "",
#         value_reference: int = None,
#     ):


def infer_undefined_attributes(
    data_type: Fmi2DataTypes,
    causality: Fmi2Causality = None,
    variability: Fmi2Variability = None,
    initial: Fmi2Initial = None,
    start: Fmi2Variable = None,
    use_non_standard_defaults=True,
) -> Tuple[Fmi2DataTypes, Fmi2Causality, Fmi2Variability, Fmi2Initial, Fmi2Variable]:
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

    """Causality"""
    if causality is None:
        # "The default of causality is “local”." p.47
        causality = Fmi2Causality.local

    """Variability"""
    if variability is None:
        # "The default is “continuous”." p.48
        variability = Fmi2Variability.continuous

    err = _validate_variability_causality(variability, causality)

    if err:
        raise ValueError(f"Definition of scalar variable is inconsistent: {err}.")

    """Initial"""
    if initial is None:
        initial = _get_default_initial(variability, causality)

    err = _validate_initial(variability, causality, initial)

    if err:
        raise ValueError(f"Definition of scalar variable is inconsistent: {err}")

    """Start"""
    if (
        use_non_standard_defaults
        and start is None
        and _should_define_start(variability, causality, initial)
    ):
        start = _get_default_start(data_type)

    err = _validate_start_value(data_type, causality, initial, variability, start)
    if err:
        raise ValueError(f"Definition of scalar variable is inconsistent: {err}.")

    return (data_type, causality, variability, Fmi2Initial, start)


def _get_default_initial(variability: Fmi2Variability, causality: Fmi2Causality):

    if _validate_variability_causality(variability, causality) is not None:
        raise Exception(
            f"Combinations of variability: {variability} and causality: {causality} is not allowed!"
        )

    return _vc_combinations[variability][causality]["initial"]["default"]


def _should_define_initial(causality: Fmi2Causality) -> bool:
    """ Whether or not the variable is allowed to define initial.

    FMI2 specification states:
    "It is not allowed to provide a value for initial if causality = "input" or "independent" p.48
    """
    return causality not in {Fmi2Causality.input, Fmi2Causality.independent}


def _validate_initial(
    variability: Fmi2Variability, causality: Fmi2Causality, initial: Fmi2Initial
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
    variability: Fmi2Variability, causality: Fmi2Causality
) -> List[Fmi2Initial]:
    """ Returns the set of initial types that are valid for the combination of specific variability and causality.
    """
    if _validate_variability_causality(variability, causality) is not None:
        raise Exception(
            f"Combinations of variability: {variability} and causality: {causality} is not allowed!"
        )

    return _vc_combinations[variability][causality]["initial"]["possible"]


def _validate_variability_causality(
    variability: Fmi2Variability, causality: Fmi2Causality
) -> Optional[str]:
    """Validate combinations of variability and causality.

    Arguments:
        variability -- [description]
        causality  -- [description]

    Returns:
        An error message if the combination is invalid, otherwise None.
    """
    return _vc_combinations[variability][causality]["err"]


def _validate_start_value(
    data_type: Fmi2DataTypes,
    causality: Fmi2Causality,
    initial: Fmi2Initial,
    variability: Fmi2Variability,
    start: Fmi2Variable,
) -> Optional[str]:

    must_be_defined = _should_define_start(variability, causality, initial)
    is_defined = start is not None

    if must_be_defined ^ is_defined:
        s = "must be defined" if not is_defined else "may not be defined"
        return f"Start values {s} for this combination of variability: {variability}, causality: {causality} and initial: {initial}"

    if must_be_defined:

        fmi2type_to_type = {
            Fmi2DataTypes.real: float,
            Fmi2DataTypes.integer: int,
            Fmi2DataTypes.boolean: bool,
            Fmi2DataTypes.string: str,
        }

        if fmi2type_to_type[data_type] is not type(start):
            return f"The type of the start value: {start}, does not match the specified data type: {data_type}."

    return None


def _should_define_start(
    variability: Fmi2Variability, causality: Fmi2Causality, initial: Fmi2Initial
) -> bool:
    """Returns true if the combination requires that a start value is defined, otherwise false.

    For reference check the FMI2 specification p.54 for a description of which combination are allowed.
    """
    # see fmi2 spec p.54
    must_define_start = (
        initial in {Fmi2Initial.exact, Fmi2Initial.approx}
        or causality in {Fmi2Causality.parameter, Fmi2Causality.input}
        or variability in {Fmi2Variability.constant}
    )

    can_not_define_start = (
        initial == Fmi2Initial.calculated or causality == Fmi2Causality.independent
    )

    assert must_define_start != can_not_define_start, "MUST be mutually exclusive"

    return must_define_start


def _get_default_start(data_type: Fmi2DataTypes) -> Fmi2Variable:
    """Get default start value for the specified type.

    The following rules are applied:
        real: 0.0
        integer: 0
        boolean: False
        string: ""
    Note that this is an extension to the FMI2 specification.

    Returns:
        default value for the specified type
    """
    type_to_default = {
        Fmi2DataTypes.real: 0.0,
        Fmi2DataTypes.integer: 0,
        Fmi2DataTypes.boolean: False,
        Fmi2DataTypes.string: "",
    }
    return type_to_default[data_type]
