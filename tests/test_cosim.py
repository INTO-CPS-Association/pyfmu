import subprocess
import logging
from pathlib import Path
from tempfile import mkdtemp
import os
import sys

logging.basicConfig(level=logging.DEBUG)


from pyfmu.resources import Resources

from .utils import MaestroExample

# maestro status code for succesfull run seems to be 1
_maestroV1_OK = 1


def execute_cosimulation(
    example_name: str, start_time: float, stop_time: float, use_tempdir=True
) -> int:
    jar_path = str(Resources.get().maestro_v1.absolute())

    with MaestroExample(example_name) as config:

        args = [
            "java",
            "-jar",
            jar_path,
            "-v",
            "--configuration",
            str(config),
            "--oneshot",
            "--starttime",
            str(start_time),
            "--endtime",
            str(stop_time),
        ]

        print(args)

        # maestroV1 creates several temporary files
        # change directory to avoid cluttering
        old_dir = os.getcwd()
        if use_tempdir:
            os.chdir(mkdtemp())

        results = subprocess.run(args)

        os.chdir(old_dir)

    return results.returncode


def test_BicycleDynamicAndDriver(caplog):
    caplog.set_level(logging.INFO)
    assert execute_cosimulation("BicycleDynamicAndDriver", 0.0, 10.0) == _maestroV1_OK


def test_SumOfSines(caplog):
    caplog.set_level(logging.INFO)
    assert execute_cosimulation("SumOfSines", 0.0, 10.0) == _maestroV1_OK


def test_TrackingSimulator(caplog):
    caplog.set_level(logging.INFO)
    assert execute_cosimulation("TrackingSimulator", 0.0, 25.0) == _maestroV1_OK
