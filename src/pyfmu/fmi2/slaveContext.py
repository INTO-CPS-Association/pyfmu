from __future__ import annotations
from typing import Dict, Tuple, Union, List, Callable, Optional
import importlib
import logging
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

from pyfmu.fmi2.types import (
    Fmi2Status_T,
    Fmi2Type,
    Fmi2Type_T,
    Fmi2Status,
    Fmi2LoggingCallback,
    Fmi2SlaveLike,
    Fmi2Value_T,
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

    def __init__(self):

        self._slaves: Dict[SlaveHandle, Fmi2SlaveLike] = {}
        self._slave_to_ids_to_attr: Dict[SlaveHandle, Dict[int, str]] = {}
        self._loggers: Dict[SlaveHandle, FMI2SlaveLogger] = {}

        logging.basicConfig(level=logging.DEBUG)

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

        print(
            f"instance_name {instance_name}, fmu_type: {fmu_type}, guid: {guid}, resources_uri {resources_uri}, logging_callback: {logging_callback}, visible: {visible}, logging_on: {logging_on}"
        )

        def get_free_handle() -> SlaveHandle:
            i = 0
            while i in self._slaves:
                i += 1
            return i

        handle = get_free_handle()

        logger = FMI2SlaveLogger(
            instance_name=instance_name,
            slave_handle=handle,
            callback=logging_callback,
            log_stdout=False,
        )

        if fmu_type is not Fmi2Type.co_simulation:
            raise NotImplementedError("Currently, only co-simulation is supported.")

        try:
            url_path = file_uri_to_path(resources_uri)

            if not str(url_path) in sys.path:
                sys.path.append(str(url_path))

            # read configuration
            config_path = url_path / "slave_configuration.json"
            logger.ok(f"Reading configuration {config_path}")
            config = None
            with open(config_path, "r") as f:
                config = json.load(f)

            slave_module = Path(config["slave_script"]).stem
            slave_class = config["slave_class"]

            logger.ok(
                msg=f"Configuration loaded, instantiating slave class {slave_class} defined in script {config['slave_script']}"
            )

            # instantiate object¨
            kwargs = {"logger": logger}
            instance = getattr(importlib.import_module(slave_module), slave_class)(
                **kwargs
            )

            logger.ok(
                msg="Extracting mapping between value references and attribute names from modelDescription.xml"
            )

            with open(url_path.parent / "modelDescription.xml", "r") as f:
                variables = ET.parse(source=f).getroot().iter("ScalarVariable")
                vref_to_attr = {
                    int(v.attrib["valueReference"]): v.attrib["name"] for v in variables
                }
                self._slave_to_ids_to_attr[handle] = vref_to_attr

            self._slaves[handle] = instance
            self._loggers[handle] = logger

            logger.ok("Instance succesfully instantiated")

            return handle

        except Exception:
            logger.error(f"Instantiation failed an exception was raised", exc_info=True)
            return None

    def free_instance(self, handle: SlaveHandle) -> Fmi2Value_T:

        self._loggers[handle].ok(
            f"Removing slave with handle {handle}, current number of slaves is {len(self._slaves)}"
        )

        try:
            del self._slaves[handle]
        except Exception:
            self._loggers[handle].error(
                "Unable to free slave instance, an exception was raised", exc_info=True
            )
            return Fmi2Status.fatal

        self._loggers[handle].ok(
            f"Slave succesfully removed, number of slaves after is {len(self._slaves)}"
        )

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

        try:

            status = self._slaves[handle].do_step(
                current_time, step_size, no_set_state_prior,
            )

            if Fmi2SlaveContext._is_valid_status(status) is False:
                self._loggers[handle].error(
                    f"call to slave's do_step returned an invalid status code: {status}",
                )
                return Fmi2Status.error

            return status

        except Exception:
            self._loggers[handle].error(
                msg="invoking do_step raised an error", exc_info=True
            )
            return Fmi2Status.error

    def setup_experiment(
        self,
        handle: SlaveHandle,
        start_time: float,
        tolerance: float = None,
        stop_time: float = None,
    ) -> Fmi2Status_T:

        try:
            status = self._slaves[handle].setup_experiment(
                start_time=start_time, tolerance=tolerance, stop_time=stop_time
            )

            if Fmi2SlaveContext._is_valid_status(status) is False:
                self._loggers[handle].error(
                    f"call to slave's setup_experiment returned an invalid status code: {status}",
                )
                return Fmi2Status.error

            return status

        except Exception:
            self._loggers[handle].error(
                msg="call to the slave's setup_experiment raised an exception",
                exc_info=True,
            )
            return Fmi2Status.error

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

        try:
            attributes = [self._slave_to_ids_to_attr[handle][i] for i in references]

            self._loggers[handle].ok(
                f"Setting references {references} with names {attributes} to values {values}"
            )

            for a, v in zip(attributes, values):
                setattr(self._slaves[handle], a, v)

            return Fmi2Status.ok

        except Exception:

            self._loggers[handle].error(
                msg=f"writing a variable of the slave failed", exc_info=True,
            )
            return Fmi2Status.error

    def set_debug_logging(
        self, handle: SlaveHandle, categories: list[str], logging_on: bool
    ) -> Fmi2Status_T:

        try:
            self._slaves[handle].set_debug_logging(categories, logging_on)
            return Fmi2Status.ok
        except Exception:
            self._loggers[handle].error(
                msg="Call to set_debug_logging of slave failed", exc_info=True
            )
            return Fmi2Status.error

    def get_xxx(
        self, handle: SlaveHandle, references: List[int]
    ) -> Tuple[List[Fmi2Value], Fmi2Status_T]:
        """Read variables of the slave specified by the handle.
        """
        try:
            attributes = [self._slave_to_ids_to_attr[handle][i] for i in references]
            values = [getattr(self._slaves[handle], a) for a in attributes]

            self._loggers[handle].ok(
                f"references {references} with names {attributes} has values {values}"
            )

            return (values, Fmi2Status.ok)
        except Exception:
            self._loggers[handle].error(
                msg=f"writing a variable of the slave failed", exc_info=True,
            )
            return ([], Fmi2Status.error)

    def enter_initialization_mode(self, handle: SlaveHandle,) -> Fmi2Status_T:

        try:

            status = self._slaves[handle].enter_initialization_mode()

            if Fmi2SlaveContext._is_valid_status(status) is False:
                self._loggers[handle].error(
                    "call to slave's enter_initialization returned an invalid status code: {status}"
                )
                return Fmi2Status.error

            return status

        except Exception:
            self._loggers[handle].error(
                msg="call to the slave's enter_initialization_mode raised an exception",
                exc_info=True,
            )
            return Fmi2Status.error

    def exit_initialization_mode(self, handle: SlaveHandle,) -> Fmi2Status_T:

        try:

            status = self._slaves[handle].enter_initialization_mode()

            if Fmi2SlaveContext._is_valid_status(status) is False:
                self._loggers[handle].error(
                    "call to slave's exit_initialization_mode returned an invalid status code: {status}"
                )
                return Fmi2Status.error

            return status

        except Exception:
            self._loggers[handle].error(
                msg="call to the slave's exit_initialization_mode raised an exception",
                exc_info=True,
            )
            return Fmi2Status.error

    def terminate(self, handle: SlaveHandle) -> Fmi2Status_T:

        try:
            status = self._slaves[handle].terminate()
            if Fmi2SlaveContext._is_valid_status(status) is False:
                self._loggers[handle].error(
                    "call to slave's terminate returned an invalid status code: {status}"
                )
                return Fmi2Status.error

            return status

        except Exception:
            self._loggers[handle].error(
                "call to slave's termiante raised an error", exc_info=True
            )
            return Fmi2Status.error

    @staticmethod
    def _is_valid_status(status: int) -> bool:
        return status in range(Fmi2Status.ok, Fmi2Status.pending + 1)
