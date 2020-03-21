from abc import ABC

from pyfmu.fmi2 import validate_vc, get_default_initial, get_possible_initial,Fmi2DataTypes, Fmi2Initial, Fmi2Causality, Fmi2Variability


class Fmi2ScalarVariable(ABC):

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


        is_valid_start = Fmi2ScalarVariable.validate_start_value(
            data_type=data_type,
            causality=causality,
            variability = variability,
            initial=initial,
            start=start)

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

    @staticmethod
    def validate_start_value(data_type, causality, initial, variability, start):
        must_be_defined = Fmi2ScalarVariable.should_define_start(variability, causality, initial)

        is_defined = start != None
        if(must_be_defined ^ is_defined):
            s = "must be defined" if not is_defined else "may not be defined"
            return f"Start values {s} for this combination of variability: {variability}, causality: {causality} and intial: {initial}"


        if(must_be_defined):

            allowed_types = {
                Fmi2DataTypes.real : ({int,float},int.__init__),
                Fmi2DataTypes.boolean : ({bool},bool.__init__),
                Fmi2DataTypes.integer : ({int},int.__init__),
                Fmi2DataTypes.string : ({str},str.__init__),
            }


            types,_ = allowed_types[data_type]
        
            valid_conversion = any([isinstance(start,t) for t in types])
            
            if(not valid_conversion):        
                raise TypeError(f'Illegal combination of data type and start value. Type is {data_type} start is {start}.')
        

        return None

    @staticmethod
    def should_define_start(variability: Fmi2Variability, causality: Fmi2Causality, initial: Fmi2Initial) -> bool:
        """Returns true if the combination requires that a start value is defined, otherwise false.

        For reference check the FMI2 specification p.54 for a description of which combination are allowed.
        """
        # see fmi2 spec p.54
        must_define_start = (initial in {Fmi2Initial.exact, Fmi2Initial.approx}
                            or causality in {Fmi2Causality.parameter, Fmi2Causality.input}
                            or variability in {Fmi2Variability.constant})

        can_not_define_start = (
            initial == Fmi2Initial.calculated or causality == Fmi2Causality.independent)

        # should be mutually exclusive
        assert(must_define_start != can_not_define_start)

        return must_define_start

    def __repr__(self):
        initial_str = self.initial.value if self.initial else 'notPermitted'
        return f'{self.name}:{self.data_type.value}:{self.causality.value}:{initial_str}'

    def __str__(self):
        return self.__repr__()