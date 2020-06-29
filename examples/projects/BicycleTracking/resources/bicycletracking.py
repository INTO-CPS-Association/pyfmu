import logging

from oomodelling.TrackingSimulator import TrackingSimulator

from pyfmu.fmi2 import Fmi2Slave, Fmi2Status, Fmi2Status_T
import numpy as np
from scipy.integrate import solve_ivp, RK45

# from thirdparty.BikeTrackingWithInput import BikeTrackingWithInput


import math

from oomodelling.Model import Model


from oomodelling.ModelSolver import ModelSolver
from oomodelling.TrackingSimulator import TrackingSimulator


class BikeTrackingWithInput(TrackingSimulator):
    def __init__(self):
        super().__init__()

        self.tracking = BicycleDynamicModel()

        self.to_track_X = self.input(lambda: 0.0)
        self.to_track_Y = self.input(lambda: 0.0)
        self.to_track_delta = self.input(lambda: 0.0)

        # Note that we assign a lambda even though self.to_track_delta is a callable.
        # This is important because it allows self.to_track_delta to be override to another callable.
        # Otherwise, the original callable is kept in self.tracking.deltaf after self.to_track_delta has been changed.
        self.tracking.deltaf = lambda: self.to_track_delta()
        # For the same reason, we match the lambda signals, because they will be defined later.
        self.match_signals(lambda d: self.to_track_X(d), self.tracking.X)
        self.match_signals(lambda d: self.to_track_Y(d), self.tracking.Y)

        self.X_idx = self.tracking.get_state_idx("X")
        self.Y_idx = self.tracking.get_state_idx("Y")

        self.save()

    def run_whatif_simulation(
        self,
        new_parameters,
        t0,
        tf,
        tracked_solutions,
        error_space,
        only_tracked_state=True,
    ):
        new_caf = new_parameters[0]
        self.l.debug(
            f"Running whatif simulation from time {t0} to time {tf} with Caf {new_caf}."
        )
        m = BicycleDynamicModel()
        m.Caf = lambda: new_caf
        # Rewrite control input to mimic the past behavior.
        m.deltaf = lambda: self.to_track_delta(-(tf - m.time()))
        assert np.isclose(self.to_track_X(-(tf - t0)), tracked_solutions[0][0])
        assert np.isclose(self.to_track_Y(-(tf - t0)), tracked_solutions[1][0])
        # Set the state to the past state: This is the main different wrt to BikeTrackingWithDynamic.
        # Here, the state is set to the inaccurate past state.
        m.x = self.tracking.x(-(tf - t0))
        m.X = self.to_track_X(-(tf - t0))
        m.y = self.tracking.y(-(tf - t0))
        m.Y = self.to_track_Y(-(tf - t0))
        m.vx = self.tracking.vx(-(tf - t0))
        m.vy = self.tracking.vy(-(tf - t0))
        m.psi = self.tracking.psi(-(tf - t0))
        m.dpsi = self.tracking.dpsi(-(tf - t0))

        sol = ModelSolver().simulate(m, t0, tf, self.time_step, error_space)
        new_trajectories = sol.y
        if only_tracked_state:
            new_trajectories = np.array([sol.y[self.X_idx, :], sol.y[self.Y_idx, :]])
            assert len(new_trajectories) == 2
            assert len(new_trajectories[0, :]) == len(sol.y[0, :])

        return new_trajectories

    def update_tracking_model(self, new_present_state, new_parameter):
        self.tracking.record_state(new_present_state, self.time(), override=True)
        self.tracking.Caf = lambda: new_parameter[0]
        assert np.isclose(new_present_state[self.X_idx], self.tracking.X())
        assert np.isclose(new_present_state[self.Y_idx], self.tracking.Y())

    def get_parameter_guess(self):
        return np.array([self.tracking.Caf()])


class BicycleDynamicModel(Model):
    def __init__(self):
        super().__init__()
        self.lf = self.parameter(
            1.105
        )  # distance from the the center of mass to the front (m)";
        self.lr = self.parameter(
            1.738
        )  # distance from the the center of mass to the rear (m)";
        self.m = self.parameter(1292.2)  # Vehicle's mass (kg)";
        self.Iz = self.parameter(1)  # Yaw inertial (kgm^2) (Not taken from the book)";
        self.Caf = self.input(lambda: 800.0)  # Front Tire cornering stiffness";
        self.Car = self.parameter(800.0)  # Rear Tire cornering stiffness";
        self.x = self.state(0.0)  # longitudinal displacement in the body frame";
        self.X = self.state(0.0)  # x coordinate in the reference frame";
        self.Y = self.state(0.0)  # x coordinate in the reference frame";
        self.vx = self.state(1.0)  # velocity along x";
        self.y = self.state(0.0)  # lateral displacement in the body frame";
        self.vy = self.state(0.0)  # velocity along y";
        self.psi = self.state(0.0)  # Yaw";
        self.dpsi = self.state(0.0)  # Yaw rate";
        self.a = self.input(lambda: 0.0)  # longitudinal acceleration";
        self.deltaf = self.input(lambda: 0.0)  # steering angle at the front wheel";
        self.af = self.var(
            lambda: self.deltaf() - (self.vy() + self.lf * self.dpsi()) / self.vx()
        )  # Front Tire slip angle";
        self.ar = self.var(
            lambda: (self.vy() - self.lr * self.dpsi()) / self.vx()
        )  # Rear Tire slip angle";
        self.Fcf = self.var(
            lambda: self.Caf() * self.af()
        )  # lateral tire force at the front tire in the frame of the front tire";
        self.Fcr = self.var(
            lambda: self.Car * (-self.ar())
        )  # lateral tire force at the rear tire in the frame of the rear tire";

        self.der("x", lambda: self.vx())
        self.der("y", lambda: self.vy())
        self.der("psi", lambda: self.dpsi())
        self.der("vx", lambda: self.dpsi() * self.vy() + self.a())
        self.der(
            "vy",
            lambda: -self.dpsi() * self.vx()
            + (1 / self.m) * (self.Fcf() * math.cos(self.deltaf()) + self.Fcr()),
        )
        self.der(
            "dpsi",
            lambda: (2 / self.Iz) * (self.lf * self.Fcf() - self.lr * self.Fcr()),
        )
        self.der(
            "X",
            lambda: self.vx() * math.cos(self.psi()) - self.vy() * math.sin(self.psi()),
        )
        self.der(
            "Y",
            lambda: self.vx() * math.sin(self.psi()) + self.vy() * math.cos(self.psi()),
        )

        self.save()


class BicycleTracking(Fmi2Slave):
    def __init__(self, visible=False, logging_on=False, *args, **kwargs):

        super().__init__(
            model_name="BicycleTracking", author="", description="", *args, **kwargs
        )

        self.log_ok("Instantiating bicycle tracking model")
        self.bicycle_tracking = BikeTrackingWithInput()
        self.bicycle_tracking.tolerance = 0.2
        self.bicycle_tracking.horizon = 5.0
        self.bicycle_tracking.cooldown = 5.0
        self.bicycle_tracking.nsamples = 10
        self.bicycle_tracking.max_iterations = 20
        self.bicycle_tracking.time_step = 0.1
        self.bicycle_tracking.conv_xatol = 1e3
        self.bicycle_tracking.conv_fatol = 0.01

        self.reset()

        # Inputs, outputs and parameters may be defined using the 'register_{input,output,parameter}' functions
        # By default these are bound to attributes of the instance.
        self.register_input(
            "to_track_X",
            "real",
            "continuous",
            description="Position X of object to track.",
        )
        self.register_input(
            "to_track_Y",
            "real",
            "continuous",
            description="Position Y of object to track.",
        )
        self.register_input(
            "deltaf",
            "real",
            "continuous",
            description="steering angle at the front wheel",
        )

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

        self.register_output(
            "tolerance", "real", "continuous", description="tolerance",
        )

        self.register_output(
            "error", "real", "continuous", description="tolerance",
        )

        self.register_output(
            "Caf", "real", "continuous", description="tolerance",
        )

        # Set the inputs
        self.log_ok("Wiring inputs.")

        self.bicycle_tracking.to_track_X = lambda: self.to_track_X
        self.bicycle_tracking.to_track_Y = lambda: self.to_track_Y
        self.bicycle_tracking.to_track_delta = lambda: self.deltaf

        if logging_on:
            print("Enabling logging.")
            self.set_debug_logging([], True)
            logging.basicConfig(
                filename="tracking_with_input.log", filemode="w", level=logging.DEBUG
            )

    def do_step(
        self, current_time: float, step_size: float, no_prior_step: bool
    ) -> Fmi2Status_T:

        # self.X = self.to_track_X
        # self.Y = self.to_track_Y

        print(f"DoStep at time {current_time}.")

        self.log_ok("Compute model derivative function.")
        f = self.bicycle_tracking.derivatives()
        self.log_ok("Compute state vector at start of step.")
        x = self.bicycle_tracking.state_vector()

        n_states = self.bicycle_tracking.nstates()

        self.log_ok("Record current state in model history.")
        self.bicycle_tracking.record_state(x, current_time)

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

        self.log_ok(f"Performing discrete step computation.")
        update_state = self.bicycle_tracking.discrete_step()

        self.log_ok(f"State updated: {update_state}")

        self.log_ok("Getting outputs from internal model.")
        # Important to convert to float64.
        # Otherwise COE will crash because the type of self.X is numpy.float64
        self.X = float(self.bicycle_tracking.tracking.X())
        self.Y = float(self.bicycle_tracking.tracking.Y())
        self.error = float(self.bicycle_tracking.error())
        self.Caf = float(self.bicycle_tracking.tracking.Caf())

        return Fmi2Status.ok

    def reset(self) -> Fmi2Status_T:
        self.to_track_X = 0.0
        self.to_track_Y = 0.0
        self.deltaf = 0.0
        self.X = 0.0
        self.Y = 0.0
        self.tolerance = self.bicycle_tracking.tolerance
        self.error = 0.0
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

