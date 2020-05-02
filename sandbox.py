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


_Fmi2Variability = Literal["constant", "continuous", "discrete", "fixed", "tunable"]
_Fmi2Initial = Literal["approx", "calculated", "exact"]
_Fmi2Value = TypeVar("_Fmi2Value", float, int, bool, str)
_Fmi2ValueType = Literal["real", "integer", "boolean", "string"]
_Fmi2ParameterInitial = Literal["fixed", "tunable"]
_Fmi2OutputVariability = Literal["constant", "continuous", "discrete"]


class Fmi2Initial:
    exact = "exact"
    approx = "approx"


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


class fmi2Input:
    """Register a property as an FMI input, using a getter and setter function.
    
     >>> @fmi2Input("real","continuous")
     >>> def x(self):
     ...    return self._x
     >>> @x.setter
     >>> def x(self,value):
     >>>    set self._x
    """

    def __set_name__(self, owner: SlaveBase, name):
        """hook used for accessing instance described in PEP 487"""
        owner._register_variable(
            owner, name, self.type, "input", self.variability, None, self.alias  # type: ignore
        )

    def __init__(
        self,
        type: Literal["real", "integer", "boolean", "string"],
        variability: Literal["continuous", "discrete"],
        alias: str = None,
        fget: Callable = None,
        fset: Callable = None,
    ):
        self.fget = fget
        self.fset = fset
        self.type: Literal["real", "integer", "boolean", "string"] = type
        self.variability: Literal["continuous", "discrete"] = variability
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
        return type(self)(self.type, self.variability, self.alias, fget, self.fset)

    def setter(self, fset):
        return type(self)(self.type, self.variability, self.alias, self.fget, self.fget)


class fmi2Output(_Fmi2Variable):
    def __init__(
        self,
        type: Literal["real", "integer", "boolean", "string"],
        variability: Literal["constant", "discrete", "continuous"],
        initial: Literal["approx", "calculated", "exact"],
        alias: str = None,
    ):
        super().__init__(type, "output", variability, initial, alias)


class fmi2Parameter(
    type: Literal["real", "integer", "boolean", "string"],
    variability: Literal["fixed", "tuneable"],
):
    pass

    def decorator_register_parameter(setter):
        pass

    return decorator_register_parameter


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

    @fmi2Input("real", "continuous")
    def x(self) -> float:
        return self._x

    @x.setter
    def x(self, value) -> None:
        self._x = 0

    @fmi2Output("real", "constant", "exact")
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    # @fmi2Parameter("real", "fixed")
    # def my_param(self, value: int):
    #     pass


if __name__ == "__main__":

    t = Test()
    print(t.x)
    test = 10
