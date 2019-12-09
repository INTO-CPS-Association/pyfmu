from abc import ABC, abstractmethod
from uuid import uuid1
from .fmi2types import Fmi2Causality, Fmi2DataTypes, Fmi2Initial, Fmi2Variability
from .fmi2variables import ScalarVariable


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

    def register_variable(self,
                          name: str,
                          data_type: Fmi2DataTypes,
                          causality = Fmi2Causality.local,
                          variability = Fmi2Variability.continuous,
                          initial : Fmi2Initial = None,
                          start = None,
                          description: str = ""):
                          

        var = ScalarVariable(name=name, data_type=Fmi2DataTypes.real, initial=initial, causality=causality,
                             variability=variability, description=description, start = start)

        self.vars.append(var)

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
