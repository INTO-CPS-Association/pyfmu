use anyhow;
use anyhow::Error;
use num_enum::IntoPrimitive;
use num_enum::TryFromPrimitive;
use pyo3::once_cell::GILOnceCell;
use pyo3::once_cell::GILOnceCell;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::types::PyTuple;
use std::boxed::Box;
use std::convert::TryFrom;
use std::ffi::CStr;
use std::ffi::CString;
use std::mem;
use std::os::raw::c_char;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_uint;
use std::os::raw::c_ulonglong;
use std::os::raw::c_void;
use std::panic::catch_unwind;
use std::ptr::null_mut;
use std::vec::Vec;

static SLAVE_MANAGER: GILOnceCell<PyObject> = GILOnceCell::new();

pub fn get_slave_manager(py: Python) -> &PyAny {
    SLAVE_MANAGER
        .get_or_init(py, || {
            let cls = || -> Result<PyObject, Error> {
                let ctx: pyo3::PyObject = py
                    .import("pyfmu.fmi2.slaveContext")
                    .map_pyerr(py)?
                    .get("Fmi2SlaveContext")
                    .map_pyerr(py)?
                    .call0()
                    .map_pyerr(py)?
                    .extract()
                    .map_pyerr(py)?;
                Ok(ctx)
            };

            cls().unwrap_or_else(|e| {
                println!("An error ocurred when instantiating slave manager: {:?}", e);
                panic!("Unable to instantiate slave manager");
            })
        })
        .as_ref(py)
}

struct CPythonBackend {}

use crate::common;

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

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetDebugLogging(
    c: *const c_int,
    logging_on: c_int,
    n_categories: usize,
    categories: *const *const c_char,
) -> c_int {
    ffi_panic_boundary! {
        let set_debug = || -> Result<c_int, Error> {
            let mut categories_vec: Vec<&str> = vec![];
            let n_categories = n_categories as isize;
            for i in 0..n_categories {
                let cat = unsafe { CStr::from_ptr(*categories.offset(i)).to_str()? };
                categories_vec.push(cat);
            }
            let h = unsafe { *c };
            let gil = Python::acquire_gil();
            let py = gil.python();

            let status: c_int = get_slave_manager(py)
                .call_method1(
                    "set_debug_logging",
                    (h, categories_vec, logging_on != 0),
                )
                .expect("Call to set_debug_logging failed")
                .extract()
                .expect("Failed extracting the status code returned form set_debug_logging");
                Fmi2Status::try_from(status)?;
                Ok(status)
        };
        match set_debug() {
            Ok(s) => s,
            Err(e) => {
                eprintln!("{}", e);
                Fmi2Status::Fmi2Error.into()
            }
        }
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetupExperiment(
    c: *const c_int,
    tolerance_defined: c_int,
    tolerance: c_double,
    start_time: c_double,
    stop_time_defined: c_int,
    stop_time: c_double,
) -> c_int {
    let setup_experiment = || -> Result<c_int, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let kwargs = PyDict::new(py);

        let h: c_int = unsafe { *c };

        kwargs.set_item("start_time", start_time).unwrap();
        kwargs.set_item("handle", h).unwrap();

        if tolerance_defined != 0 {
            kwargs.set_item("tolerance", tolerance).unwrap()
        };

        if stop_time_defined != 0 {
            kwargs.set_item("stop_time", stop_time).unwrap()
        };

        let status: c_int = get_slave_manager(py)
            .call_method("setup_experiment", (), Some(kwargs))
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        Fmi2Status::try_from(status)?;

        Ok(status)
    };

    match setup_experiment() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error.into()
        }
    }
}

/// Set the FMU to initialization mode.
///
/// ## Notes
///
/// "Informs the FMU to enter Initialization Mode. Before calling this function, all variables with
/// attribute <ScalarVariable initial = "exact" or "approx"> can be set with the “fmi2SetXXX” functions
/// (the ScalarVariable attributes are defined in the Model Description File, see section 2.2.7).
/// Setting other variables is not allowed. Furthermore, fmi2SetupExperiment must be called at least
/// once before calling fmi2EnterInitializationMode, in order that startTime is defined." **(2.1.6 p.22)**
#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2EnterInitializationMode(c: *const c_int) -> c_int {
    call_parameterless_method(c, "enter_initialization_mode")
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2ExitInitializationMode(c: *const c_int) -> c_int {
    call_parameterless_method(c, "exit_initialization_mode")
}

/// Informs an FMU that the simulation has terminated, allowing the environment to read the final output values.
///
/// **This should not be confused with freeing the instance**
///
/// ## Note
/// "Informs the FMU that the simulation run is terminated. After calling this function,
/// the final values of all variables can be inquired with the fmi2GetXXX(..) functions.
/// It is not allowed to call this function after one of the functions returned with a status flag of fmi2Error or fmi2Fatal."
/// **(2.1.6 p.22-23)**
#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Terminate(c: *const c_int) -> c_int {
    call_parameterless_method(c, "terminate")
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Reset(c: *const c_int) -> c_int {
    call_parameterless_method(c, "reset")
}

/// Call generic
fn call_parameterless_method(c: *const c_int, function: &str) -> c_int {
    let call_parameterless = || -> Result<c_int, Error> {
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        let status: c_int = get_slave_manager(py)
            .call_method1(function, (h,))
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        Fmi2Status::try_from(status)?;

        Ok(status)
    };

    match call_parameterless() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error.into()
        }
    }
}

fn get_xxx<T>(c: *const c_int, vr: *const c_uint, nvr: usize, values: *mut T) -> c_int
where
    T: for<'a> FromPyObject<'a>,
{
    let get_real = || -> Result<c_int, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize) }.to_vec();
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with "map_error"
        let (values_vec, status): (Vec<T>, c_int) = get_slave_manager(py)
            .call_method1("get_xxx", (h, references))
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        unsafe {
            std::ptr::copy(values_vec.as_ptr(), values, nvr);
        }

        Fmi2Status::try_from(status)?;

        Ok(status)
    };

    match get_real() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error.into()
        }
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetReal(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_double,
) -> c_int {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetInteger(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> c_int {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetBoolean(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> c_int {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
unsafe extern "C" fn free_string_array(ptr: *mut *mut c_char, len: c_int) {
    let len = len as usize;

    // Get back our vector.
    // Previously we shrank to fit, so capacity == length.
    let v = Vec::from_raw_parts(ptr, len, len);

    // Now drop one string at a time.
    for elem in v {
        let s = CString::from_raw(elem);
        mem::drop(s);
    }

    // Afterwards the vector will be dropped and thus freed.
}

/// Convert vector of strings to a array of c strings
/// This function does not drop automatically drop the memory
unsafe fn vector_to_string_array(v: Vec<String>) -> *mut *mut c_char {
    // Let's fill a vector with null-terminated strings

    let mut out = v
        .into_iter()
        .map(|s| CString::new(s).unwrap().into_raw())
        .collect::<Vec<_>>();

    out.shrink_to_fit();
    assert!(out.len() == out.capacity());

    let ptr = out.as_mut_ptr();
    mem::forget(out);
    ptr
}

/// Read string variables from an FMU
///
/// ## Notes
///
/// "The strings returned by fmi2GetString must be copied in the target environment
/// because the allocated memory for these strings might be deallocated by the next
/// call to any of the fmi2 interface functions or it might be an internal string buffer that is reused." (2.1.7 p.23)
#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetString(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *mut *mut *mut c_char,
) -> c_int {
    unsafe { std::ptr::write(values, null_mut()) };

    let get_string = || -> Result<c_int, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize) }.to_vec();
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with "map_error"
        let (values_vec, status): (Vec<String>, c_int) = get_slave_manager(py)
            .call_method1("get_xxx", (h, references))
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        unsafe { std::ptr::write(values, vector_to_string_array(values_vec)) };

        Fmi2Status::try_from(status)?;

        Ok(status)
    };

    match get_string() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error.into()
        }
    }
}

fn set_xxx<T>(c: *const c_int, vr: *const c_uint, nvr: usize, values: *const T) -> c_int
where
    T: for<'a> FromPyObject<'a> + Clone + std::fmt::Debug,
    (c_int, Vec<c_uint>, Vec<T>): IntoPy<Py<PyTuple>>,
{
    let set_xxx = || -> Result<c_int, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr).to_vec() };
        let values = unsafe { std::slice::from_raw_parts(values, nvr).to_vec() };
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with ?
        let status: c_int = get_slave_manager(py)
            .call_method1("set_xxx", (h, references, values))
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        Fmi2Status::try_from(status)?;

        Ok(status)
    };

    match set_xxx() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error.into()
        }
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetReal(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_double,
) -> c_int {
    set_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetInteger(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_int,
) -> c_int {
    set_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetBoolean(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_int,
) -> c_int {
    set_xxx(c, vr, nvr, values as *mut bool)
}

/// Set string variables of an FMU
///
/// ### Notes
///
/// "All strings passed as arguments to fmi2SetString must be copied inside this function,
/// because there is no guarantee of the lifetime of strings when this function returns." (2.1.7 p.24)
#[no_mangle]
#[allow(non_snake_case)]
#[allow(unused_variables)]
pub extern "C" fn fmi2SetString(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const *const c_char,
) -> c_int {
    let set_xxx = || -> Result<c_int, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr).to_vec() };
        let h = unsafe { *c };

        let mut vec: Vec<String> = Vec::with_capacity(nvr);

        for i in 0..nvr {
            unsafe { vec.insert(i, cstr_to_string(*values.offset(i as isize))) };
        }

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with ?
        let status: c_int = get_slave_manager(py)
            .call_method1("set_xxx", (h, references, vec))
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        Fmi2Status::try_from(status)?;

        Ok(status)
    };

    match set_xxx() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error.into()
        }
    }
}

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

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2FreeFMUstate(c: *const c_int) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Instantiate(
    instance_name: *const c_char,
    fmu_type: c_int,
    fmu_guid: *const c_char,
    fmu_resource_location: *const c_char,
    functions: Fmi2CallbackFunctions,
    visible: c_int,
    logging_on: c_int,
) -> *mut c_int {
    let get_instance = || -> Result<SlaveHandle, Error> {
        let logger = functions.logger.ok_or_else(|| {
            anyhow::anyhow!(
                "Logging callback function appears to be null, this is not permitted according to FMI2 specification."
            )
        })?;

        let gil = Python::acquire_gil();
        let py = gil.python();
        let kwargs = PyDict::new(py);

        kwargs
            .set_item("instance_name", cstr_to_string(instance_name))
            .map_pyerr(py)?;

        kwargs.set_item("fmu_type", fmu_type).map_pyerr(py)?;
        kwargs
            .set_item("guid", cstr_to_string(fmu_guid))
            .map_pyerr(py)?;
        kwargs
            .set_item("resources_uri", cstr_to_string(fmu_resource_location))
            .map_pyerr(py)?;
        kwargs.set_item("visible", visible != 0).map_pyerr(py)?;
        kwargs
            .set_item("logging_on", logging_on != 0)
            .map_pyerr(py)?;
        let wrapper = PyCell::new(py, CallbacksWrapper::new(logger)).map_pyerr(py)?;
        kwargs.set_item("logging_callback", wrapper).map_pyerr(py)?;

        let handle_or_none: &PyAny = get_slave_manager(py)
            .call_method("instantiate", (), Some(kwargs))
            .map_pyerr(py)?;

        if handle_or_none.is_none() {
            Err(anyhow::anyhow!("Unable to instantiate slave"))
        } else {
            let handle: c_int = handle_or_none.extract().map_pyerr(py)?;
            Ok(handle)
        }
    };

    match catch_unwind(|| get_instance()) {
        Err(_) => {
            println!("An fatal error has ocurred leading to an panic in the Rust component of the wrapper.");
            null_mut()
        }

        Ok(res) => match res {
            Ok(h) => Box::into_raw(Box::new(h)),
            Err(e) => {
                println!(
                    "An error has ocurred during instantiation of the FMU: {}",
                    e
                );
                null_mut()
            }
        },
    }
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetFMUstate(c: *const c_int, state: *const c_void) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetDirectionalDerivative(
    c: *const c_int,
    unknown_refs: *const c_int,
    nvr_unknown: usize,
    known_refs: *const c_int,
    nvr_known: usize,
    values_known: *const c_double,
    values_unkown: *mut c_double,
) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetFMUstate(c: *const c_int, state: *mut *mut c_void) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SerializeFMUstate(
    c: *const c_int,
    state: *mut c_void,
    data: *const c_char,
    size: usize,
) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2DeSerializeFMUstate(
    c: *const c_int,
    serialized_state: *const c_char,
    size: usize,
    state: *mut c_void,
) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SerializedFMUstateSize(c: *const c_int, state: *mut *mut c_void) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetRealInputDerivatives(c: *const c_int, vr: *const c_uint) -> c_int {
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealOutputDerivatives(c: *const c_int) -> c_int {
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2CancelStep(c: *const c_int) -> c_int {
    call_parameterless_method(c, "cancel_step")
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_double,
) -> c_int {
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStatus(
    c: *const c_int,
    status_kind: c_int,
    Fmi2Status: *mut c_int,
) -> c_int {
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetIntegerStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_int,
) -> c_int {
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetBooleanStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_int,
) -> c_int {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStringStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_char,
) -> c_int {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2DoStep(
    c: *const c_int,
    current_communication_point: c_double,
    communication_step_size: c_double,
    no_set_fmu_state_prior_to_current_point: c_int,
) -> c_int {
    let do_step = || -> Result<c_int, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();
        let status: c_int = get_slave_manager(py)
            .call_method1(
                "do_step",
                (
                    unsafe { *c },
                    current_communication_point,
                    communication_step_size,
                    no_set_fmu_state_prior_to_current_point,
                ),
            )
            .map_pyerr(py)?
            .extract()
            .map_pyerr(py)?;

        let status: c_int = Fmi2Status::try_from(status).unwrap().into();

        Ok(status)
    };

    match do_step() {
        Ok(s) => s,
        Err(e) => {
            println!("Do step failed due to error: {}", e);
            Fmi2Status::Fmi2Error.into()
        }
    }
}

#[no_mangle]
pub extern "C" fn fmi2FreeInstance(c: *mut c_int) {
    let free_instance = || -> Result<(), Error> {
        if c.is_null() {
            Ok(())
        } else {
            let gil = Python::acquire_gil();
            let py = gil.python();

            get_slave_manager(py)
                .call_method1("free_instance", (unsafe { *c },))
                .map_pyerr(py)?;

            unsafe { Box::from_raw(c) };

            Ok(())
        }
    };

    match free_instance() {
        Ok(_) => (),
        Err(e) => eprintln!("An error ocurred when freeing instance: {}", e), // TODO
    }
}
