"""This file contains tests related to how the Python FMU manages resources.

For ease of testing fmpy is used as a cosimulation engine.
"""
from ctypes import cdll
import platform

import pytest
from fmpy.simulation import simulate_fmu, FMU2Slave
from fmpy.model_description import read_model_description

from pyfmu.tests import get_all_examples, get_correct_examples, get_incorrect_examples, ExampleArchive
from pyfmu.resources import Resources



def test_shared_library_can_be_loaded():

    sys = platform.system()

    for pname in get_all_examples():

        with ExampleArchive(pname) as archive:

            if(sys == 'Windows'):
                p = archive.wrapper_win64
            elif(sys == 'Linux'):
                p = archive.wrapper_linux64
            else:
                raise NotImplementedError(f'Not implemented for platform {sys}')

            p = str(p.resolve())

            cdll.LoadLibrary(p)


def test_singleInstantiation_canSimulate():

    for pname in get_correct_examples():

        with ExampleArchive(pname) as archive:

            # seems like fmpy does not accept Path objects
            path = str(archive.root.resolve())

            simulate_fmu(path)


def test_multipleExports_canSimulate():

    for pname in get_correct_examples():

        with ExampleArchive(pname) as archive:

            print(archive.model_description)
            # seems like fmpy does not accept Path objects
            path = str(archive.root.resolve())

            simulate_fmu(path)



def test_multipleInstantiationsAllDifferentInstanceNames_canSimulate():

    for idx, pname in enumerate(get_correct_examples()):

        with ExampleArchive(pname) as archive:

            print(archive.model_description)
            # seems like fmpy does not accept Path objects
            path = str(archive.root)

            md = read_model_description(str(archive.root))

            instance_a = str(idx) + 'a'
            instance_b = str(idx) + 'b'

            fmu_a = FMU2Slave(guid=md.guid,
                              unzipDirectory=archive.root,
                              modelIdentifier=md.coSimulation.modelIdentifier,
                              instanceName=instance_a,
                              fmiCallLogger=None)

            fmu_b = FMU2Slave(guid=md.guid,
                              unzipDirectory=archive.root,
                              modelIdentifier=md.coSimulation.modelIdentifier,
                              instanceName=instance_b,
                              fmiCallLogger=None)

            fmu_a.instantiate()
            fmu_b.instantiate()


def atest_identicalNamesSameTypes_throws():

    with pytest.raises(Exception):
        with ExampleArchive('Adder') as a, ExampleArchive('Adder') as b:

            md_a = read_model_description(str(b.root))
            md_b = read_model_description(str(a.root))

            instance_a = 'a'
            instance_b = 'a'

            fmu_a = FMU2Slave(guid=md_a.guid,
                              unzipDirectory=a.root,
                              modelIdentifier=md_a.coSimulation.modelIdentifier,
                              instanceName=instance_a,
                              fmiCallLogger=None)

            fmu_b = FMU2Slave(guid=md_b.guid,
                              unzipDirectory=b.root,
                              modelIdentifier=md_b.coSimulation.modelIdentifier,
                              instanceName=instance_b,
                              fmiCallLogger=None)

            fmu_a.instantiate()
            fmu_b.instantiate()


def atest_identicalNamesDifferentTypes_throws():

    with pytest.raises(Exception):
        with ExampleArchive('Adder') as a, ExampleArchive('ConstantSignalGenerator') as b:

            md_a = read_model_description(str(b.root))
            md_b = read_model_description(str(a.root))

            instance_a = 'a'
            instance_b = 'a'

            fmu_a = FMU2Slave(guid=md_a.guid,
                              unzipDirectory=a.root,
                              modelIdentifier=md_a.coSimulation.modelIdentifier,
                              instanceName=instance_a,
                              fmiCallLogger=None)

            fmu_b = FMU2Slave(guid=md_b.guid,
                              unzipDirectory=b.root,
                              modelIdentifier=md_b.coSimulation.modelIdentifier,
                              instanceName=instance_b,
                              fmiCallLogger=None)

            fmu_a.instantiate()
            fmu_b.instantiate()


def test_Adder():
    with ExampleArchive('Adder') as a:

        md_a = read_model_description(str(a.root))

        instance_a = 'a'

        fmu_a = FMU2Slave(guid=md_a.guid,
                            unzipDirectory=a.root,
                            modelIdentifier=md_a.coSimulation.modelIdentifier,
                            instanceName=instance_a,
                            fmiCallLogger=None)


        fmu_a.instantiate()
        # set input a
        fmu_a.setReal([1],[1])
        # set input b
        fmu_a.setReal([2],[2])

        fmu_a.doStep(0,1)

        # read output
        s = fmu_a.getReal([0])[0]
        assert s == 3

def test_bicycle():
    with ExampleArchive('BicycleKinematic') as a:

        md_a = read_model_description(str(a.root))


        fmu_a = FMU2Slave(guid=md_a.guid,
                            unzipDirectory=a.root,
                            modelIdentifier=md_a.coSimulation.modelIdentifier,
                            instanceName='a',
                            fmiCallLogger=None)

        fmu_a.instantiate()
        fmu_a.doStep(0,1)

