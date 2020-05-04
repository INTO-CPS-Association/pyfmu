from pyfmu.fmi2 import (
    Fmi2Slave,
    Fmi2Status,
)


class Adder(Fmi2Slave):
    def __init__(self, *args, **kwargs):

        author = ""
        modelName = "Adder"
        description = ""

        super().__init__(
            modelName=modelName, author=author, description=description, *args, **kwargs
        )

        self.a = 0
        self.b = 0
        self.register_input("a", "real", "continuous")
        self.register_input("b", "real", "continuous")
        self.register_output("s", "real", "continuous", "calculated")
        self.register_input("boo","real","continuous")

    def __getattr__(self, item):
        return item

    @property
    def s(self):
        return self.a + self.b


if __name__ == "__main__":

    def callback(status, category, message):
        print(f"{status}:{category}:{message}")

    fmu = Adder(logging_callback=callback)

    s = fmu.enter_initialization_mode()
    assert s == Fmi2Status.ok
    s = fmu.exit_initialization_mode()
    assert s == Fmi2Status.ok

    fmu.do_step(0, 1, False)
    fmu.do_step(1, 2, False)
