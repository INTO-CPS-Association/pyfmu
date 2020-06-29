from oomodelling.Model import Model
from scipy.integrate import solve_ivp, RK45

from pyfmu.fmi2 import Fmi2Slave, Fmi2Status, Fmi2Status_T
import numpy as np


class BicycleDriver(Fmi2Slave):
    def __init__(self, visible=False, logging_on=False, *args, **kwargs):
        super().__init__(
            model_name="BicycleDriver", author="", description="", *args, **kwargs
        )

        self.driver_model = DriverDynamic()

        self.reset()

        # Inputs, outputs and parameters may be defined using the 'register_{input,output,parameter}' functions
        # By default these are bound to attributes of the instance.
        self.register_output(
            "deltaf",
            "real",
            "continuous",
            "calculated",
            description="steering angle at the front wheel",
        )
        self.register_output(
            "Caf", "real", "continuous", "calculated", description="Slippery"
        )

    def do_step(
        self, current_time: float, step_size: float, no_prior_step: bool
    ) -> Fmi2Status_T:

        self.log_ok("Compute model derivative function.")
        f = self.driver_model.derivatives()
        self.log_ok("Compute state vector at start of step.")
        x = self.driver_model.state_vector()

        n_states = self.driver_model.nstates()

        self.log_ok("Record current state in model history.")
        self.driver_model.record_state(x, current_time)

        self.log_ok("Invoking internal solver.")
        stop_time = current_time + step_size
        sol = solve_ivp(
            f,
            (current_time, stop_time),
            x,
            method=RK45,
            max_step=step_size,
            t_eval=[stop_time],
        )
        self.log_ok(f"Solution success: {sol.success}")
        assert sol.success
        assert sol.y.shape == (n_states, 1), (sol.y, sol.y.shape)

        self.log_ok("Getting outputs from internal model.")
        # Important to convert to float64.
        # Otherwise COE will crash because the type of self.X is numpy.float64
        self.deltaf = float(self.driver_model.steering())

        if current_time > 10.0:
            self.Caf = 500.0

        return Fmi2Status.ok

    def reset(self) -> Fmi2Status_T:
        self.deltaf = 0.0
        self.Caf = 800.0
        return Fmi2Status.ok

    def enter_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def exit_initialization_mode(self) -> Fmi2Status_T:
        return Fmi2Status.ok

    def setup_experiment(
        self, start_time: float, stop_time: float = None, tolerance: float = None
    ) -> Fmi2Status_T:
        return Fmi2Status.ok


class DriverDynamic(Model):

    def __init__(self):
        super().__init__()
        self.width = self.parameter(2.6)
        self.amplitude = self.parameter(0.8)
        self.risingtime = self.parameter(3.0)
        self.starttime = self.parameter(3.0)
        self.steering = self.var(self.get_steering)
        self.last_period_endtime = 0
        self.nperiods = self.parameter(2)
        self.nperiods_counter = 0
        self.save()

    def get_steering(self):
        if self.nperiods_counter >= self.nperiods:
            return 0.0

        t = self.time() - self.last_period_endtime
        if t < self.starttime:
            return 0.0
        elif (t - self.starttime) < self.risingtime:
            # rising
            return self.amplitude * (t - self.starttime) / self.risingtime
        elif (t - self.starttime - self.risingtime) < self.width:
            # plateau
            return self.amplitude
        else:
            # falling
            res = self.amplitude - self.amplitude * (t - self.starttime - self.risingtime - self.width) / self.risingtime
            if res <= 0.0:
                # New period ended
                self.last_period_endtime = self.time()
                self.nperiods_counter += 1
            return max(0.0, res)


# Writing a small test program to test slave saves a lot of time.
# Proper unit testing frameworks may be used as well.
if __name__ == "__main__":

    fmu = BicycleDriver()

    t_start = 0
    t_end = 1
    n_steps = 100

    ts, t_step = np.linspace(start=t_start, stop=t_end, num=n_steps, retstep=True)

    assert fmu.setup_experiment(t_start, t_end) == Fmi2Status.ok
    assert fmu.enter_initialization_mode() == Fmi2Status.ok
    assert fmu.exit_initialization_mode() == Fmi2Status.ok

    for t in ts:
        assert fmu.do_step(t, t + t_step, False) == Fmi2Status.ok
        assert fmu.Caf == 800.0

    assert fmu.terminate() == Fmi2Status.ok
    assert fmu.reset() == Fmi2Status.ok

