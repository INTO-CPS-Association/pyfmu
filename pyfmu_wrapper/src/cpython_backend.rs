use crate::Fmi2CallbackLogger;
use crate::Fmi2Status;
use anyhow::Error;
use pyo3::prelude::*;
use pyo3::types::PyAny;
use pyo3::types::PyDict;
use pyo3::types::PyTuple;
use pyo3::PyCell;
use pyo3::PyObject;
use pyo3::PyResult;
use pyo3::Python;
use std::convert::TryFrom;
use std::ffi::CString;
use std::os::raw::c_int;

use crate::common::Fmi2Type;
use crate::common::PyFmuBackend;
use crate::common::SlaveHandle;

// ------------------------------------- Error Handling -------------------------------------

trait PyErrToErr<T> {
    fn map_pyerr(self, py: Python) -> Result<T, Error>;
}

/// Map PyErr to Error
impl<T> PyErrToErr<T> for PyResult<T> {
    fn map_pyerr(self, py: Python) -> Result<T, Error> {
        self.map_err(|e| {
            e.print_and_set_sys_last_vars(py);
            anyhow::anyhow!(
                "whoops some python code failed, TODO put into message instead of printing"
            )
        })
    }
}

// ------------------------------------- Logging -------------------------------------

/// Wraps C logging function pointer in a Rust struct enabling it to be passed to Python.
///
/// ## Notes
/// passing functions to Python
/// https://pyo3.rs/master/function.html
#[pyclass]
struct CallbacksWrapper {
    logger_callback: Box<Fmi2CallbackLogger>,
}

impl CallbacksWrapper {
    pub fn new(logger_callback: Fmi2CallbackLogger) -> Self {
        Self {
            logger_callback: Box::new(logger_callback),
        }
    }
}

#[pymethods]
impl CallbacksWrapper {
    #[call]
    pub fn __call__(
        &self,
        instance_name: String,
        status: c_int,
        category: String,
        message: String,
    ) {
        let instance_name = CString::new(instance_name).unwrap();
        let category = CString::new(category).unwrap();
        let message = CString::new(message).unwrap();

        match &self.logger_callback {
            callback => callback(
                std::ptr::null_mut(),
                instance_name.as_ptr(),
                status,
                category.as_ptr(),
                message.as_ptr(),
            ),
        }
    }
}

// ------------------------------------- Backend -------------------------------------
pub struct CPythonEmbedded {
    /// Python object that manages multiple slave instances in the interpreter.
    /// The object acts as a hub where methods of individual slave instances are
    /// accessed by invoking the corresponding method on the manager:
    /// manager.do_step(handle=0, ...) -> does step on slave with handle 0
    slave_manager: PyObject,
}

impl CPythonEmbedded {
    /// Instantiates the Embedded-CPython backend.
    pub fn new() -> Result<Self, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let ctx: pyo3::PyObject = py
            .import("pyfmu.fmi2.slaveContext")
            .map_pyerr(py)?
            .get("Fmi2SlaveContext")
            .map_pyerr(py)?
            .call0()
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        Ok(Self { slave_manager: ctx })
    }

    /// Utility method for calling python methods on the slave manager
    fn call_manager_method(
        &self,
        name: &str,
        args: impl IntoPy<Py<PyTuple>>,
        kwargs: Option<&PyDict>,
    ) -> Result<PyObject, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        Ok(self
            .slave_manager
            .call_method(py, name, args, kwargs)
            .map_pyerr(py)?)
    }

    /// Call method and parse result as status
    fn call_manager_method_s(
        &self,
        name: &str,
        args: impl IntoPy<Py<PyTuple>>,
        kwargs: Option<&PyDict>,
    ) -> Result<Fmi2Status, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let status: i32 = self
            .call_manager_method(name, args, kwargs)?
            .extract(py)
            .map_pyerr(py)?;

        Ok(Fmi2Status::try_from(status)?)
    }

    /// Call method and parse results as a get_xxx return
    /// If status is more severe than warning, none of the read values
    /// are returned
    fn call_manager_method_r<T>(
        &self,
        name: &str,
        args: impl IntoPy<Py<PyTuple>>,
        kwargs: Option<&PyDict>,
    ) -> Result<(Fmi2Status, Option<Vec<T>>), Error>
    where
        T: for<'a> FromPyObject<'a>,
    {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let (values, status): (Vec<T>, i32) = self
            .call_manager_method(name, args, kwargs)?
            .extract(py)
            .map_pyerr(py)?;

        let status = Fmi2Status::try_from(status)?;
        let values = {
            if status <= Fmi2Status::Fmi2Warning {
                Some(values)
            } else {
                None
            }
        };

        Ok((status, values))
    }
}

// ------------------------------------- FMI functions -------------------------------------

impl PyFmuBackend for CPythonEmbedded {
    fn instantiate(
        &self,
        instance_name: &str,
        fmu_type: Fmi2Type,
        fmu_guid: &str,
        fmu_resource_location: &str,
        logger: Fmi2CallbackLogger,
        visible: bool,
        logging_on: bool,
    ) -> Result<SlaveHandle, anyhow::Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let fmu_type: i32 = fmu_type.into();

        let kwargs = PyDict::new(py);

        kwargs
            .set_item("instance_name", instance_name)
            .map_pyerr(py)?;

        kwargs.set_item("fmu_type", fmu_type).map_pyerr(py)?;
        kwargs.set_item("guid", fmu_guid).map_pyerr(py)?;
        kwargs
            .set_item("resources_uri", fmu_resource_location)
            .map_pyerr(py)?;
        kwargs.set_item("visible", visible).map_pyerr(py)?;
        kwargs.set_item("logging_on", logging_on).map_pyerr(py)?;

        // Raw C function pointer is wrapped in an object defining the python __call__ function
        // This allows it to be passed to Python and called as if it was a function.
        let wrapper = PyCell::new(py, CallbacksWrapper::new(logger)).map_pyerr(py)?;
        kwargs.set_item("logging_callback", wrapper).map_pyerr(py)?;

        // Invoke the instantiate method of the slave manager resulting in the creation
        // of a new python slave. The specific slave can be acccessed by passing the handle
        // when invoking functions such as "do_step" or "get_xxx"
        let handle_or_none = self
            .slave_manager
            .call_method(py, "instantiate", (), Some(kwargs))
            .map_pyerr(py)?;
        if handle_or_none.is_none(py) {
            Err(anyhow::anyhow!("Unable to instantiate slave"))
        } else {
            let handle: c_int = handle_or_none.extract(py).map_pyerr(py)?;
            Ok(handle)
        }
    }

    fn free_instance(&self, handle: SlaveHandle) -> Result<(), Error> {
        self.call_manager_method("free_instance", (handle,), None)
            .map(|obj| ())
    }

    fn do_step(
        &self,
        handle: SlaveHandle,
        current_communication_time: f64,
        communication_step_size: f64,
        no_step_prior: bool,
    ) -> std::result::Result<Fmi2Status, Error> {
        self.call_manager_method_s(
            "do_step",
            (
                handle,
                current_communication_time,
                communication_step_size,
                no_step_prior,
            ),
            None,
        )
    }
    fn set_debug_logging(
        &self,
        handle: SlaveHandle,
        logging_on: bool,
        categories: Vec<&str>,
    ) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s("set_debug_logging", (handle, categories, logging_on), None)
    }
    fn setup_experiment(
        &self,
        handle: SlaveHandle,
        start_time: f64,
        tolarance: Option<f64>,
        stop_time: Option<f64>,
    ) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s(
            "setup_experiment",
            (handle, start_time, tolarance, stop_time),
            None,
        )
    }
    fn enter_initialization_mode(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s("enter_initialization_mode", (handle,), None)
    }
    fn exit_initialization_mode(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s("exit_initialization_mode", (handle,), None)
    }
    fn terminate(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s("terminate", (handle,), None)
    }
    fn reset(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s("reset", (handle,), None)
    }

    // ------------------------------------ Getters ------------------------------------

    fn get_real(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<f64>>), Error> {
        self.call_manager_method_r("get_xxx", (handle, references.to_owned()), None)
    }
    fn get_integer(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<i32>>), Error> {
        self.call_manager_method_r("get_xxx", (handle, references.to_owned()), None)
    }
    fn get_boolean(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<bool>>), Error> {
        self.call_manager_method_r("get_xxx", (handle, references.to_owned()), None)
    }
    fn get_string(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<String>>), Error> {
        self.call_manager_method_r("get_xxx", (handle, references.to_owned()), None)
    }
    // ------------------------------------ Setters ------------------------------------
    fn set_real(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[f64],
    ) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s(
            "set_xxx",
            (handle, references.to_owned(), values.to_owned()),
            None,
        )
    }
    fn set_integer(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[i32],
    ) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s(
            "set_xxx",
            (handle, references.to_owned(), values.to_owned()),
            None,
        )
    }
    fn set_boolean(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[bool],
    ) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s(
            "set_xxx",
            (handle, references.to_owned(), values.to_owned()),
            None,
        )
    }
    fn set_string(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[&str],
    ) -> Result<Fmi2Status, Error> {
        self.call_manager_method_s(
            "set_xxx",
            (handle, references.to_owned(), values.to_owned()),
            None,
        )
    }
}
