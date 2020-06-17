use anyhow;
use anyhow::Error;
use num_enum::IntoPrimitive;
use num_enum::TryFromPrimitive;
use pyo3::once_cell::OnceCell;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::types::PyTuple;
use std::boxed::Box;
use std::collections::HashMap;
use std::convert::TryFrom;
use std::ffi::CStr;
use std::ffi::CString;
use std::mem;
use std::mem::MaybeUninit;
use std::ops::Deref;
use std::os::raw::c_char;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_uint;
use std::os::raw::c_ulonglong;
use std::os::raw::c_void;
use std::panic::catch_unwind;
use std::ptr::null_mut;
use std::vec::Vec;

#[macro_use]
extern crate lazy_static;
extern crate num_enum;

pub type SlaveHandle = i32;

/// Capture Rust panics and return Fmi2Error instead
macro_rules! ffi_panic_boundary {($($tt:tt)*) => (
    match catch_unwind(|| {$($tt)*}) {
        | Ok(ret) => ret,
        | Err(_) => {
            eprintln!("Rust panicked; return Fmi2Error");
            Fmi2Status::Fmi2Error.into()
        },
    }
)}

pub type Fmi2CallbackLogger = extern "C" fn(
    component_environment: *mut c_void,
    instance_name: *const c_char,
    status: c_int,
    category: *const c_char,
    message: *const c_char,
    // ... variadic functions support in rust seems to be unstable
);
pub type Fmi2CallbackAllocateMemory = extern "C" fn(nobj: c_ulonglong, size: c_ulonglong);
pub type Fmi2CallbackFreeMemory = extern "C" fn(obj: *const c_void);
pub type Fmi2StepFinished = extern "C" fn(component_environment: *mut c_void, status: Fmi2Status);

#[repr(C)]
#[derive(Copy, Clone)]
pub struct Fmi2CallbackFunctions {
    logger: Option<Fmi2CallbackLogger>,
    allocate_memory: Option<Fmi2CallbackAllocateMemory>,
    free_memory: Option<Fmi2CallbackFreeMemory>,
    step_finished: Option<Fmi2StepFinished>,
    component_environment: Option<*mut c_void>,
}

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

#[derive(Debug, TryFromPrimitive, IntoPrimitive, PartialEq, Eq)]
#[repr(i32)]
pub enum Fmi2Status {
    Fmi2OK,
    Fmi2Warning,
    Fmi2Discard,
    Fmi2Error,
    Fmi2Fatal,
    Fmi2Pending,
}

#[derive(Debug, TryFromPrimitive, PartialEq, Eq)]
#[repr(i32)]
pub enum Fmi2StatusKind {
    Fmi2DoStepStatus = 0,
    Fmi2PendingStatus = 1,
    Fmi2LastSuccessfulTime = 2,
    Fmi2Terminated = 3,
}

#[derive(Debug, TryFromPrimitive, PartialEq, Eq)]
#[repr(i32)]
pub enum Fmi2Type {
    Fmi2ModelExchange = 0,
    Fmi2CoSimulation = 1,
}

static SLAVE_MANAGER: OnceCell<PyObject> = OnceCell::new();

pub fn get_slave_manager(py: Python) -> &PyAny {
    SLAVE_MANAGER
        .get_or_init(py, || {
            let cls = || -> PyResult<PyObject> {
                let ctx: pyo3::PyObject = py
                    .import("pyfmu.fmi2.slaveContext")
                    .expect("Unable to import module declaring slave manager. Ensure that PyFMU is installed inside your current envrioment.")
                    .get("Fmi2SlaveContext")?
                    .call0()?
                    .extract()?;
                Ok(ctx)
            };

            cls().unwrap_or_else(|e| {
                e.print_and_set_sys_last_vars(py);
                panic!("Unable to instantiate slave manager");
            })
        })
        .as_ref(py)
}

fn cstr_to_string(cstr: *const c_char) -> String {
    unsafe { CStr::from_ptr(cstr).to_string_lossy().into_owned() }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetTypesPlatform() -> *const c_char {
    static TYPES_PLATFORM: &str = "default";
    TYPES_PLATFORM.as_ptr() as *const i8
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetVersion() -> *const c_char {
    static FMI_VERISON: &str = "2.0";
    FMI_VERISON.as_ptr() as *const i8
}

/// Configures the logging behavior of an FMU
///
/// ## Notes
///
/// The logging functionality of a FMU is somewhat ill defined:
///
/// "The function controls debug logging that is output via the logger function callback. If loggingOn = fmi2True,
/// debug logging is enabled, otherwise it is switched off. If loggingOn = fmi2True and nCategories = 0, then all
/// debug messages shall be output. If loggingOn=fmi2True and nCategories > 0, then only debug messages according to
/// the categories argument shall be output. Vector categories has nCategories elements. The allowed values of categories
/// are defined by the modeling environment that generated the FMU. Depending on the generating modeling environment, none, some or
/// all allowed values for categories for this FMU are defined in the modelDescription.xml file via element “fmiModelDescription.LogCategories, see section 2.2.4."
/// **(2.1.5 p.21)**
///
/// LogCategories defines an unordered set of category strings that can be utilized to define the log output via function “logger”, see section 2.1.5.
/// A tool is free to use any normalizedString for a category value. The “name” attribute of “Category” must be unique with respect to all other elements of the LogCategories list.
/// There are the following standardized names for “Category” and these names should be used if a tool supports the corresponding log category.
/// If a tool supports one of these log categories and wants to expose it, then an element Category with this name should be added to LogCategories
/// [To be clear, only the Category names listed under LogCategories in the xml-file are known to the environment in which the FMU is called.]" **(2.2.4 p.43)**
///
/// The following table of standard categories are provided:
/// * logEvents: Log all events (during initialization and simulation).
/// * logSingularLinearSystems: Log the solution of linear systems of equations if the solution is singular (and the tool picked one solution of the infinitely many solutions).
/// * logNonlinearSystems: Log the solution of nonlinear systems of equations.
/// * logDynamicStateSelection: Log the dynamic selection of states.
/// * logStatusWarning: Log messages when returning fmi2Warning status from any function.
/// * logStatusDiscard: Log messages when returning fmi2Discard status from any function.
/// * logStatusError: Log messages when returning fmi2Error status from any function.
/// * logStatusFatal: Log messages when returning fmi2Fatal status from any function.
/// * logStatusPending: Log messages when returning fmi2Pending status from any function.
/// * logStatusAll: Log all messages.
/// List adapted from table **(2.2.4 p.43)**
#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetDebugLogging(
    c: *const i32,
    logging_on: c_int,
    n_categories: usize,
    categories: *const *const c_char,
) -> i32 {
    ffi_panic_boundary! {
        let set_debug = || -> Result<i32, Error> {
            let mut categories_vec: Vec<&str> = vec![];
            let n_categories = n_categories as isize;
            for i in 0..n_categories {
                let cat = unsafe { CStr::from_ptr(*categories.offset(i)).to_str()? };
                categories_vec.push(cat);
            }
            let h = unsafe { *c };
            let gil = Python::acquire_gil();
            let py = gil.python();

            let status: i32 = get_slave_manager(py)
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

/// Informs the FMU of the start time and optionally the tolerated error and stop time.
///
/// ## Specification:
/// 2.1.6 p.22)
/// The significance of the tolerance value depends on whether the FMU is simulated as model exchange or co-simulation.
///
/// ### Model Exchange
/// If “toleranceDefined = fmi2True”, then the model is called with a numerical integration scheme where the step size is controlled by
/// using “tolerance” for error estimation (usually as relative tolerance). In such a case, all numerical algorithms used inside the model
/// (for example, to solve non-linear algebraic equations) should also operate with an error estimation of an appropriate smaller relative tolerance.
///
/// ### Co-simulation
/// If “toleranceDefined = fmi2True”, then the communication interval of the slave is controlled by error estimation. In case the slave utilizes a
/// numerical integrator with variable step size and error estimation, it is suggested to use “tolerance” for the error estimation of the internal
/// integrator (usually as relative tolerance). **An FMU for Co-Simulation might ignore this argument**.
#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetupExperiment(
    c: *const i32,
    tolerance_defined: c_int,
    tolerance: c_double,
    start_time: c_double,
    stop_time_defined: c_int,
    stop_time: c_double,
) -> i32 {
    let setup_experiment = || -> Result<i32, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let kwargs = PyDict::new(py);

        let h: i32 = unsafe { *c };

        kwargs.set_item("start_time", start_time).unwrap();
        kwargs.set_item("handle", h).unwrap();

        if tolerance_defined != 0 {
            kwargs.set_item("tolerance", tolerance).unwrap()
        };

        if stop_time_defined != 0 {
            kwargs.set_item("stop_time", stop_time).unwrap()
        };

        let status: i32 = get_slave_manager(py)
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
pub extern "C" fn fmi2EnterInitializationMode(c: *const i32) -> i32 {
    call_parameterless_method(c, "enter_initialization_mode")
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2ExitInitializationMode(c: *const i32) -> i32 {
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
pub extern "C" fn fmi2Terminate(c: *const i32) -> i32 {
    call_parameterless_method(c, "terminate")
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Reset(c: *const i32) -> i32 {
    call_parameterless_method(c, "reset")
}

/// Call generic
fn call_parameterless_method(c: *const i32, function: &str) -> i32 {
    let call_parameterless = || -> Result<i32, Error> {
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        let status: i32 = get_slave_manager(py)
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

fn get_xxx<T>(c: *const i32, vr: *const c_uint, nvr: usize, values: *mut T) -> i32
where
    T: for<'a> FromPyObject<'a>,
{
    let get_real = || -> Result<i32, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize) }.to_vec();
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with "map_error"
        let (values_vec, status): (Vec<T>, i32) = get_slave_manager(py)
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
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_double,
) -> i32 {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetInteger(
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> i32 {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetBoolean(
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> i32 {
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

    println!("I am leaking memory fix me :(");

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
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *mut *mut *mut c_char,
) -> c_int {
    unsafe { std::ptr::write(values, null_mut()) };

    let get_string = || -> Result<i32, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize) }.to_vec();
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with "map_error"
        let (values_vec, status): (Vec<String>, i32) = get_slave_manager(py)
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

fn set_xxx<T>(c: *const i32, vr: *const c_uint, nvr: usize, values: *const T) -> i32
where
    T: for<'a> FromPyObject<'a> + Clone + std::fmt::Debug,
    (i32, Vec<c_uint>, Vec<T>): IntoPy<Py<PyTuple>>,
{
    let set_xxx = || -> Result<i32, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr).to_vec() };
        let values = unsafe { std::slice::from_raw_parts(values, nvr).to_vec() };
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with ?
        let status: i32 = get_slave_manager(py)
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
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_double,
) -> i32 {
    set_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetInteger(
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_int,
) -> c_int {
    set_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetBoolean(
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *const i32,
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
    c: *const i32,
    vr: *const c_uint,
    nvr: usize,
    values: *const *const c_char,
) -> c_int {
    let set_xxx = || -> Result<i32, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr).to_vec() };
        let h = unsafe { *c };

        let mut vec: Vec<String> = Vec::with_capacity(nvr);

        for i in 0..nvr {
            unsafe { vec.insert(i, cstr_to_string(*values.offset(i as isize))) };
        }

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with ?
        let status: i32 = get_slave_manager(py)
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
pub extern "C" fn fmi2FreeFMUstate(c: *const i32) -> c_int {
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
) -> *mut i32 {
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
            let handle: i32 = handle_or_none.extract().map_pyerr(py)?;
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
pub extern "C" fn fmi2SetFMUstate(c: *const i32, state: *const c_void) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetDirectionalDerivative(
    c: *const i32,
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
pub extern "C" fn fmi2GetFMUstate(c: *const i32, state: *mut *mut c_void) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SerializeFMUstate(
    c: *const i32,
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
    c: *const i32,
    serialized_state: *const c_char,
    size: usize,
    state: *mut c_void,
) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SerializedFMUstateSize(c: *const i32, state: *mut *mut c_void) -> c_int {
    println!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetRealInputDerivatives(c: *const i32, vr: *const c_uint) -> i32 {
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealOutputDerivatives(c: *const i32) -> i32 {
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2CancelStep(c: *const i32) -> i32 {
    call_parameterless_method(c, "cancel_step")
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealStatus(
    c: *const i32,
    status_kind: c_int,
    value: *mut c_double,
) -> i32 {
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStatus(c: *const i32, status_kind: c_int, Fmi2Status: *mut c_int) -> i32 {
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetIntegerStatus(
    c: *const i32,
    status_kind: c_int,
    value: *mut c_int,
) -> i32 {
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetBooleanStatus(
    c: *const i32,
    status_kind: c_int,
    value: *mut c_int,
) -> i32 {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStringStatus(
    c: *const i32,
    status_kind: c_int,
    value: *mut c_char,
) -> i32 {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2DoStep(
    c: *const i32,
    current_communication_point: c_double,
    communication_step_size: c_double,
    no_set_fmu_state_prior_to_current_point: i32,
) -> c_int {
    let do_step = || -> Result<c_int, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();
        let status: i32 = get_slave_manager(py)
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

        let status: i32 = Fmi2Status::try_from(status).unwrap().into();

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

/// Disposes the specified FMU instance and free all allocated memory.
///
/// **This should not be confused with terminate**
///
/// ## Notes
///
/// "Disposes the given instance, unloads the loaded model, and frees all the allocated memory
/// and other resources that have been allocated by the functions of the FMU interface.
/// If a null pointer is provided for “c”, the function call is ignored (does not have an effect)."
/// **(2.1.5 p.21)**
#[no_mangle]
pub extern "C" fn fmi2FreeInstance(c: *mut i32) {
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

#[allow(unused_variables, dead_code)] // linter does not detect tests use of this code
extern "C" fn logger(
    component_environment: *mut c_void,
    instance_name: *const c_char,
    status: c_int,
    category: *const c_char,
    message: *const c_char,
) {
    let instance_name = cstr_to_string(instance_name);
    let category = cstr_to_string(category);
    let message = cstr_to_string(message);
    println!(
        "Callback:{}:{}:{}:{}",
        instance_name, category, status, message
    )
}

#[cfg(test)]
mod tests {
    // Note this useful idiom: importing names from outer (for mod tests) scope.
    use super::*;
    use std::ptr::null_mut;
    #[test]
    fn test_adder() {
        // see documentation of Cstring.as_ptr
        let instance_name = CString::new("a").unwrap();
        let instance_name_ptr = instance_name.as_ptr();

        let fmu_type = 1;
        let guid = CString::new("1234").unwrap();
        let guid_ptr = guid.as_ptr();

        let fmu_resources_path =
            CString::new("file:///C:/Users/clega/Desktop/pyfmu/examples/exported/Adder/resources")
                .unwrap();
        let fmu_resources_path_ptr = fmu_resources_path.as_ptr();

        let functions = Fmi2CallbackFunctions {
            logger: Some(logger),
            allocate_memory: None,
            free_memory: None,
            step_finished: None,
            component_environment: None,
        };
        let visible: i32 = 0;
        let logging_on: i32 = 0;

        println!("{:?}", instance_name);

        let h1 = fmi2Instantiate(
            instance_name_ptr,
            fmu_type,
            guid_ptr,
            fmu_resources_path_ptr,
            functions,
            visible,
            logging_on,
        );

        assert_ne!(h1, null_mut());

        let status = fmi2DoStep(h1, 0.0, 10.0, 0);

        let references = &[0, 1];
        let mut values: [f64; 2] = [10.0, 20.0];

        let references_ptr = references.as_ptr();
        let values_ptr = values.as_mut_ptr();

        let log_all = CString::new("logAll").unwrap();
        let categories = [log_all.as_ptr()];
        let categories_ptr = categories.as_ptr();

        assert_eq!(
            fmi2SetDebugLogging(h1, 0, 1, categories_ptr),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(
            fmi2SetupExperiment(h1, 0, 0.0, 0.0, 0, 0.0),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2EnterInitializationMode(h1), Fmi2Status::Fmi2OK.into());
        assert_eq!(fmi2ExitInitializationMode(h1), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2SetReal(h1, references_ptr, 2, values_ptr),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2DoStep(h1, 0.0, 1.0, 0), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2GetReal(h1, references_ptr, 2, values_ptr),
            Fmi2Status::Fmi2OK.into()
        );
        assert_eq!(values, [10.0, 20.0]);

        let references = &[2];
        let references_ptr = references.as_ptr();

        assert_eq!(
            fmi2GetReal(h1, references_ptr, 1, values_ptr),
            Fmi2Status::Fmi2OK as i32
        );

        assert_eq!(values[0], 30.0);

        fmi2FreeInstance(h1);

        assert_eq!(status, Fmi2Status::Fmi2OK.into())
    }
    #[test]
    fn test_types() {
        // see documentation of Cstring.as_ptr
        let instance_name = CString::new("a").unwrap();
        let instance_name_ptr = instance_name.as_ptr();

        let fmu_type = 1;
        let guid = CString::new("1234").unwrap();
        let guid_ptr = guid.as_ptr();

        let fmu_resources_path = CString::new(
            "file:///C:/Users/clega/Desktop/pyfmu/examples/exported/FmiTypes/resources",
        )
        .unwrap();
        let fmu_resources_path_ptr = fmu_resources_path.as_ptr();

        let functions = Fmi2CallbackFunctions {
            logger: Some(logger),
            allocate_memory: None,
            free_memory: None,
            step_finished: None,
            component_environment: None,
        };
        let visible: c_int = 0;
        let logging_on: c_int = 0;

        println!("{:?}", instance_name);

        let h1 = fmi2Instantiate(
            instance_name_ptr,
            fmu_type,
            guid_ptr,
            fmu_resources_path_ptr,
            functions,
            visible,
            logging_on,
        );

        assert_ne!(h1, null_mut());

        let ref_real_in = &[0, 1];
        let ref_real_out = &[2, 3];
        let ref_integer_in = &[4, 5];
        let ref_integer_out = &[6, 7];
        let ref_boolean_in = &[8, 9];
        let ref_boolean_out = &[10, 11];
        let ref_string_in = &[12, 13];
        let ref_string_out = &[14, 15];

        let val_real_in: [c_double; 2] = [1.0, 2.0];
        let mut val_real_out: [c_double; 2] = [0.0, 0.0];

        let val_integer_in: [c_int; 2] = [1, 2];
        let mut val_integer_out: [c_int; 2] = [0, 0];

        let val_boolean_in: [c_int; 2] = [1, 0];
        let mut val_boolean_out: [c_int; 2] = [0, 1];

        let val_str_in_str_a = CString::new("a").unwrap();
        let val_str_in_str_b = CString::new("b").unwrap();

        let val_str_out_cstr: *mut *mut *mut c_char = MaybeUninit::uninit().as_mut_ptr();

        let val_string_in: [*const c_char; 2] =
            [val_str_in_str_a.as_ptr(), val_str_in_str_b.as_ptr()];

        assert_eq!(
            fmi2SetupExperiment(h1, 0, 0.0, 0.0, 0, 0.0),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2EnterInitializationMode(h1), Fmi2Status::Fmi2OK.into());
        assert_eq!(fmi2ExitInitializationMode(h1), Fmi2Status::Fmi2OK.into());

        // Real

        assert_eq!(
            fmi2SetReal(
                h1,
                ref_real_in.as_ptr(),
                val_real_in.len(),
                val_real_in.as_ptr()
            ),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2DoStep(h1, 0.0, 1.0, 0), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2GetReal(
                h1,
                ref_real_out.as_ptr(),
                val_real_out.len(),
                val_real_out.as_mut_ptr()
            ),
            Fmi2Status::Fmi2OK.into()
        );
        assert_eq!(val_real_out, val_real_in);

        // Integer

        assert_eq!(
            fmi2SetInteger(
                h1,
                ref_integer_in.as_ptr(),
                val_integer_in.len(),
                val_integer_in.as_ptr()
            ),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2DoStep(h1, 1.0, 2.0, 0), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2GetInteger(
                h1,
                ref_integer_out.as_ptr(),
                val_integer_out.len(),
                val_integer_out.as_mut_ptr()
            ),
            Fmi2Status::Fmi2OK.into()
        );
        assert_eq!(val_integer_out, val_integer_in);

        // boolean

        assert_eq!(
            fmi2SetBoolean(
                h1,
                ref_boolean_in.as_ptr(),
                val_boolean_in.len(),
                val_boolean_in.as_ptr()
            ),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2DoStep(h1, 2.0, 3.0, 0), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2GetBoolean(
                h1,
                ref_boolean_out.as_ptr(),
                val_boolean_out.len(),
                val_boolean_out.as_mut_ptr()
            ),
            Fmi2Status::Fmi2OK.into()
        );
        assert_eq!(val_integer_out, val_integer_out);

        // string

        assert_eq!(
            fmi2SetString(
                h1,
                ref_string_in.as_ptr(),
                val_string_in.len(),
                val_string_in.as_ptr()
            ),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2DoStep(h1, 2.0, 3.0, 0), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2GetString(
                h1,
                ref_string_out.as_ptr(),
                val_string_in.len(),
                val_str_out_cstr
            ),
            Fmi2Status::Fmi2OK.into()
        );
        panic!("TODO check string return is correct");
        assert_eq!(val_integer_out, val_integer_out);

        assert_eq!(fmi2Terminate(h1), Fmi2Status::Fmi2OK.into());
        assert_eq!(fmi2Reset(h1), Fmi2Status::Fmi2OK.into());
        fmi2FreeInstance(h1);
    }

    #[test]
    fn test_bicycle_kinematic() {
        // see documentation of Cstring.as_ptr
        let instance_name = CString::new("a").unwrap();
        let instance_name_ptr = instance_name.as_ptr();

        let fmu_type = 1;
        let guid = CString::new("1234").unwrap();
        let guid_ptr = guid.as_ptr();

        let fmu_resources_path = CString::new(
            "file:///C:/Users/clega/Desktop/pyfmu/examples/exported/BicycleKinematic/resources",
        )
        .unwrap();
        let fmu_resources_path_ptr = fmu_resources_path.as_ptr();

        let functions = Fmi2CallbackFunctions {
            logger: Some(logger),
            allocate_memory: None,
            free_memory: None,
            step_finished: None,
            component_environment: None,
        };
        let visible: i32 = 0;
        let logging_on: i32 = 0;

        println!("{:?}", instance_name);

        let h1 = fmi2Instantiate(
            instance_name_ptr,
            fmu_type,
            guid_ptr,
            fmu_resources_path_ptr,
            functions,
            visible,
            logging_on,
        );

        assert_ne!(h1, null_mut());

        let vr_accel = 0;
        let val_accel: f64 = 1.0;
        let references = &[vr_accel];
        let mut values = [val_accel];

        let references_ptr = references.as_ptr();
        let values_ptr = values.as_mut_ptr();

        assert_eq!(
            fmi2SetupExperiment(h1, 0, 0.0, 0.0, 0, 0.0),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2EnterInitializationMode(h1), Fmi2Status::Fmi2OK.into());
        assert_eq!(fmi2ExitInitializationMode(h1), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2SetReal(h1, references_ptr, values.len(), values_ptr),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(
            fmi2GetReal(h1, references_ptr, values.len(), values_ptr),
            Fmi2Status::Fmi2OK.into()
        );
        assert_eq!(values, [val_accel]);

        assert_eq!(fmi2DoStep(h1, 0.0, 10.0, 0), Fmi2Status::Fmi2OK.into());

        let vr_pos_x = 2;
        let references = &[vr_pos_x];

        assert_eq!(
            fmi2GetReal(h1, references.as_ptr(), references.len(), values_ptr),
            Fmi2Status::Fmi2OK.into()
        );

        assert!(values[0] > 1.0); // should have moved more than 1 meter in 10 seconds with accel of 1

        fmi2FreeInstance(h1);
    }

    #[test]
    fn test_multiple_instantiations() {
        const N: usize = 10;

        let fmu_type = 1; // cosim

        let guid = CString::new("1234").unwrap();
        let guid_ptr = guid.as_ptr();

        let fmu_resources_path =
            CString::new("file:///C:/Users/clega/Desktop/pyfmu/examples/exported/Adder/resources")
                .unwrap();
        let fmu_resources_path_ptr = fmu_resources_path.as_ptr();

        let functions = Fmi2CallbackFunctions {
            logger: Some(logger),
            allocate_memory: None,
            free_memory: None,
            step_finished: None,
            component_environment: None,
        };
        let visible: i32 = 0;
        let logging_on: i32 = 0;

        let mut handles: Vec<*mut i32> = vec![];
        for i in 0..N {
            let instance_name = CString::new(i.to_string()).unwrap();
            let instance_name_ptr = instance_name.as_ptr();

            let h = fmi2Instantiate(
                instance_name_ptr,
                fmu_type,
                guid_ptr,
                fmu_resources_path_ptr,
                functions,
                visible,
                logging_on,
            );

            assert_eq!(
                fmi2SetupExperiment(h, 0, 0.0, 0.0, 0, 0.0),
                Fmi2Status::Fmi2OK.into()
            );
            assert_eq!(fmi2EnterInitializationMode(h), Fmi2Status::Fmi2OK.into());
            assert_eq!(fmi2ExitInitializationMode(h), Fmi2Status::Fmi2OK.into());

            handles.push(h);
        }

        for h in handles {
            assert_eq!(fmi2Terminate(h), Fmi2Status::Fmi2OK.into());
            fmi2FreeInstance(h)
        }
    }

    #[test]
    fn test_live_logging() {
        let instance_name = CString::new("live_logger").unwrap();
        let instance_name_ptr = instance_name.as_ptr();

        let fmu_type = 1;
        let guid = CString::new("1234").unwrap();
        let guid_ptr = guid.as_ptr();

        let fmu_resources_path = CString::new(
            "file:///C:/Users/clega/Desktop/pyfmu/examples/exported/LivePlotting/resources",
        )
        .unwrap();
        let fmu_resources_path_ptr = fmu_resources_path.as_ptr();

        let functions = Fmi2CallbackFunctions {
            logger: Some(logger),
            allocate_memory: None,
            free_memory: None,
            step_finished: None,
            component_environment: None,
        };
        let visible: i32 = 0;
        let logging_on: i32 = 0;

        println!("{:?}", instance_name);

        let h1 = fmi2Instantiate(
            instance_name_ptr,
            fmu_type,
            guid_ptr,
            fmu_resources_path_ptr,
            functions,
            visible,
            logging_on,
        );

        assert_eq!(
            fmi2SetupExperiment(h1, 0, 0.0, 0.0, 0, 0.0),
            Fmi2Status::Fmi2OK.into()
        );

        assert_eq!(fmi2EnterInitializationMode(h1), Fmi2Status::Fmi2OK.into());
        assert_eq!(fmi2ExitInitializationMode(h1), Fmi2Status::Fmi2OK.into());

        for i in 0..10 {
            assert_eq!(
                fmi2DoStep(h1, i as f64, i as f64 + 1.0, 0),
                Fmi2Status::Fmi2OK.into()
            );
        }

        assert_eq!(fmi2Terminate(h1), Fmi2Status::Fmi2OK.into());
        fmi2FreeInstance(h1);
    }
}
