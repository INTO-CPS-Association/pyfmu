from fmi2slave import Real, Fmi2Slave, Fmi2Causality, Fmi2Variability, Fmi2Initial

from math import sin

slave_class = "PythonSlave"  # REQUIRED - Name of the class extending Fmi2Slave


class PythonSlave(Fmi2Slave):

    Fmi2Slave.author = "Christian Legaard"
    Fmi2Slave.modelName = "PythonSlave"  # REQUIRED
    Fmi2Slave.description = "Generates a sine wave at a "

    def __init__(self):
        super().__init__()

        self.y = 0
        self.amplitude = 1
        self.frequency = 1
        self.phase = 0

        self.register_variable(
            Real("y").set_causality(Fmi2Causality.output))

        self.register_variable(
            Real("amplitude").set_causality(Fmi2Causality.parameter).set_variability(Fmi2Variability.tunable).set_initial(Fmi2Initial.exact))

        self.register_variable(
            Real("frequency").set_causality(Fmi2Causality.parameter).set_variability(Fmi2Variability.tunable).set_initial(Fmi2Initial.exact))

        self.register_variable(
            Real("phase").set_causality(Fmi2Causality.parameter).set_variability(Fmi2Variability.tunable).set_initial(Fmi2Initial.exact))

    def do_step(self, current_time, step_size):

        self.y = self.amplitude * \
            sin(current_time * self.frequency + self.phase)

        return True
