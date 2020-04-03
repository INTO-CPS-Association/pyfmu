from pyfmu.fmi2 import Fmi2Slave, Fmi2Causality, Fmi2DataTypes, Fmi2Status


class LoggerFMU(Fmi2Slave):

    def __init__(self, *args, **kwargs):

        author = ""
        modelName = "LoggerFMU"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description,
            *args,
            **kwargs
        )

        self.register_variable(
            "s", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.output)
        self.register_variable(
            "a", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0.0)
        self.register_variable(
            "b", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0.0)

    def enter_initialization_mode(self):

        self.s = self.a + self.b

        self.log(f"inputs was set to {self.a} {self.b}, output is {self.s}")

        return True

    def do_step(self, current_time: float, step_size: float, no_prior_step: bool):

        self.log("Stepping!")

        self.s = self.a + self.b
        return True


if __name__ == "__main__":
    fmu = LoggerFMU()
    fmu.set_debug_logging(True, ['fmi2slave'])

    # extra check used to ensure the fmu is initialized according to the standard (not necessary)
    s = fmu._enter_initialization_mode()
    assert(s == Fmi2Status.ok.value)
    s = fmu._exit_initialization_mode()
    assert(s == Fmi2Status.ok.value)

    test = 10.0
