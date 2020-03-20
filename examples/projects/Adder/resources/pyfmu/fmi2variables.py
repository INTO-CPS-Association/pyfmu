from abc import ABC

from .fmi2validation import validate_vc, get_default_initial, get_possible_initial, validate_start_value
from .fmi2types import Fmi2DataTypes, Fmi2Initial, Fmi2Causality, Fmi2Variability


class ScalarVariable(ABC):

    def __init__(self,
                 name: str, 
                 data_type: Fmi2DataTypes,
                 initial: Fmi2Initial = None,
                 causality=Fmi2Causality.local,
                 variability=Fmi2Variability.continuous,
                 start = None,
                 description: str = "",
                 value_reference: int = None):

        err = validate_vc(
            variability, causality)

        if(err is not None):
            raise Exception(
                "Illegal combination fo variability and causality, FMI2 specification describes the issue with this combination as:\n" + err)

        initial = initial if initial is not None else get_default_initial(
            variability, causality)

        allowed_initial = get_possible_initial(variability, causality)

        is_valid_initial = initial in allowed_initial

        if(not is_valid_initial):
            raise Exception(
                "Illegal combination of variabilty causality, see FMI2 spec p.49 for legal combinations")


        is_valid_start = validate_start_value(variability,causality,initial,start)

        if(is_valid_start != None):
            raise Exception("Illegal start value\n")

        self.causality = causality
        self.data_type = data_type
        self.description = description
        self.initial = initial
        self.name = name
        self.variability = variability
        self.start = start
        self.value_reference = value_reference
        

    def is_real(self) -> bool:
        return self.data_type == Fmi2DataTypes.real

    def is_integer(self) -> bool:
        return self.data_type == Fmi2DataTypes.integer

    def is_boolean(self) -> bool:
        return self.data_type == Fmi2DataTypes.boolean

    def is_string(self) -> bool:
        return self.data_type == Fmi2DataTypes.string