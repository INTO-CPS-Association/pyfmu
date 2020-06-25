from math import sin

from pyfmu.fmi2 import (
    Fmi2Slave,
    Fmi2Status,
)


class SineGenerator(Fmi2Slave):
    def __init__(self, visible=False, logging_on=False, *args, **kwargs):

        super().__init__(
            model_name="SineGenerator",
            author="Chrisitian Møldrup Legaard",
            description="Single output sinewave generator",
            *args,
            **kwargs,
        )

        self.reset()

        self.register_parameter("amplitude", description="amplitude of the sine wave")
        self.register_parameter(
            "frequency", description="frequency of the sine wave",
        )
        self.register_parameter(
            "phase", description="phase of the sine wave",
        )
        self.register_output("y", description="output of the generator")

    def reset(self):
        self.amplitude = 1.0
        self.frequency = 1.0
        self.phase = 0.0
        return Fmi2Status.ok

    def setup_experiment(self, start_time, stop_time, tolerance):
        self.y = self.amplitude * sin(start_time * self.frequency + self.phase)
        return Fmi2Status.ok

    def do_step(
        self, current_time: float, step_size: float, no_set_fmu_state_prior: bool
    ):
        self.y = self.amplitude * sin(current_time * self.frequency + self.phase)
        return Fmi2Status.ok
