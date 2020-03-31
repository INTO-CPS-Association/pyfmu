from pyfmu.fmi2 import Fmi2Slave, Fmi2DataTypes, Fmi2Causality, Fmi2Variability, Fmi2Status, Fmi2Initial,Fmi2StdLogCats


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

    result = [0.0]
    s = d._get_real([vr],result)

    assert(s == Fmi2Status.ok.value)
    assert(result[0] == start)

def test_parametersUseStartValue():
    d = Dummy()

    start = 10
    vr = 0

    d.register_variable("a",data_type=Fmi2DataTypes.real,variability=Fmi2Variability.fixed,causality = Fmi2Causality.parameter,start=start,value_reference=vr)

    result = [0.0]

    s = d._get_real([vr],result)
    assert(s == Fmi2Status.ok.value)
    assert(result[0] == start)

def test_registerVariable_acceptsStrings():

    slave = Fmi2Slave("")

    valid_combinations = {
        ('real','input','continuous',None),
        ('real','output','continuous','exact')
    }

    for data_type,causality,variability,initial in valid_combinations:
        slave.register_variable("a",data_type=data_type,causality=causality,variability=variability,initial=initial,start=0)

def test_registerVariable_infersDataTypeFromStart():

    s = Fmi2Slave("")
    s.register_variable('a',causality='input',start=1.0)
    matches = [v for v in s.vars if v.data_type is Fmi2DataTypes.real]

    assert(len(matches) is 1)


def test_registerVariable_defaultStartValues():

    s = Fmi2Slave("")

    # exact should apply default values
    s.register_variable('re','real',initial='exact')
    s.register_variable('ie','integer',variability='discrete',initial='exact')
    s.register_variable('be','boolean',variability='discrete',initial='exact')
    s.register_variable('se','string',variability='discrete',initial='exact')

    assert(s.re == 0.0)
    assert(s.ie == 0)
    assert(s.be == False)
    assert(s.se == "")

    v_re = [v for v in s.vars if v.name == 're']
    v_ie = [v for v in s.vars if v.name == 'ie']
    v_be = [v for v in s.vars if v.name == 'be']
    v_se = [v for v in s.vars if v.name == 'se']

    assert(len(v_re) == 1)
    assert(len(v_ie) == 1)
    assert(len(v_be) == 1)
    assert(len(v_se) == 1)

    # approx should also apply default values

    s.register_variable('ra','real',initial='approx')
    s.register_variable('ia','integer',variability='discrete',initial='approx')
    s.register_variable('ba','boolean',variability='discrete',initial='approx')
    s.register_variable('sa','string',variability='discrete',initial='approx')

    assert(s.ra == 0.0)
    assert(s.ia == 0)
    assert(s.ba == False)
    assert(s.sa == "")

    v_ra = [v for v in s.vars if v.name == 'ra']
    v_ia = [v for v in s.vars if v.name == 'ia']
    v_ba = [v for v in s.vars if v.name == 'ba']
    v_sa = [v for v in s.vars if v.name == 'sa']

    assert(len(v_ra) == 1)
    assert(len(v_ia) == 1)
    assert(len(v_ba) == 1)
    assert(len(v_sa) == 1)


def test_setXXX_onlyAcceptsCorrectType():


    fmu = Fmi2Slave("")

    fmu.register_variable("r",'real','input')
    fmu.register_variable("i",'integer','input','discrete')
    fmu.register_variable("b",'boolean','input','discrete')
    fmu.register_variable("s",'string','input','discrete')

    combinations = {
        'real' : {0.0, 1.0},
        'integer' : {1,0},
        'boolean' : {True,False},
        'string' : {"", "hello world!"}
    }

    s = fmu._set_real([0],[0.0]) # integer is incorrect
    assert(s == Fmi2Status.ok.value)

    for i,(func,t) in enumerate([
        (fmu._set_real,'real'),
        (fmu._set_integer,'integer'),
        (fmu._set_boolean,'boolean'),
        (fmu._set_string,'string')]):

        not_valid = set()

        for c in [k for k in combinations if k != t]:
            not_valid.update(combinations[c])

        for valid in combinations[t]:
            s = func([i],[valid])
            assert s == Fmi2Status.ok.value

