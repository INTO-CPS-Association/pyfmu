from fmpy import *

from ...examples.example_finder import get_exported_example_project

import numpy as np


class Tests_fmpy:
    
    def test_SineGenerator(self):
        p = get_exported_example_project('SineGenerator')
        res = simulate_fmu(p)


    def test_ConstantSignalSource(self):
        p = get_exported_example_project('ConstantSignalSource')
        res = simulate_fmu(p)


        
    def test_Adder(self):
        p = get_exported_example_project('Adder')
        res = simulate_fmu(p)
        