from typing import List, Tuple, Union
from uuid import uuid4

from pyfmu.fmi2.validation import infer_undefined_attributes

from pyfmu.fmi2.types import (
    Fmi2SlaveBase,
    Fmi2Status,
    Fmi2Variable,
    Fmi2ScalarVariable,
    Fmi2DataTypes,
    Fmi2Variability,
    Fmi2Causality,
    Fmi2Initial,
)


class Fmi2Slave(Fmi2SlaveBase):
    def __init__(
        self,
        modelName: str,
        author="",
        copyright="",
        version="",
        description="",
        logging_callback=None,
        logging_logAll=False,
        logging_stdout=False,
        logging_add_standard_categories=True,
        logging_slave_fmi_calls=True,
        check_uninitialized_variables=True,
    ):
        """Constructs a FMI2

        Arguments:
            modelName {str} -- [description]

        Keyword Arguments:
            author {str} -- [description] (default: {""})
            copyright {str} -- [description] (default: {""})
            version {str} -- [description] (default: {""})
            description {str} -- [description] (default: {""})
            logging_add_standard_categories {bool} -- registers standard logging categories defined by the FMI2 specification (default: {True})
            add_logging_override_param {bool} -- if true, add a boolean parameter to the FMU which allows it to log all, useful for FMPy (default: {True}).
        """

        self._author = author
        self._copyright = copyright
        self._description = description
        self._model_name = modelName
        self._license = license
        self._guid = uuid4()
        self._vars: List[Fmi2ScalarVariable] = []
        self._version = version
        self._value_reference_counter = 0
        self._used_value_references = {}

        self.type_to_tuple = {
            Fmi2DataTypes.integer: (int, "integer"),
            Fmi2DataTypes.real: (float, "real"),
            Fmi2DataTypes.boolean: (bool, "boolean"),
            Fmi2DataTypes.string: (str, "string"),
        }

    def register_variable(
        self,
        name: str,
        data_type: Fmi2DataTypes = None,
        causality=Fmi2Causality.local,
        variability=Fmi2Variability.continuous,
        initial: Fmi2Initial = None,
        start=None,
        description: str = "",
        define_attribute: bool = True,
        value_reference: int = None,
    ) -> Union[float, int, bool, str]:
        """Add a variable to the model such as an input, output or parameter.

        Arguments:
            name -- [description]
            data_type -- [description]

        Keyword Arguments:
            causality -- defines the type of the variable, such as input, output or parameter (default: {Fmi2Causality.local})
            variability -- defines the time dependency of the variable. (default: {Fmi2Variability.continuous})
            initial -- defines how the variable is initialized (default: {None})
            start -- start value of the variable. (default: {None})
            description -- a description of the variable which is added to the model description (default: {""})
            define_attribute -- if true, automatically add the specified attribute to instance if it does not already exist. (default: {True})

        Inference Rules:
            i1. shorthands and aliases:
                data_type,causality,initial and variablity can be defined using string shorthands.

            i2. default start values:
                if data_type is defined but start is undefined, default values are used based on data_type

            i3. data type inference:
                if data_type is undefined but start is defined, data_type is inferred from start's type.

            i4. initial based on causality and variability (2.2.7 p.49)
                Default initial are defined based on the combination of causality and variability:
                    * exact : constant[local|output], [fixed|tunable]parameter
                    * calculated : [fixed|tunable][calculatedParameter|local], [continuos|discrete][local|output]
                    * (do not define) : [discrete|continuous]input, continuos independent.


        Validation Rules:
            v1: data type and causality (2.2.7 p.48)
                only real valued variables may have causality continuous

            v2: causality and variability (2.2.7 p.48-49)
                Only the following combinations of variability and causality are allowed:
                * calculatedParameter: {fixed,tunable}
                * independent: {continuous}
                * input : {continuous,discrete}
                * local : {continuous,constant,discrete,fixed,tuneable}
                * output : {continuous,constant,discrete}
                * parameter : {fixed,tuneable}

            v3: initial allowed (2.2.7 p.49)
                Only certain certain initials are allowed for a given combination of varability and causality.

            v4: should define start (2.2.7 p.47)
                Only certain combinations of causality, initial are allowed to provide start values.
                * [exact|approx] -> must define start
                * calculated -> must not define start
                *

            Ordering:
            i1 -> i2 -> i3 -> v2 -> i4 -> v1 -> v3

        """

        # i1. shorthands and aliases
        type_aliases = {
            None: None,
            Fmi2DataTypes.real: Fmi2DataTypes.real,
            "real": Fmi2DataTypes.real,
            float: Fmi2DataTypes.real,
            Fmi2DataTypes.boolean: Fmi2DataTypes.boolean,
            "bool": Fmi2DataTypes.boolean,
            "boolean": Fmi2DataTypes.boolean,
            bool: Fmi2DataTypes.boolean,
            Fmi2DataTypes.integer: Fmi2DataTypes.integer,
            "int": Fmi2DataTypes.integer,
            "integer": Fmi2DataTypes.integer,
            int: Fmi2DataTypes.integer,
            Fmi2DataTypes.string: Fmi2DataTypes.string,
            "string": Fmi2DataTypes.string,
            "str": Fmi2DataTypes.string,
            str: Fmi2DataTypes.string,
        }
        causality_aliases = {
            None: None,
            Fmi2Causality.parameter: Fmi2Causality.parameter,
            "parameter": Fmi2Causality.parameter,
            Fmi2Causality.calculatedParameter: Fmi2Causality.calculatedParameter,
            "calculatedparameter": Fmi2Causality.calculatedParameter,
            Fmi2Causality.input: Fmi2Causality.input,
            "input": Fmi2Causality.input,
            Fmi2Causality.output: Fmi2Causality.output,
            "output": Fmi2Causality.output,
            Fmi2Causality.local: Fmi2Causality.local,
            "local": Fmi2Causality.local,
            Fmi2Causality.independent: Fmi2Causality.independent,
            "independent": Fmi2Causality.independent,
        }
        initial_aliases = {
            None: None,
            Fmi2Initial.exact: Fmi2Initial.exact,
            "exact": Fmi2Initial.exact,
            Fmi2Initial.approx: Fmi2Initial.approx,
            "approx": Fmi2Initial.approx,
            Fmi2Initial.calculated: Fmi2Initial.calculated,
            "calculated": Fmi2Initial.calculated,
        }
        variability_aliases = {
            None: None,
            Fmi2Variability.constant: Fmi2Variability.constant,
            "constant": Fmi2Variability.constant,
            Fmi2Variability.fixed: Fmi2Variability.fixed,
            "fixed": Fmi2Variability.fixed,
            Fmi2Variability.tunable: Fmi2Variability.tunable,
            "tunable": Fmi2Variability.tunable,
            Fmi2Variability.discrete: Fmi2Variability.discrete,
            "discrete": Fmi2Variability.discrete,
            Fmi2Variability.continuous: Fmi2Variability.continuous,
            "continuous": Fmi2Variability.continuous,
        }

        if data_type not in type_aliases:
            raise ValueError(
                f"Unrecognized data type: {data_type}. Possible values are {type_aliases.keys()}"
            )

        if causality not in causality_aliases:
            raise ValueError(
                f"Unrecognized causality: {causality}. Possible values are {causality_aliases.keys()}"
            )

        if initial not in initial_aliases:
            raise ValueError(
                f"Unrecognized initial: {initial}. Possible values are {initial_aliases.keys()}"
            )

        if variability not in variability_aliases:
            raise ValueError(
                f"Unrecognized initial: {variability}. Possible values are {variability_aliases.keys()}"
            )

        data_type = type_aliases[data_type]
        causality = causality_aliases[causality]
        initial = initial_aliases[initial]
        variability = variability_aliases[variability]

        data_type, causality, variability, initial, start = infer_undefined_attributes(
            data_type, causality, variability, initial, start
        )

        # if not specified find an unused value reference
        if value_reference is None:
            value_reference = self._acquire_unused_value_reference()

        var = Fmi2ScalarVariable(
            name=name,
            data_type=data_type,
            initial=initial,
            causality=causality,
            variability=variability,
            description=description,
            start=start,
            value_reference=value_reference,
        )

        self._vars.append(var)

        if define_attribute:
            self._define_variable(var)

        return start

    def register_log_category(self, name: str):
        """Registers a new log category which will be visible to the simulation tool..
        This information is used by co-simulation engines to filter messages.


        Arguments:
            name {str} -- name of the category.

        Examples:

        ```
        self.register_log_category('runtime validation')

        ```
        """

        self._logger.register_log_category(name)

    def do_step(
        self, current_time: float, step_size: float, no_set_fmu_state_prior: bool
    ) -> Fmi2Status:
        return Fmi2Status.ok

    def get_xxx(self, references: List[int]) -> Tuple[List[Fmi2Variable], Fmi2Status]:
        raise NotImplementedError()

    def set_xxx(self, references: List[int], values: List[Fmi2Variable]) -> Fmi2Status:
        raise NotImplementedError()

    def setup_experiment(
        self, start_time: float, stop_time: float = None, tolerance: float = None
    ) -> Fmi2Status:
        return Fmi2Status.ok

    def enter_initialization_mode(self) -> Fmi2Status:
        return Fmi2Status.ok

    def exit_initialization_mode(self) -> Fmi2Status:
        return Fmi2Status.ok

    def reset(self) -> Fmi2Status:
        return Fmi2Status.ok

    def _acquire_unused_value_reference(self) -> int:
        """ Returns the an unused value reference
        """
        while True:
            vr = self._value_reference_counter
            self._value_reference_counter += 1

            if vr not in self._used_value_references:
                return vr

    def _define_variable(self, sv: Fmi2ScalarVariable):

        if not hasattr(self, sv.name):

            setattr(self, sv.name, sv.start)
            return

        if sv.initial in {Fmi2Initial.exact, Fmi2Initial.approx}:
            old = getattr(self, sv.name)
            new = sv.start

            if old != new:
                self.log(
                    f"start value variable defined using the 'register_variable' function does not match initial value, using the new value: {new}",
                    "wrapper",
                    Fmi2Status.warning,
                )
                setattr(self, sv.name, new)

    @property
    def log_categories(self) -> List[str]:
        return []  # TODO

    @property
    def variables(self) -> List[Fmi2ScalarVariable]:
        return self._vars
