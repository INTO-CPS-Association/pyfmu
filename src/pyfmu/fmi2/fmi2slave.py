from abc import ABC, abstractmethod
from typing import List, Iterable, Tuple
from uuid import uuid4
import inspect
import logging
import json
from pathlib import Path
import os
import sys

from pyfmu.fmi2 import Fmi2ScalarVariable, Fmi2CallbackLogger, Fmi2NullLogger, Fmi2Causality, Fmi2DataTypes, Fmi2Initial, Fmi2Variability, Fmi2Status

############### CONFIGURATION ###############
_slave_configuration_name = "slave_configuration.json"

############### LOGGING OF FMI INTERFACE ###############
_internal_log_catergory = 'fmi2slave'
# category if an FMI method implementation fails
_internal_throw_category = Fmi2Status.fatal
# category if an FMI method returns and invalid status
_internal_invalid_status_category = Fmi2Status.fatal
_logging_override_name = "pyfmu_log_all_override"

log = logging.getLogger('fmu')

############### ERRONEOUS READING ###############
_read_wrong_type_status = Fmi2Status.discard
_invalid_fmi_invalid_arguments = Fmi2Status.error
_invalid_return_type_status = Fmi2Status.error
_invalid_external_call_status = Fmi2Status.fatal


class Fmi2Slave:

    def __init__(self,
                 modelName: str,
                 author="",
                 copyright="",
                 version="",
                 description="",
                 logging_callback=None,
                 logging_logAll=False,
                 logging_stdout=False,
                 logging_add_standard_categories=True,
                 logging_slave_fmi_calls=True
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

        self.author = author
        self.copyright = copyright
        self.description = description
        self.modelName = modelName
        self.license = license
        self.guid = uuid4()
        self.vars: Fmi2ScalarVariable = []
        self.version = version
        self.value_reference_counter = 0
        self.used_value_references = {}
        if(logging_callback):
            self.logger = Fmi2CallbackLogger(logging_callback, logging_stdout)
        else:
            self.logger = Fmi2NullLogger()

        if(logging_add_standard_categories):
            self.logger.register_all_standard_categories()

        if(logging_slave_fmi_calls):
            self.logger.register_log_category(_internal_log_catergory)
            self.logger.log(
                'FMI call logging enabled, all fmi calls will be logged', _internal_log_catergory)

        self._configure()

        self.type_to_tuple = {
            Fmi2DataTypes.integer: (int, "integer"),
            Fmi2DataTypes.real: (float, "real"),
            Fmi2DataTypes.boolean: (bool, "boolean"),
            Fmi2DataTypes.string: (str, "string")
        }

    def _configure(self):
        """ Performs configuration of the FMI slave based on the contents of the slave configuration file.

            The configuration function is only available for Fmi2Slaves which are running from inside an FMU, e.g. they have a slave_configuration.json

            Options:
                1. Logging, allows the user to override log settings.
        """

        if(not self._is_running_as_fmu):
            self.log("Skipping configuration due to the FMU running in project-mode",
                     _internal_log_catergory)

        try:

            self.log(
                f"Trying to locate configuration file : {_slave_configuration_name} in Python Path : {sys.path}", _internal_log_catergory)

            config_path = None

            for potential in sys.path:

                p = Path(potential) / _slave_configuration_name

                if(p.is_file()):
                    config_path = p
                    break
            else:
                self.log(
                    'Configuration process failed the file could not be found in Pythons path, continuing using defaults', _internal_log_catergory)
                return

            with open(config_path, 'r') as f:
                config = json.load(f)

                # 1. Logging
                cats = config['logging']['override_log_categories']

                if(len(cats) != 0):
                    self.log(
                        f'Log categories overriden in : {_slave_configuration_name}, marking categories : {cats} as active', _internal_log_catergory)
                    self._set_debug_logging(True, cats)

        except Exception as e:
            print(e)
            self.log(
                f'Configuration process failed due to error : {e}, continuing using default options', _internal_log_catergory, Fmi2Status.warning)

    def _set_resources_path(self, path):
        """Called by the wrapper to set the path to resource folder.

        This is used for configuration.

        Arguments:
            path {[str]} -- Path to the resources folder
        """

        self._resources_path = Path(path)

    def _is_running_as_project(self):
        """Returns true if the Fmi2Slave is running inside a project that has not yet been exported.
        """
        return not self._is_running_as_fmu

    def _is_running_as_fmu(self):
        """Returns true if the FMI2Slave is running from inside an exported FMU
        """
        for potential in sys.path:

            p = Path(potential) / _slave_configuration_name

            if(p.is_file()):
                return True

        return False

    # REGISTER VARIABLES AND LOG CATEGORIES

    def register_variable(self,
                          name: str,
                          data_type: Fmi2DataTypes = None,
                          causality=Fmi2Causality.local,
                          variability=Fmi2Variability.continuous,
                          initial: Fmi2Initial = None,
                          start=None,
                          description: str = "",
                          define_attribute: bool = True,
                          value_reference: int = None,
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

        # i1. shorthands and aliases
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

            Fmi2Causality.independent: Fmi2Causality.independent,
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
            (Fmi2Variability.fixed, Fmi2Causality.parameter): case_a,
            (Fmi2Variability.tunable, Fmi2Causality.parameter): case_a,

            (Fmi2Variability.fixed, Fmi2Causality.calculatedParameter): case_b,
            (Fmi2Variability.fixed, Fmi2Causality.local): case_b,
            (Fmi2Variability.tunable, Fmi2Causality.calculatedParameter): case_b,
            (Fmi2Variability.tunable, Fmi2Causality.local): case_b,


            (Fmi2Variability.discrete, Fmi2Causality.output): case_c,
            (Fmi2Variability.discrete, Fmi2Causality.local): case_c,
            (Fmi2Variability.continuous, Fmi2Causality.output): case_c,
            (Fmi2Variability.continuous, Fmi2Causality.local): case_c,

            (Fmi2Variability.discrete, Fmi2Causality.input): case_de,
            (Fmi2Variability.continuous, Fmi2Causality.input): case_de,
            (Fmi2Variability.continuous, Fmi2Causality.independent): case_de,
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

        # v2. causality and variablity
        if((variability, causality) not in variabilityAndCausality_to_intial):
            raise ValueError(
                f'Illegal combination of causality : {causality} and variablity : {variability}. The combination is not permitted.')

        # v1. type and causality
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
        """Registers a new log category which will be visible to the simulation tool..
        This information is used by co-simulation engines to filter messages.


        Arguments:
            name {str} -- name of the category.

        Examples:

        ```
        self.register_log_category('runtime validation')

        ```
        """

        self.logger.register_log_category(name)

    def _acquire_unused_value_reference(self) -> int:
        """ Returns the an unused value reference
        """
        while(True):
            vr = self.value_reference_counter
            self.value_reference_counter += 1

            if(vr not in self.used_value_references):
                return vr

    # FMI FUNCTIONS

    def _setup_experiment(self,
                          start_time: float,
                          tolerance: float = None,
                          stop_time: float = None):

        return self._do_fmi_call(
            self.setup_experiment,
            start_time,
            stop_time, tolerance)

    def setup_experiment(self,
                         start_time: float,
                         tolerance: float = None,
                         stop_time: float = None):
        pass

    def _enter_initialization_mode(self):
        return self._do_fmi_call(self.enter_initialization_mode)

    def enter_initialization_mode(self):
        pass

    def _exit_initialization_mode(self):

        return self._do_fmi_call(self.exit_initialization_mode)

    def exit_initialization_mode(self):
        pass

    def _do_step(self,
                 current_time: float,
                 step_size: float,
                 no_set_fmu_state_prior: bool):

        return self._do_fmi_call(self.do_step, current_time,
                                 step_size, no_set_fmu_state_prior)

    def do_step(self,
                current_time: float,
                step_size: float,
                no_set_fmu_state_prior: bool):
        pass

    def _reset(self):
        return self._do_fmi_call(self.reset)

    def reset(self):
        pass

    def _terminate(self):
        return self._do_fmi_call(self.terminate)

    def terminate(self):
        pass

    def _set_debug_logging(self, logging_on: bool, categories: Iterable[str]) -> None:

        return self._do_fmi_call(
            self.set_debug_logging,
            logging_on,
            categories)

    def set_debug_logging(self, logging_on: bool, categories: Iterable[str]):
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
            fmu._set_debug_logging({'LogAll'})

            fmu.log(Fmi2Status.ok,'logEvents',)

        ```
        """
        self.logger.set_debug_logging(logging_on, categories)

    def _get_xxx(self, vrs, values, data_type: Fmi2DataTypes):

        t, t_name = self.type_to_tuple[data_type]

        if(not all(isinstance(v, t) for v in values)):
            self.log(f"Unable to get {t_name}, some of the provided values : {values} are not {t_name}.",
                     _internal_log_catergory,
                     _invalid_external_call_status)
            return _invalid_external_call_status

        if(not all(isinstance(vr, int) for vr in vrs)):
            self.log(f"Unable to get {t_name}, some of the provided values references : {vrs} are not integers.",
                     _internal_log_catergory,
                     _invalid_external_call_status
                     )
            return _invalid_external_call_status

        for i, vr in enumerate(vrs):
            var = self.vars[vr]
            if var.is_type(data_type):
                values[i] = getattr(self, var.name)
            else:
                self.log(f"Unable to get {t_name}, some references point to variables : {[self.vars[vr] for vr in vrs]} which are not {t_name}s.",
                         _internal_log_catergory,
                         _invalid_external_call_status
                         )
                return _invalid_external_call_status

        return Fmi2Status.ok

    def _get_integer(self, vrs, values):
        return self._do_fmi_call(self.get_integer, vrs, values)

    def get_integer(self, vrs, values):
        return self._get_xxx(vrs, values, Fmi2DataTypes.integer)

    def _get_real(self, vrs, values):
        return self._do_fmi_call(self.get_real, vrs, values)

    def get_real(self, vrs, values):
        return self._get_xxx(vrs, values, Fmi2DataTypes.real)

    def _get_boolean(self, vrs, values):
        return self._do_fmi_call(self.get_boolean, vrs, values)

    def get_boolean(self, vrs, values):
        return self._get_xxx(vrs, values, Fmi2DataTypes.boolean)

    def _get_string(self, vrs, values):
        return self._do_fmi_call(self.get_string, vrs, values)

    def get_string(self, vrs, values):
        return self._get_xxx(vrs, values, Fmi2DataTypes.string)

    def _set_xxx(self, vrs, values, data_type: Fmi2DataTypes):
        """Generic implementation of setter methods used for set_real, set_integer, set_boolean and set_string

        Arguments:
            vrs {List[int]} -- List of value references of the variables to be set
            values {List[]} -- List of the values which must be assigned to the specified references.
            data_type {Fmi2DataTypes} -- The datatype "expected" data type of the variable, used for validation.

        Returns:
            [FmiStatus] -- a status indicating whether the call was succesful
        """

        t, t_name = self.type_to_tuple[data_type]

        if(not all(isinstance(v, t) for v in values)):
            self.log(f"Unable to set {t_name}, some of the provided values : {values} are not {t_name}.",
                     _internal_log_catergory,
                     _invalid_external_call_status)
            return _invalid_external_call_status

        if(not all(isinstance(vr, int) for vr in vrs)):
            self.log(f"Unable to set {t_name}, some of the provided values references : {vrs} are not integers.",
                     _internal_log_catergory,
                     _invalid_external_call_status
                     )
            return _invalid_external_call_status

        for i, vr in enumerate(vrs):
            var = self.vars[vr]
            if var.is_type(data_type):
                setattr(self, var.name, values[i])
            else:
                self.log(
                    f"Unable to set variables. Variable with value reference {vr} is not an {t_name}",
                    _internal_log_catergory,
                    _invalid_external_call_status)
                return _invalid_external_call_status

        return Fmi2Status.ok

    def _set_integer(self, vrs, values):
        return self._do_fmi_call(self.set_integer, vrs, values)

    def set_integer(self, vrs, values):
        return self._set_xxx(vrs, values, Fmi2DataTypes.integer)

    def _set_real(self, vrs, values):
        return self._do_fmi_call(self.set_real, vrs, values)

    def set_real(self, vrs, values):
        return self._set_xxx(vrs, values, Fmi2DataTypes.real)

    def _set_boolean(self, vrs, values):
        return self._do_fmi_call(self.set_boolean, vrs, values)

    def set_boolean(self, vrs, values):
        return self._set_xxx(vrs, values, Fmi2DataTypes.boolean)

    def _set_string(self, vrs, values):
        return self._do_fmi_call(self.set_string, vrs, values)

    def set_string(self, vrs, values):
        return self._set_xxx(vrs, values, Fmi2DataTypes.string)

    def _do_fmi_call(self, f, *args, **kwargs) -> Fmi2Status:
        """ Performs the call to the fmi function implemented by the subclass and returns the status.

        Purpose of the function is:
        1. logging of the function calls
        2. handle exceptions in implementation
        3. convert return values to FMI status values

        Arguments:
            f {[type]} -- the function to be invoked.
        """

        if(not callable(f)):
            self.log("Whoops", Fmi2Status.error)
            raise TypeError(
                f'The argument : {f} does not appear to be a function, ensure that the argument is pointing to the FMI function implemented by the subclass, such as do_step.')

        try:
            self.log(
                f'Calling {f.__name__} with arguments : {args} and key-word arguments : {kwargs}', _internal_log_catergory)
            s = f(*args, **kwargs)
        except Exception as e:
            self.log(
                f'Call resulted in an exception being raise : {e}. Treating this as a {_internal_throw_category}.', _internal_log_catergory, _internal_throw_category)
            return _internal_invalid_status_category
        # convert return status to appropritate fmi status
        return_to_status = {
            None: Fmi2Status.ok,
            True: Fmi2Status.ok,
            False: Fmi2Status.fatal,
            Fmi2Status.ok: Fmi2Status.ok,
            Fmi2Status.warning: Fmi2Status.warning,
            Fmi2Status.discard: Fmi2Status.discard,
            Fmi2Status.error: Fmi2Status.error,
            Fmi2Status.fatal: Fmi2Status.fatal,
            Fmi2Status.pending: Fmi2Status.pending,
        }

        s_fmi = None

        if(s in return_to_status):
            s_fmi = return_to_status[s]
            self.log(
                f'Call was succesful, status returned : {s} treated as : {s_fmi}', _internal_log_catergory, s_fmi)
        else:
            s_fmi = Fmi2Status.warning
            self.log(
                f'Call was succesful, but returned status : {s} was invalid, treating this as : {s_fmi}', _internal_log_catergory, s_fmi)

        return s_fmi.value

    def _define_variable(self, sv: Fmi2ScalarVariable):

        if(not hasattr(self, sv.name)):

            setattr(self, sv.name, sv.start)
            return

        if(sv.initial in {Fmi2Initial.exact, Fmi2Initial.approx}):
            old = getattr(self, sv.name)
            new = sv.start

            if(old != new):
                self.log(
                    f"start value variable defined using the 'register_variable' function does not match initial value, using the new value: {new}",
                    _internal_log_catergory,
                    Fmi2Status.warning)
                setattr(self, sv.name, new)

    # Logging

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

    def _get_log_size(self):
        """Returns the number of log messages that are currently on the log stack.

        Returns:
            int -- [description]
        """
        return len(self.logger)

    def _pop_log_messages(self, n: int):
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

    """Called by the wrapper to register a log callback function.
    """

    def _register_log_callback(self, callback):

        print(f"callback registered {callback}")
        t = (0, _internal_log_catergory, "log callback registered")
        callback(0, _internal_log_catergory, "log callback registered")
        # callback(t)
        #args = (0,_internal_log_catergory,"log callback function registered")
        # callback(args)
        #self._log_callback = callback

    @property
    def available_categories(self):
        return self.logger.available_categories
