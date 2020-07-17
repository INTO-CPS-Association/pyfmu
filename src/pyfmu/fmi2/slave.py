from __future__ import annotations

from typing import List, Tuple, Optional, Literal, Callable
from uuid import uuid4
from pyfmu.fmi2.exception import SlaveAttributeError
from pyfmu.fmi2.logging import Fmi2LoggerBase, FMI2PrintLogger

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
        logger: Fmi2LoggerBase = None,
        register_standard_log_categories=True,
    ):
        """Constructs a new FMI2 slave

        Args:
            model_name (str): [description]
            author (str, optional): [description]. Defaults to None.
            copyright (str, optional): [description]. Defaults to None.
            version (str, optional): [description]. Defaults to None.
            description (str, optional): [description]. Defaults to None.
            logger (FMI2SlaveLogger, optional): [description]. Defaults to None.
        """

        self.author = author
        self.copyright = copyright
        self.description = description
        self.model_name = model_name
        self.license = license
        self.guid = str(uuid4())

        if logger is None:
            logger = FMI2PrintLogger(model_name=model_name)

        self._variables: List[Fmi2ScalarVariable] = []
        self._version = version
        self._value_reference_counter = 0
        self._used_value_references = {}
        self._logger = logger

        if register_standard_log_categories:

            self.register_log_category(
                "logStatusWarning", lambda m, c, s: c == Fmi2Status.warning
            )
            self.register_log_category(
                "logStatusDiscard", lambda m, c, s: c == Fmi2Status.discard
            )
            self.register_log_category(
                "logStatusError", lambda m, c, s: s == Fmi2Status.error
            )
            self.register_log_category(
                "logStatusFatal", lambda m, c, s: s == Fmi2Status.fatal
            )
            self.register_log_category(
                "logStatusPending", lambda m, c, s: s == Fmi2Status.pending
            )
            self.register_log_category("logAll", lambda m, c, s: True)

    def register_input(
        self,
        attr_name: str,
        data_type: Literal["real", "integer", "boolean", "string"] = "real",
        variability: Literal["continuous", "discrete"] = "continuous",
        description: str = None,
    ) -> None:
        """Declares a new input of the model.

        This is added to the model description as a scalar variable with causality=input.

        Args:
            attr_name: name of the variable.
            data_type: the underlying type of the variable. Defaults to "real".
            variability: defines when the variable may change value with respect to time. Defaults to "continuous".
            description: text added to model description, often displayed by simulation environment. Defaults to None.
        """
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
        """Declares a new output of the model

        This is added to the model description as a scalar variable with causality=output.
        """

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

        if attr_name in [v.name for v in self.variables]:
            raise SlaveAttributeError(f"Attribute has already been registered.")

        if initial in {"approx", "exact"} or causality == "input":
            try:
                start = getattr(self, attr_name)
            except Exception as e:
                raise SlaveAttributeError(
                    f"""Failed determining a start value for the variable {attr_name}. Ensure that an attribute matching the name of the registered variable has been declared."""
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

    def register_log_category(
        self, name: str, predicate: Callable[[str, str, Fmi2Status_T], bool]
    ):
        """Register a new log category which may be used by the envrionment to filter log messages.

        A predicate function is used to determine which messages match the specified category.
        
        Args:
            name: identifier added to the model descriptions log categories.
            predicate: function used to determine whether message belongs to this log category.
        
        Examples:

            Filter based on category:
            >>> self.register_log_category("gui", lambda message, catergory, status: catergory == "gui")
        """
        self._logger.register_new_category(name, predicate)

    def do_step(
        self, current_time: float, step_size: float, no_set_fmu_state_prior: bool
    ) -> Fmi2Status_T:
        return Fmi2Status.ok

    def get_xxx(self, references: List[int]) -> Tuple[List[Fmi2Value_T], Fmi2Status_T]:
        try:
            # variables are stored in order of their value reference
            attributes = [self.variables[i].name for i in references]

            values = [getattr(self, a) for a in attributes]

            return (Fmi2Status.ok, values)

        except Exception:
            self.log_err(
                "An exception was raised when reading variables from slave",
                exc_info=True,
            )
            return (Fmi2Status.error, None)

    def set_xxx(self, references: List[int], values: List[Fmi2Value_T]) -> Fmi2Status_T:
        try:
            # variables are stored in order of their value reference
            attributes = [self.variables[i].name for i in references]

            for a, v in zip(attributes, values):
                setattr(self, a, v)

            return Fmi2Status.ok

        except Exception:

            self._loggers[handle].error(
                msg=f"Failed setting variable: {a} to the value: {v}. Ensure that the slave defines a attribute a matching name.",
                exc_info=True,
            )
            return Fmi2Status.error

    def setup_experiment(
        self, start_time: float, stop_time: float = None, tolerance: float = None
    ) -> Fmi2Status_T:
        return Fmi2Status.ok

    def set_debug_logging(
        self, categories: list[str], logging_on: bool
    ) -> Fmi2Status_T:
        """Set the active categories for which messages are passed to the evironment.          

        Note that a special case of "categories == [] and logging_on = True" is defined to have special significance.
        This is equivalent to logging all debug messages irregardless of category, see 2.1.5 p.21.

        Args:
            logging_on: flag used to indicate whether the specified categories should be enabled or not
            categories: list of categories to enable/disable
        """
        self._logger.set_debug_logging(logging_on, categories)
        return Fmi2Status.ok

    def enter_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def exit_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def reset(self) -> Fmi2Status_T:
        """Inform the FMU to set its internal state to that match that of a freshly instantiated FMU.

        Resources such as file handles and GUI windows may be reused, as long
        as the state that influences the simulation is reset.

        Returns:
            Fmi2Status_T: status code indicating the success of the operation
        """
        return Fmi2Status.ok

    def terminate(self) -> Fmi2Status_T:
        r"""Informs the FMU that the simulation has terminated and allows the
        environment read the final values of variables.
        
        For cleanup of managed resources it is recommended to use the regular Python pattern
        of defining function \_\_del\_\_ referred to as a finalizer.

        Returns:
            Fmi2Status_T: status code indicating the success of the operation
        """
        return Fmi2Status.ok

    def _acquire_unused_value_reference(self) -> int:
        """ Returns the an unused value reference
        """
        while True:
            vr = self._value_reference_counter
            self._value_reference_counter += 1

            if vr not in self._used_value_references:
                return vr

    def log_ok(
        self, msg: str, category: str = None, exc_info=False, stack_info=False,
    ):
        self._log(
            status=Fmi2Status.ok,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
        )

    def log_warning(
        self,
        msg: str,
        category: str = None,
        exc_info=False,
        stack_info=False,
        stack_level: float = None,
    ):
        self._log(
            status=Fmi2Status.warning,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
        )

    def log_discard(
        self,
        msg: str,
        category: str = None,
        exc_info=False,
        stack_info=False,
        stack_level: float = None,
    ):
        self._log(
            status=Fmi2Status.discard,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
        )

    def log_error(
        self,
        msg: str,
        category: str = None,
        exc_info=False,
        stack_info=False,
        stack_level: float = None,
    ):
        self._log(
            status=Fmi2Status.error,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
        )

    def log_fatal(
        self,
        msg: str,
        category: str = None,
        exc_info=False,
        stack_info=False,
        stack_level: float = None,
    ):
        self._log(
            status=Fmi2Status.fatal,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
        )

    def log_pending(
        self,
        msg: str,
        category: str = None,
        exc_info=False,
        stack_info=False,
        stack_level: float = None,
    ):
        self._log(
            status=Fmi2Status.pending,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
        )

    def _log(
        self,
        status: Fmi2Status_T,
        msg: str,
        category: str = None,
        exc_info=False,
        stack_info=False,
        stack_level: float = None,
    ):

        self._logger.log(
            status=status,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
            stack_level=stack_level,
        )

    @property
    def log_categories(self) -> List[str]:
        """List of available log categories.
        """
        return self._logger._category_to_predicates.keys()

    @property
    def variables(self) -> List[Fmi2ScalarVariable]:
        return self._variables
