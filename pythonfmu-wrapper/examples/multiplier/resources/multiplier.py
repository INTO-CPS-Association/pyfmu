from pyfmu.fmi2slave import Fmi2Slave
from pyfmu.fmi2types import Fmi2Causality, Fmi2Variability, Fmi2DataTypes

class Multiplier(Fmi2Slave):

    def __init__(self):
        
        author = ""
        modelName = "Multiplier"
        description = ""    
        
        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

        self.register_variable("a", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("b", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("c", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.output, start=0)


    def setup_experiment(self, start_time: float):
        pass

    def enter_initialization_mode(self):
        pass

    def exit_initialization_mode(self):
        pass

    def do_step(self, current_time: float, step_size: float) -> bool:
        
        self.c = self.a * self.b

        return True

    def reset(self):
        pass

    def terminate(self):
        pass