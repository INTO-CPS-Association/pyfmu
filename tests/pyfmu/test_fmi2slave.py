from pybuilder.libs.pyfmu.fmi2slave import Fmi2Slave
from pybuilder.libs.pyfmu.fmi2types import Fmi2DataTypes, Fmi2Causality, Fmi2Variability

class Adder(Fmi2Slave):
    
    def __init__(self):
        super().__init__("Adder")

        self.register_variable("a", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("b", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("c", data_type=Fmi2DataTypes.real,causality = Fmi2Causality.output)

class Dummy(Fmi2Slave):

    def __init__(self):
        super().__init__("Dummy")

class Tests_fmi2Slave:
    
    def test_register_variable_implicitly_defines_attribute(self):

        a = Adder()

        assert(hasattr(a,'a'))
        assert(hasattr(a,'b'))
        assert(hasattr(a,'c'))

        assert(a.a == 0)
        assert(a.b == 0)


def test_inputsUseStartValue():
    
    d = Dummy()
    
    start = 10
    vr = 0

    d.register_variable("a",data_type = Fmi2DataTypes.real,causality=Fmi2Causality.input, start=start,value_reference=vr)

    result = [0]

    d.__get_real__([vr],result)
    assert(result[0] == start)

def test_parametersUseStartValue():
    d = Dummy()

    start = 10
    vr = 0

    d.register_variable("a",data_type=Fmi2DataTypes.real,variability=Fmi2Variability.fixed,causality = Fmi2Causality.parameter,start=start,value_reference=vr)

    result = [0]

    d.__get_real__([vr],result)
    assert(result[0] == start)

def test_inputsSetOverridesStart():

    d = Dummy()

    start = 10
    vr = 0
    d.register_variable("a",data_type)