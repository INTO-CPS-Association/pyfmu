from fmpy import *

from ...examples.example_finder import get_exported_example_project

import numpy as np


class Tests_fmpy:
    
    def test_SineGenerator(self):
        p = get_exported_example_project('SineGenerator')
        _ = simulate_fmu(p)


    def test_ConstantSignalSource(self):
        p = get_exported_example_project('ConstantSignalGenerator')
        _ = simulate_fmu(p)


        
    def test_Adder(self):
        p = get_exported_example_project('Adder')
        _ = simulate_fmu(p)
        