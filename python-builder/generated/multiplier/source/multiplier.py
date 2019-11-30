from fmi2slave import Fmi2Slave, Real, Fmi2Causality, Fmi2Variability

slave_class = "multiplier"

class multiplier(Fmi2Slave):

    Fmi2Slave.author = ""
    Fmi2Slave.modelName = "multiplier"
    Fmi2Slave.description = ""

    def __init__(self):
        super().__init__()

        # Additional initialization code
        pass

    def setup_experiment(self, start_time: float):
        pass

    def enter_initialization_mode(self):
        pass

    def exit_initialization_mode(self):
        pass

    def do_step(self, current_time: float, step_size: float) -> bool:
        return True

    def reset(self):
        pass

    def terminate(self):
        pass