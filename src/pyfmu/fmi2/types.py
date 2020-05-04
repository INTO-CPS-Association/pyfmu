"""Define commonly enumerations and classes for FMI2 types"""

from abc import abstractmethod
from typing import List, Tuple, Protocol, TypeVar, Literal, Dict, Set, Optional

from pyfmu.fmi2.exception import InvalidVariableError


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

    parameter: str = "parameter"
    calculatedParameter: str = "calculatedParameter"
    input: str = "input"
    output: str = "output"
    local: str = "local"
    independent: str = "independent"


class Fmi2DataTypes:
    """Defines the type of a variable.

    Values:
        * real: a real numbered value.
        * integer: a interger value.
        * boolean: a boolean value.
        * string: a text string.
    """

    real: Literal["real"] = "real"
    integer: Literal["integer"] = "integer"
    boolean: Literal["boolean"] = "boolean"
    string: Literal["string"] = "string"


class Fmi2Initial:
    """Defines how the initial value of a variable is initialized.

    Values:
        exact: The variable is initialized with the provided start value.
        calculated: The variable is defined based on other variables during initialization.
        "approx": The variable is defined based on the an iteration of an algebraic loop with the provided start value.
    """

    approx: Literal["approx"] = "approx"
    calculated: Literal["calculated"] = "calculated"
    exact: Literal["exact"] = "exact"


class Fmi2Variability:
    """ Defines the time instants where the variable can change value.

    Values:
        * constant: The variable never changes.
        * fixed: The variable never changes after initialization, specifically after exit_initialization_mode has been called.
        * tunable: ?
        * discrete : ?
        * continuous : No restriction on when the variable can change.
    """

    constant: Literal["constant"] = "constant"
    fixed: Literal["fixed"] = "fixed"
    tunable: Literal["tunable"] = "tunable"
    discrete: Literal["discrete"] = "discrete"
    continuous: Literal["continuous"] = "continuous"


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

    ok: Literal[0] = 0
    warning: Literal[1] = 1
    discard: Literal[2] = 2
    error: Literal[3] = 3
    fatal: Literal[4] = 4
    pending: Literal[5] = 5


Fmi2Status_T = Literal[0, 1, 2, 3, 4, 5]
Fmi2Value_T = TypeVar("Fmi2Value_T", float, int, bool, str)


Fmi2DataType_T = Literal["real", "integer", "boolean", "string"]
Fmi2Causality_T = Literal[
    "calculatedParameter", "independent", "input", "local", "output", "parameter"
]
Fmi2Variability_T = Literal["constant", "continuous", "discrete", "fixed", "tunable"]
Fmi2Initial_T = Literal["approx", "calculated", "exact"]

# ----- FMI2 Scalar variable -----

_causality_and_variability_to_initial: Dict[
    Tuple[Fmi2Causality_T, Fmi2Variability_T], Optional[Set[Optional[Fmi2Initial_T]]]
] = {
    ("parameter", "fixed"): {"exact"},
    ("parameter", "tunable"): {"exact"},
    ("calculatedParameter", "fixed"): {"approx", "calculated"},
    ("calculatedParameter", "tunable"): {"approx", "calculated"},
    ("input", "discrete"): {None},
    ("input", "continuous"): {None},
    ("output", "constant"): {"exact"},
    ("output", "discrete"): {"approx", "calculated", "exact"},
    ("output", "continuous"): {"approx", "calculated", "exact"},
    ("local", "constant"): {"exact"},
    ("local", "fixed"): {"approx", "calculated"},
    ("local", "tunable"): {"approx", "calculated"},
    ("local", "discrete"): {"approx", "calculated", "exact"},
    ("local", "continuous"): {"approx", "calculated", "exact"},
    ("independent", "continuous"): {None},
}

_type_to_pyType: Dict[Fmi2DataType_T, Fmi2Value_T] = {
    "real": float,  # type: ignore
    "integer": int,  # type: ignore
    "boolean": bool,  # type: ignore
    "string": str,  # type: ignore
}


class Fmi2ScalarVariable:
    """Represents an variable as defined by the FMI2 specification.

    .. warning::
        The FMI2 specification defines implicit initial values for specific
        causalities:
        * input: "initial must be exact or not present (meaning exact)" p.47
        * calculatedParameter: "initial must be "approx", "calculated" or not present (meaning calculated)" p.47.

        Implicit initial values are NOT allowed within the python part of the PyFMU, i.e. initial must be specified explicitly.
        No restrictions apply to how these are being represented in the model description.
    
    """

    def __init__(
        self,
        name: str,
        data_type: Fmi2DataType_T,
        causality: Fmi2Causality_T,
        variability: Fmi2Variability_T,
        value_reference: int,
        initial: Fmi2Initial_T = None,
        start: Fmi2Value_T = None,
        description: str = None,
    ):
        """Create a new variable with the specified type, causality, variability, initial and start value.

        Args:
            name: name of the variable
            data_type: the type of the variable.
            causality: whether the variable is an input, output, etc.
            variability: declares when the variable's value is allowed to change.
            value_reference: an index used to refer to the variable by the FMI interface.
            initial: declares how the start value of the variable should be determined.
            start: in case initial is exact or approx, this value defines the start value of the variable.
            description: an optional description of the variable, typically displayed by simulation tools.

        """

        # validate combinations of causality and variability
        if (causality, variability) not in _causality_and_variability_to_initial:
            raise InvalidVariableError(
                f"Illegal combination of causality: {causality} and variability: {variability}"
            )

        # validate initial value for combination of causality and variability
        if (
            initial
            not in _causality_and_variability_to_initial[(causality, variability)]
        ):
            raise InvalidVariableError(
                f"Initial: {initial}, is illegal for combination of causality: {causality} and variability: {variability}"
            )

        # validate start value for combination of causality, variability and initial
        # see fmi2 spec p.56
        must_define_start = (
            initial in {"exact", "approx"}
            or causality in {"input", "parameter"}
            or variability in {"constant"}
        )
        assert must_define_start != (
            initial == "calculated" or causality == "independent"
        )

        if (start_defined := start is not None) ^ must_define_start:
            s = "must be defined" if not start_defined else "may not be defined"
            raise InvalidVariableError(
                f"Start values {s} for this combination of variability: {variability}, causality: {causality} and initial: {initial}"
            )

        if (
            must_define_start
            and start is not None
            and type(start) is not (expected := _type_to_pyType[data_type])
        ):
            raise InvalidVariableError(
                f"Start value: {start} of type: {type(start)}, and declared data type: {data_type} are not compatible."
            )

        self.name = name
        self.data_type: Fmi2DataType_T = data_type
        self.causality: Fmi2Causality_T = causality
        self.initial: Optional[Fmi2Initial_T] = initial
        self.variability: Fmi2Variability_T = variability
        self.description = description
        self.start = start
        self.value_reference = value_reference

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
    ) -> Fmi2Status_T:
        ...

    def get_xxx(self, references: List[int]) -> Tuple[List[Fmi2Value_T], Fmi2Status_T]:
        ...

    def set_xxx(self, references: List[int], values: List[Fmi2Value_T]) -> Fmi2Status_T:
        ...

    def setup_experiment(
        self, start_time: float, stop_time: float = None, tolerance: float = None
    ) -> Fmi2Status_T:
        ...

    def enter_initialization_mode(self) -> Fmi2Status_T:
        ...

    def exit_initialization_mode(self) -> Fmi2Status_T:
        ...

    def reset(self) -> Fmi2Status_T:
        ...

    @property
    @abstractmethod
    def log_categories(self) -> List[str]:
        ...

    @property
    @abstractmethod
    def variables(self) -> List[Fmi2ScalarVariable]:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def author(self) -> str:
        ...

    @property
    @abstractmethod
    def guid(self) -> str:
        ...
