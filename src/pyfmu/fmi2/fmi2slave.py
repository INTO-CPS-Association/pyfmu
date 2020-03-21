from abc import ABC, abstractmethod
from typing import List, Iterable, Tuple
from uuid import uuid4
import logging

from pyfmu.fmi2 import Fmi2ScalarVariable,Fmi2LogMessage, Fmi2Logger,Fmi2Causality, Fmi2DataTypes, Fmi2Initial, Fmi2Variability, Fmi2Status


_internal_log_catergory = 'pyfmu'

log = logging.getLogger('fmu')


class Fmi2Slave:

    def __init__(self, modelName: str, author="", copyright="", version="", description="", standard_log_categories=True):
        """Constructs a FMI2

        Arguments:
            modelName {str} -- [description]

        Keyword Arguments:
            author {str} -- [description] (default: {""})
            copyright {str} -- [description] (default: {""})
            version {str} -- [description] (default: {""})
            description {str} -- [description] (default: {""})
            standard_log_categories {bool} -- registers standard logging categories defined by the FMI2 specification (default: {True})
        """

        self.author = author
        self.copyright = copyright
        self.description = description
        self.modelName = modelName
        self.license = license
        self.guid = uuid4()
        self.vars = []
        self.version = version
        self.value_reference_counter = 0
        self.used_value_references = {}

        self.logger = Fmi2Logger()
        if(standard_log_categories):
            self.logger.register_all_standard_categories()

    def register_variable(self,
                          name: str,
                          data_type: Fmi2DataTypes = None,
                          causality=Fmi2Causality.local,
                          variability=Fmi2Variability.continuous,
                          initial: Fmi2Initial = None,
                          start=None,
                          description: str = "",
                          define_attribute: bool = True,
                          value_reference: int = None
                          ):
        """Add a variable to the model such as an input, output or parameter.

        Arguments:
            name {str} -- [description]
            data_type {Fmi2DataTypes} -- [description]

        Keyword Arguments:
            causality {[type]} -- defines the type of the variable, such as input, output or parameter (default: {Fmi2Causality.local})
            variability {[type]} -- defines the time dependency of the variable. (default: {Fmi2Variability.continuous})
            initial {Fmi2Initial} -- defines how the variable is initialized (default: {None})
            start {[type]} -- start value of the variable. (default: {None})
            description {str} -- a description of the variable which is added to the model description (default: {""})
            define_attribute {bool} -- if true, automatically add the specified attribute to instance if it does not already exist. (default: {True})

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
                    * calculated : [fixed|tunable][calculatedParameter|local], [continous|discrete][local|output]
                    * (do not define) : [discrete|continuous]input, continous independent.


        Validation Rules:
            v1: data type and causality (2.2.7 p.48)
                only real valued variables may have causality continuous

            v2: causality and variablity (2.2.7 p.48-49)
                Only the following combinations of variability and causality are allowed:
                * calculatedParameter: {fixed,tunable}
                * independent: {continuous}
                * input : {continuous,discrete}
                * local : {continuous,constant,discrete,fixed,tuneable}
                * output : {continuous,constant,discrete}
                * parameter : {fixed,tuneable}

            v3: initial allowed (2.2.7 p.49)
                Only certain certain intials are allowed for a given combination of varability and causality.

            v4: should define start (2.2.7 p.47)
                Only certain combinations of causality, intial are allowed to provide start values.
                * [exact|approx] -> must define start
                * calculated -> must not define start
                * 

            Ordering:
            i1 -> i2 -> i3 -> v2 -> i4 -> v1 -> v3

        """

        #i1. shorthands and aliases
        type_aliases = {

            None: None,

            Fmi2DataTypes.real: Fmi2DataTypes.real,
            'real': Fmi2DataTypes.real,
            float: Fmi2DataTypes.real,

            Fmi2DataTypes.boolean: Fmi2DataTypes.boolean,
            'bool': Fmi2DataTypes.boolean,
            'boolean': Fmi2DataTypes.boolean,
            bool: Fmi2DataTypes.boolean,

            Fmi2DataTypes.integer: Fmi2DataTypes.integer,
            'int': Fmi2DataTypes.integer,
            'integer': Fmi2DataTypes.integer,
            int: Fmi2DataTypes.integer,

            Fmi2DataTypes.string: Fmi2DataTypes.string,
            'string': Fmi2DataTypes.string,
            'str': Fmi2DataTypes.string,
            str: Fmi2DataTypes.string
        }
        causality_aliases = {
            None: None,

            Fmi2Causality.parameter: Fmi2Causality.parameter,
            'parameter': Fmi2Causality.parameter,

            Fmi2Causality.calculatedParameter: Fmi2Causality.calculatedParameter,
            'calculatedparameter': Fmi2Causality.calculatedParameter,

            Fmi2Causality.input: Fmi2Causality.input,
            'input': Fmi2Causality.input,

            Fmi2Causality.output: Fmi2Causality.output,
            'output': Fmi2Causality.output,

            Fmi2Causality.local: Fmi2Causality.local,
            'local': Fmi2Causality.local,

            Fmi2Causality.independent : Fmi2Causality.independent,
            'independent': Fmi2Causality.independent,
        }
        initial_aliases = {
            None: None,
            Fmi2Initial.exact: Fmi2Initial.exact,
            'exact': Fmi2Initial.exact,

            Fmi2Initial.approx: Fmi2Initial.approx,
            'approx': Fmi2Initial.approx,

            Fmi2Initial.calculated: Fmi2Initial.calculated,
            'calculated': Fmi2Initial.calculated
        }
        variability_aliases = {
            None: None,
            Fmi2Variability.constant: Fmi2Variability.constant,
            'constant': Fmi2Variability.constant,

            Fmi2Variability.fixed: Fmi2Variability.fixed,
            'fixed': Fmi2Variability.fixed,

            Fmi2Variability.tunable: Fmi2Variability.tunable,
            'tunable': Fmi2Variability.tunable,

            Fmi2Variability.discrete: Fmi2Variability.discrete,
            'discrete': Fmi2Variability.discrete,

            Fmi2Variability.continuous: Fmi2Variability.continuous,
            'continuous': Fmi2Variability.continuous
        }

        if(data_type not in type_aliases):
            raise ValueError(
                f'Unrecognized data type: {data_type}. Possible values are {type_aliases.keys()}')

        if(causality not in causality_aliases):
            raise ValueError(
                f'Unrecognized causality: {causality}. Possible values are {causality_aliases.keys()}')

        if(initial not in initial_aliases):
            raise ValueError(
                f'Unrecognized initial: {initial}. Possible values are {initial_aliases.keys()}')

        if(variability not in variability_aliases):
            raise ValueError(
                f'Unrecognized initial: {variability}. Possible values are {variability_aliases.keys()}')

        data_type = type_aliases[data_type]
        causality = causality_aliases[causality]
        initial = initial_aliases[initial]
        variability = variability_aliases[variability]

        # i4. intial default

        case_a = (Fmi2Initial.exact, {Fmi2Initial.exact})
        case_b = (Fmi2Initial.calculated, {
                  Fmi2Initial.approx, Fmi2Initial.calculated})
        case_c = (Fmi2Initial.calculated, {
                  Fmi2Initial.approx, Fmi2Initial.calculated, Fmi2Initial.exact})
        case_de = (None, {None})

        variabilityAndCausality_to_intial = {
            (Fmi2Variability.constant, Fmi2Causality.local): case_a,
            (Fmi2Variability.constant, Fmi2Causality.output): case_a,
            (Fmi2Variability.fixed, Fmi2Causality.parameter) : case_a,
            (Fmi2Variability.tunable, Fmi2Causality.parameter) : case_a,

            (Fmi2Variability.fixed, Fmi2Causality.calculatedParameter): case_b,
            (Fmi2Variability.fixed, Fmi2Causality.local): case_b,
            (Fmi2Variability.tunable, Fmi2Causality.calculatedParameter): case_b,
            (Fmi2Variability.tunable, Fmi2Causality.local): case_b,
      
    
            (Fmi2Variability.discrete, Fmi2Causality.output): case_c,
            (Fmi2Variability.discrete, Fmi2Causality.local): case_c,
            (Fmi2Variability.continuous, Fmi2Causality.output): case_c,
            (Fmi2Variability.continuous, Fmi2Causality.local): case_c,

            (Fmi2Variability.discrete, Fmi2Causality.input) : case_de,
            (Fmi2Variability.continuous, Fmi2Causality.input) : case_de,
            (Fmi2Variability.continuous, Fmi2Causality.independent) : case_de,
        }

        if(initial is None):
            initial = variabilityAndCausality_to_intial[(
                variability, causality)][0]

        # i2. default start values + v4. should define start
        must_define_start = (initial in {Fmi2Initial.exact, Fmi2Initial.approx}
                             or causality in {Fmi2Causality.parameter, Fmi2Causality.input}
                             or variability in {Fmi2Variability.constant})

        can_not_define_start = (
            initial == Fmi2Initial.calculated or causality == Fmi2Causality.independent)

        assert(must_define_start != can_not_define_start)

        if(must_define_start and start is None and data_type is not None):

            type_to_start = {
                Fmi2DataTypes.boolean: False,
                Fmi2DataTypes.integer: 0,
                Fmi2DataTypes.real: 0.0,
                Fmi2DataTypes.string: ''
            }
            start = type_to_start[data_type]

        elif (must_define_start and start is None and data_type is None):
            raise ValueError(
                f"""A start value must be specified for the combination of causality : {causality}, intial : {initial} and variability {variability}.
                 Specify either a start value or the datatype such that a default will be provided.""")

        elif (not must_define_start and start is not None):
            raise ValueError(
                f"""Start value must NOT be specified for the combination of causality : {causality}, intial : {initial} and variability {variability}.""")

        # i3. data type inference
        start_to_type = {
            bool: Fmi2DataTypes.boolean,
            int: Fmi2DataTypes.integer,
            float: Fmi2DataTypes.real,
            str: Fmi2DataTypes.string
        }
        if(data_type is None and start is not None):
            for t in start_to_type:
                if(isinstance(start, t)):
                    data_type = start_to_type[t]
                    break

        #v2. causality and variablity
        if((variability, causality) not in variabilityAndCausality_to_intial):
            raise ValueError(
                f'Illegal combination of causality : {causality} and variablity : {variability}. The combination is not permitted.')


        #v1. type and causality
        if(data_type is not Fmi2DataTypes.real and variability is Fmi2Variability.continuous):
            raise ValueError(
                f'Illegal combination of type : {data_type} and variability : {variability}. Only real valued variables are allowed to be continuous')

        # v3 initial allowed
        if(initial not in variabilityAndCausality_to_intial[variability, causality][1]):
            raise ValueError(
                f'Illegal initial value : {initial} for combination of causality : {causality} and variability : {variability}')

        # if not specified find an unused value reference
        if(value_reference is None):
            value_reference = self._acquire_unused_value_reference()

        var = Fmi2ScalarVariable(name=name, data_type=data_type, initial=initial, causality=causality,
                             variability=variability, description=description, start=start, value_reference=value_reference)

        self.vars.append(var)

        if(define_attribute):
            self._define_variable(var)

    def register_log_category(self, name: str):
        """Registers a new log category.
        This information is used by co-simulation engines to filter messages

        Arguments:
            name {str} -- name of the category.

        Examples:

        ```
        self.register_log_category('runtime validation')

        ```
        """

        pass

    def setup_experiment(self, start_time: float):
        pass

    def enter_initialization_mode(self):
        pass

    def exit_initialization_mode(self):
        pass

    def do_step(self, current_time: float, step_size: float) -> bool:
        pass

    def reset(self):
        pass

    def terminate(self):
        pass

    def __set_debug_logging__(self, logging_on: bool, categories: Iterable[str]) -> None:
        """Defines the set of active log categories for which log messages will logged.
        Messages logged to any other categories will be ignored.


        This function is called by the tool though the fmi2SetDebugLogging function.

        Note that the tool can only "see" categories registered in the model description using the register_log_category.


        Arguments:
            categories {Iterable[str]} -- a set of categories which are set to be active
            logging_on {bool} -- if true, enable the categories, otherwise disable them

        Defaults category mapping:
            FMI2 specifies several standardized categories.

            * logEvents                 : Log all events (during initialization and simulation).
            * logSingularLinearSystems  : Log the solution of linear systems of equations if the solution is singular
                                          (and the tool picked one solution of the infinitely many solutions).
            * logNonlinearSystems       : Log the solution of nonlinear systems of equations.
            * logDynamicStateSelection  : Log the dynamic selection of states.
            * logStatusWarning          : Log messages when returning fmi2Warning status from any function.
            * logStatusDiscard          : Log messages when returning fmi2Discard status from any function.
            * logStatusError            : Log messages when returning fmi2Error status from any function.
            * logStatusFatal            : Log messages when returning fmi2Fatal status from any function.
            * logStatusPending          : Log messages when returning fmi2Pending status from any function.
            * logAll                    : Log all messages.

            The standard standard leaves it up to the implementation to decide which "categories" map to each of the log-categories.

            ``` Python
            self.log(Fmi2Status.OK,"events","initialized FMU")
            ```

        Examples:
        ``` Python
            # standard logging
            fmu = MyFMU()
            fmu.standard_log_catgories()
            fmu.__set_debug_logging__({'LogAll'})

            fmu.log(Fmi2Status.ok,'logEvents',)

        ```
        """

        self.logger.set_active_log_categories(logging_on, categories)

    def log(self, message: str, category=None, status=Fmi2Status.ok) -> None:
        """Logs a message to the fmi interface.

        Note that only categories which are set as active using the __set_debug_logging__, are propageted to the tool.
        The function is called by the tool using with the categories which the user wishes to be active.

        Arguments:
            status {Fmi2Status} -- The current status of the FMU.
            category {str} -- The category of the log message.
            message {str} -- The log message itself.

        Logging categories mappings:


        """

        self.logger.log(message, category, status)

    def __pop_log_messages__(self, n: int) -> Tuple[str, str, str]:
        """Function called by the wrapper to fetch log messages

        Arguments:
            n {int} -- Number of messages to fetch
        """
        if(n > len(self.logger)):
            self.log(
                f"Unable to pop messages. Requested number of log messages: {n}, is larger than the number currently available: {len(self.logger)}.")
            return None

        messages = self.logger.pop_messages(n)

        # for convenience we convert the object into tuples
        messages_tuples = [(m.status.value, m.category, m.message)
                           for m in messages]

        return messages_tuples

    def __get_log_size__(self) -> int:
        """Returns the number of log messages that are currently on the log stack.

        Returns:
            int -- [description]
        """
        return len(self.logger)

    def __get_integer__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_integer():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Integer!")

    def __get_real__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_real():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Real!")

    def __get_boolean__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_boolean():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Boolean!")

    def __get_string__(self, vrs, refs):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_string():
                refs[i] = getattr(self, var.name)
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type String!")

    def __set_integer__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_integer:
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Integer!")

    def __set_real__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_real():
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Real!")

    def __set_boolean__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_boolean():
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type Boolean!")

    def __set_string__(self, vrs, values):
        for i in range(len(vrs)):
            vr = vrs[i]
            var = self.vars[vr]
            if var.is_string():
                setattr(self, var.name, values[i])
            else:
                raise Exception(
                    f"Variable with valueReference={vr} is not of type String!")

    def _define_variable(self, sv: Fmi2ScalarVariable):

        if(not hasattr(self, sv.name)):
            log.debug(f'adding')

            setattr(self, sv.name, sv.start)
            return

        if(sv.initial in {Fmi2Initial.exact, Fmi2Initial.approx}):
            old = getattr(self, sv.name)
            new = sv.start

            if(old != new):
                log.warning(
                    "start value variable defined using the 'register_variable' function does not match initial value")
                setattr(self, sv.name, new)

    def _acquire_unused_value_reference(self) -> int:
        """ Returns the an unused value reference
        """
        while(True):
            vr = self.value_reference_counter
            self.value_reference_counter += 1

            if(vr not in self.used_value_references):
                return vr
