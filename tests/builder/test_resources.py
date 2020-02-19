from fmpy.ssp.simulation import simulate_ssp
from fmpy.simulation import simulate_fmu

from ..examples.example_finder import get_available_examples, ExampleProject

"""This file contains tests related to how the Python FMU manages resources.

For ease of testing fmpy is used as a cosimulation engine.
"""


def test_singleInstantiation_canSimulate():
    
    with ExampleProject('Adder') as archive:

        # seems like fmpy does not accept Path objects
        path = str(archive.root)

        simulate_fmu(path)
    
    
    


def test_multiple_instantiations():

    for pname in get_available_examples():
        
        with ExampleProject(pname) as archive:

            # seems like fmpy does not accept Path objects
            path = str(archive.root)

            simulate_fmu(path)