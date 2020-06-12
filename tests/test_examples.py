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
_validate_with = ["fmpy"]


def test_Adder():
    with ExampleArchive("Adder") as a:
        res = validate_fmu(a.root, _validate_with)
        print(res.get_report())
        assert res.valid


def test_BicycleKinematic():
    with ExampleArchive("BicycleKinematic") as a:

        res = validate_fmu(a.root, _validate_with)
        print(res.get_report())
        assert res.valid


def test_ConstantSignalGenerator():
    with ExampleArchive("ConstantSignalGenerator") as a:
        res = validate_fmu(a.root, _validate_with)
        print(res.get_report())
        assert res.valid


def test_FmiTypes():
    with ExampleArchive("FmiTypes") as a:

        res = validate_fmu(a.root, _validate_with)
        print(res.get_report())
        assert res.valid


def test_LivePlotting():
    with ExampleArchive("LivePlotting") as a:
        res = validate_fmu(a.root, _validate_with)
        print(res.get_report())
        assert res.valid


def test_SineGenerator():
    with ExampleArchive("SineGenerator") as a:
        res = validate_fmu(a.root, _validate_with)
        print(res.get_report())
        assert res.valid
