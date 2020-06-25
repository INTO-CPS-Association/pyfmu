from pyfmu.fmi2 import Fmi2Slave, Fmi2Status, Fmi2Status_T
import numpy as np


class Adder(Fmi2Slave):
    def __init__(self, visible=False, logging_on=False, *args, **kwargs):

        super().__init__(
            model_name="Adder",
            author="Christian Møldrup Legaard",
            description="Two input adder",
            *args,
            **kwargs,
        )

        self.reset()
        self.register_input("a", "real", "continuous")
        self.register_input("b", "real", "continuous")
        self.register_output("s", "real", "continuous", "calculated")

    def reset(self) -> Fmi2Status_T:
        self.a = 0.0
        self.b = 0.0
        return Fmi2Status.ok

    @property
    def s(self):
        return self.a + self.b


if __name__ == "__main__":

    fmu = Adder()

    t_start = 0
    t_end = 1
    n_steps = 100

    ts, t_step = np.linspace(start=t_start, stop=t_end, num=n_steps, retstep=True)

    assert fmu.setup_experiment(t_start, t_end) == Fmi2Status.ok
    assert fmu.enter_initialization_mode() == Fmi2Status.ok
    assert fmu.exit_initialization_mode() == Fmi2Status.ok

    for t in ts:
        assert fmu.do_step(t, t + t_step, False) == Fmi2Status.ok
        assert fmu.s == fmu.a + fmu.b

    assert fmu.terminate() == Fmi2Status.ok
    assert fmu.reset() == Fmi2Status.ok

