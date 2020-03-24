from math import sin

from pyfmu.fmi2 import Fmi2Slave, Fmi2Causality, Fmi2Variability, Fmi2DataTypes, Fmi2Initial


class SineGenerator(Fmi2Slave):

    def __init__(self):

        author = ""
        modelName = "SineGenerator"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description)

        self.register_variable("amplitude", 'real', 'parameter', 'fixed', start=1, description='amplitude of the sine wave')
        self.register_variable("frequency", 'real', 'parameter', 'fixed', start=1, description='frequency of the sine wave')
        self.register_variable("phase", 'real', 'parameter', 'fixed', start=0, description='phase of the sine wave')
        self.register_variable("y", 'real', 'output',description='output of the generator')

    def setup_experiment(self, start_time, stop_time, tolerance):
        # its necessary to record this, to provide correct output at t=t_start
        self.start_time = start_time

    def exit_initialization_mode(self):
        # output has initial calculated, e.g. it must be defined after the FMU has been initialized.
        self.y = self.amplitude * sin(self.start_time * self.frequency + self.phase)

    def do_step(self, current_time: float, step_size: float, no_prior_step : bool):
        self.y = self.amplitude * sin(current_time * self.frequency + self.phase)


if __name__ == "__main__":
    s = SineGenerator()
    s.do_step(0,0,False)