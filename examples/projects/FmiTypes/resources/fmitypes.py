from pyfmu.fmi2 import Fmi2Slave, Fmi2Status


class FmiTypes(Fmi2Slave):

    def __init__(self, *args, **kwargs):

        author = "Christian Moeldrup Legaard"
        modelName = "FmiTypes"
        description = "FMU for testing different FMI types"

        super().__init__(
            modelName=modelName,
            author=author,
            description=description,
            *args,
            **kwargs
        )

        # Inputs, outputs and parameters may be defined using the 'register_variable' function
        self.register_variable("real_in", 'real', 'input')
        self.register_variable("real_out", 'real', 'output')
        self.register_variable("integer_in", 'integer', 'input', 'discrete')
        self.register_variable("integer_out", 'integer', 'output', 'discrete')
        self.register_variable("boolean_in", 'boolean', 'input', 'discrete')
        self.register_variable("boolean_out", 'boolean', 'output', 'discrete')
        self.register_variable("string_in", 'string', 'input', 'discrete')
        self.register_variable("string_out", 'string', 'output', 'discrete')

    def _update(self):
        self.real_out = self.real_in
        self.integer_out = self.integer_in
        self.boolean_out = self.boolean_in
        self.string_out = self.string_in

    # functions may be overridden
    def do_step(self, current_time: float, step_size: float, no_prior_step: bool):
        self._update()

    def exit_initialization_mode(self):
        self._update()


if __name__ == "__main__":
    fmu = FmiTypes()
    fmu.enter_initialization_mode()
    fmu.exit_initialization_mode()

    for i in range(100):
        fmu.real_in = float(i)
        fmu.integer_in = int(i)
        fmu.boolean_in = bool(i)
        fmu.string_in = str(i)

        fmu._set_real([0], [1.0])

        s = fmu._do_step(i, i, False)
        assert s == Fmi2Status.ok.value
        assert fmu.real_in == fmu.real_out
        assert fmu.integer_in == fmu.integer_out
        assert fmu.boolean_in == fmu.boolean_out
        assert fmu.string_in == fmu.string_out
