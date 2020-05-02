from __future__ import annotations

from typing import Optional, Union, Callable, TypeVar
import typing


class _NoAlias:
    pass


_UnboundType = Optional[Union[str, _NoAlias]]

Fmi2Value = TypeVar("T", float, int, bool, str)


Fmi2InputVariability = str
Fmi2OutputVariability = str

Fmi2DataType = TypeVar("T", float, int, bool, str)


class Fmi2Variability:
    continuous = "continuous"
    discrete = "discrete"
    constant = "constant"


class Fmi2Initial:
    exact = "exact"
    approx = "approx"


def register_variable_as_property(alias: str = None):
    def decorator_register_variable(getter: Callable[["SlaveBase"], Fmi2Value]):
        nonlocal alias
        if alias is None:
            alias = getter.__name__

        print(f"Register: {alias} as a property.")
        return getter

    return decorator_register_variable


class _AssignEnsure:
    def __init__(self, value: Fmi2Value):
        self.assigned = False
        self.value = value

    def __del__(self):
        if (self.assigned) is False:
            raise RuntimeError("Whoops you forgot to assign!")


class SlaveBase:
    def __init__(self):
        self._unbound_variable: _UnboundType = None
        self._alias_to_attribute: dict[str, str] = {}
        self._alias_to_value_reference: dict[str, int]

    def register_variable(
        self, start: Fmi2InputVariability, alias: str = None
    ) -> Fmi2Value:
        self._check_unbound_variable()

        if alias is not None:
            self._unbound_variable = alias
        else:
            self._unbound_variable = _NoAlias()

        """ To ensure that the user does the variable assignment on the same
        line as the register variable an special object is returned.
        The overloaded setattr will recognize the object and associate the name
        of the attribute and the fmi variable.

         >>> self.x = register_variable("input","exact", 0.0)
         >>> self.x
         ... 0.0
         >>> self.y = register_variable("input","continuous","exact", 0.0, alias="y_value")
         >>> register_variable("input","calculated") # forgot to assign raises exception
        """
        return _AssignEnsure(start)  # type: ignore

    def register_input(self, variability: str, start: Fmi2Value) -> Fmi2Value:
        pass

    def register_output(
        self,
        variability: Fmi2OutputVariability,
        initial: Fmi2Initial,
        start: Optional[Fmi2Value],
    ) -> Fmi2Value:
        pass

    def __setattr__(self, item: str, value) -> None:

        if type(value) is _AssignEnsure:

            alias = (
                self._unbound_variable if type(self._unbound_variable) is str else item
            )
            self.__dict__["_alias_to_attribute"][alias] = item
            self.__dict__["_unbound_variable"] = None
            self.__dict__[item] = value.value
            value.assigned = True

        else:
            self.__dict__[item] = value

    def _check_unbound_variable(self):
        if self._unbound_variable is not None:
            raise RuntimeError(
                "The value registered last was not bound to a variable. Ensure that the return of register variable is assigned to an attribute of the slave."
            )

    def _get_register_ready(self) -> bool:
        return hasattr(self, "_unbound_variable")

    def _get_value_reference_for(self, alias: str):
        pass

    @register_variable_as_property()
    def a(self) -> int:
        return 10


class Test(SlaveBase):
    def __init__(self):
        super().__init__()

        # All Good
        self.x = self.register_variable(10)
        self.y = self.register_variable(15, "yy")
        self.z = self.register_variable(20)
        self.my_str = self.register_variable("my_string")

        # Whoops
        self.register_variable(10, "a")
        self.b = 10


if __name__ == "__main__":

    t = Test()
    print(t.x)
    print(t.y)

    a = t.y
