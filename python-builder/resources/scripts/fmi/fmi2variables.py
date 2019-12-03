from fmi2validation import validate_combination_variability_causality, get_default_initial_for, get_possible_initial_for
from fmi2types import Fmi2DataTypes, Fmi2Initial, Fmi2Causality, Fmi2Variability


class Variable:

    __vr_counter = 0

    def __init__(self, name: str, data_type: Fmi2DataTypes, initial: Fmi2Initial = None, causality: Fmi2Causality = Fmi2Causality.local, variability: Fmi2Variability = Fmi2Variability.continuous, description: str = ""):

        err = validate_combination_variability_causality(
            variability, causality)

        if(err is not None):
            raise Exception(
                "Illegal combination fo variablity and causality, FMI2 specification describes the issue with this combination as:\n" + err)
        
        initial = initial if initial is not None else get_default_initial_for(variability,causality)

        allowed_initial = get_possible_initial_for(variability,causality)

        is_valid_initial = initial in allowed_initial

        if(not is_valid_initial):
            raise Exception("Illegal combination of variabilty causality, see FMI2 spec p.49 for legal combinations")


        self.name = name
        self.type = data_type
        self.initial = initial
        self.causality = causality
        self.variability = variability
        self.description = description
        self.value_reference = Variable.__get_and_increment_vr()

    @staticmethod
    def __get_and_increment_vr():
        vr = Variable.__vr_counter
        Variable.__vr_counter += 1
        return vr

    def set_description(self, description: str):
        self.description = description
        return self

    def set_initial(self, initial: Fmi2Initial):
        self.initial = initial
        return self

    def set_causality(self, causality: Fmi2Causality):
        self.causality = causality
        return self

    def set_variability(self, variability: Fmi2Variability):
        self.variability = variability
        return self
