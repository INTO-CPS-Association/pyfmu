from pyfmu.fmi2slave import Fmi2Slave
from pyfmu.fmi2types import Fmi2Causality, Fmi2Variability, Fmi2DataTypes

class ConstantSignalGenerator(Fmi2Slave):

    def __init__(self):
        
        author = ""
        modelName = "ConstantSignalGenerator"
        description = ""    
        
        super().__init__(
            modelName=modelName,
            author=author,
            description=description)


        self.register_variable("y",data_type=Fmi2DataTypes.real,causality=Fmi2Causality.output)
        self.register_variable("k",data_type=Fmi2DataTypes.real,causality=Fmi2Causality.parameter,variability=Fmi2Variability.fixed, start=0)


    def exit_initialization_mode(self):
        self.y = self.k

    def do_step(self, current_time: float, step_size: float) -> bool:
        self.y = self.k
        return True