"""Defines logging related functionality
"""
from enum import Enum
from typing import Iterable

from .fmi2types import Fmi2Status

# log category which the pyfmu framework logs to
_internal_log_catergory = 'pyfmu'

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

class FMI2LogMessage:
    """Represents an log message as defined by FMI2
    """
    def __init__(self,status : Fmi2Status, category: str, message : str):
        """Creates a new log message
        
        Arguments:
            status {Fmi2Status} -- status of the FMU when the logging was performed.
            category {str} -- category of the log message.
            message {str} -- the message describing the logged event.

        Examples:

            ```
            FMI2LogMessage(Fmi2Status.OK,"misc","foo() was called")
            ```
        """
        if(not isinstance(status, Fmi2Status)):
            raise RuntimeError("")

        if(not isinstance(category,str)):
            raise RuntimeError("")

        if(not isinstance(message,str)):
            raise RuntimeError()

        self.status : Fmi2Status = status
        self.category : str = category
        self.message : str = message
        


class FMI2Logger():
    
    def __init__(self, callback = None):
        
        self._callback = callback
        self._log_stack = []
        self._active_log_categories = set()

    def set_active_log_categories(self, logging_on: bool, categories : Iterable[str]):
        
        try:
            categories = set(categories)

        except Exception as e:
            msg = f"""Failed setting the debug categories.
            The argument categories could not be converted to a set, value was {categories}.
            Exception thrown by python was:
            {e}
            """
            self.log(Fmi2Status.warning,_internal_log_catergory,msg)
            return Fmi2Status.warning

        is_empty = (len(categories) == 0)
        if(is_empty):
            msg = "Failed setting debug categories, list of categories is empty."
            self.log(Fmi2Status.warning,_internal_log_catergory,msg)

        not_strings = [c for c in categories if not isinstance(c,str)]
        strings = categories.difference(not_strings)
        
        is_all_strings = not_strings.empty()

        if(not is_all_strings):
            msg = f"""Not all elements of argument categories are strings.
            Non-string values are: {is_all_strings}
            string values are: {strings}
            Continuing using only valid categories.
            """
        
        if(logging_on):
            self.a_active_log_categoriesctive_log_categories = self.a_active_log_categoriesctive_log_categories.union(categories)
        else:
            self.a_active_log_categoriesctive_log_categories = self.a_active_log_categoriesctive_log_categories.difference(categories)

    def register_log_category(self,category : str, aliases = None, predicate = None) -> None:
        """Registers a new log category
        
        Arguments:
            category {str} -- [description]
        
        Keyword Arguments:
            aliases {[type]} -- [description] (default: {None})
            predicate {[type]} -- [description] (default: {None})
        """
        pass

    
    def log(self,message : str,  category : str, status = Fmi2Status.ok) -> None:
        
        msg = FMI2LogMessage(status,category,message)
        
        
        has_callback = (self._callback != None)
        if(has_callback):
            self._callback(msg)
    
        self._log_stack.append(msg)



    def _register_standard_categories(self) -> None:
        pass