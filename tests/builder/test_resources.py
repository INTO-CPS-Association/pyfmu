from fmpy.ssp.simulation import simulate_ssp
from fmpy.simulation import simulate_fmu

from ..examples.example_finder import get_available_examples, ExampleArchive

"""This file contains tests related to how the Python FMU manages resources.

For ease of testing fmpy is used as a cosimulation engine.
"""


def test_singleInstantiation_canSimulate():
    
    with ExampleArchive('Adder') as archive:

        # seems like fmpy does not accept Path objects
        path = str(archive.root)

        simulate_fmu(path)
    
    
    


def test_multipleInstantiations_canSimulate():

    for pname in get_available_examples():
        
        with ExampleArchive(pname) as archive:
            
            print(archive.model_description)
            # seems like fmpy does not accept Path objects
            path = str(archive.root)

            # AHA. problem is that 
            # export A -> increment vref counter
            # simulate A -> increment vref counter. 

            simulate_fmu(path)