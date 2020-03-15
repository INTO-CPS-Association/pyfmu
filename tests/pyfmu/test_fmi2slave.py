from pybuilder.resources.pyfmu.fmi2slave import Fmi2Slave
from pybuilder.resources.pyfmu.fmi2types import Fmi2DataTypes, Fmi2Causality, Fmi2Variability, Fmi2Status,Fmi2Initial

from pybuilder.resources.pyfmu.fmi2logging import Fmi2StdLogCats

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

def test_registerVariable_acceptsStrings():

    slave = Fmi2Slave("")

    valid_combinations = {
        ('real','input','continuous',None),
        ('real','output','continuous','exact')
    }

    for c in valid_combinations:
        data_type,causality,variability,initial = c
        slave.register_variable("a",data_type=data_type,causality=causality,variability=variability,initial=initial,start=0)

def test_registerVariable_infersDataTypeFromStart():
    raise NotImplementedError()


# test logging functions used by the wrapper


def test_setDebugLogging():

    fmu = Fmi2Slave("a")

    fmu.log("test")
    
    assert(fmu.__get_log_size__() == 0)

    fmu.__set_debug_logging__(True,["logAll"])

    fmu.log("test")

    assert(fmu.__get_log_size__() == 1)
    

def test__get_log_size__():
    
    fmu = Fmi2Slave("logger",standard_log_categories=True)
    fmu.__set_debug_logging__(True,["logAll"])

    fmu.log("test 1")
    
    assert(fmu.__get_log_size__() == 1)
    
    fmu.log("test 2")

    assert(fmu.__get_log_size__() == 2)


def test__get_log_messages__():

    fmu = Fmi2Slave("logger", standard_log_categories=True)
    fmu.__set_debug_logging__(True,["logAll"])

    fmu.log("test",category="a",status=Fmi2Status.ok)

    ms = fmu.__pop_log_messages__(1)

    (status,category,message) = ms[0]

    assert(status == Fmi2Status.ok.value)
    assert(isinstance(status,int))
    assert(category == "a")
    assert(message == 'test')
