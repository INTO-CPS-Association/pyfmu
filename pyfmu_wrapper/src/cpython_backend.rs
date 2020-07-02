use anyhow::Error;
use pyo3::once_cell::GILOnceCell;
use pyo3::PyObject;
use pyo3::PyResult;
use pyo3::Python;

use crate::common::FMI2Logger;
use crate::common::Fmi2Type;
use crate::common::PyFmuBackend;

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

// ------------------------------------- Backend -------------------------------------
pub struct CPythonEmbedded {
    slave_manager: PyObject,
}

impl CPythonEmbedded {
    // Instantiates the Embedded-CPython backend.

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
}

impl PyFmuBackend for CPythonEmbedded {
    fn instantiate(
        &self,
        instance_name: &str,
        fmu_type: Fmi2Type,
        fmu_guid: &str,
        fmu_resource_location: &str,
        logger: std::boxed::Box<(dyn FMI2Logger + 'static)>,
        visible: bool,
        logging_on: bool,
    ) -> Result<i32, anyhow::Error> {
        Ok(0)
    }
}
