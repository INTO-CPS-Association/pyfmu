// TODO enable once functions are implemented
#![allow(dead_code)]
#![allow(unreachable_code)]
#![allow(unused_variables)]

use crate::common::SlaveHandle;
use libc::c_ulonglong;
use std::convert::TryFrom;
use std::ffi::CStr;
use std::os::raw::c_char;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_uint;
use std::os::raw::c_void;
use std::ptr::null_mut;

#[macro_use]
extern crate lazy_static;

mod common;
mod cpython_backend;

use crate::common::FMI2Logger;
use crate::common::Fmi2Status;
use crate::common::Fmi2Type;
use crate::common::PyFmuBackend;
use crate::cpython_backend::CPythonEmbedded;
//use crate::backends::CPythonEmbedded;

// ------------------------------------- Utility -------------------------------------

/// Capture Rust panics and return Fmi2Error instead
#[allow(unused_macros)]
macro_rules! ffi_panic_boundary {($($tt:tt)*) => (
    match catch_unwind(|| {$($tt)*}) {
        | Ok(ret) => ret,
        | Err(_) => {
            eprintln!("Rust panicked; return Fmi2Error");
            Fmi2Status::Fmi2Error.into()
        },
    }
)}

fn cstr_to_string(cstr: *const c_char) -> String {
    unsafe { CStr::from_ptr(cstr).to_string_lossy().into_owned() }
}

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

/// Instantiates
fn get_backend(backend: BackendsType) -> Box<dyn PyFmuBackend + Sync> {
    match backend {
        BackendsType::CPythonEmbedded => {
            Box::new(CPythonEmbedded::new().expect("Unable to instantiate backend"))
        }
        BackendsType::InterpreterProcess => panic!("not implementated"),
    }
}

lazy_static! {
    static ref BACKEND: Box<dyn PyFmuBackend + Sync> = get_backend(BackendsType::CPythonEmbedded);
}

// ------------------------------------- LOGGING -------------------------------------

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

/// Thin wrapper around C callback
struct LoggingWrapper {
    c_callback: Fmi2CallbackLogger,
}

impl LoggingWrapper {
    fn new(callback: Option<Fmi2CallbackLogger>) -> Self {
        match callback {
            None => panic!("Logging callback function appears to be null, which is not allowed according to the specificiation"),
            Some(c) => Self {
                c_callback: c
            }
        }
    }
}

impl FMI2Logger for LoggingWrapper {
    fn log(self, instance_name: &str, status: Fmi2Status, category: &str, message: &str) {
        panic!("not implemented")
    }
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

    let guid = unsafe { CStr::from_ptr(fmu_guid) }
        .to_str()
        .expect("Unable to convert guid to a string");
    let resource_location = unsafe { CStr::from_ptr(fmu_resource_location) }
        .to_str()
        .expect("Unable to convert resource location to a string");
    let fmu_type = Fmi2Type::try_from(fmu_type).expect("Unrecognized FMU type code");

    let visible = visible != 0;
    let logging_on = logging_on != 0;

    let logger = Box::new(LoggingWrapper::new(functions.logger));

    let handle = BACKEND.instantiate(
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
        Ok(h) => Box::into_raw(Box::new(h)),
        Err(e) => {
            eprintln!("Failed instantiating slave {}", e);
            null_mut()
        }
    }
}

#[no_mangle]
pub extern "C" fn fmi2FreeInstance(c: *mut c_int) {
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetDebugLogging(
    c: *const SlaveHandle,
    logging_on: c_int,
    n_categories: usize,
    categories: *const *const c_char,
) -> c_int {
    panic!("NOT IMPLEMENTED");
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
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2EnterInitializationMode(c: *const SlaveHandle) -> c_int {
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2ExitInitializationMode(c: *const SlaveHandle) -> c_int {
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Terminate(c: *const SlaveHandle) -> c_int {
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Reset(c: *const SlaveHandle) -> c_int {
    panic!("NOT IMPLEMENTED");
}

// ------------------------------------- FMI FUNCTIONS (Stepping) --------------------------------

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2DoStep(
    c: *const c_int,
    current_communication_point: c_double,
    communication_step_size: c_double,
    no_set_fmu_state_prior_to_current_point: c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
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
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetInteger(
    c: *const SlaveHandle,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetBoolean(
    c: *const SlaveHandle,
    vr: *const c_uint,
    nvr: usize,
    values: *mut c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetString(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *mut *mut *mut c_char,
) -> c_int {
    Fmi2Status::Fmi2Error.into()
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
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetInteger(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetBoolean(
    c: *const c_int,
    vr: *const c_uint,
    nvr: usize,
    values: *const c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
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
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
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
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetRealInputDerivatives(c: *const c_int, vr: *const c_uint) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetRealOutputDerivatives(c: *const c_int) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

// ------------------------------------- FMI FUNCTIONS (Serialization) --------------------------------
#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SetFMUstate(c: *const c_int, state: *const c_void) -> c_int {
    panic!("NOT IMPLEMENTED");
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
    panic!("NOT IMPLEMENTED");
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
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Error.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2SerializedFMUstateSize(c: *const c_int, state: *mut *mut c_void) -> c_int {
    panic!("NOT IMPLEMENTED");
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
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStatus(
    c: *const c_int,
    status_kind: c_int,
    Fmi2Status: *mut c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetIntegerStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2Fatal.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetBooleanStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_int,
) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2OK.into()
}

#[no_mangle]
#[allow(non_snake_case, unused_variables)]
pub extern "C" fn fmi2GetStringStatus(
    c: *const c_int,
    status_kind: c_int,
    value: *mut c_char,
) -> c_int {
    panic!("NOT IMPLEMENTED");
    Fmi2Status::Fmi2OK.into()
}
