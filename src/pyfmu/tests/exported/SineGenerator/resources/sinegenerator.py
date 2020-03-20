from math import sin

from pyfmu.fmi2 import Fmi2Slave,Fmi2Causality, Fmi2Variability,Fmi2DataTypes,Fmi2Initial

class SineGenerator(Fmi2Slave):

    def __init__(self):

        author = ""
        modelName = "SineGenerator"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

        self.register_variable("amplitude", data_type=Fmi2DataTypes.real, variability=Fmi2Variability.fixed, causality=Fmi2Causality.parameter, start=1)
        self.register_variable("frequency", data_type=Fmi2DataTypes.real, variability=Fmi2Variability.fixed, causality=Fmi2Causality.parameter, start=1)
        self.register_variable("phase", data_type=Fmi2DataTypes.real, variability = Fmi2Variability.fixed, causality=Fmi2Causality.parameter, start=0)

        self.register_variable("y", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.output)

    def setup_experiment(self, start_time: float):
        self.start_time = start_time
        return True

    def exit_initialization_mode(self) -> bool:
        self.y = self.amplitude * sin(self.start_time * self.frequency + self.phase)
        return True

    def do_step(self, current_time: float, step_size: float):
        
        self.y = self.amplitude * sin(current_time * self.frequency + self.phase)
        return True


