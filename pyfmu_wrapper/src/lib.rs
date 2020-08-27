// TODO enable once functions are implemented
// #![allow(dead_code)]
// #![allow(unreachable_code)]
// #![allow(unused_variables)]

use crate::common::SlaveHandle;
use libc::c_ulonglong;
use std::collections::HashMap;
use std::convert::TryFrom;
use std::ffi::CStr;
use std::ffi::CString;
use std::mem::forget;
use std::os::raw::c_char;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_uint;
use std::os::raw::c_void;
use std::ptr::null_mut;
use std::sync::Mutex;

#[macro_use]
extern crate lazy_static;

pub mod common;
mod cpython_backend;
mod interpreter_backend;
pub mod utils;

use crate::common::Fmi2Status;
use crate::common::Fmi2Type;
use crate::common::PyFmuBackend;

use crate::cpython_backend::CPythonEmbedded;
use crate::interpreter_backend::InterpreterBackend;

// ------------------------------------- Utility -------------------------------------

// ------------------------------------- Backend -------------------------------------

#[allow(dead_code)]
/// Defines available backend types.
/// These determine how the Python code defining the slave gets executed.
enum BackendsType {
    /// Use embedded CPython
    CPythonEmbedded,
    /// Spawn slaves as seperate Python processes
    InterpreterProcess,
}

type BackendType = Box<dyn PyFmuBackend + Sync + Send>;

/// Instantiates
fn get_backend(backend: BackendsType) -> BackendType {
    match backend {
        BackendsType::CPythonEmbedded => Box::new(
            CPythonEmbedded::new().expect("Unable to instantiate embedded CPython-backend"),
        ),
        BackendsType::InterpreterProcess => Box::new(
            InterpreterBackend::new("python3").expect("Unable to instantiate interpreter backend."),
        ),
    }
}

lazy_static! {
    static ref BACKEND: Mutex<BackendType> =
        Mutex::new(get_backend(BackendsType::InterpreterProcess));
}

// ------------------------------------- LOGGING (types) -------------------------------------

/// Represents the function signature of the logging callback function passsed
/// from the envrionment to the slave during instantiation.
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
    pub logger: Option<Fmi2CallbackLogger>,
    pub allocate_memory: Option<Fmi2CallbackAllocateMemory>,
    pub free_memory: Option<Fmi2CallbackFreeMemory>,
    pub step_finished: Option<Fmi2StepFinished>,
    pub component_environment: Option<*mut c_void>,
}

lazy_static! {
    /// In order to log messages from the Rust portion of the wrapper we store callback
    /// This is useful in cases where the wrapper itself fails, and it needs to be conveyed to the
    /// environment
    static ref LOGGERS: Mutex<HashMap<SlaveHandle, Fmi2CallbackLogger>> = Mutex::new(HashMap::new());
}

lazy_static! {
    static ref HANDLE_TO_NAMES: Mutex<HashMap<SlaveHandle, String>> = Mutex::new(HashMap::new());
}

/// Logs message using the callback the specified slave
/// Note that the slave must already have been instantiated.
fn log_slave(handle: &SlaveHandle, status: Fmi2Status, category: &str, message: &str) {
    let instance_name: String = HANDLE_TO_NAMES
        .lock()
        .unwrap()
        .get(handle)
        .expect("handle is not associated with an instance name, this is a bug")
        .clone();

    let instance_name = CString::new(instance_name.as_str()).unwrap();
    let category = CString::new(category).unwrap();
    let message = CString::new(message).unwrap();

    LOGGERS
        .lock()
        .unwrap()
        .get(handle)
        .expect("unable to get logger associated with handle")(
        std::ptr::null_mut(),
        instance_name.as_ptr(),
        status.into(),
        category.as_ptr(),
        message.as_ptr(),
    );
}

// ------------------------------------- FMI FUNCTIONS --------------------------------

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

// ------------------------------------- FMI FUNCTIONS (Life-Cycle) --------------------------------

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
    let instance_name = unsafe { CStr::from_ptr(instance_name) }
        .to_str()
        .expect("Unable to convert instance name to a string");

    let fmu_type = Fmi2Type::try_from(fmu_type).expect("Unrecognized FMU type code");

    let guid = unsafe { CStr::from_ptr(fmu_guid) }
        .to_str()
        .expect("Unable to convert guid to a string");

    let resource_location = unsafe { CStr::from_ptr(fmu_resource_location) }
        .to_str()
        .expect("Unable to convert resource location to a string");

    let logger = functions.logger.expect(
        "logging function appears to be null, this is not permitted by the FMI specification.",
    );

    let visible = visible != 0;
    let logging_on = logging_on != 0;

    let handle = BACKEND.lock().unwrap().instantiate(
        instance_name,
        fmu_type,
        guid,
        resource_location,
        logger,
        visible,
        logging_on,
    );

    // If slave was successfully instantiated a pointer to a heap allocated integer is returned
    // otherwise null is returned. Note that the integer must explictly be deallocated, which
    // must happen in the fmi2FreeSlave function, to avoid memory leaks.
    match handle {
        Ok(h) => {
            LOGGERS.lock().unwrap().insert(h, logger);
            Box::into_raw(Box::new(h))
        }
        Err(e) => {
            eprintln!("Failed instantiating slave {}", e);
            null_mut()
        }
    }
}

#[no_mangle]
pub extern "C" fn fmi2FreeInstance(c: *mut c_int) {
    let handle = unsafe { *c };

    match BACKEND.lock().unwrap().free_instance(handle) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetDebugLogging(
    c: *const SlaveHandle,
    logging_on: c_int,
    n_categories: usize,
    categories: *const *const c_char,
) -> c_int {
    let mut categories_vec: Vec<&str> = vec![];
    let n_categories = n_categories as isize;
    for i in 0..n_categories {
        let cat = unsafe { CStr::from_ptr(*categories.offset(i)).to_str().unwrap() };
        categories_vec.push(cat);
    }
    match BACKEND
        .lock()
        .unwrap()
        .set_debug_logging(unsafe { *c }, logging_on != 0, categories_vec)
    {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetupExperiment(
    c: *const SlaveHandle,
    tolerance_defined: c_int,
    tolerance: c_double,
    start_time: c_double,
    stop_time_defined: c_int,
    stop_time: c_double,
) -> c_int {
    let tolerance = {
        if tolerance_defined != 0 {
            Some(tolerance)
        } else {
            None
        }
    };

    let stop_time = {
        if stop_time_defined != 0 {
            Some(stop_time)
        } else {
            None
        }
    };

    let handle = unsafe { *c };

    match BACKEND
        .lock()
        .unwrap()
        .setup_experiment(handle, start_time, tolerance, stop_time)
    {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2EnterInitializationMode(c: *const SlaveHandle) -> c_int {
    let handle = unsafe { *c };

    match BACKEND.lock().unwrap().enter_initialization_mode(handle) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2ExitInitializationMode(c: *const SlaveHandle) -> c_int {
    let handle = unsafe { *c };

    match BACKEND.lock().unwrap().exit_initialization_mode(handle) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Terminate(c: *const SlaveHandle) -> c_int {
    let handle = unsafe { *c };

    match BACKEND.lock().unwrap().terminate(handle) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Reset(c: *const SlaveHandle) -> c_int {
    let handle = unsafe { *c };

    match BACKEND.lock().unwrap().reset(handle) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

// ------------------------------------- FMI FUNCTIONS (Stepping) --------------------------------

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2DoStep(
    c: *const SlaveHandle,
    current_communication_point: c_double,
    communication_step_size: c_double,
    no_set_fmu_state_prior_to_current_point: c_int,
) -> c_int {
    let handle = unsafe { *c };

    match BACKEND.lock().unwrap().do_step(
        handle,
        current_communication_point,
        communication_step_size,
        no_set_fmu_state_prior_to_current_point != 0,
    ) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2CancelStep(c: *const c_int) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

// ------------------------------------- FMI FUNCTIONS (Getters) --------------------------------
#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetReal(
    c: *const SlaveHandle,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_double,
) -> c_int {
    let handle = unsafe { *c };
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };

    match BACKEND.lock().unwrap().get_real(handle, references) {
        Ok((status, values_slave)) => {
            // if severity of status is warning or lower, copy results to
            // environments values vector
            if status <= Fmi2Status::Fmi2Warning {
                unsafe {
                    std::ptr::copy(values_slave.unwrap().as_ptr(), values, nvr);
                }
            }
            status.into()
        }
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetInteger(
    c: *const SlaveHandle,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> c_int {
    let handle = unsafe { *c };
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };

    match BACKEND.lock().unwrap().get_integer(handle, references) {
        Ok((status, values_slave)) => {
            // if severity of status is warning or lower, copy results to
            // environments values vector
            if status <= Fmi2Status::Fmi2Warning {
                unsafe {
                    std::ptr::copy(values_slave.unwrap().as_ptr(), values, nvr);
                }
            }
            status.into()
        }
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetBoolean(
    c: *const SlaveHandle,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> c_int {
    let handle = unsafe { *c };
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };

    match BACKEND.lock().unwrap().get_boolean(handle, references) {
        Ok((status, values_slave)) => {
            // if severity of status is warning or lower, copy results to
            // environments values vector
            if status <= Fmi2Status::Fmi2Warning {
                unsafe {
                    let values_slave = values_slave
                        .unwrap()
                        .into_iter()
                        .map(|s| s as i32)
                        .collect::<Vec<_>>();

                    std::ptr::copy(values_slave.as_ptr(), values, nvr);
                }
            }
            status.into()
        }
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

/* See https://github.com/rust-lang/rust/issues/21709
lazy_static! {
    /// To ensure that c-strings returned by fmi2GetString can be used by the envrionment,
    /// they must remain valid until another FMI function is invoked. see 2.1.7 p.23.
    /// We chose to do it on an instance basis, e.g. each instance has its own string buffer.
    static ref HANDLE_TO_STR_BUFFER: Mutex<HashMap<SlaveHandle, >> = Mutex::new(HashMap::new());
}
*/

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetString(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *mut *mut *mut c_char,
) -> c_int {
    let handle = unsafe { *c };
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };

    match BACKEND.lock().unwrap().get_string(handle, references) {
        Ok((status, values_slave)) => {
            if status <= Fmi2Status::Fmi2Warning {
                // Convert vector of strings into c-string double pointer
                // Note that we intentionally omit dropping the memory
                // This should be cleared by next call to a FMI function (currently is not the case)
                let mut vec_cstr = values_slave
                    .unwrap()
                    .into_iter()
                    .map(|s| CString::new(s).unwrap().into_raw())
                    .collect::<Vec<_>>();

                vec_cstr.shrink_to_fit();
                assert!(vec_cstr.len() == vec_cstr.capacity());

                let vec_cstr = Box::leak(Box::new(vec_cstr)); // TODO fix leak

                unsafe { std::ptr::write(values, vec_cstr.as_mut_ptr()) };
            }
            status.into()
        }
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

// ------------------------------------- FMI FUNCTIONS (Setters) --------------------------------

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetReal(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_double,
) -> c_int {
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let values = unsafe { std::slice::from_raw_parts(values, nvr) };
    let h = unsafe { *c };

    match BACKEND.lock().unwrap().set_real(h, references, values) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetInteger(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_int,
) -> c_int {
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let values = unsafe { std::slice::from_raw_parts(values, nvr) };
    let h = unsafe { *c };

    match BACKEND.lock().unwrap().set_integer(h, references, values) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetBoolean(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_int,
) -> c_int {
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let values = unsafe { std::slice::from_raw_parts(values as *const bool, nvr) };
    let h = unsafe { *c };

    match BACKEND.lock().unwrap().set_boolean(h, references, values) {
        Ok(status) => status.into(),
        Err(_e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

#[no_mangle]
#[allow(non_snake_case)]
#[allow(unused_variables)]
pub extern "C" fn fmi2SetString(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const *const c_char,
) -> c_int {
    let references = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let handle = unsafe { *c };

    let mut vec: Vec<&str> = Vec::with_capacity(nvr);

    for i in 0..nvr {
        unsafe {
            let cstr = CStr::from_ptr(*values.offset(i as isize))
                .to_str()
                .expect("Unable to convert C-string to Rust compatible string");
            vec.insert(i, cstr);
        };
    }

    match BACKEND
        .lock()
        .unwrap()
        .set_string(handle, references, vec.as_slice())
    {
        Ok(status) => status.into(),
        Err(e) => panic!("ERROR HANDLING NOT IMPLEMENTED"),
    }
}

// ------------------------------------- FMI FUNCTIONS (Derivatives) --------------------------------

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
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetRealInputDerivatives(c: *const c_int, vr: *const c_uint) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealOutputDerivatives(c: *const c_int) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

// ------------------------------------- FMI FUNCTIONS (Serialization) --------------------------------
#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetFMUstate(c: *const c_int, state: *const c_void) -> c_int {
    eprintln!("NOT IMPLEMENTED");
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
    eprintln!("NOT IMPLEMENTED");
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
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SerializedFMUstateSize(c: *const c_int, state: *mut *mut c_void) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetFMUstate(c: *const c_int, state: *mut *mut c_void) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2FreeFMUstate(c: *const c_int) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

// ------------------------------------- FMI FUNCTIONS (Status) --------------------------------

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_double,
) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStatus(
    c: *const c_int,
    status_kind: c_int,
    Fmi2Status: *mut c_int,
) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetIntegerStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_int,
) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetBooleanStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_int,
) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStringStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_char,
) -> c_int {
    eprintln!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}
