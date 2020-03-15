from pyfmu.fmi2slave import Fmi2Slave
from pyfmu.fmi2types import Fmi2Causality, Fmi2Variability, Fmi2DataTypes, Fmi2Initial


from scipy.integrate import odeint


class bicycle_model(Fmi2Slave):

    def __init__(self):

        author = ""
        modelName = "bicycle_model"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

        # model
        self.register_variable("a", "real", "input", start=0)
        self.register_variable("df", "real", "input", start=0)

        self.register_variable("x", "real", "output")
        self.register_variable("y", "real", "output")
        self.register_variable("psi", "real", "output")
        self.register_variable("v", "real", "output")
        self.register_variable("beta", "real", "output")

        # Initial values
        # declare variables to make IDE shut up.
        self.x0 = 0
        self.y0 = 0
        self.psi0 = 0
        self.v0 = 0
        self.beta0 = 0
        self.register_variable("x0", "real", "parameter", "fixed", start=0)
        self.register_variable("y0", "real", "parameter", "fixed", start=0)
        self.register_variable("psi0", "real", "parameter", "fixed", start=0)
        self.register_variable("v0", "real", "parameter", "fixed", start=0)
        self.register_variable("beta0", "real", "parameter", "fixed", start=0)

        # reference
        self.register_variable("x_r", "real", "input", start=0)
        self.register_variable("y_r", "real", "input", start=0)
        self.register_variable("psi_r", "real", "input", start=0)
        self.register_variable("v_r", "real", "input", start=0)
        self.register_variable("beta_r", "real", "input", start=0)


    def exit_initialization_mode(self):
        # outputs are have initial = calculated
        self.x = self.x0
        self.y = self.y0
        self.psi = self.psi0
        self.v = self.v0
        self.beta = self.beta0

    def do_step(self, current_time: float, step_size: float) -> bool:
        return True

# validation
if __name__ == "__main__":
    model = bicycle_model()
