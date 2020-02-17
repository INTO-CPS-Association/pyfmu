import pytest

from pybuilder.libs.pyfmu.fmi2variables import ScalarVariable
from pybuilder.libs.pyfmu.fmi2types import Fmi2Initial, Fmi2DataTypes, Fmi2Causality, Fmi2Variability

def test_defaultCausality_isLocal():
    v = ScalarVariable("a",data_type=Fmi2DataTypes.real)
    assert(v.causality == Fmi2Causality.local)

def test_defaultVariability_isContinous():
    v = ScalarVariable("a",data_type=Fmi2DataTypes.real)
    assert(v.variability == Fmi2Variability.continuous)

def test_input_initialNotAllowed():

    with pytest.raises(Exception):
        v = ScalarVariable("a",data_type=Fmi2DataTypes.real,causality=Fmi2Causality.input,initial=Fmi2Initial.exact)

    with pytest.raises(Exception):
        v = ScalarVariable("a",data_type=Fmi2DataTypes.real,causality=Fmi2Causality.input,initial=Fmi2Initial.approx)

    with pytest.raises(Exception):
        v = ScalarVariable("a",data_type=Fmi2DataTypes.real,causality=Fmi2Causality.input,initial=Fmi2Initial.calculated)

def test_approx_startDefined_NOK():
    with pytest.raises(Exception):
        ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.approx)

def test_approx_startNotDefined_OK():
    ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.approx, start=0)

def test_initialIsCalculated_startDefined_NOK():
    with pytest.raises(Exception):
        ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.calculated,start=0)

def test_initialIsCalculated_startNotDefined_OK():
    ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.calculated)
    
def test_initialIsExact_startNotDefined_NOK():
    with pytest.raises(Exception):
        ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.exact)
    
def test_initialIsExact_startDefined_NOK():
    
    ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.exact, start=0)

def test_input_startNotDefined_NOK():
    with pytest.raises(Exception):
        ScalarVariable("a",causality=Fmi2Causality.input,data_type=Fmi2DataTypes.real)

def test_input_startDefined_OK():
    ScalarVariable("a",causality=Fmi2Causality.input,data_type=Fmi2DataTypes.real, start=0)

# Output valid start values

def test_output_exact_startDefined_OK():
    ScalarVariable('a',causality=Fmi2Causality.output,initial=Fmi2Initial.exact, data_type=Fmi2DataTypes.real, start=0)

def test_output_exact_startUndefined_NOK():
    with pytest.raises(Exception):
        ScalarVariable('a',causality=Fmi2Causality.output, initial=Fmi2Initial.exact, data_type=Fmi2DataTypes.real)

def test_output_calculated_startDefined_NOK():
    with pytest.raises(Exception):
        ScalarVariable('a',causality=Fmi2Causality.output,initial=Fmi2Initial.calculated, data_type=Fmi2DataTypes.real, start=0)

def test_output_calculated_startUndefined_OK():
    ScalarVariable('a',causality=Fmi2Causality.output,initial=Fmi2Initial.calculated, data_type=Fmi2DataTypes.real)


def test_output_approx_startDefined_OK():
    ScalarVariable('a',causality=Fmi2Causality.output, initial=Fmi2Initial.approx, data_type=Fmi2DataTypes.real, start=0)
 
def test_output_approx_startUndefined_NOK():
    with pytest.raises(Exception):
        ScalarVariable('a',causality=Fmi2Causality.output, initial=Fmi2Initial.approx, data_type=Fmi2DataTypes.real)