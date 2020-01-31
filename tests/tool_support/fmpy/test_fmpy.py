from fmpy import *

from ...examples.example_finder import get_example_project




class Tests_fmpy:
    
    def test_register_variable_implicitly_defines_attribute(self):
        p = get_example_project('SineGenerator')

        simulate_fmu(p)

        
        
        