from pyfmu.fmi2 import Fmi2Slave, Fmi2Status


class FmiTypes(Fmi2Slave):
    def __init__(self, *args, **kwargs):

        author = "Christian Møldrup Legaard"
        modelName = "FmiTypes"
        description = "FMU for testing different FMI types"

        super().__init__(
            model_name=modelName,
            author=author,
            description=description,
            *args,
            **kwargs
        )

        self.real_in = 0.0
        self.integer_in = 0
        self.boolean_in = False
        self.string_in = ""

        # Inputs, outputs and parameters may be defined using the 'register_variable' function
        self.register_input("real_in", "real", "continuous")
        self.register_output("real_out", "real", "continuous", "calculated")
        self.register_input("integer_in", "integer", "discrete")
        self.register_output("integer_out", "integer", "discrete", "calculated")
        self.register_input("boolean_in", "boolean", "discrete")
        self.register_output("boolean_out", "boolean", "discrete", "calculated")
        self.register_input("string_in", "string", "discrete")
        self.register_output("string_out", "string", "discrete", "calculated")

    @property
    def real_out(self):
        return self.real_in

    @property
    def integer_out(self):
        return self.integer_in

    @property
    def boolean_out(self):
        return self.boolean_in

    @property
    def string_out(self):
        return self.string_in


if __name__ == "__main__":
    fmu = FmiTypes()
    # extra check used to ensure the fmu is initialized according to the standard (not necessary)
    s = fmu.enter_initialization_mode()
    assert s == Fmi2Status.ok
    s = fmu.exit_initialization_mode()
    assert s == Fmi2Status.ok

    for i in range(100):
        fmu.real_in = float(i)
        fmu.integer_in = int(i)
        fmu.boolean_in = bool(i)
        fmu.string_in = str(i)

        s = fmu.do_step(i, i, False)
        assert s == Fmi2Status.ok
        assert fmu.real_in == fmu.real_out
        assert fmu.integer_in == fmu.integer_out
        assert fmu.boolean_in == fmu.boolean_out
        assert fmu.string_in == fmu.string_out
