# from test.example_finder import ExampleArchive
import os


from pyfmu.fmi2 import Fmi2SlaveContext
from tests.utils.example_finder import ExampleArchive


def callback(*args):
    pass


class TestSlaveManager:
    def test_instantiate(self):
        mgr = Fmi2SlaveContext()

        with ExampleArchive("Adder") as a:

            h1 = mgr.instantiate(
                instance_name="a",
                fmu_type="fmi2CoSimulation",
                guid="",
                resources_uri=a.resources_dir.as_uri(),
                logging_callback=callback,
                visible=True,
            )

            h2 = mgr.instantiate(
                instance_name="a",
                fmu_type="fmi2CoSimulation",
                guid="",
                resources_uri=a.resources_dir.as_uri(),
                logging_callback=callback,
                visible=True,
            )

            mgr.do_step(h1, 0, 1, False)

    pass
