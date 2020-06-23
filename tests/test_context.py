# from test.example_finder import ExampleArchive
import os

import pytest


from pyfmu.fmi2 import Fmi2SlaveContext
from pyfmu.fmi2.types import Fmi2Status, Fmi2Type
from tests.utils.example_finder import ExampleArchive


def callback(**kwargs):
    print(kwargs)


class TestSlaveManager:
    def test_instantiate(self):
        mgr = Fmi2SlaveContext()

        with ExampleArchive("Adder") as a:

            h1 = mgr.instantiate(
                instance_name="a",
                fmu_type=Fmi2Type.co_simulation,
                guid="",
                resources_uri=a.resources_dir.as_uri(),
                logging_callback=callback,
                logging_on=True,
                visible=True,
            )

            h2 = mgr.instantiate(
                instance_name="a",
                fmu_type=Fmi2Type.co_simulation,
                guid="",
                resources_uri=a.resources_dir.as_uri(),
                logging_callback=callback,
                logging_on=True,
                visible=True,
            )

            assert h1 is not None
            assert h2 is not None
            assert h1 != h2

            assert mgr.do_step(h1, 0, 1, False) is Fmi2Status.ok
            assert mgr.do_step(h2, 0, 1, False) is Fmi2Status.ok

            assert mgr.setup_experiment(h1, 0) is Fmi2Status.ok
            assert mgr.setup_experiment(h2, 0) is Fmi2Status.ok

            # correct datatype
            assert (
                mgr.set_xxx(h1, references=[0, 1], values=[1.0, 2.0]) is Fmi2Status.ok
            )
            assert (
                mgr.set_xxx(h2, references=[0, 1], values=[3.0, 4.0]) is Fmi2Status.ok
            )

            # incorrect data type, int instead of float
            assert mgr.set_xxx(h1, references=[0, 1], values=[1, 2]) is Fmi2Status.error
            assert mgr.set_xxx(h2, references=[0, 1], values=[3, 4]) is Fmi2Status.error

            # reading values
            val, status = mgr.get_xxx(h1, references=[2])
            assert status is Fmi2Status.ok and val == [3.0]

            val, status = mgr.get_xxx(h2, references=[2])
            assert status is Fmi2Status.ok and val == [7.0]

            # illegal value caught but returns error status
            assert mgr.set_xxx(h1, references=[3], values=[0]) is Fmi2Status.error
            assert mgr.set_xxx(h2, references=[3], values=[0]) is Fmi2Status.error

    pass
