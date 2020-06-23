from pyfmu.fmi2 import Fmi2Slave, Fmi2Status, Fmi2Status_T
import numpy as np


class SourceTwo(Fmi2Slave):

    def __init__(self, *args, **kwargs):
        
  
        
        super().__init__(
            model_name="SourceTwo",
            author="",
            description="",
            *args,
            **kwargs
            )

        self.reset()

        # Inputs, outputs and parameters may be defined using the 'register_{input,output,parameter}' functions
        # By default these are bound to attributes of the instance.
        # self.register_input("a", "real", "continuous", description="first input")
        # self.register_input("b", "real", "continuous", description="second input")
        self.register_output("s1", "real", "continuous", description="s1")
        self.register_output("s2", "real", "continuous", description="s2")

    def do_step(self, current_time: float, step_size: float, no_prior_step : bool) -> Fmi2Status_T:
        return Fmi2Status.ok

    def reset(self) -> Fmi2Status_T:
        self.s1 = 1.0
        self.s2 = 2.0
        return Fmi2Status.ok

    def enter_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def exit_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok 

    def setup_experiment(
        self, start_time: float, stop_time: float = None, tolerance: float = None
    ) -> Fmi2Status_T:
        return Fmi2Status.ok


# Writing a small test program to test slave saves a lot of time.
# Proper unit testing frameworks may be used as well.
if __name__ == "__main__":

    fmu = SourceTwo()

    t_start = 0
    t_end = 1
    n_steps = 100

    ts, t_step = np.linspace(start=t_start, stop=t_end, num=n_steps, retstep=True)

    assert fmu.setup_experiment(t_start, t_end) == Fmi2Status.ok
    assert fmu.enter_initialization_mode() == Fmi2Status.ok
    assert fmu.exit_initialization_mode() == Fmi2Status.ok

    for t in ts:
        assert fmu.do_step(t, t + t_step, False) == Fmi2Status.ok
        assert fmu.s1 == 1.0
        assert fmu.s2 == 2.0

    assert fmu.terminate() == Fmi2Status.ok
    assert fmu.reset() == Fmi2Status.ok

