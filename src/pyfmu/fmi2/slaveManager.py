from typing import Dict, Tuple, Union, List, Callable
import importlib

from pathlib import Path
import json
import sys

from pyfmu.fmi2.types import Fmi2Status_T, Fmi2Status
from pyfmu.fmi2.logging import Fmi2CallbackLogger
from pyfmu.utils import file_uri_to_path
from pyfmu.fmi2.types import IsFmi2Slave


SlaveHandle = int
Fmi2Value = Union[float, int, bool, str]
Fmi2LoggingCallback = Callable[[Fmi2Status_T, str, str, str], None]


class Fmi2SlaveManager:
    def __init__(self):

        self._slaves: Dict[SlaveHandle, IsFmi2Slave] = {}
        self._slave_to_ids_to_attr: Dict[SlaveHandle, Dict[int, str]] = {}
        self._loggers: Dict[SlaveHandle, Fmi2CallbackLogger] = {}

    def instantiate(
        self,
        instance_name: str,
        fmu_type: str,
        guid: str,
        resources_uri: str,
        logging_callback: Fmi2LoggingCallback,
        visible: bool,
        logging_on: bool,
    ) -> SlaveHandle:
        """Create a new instance of the specified FMU and return a handle to the caller.

        The process of doing this is:
            1. The slave configuration is located in the resources directory.
            2. The name of the slave class and the script defining it is read from the configuration.
            3. The object is instantiated and stored in the manager.
            4. A handle to the instance is returned to the FMI interface.

        Args:
            instance_name: [description]
            type: [description]
            guid: [description]
            resources_uri: [description]
            logging_callback ([type]): [description]
            visible (bool): [description]
            logging_on (bool): [description]

        Returns:
            SlaveHandle: [description]
        """
        if fmu_type != "fmi2CoSimulation":
            raise RuntimeError("Only co-simulation is supported.")

        url_path = file_uri_to_path(resources_uri)

        if not str(url_path) in sys.path:
            sys.path.append(str(url_path))

        # read configuration
        config = None
        with open(url_path / "slave_configuration.json", "r") as f:
            config = json.load(f)

        slave_module = Path(config["main_script"]).stem
        slave_class = config["main_class"]

        # instantiate object
        instance = getattr(importlib.import_module(slave_module), slave_class)
        handle = self._get_free_handle()

        logger = Fmi2CallbackLogger(instance_name, logging_callback)

        self._slaves[handle] = instance
        self._loggers[handle] = logger

        return handle

    def do_step(
        self,
        handle: SlaveHandle,
        current_time: float,
        step_size: float,
        no_set_state_prior: bool,
    ) -> Fmi2Status_T:
        assert handle in self._slaves
        assert current_time >= 0

        return self._slaves[handle].do_step(current_time, step_size, no_set_state_prior)

    def set_xxx(
        self, handle: SlaveHandle, references: List[int], values: List[Fmi2Value]
    ) -> Fmi2Status_T:

        attributes = [self._slave_to_ids_to_attr[handle][i] for i in references]

        for a, v in zip(attributes, values):
            setattr(self._slaves[handle], a, v)

        return Fmi2Status.ok

    def get_xxx(
        self, handle: SlaveHandle, references: List[int]
    ) -> Tuple[List[Fmi2Value], Fmi2Status_T]:

        s = self._slaves[handle]
        attributes = [self._slave_to_ids_to_attr[handle][i] for i in references]
        values = [getattr(s, a) for a in attributes]

        return (values, Fmi2Status.ok)

    def _get_free_handle(self) -> SlaveHandle:
        i = 0
        while i in self._slaves:
            i += 1
        return i
