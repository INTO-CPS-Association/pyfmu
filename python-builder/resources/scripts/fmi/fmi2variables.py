from abc import ABC

from fmi2validation import validate_vc, get_default_initial_for, get_possible_initial_for
import fmi2validation
from fmi2types import Fmi2DataTypes, Fmi2Initial, Fmi2Causality, Fmi2Variability


class ScalarVariable(ABC):

    __vr_counter = 0

    def __init__(self, name: str, data_type: Fmi2DataTypes, initial: Fmi2Initial = None, causality: Fmi2Causality = Fmi2Causality.local, variability: Fmi2Variability = Fmi2Variability.continuous, description: str = ""):

        err = validate_vc(
            variability, causality)

        if(err is not None):
            raise Exception(
                "Illegal combination fo variability and causality, FMI2 specification describes the issue with this combination as:\n" + err)

        initial = initial if initial is not None else get_default_initial_for(
            variability, causality)

        allowed_initial = get_possible_initial_for(variability, causality)

        is_valid_initial = initial in allowed_initial

        if(not is_valid_initial):
            raise Exception(
                "Illegal combination of variabilty causality, see FMI2 spec p.49 for legal combinations")

        self.name = name
        self.initial = initial
        self.causality = causality
        self.variability = variability
        self.description = description
        self.value_reference = ScalarVariable.__get_and_increment_vr()

    @staticmethod
    def __get_and_increment_vr():
        vr = ScalarVariable.__vr_counter
        ScalarVariable.__vr_counter += 1
        return vr


class Real(ScalarVariable):

    def __init__(
            self,
            name: str,
            initial: Fmi2Initial = None,
            causality: Fmi2Causality = Fmi2Causality.local,
            variability: Fmi2Variability = Fmi2Variability.continuous,
            start: float = None,
            description: str = ""
    ):
        super().__init__(name, Fmi2DataTypes.real,
                         initial, causality, variability, description)

        c1 = self.initial in {Fmi2Initial.approx, Fmi2Initial.approx}
        c2 = self.causality in {Fmi2Initial}

        err = fmi2validation.validate_start_value(self.variability, self.causality,self.initial, start)

        if(err != None):
            raise ValueError(err)

        self.start = start