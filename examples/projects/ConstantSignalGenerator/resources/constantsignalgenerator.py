from pyfmu.fmi2 import (
    Fmi2Slave,
    Fmi2Causality,
    Fmi2Variability,
    Fmi2DataTypes,
    Fmi2Initial,
)


class ConstantSignalGenerator(Fmi2Slave):
    def __init__(self, *args, **kwargs):

        super().__init__(
            model_name="ConstantSignalGenerator",
            author="Christian Møldrup Legaard",
            description="Produces a constant signal",
            *args,
            **kwargs
        )
        self.k = 1.0
        self.register_output("y")
        self.register_parameter("k")

    @property
    def y(self):
        return self.k
