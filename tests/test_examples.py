"""This file contains tests related to how the Python FMU manages resources.

For ease of testing fmpy is used as a cosimulation engine.
"""
from ctypes import cdll
import _ctypes
import platform

import pytest
from fmpy.simulation import FMU2Slave
from fmpy.model_description import read_model_description

from pyfmu.builder import validate_fmu
from .utils import get_all_examples, get_correct_examples, ExampleArchive


def log_callback(e, i, s, c, m):
    print(f"{i}{s}{c}{m}")


def fmi_logger(m):
    print(f"{m}")


# validate every example with
_validate_with = ["fmpy", "fmucheck", "vdmcheck", "maestro_v1"]
_validate_with = ["fmucheck"]


def test_shared_library_can_be_loaded():

    sys = platform.system()

    for pname in get_all_examples():

        with ExampleArchive(pname) as archive:

            if sys == "Windows":
                p = archive.wrapper_win64
            elif sys == "Linux":
                p = archive.wrapper_linux64
            else:
                raise NotImplementedError(f"Not implemented for platform {sys}")

            p = str(p.resolve())

            c = cdll.LoadLibrary(p)
            _ctypes.FreeLibrary(c._handle)


def test_Adder():
    with ExampleArchive("Adder") as a:

        assert validate_fmu(a.root, _validate_with).valid


def test_BicycleKinematic():
    with ExampleArchive("BicycleKinematic") as a:

        assert validate_fmu(a.root, _validate_with).valid


def test_ConstantSignalGenerator():
    with ExampleArchive("ConstantSignalGenerator") as a:
        res = validate_fmu(a.root, _validate_with)
        print(res.get_report())
        assert res.valid


def test_FmiTypes():
    with ExampleArchive("FmiTypes") as a:

        res = validate_fmu(a.root, _validate_with)
        assert res.valid


def test_LivePlotting():
    with ExampleArchive("LivePlotting") as a:

        assert validate_fmu(a.root, _validate_with).valid


def test_SineGenerator():
    with ExampleArchive("SineGenerator") as a:

        assert validate_fmu(a.root, _validate_with).valid


def test_multipleInstantiationsAllDifferentInstanceNames_canSimulate():

    for idx, pname in enumerate(get_correct_examples()):

        with ExampleArchive(pname) as archive:

            print(archive.model_description)
            # seems like fmpy does not accept Path objects
            # path = str(archive.root)

            md = read_model_description(str(archive.root))

            instance_a = str(idx) + "a"
            instance_b = str(idx) + "b"

            try:
                fmu_a = FMU2Slave(
                    guid=md.guid,
                    unzipDirectory=archive.root,
                    modelIdentifier=md.coSimulation.modelIdentifier,
                    instanceName=instance_a,
                    fmiCallLogger=None,
                )

                fmu_b = FMU2Slave(
                    guid=md.guid,
                    unzipDirectory=archive.root,
                    modelIdentifier=md.coSimulation.modelIdentifier,
                    instanceName=instance_b,
                    fmiCallLogger=None,
                )

            finally:
                if fmu_a is not None:
                    fmu_a.freeInstance()
                if fmu_b is not None:
                    fmu_b.freeInstance()


def atest_identicalNamesSameTypes_throws():

    with pytest.raises(Exception):
        with ExampleArchive("Adder") as a, ExampleArchive("Adder") as b:

            md_a = read_model_description(str(b.root))
            md_b = read_model_description(str(a.root))

            instance_a = "a"
            instance_b = "a"

            fmu_a = FMU2Slave(
                guid=md_a.guid,
                unzipDirectory=a.root,
                modelIdentifier=md_a.coSimulation.modelIdentifier,
                instanceName=instance_a,
                fmiCallLogger=None,
            )

            fmu_b = FMU2Slave(
                guid=md_b.guid,
                unzipDirectory=b.root,
                modelIdentifier=md_b.coSimulation.modelIdentifier,
                instanceName=instance_b,
                fmiCallLogger=None,
            )

            fmu_a.instantiate()
            fmu_b.instantiate()
            fmu_a.freeInstance()
            fmu_b.freeInstance()


def atest_identicalNamesDifferentTypes_throws():

    with pytest.raises(Exception):
        with ExampleArchive("Adder") as a, ExampleArchive(
            "ConstantSignalGenerator"
        ) as b:

            md_a = read_model_description(str(b.root))
            md_b = read_model_description(str(a.root))

            instance_a = "a"
            instance_b = "a"

            fmu_a = FMU2Slave(
                guid=md_a.guid,
                unzipDirectory=a.root,
                modelIdentifier=md_a.coSimulation.modelIdentifier,
                instanceName=instance_a,
                fmiCallLogger=None,
            )

            fmu_b = FMU2Slave(
                guid=md_b.guid,
                unzipDirectory=b.root,
                modelIdentifier=md_b.coSimulation.modelIdentifier,
                instanceName=instance_b,
                fmiCallLogger=None,
            )

            fmu_a.instantiate()
            fmu_b.instantiate()

            fmu_a.freeInstance()
            fmu_b.freeInstance()
