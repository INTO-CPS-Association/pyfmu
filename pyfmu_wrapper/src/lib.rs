use num_enum::IntoPrimitive;
use num_enum::TryFromPrimitive;
use num_enum::TryFromPrimitiveError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3::types::PyTuple;
use pyo3::PyClass;
use std::boxed::Box;
use std::convert::TryFrom;
use std::convert::TryInto;
use std::ffi::CStr;
use std::ffi::CString;
use std::os::raw::c_char;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_uint;
use std::os::raw::c_ulonglong;
use std::os::raw::c_void;
use std::panic::catch_unwind;
use std::ptr::null_mut;
use std::sync::Mutex;
use std::vec::Vec;

use anyhow::Error;

#[macro_use]
extern crate lazy_static;
extern crate num_enum;

pub type SlaveHandle = i32;

//pub type Fmi2Component = *mut c_void;
pub type Fmi2Component = *mut i32;
pub type Fmi2ComponentEnvironment = *mut c_void;
pub type Fmi2FMUstate = *mut c_void;
pub type Fmi2ValueReference = c_uint;
pub type Fmi2Real = c_double;
pub type Fmi2Integer = c_int;
pub type Fmi2Boolean = c_int;
pub type Fmi2Char = c_char;
pub type Fmi2String = *const Fmi2Char;
pub type Fmi2Byte = c_char;
pub type Fmi2StatusType = c_int;
pub type Fmi2StatusKindType = c_int;
pub type SizeT = c_ulonglong;

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
    component_environment: Fmi2ComponentEnvironment,
    instance_name: Fmi2String,
    status: c_int,
    category: Fmi2String,
    message: Fmi2String,
    ...
);
pub type Fmi2CallbackAllocateMemory = extern "C" fn(nobj: c_ulonglong, size: c_ulonglong);
pub type Fmi2CallbackFreeMemory = extern "C" fn(obj: *const c_void);
pub type Fmi2StepFinished =
    extern "C" fn(component_environment: Fmi2ComponentEnvironment, status: Fmi2Status);

#[repr(C)]
pub struct Fmi2CallbackFunctions {
    logger: Option<Fmi2CallbackLogger>,
    allocate_memory: Option<Fmi2CallbackAllocateMemory>,
    free_memory: Option<Fmi2CallbackFreeMemory>,
    step_finished: Option<Fmi2StepFinished>,
    component_environment: Option<Fmi2ComponentEnvironment>,
}

/// Wraps C logging function pointer in a Rust struct enabling it to be passed to Python.
///
/// ## Notes
/// passing functions to Python
/// https://pyo3.rs/master/function.html
#[pyclass]
struct CallbacksWrapper {
    logger_callback: Option<Box<Fmi2CallbackLogger>>,
}

impl CallbacksWrapper {
    pub fn new(logger_callback: Option<Fmi2CallbackLogger>) -> Self {
        match logger_callback {
            Some(callback) => CallbacksWrapper {
                logger_callback: Some(Box::new(callback)),
            },
            _ => CallbacksWrapper {
                logger_callback: None,
            },
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
        let instance_name = CString::new(instance_name).unwrap().as_ptr();
        let category = CString::new(category).unwrap().as_ptr();
        let message = CString::new(message).unwrap().as_ptr();

        println!("Callback invoked");

        match &self.logger_callback {
            Some(callback) => callback(
                std::ptr::null_mut(),
                instance_name,
                status,
                category,
                message,
            ),
            _ => (),
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

lazy_static! {
    static ref SLAVE_HANDLES_LOCK: Mutex<i32> = Mutex::new(0);
}

lazy_static! {
    static ref SLAVE_MANAGER: pyo3::PyObject = {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let cls = || -> PyResult<PyObject> {
            let ctx: pyo3::PyObject = py
                .import("pyfmu.fmi2.slaveContext")
                .expect("Unable to import module declaring slave manager. Ensure that PyFMU is installed inside your current envrioment.")
                .get("Fmi2SlaveContext")?
                .call0()?
                .extract()?;
            println!("{:?}", ctx);
            Ok(ctx)
        };

        match cls() {
            Err(e) => {
                e.print_and_set_sys_last_vars(py);
                panic!("Unable to instantiate slave manager");
            }
            Ok(o) => o,
        }
    };
}

fn cstr_to_string(cstr: Fmi2String) -> String {
    unsafe { CStr::from_ptr(cstr).to_string_lossy().into_owned() }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetTypesPlatform() -> Fmi2String {
    static TYPES_PLATFORM: &str = "default";
    TYPES_PLATFORM.as_ptr() as *const i8
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetVersion() -> Fmi2String {
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
    c: Fmi2Component,
    logging_on: Fmi2Boolean,
    n_categories: SizeT,
    categories: *const Fmi2String,
) -> Fmi2StatusType {
    ffi_panic_boundary! {
        let set_debug = || -> Result<Fmi2StatusType, Error> {
            let mut categories_vec: Vec<&str> = vec![];
            let n_categories = n_categories as isize;
            for i in 0..n_categories {
                let cat = unsafe { CStr::from_ptr(*categories.offset(i)).to_str()? };
                categories_vec.push(cat);
            }
            let h = unsafe { *c };
            let gil = Python::acquire_gil();
            let py = gil.python();
            let status: i32 = SLAVE_MANAGER
                .call_method1(
                    py,
                    "set_debug_logging",
                    (h, categories_vec, logging_on != 0),
                )
                .expect("Call to set_debug_logging failed")
                .extract(py)
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
    c: Fmi2Component,
    tolerance_defined: Fmi2Boolean,
    tolerance: Fmi2Real,
    start_time: Fmi2Real,
    stop_time_defined: Fmi2Boolean,
    stop_time: Fmi2Real,
) -> Fmi2StatusType {
    let setup_experiment = || -> Result<Fmi2StatusType, Error> {
        let gil = Python::acquire_gil();
        let py = gil.python();

        let kwargs = PyDict::new(py);

        let h: i32 = unsafe { *c };

        kwargs.set_item("start_time", start_time).unwrap();
        kwargs.set_item("handle", h).unwrap();

        if tolerance_defined != 0 {
            kwargs.set_item("tolearance", tolerance).unwrap()
        };

        if stop_time_defined != 0 {
            kwargs.set_item("stop_time", stop_time).unwrap()
        };

        let status: Fmi2StatusType = SLAVE_MANAGER
            .call_method(py, "setup_experiment", (), Some(kwargs))
            .unwrap()
            .extract(py)
            .unwrap();

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
pub extern "C" fn fmi2EnterInitializationMode(c: Fmi2Component) -> Fmi2StatusType {
    call_parameterless_method(c, "enter_initialization_mode")
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2ExitInitializationMode(c: Fmi2Component) -> Fmi2StatusType {
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
pub extern "C" fn fmi2Terminate(c: Fmi2Component) -> Fmi2StatusType {
    call_parameterless_method(c, "terminate")
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Reset(c: Fmi2Component) -> Fmi2StatusType {
    call_parameterless_method(c, "terminate")
}

/// Call generic
fn call_parameterless_method(c: Fmi2Component, function: &str) -> Fmi2StatusType {
    let call_parameterless = || -> Result<Fmi2StatusType, Error> {
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        let status: i32 = SLAVE_MANAGER
            .call_method1(py, function, (h,))
            .map_pyerr(py)?
            .extract(py)
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

fn get_xxx<T>(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *mut T,
) -> Fmi2StatusType
where
    T: for<'a> FromPyObject<'a>,
{
    let get_real = || -> Result<Fmi2StatusType, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize) }.to_vec();
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with "map_error"
        let (values_vec, status): (Vec<T>, i32) = SLAVE_MANAGER
            .call_method1(py, "get_xxx", (h, references))
            .unwrap()
            .extract(py)
            .unwrap();

        unsafe {
            std::ptr::copy(values_vec.as_ptr(), values, nvr as usize);
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
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *mut Fmi2Real,
) -> Fmi2StatusType {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetInteger(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *mut Fmi2Integer,
) -> Fmi2StatusType {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetBoolean(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *mut Fmi2Boolean,
) -> Fmi2StatusType {
    get_xxx(c, vr, nvr, values)
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
#[allow(unused_variables)]
pub extern "C" fn fmi2GetString(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *mut Fmi2String,
) -> Fmi2StatusType {
    // TODO implement
    return Fmi2Status::Fmi2Fatal.into();
}

fn set_xxx<T>(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *const T,
) -> Fmi2StatusType
where
    T: for<'a> FromPyObject<'a> + Clone,
    (i32, Vec<Fmi2ValueReference>, Vec<T>): IntoPy<Py<PyTuple>>,
{
    let set_xxx = || -> Result<Fmi2StatusType, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize).to_vec() };
        let values = unsafe { std::slice::from_raw_parts(values, nvr as usize).to_vec() };
        let h = unsafe { *c };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with ?
        let status: i32 = SLAVE_MANAGER
            .call_method1(py, "set_xxx", (h, references, values))
            .unwrap()
            .extract(py)
            .unwrap();

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
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *const Fmi2Real,
) -> Fmi2StatusType {
    set_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetInteger(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *const Fmi2Integer,
) -> Fmi2StatusType {
    set_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetBoolean(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    values: *const Fmi2Boolean,
) -> Fmi2StatusType {
    set_xxx(c, vr, nvr, values)
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
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: SizeT,
    value: *const Fmi2String,
) -> Fmi2StatusType {
    Fmi2Status::Fmi2Fatal.into() // TODO
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
#[allow(non_snake_case)]
pub extern "C" fn fmi2Instantiate(
    instance_name: *const c_char,
    fmu_type: c_int,
    fmu_guid: *const c_char,
    fmu_resource_location: *const c_char,
    functions: Fmi2CallbackFunctions,
    visible: c_int,
    logging_on: c_int,
) -> Fmi2Component {
    eprintln!("YOOOOO this should really be passed to stderr");

    let get_instance = || -> Result<SlaveHandle, Error> {
        println!("Trying to acquire GIL");

        let gil = Python::acquire_gil();
        let py = gil.python();
        let kwargs = PyDict::new(py);

        kwargs
            .set_item("instance_name", cstr_to_string(instance_name))
            .map_pyerr(py)?;

        kwargs.set_item("fmu_type", fmu_type as i32).map_pyerr(py)?;
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
        // kwargs.set_item("logging_callback", ()).unwrap();
        let wrapper = Py::new(
            py,
            CallbacksWrapper {
                logger_callback: None,
            },
        )
        .map_pyerr(py)?;
        kwargs.set_item("logging_callback", wrapper).map_pyerr(py)?;

        let handle: i32 = SLAVE_MANAGER
            .call_method(py, "instantiate", (), Some(kwargs))
            .map_pyerr(py)?
            .extract(py)
            .map_pyerr(py)?;

        Ok(handle)
    };

    match catch_unwind(|| get_instance()) {
        Err(e) => {
            println!("a panic occurrec inside the code");
            // TODO log error message
            null_mut()
        }

        Ok(res) => match res {
            Ok(h) => {
                println!("Returning handle {}", h);
                Box::into_raw(Box::new(h))
            }
            Err(e) => {
                println!("whoops an error was raised: {}", e);
                null_mut()
            }
        },
    }
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetRealInputDerivatives(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
) -> Fmi2StatusType {
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealOutputDerivatives(c: Fmi2Component) -> Fmi2StatusType {
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2CancelStep(c: Fmi2Component) -> Fmi2StatusType {
    call_parameterless_method(c, "cancel_step")
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealStatus(
    c: Fmi2Component,
    status_kind: u8,
    value: *mut Fmi2Real,
) -> Fmi2StatusType {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStatus(
    c: Fmi2Component,
    status_kind: Fmi2StatusKindType,
    Fmi2Status: *mut Fmi2StatusType,
) -> Fmi2StatusType {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetIntegerStatus(
    c: Fmi2Component,
    status_kind: u8,
    value: *mut Fmi2Integer,
) -> Fmi2StatusType {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetBooleanStatus(
    c: Fmi2Component,
    status_kind: u8,
    value: *mut Fmi2Boolean,
) -> Fmi2StatusType {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStringStatus(
    c: Fmi2Component,
    status_kind: u8,
    value: *mut Fmi2String,
) -> Fmi2StatusType {
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2DoStep(
    c: Fmi2Component,
    current_communication_point: Fmi2Real,
    communication_step_size: Fmi2Real,
    no_set_fmu_state_prior_to_current_point: Fmi2Boolean,
) -> Fmi2StatusType {
    match c {
        c if c.is_null() => Fmi2Status::Fmi2Error.into(), // TODO add logging
        c => {
            let gil = Python::acquire_gil();
            let py = gil.python();
            let status: i32 = SLAVE_MANAGER
                .call_method1(
                    py,
                    "do_step",
                    (
                        unsafe { *c },
                        current_communication_point,
                        communication_step_size,
                        no_set_fmu_state_prior_to_current_point,
                    ),
                )
                .expect(&format!("unable to invoke do_step method for slave {}", 1))
                .extract(py)
                .expect("do_step should return a integer corresponding to a status");

            Fmi2Status::try_from(status)
                .expect(&format!(
                    "status {} returned from do_step is not a valid FMI2 status code.",
                    status
                ))
                .into()
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
    let gil = Python::acquire_gil();
    let py = gil.python();

    if c.is_null() {
        ()
    }
    match SLAVE_MANAGER.call_method1(py, "free_instance", (unsafe { *c },)) {
        Err(e) => {
            e.print_and_set_sys_last_vars(py);
        }
        _ => (),
    };

    let _ = unsafe {
        Box::from_raw(c);
    };
}

#[no_mangle]
pub extern "C" fn print_str(msg: *const c_char) {
    let cstr = unsafe { CStr::from_ptr(msg).to_str().unwrap() };

    let uppercase = cstr.to_uppercase();

    println!("In uppercase is {}", uppercase)

    //unsafe { std::ptr::copy(uppercase.as_ptr(), msg as *mut u8, 10) };
}

#[no_mangle]
pub extern "C" fn print_str_callback(msg: *const c_char, functions: Fmi2CallbackFunctions) {
    let cstr = unsafe { CStr::from_ptr(msg).to_str().unwrap() };

    let uppercase = cstr.to_uppercase();

    println!("In uppercase is {}", uppercase)

    //unsafe { std::ptr::copy(uppercase.as_ptr(), msg as *mut u8, 10) };
}

#[cfg(test)]
mod tests {
    // Note this useful idiom: importing names from outer (for mod tests) scope.
    use super::*;
    use std::ptr::null_mut;
    #[test]
    fn instantiate_works() {
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
            logger: None,
            allocate_memory: None,
            free_memory: None,
            step_finished: None,
            component_environment: None,
        };
        let visible: Fmi2Boolean = 0;
        let logging_on: Fmi2Boolean = 0;

        println!("{:?}", instance_name);

        let mut h1 = fmi2Instantiate(
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
        let mut values = [10.0, 20.0];

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

        // assert_eq!(fmi2ExitInitializationMode(h1), Fmi2Status::Fmi2OK.into());

        assert_eq!(
            fmi2SetReal(h1, references_ptr, 2, values_ptr),
            Fmi2Status::Fmi2OK.into()
        );

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
}
