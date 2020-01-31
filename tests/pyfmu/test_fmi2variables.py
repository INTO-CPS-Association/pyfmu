import pytest

from pybuilder.libs.pyfmu.fmi2variables import ScalarVariable
from pybuilder.libs.pyfmu.fmi2types import Fmi2Initial, Fmi2DataTypes, Fmi2Causality

def test_initialApprox_startDefined_throwsError():
    with pytest.raises(Exception):
        v = ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.approx)

def test_initialApprox_startNotDefined_OK():
    ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.approx, start=0)

def test_initialIsCalculated_startDefined_throwsError():
    with pytest.raises(Exception):
        v = ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.calculated,start=0)

def test_initialIsCalculated_startNotDefined_OK():
    ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.calculated)
    
def test_initialIsExact_startNotDefined_throwsError():
    with pytest.raises(Exception):
        v = ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.exact)
    
def test_initialIsExact_startDefined_throwsError():
    
    ScalarVariable("a",data_type=Fmi2DataTypes.real, initial=Fmi2Initial.exact, start=0)

def test_causalityInput_startNotDefined_throwsError():
    with pytest.raises(Exception):
        v = ScalarVariable("a",causality=Fmi2Causality.input,data_type=Fmi2DataTypes.real)

def test_causalityInput_startDefined_OK():
    
    ScalarVariable("a",causality=Fmi2Causality.input,data_type=Fmi2DataTypes.real, start=0)


