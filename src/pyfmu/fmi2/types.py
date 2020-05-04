"""Define commonly enumerations and classes for FMI2 types"""

from abc import abstractmethod
from typing import List, Tuple, Protocol, TypeVar


class Fmi2Causality:
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


class Fmi2DataTypes:
    """Defines the type of a variable.

    Values:
        * real: a real numbered value.
        * integer: a interger value.
        * boolean: a boolean value.
        * string: a text string.
    """

    real = "read"
    integer = "integer"
    boolean = "boolean"
    string = "string"


class Fmi2Initial:
    """Defines how the initial value of a variable is initialized.

    Values:
        exact: The variable is initialized with the provided start value.
        calculated: The variable is defined based on other variables during initialization.
        "approx": The variable is defined based on the an iteration of an algebraic loop with the provided start value.
    """

    approx = "approx"
    calculated = "calculated"
    exact = "exact"


class Fmi2Variability:
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


class Fmi2Status:
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


_Fmi2Variable = TypeVar("_Fmi2Variable", float, int, bool, str)


class Fmi2ScalarVariable:
    def __init__(
        self,
        name: str,
        data_type: Fmi2DataTypes,
        initial: Fmi2Initial = None,
        causality: Fmi2Causality = None,
        variability: Fmi2Variability = None,
        start: _Fmi2Variable = None,
        description: str = "",
        value_reference: int = None,
    ):

        self.name = name
        self.data_type = data_type
        self.causality = causality
        self.initial = initial
        self.variability = variability
        self.start: _Fmi2Variable = start
        self.description = description
        self.value_reference = value_reference

    def is_type(self, t: Fmi2DataTypes):
        return self.data_type == t

    def is_real(self) -> bool:
        return self.data_type == Fmi2DataTypes.real

    def is_integer(self) -> bool:
        return self.data_type == Fmi2DataTypes.integer

    def is_boolean(self) -> bool:
        return self.data_type == Fmi2DataTypes.boolean

    def is_string(self) -> bool:
        return self.data_type == Fmi2DataTypes.string

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        initial_str = "omitted" if self.initial is None else self.initial
        return f"{self.name}:{self.data_type}:{self.causality}:{initial_str}"


class IsFmi2Slave(Protocol):
    """Interface implemented by classes adhering to the FMI2 interface.
    It declares a set of functions which are invoked whenever the
    corresponding function is called in the fmi interface.
    """

    def do_step(
        self, current_time: float, step_size: float, no_set_fmu_state_prior: bool
    ) -> Fmi2Status:
        ...

    def get_xxx(self, references: List[int]) -> Tuple[List[_Fmi2Variable], Fmi2Status]:
        ...

    def set_xxx(self, references: List[int], values: List[_Fmi2Variable]) -> Fmi2Status:
        ...

    def setup_experiment(
        self, start_time: float, stop_time: float = None, tolerance: float = None
    ) -> Fmi2Status:
        ...

    def enter_initialization_mode(self) -> Fmi2Status:
        ...

    def exit_initialization_mode(self) -> Fmi2Status:
        ...

    def reset(self) -> Fmi2Status:
        ...

    @property
    @abstractmethod
    def log_categories(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def variables(self) -> List[Fmi2ScalarVariable]:
        ...
