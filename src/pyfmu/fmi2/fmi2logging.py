"""Defines logging related functionality
"""
from enum import Enum
from typing import Iterable, List
from abc import ABC, abstractmethod

from pyfmu.fmi2 import Fmi2Status

# log category which the pyfmu framework logs to
_internal_log_catergory = 'pyfmu'
# default parameter for events
_default_category = 'events'


class Fmi2StdLogCats(Enum):
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

    def set_debug_logging(self, logging_on: bool, categories: Iterable[str]):

        try:
            categories = set(categories)

        except Exception as e:
            msg = f"""Failed setting the debug categories.
            The argument categories could not be converted to a set, value was {categories}.
            Exception thrown by python was:
            {e}
            """
            self.log(Fmi2Status.warning, _internal_log_catergory, msg)
            return Fmi2Status.warning


        if(len(categories) == 0):
            msg = "Failed setting debug categories, list of categories is empty."
            self.log(Fmi2Status.warning, _internal_log_catergory, msg)

        not_strings = [c for c in categories if not isinstance(c, str)]
        strings = categories.difference(not_strings)

        is_all_strings = (len(not_strings) == 0)

        if(not is_all_strings):
            msg = f"""Not all elements of argument categories are strings.
            Non-string values are: {is_all_strings}
            string values are: {strings}
            Continuing using only valid categories.
            """

        if(logging_on):
            self._active_categories = self._active_categories.union(categories)
        else:
            self._active_categories = self._active_categories.difference(
                categories)

    def register_log_category(self, category: str, aliases=None, predicate=None) -> None:
        """Registers a new log category

        Arguments:
            category {str} -- [description]

        Keyword Arguments:
            aliases {[type]} -- a list of aliases for the category (default: {None})
            predicate {[type]} -- a predicate function which takes as input a message and whether it should be logged. (default: {None})

        """

        if(aliases != None and predicate != None):
            raise ValueError(
                'Unable to register log category, both a set of aliases and predicate were supplied.')

        # if neither aliases or predicate is registed log category and category are associated
        if(aliases == None and predicate == None):
            def default_predicated(s,c,m):
                nonlocal category
                return c == category

            predicate = default_predicated

        if(aliases):

            def alias_predicate(s,c,m):
                nonlocal aliases
                return c in aliases

            predicate = alias_predicate

        self._categories_to_predicates[category] = predicate

    def log(self, message: str,  category: str = _default_category, status=Fmi2Status.ok) -> None:

        statusArgs_to_category = {

            None : Fmi2Status.ok,

            Fmi2Status.ok : Fmi2Status.ok,
            'ok' : Fmi2Status.ok,

            Fmi2Status.warning : Fmi2Status.warning,
            'warning' : Fmi2Status.warning,

            Fmi2Status.discard : Fmi2Status.discard,
            'discard' : Fmi2Status.discard,

            Fmi2Status.error : Fmi2Status.error,
            'error' : Fmi2Status.error,

            Fmi2Status.fatal : Fmi2Status.fatal,
            'fatal' : Fmi2Status.fatal,

            Fmi2Status.pending : Fmi2Status.pending,
            'pending' : Fmi2Status.pending
        }

        if(status not in statusArgs_to_category):
            raise RuntimeError(f"Unrecognized status: {status}, valid options are : {statusArgs_to_category.keys()}")

        status = statusArgs_to_category[status]

        if(category is None):
            category = _default_category

        msg = (status, category, message)

        # log only for the active categories
        activate_categories_to_predicates = { c:p for c,p in self._categories_to_predicates.items() if c in self._active_categories}

        # an message should be logged if a predicate exists which matches it.
        for p in activate_categories_to_predicates.values():

            if(p(status,category,message) == True):

                self._do_log(status, category, message)
                break

    def _do_log(self, message : str ,category :str , status : Fmi2Status):
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
                f'Unable to register standard log categories. The specified categories could not be converted to a set.') from e

        def events_predicate(status,category,message):
            c = category.lower()
            matches = {'event', 'events'}
            return c in matches

        def sls_predicate(status,category,message):
            c = category.lower()
            matches = {'singularlinearsystem', 'singularlinearsystems', 'sls'}
            return c in matches

        def nls_predicate(status,category,message):
            c = category.lower()
            matches = {'nonlinearsystem', 'nonlinearsystems', 'nls'}
            return c in matches

        def dss_predicate(status,category,message):
            c = category.lower()
            matches = {'dynamicstateselection', 'dss'}
            return c in matches

        def warning_predicate(status,category,message):
            return status == Fmi2Status.warning

        def discard_predicate(status,category,message):
            return status == Fmi2Status.discard

        def error_predicate(status,category,message):
            return status == Fmi2Status.error

        def fatal_predicate(status,category,message):
            return status == Fmi2Status.fatal

        def pending_predicate(status,category,message):
            return status == Fmi2Status.pending

        def all_predicate(_):
            return True

        predicates = {
            "logEvents"                 : events_predicate,
            "logSingularLinearSystems"  : sls_predicate,
            "logNonlinearSystems"       : nls_predicate,
            "logDynamicStateSelection"  : dss_predicate,
            "logStatusWarning"          : warning_predicate,
            "logStatusDiscard"          : discard_predicate,
            "logStatusError"            : error_predicate,
            "logStatusFatal"            : fatal_predicate,
            "logStatusPending"          : pending_predicate,
            "logAll"                    : all_predicate
        }

        predicate_matches = {cat: pred for cat,
                             pred in predicates.items() if cat in categories}

        self._categories_to_predicates = {
            **self._categories_to_predicates, **predicate_matches}

    def register_all_standard_categories(self) -> None:
        """Convenience method used to register all standard FMI2 log categories
        """
        self.register_standard_categories([
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
        ])

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

    def __init__(self, callback, log_stdout = False):

        super().__init__()
        self._callback = callback
        self._log_stdout = log_stdout



    def _do_log(self, status, category, message):

        if(self._log_stdout):
            print(status,category,message)

        assert isinstance(status.value,int), "status should be int"
        assert isinstance(category,str), "status should be int"
        assert isinstance(message,str), "status should be int"

        #print(self._callback)
        self._callback(status.value,category,message)

class Fmi2NullLogger(Fmi2LoggerBase):

    def __init__(self):
        super().__init__()

    def log(self, message, category: str = "", status = None):
        pass