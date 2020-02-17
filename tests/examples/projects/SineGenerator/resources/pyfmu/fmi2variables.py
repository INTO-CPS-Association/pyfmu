from abc import ABC

from .fmi2validation import validate_vc, get_default_initial, get_possible_initial, validate_start_value, should_define_start
from .fmi2types import Fmi2DataTypes, Fmi2Initial, Fmi2Causality, Fmi2Variability


class ScalarVariable(ABC):

    __vr_counter = 0

    def __init__(self,
                 name: str, 
                 data_type: Fmi2DataTypes,
                 initial: Fmi2Initial = None,
                 causality=Fmi2Causality.local,
                 variability=Fmi2Variability.continuous,
                 start = None,
                 description: str = ""):

        # Certain combinations of variablity and causality are not allowed.
        # 2.2.6) p.48
        err = validate_vc(
            variability, causality)

        if(err is not None):
            raise Exception(
                "Illegal combination fo variability and causality, FMI2 specification describes the issue with this combination as:\n" + err)

        # For a given combination of variability and causality only some intial types are allowed
        # 2.2.6) p.49
        allowed_initial = get_possible_initial(variability, causality)

        # FMI defines default values of initial based on variability and causality
        # 2.2.6) p.49 
        initial = initial if initial is not None else get_default_initial(
            variability, causality)

        is_valid_initial = initial in allowed_initial

        if(not is_valid_initial):
            raise Exception(
                "Illegal combination of variabilty causality, see FMI2 spec p.49 for legal combinations")

        # Certain combination of causality,initial and variability requires a start value to be defined, whereas other may prohibit it.
        # 2.2.6) p.46 + p.49
        is_valid_start = validate_start_value(variability,causality,initial,start)

        if(not is_valid_start):
            raise ValueError(f'Illegal start value')

        self.causality = causality
        self.data_type = data_type
        self.description = description
        self.initial = initial
        self.name = name
        self.variability = variability
        self.value_reference = ScalarVariable.__get_and_increment_vr()
        self.start = start
        
    @staticmethod
    def __get_and_increment_vr():
        vr = ScalarVariable.__vr_counter
        ScalarVariable.__vr_counter += 1
        return vr

    def is_real(self) -> bool:
        return self.data_type == Fmi2DataTypes.real

    def is_integer(self) -> bool:
        return self.data_type == Fmi2DataTypes.integer

    def is_boolean(self) -> bool:
        return self.data_type == Fmi2DataTypes.boolean

    def is_string(self) -> bool:
        return self.data_type == Fmi2DataTypes.string