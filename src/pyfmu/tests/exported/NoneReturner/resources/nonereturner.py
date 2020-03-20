from pyfmu.fmi2 import Fmi2Slave,Fmi2Causality, Fmi2Variability,Fmi2DataTypes,Fmi2Initial

class NoneReturner(Fmi2Slave):
    """ FMU which returns invalid types
    
    """

    def __init__(self):
        
        author = ""
        modelName = "NoneReturner"
        description = ""    
        
        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

    
        
        self.register_variable("real", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.output)
        self.register_variable("integer", data_type=Fmi2DataTypes.integer, causality = Fmi2Causality.output,variability=Fmi2Variability.discrete)
        self.register_variable("boolean", data_type=Fmi2DataTypes.boolean, causality = Fmi2Causality.output,variability=Fmi2Variability.discrete)
        self.register_variable("string", data_type=Fmi2DataTypes.string, causality = Fmi2Causality.output,variability=Fmi2Variability.discrete)
        
        
        # return None for all 
        self.real = None
        self.integer = None
        self.boolean = None
        self.string = None
        
        

    def setup_experiment(self, start_time: float):
        pass

    def enter_initialization_mode(self):
        pass

    def exit_initialization_mode(self):
        pass

    def do_step(self, current_time: float, step_size: float) -> bool:
        return True

    def reset(self):
        pass

    def terminate(self):
        pass