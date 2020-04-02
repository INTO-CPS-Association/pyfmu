from pyfmu.fmi2 import Fmi2Slave,Fmi2Causality, Fmi2Variability,Fmi2DataTypes,Fmi2Initial

class ConstantSignalGenerator(Fmi2Slave):

    def __init__(self, *args, **kwargs):
        
        author = ""
        modelName = "ConstantSignalGenerator"
        description = ""    
        
        super().__init__(
            modelName=modelName,
            author=author,
            description=description,
            *args,
            **kwargs
            )


        self.register_variable("y",data_type=Fmi2DataTypes.real,causality=Fmi2Causality.output)
        self.register_variable("k",data_type=Fmi2DataTypes.real,causality=Fmi2Causality.parameter,variability=Fmi2Variability.fixed, start=0.0)


    def exit_initialization_mode(self):
        self.y = self.k

    def do_step(self, current_time: float, step_size: float, no_prior_step : bool):
        self.y = self.k
        return True