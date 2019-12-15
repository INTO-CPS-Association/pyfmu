from pyfmu.fmi2slave import Fmi2Slave
from pyfmu.fmi2types import Fmi2Causality, Fmi2Variability, Fmi2DataTypes

from math import sin

class SineGenerator(Fmi2Slave):

    def __init__(self):

        author = ""
        modelName = "SineGenerator"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

        self.register_variable("amplitude", data_type=Fmi2DataTypes.real,
                               variability=Fmi2Variability.fixed, causality=Fmi2Causality.parameter, start=1)
                               
        self.register_variable("frequency", data_type=Fmi2DataTypes.real,
                               variability=Fmi2Variability.fixed, causality=Fmi2Causality.parameter, start=1)

        self.register_variable(
            "phase", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.parameter, variability = Fmi2Variability.fixed, start=0)

        self.register_variable(
            "y", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.output, start=0)

    def do_step(self, current_time: float, step_size: float):
        
        self.y = self.amplitude * sin(current_time * self.frequency + self.phase)


