from pyfmu.tests.example_finder import ExampleArchive

from pyfmu.fmi2 import Fmi2SlaveManager


def callback(*args):
    pass


class TestSlaveManager:
    def test_instantiate(self):
        mgr = Fmi2SlaveManager()

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
