from __future__ import annotations


from typing import List, Tuple, Optional, Callable, TypeVar, Any, Literal
from uuid import uuid4
from pyfmu.fmi2.exception import Fmi2ModelExtractionError

from pyfmu.fmi2.types import (
    Fmi2Status,
    Fmi2Value_T,
    Fmi2Status_T,
    Fmi2ScalarVariable,
    Fmi2DataType_T,
    Fmi2Variability_T,
    Fmi2Causality_T,
    Fmi2Initial_T,
)


# -------- input, output and parameter decorators for Fmi2Slave class --------

Fmi2Getter_T = Callable[[Any], TypeVar("Fmi2Getter_T", float, int, bool, str)]
Fmi2Setter_T = Callable[[Any, TypeVar("Fmi2Setter_T", float, int, bool, str)], None]


class _Fmi2VariableDecorator:
    def __set_name__(self, owner: Fmi2Slave, name):
        """hook used for accessing instance described in PEP 487"""

        if self.causality in {"approx", "exact"}:
            try:
                start = getattr(owner, name)
            except Exception as e:
                raise Fmi2ModelExtractionError(
                    f"Unable to get start value by reading attribute: {name}"
                ) from e
        else:
            start = None

        owner._register_variable(
            owner, name, self.type, self.causality, self.variability, self.initial, self.alias, start  # type: ignore
        )

    def __init__(
        self,
        type: Fmi2DataType_T,
        causality: Fmi2Causality_T,
        variability: Fmi2Variability_T,
        initial: Optional[Fmi2Initial_T],
        alias: str = None,
        fget: Callable = None,
        fset: Callable = None,
    ):
        self.type: Fmi2DataType_T = type
        self.causality: Fmi2Causality_T = causality
        self.variability: Fmi2Variability_T = variability
        self.initial: Optional[Fmi2Initial_T] = initial
        self.fget = fget
        self.fset = fset
        self.alias = alias

    def __call__(self, func: Fmi2Getter_T):
        self.fget = func
        return self

    def __get__(self, instance: Fmi2Slave, owner):
        if instance is None:
            return self
        elif self.fget is None:
            raise AttributeError(
                f"No getter has been defined for the specified {self.causality}."
            )
        else:
            return self.fget(instance)

    def __set__(self, instance: Fmi2Slave, value) -> None:
        if self.fset is None:
            raise AttributeError(
                f"No setter has been defined for the specified {self.causality}."
            )
        else:
            self.fset(instance, value)

    def getter(self, fget):
        self.fget = fget
        return self
        return type(self)(
            self.type,  # type: ignore
            self.causality,  # type: ignore
            self.variability,  # type: ignore
            self.initial,  # type: ignore
            self.alias,
            fget,
            self.fset,
        )

    def setter(self, fset):
        self.fset = fset
        return self
        return type(self)(
            self.type,  # type: ignore
            self.causality,  # type: ignore
            self.variability,  # type: ignore
            self.initial,  # type: ignore
            self.alias,
            self.fget,
            fset,
        )


class _Fmi2InputDecorator(_Fmi2VariableDecorator):
    """Register an input to the model which uses the specified "setter" to
    handle new inputs to the model.

    For example it may store it to an attribute "_x" for later use:
        >>> class slave(Fmi2Slave):
        ...
        ...     def __init__(self):
        ...         self._x = 10
        ...
        ...     @fmi2Input("real","continuous")
        ...     def x(self,value):
        ...         self._x = value
        ...
        >>> s = slave()
        >>> v.variables[0].name
        "x"
        >>> v.variables[0].causality
        "input"
        >>> v.variables[0] = 10
        >>> v.variables[0]
        10

    ..note:
        This may only be used to decorate methods of classes which implement the Fmi2Slave protocol.
    """

    def __init__(
        self,
        type: Literal["real", "integer", "boolean", "string"],
        variability: Literal["continuous", "discrete"],
        alias: str = None,
    ):
        super().__init__(
            type=type,
            causality="input",
            variability=variability,
            initial=None,
            alias=alias,
        )

    def __call__(self, func: Fmi2Setter_T):
        self.fset = func
        return self


class _Fmi2OutputDecorator(_Fmi2VariableDecorator):
    """Register a new output to the model using specified "getter" read the values.

    In the simplest case this may simply return an attribute of the slave which has
    been computed and stored in a prior step:
        >>> class slave(Fmi2Slave):
        ...
        ...     def __init__(self):
        ...         self._x = 10
        ...
        ...     @fmi2Output("real","continuous","exact")
        ...     def x(self):
        ...         return self._x
        ...
        >>> v = slave().variables[0]
        >>> v.name
        "x"
        >>> v.causality
        "output"
        >>> v.start
        10

    If initial is set to either exact or approx, the outputs start value will
    be determined by sampling the value after initialization of the slave object.

    ..note:
        This may only be used to decorate methods of classes which implement the Fmi2Slave protocol.
    """

    def __init__(
        self,
        type: Literal["real", "integer", "boolean", "string"],
        variability: Literal["constant", "discrete", "continuous"],
        initial: Literal["approx", "calculated", "exact"],
        alias: str = None,
    ):
        super().__init__(
            type=type,
            causality="output",
            variability=variability,
            initial=initial,
            alias=alias,
        )


class _Fmi2ParameterDecorator(_Fmi2VariableDecorator):
    """Register the specified property as an parameter of the model.

    This may only be used to decorate methods of classes which implement the Fmi2Slave protocol.
    """

    def __init__(
        self,
        type: Fmi2DataType_T,
        variability: Literal["fixed", "tunable"],
        alias: str = None,
    ):
        super().__init__(
            type=type,
            causality="parameter",
            variability=variability,
            initial=None,
            alias=alias,
        )

    def __call__(self, func: Fmi2Setter_T):
        self.fset = func
        return self


class Fmi2Slave:
    def __init__(
        self,
        modelName: str,
        author="",
        copyright="",
        version="",
        description="",
        logging_callback=None,
        logging_logAll=False,
        logging_stdout=False,
        logging_add_standard_categories=True,
        logging_slave_fmi_calls=True,
        check_uninitialized_variables=True,
    ):
        """Constructs a FMI2

        Arguments:
            modelName {str} -- [description]

        Keyword Arguments:
            author {str} -- [description] (default: {""})
            copyright {str} -- [description] (default: {""})
            version {str} -- [description] (default: {""})
            description {str} -- [description] (default: {""})
            logging_add_standard_categories {bool} -- registers standard logging categories defined by the FMI2 specification (default: {True})
            add_logging_override_param {bool} -- if true, add a boolean parameter to the FMU which allows it to log all, useful for FMPy (default: {True}).
        """

        self._author = author
        self._copyright = copyright
        self._description = description
        self._model_name = modelName
        self._license = license
        self._guid = uuid4()
        self._vars: List[Fmi2ScalarVariable] = []
        self._version = version
        self._value_reference_counter = 0
        self._used_value_references = {}

    def register_variable(
        self,
        name: str,
        type: Fmi2DataType_T,
        causality: Fmi2Causality_T,
        variability: Fmi2Variability_T,
        initial: Optional[Fmi2Initial_T],
        start: Optional[Fmi2Value_T],
        alias: str = None,
    ) -> None:

        print(f"registering variable: {type}:{causality}:{initial}:{variability}")

    def register_log_category(self, name: str):
        raise NotImplementedError()

    def do_step(
        self, current_time: float, step_size: float, no_set_fmu_state_prior: bool
    ) -> Fmi2Status_T:
        return Fmi2Status.ok

    def get_xxx(self, references: List[int]) -> Tuple[List[Fmi2Value_T], Fmi2Status_T]:
        raise NotImplementedError()

    def set_xxx(self, references: List[int], values: List[Fmi2Value_T]) -> Fmi2Status_T:
        raise NotImplementedError()

    def setup_experiment(
        self, start_time: float, stop_time: float = None, tolerance: float = None
    ) -> Fmi2Status_T:
        return Fmi2Status.ok

    def enter_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def exit_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def reset(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def _acquire_unused_value_reference(self) -> int:
        """ Returns the an unused value reference
        """
        while True:
            vr = self._value_reference_counter
            self._value_reference_counter += 1

            if vr not in self._used_value_references:
                return vr

    @property
    def log_categories(self) -> List[str]:
        raise NotImplementedError()
        return []  # TODO

    @property
    def variables(self) -> List[Fmi2ScalarVariable]:
        raise NotImplementedError()
        return []  # TODO

    # ----- Short-hand access to decorators -----
    input = _Fmi2InputDecorator
    output = _Fmi2OutputDecorator
    parameter = _Fmi2ParameterDecorator
