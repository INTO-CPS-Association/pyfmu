import pytest
from pyfmu.fmi2 import Fmi2ScalarVariable, Fmi2Initial, Fmi2DataTypes, Fmi2Causality, Fmi2Variability


def test_defaultCausality_isLocal():
    v = Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real)
    assert(v.causality == Fmi2Causality.local)


def test_defaultVariability_isContinous():
    v = Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real)
    assert(v.variability == Fmi2Variability.continuous)


def test_input_initialNotAllowed():

    with pytest.raises(Exception):
        v = Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                           causality=Fmi2Causality.input, initial=Fmi2Initial.exact)

    with pytest.raises(Exception):
        v = Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                           causality=Fmi2Causality.input, initial=Fmi2Initial.approx)

    with pytest.raises(Exception):
        v = Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                           causality=Fmi2Causality.input, initial=Fmi2Initial.calculated)


def test_approx_startDefined_NOK():
    with pytest.raises(Exception):
        Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                       initial=Fmi2Initial.approx)


def test_approx_startNotDefined_OK():
    Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                   initial=Fmi2Initial.approx, start=0)


def test_initialIsCalculated_startDefined_NOK():
    with pytest.raises(Exception):
        Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                       initial=Fmi2Initial.calculated, start=0)


def test_initialIsCalculated_startNotDefined_OK():
    Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                   initial=Fmi2Initial.calculated)


def test_initialIsExact_startNotDefined_NOK():
    with pytest.raises(Exception):
        Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                       initial=Fmi2Initial.exact)


def test_initialIsExact_startDefined_NOK():

    Fmi2ScalarVariable("a", data_type=Fmi2DataTypes.real,
                   initial=Fmi2Initial.exact, start=0)


def test_input_startNotDefined_NOK():
    with pytest.raises(Exception):
        Fmi2ScalarVariable("a", causality=Fmi2Causality.input,
                       data_type=Fmi2DataTypes.real)


def test_input_startDefined_OK():
    Fmi2ScalarVariable("a", causality=Fmi2Causality.input,
                   data_type=Fmi2DataTypes.real, start=0)


def test_dataTypeAndStartTypeMismatch_NOK():


    type_to_invalidStartValues = {
        Fmi2DataTypes.real: {
            '', True, False
        },
        Fmi2DataTypes.boolean: {
            '', 1, 0, 0.5
        },
        Fmi2DataTypes.integer: {
            '', True, False, 0.5, 1.5
        }}

  

    with pytest.raises(TypeError):
        for t, ss in type_to_invalidStartValues.items():
            for s in ss:
                Fmi2ScalarVariable("",data_type = t,causality=Fmi2Causality.input,start=s) 

# Output valid start values

def test_output_exact_startDefined_OK():
    Fmi2ScalarVariable('a', causality=Fmi2Causality.output,
                   initial=Fmi2Initial.exact, data_type=Fmi2DataTypes.real, start=0)


def test_output_exact_startUndefined_NOK():
    with pytest.raises(Exception):
        Fmi2ScalarVariable('a', causality=Fmi2Causality.output,
                       initial=Fmi2Initial.exact, data_type=Fmi2DataTypes.real)


def test_output_calculated_startDefined_NOK():
    with pytest.raises(Exception):
        Fmi2ScalarVariable('a', causality=Fmi2Causality.output,
                       initial=Fmi2Initial.calculated, data_type=Fmi2DataTypes.real, start=0)


def test_output_calculated_startUndefined_OK():
    Fmi2ScalarVariable('a', causality=Fmi2Causality.output,
                   initial=Fmi2Initial.calculated, data_type=Fmi2DataTypes.real)


def test_output_approx_startDefined_OK():
    Fmi2ScalarVariable('a', causality=Fmi2Causality.output,
                   initial=Fmi2Initial.approx, data_type=Fmi2DataTypes.real, start=0)


def test_output_approx_startUndefined_NOK():
    with pytest.raises(Exception):
        Fmi2ScalarVariable('a', causality=Fmi2Causality.output,
                       initial=Fmi2Initial.approx, data_type=Fmi2DataTypes.real)
