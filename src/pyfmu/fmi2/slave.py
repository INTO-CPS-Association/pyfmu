from __future__ import annotations


from typing import List, Tuple, Optional, Literal
from uuid import uuid4
from pyfmu.fmi2.exception import SlaveAttributeError

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


class Fmi2Slave:
    def __init__(
        self,
        model_name: str,
        author: str = None,
        copyright: str = None,
        version: str = None,
        description: str = None,
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

        self.author = author
        self.copyright = copyright
        self.description = description
        self.model_name = model_name
        self.license = license
        self.guid = str(uuid4())

        self._variables: List[Fmi2ScalarVariable] = []
        self._log_categories: List[str] = []
        self._version = version
        self._value_reference_counter = 0
        self._used_value_references = {}

    def register_input(
        self,
        attr_name: str,
        data_type: Literal["real", "integer", "boolean", "string"] = "real",
        variability: Literal["continuous", "discrete"] = "continuous",
        description: str = None,
    ) -> None:
        self._register_variable(
            attr_name, data_type, "input", variability, None, description
        )

    def register_output(
        self,
        attr_name: str,
        data_type: Literal["real", "integer", "boolean", "string"] = "real",
        variability: Literal["constant", "discrete", "continuous"] = "continuous",
        initial: Literal["approx", "calculated", "exact"] = "calculated",
        description: str = None,
    ) -> None:

        self._register_variable(
            attr_name, data_type, "output", variability, initial, description
        )

    def register_parameter(
        self,
        attr_name: str,
        data_type: Literal["real", "integer", "boolean", "string"] = "real",
        variability: Literal["fixed", "tunable"] = "tunable",
        description: str = None,
    ) -> None:

        self._register_variable(
            attr_name, data_type, "parameter", variability, "exact", description
        )

    def _register_variable(
        self,
        attr_name: str,
        type: Fmi2DataType_T,
        causality: Fmi2Causality_T,
        variability: Fmi2Variability_T,
        initial: Optional[Fmi2Initial_T],
        description: str = None,
    ) -> None:
        """Expose an attribute of the slave as an variable of the model.

        Args:
            attr_name (str): name of the attribute
            type (Fmi2DataType_T): [description]
            causality (Fmi2Causality_T): [description]
            variability (Fmi2Variability_T): [description]
            initial (Optional[Fmi2Initial_T]): [description]
            description (str, optional): [description]. Defaults to None.

        Raises:
            Fmi2SlaveError: raised if a combination of variables are provided which does not

        """
        if attr_name not in dir(self):
            raise SlaveAttributeError(
                f"The slave instance has no attribute: {attr_name}"
            )

        if attr_name in [v.name for v in self.variables]:
            raise SlaveAttributeError(f"Attribute has already been registered.")

        if initial in {"approx", "exact"} or causality == "input":
            try:
                start = getattr(self, attr_name)
            except Exception as e:
                raise SlaveAttributeError(
                    f"""Failed determining a start value for the variable {attr_name}."""
                ) from e
        else:
            start = None

        value_reference = self._acquire_unused_value_reference()
        v = Fmi2ScalarVariable(
            attr_name,
            type,
            causality,
            variability,
            value_reference,
            initial,
            start,
            description,
        )
        self._variables.append(v)

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
        return self._log_categories

    @property
    def variables(self) -> List[Fmi2ScalarVariable]:
        return self._variables
