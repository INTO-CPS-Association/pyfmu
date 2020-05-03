from __future__ import annotations

from typing import Optional, Union, TypeVar, Literal, Callable
from functools import partial
import inspect
import abc


class Fmi2Variability:
    constant = "constant"
    continuous = "continuous"
    discrete = "discrete"
    fixed = "fixed"
    tunable = "tunable"


class Fmi2DataTypes:
    real = "real"
    integer = "integer"
    boolean = "boolean"
    string = "string"


class Fmi2Initial:
    exact = "exact"
    approx = "approx"
    calculated = "calculated"


class _Fmi2Variable:
    def __set_name__(self, owner: SlaveBase, name):
        """hook used for accessing instance described in PEP 487"""
        owner._register_variable(
            owner, name, self.type, self.causality, self.variability, self.initial, self.alias  # type: ignore
        )

    def __init__(
        self,
        type: Literal["real", "integer", "boolean", "string"],
        causality: Literal[
            "calculatedParameter",
            "independent",
            "input",
            "local",
            "output",
            "parameter",
        ],
        variability: Literal["constant", "continuous", "discrete", "fixed", "tunable"],
        initial: Optional[Literal["approx", "calculated", "exact"]],
        alias: str = None,
        fget: Callable = None,
        fset: Callable = None,
    ):
        self.type = type
        self.causality = causality
        self.variability = variability
        self.initial = initial
        self.fget = fget
        self.fset = fset
        self.alias = alias

    def __call__(self, func):
        self.fget = func
        return self

    def __get__(self, instance: SlaveBase, owner):
        if instance is None:
            return self
        elif self.fget is None:
            raise AttributeError("no getter is defined.")
        else:
            return self.fget(instance)

    def __set__(self, instance: SlaveBase, value) -> None:
        if self.fset is None:
            raise AttributeError("no setter is defined.")
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


class fmi2Input(_Fmi2Variable):
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

    def __call__(self, func):
        self.fset = func
        return self


class fmi2Output(_Fmi2Variable):
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


class fmi2Parameter(_Fmi2Variable):
    """Register the specified property as an parameter of the model.

    This may only be used to decorate methods of classes which implement the Fmi2Slave protocol.
    """

    def __init__(
        self,
        type: Literal["real", "integer", "boolean", "string"],
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


class SlaveBase:
    def __init__(self):
        self._alias_to_attribute: dict[str, str] = {}
        self._alias_to_value_reference: dict[str, int]

    def _register_variable(
        self,
        name: str,
        type: Literal["real", "integer", "boolean", "string"],
        causality: Literal[
            "calculatedParameter",
            "independent",
            "input",
            "local",
            "output",
            "parameter",
        ],
        variability: Literal["constant", "continuous", "discrete", "fixed", "tunable"],
        initial: Optional[Literal["approx", "calculated", "exact"]],
        alias: str = None,
    ) -> None:
        print(f"registering variable: {type}:{causality}:{initial}:{variability}")


class Test(SlaveBase):
    def __init__(self):
        super().__init__()

        self._x = 10.0
        self._y = 10
        self.z = 10

    @fmi2Input("real", "continuous")
    def x(self, value) -> None:
        self._x = value

    @fmi2Output("real", "constant", "exact")
    def y(self):
        return self._y

    @fmi2Parameter("real", "fixed")
    def z(self, value: int):
        return self._z


if __name__ == "__main__":

    t = Test()
    print(t.x)
    test = 10
