import logging
import math

from oomodelling.Model import Model
from scipy.integrate import solve_ivp, RK45

from thirdparty.BicycleDynamicModel import BicycleDynamicModel
from pyfmu.fmi2 import Fmi2Slave, Fmi2Status, Fmi2Status_T
import numpy as np


class BicycleDynamic(Fmi2Slave):

    def __init__(self, *args, **kwargs):
        super().__init__(
            model_name="BicycleDynamic",
            author="",
            description="",
            *args,
            **kwargs
            )

        self.log_ok("Instantiating bicycle model")
        self.bicycle_model = BicycleDynamicModel()

        self.reset()

        # Inputs, outputs and parameters may be defined using the 'register_{input,output,parameter}' functions
        # By default these are bound to attributes of the instance.
        self.register_input("Caf", "real", "continuous", description="Front Tire cornering stiffness")
        self.register_input("deltaf", "real", "continuous", description="steering angle at the front wheel")

        self.register_output(
            "X",
            "real",
            "continuous",
            description="x coordinate in the reference frame",
        )

        self.register_output(
            "Y",
            "real",
            "continuous",
            description="y coordinate in the reference frame",
        )




    def do_step(self, current_time: float, step_size: float, no_prior_step : bool) -> Fmi2Status_T:
        self.log_ok("Setting inputs.")
        self.bicycle_model.Caf = lambda: self.Caf
        self.bicycle_model.deltaf = lambda: self.deltaf

        self.log_ok("Compute model derivative function.")
        f = self.bicycle_model.derivatives()
        self.log_ok("Compute state vector at start of step.")
        x = self.bicycle_model.state_vector()

        n_states = self.bicycle_model.nstates()

        self.log_ok("Record current state in model history.")
        self.bicycle_model.record_state(x, current_time)

        self.log_ok("Invoking internal solver.")
        stop_time = current_time + step_size
        sol = solve_ivp(f, (current_time, stop_time), x,
                        method=RK45, max_step=step_size,
                        t_eval=[stop_time])
        self.log_ok(f"Solution success: {sol.success}")
        assert sol.success
        assert sol.y.shape == (n_states, 1), (sol.y, sol.y.shape)

        self.log_ok("Getting outputs from internal model.")
        # Important to convert to float64.
        # Otherwise COE will crash because the type of self.X is numpy.float64
        self.X = float(self.bicycle_model.X())
        self.Y = float(self.bicycle_model.Y())

        return Fmi2Status.ok

    def reset(self) -> Fmi2Status_T:
        self.X = 0.0
        self.Y = 0.0
        self.Caf = 800.0
        self.deltaf = 0.0
        self.bicycle_model.reset()
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

    fmu = BicycleDynamic()

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

