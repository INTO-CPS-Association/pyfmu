import subprocess
import logging
from pathlib import Path

from pyfmu.resources import Resources

from .utils import MaestroExample

# maestro status code for succesfull run seems to be 1
_maestroV1_OK = 1


def execute_cosimulation(example_name: str, start_time: float, stop_time: float) -> int:

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

        results = subprocess.run(args)

    return results.returncode


def test_BicycleDynamicAndDriver(caplog):
    caplog.set_level(logging.INFO)
    assert execute_cosimulation("BicycleDynamicAndDriver", 0.0, 10.0) == _maestroV1_OK


def test_SumOfSines(caplog):
    caplog.set_level(logging.INFO)
    assert execute_cosimulation("SumOfSines", 0.0, 10.0) == _maestroV1_OK

