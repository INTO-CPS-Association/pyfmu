use libc::c_ulonglong;
use std::convert::TryFrom;
use std::ffi::CStr;
use std::os::raw::c_char;
use std::os::raw::c_int;
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
fn get_backend(backend: BackendsType) -> &'static (dyn PyFmuBackend + Sync) {
    match backend {
        BackendsType::CPythonEmbedded => {
            CPythonEmbedded::new().expect("Unable to instantiate backend")
        }
        BackendsType::InterpreterProcess => panic!("not implementated"),
    }
}

lazy_static! {
    static ref BACKEND: &'static (dyn PyFmuBackend + Sync) =
        get_backend(BackendsType::CPythonEmbedded);
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
