from math import sin

from pyfmu.fmi2 import (
    Fmi2Slave,
    Fmi2Status,
)


class SineGenerator(Fmi2Slave):
    def __init__(self, *args, **kwargs):

        super().__init__(
            model_name="SineGenerator",
            author="Chrisitian Møldrup Legaard",
            description="Single output sinewave generator",
            *args,
            **kwargs,
        )

        self.amplitude = 1.0
        self.frequency = 1.0
        self.phase = 0.0

        self.register_parameter("amplitude", description="amplitude of the sine wave")
        self.register_parameter(
            "frequency", description="frequency of the sine wave",
        )
        self.register_parameter(
            "phase", description="phase of the sine wave",
        )
        self.register_output("y", description="output of the generator")

    @property
    def y(self):
        return self.amplitude * sin(self.t * self.frequency + self.phase)

    def setup_experiment(self, start_time, stop_time, tolerance):
        self.t = start_time
        return Fmi2Status.ok

    def do_step(
        self, current_time: float, step_size: float, no_set_fmu_state_prior: bool
    ):
        print(f"step {current_time} size {step_size} ")
        self.t = current_time + step_size
        return Fmi2Status.ok
