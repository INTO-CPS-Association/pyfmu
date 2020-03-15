
from enum import Enum
from typing import Union

class Fmi2Causality(Enum):
    """ Defines the causality of the variable, that is whether it is an input, output, parameter, etc.

    Values:
        * parameter: a value set by the environment which remains constant during the simulation.
        * calculatedParameter: ?
        * input: An input from another model.
        * output: An output to other models.
        * local: ?
        * independent: Independent variable, typically time. At most one variable of an FMU may be declared as independent.

    """
    parameter = "parameter"
    calculatedParameter = "calculatedParameter"
    input = "input"
    output = "output"
    local = "local"
    independent = "independent"

class Fmi2DataTypes(Enum):
    """Defines the type of a variable.

    Values:
        * real: a real numbered value.
        * integer: a interger value.
        * boolean: a boolean value.
        * string: a text string.
    """
    real = "Real"
    integer = "Integer"
    boolean = "Boolean"
    string = "String"

class Fmi2Initial(Enum):
    """Defines how the initial value of a variable is initialized.
    
    Values:
        exact: The variable is initialised with the provided start value.
        calculated: The variable is defined based on other variables during initialisation. 
        "approx": The variable is defined based on the an iteration of an algebraic loop with the provided start value.
    """
    exact = "exact"
    approx = "approx"
    calculated = "calculated"

class Fmi2Variability(Enum):
    """ Defines the time instants where the variable can change value.

    Values:
        * constant: The variable never changes.
        * fixed: The variable never changes after initialization, specifically after exit_initialization_mode has been called.
        * tunable: ?
        * discrete : ?
        * continuous : No restriction on when the variable can change. 
    """
    constant = "constant"
    fixed = "fixed"
    tunable = "tunable"
    discrete = "discrete"
    continuous = "continuous"

class Fmi2Status(Enum):
    """Represents the status of the FMU or the results of function calls.

    Values:
        * ok: all well
        * warning: an issue has arisen, but the computation can continue.
        * discard: an operation has resulted in invalid output, which must be discarded
        * error: an error has ocurred for this specific FMU instance.
        * fatal: an fatal error has ocurred which has corrupted ALL FMU instances.
        * pending: indicates that the FMu is doing work asynchronously, which can be retrived later.

    Notes:
        FMI section 2.1.3    
    
    """
    ok = 0
    warning = 1
    discard = 2
    error = 3
    fatal = 4
    pending = 5