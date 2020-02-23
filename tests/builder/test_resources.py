from fmpy.simulation import simulate_fmu, FMU2Slave
from fmpy.model_description import read_model_description

from ..examples.example_finder import get_available_examples, ExampleArchive

"""This file contains tests related to how the Python FMU manages resources.

For ease of testing fmpy is used as a cosimulation engine.
"""


def test_singleInstantiation_canSimulate():
    
    with ExampleArchive('Adder') as archive:

        # seems like fmpy does not accept Path objects
        path = str(archive.root)

        simulate_fmu(path)
    
    
    


def test_multipleExports_canSimulate():

    for pname in get_available_examples():
        
        with ExampleArchive(pname) as archive:
            
            print(archive.model_description)
            # seems like fmpy does not accept Path objects
            path = str(archive.root)

            simulate_fmu(path)


def test_multipleInstantiations_canSimulate():

    for idx, pname in enumerate(get_available_examples()):
        
        with ExampleArchive(pname) as archive:
            
            print(archive.model_description)
            # seems like fmpy does not accept Path objects
            path = str(archive.root)

            md = read_model_description(str(archive.root))

            instance_name = str(idx)

            fmu = FMU2Slave(guid=md.guid,
                        unzipDirectory=archive.root,
                        modelIdentifier=md.coSimulation.modelIdentifier,
                        instanceName=instance_name,
                        fmiCallLogger=None)

            a = fmu.instantiate()
            b = fmu.instantiate()
            c = fmu.instantiate()