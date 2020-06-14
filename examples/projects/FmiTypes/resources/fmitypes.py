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

        self.real_in_a = 0.0
        self.real_in_b = 0.0
        self.integer_in_a = 0
        self.integer_in_b = 0
        self.boolean_in_a = False
        self.boolean_in_b = False
        self.string_in_a = ""
        self.string_in_b = ""

        # Inputs, outputs and parameters may be defined using the 'register_variable' function
        self.register_input("real_in_a", "real", "continuous")
        self.register_input("real_in_b", "real", "continuous")
        self.register_output("real_out_a", "real", "continuous", "calculated")
        self.register_output("real_out_b", "real", "continuous", "calculated")
        self.register_input("integer_in_a", "integer", "discrete")
        self.register_input("integer_in_b", "integer", "discrete")
        self.register_output("integer_out_a", "integer", "discrete", "calculated")
        self.register_output("integer_out_b", "integer", "discrete", "calculated")
        self.register_input("boolean_in_a", "boolean", "discrete")
        self.register_input("boolean_in_b", "boolean", "discrete")
        self.register_output("boolean_out_a", "boolean", "discrete", "calculated")
        self.register_output("boolean_out_b", "boolean", "discrete", "calculated")
        self.register_input("string_in_a", "string", "discrete")
        self.register_input("string_in_b", "string", "discrete")
        self.register_output("string_out_a", "string", "discrete", "calculated")
        self.register_output("string_out_b", "string", "discrete", "calculated")

    @property
    def real_out_a(self):
        return self.real_in_a

    @property
    def real_out_b(self):
        return self.real_in_b

    @property
    def integer_out_a(self):
        return self.integer_in_a

    @property
    def integer_out_b(self):
        return self.integer_in_b

    @property
    def boolean_out_a(self):
        return self.boolean_in_a

    @property
    def boolean_out_b(self):
        return self.boolean_in_b

    @property
    def string_out_a(self):
        return self.string_in_a

    @property
    def string_out_b(self):
        return self.string_in_b


if __name__ == "__main__":
    fmu = FmiTypes()
    # extra check used to ensure the fmu is initialized according to the standard (not necessary)
    assert fmu.enter_initialization_mode() == Fmi2Status.ok

    assert fmu.exit_initialization_mode() == Fmi2Status.ok

    for i in range(100):
        fmu.real_in_a = float(i)
        fmu.real_in_b = float(i)
        fmu.integer_in_a = int(i)
        fmu.integer_in_b = int(i)
        fmu.boolean_in_a = bool(i)
        fmu.boolean_in_b = bool(i)
        fmu.string_in_a = str(i)
        fmu.string_in_b = str(i)

        assert fmu.do_step(i, i, False) == Fmi2Status.ok

        assert fmu.real_in_a == fmu.real_out_a
        assert fmu.real_in_b == fmu.real_out_b
        assert fmu.integer_in_a == fmu.integer_out_a
        assert fmu.integer_in_b == fmu.integer_out_b
        assert fmu.boolean_in_a == fmu.boolean_out_a
        assert fmu.boolean_in_b == fmu.boolean_out_b
        assert fmu.string_in_a == fmu.string_out_a
        assert fmu.string_in_b == fmu.string_out_b
