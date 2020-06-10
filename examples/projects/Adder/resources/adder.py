from pyfmu.fmi2 import (
    Fmi2Slave,
    Fmi2Status,
)


class Adder(Fmi2Slave):
    def __init__(self, *args, **kwargs):

        super().__init__(
            model_name="Adder",
            author="Christian Møldrup Legaard",
            description="Two input adder",
            *args,
            **kwargs,
        )

        self.a = 0.0
        self.b = 0.0
        self.register_input("a", "real", "continuous")
        self.register_input("b", "real", "continuous")
        self.register_output("s", "real", "continuous", "calculated")

    @property
    def s(self):
        return self.a + self.b


if __name__ == "__main__":

    def callback(status, category, message):
        print(f"{status}:{category}:{message}")

    fmu = Adder()

    s = fmu.enter_initialization_mode()
    assert s == Fmi2Status.ok
    s = fmu.exit_initialization_mode()
    assert s == Fmi2Status.ok

    fmu.do_step(0, 1, False)
    fmu.do_step(1, 2, False)
