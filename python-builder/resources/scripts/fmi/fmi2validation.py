
from collections import defaultdict
from fmi2types import Fmi2Variability, Fmi2Causality, Fmi2Initial

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

_A_initial = {"default" : Fmi2Initial.exact, "possible" : {Fmi2Initial.exact}}
_B_initial = {"default" : Fmi2Initial.calculated, "possible" : {Fmi2Initial.approx, Fmi2Initial.calculated}}
_C_initial = {"default" : Fmi2Initial.calculated, "possible" : {Fmi2Initial.exact, Fmi2Initial.approx, Fmi2Initial.calculated}}

_vc_combinations[Fmi2Variability.constant][Fmi2Causality.parameter]             = {"err" : _a_error}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.calculatedParameter]   = {"err" : _a_error}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.input]                 = {"err" : _a_error}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.output]                = {"err" : None, "initial" : _A_initial}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.local]                 = {"err" : None, "initial" : _A_initial}
_vc_combinations[Fmi2Variability.constant][Fmi2Causality.independent]           = {"err": _c_error}


_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.parameter]                = {"err" : None, "initial" : _A_initial}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.calculatedParameter]      = {"err" : None, "initial" : _B_initial}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.input]                    = {"err" : _d_error}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.output]                   = {"err" : _e_error}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.local]                    = {"err" : None, "initial": _B_initial}
_vc_combinations[Fmi2Variability.fixed][Fmi2Causality.independent]              = {"err":_c_error}

_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.parameter]             = {"err" : None, "initial" : _A_initial}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.calculatedParameter]   = {"err" : None, "initial" : _B_initial}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.input]                 = {"err" : _d_error}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.output]                = {"err" : _e_error}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.local]                 = {"err" : None, "initial": _B_initial}
_vc_combinations[Fmi2Variability.tunable][Fmi2Causality.independent]           = {"err" : _c_error}

    
def get_default_initial_for(variability : Fmi2Variability, causality : Fmi2Causality):
    
    if(validate_combination_variability_causality(variability,causality) is not None):
        raise Exception(f"Combinations of variability: {variability} and causality: {causaility} is not allowed!")

    return _vc_combinations[variability,causality]["initial"]["default"]

def get_possible_initial_for(variability : Fmi2Variability, causality : Fmi2Causality):

    if(validate_combination_variability_causality(variability,causality) is not None):
        raise Exception(f"Combinations of variability: {variability} and causality: {causaility} is not allowed!")

    return _vc_combinations[variability,causality]["initial"]["possible"]

def validate_combination_variability_causality(variability : Fmi2Variability, causality : Fmi2Causality):
    return _vc_combinations[variability][causality]["err"]


