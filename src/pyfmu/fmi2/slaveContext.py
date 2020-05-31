from typing import Dict, Tuple, Union, List, Callable, Optional
import importlib
import logging
from pathlib import Path
import json
import sys

from pyfmu.fmi2.types import Fmi2Status_T, Fmi2Status
from pyfmu.fmi2.logging import Fmi2CallbackLogger, Fmi2NullLogger
from pyfmu.utils import file_uri_to_path
from pyfmu.fmi2.types import Fmi2SlaveLike, Fmi2Value_T


SlaveHandle = int
Fmi2Value = Union[float, int, bool, str]
Fmi2LoggingCallback = Callable[[Fmi2Status_T, str, str, str], None]


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
        self._loggers: Dict[SlaveHandle, Fmi2CallbackLogger] = {}

    def instantiate(
        self,
        instance_name: str,
        fmu_type: str,
        guid: str,
        resources_uri: str,
        logging_callback: Optional[Fmi2LoggingCallback],
        visible: bool,
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

        try:
            pass
        except Exception as e:

            return None

        if logging_callback:
            logger = Fmi2CallbackLogger(logging_callback)
        else:
            logger = Fmi2NullLogger()

        if fmu_type != "fmi2CoSimulation":

            raise NotImplementedError("Only co-simulation is supported.")

        if logging_callback:
            logger = Fmi2CallbackLogger(logging_callback)
        else:
            logger = Fmi2NullLogger()

        url_path = file_uri_to_path(resources_uri)

        if not str(url_path) in sys.path:
            sys.path.append(str(url_path))

        # read configuration
        config = None
        with open(url_path / "slave_configuration.json", "r") as f:
            config = json.load(f)

        slave_module = Path(config["slave_script"]).stem
        slave_class = config["slave_class"]

        # instantiate object
        instance = getattr(importlib.import_module(slave_module), slave_class)()

        def get_free_handle() -> SlaveHandle:
            i = 0
            while i in self._slaves:
                i += 1
            return i

        handle = get_free_handle()

        logger = Fmi2CallbackLogger(instance_name, logging_callback)

        self._slaves[handle] = instance
        self._loggers[handle] = logger

        return handle

    def free_instance(self, handle: SlaveHandle) -> Fmi2Value_T:
        try:
            del self._slaves[handle]
        except Exception as e:
            self._loggers[handle].log(str(e))
            raise e

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
        assert handle in self._slaves
        assert current_time >= 0

        return self._slaves[handle].do_step(current_time, step_size, no_set_state_prior)

    def setup_experiment(
        self,
        handle: SlaveHandle,
        start_time: float,
        tolerance: float = None,
        stop_time: float = None,
    ) -> Fmi2Status_T:

        try:
            return self._slaves[handle].setup_experiment(
                start_time=start_time, tolerance=tolerance, stop_time=stop_time
            )
        except Exception as e:
            raise NotImplementedError()
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

        attributes = [self._slave_to_ids_to_attr[handle][i] for i in references]

        try:
            for a, v in zip(attributes, values):
                setattr(self._slaves[handle], a, v)

            return Fmi2Status.ok

        except Exception as e:
            raise NotImplementedError()
            return Fmi2Status.error

    def get_xxx(
        self, handle: SlaveHandle, references: List[int]
    ) -> Tuple[List[Fmi2Value], Fmi2Status_T]:
        """Read variables of the slave specified by the handle.
        """
        attributes = [self._slave_to_ids_to_attr[handle][i] for i in references]

        try:
            values = [getattr(self._slaves[handle], a) for a in attributes]
            return (values, Fmi2Status.ok)
        except Exception as e:
            raise NotImplementedError()
            return Fmi2Status.error
