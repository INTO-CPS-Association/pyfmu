from abc import ABC, abstractmethod
from typing import List, Iterable
from uuid import uuid4
import logging

from .fmi2types import Fmi2Causality, Fmi2DataTypes, Fmi2Initial, Fmi2Variability, Fmi2Status
from .fmi2logging import Fmi2StdLogCats, FMI2LogMessage
from .fmi2variables import ScalarVariable
from .fmi2logging import FMI2Logger


_internal_log_catergory = 'pyfmu'

log = logging.getLogger('fmu')

class Fmi2Slave:
    

    def __init__(self, modelName: str, author="", copyright="", version="", description=""):

        self.author = author
        self.copyright = copyright
        self.description = description
        self.modelName = modelName
        self.license = license
        self.guid = uuid4()
        self.vars = []
        self.version = version
        self.value_reference_counter = 0
        self.used_value_references = {}

        self.logger = Fmi2Logger()

    def register_variable(self,
                          name: str,
                          data_type: Fmi2DataTypes,
                          causality = Fmi2Causality.local,
                          variability = Fmi2Variability.continuous,
                          initial : Fmi2Initial = None,
                          start = None,
                          description: str = "",
                          define_attribute: bool = True,
                          value_reference: int = None
                          ):
        """Add a variable to the model such as an input, output or parameter.
        
        Arguments:
            name {str} -- [description]
            data_type {Fmi2DataTypes} -- [description]
        
        Keyword Arguments:
            causality {[type]} -- defines the type of the variable, such as input, output or parameter (default: {Fmi2Causality.local})
            variability {[type]} -- defines the time dependency of the variable. (default: {Fmi2Variability.continuous})
            initial {Fmi2Initial} -- defines how the variable is initialized (default: {None})
            start {[type]} -- start value of the variable. (default: {None})
            description {str} -- a description of the variable which is added to the model description (default: {""})
            define_attribute {bool} -- if true, automatically add the specified attribute to instance if it does not already exist. (default: {True})
        """      


        # if not specified find an unused value reference
        if(value_reference is None):
            value_reference = self._acquire_unused_value_reference()

        var = ScalarVariable(name=name, data_type=Fmi2DataTypes.real, initial=initial, causality=causality,
                             variability=variability, description=description, start = start, value_reference = value_reference)

        self.vars.append(var)

        
        if(define_attribute):
            self._define_variable(var)    

    def register_log_category(self, name : str):
        """Registers a new log category.
        This information is used by co-simulation engines to filter messages
        
        Arguments:
            name {str} -- name of the category.

        Examples:

        ```
        self.register_log_category('runtime validation')

        ```
        """

        pass

    def setup_experiment(self, start_time: float):
        pass

    def enter_initialization_mode(self):
        pass

    def exit_initialization_mode(self):
        pass

    def do_step(self, current_time: float, step_size: float) -> bool:
        pass

    def reset(self):
        pass

    def terminate(self):
        pass

    def __set_debug_logging__(self, logging_on : bool, categories : Iterable[str]) -> None:
        """Defines the set of active log categories for which log messages will logged.
        Messages logged to any other categories will be ignored.


        This function is called by the tool though the fmi2SetDebugLogging function.

        Note that the tool can only "see" categories registered in the model description using the register_log_category.

        
        Arguments:
            categories {Iterable[str]} -- a set of categories which are set to be active
            logging_on {bool} -- if true, enable the categories, otherwise disable them
        
        Defaults category mapping:
            FMI2 specifies several standardized categories.

            * logEvents                 : Log all events (during initialization and simulation).
            * logSingularLinearSystems  : Log the solution of linear systems of equations if the solution is singular
                                          (and the tool picked one solution of the infinitely many solutions).
            * logNonlinearSystems       : Log the solution of nonlinear systems of equations.
            * logDynamicStateSelection  : Log the dynamic selection of states.
            * logStatusWarning          : Log messages when returning fmi2Warning status from any function.
            * logStatusDiscard          : Log messages when returning fmi2Discard status from any function.
            * logStatusError            : Log messages when returning fmi2Error status from any function.
            * logStatusFatal            : Log messages when returning fmi2Fatal status from any function.
            * logStatusPending          : Log messages when returning fmi2Pending status from any function.
            * logAll                    : Log all messages.

            The standard standard leaves it up to the implementation to decide which "categories" map to each of the log-categories.

            ``` Python
            self.log(Fmi2Status.OK,"events","initialized FMU")
            ```

        Examples:
        ``` Python
            # standard logging
            fmu = MyFMU()
            fmu.register_standard_log_catgories()
            fmu.__set_debug_logging__({'LogAll'})

            fmu.log(Fmi2Status.ok,'logEvents',)

        ```
        """

       
        
    def log(self, message : str, category : str,status: Fmi2Status) -> None:
        """Logs a message to the fmi interface.

        Note that only categories which are set as active using the __set_debug_logging__, are propageted to the tool.
        The function is called by the tool using with the categories which the user wishes to be active.
        
        Arguments:
            status {Fmi2Status} -- The current status of the FMU.
            category {str} -- The category of the log message.
            message {str} -- The log message itself.

        Logging categories mappings:


        """

        self.logger.log(status,category,message)
            
    def __get_log_messages__(self):
        pass

    def __get_log_size__(self) -> int:
        """Returns the number of log messages that are currently on the log stack.

        Returns:
            int -- [description]
        """
        return None

    def __get_integer__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_integer():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Integer!")

    def __get_real__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_real():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Real!")

    def __get_boolean__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_boolean():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Boolean!")

    def __get_string__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_string():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type String!")

    def __set_integer__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_integer:
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Integer!")

    def __set_real__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_real():
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Real!")

    def __set_boolean__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_boolean():
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Boolean!")

    def __set_string__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_string():
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type String!")

    def _define_variable(self, sv : ScalarVariable):
        
        
        if(not hasattr(self,sv.name)):
            log.debug(f'adding')
             
            setattr(self,sv.name,sv.start)

            
        else:
            old = getattr(self,sv.name)
            new = sv.start

            if(old != new):
                log.warning("start value variable defined using the 'register_variable' function does not match initial value")
                setattr(self,sv.name,new)

    def _acquire_unused_value_reference(self) -> int:
        """ Returns the an unused value reference
        """
        while(True):
            vr = self.value_reference_counter
            self.value_reference_counter += 1

            if(vr not in self.used_value_references):
                return vr