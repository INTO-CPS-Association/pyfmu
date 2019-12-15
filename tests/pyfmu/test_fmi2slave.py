from libs.pyfmu.fmi2slave import Fmi2Slave
from libs.pyfmu.fmi2types import Fmi2DataTypes, Fmi2Causality

class Adder(Fmi2Slave):
    
    def __init__(self):
        super().__init__("Adder")

        self.register_variable("a", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("b", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("c", data_type=Fmi2DataTypes.real,causality = Fmi2Causality.output)

class Tests_fmi2Slave:
    
    def test_register_variable_implicitly_defines_attribute(self):

        a = Adder()

        assert(hasattr(a,'a'))
        assert(hasattr(a,'b'))
        assert(hasattr(a,'c'))

        assert(a.a == 0)
        assert(a.b == 0)

        

    
    pass