from __future__ import annotations
from typing import Dict, Tuple, Union, List, Callable, Optional
import importlib
import logging
from pathlib import Path
import json
import sys
import multiprocessing as mp
import os

from pyfmu.fmi2.types import (
    Fmi2Status_T,
    Fmi2Type,
    Fmi2Type_T,
    Fmi2Status,
    Fmi2LoggingCallback,
    Fmi2SlaveLike,
    Fmi2Value_T,
    Fmi2DataType_T,
)
from pyfmu.fmi2.logging import FMI2SlaveLogger
from pyfmu.utils import file_uri_to_path


SlaveHandle = int
Fmi2Value = Union[float, int, bool, str]


class Fmi2SlaveContext:
    """Provides functionality to instantiate and invoke FMI-related methods on slaves.
    
    The methods of the class provides functionality 


    ----------------------------
    Value Reference To Attribute
    ----------------------------

    The FMI2 interface lists of indices known as *value references*, to refer to read and write to a specific variable.
    Contrary to this, a slave's variables are accessed as attributes using the name specified in the model description.
    Note that the attribute may defined freely as a "plain" attribute, a property or by overriding the *__setattr__* 
    or similar method.

    The mapping between indices and variable names is automatically made by the context during instantiation
     and is made possible by reading the model description.
    
    .. note::
        The FMI specification does not define how the FMU archive should be extracted and states that a FMU may be executed 
        on a target without its model description file, see (1.1 p.10 "small footprint").
        PyFMU assumes that the modelDescription.xml file is located in the parent folder of the *resources* directory. 

    -------
    Handles
    -------
    
    When a slave is instantiated it is inserted into a list and is associated with a key, referred to as a handle.
    The handle is passed to the environment which can subsequently use it to access a specific slave
    by providing it as an argument when invoking FMI-related methods.

    ------------
    Status Codes
    ------------

    Dut to the FMI's close ties to the C language, integer status codes are used by slaves to communicate the 
    outcome of their operation to the environment. This is in contrast to Python's exception-based fault handling.

    ----------
    Validation
    ----------

    The context class uses a layered approach for validating the data from the FMI interface and the slave.
    Data from the FMI interface is assumed to be correct and will not be validated. On the contrary, the presumption is that data
    from the slave may be erroneous and will be validated.

    """

    def do_step(
        self,
        handle: SlaveHandle,
        current_time: float,
        step_size: float,
        no_set_state_prior: bool,
    ) -> Fmi2Status_T:
        """Invoke step method on the slave specified by the handle.

        Args:
            handle (SlaveHandle): [description]
            current_time (float): [description]
            step_size (float): [description]
            no_set_state_prior (bool): [description]

        Returns:
            Fmi2Status_T: [description]
        """
        return self._call_slave_method(
            handle, "do_step", args=(current_time, step_size, no_set_state_prior)
        )

    def enter_initialization_mode(self, handle: SlaveHandle,) -> Fmi2Status_T:
        return self._call_slave_method(handle, "enter_initialization_mode")

    def exit_initialization_mode(self, handle: SlaveHandle,) -> Fmi2Status_T:
        return self._call_slave_method(handle, "exit_initialization_mode")

    def free_instance(self, handle: SlaveHandle):

        assert handle in self._slaves
        assert handle in self._loggers

        self._loggers[handle].ok(
            f"Removing slave with handle {handle}, current number of slaves is {len(self._slaves)}",
            category="slave_manager",
        )

        logger = self._loggers[handle]

        try:
            del self._slaves[handle]
            del self._loggers[handle]
        except Exception:
            self._loggers[handle].error(
                "Unable to free slave instance, an exception was raised",
                category="slave_manager",
                exc_info=True,
            )
            return

        assert handle not in self._slaves
        assert handle not in self._loggers

        logger.ok(
            f"Slave succesfully removed, number of slaves after is {len(self._slaves)}",
            category="slave_manager",
        )

    def get_xxx(
        self, handle: SlaveHandle, references: List[int]
    ) -> Tuple[List[Fmi2Value], Fmi2Status_T]:
        """Read variables of the slave specified by the handle.
        """
        try:

            attributes = [self._slave_to_refs_to_attr[handle][i] for i in references]
            values = [getattr(self._slaves[handle], a) for a in attributes]

            invalid_type_variables = [
                f"attribute {self._get_attr_for_vref(handle, vref)} has value: {values[idx]}, expected type: {self._get_type_for_vref(handle, vref).__name__}, actual: {type(values[idx])}"
                for idx, vref in enumerate(references)
                if type(values[idx]) != self._get_type_for_vref(handle, vref)
            ]

            if invalid_type_variables != []:
                self._loggers[handle].error(
                    f"One or more of the variables read from the slave has an incorrect type: {invalid_type_variables}",
                    category="slave_manager",
                )
                return ([], Fmi2Status.error)

            # self._loggers[handle].ok(
            #     f"references {references} with names {attributes} has values {values}",
            #     category="slave_manager",
            # )

            return (values, Fmi2Status.ok)
        except Exception:
            self._loggers[handle].error(
                msg=f"writing a variable of the slave failed",
                category="slave_manager",
                exc_info=True,
            )
            return ([], Fmi2Status.error)

    def __init__(self):

        self._slaves: Dict[SlaveHandle, Fmi2SlaveLike] = {}
        self._slave_to_refs_to_attr: Dict[SlaveHandle, Dict[int, str]] = {}
        self._slave_to_refs_to_types: Dict[
            SlaveHandle, Dict[int, Union[float, int, bool, str]]
        ] = {}
        self._loggers: Dict[SlaveHandle, FMI2SlaveLogger] = {}
        self._log_calls_to_slave = False
        self._awaiting_instantiation_handles = set()
        logging.basicConfig(level=logging.DEBUG)

        if "win" in sys.platform:
            mp.set_executable(os.path.join(sys.exec_prefix, "pythonw.exe"))

    def instantiate(
        self,
        instance_name: str,
        fmu_type: Fmi2Type_T,
        guid: str,
        resources_uri: str,
        logging_callback: Optional[Fmi2LoggingCallback],
        visible: bool,
        logging_on: bool,
    ) -> Optional[SlaveHandle]:
        """Create a new instance of the specified FMU and return a handle to the caller.

        The process of doing this is:
            1. The slave configuration is located in the resources directory.
            2. The name of the slave class and the script defining it is read from the configuration.
            3. The object is instantiated and stored in the manager.
            4. A handle to the instance is returned to the FMI interface.

        Args:
            instance_name: identifier of the slave instance
            type: [description]
            guid: [description]
            resources_uri: [description]
            logging_callback: [description]
            visible (bool): if false, limit the FMUs interaction with the user plotting and animatios, see (2.1.5 p.19)
            logging_on (bool): [description]

        Returns:
            SlaveHandle: [description]
        """

        # get a unused handle which is not currently in use
        # Note that some operation in CPython such imports will release the GIL
        def get_free_handle() -> SlaveHandle:
            i = 0
            while i in self._slaves or i in self._awaiting_instantiation_handles:
                i += 1
            return i

        handle = get_free_handle()

        self._awaiting_instantiation_handles.add(handle)

        assert handle not in self._slaves

        logger = FMI2SlaveLogger(
            instance_name=instance_name,
            slave_handle=handle,
            callback=logging_callback,
            log_stdout=False,
        )

        logger.ok(
            f"Creating instance of FMU with name {instance_name}, fmu_type: {fmu_type}, guid: {guid}, resources_uri {resources_uri}, logging_callback: {logging_callback}, visible: {visible}, logging_on: {logging_on}",
            category="slave_manager",
        )

        if fmu_type is not Fmi2Type.co_simulation:
            raise NotImplementedError("Currently, only co-simulation is supported.")

        try:
            url_path = file_uri_to_path(resources_uri)

            if not str(url_path) in sys.path:
                sys.path.append(str(url_path))

            # read configuration
            config_path = url_path / "slave_configuration.json"
            logger.ok(f"Reading configuration {config_path}", category="slave_manager")
            config = None
            with open(config_path, "r") as f:
                config = json.load(f)

            slave_module = Path(config["slave_script"]).stem
            slave_class = config["slave_class"]

            logger.ok(
                msg=f"Configuration loaded, instantiating slave class {slave_class} defined in script {config['slave_script']}",
                category="slave_manager",
            )

            # instantiate object
            kwargs = {"logger": logger}
            instance: Fmi2SlaveLike = getattr(
                importlib.import_module(slave_module), slave_class
            )(**kwargs)

            logger.ok(
                "creating mapping from value references to their names and data types",
                category="slave_manager",
            )

            self._slave_to_refs_to_attr[handle] = {
                v.value_reference: v.name for v in instance.variables
            }

            self._slave_to_refs_to_types[handle] = {
                v.value_reference: {
                    "real": float,
                    "integer": int,
                    "boolean": bool,
                    "string": str,
                }[v.data_type]
                for v in instance.variables
            }

            assert handle not in self._slaves
            assert handle not in self._loggers

            self._slaves[handle] = instance
            self._loggers[handle] = logger
            self._awaiting_instantiation_handles.remove(handle)

            logger.ok(
                f"An slave object has been instantiated successfully and assigned the handle: {handle}",
                category="slave_manager",
            )

            return handle

        except Exception:
            logger.error(
                f"Instantiation failed an exception was raised",
                category="slave_manager",
                exc_info=True,
            )
            return None

    def reset(self, handle: SlaveHandle) -> Fmi2Status_T:
        return self._call_slave_method(handle, "reset")

    def terminate(self, handle: SlaveHandle) -> Fmi2Status_T:
        return self._call_slave_method(handle, "terminate")

    def setup_experiment(
        self,
        handle: SlaveHandle,
        start_time: float,
        tolerance: float = None,
        stop_time: float = None,
    ) -> Fmi2Status_T:
        return self._call_slave_method(
            handle, "setup_experiment", args=(start_time, tolerance, stop_time)
        )

    def set_xxx(
        self, handle: SlaveHandle, references: List[int], values: List[Fmi2Value]
    ) -> Fmi2Status_T:
        """Set variables of the slave specified by the handle.

        Args:
            handle (SlaveHandle): [description]
            references (List[int]): [description]
            values (List[Fmi2Value]): [description]

        Returns:
            Fmi2Status_T: [description]
        """

        a = None
        v = None
        try:
            attributes = [self._slave_to_refs_to_attr[handle][i] for i in references]

            invalid_type_variables = [
                f"attribute {self._get_attr_for_vref(handle, vref)} has value: {values[idx]}, expected type: {self._get_type_for_vref(handle, vref).__name__}, actual: {type(values[idx])}"
                for idx, vref in enumerate(references)
                if type(values[idx]) != self._get_type_for_vref(handle, vref)
            ]

            if invalid_type_variables != []:
                self._loggers[handle].error(
                    f"One or more of the variables received from the envrionment has an incorrect type: {invalid_type_variables}",
                    category="slave_manager",
                )
                return Fmi2Status.error

            for a, v in zip(attributes, values):
                setattr(self._slaves[handle], a, v)

            return Fmi2Status.ok

        except Exception:

            self._loggers[handle].error(
                msg=f"Failed setting variable: {a} to the value: {v}. Ensure that the slave defines a attribute a matching name.",
                exc_info=True,
            )
            return Fmi2Status.error

    def set_debug_logging(
        self, handle: SlaveHandle, categories: list[str], logging_on: bool
    ) -> Fmi2Status_T:
        return self._call_slave_method(
            handle, "set_debug_logging", args=(categories, logging_on)
        )

    def _call_slave_method(self, handle: SlaveHandle, fname: str, args=(), kwargs={}):

        assert handle in self._slaves
        assert hasattr(self._slaves[handle], fname)

        try:

            if self._log_calls_to_slave:
                self._loggers[handle].ok(
                    f"calling slave's {fname} method", category="slave_manager"
                )

            status = getattr(self._slaves[handle], fname)(*args, **kwargs)

            if status not in range(Fmi2Status.ok, Fmi2Status.pending + 1):
                self._loggers[handle].error(
                    f"call to slave's {fname} returned an invalid status code: {status}",
                    category="slave_manager",
                )
                return Fmi2Status.error

            return status

        except Exception:
            self._loggers[handle].error(
                msg=f"call to slave's {fname} raised an exception",
                exc_info=True,
                category="slave_manager",
            )
            return Fmi2Status.error

    def _get_type_for_vref(
        self, handle: SlaveHandle, vref: int
    ) -> Union[float, int, bool, str]:
        return self._slave_to_refs_to_types[handle][vref]

    def _get_attr_for_vref(self, handle: SlaveHandle, vref: int) -> str:
        return self._slave_to_refs_to_attr[handle][vref]
