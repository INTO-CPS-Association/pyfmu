from pyfmu.fmi2slave import Fmi2Slave
from pyfmu.fmi2types import Fmi2Causality, Fmi2Variability, Fmi2DataTypes, Fmi2Initial

class LoggerFMU(Fmi2Slave):

    def __init__(self):

        author = ""
        modelName = "LoggerFMU"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description)


        self.register_variable("s", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.output)
        self.register_variable("a", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0)
        self.register_variable("b", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0)


    def exit_initialization_mode(self):

        self.s = self.a + self.b

        self.log(f"inputs was set to {self.a} {self.b}, output is {self.s}")


        return True

    def do_step(self, current_time: float, step_size: float) -> bool:
        
        self.log("Stepping!")

        self.s = self.a + self.b
        return True
