from pyfmu.fmi2slave import Fmi2Slave
from pyfmu.fmi2types import Fmi2Causality, Fmi2Variability, Fmi2DataTypes

class Adder(Fmi2Slave):

    def __init__(self):
        
        author = ""
        modelName = "Adder"
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
        return True

    def do_step(self, current_time: float, step_size: float) -> bool:
        self.s = self.a + self.b
        return True
