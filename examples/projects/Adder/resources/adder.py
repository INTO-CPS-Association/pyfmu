from pyfmu.fmi2 import Fmi2Slave, Fmi2Causality, Fmi2Variability, Fmi2DataTypes, Fmi2Initial


class Adder(Fmi2Slave):

    def __init__(self, *args, **kwargs):

        author = ""
        modelName = "Adder"
        description = ""

        super().__init__(
            modelName=modelName,
            author=author,
            description=description,
            *args,
            **kwargs
            )

        self.register_variable("s", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.output)
        self.register_variable("a", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0.0)
        self.register_variable("b", data_type=Fmi2DataTypes.real, causality=Fmi2Causality.input, start=0.0)


    def exit_initialization_mode(self):
        self.s = self.a + self.b
        return True

    def do_step(self, current_time: float, step_size: float,no_set_fmu_state_prior : bool):
        self.s = self.a + self.b
        return True


if __name__ == "__main__":

    def callback(status,category,message):
        print(f"{status}:{category}:{message}")

    fmu = Adder(logging_callback=callback)
    fmu._set_debug_logging(True,["logAll"])

    fmu._do_step(0,1,False)
    fmu._do_step(1,2,False)
