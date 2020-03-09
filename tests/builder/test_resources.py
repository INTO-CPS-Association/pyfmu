#from os import add_dll_directory
from ctypes import cdll

from fmpy.simulation import simulate_fmu, FMU2Slave
from fmpy.model_description import read_model_description

from ..examples.example_finder import get_available_examples, ExampleArchive
from pybuilder.resources.resources import Resources

import pytest

"""This file contains tests related to how the Python FMU manages resources.

For ease of testing fmpy is used as a cosimulation engine.
"""


def test_shared_library_can_be_loaded():

    for pname in get_available_examples():

        with ExampleArchive(pname) as archive:

            # TODO load appropriate dll
            lib_dir = Resources.get().binaries_dir / 'win64'
            lib_path = lib_dir / 'libpyfmu.dll'

            p = str(lib_path.resolve())

            lib_loaded = cdll.LoadLibrary(p)

            test = 10


def test_singleInstantiation_canSimulate():

    with ExampleArchive('Adder') as archive:

        # seems like fmpy does not accept Path objects
        path = str(archive.root.resolve())

        simulate_fmu(path)


def test_multipleExports_canSimulate():

    for pname in get_available_examples():

        with ExampleArchive(pname) as archive:

            print(archive.model_description)
            # seems like fmpy does not accept Path objects
            path = str(archive.root.resolve())

            simulate_fmu(path)


def test_multipleInstantiationsAllDifferentInstanceNames_canSimulate():

    for idx, pname in enumerate(get_available_examples()):

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
