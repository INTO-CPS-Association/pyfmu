from abc import ABC, abstractmethod
from uuid import uuid1
from .fmi2types import Fmi2Causality, Fmi2DataTypes, Fmi2Initial, Fmi2Variability
from .fmi2variables import ScalarVariable

import logging


log = logging.getLogger('fmu')

class Fmi2Slave:
    
    guid = uuid1()
    author = None
    license = None
    version = None
    copyright = None
    modelName = None
    description = None

    def __init__(self, modelName: str, author="", copyright="", version="", description=""):

        self.author = author
        self.copyright = copyright
        self.description = description
        self.modelName = modelName
        self.vars = []
        self.version = version
        self.value_reference_counter = 0
        self.used_value_references = {}

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

    def setup_experiment(self, start_time: float):
        pass

    def enter_initialization_mode(self):
        pass

    def exit_initialization_mode(self):
        pass

    @abstractmethod
    def do_step(self, current_time: float, step_size: float) -> bool:
        pass

    def reset(self):
        pass

    def terminate(self):
        pass

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