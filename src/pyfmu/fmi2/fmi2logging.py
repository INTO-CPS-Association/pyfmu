"""Defines logging related functionality
"""
from enum import Enum
from typing import Iterable, List

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


class Fmi2LogMessage:
    """Represents an log message as defined by FMI2
    """

    def __init__(self, status: Fmi2Status, category: str, message: str):
        """Creates a new log message

        Arguments:
            status {Fmi2Status} -- status of the FMU when the logging was performed.
            category {str} -- category of the log message.
            message {str} -- the message describing the logged event.

        Examples:

            ```
            Fmi2LogMessage(Fmi2Status.OK,"misc","foo() was called")
            ```
        """
        if(not isinstance(status, Fmi2Status)):
            raise RuntimeError("")

        if(not isinstance(category, str)):
            raise RuntimeError("")

        if(not isinstance(message, str)):
            raise RuntimeError()

        self.status: Fmi2Status = status
        self.category: str = category
        self.message: str = message


class Fmi2Logger():

    def __init__(self, callback=None):

        self._callback = callback
        self._log_stack: List[Fmi2LogMessage] = []
        self._categories_to_predicates = {}
        self._active_categories = set()

    def set_active_log_categories(self, logging_on: bool, categories: Iterable[str]):

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
            aliases {[type]} -- [description] (default: {None})
            predicate {[type]} -- [description] (default: {None})
        """

        if(aliases != None and predicate != None):
            raise ValueError(
                'Unable to register log category, both a set of aliases and predicate were supplied.')

        # if neither aliases or predicate is registed log category and category are assocaited
        if(aliases == None and predicate == None):
            def default_predicated(msg: Fmi2LogMessage):
                nonlocal category
                return msg.category == category

            predicate = default_predicated

        if(aliases):

            def alias_predicate(msg: Fmi2LogMessage):
                nonlocal aliases
                return msg.category in aliases

            predicate = alias_predicate

        self._categories_to_predicates[category] = predicate

    def log(self, message: str,  category: str = _default_category, status=Fmi2Status.ok) -> None:


        if(category == None):
            category = _default_category
            
        msg = Fmi2LogMessage(status, category, message)
        

        # log only for the active categories
        activate_categories_to_predicates = { c:p for c,p in self._categories_to_predicates.items() if c in self._active_categories}

        for p in activate_categories_to_predicates.values():
            
            if(p(msg) == True):
                self._log_stack.append(msg)

                # testing callback
                if(self._callback):
                    self._callback(msg)

                break

    def register_standard_categories(self, categories: Iterable[str]) -> None:

        try:
            categories = set(categories)
        except Exception as e:
            raise ValueError(
                f'Unable to register standard log categories. The specified categories could not be converted to a set.') from e

        def events_predicate(msg: Fmi2LogMessage):
            c = msg.category.lower()
            matches = {'event', 'events'}
            return c in matches

        def sls_predicate(msg: Fmi2LogMessage):
            c = msg.category.lower()
            matches = {'singularlinearsystem', 'singularlinearsystems', 'sls'}
            return c in matches

        def nls_predicate(msg: Fmi2LogMessage):
            c = msg.category.lower()
            matches = {'nonlinearsystem', 'nonlinearsystems', 'nls'}
            return c in matches

        def dss_predicate(msg: Fmi2LogMessage):
            c = msg.category.lower()
            matches = {'dynamicstateselection', 'dss'}
            return c in matches

        def warning_predicate(msg: Fmi2LogMessage):
            return msg.status == Fmi2Status.warning

        def discard_predicate(msg: Fmi2LogMessage):
            return msg.status == Fmi2Status.discard

        def error_predicate(msg: Fmi2LogMessage):
            return msg.status == Fmi2Status.error

        def fatal_predicate(msg: Fmi2LogMessage):
            return msg.status == Fmi2Status.fatal

        def pending_predicate(msg: Fmi2LogMessage):
            return msg.status == Fmi2Status.pending

        def all_predicate(_: Fmi2LogMessage):
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
            "logStatusWarning",
            "logStatusError",
            "logStatusFatal",
            "logStatusPending",
            "logAll",
        ])

    def pop_messages(self, n: int) -> List[Fmi2LogMessage]:
        """Pops the top n messages of the message stack

        Arguments:
            n {int} -- number of messages to pop

        Returns:
            List[Fmi2LogMessage] -- List of messages
        """

        messages = self._log_stack[-n:]
        self._log_stack = self._log_stack[:-n]

        return messages

    def __len__(self):
        return len(self._log_stack)
