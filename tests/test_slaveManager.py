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

            mgr.instantiate(
                "a",
                "fmi2CoSimulation",
                "",
                a.resources_dir.as_uri(),
                callback,
                True,
                True,
            )

    pass
