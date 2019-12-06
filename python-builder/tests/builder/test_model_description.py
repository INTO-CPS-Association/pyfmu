from libs.pyfmu.fmi2slave import Fmi2Slave
from libs.pyfmu.fmi2types import Fmi2DataTypes, Fmi2Causality, Fmi2Variability

from libs.builder.modelDescription import extract_model_description_v2

class Adder(Fmi2Slave):
    
    

    def __init__(self):
        super().__init__("Adder")

        self.register_variable("a", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("b", data_type=Fmi2DataTypes.real, causality = Fmi2Causality.input, start=0)
        self.register_variable("c", data_type=Fmi2DataTypes.real,causality = Fmi2Causality.output)

        


def test_extract_model_description_v2():
    

    a = Adder()
    
    md = extract_model_description_v2(a)

    with open("test.xml",'w') as f:
        f.write(md)

