use crate::common::Fmi2CallbackFunctions;
use std::ffi::CStr;
use std::os::raw::c_char;
use std::os::raw::c_int;
use std::sync::Mutex;
use std::vec::Vec;

#[macro_use]
extern crate lazy_static;

mod common;

use crate::common::Fmi2Status;
use crate::common::PyFmuBackend;

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
        CPythonEmbedded => panic!("not implemented"),
        InterpreterProcess => panic!("not implementated"),
    }
}

lazy_static! {
    static ref BACKEND: &'static (dyn PyFmuBackend + Sync) =
        get_backend(BackendsType::CPythonEmbedded);
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
)
// -> *mut c_int
{
    BACKEND.instantiate();
}
