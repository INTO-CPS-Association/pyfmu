from math import cos, sin, atan, tan

from scipy.integrate import solve_ivp


from pyfmu.fmi2 import (
    Fmi2Slave,
    Fmi2Status,
    Fmi2Status_T,
)


class Bicycle_Kinematic(Fmi2Slave):
    def __init__(self, visible=False, logging_on=False, *args, **kwargs):

        super().__init__(
            model_name="BicycleKinematic", author="", description="", *args, **kwargs
        )

        # silience incorrect warnings about undeclared variables

        self.reset()

        # model
        self.register_input("a", "real", "continuous", description="acceleration")
        self.register_input("df", "real", "continuous", description="steering angle")

        self.register_output(
            "x",
            "real",
            "continuous",
            "calculated",
            description="x position of the robot",
        )
        self.register_output(
            "y",
            "real",
            "continuous",
            "calculated",
            description="y position of the robot",
        )
        self.register_output(
            "psi",
            "real",
            "continuous",
            "calculated",
            description="inertial heading of the robot",
        )
        self.register_output(
            "v", "real", "continuous", "calculated", description="velocity of the robot"
        )

        self.register_parameter(
            "lf", "real", "fixed", description="distance from CM to front wheel",
        )
        self.register_parameter(
            "lr", "real", "fixed", description="distance from CM to rear wheel",
        )

        self.register_parameter("x0", "real", "fixed")
        self.register_parameter("y0", "real", "fixed")
        self.register_parameter("psi0", "real", "fixed")
        self.register_parameter("v0", "real", "fixed")

        self.register_input("x_r", "real", "continuous")
        self.register_input("y_r", "real", "continuous")
        self.register_input("psi_r", "real", "continuous")
        self.register_input("v_r", "real", "continuous")

    def reset(self) -> Fmi2Status_T:
        self.a = 0.0
        self.df = 0.0
        self.x = 0.0
        self.y = 0.0
        self.v = 0.0
        self.psi = 0.0
        self.beta = 0.0
        self.lf = 1.0
        self.lr = 1.0

        # Initial values
        self.x0 = 0.0
        self.y0 = 0.0
        self.psi0 = 0.0
        self.v0 = 0.0

        # reference model
        self.x_r = 0.0
        self.y_r = 0.0
        self.psi_r = 0.0
        self.v_r = 0.0
        return Fmi2Status.ok

    @staticmethod
    def _derivatives(t, state, params):
        df, a, lf, lr = params

        _, _, psi, v = state

        beta = atan((lr / (lr + lf)) * tan(df))

        x_d = v * cos(psi + beta)
        y_d = v * sin(psi + beta)
        psi_d = (v / lr) * sin(beta)
        v_d = a

        return [x_d, y_d, psi_d, v_d]

    def enter_initialization_mode(self):
        # outputs are have initial = calculated
        self.x = self.x0
        self.y = self.y0
        self.psi = self.psi0
        self.v = self.v0
        return Fmi2Status.ok

    def do_step(self, current_time: float, step_size: float, no_prior_step: bool):

        # bundle the parameters in the function call
        def fun(t, state):
            params = (self.df, self.a, self.lf, self.lr)
            return Bicycle_Kinematic._derivatives(t, state, params)

        h0 = (self.x, self.y, self.psi, self.v)
        end = current_time + step_size
        t_span = (current_time, end)

        res = solve_ivp(
            fun,
            t_span,
            h0,
            # max_step=0.1,
            t_eval=[end],
        )

        x, y, psi, v = tuple(res.y)
        self.x = x[0].item()
        self.y = y[0].item()
        self.psi = psi[0].item()
        self.v = v[0].item()

        return Fmi2Status.ok


if __name__ == "__main__":

    m = Bicycle_Kinematic()
    for i in range(1000):
        m.do_step(i, i + 1, False)
