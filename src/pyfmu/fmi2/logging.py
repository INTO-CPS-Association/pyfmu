"""Defines logging related functionality
"""
from typing import Iterable, List, Callable, Optional
from abc import ABC
import logging
from traceback import format_exc

from pyfmu.fmi2.types import Fmi2Status, Fmi2Status, Fmi2Status_T, Fmi2LoggingCallback


# log category which the pyfmu framework logs to
_internal_log_catergory = "pyfmu"
# default parameter for events
_default_category = "events"


class Fmi2StdLogCats:
    """Standard log categories defined in the FMI2 specification.
    """

    logEvents = "logEvents"
    logSingularLinearSystems = "logSingularLinearSystems"
    logNonlinearSystems = "logNonlinearSystems"
    logDynamicStateSelection = "logDynamicStateSelection"
    logStatusWarning = "logStatusWarning"
    logStatusDiscard = "logStatusDiscard"
    logStatusError = "logStatusError"
    logStatusFatal = "logStatusFatal"
    logStatusPending = "logStatusPending"
    logAll = "logAll"


class Fmi2LoggerBase(ABC):
    def __init__(self):

        self._categories_to_predicates = {}
        self._active_categories = set()

    def set_debug_logging(self, logging_on: bool, categories: List[str]):
        if logging_on:
            self._active_categories = self._active_categories.union(categories)
        else:
            self._active_categories = self._active_categories.difference(categories)

    def register_log_category(
        self,
        category: str,
        aliases: List[str] = None,
        predicate: Callable[[Fmi2Status, str, str], bool] = None,
    ) -> None:
        """Registers a new log category

        Arguments:
            category {str} -- [description]

        Keyword Arguments:
            aliases {[type]} -- a list of aliases for the category (default: {None})
            predicate {[type]} -- a predicate function which takes as input a message and whether it should be logged. (default: {None})

        """

        if aliases is not None and predicate is not None:
            raise ValueError(
                "Unable to register log category, both a set of aliases and predicate were supplied."
            )

        # if neither aliases or predicate is registed log category and category are associated
        if aliases is None and predicate is None:

            def default_predicated(s, c, m) -> bool:
                nonlocal category
                return c == category

            predicate = default_predicated

        if aliases:

            def alias_predicate(s, c, m):
                nonlocal aliases
                return c in aliases

            predicate = alias_predicate

        self._categories_to_predicates[category] = predicate

    def log(
        self, message: str, category: str = _default_category, status=Fmi2Status.ok
    ) -> None:

        statusArgs_to_category = {
            None: Fmi2Status.ok,
            Fmi2Status.ok: Fmi2Status.ok,
            "ok": Fmi2Status.ok,
            Fmi2Status.warning: Fmi2Status.warning,
            "warning": Fmi2Status.warning,
            Fmi2Status.discard: Fmi2Status.discard,
            "discard": Fmi2Status.discard,
            Fmi2Status.error: Fmi2Status.error,
            "error": Fmi2Status.error,
            Fmi2Status.fatal: Fmi2Status.fatal,
            "fatal": Fmi2Status.fatal,
            Fmi2Status.pending: Fmi2Status.pending,
            "pending": Fmi2Status.pending,
        }

        if status not in statusArgs_to_category:
            raise RuntimeError(
                f"Unrecognized status: {status}, valid options are : {statusArgs_to_category.keys()}"
            )

        status = statusArgs_to_category[status]

        if category is None:
            category = _default_category

        # log only for the active categories
        activate_categories_to_predicates = {
            c: p
            for c, p in self._categories_to_predicates.items()
            if c in self._active_categories
        }

        # an message should be logged if a predicate exists which matches it.
        for p in activate_categories_to_predicates.values():

            if p(status, category, message) is True:

                self._do_log(status, category, message)
                break

    def _do_log(self, message: str, category: str, status: Fmi2Status):
        pass

    def register_standard_categories(self, categories: Iterable[str]) -> None:
        """Registers the standard log categories defined by FMI2.

        Arguments:
            categories {Iterable[str]} -- A list of standard categories register.
            Possible values are:
            * logEvents
            * logNonlinearSystems
            * logNonlinearSystems
            * logDynamicStateSelection,
            * logStatusWarning
            * logStatusDiscard
            * logStatusError
            * logStatusFatal
            * logStatusPending
            * logAll

        See 2.2.4 p.42 for reference
        """
        try:
            categories = set(categories)
        except Exception as e:
            raise ValueError(
                f"Unable to register standard log categories. The specified categories could not be converted to a set."
            ) from e

        def events_predicate(status, category, message):
            c = category.lower()
            matches = {"event", "events"}
            return c in matches

        def sls_predicate(status, category, message):
            c = category.lower()
            matches = {"singularlinearsystem", "singularlinearsystems", "sls"}
            return c in matches

        def nls_predicate(status, category, message):
            c = category.lower()
            matches = {"nonlinearsystem", "nonlinearsystems", "nls"}
            return c in matches

        def dss_predicate(status, category, message):
            c = category.lower()
            matches = {"dynamicstateselection", "dss"}
            return c in matches

        def warning_predicate(status, category, message):
            return status == Fmi2Status.warning

        def discard_predicate(status, category, message):
            return status == Fmi2Status.discard

        def error_predicate(status, category, message):
            return status == Fmi2Status.error

        def fatal_predicate(status, category, message):
            return status == Fmi2Status.fatal

        def pending_predicate(status, category, message):
            return status == Fmi2Status.pending

        def all_predicate(status, category, message):
            return True

        predicates = {
            "logEvents": events_predicate,
            "logSingularLinearSystems": sls_predicate,
            "logNonlinearSystems": nls_predicate,
            "logDynamicStateSelection": dss_predicate,
            "logStatusWarning": warning_predicate,
            "logStatusDiscard": discard_predicate,
            "logStatusError": error_predicate,
            "logStatusFatal": fatal_predicate,
            "logStatusPending": pending_predicate,
            "logAll": all_predicate,
        }

        predicate_matches = {
            cat: pred for cat, pred in predicates.items() if cat in categories
        }

        self._categories_to_predicates = {
            **self._categories_to_predicates,
            **predicate_matches,
        }

    def register_all_standard_categories(self) -> None:
        """Convenience method used to register all standard FMI2 log categories
        """
        self.register_standard_categories(
            [
                "logEvents",
                "logSingularLinearSystems",
                "logNonlinearSystems",
                "logDynamicStateSelection",
                "logStatusWarning",
                "logStatusDiscard",
                "logStatusError",
                "logStatusFatal",
                "logStatusPending",
                "logAll",
            ]
        )

    @property
    def active_categories(self):
        """Categories which are marked as active.
        """
        return self._active_categories

    @property
    def available_categories(self):
        """Categories which have been declared by the FMU.
        """
        return self._categories_to_predicates.keys()


class Fmi2CallbackLogger(Fmi2LoggerBase):
    """Class implementing the FMI2 logging system by providing methods to register and enable specific categories.
    """

    def __init__(self, callback, log_stdout=False):

        super().__init__()
        self._callback = callback
        self._log_stdout = log_stdout

    def _do_log(self, status, category, message):

        if self._log_stdout:
            print(status, category, message)

        assert isinstance(status.value, int), "status should be int"
        assert isinstance(category, str), "status should be int"
        assert isinstance(message, str), "status should be int"

        # print(self._callback)
        self._callback(status.value, category, message)


class Fmi2NullLogger(Fmi2LoggerBase):
    def __init__(self):
        super().__init__()

    def log(self, message, category: str = "", status=None):
        pass


class FMI2SlaveLogger:
    """Logger object specific to a given slave instance.

    The interface is inspired by the logging library:
    https://docs.python.org/3/library/logging.html
    """

    _fmi_to_log_categories = {
        Fmi2Status.ok: logging.INFO,
        Fmi2Status.warning: logging.WARNING,
        Fmi2Status.discard: logging.WARNING,
        Fmi2Status.error: logging.ERROR,
        Fmi2Status.fatal: logging.CRITICAL,
    }

    def __init__(
        self,
        instance_name: str,
        slave_handle: int,
        callback: Optional[Fmi2LoggingCallback],
        log_stdout=True,
    ):
        self._callback = callback
        self._instance_name = instance_name

        if log_stdout:
            self._logger = logging.getLogger(f"{instance_name}.{slave_handle}")

    def ok(
        self, msg: str, category: str = None, exc_info=False, stack_info=False,
    ):
        self._log(
            status=Fmi2Status.ok,
            msg=msg,
            category=category,
            exc_info=exc_info,
            stack_info=stack_info,
        )

    def warning(
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

    def discard(
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

    def error(
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

    def fatal(
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

    def pending(
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

        if exc_info:
            msg = f"{msg}\n{format_exc()}"

        if stack_info or stack_level:
            raise NotImplementedError()

        if category is None:
            category = "info"

        self._logger.log(level=FMI2SlaveLogger._fmi_to_log_categories[status], msg=msg)

        if self._callback is not None:
            print("Invoking callback!")
            self._callback(
                instance_name=self._instance_name,
                status=status,
                category=category,
                message=msg,
            )

    def register_new_category(self, categrory: str, predicate: Callable[[str], bool]):
        raise NotImplementedError()
