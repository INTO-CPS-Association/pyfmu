from fmi2slave import Fmi2Slave, Real, Fmi2Causality, Fmi2Variability

slave_class = "Adder"

class Adder(Fmi2Slave):

    def __init__(self):
        
        author = ""
        modelName = "Adder"
        description = "Adds two real numbers"
        super().__init__(author = author, modelName = modelName, )

        
        

        self.a = 0
        self.b = 0

        self.register_variable(Real("a").set_causality(Fmi2Causality.input))
        self.register_variable(Real("b").set_causality(Fmi2Causality.input))

        self.c = 0    
        self.register_variable(Real("c").set_causality(Fmi2Causality.output))

    def do_step(self, current_time: float, step_size: float) -> bool:
        
        self.c = self.a + self.b
        
        return True