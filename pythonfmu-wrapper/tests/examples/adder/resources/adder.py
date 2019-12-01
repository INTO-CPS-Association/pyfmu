from fmi2slave import Fmi2Slave, Real, Fmi2Causality, Fmi2Variability

slave_class = "Adder"

class Adder(Fmi2Slave):

    Fmi2Slave.author = "Christian Legaard"
    Fmi2Slave.modelName = "Adder"
    Fmi2Slave.description = "Adds two real numbers"


    def __init__(self):
        
        

        super().__init__()

        
        

        self.a = 0
        self.b = 0

        self.register_variable(Real("a").set_causality(Fmi2Causality.input))
        self.register_variable(Real("b").set_causality(Fmi2Causality.input))

        self.c = 0    
        self.register_variable(Real("c").set_causality(Fmi2Causality.output))

    def do_step(self, current_time: float, step_size: float) -> bool:
        
        self.c = self.a + self.b
        
        return True