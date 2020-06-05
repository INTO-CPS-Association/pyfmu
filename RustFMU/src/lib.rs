use failure::Error;
use num_enum::IntoPrimitive;
use num_enum::TryFromPrimitive;
use num_enum::TryFromPrimitiveError;
use pyo3::prelude::*;
use pyo3::types::PyDict;
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
use std::sync::Mutex;
use std::vec::from_elem;
use std::vec::Vec;

#[macro_use]
extern crate lazy_static;
extern crate num_enum;

pub type SlaveHandle = i32;

//pub type Fmi2Component = *mut c_void;
pub type Fmi2Component = Option<*mut i32>;
pub type Fmi2ComponentEnvironment = *mut c_void;
pub type Fmi2FMUstate = *mut c_void;
pub type Fmi2ValueReference = c_uint;
pub type Fmi2Real = c_double;
pub type Fmi2Integer = c_int;
pub type Fmi2Boolean = c_int;
pub type Fmi2Char = c_char;
pub type Fmi2String = *const Fmi2Char;
pub type Fmi2Byte = c_char;
pub type size_t = c_ulonglong;

pub type Fmi2CallbackLogger = extern "C" fn(
    component_environment: Fmi2ComponentEnvironment,
    instance_name: Fmi2String,
    status: Fmi2Status,
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

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetDebugLogging(
    c: Fmi2Component,
    logging_on: Fmi2Boolean,
    n_categories: size_t,
    categories: *const Fmi2String,
) -> Fmi2Status {
    let set_debug = || -> Result<Fmi2Status, Error> {
        let mut categories_vec: Vec<&str> = vec![];
        let n_categories = n_categories as isize;

        for i in 0..n_categories {
            let cat = unsafe { CStr::from_ptr(*categories.offset(i)).to_str()? };
            categories_vec.push(cat);
        }

        let h = unsafe { *c.expect("handle was null") };

        let gil = Python::acquire_gil();
        let py = gil.python();
        let status: i32 = SLAVE_MANAGER
            .call_method1(
                py,
                "set_debug_logging",
                (h, categories_vec, logging_on != 0),
            )
            .unwrap()
            .extract(py)
            .unwrap();

        Ok(Fmi2Status::try_from(status)?)
    };

    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetupExperiment(
    c: Fmi2Component,
    tolerance_defined: Fmi2Boolean,
    tolerance: Fmi2Real,
    start_time: Fmi2Real,
    stop_time_defined: Fmi2Boolean,
    stop_time: Fmi2Real,
) -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2EnterInitializationMode() -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2ExitInitializationMode() -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Terminate() -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Reset() -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

fn get_xxx<T>(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    values: *mut T,
) -> Fmi2Status
where
    T: for<'a> FromPyObject<'a>,
{
    let get_real = || -> Result<Fmi2Status, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize) }.to_vec();
        let h = unsafe { *c.expect("handle was null") };

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

        Ok(Fmi2Status::try_from(status)?)
    };

    match get_real() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error
        }
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetReal(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    values: *mut Fmi2Real,
) -> Fmi2Status {
    get_xxx(c, vr, nvr, values)
    // let get_real = || -> Result<Fmi2Status, Error> {
    //     let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize) }.to_vec();
    //     let h = unsafe { *c.expect("handle was null") };

    //     let gil = Python::acquire_gil();
    //     let py = gil.python();

    //     // TODO replace with "?"
    //     let (values_vec, status): (Vec<Fmi2Real>, i32) = SLAVE_MANAGER
    //         .call_method1(py, "get_xxx", (h, references))
    //         .unwrap()
    //         .extract(py)
    //         .unwrap();

    //     unsafe {
    //         std::ptr::copy(values_vec.as_ptr(), values, nvr as usize);
    //     }

    //     Ok(Fmi2Status::try_from(status)?)
    // };

    // match get_real() {
    //     Ok(s) => s,
    //     Err(e) => {
    //         println!("{}", e);
    //         Fmi2Status::Fmi2Error
    //     }
    // }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetInteger(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    values: *mut Fmi2Integer,
) -> Fmi2Status {
    get_xxx(c, vr, nvr, values)
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetBoolean(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    value: *const Fmi2Boolean,
) -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2GetString(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    value: *const Fmi2String,
) -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetReal(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    values: *const Fmi2Real,
) -> Fmi2Status {
    let set_real = || -> Result<Fmi2Status, Error> {
        let references = unsafe { std::slice::from_raw_parts(vr, nvr as usize).to_vec() };
        let values = unsafe { std::slice::from_raw_parts(values, nvr as usize).to_vec() };
        let h = unsafe { *c.expect("handle was null") };

        let gil = Python::acquire_gil();
        let py = gil.python();

        // TODO replace with ?
        let status: i32 = SLAVE_MANAGER
            .call_method1(py, "set_xxx", (h, references, values))
            .unwrap()
            .extract(py)
            .unwrap();

        Ok(Fmi2Status::try_from(status)?)
    };

    match set_real() {
        Ok(s) => s,
        Err(e) => {
            println!("{}", e);
            Fmi2Status::Fmi2Error
        }
    }
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetInteger(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    value: *const Fmi2Integer,
) -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetBoolean(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    value: *const Fmi2Boolean,
) -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2SetString(
    c: Fmi2Component,
    vr: *const Fmi2ValueReference,
    nvr: size_t,
    value: *const Fmi2String,
) -> Fmi2Status {
    Fmi2Status::Fmi2Fatal
}

#[no_mangle]
#[allow(non_snake_case)]
pub extern "C" fn fmi2Instantiate(
    instance_name: Fmi2String,
    fmu_type: Fmi2Type,
    fmu_guid: Fmi2String,
    fmu_resource_location: Fmi2String,
    functions: Fmi2CallbackFunctions,
    visible: Fmi2Boolean,
    logging_on: Fmi2Boolean,
) -> Fmi2Component {
    let gil = Python::acquire_gil();
    let py = gil.python();

    let kwargs = PyDict::new(py);

    kwargs
        .set_item("instance_name", cstr_to_string(instance_name))
        .unwrap();
    kwargs.set_item("fmu_type", fmu_type as i32).unwrap();
    kwargs.set_item("guid", cstr_to_string(fmu_guid)).unwrap();
    kwargs
        .set_item("resources_uri", cstr_to_string(fmu_resource_location))
        .unwrap();
    kwargs.set_item("visible", visible != 0).unwrap();
    kwargs.set_item("logging_on", logging_on != 0).unwrap();
    kwargs.set_item("logging_callback", ()).unwrap();

    let get_instance = || -> PyResult<SlaveHandle> {
        let handle: i32 = SLAVE_MANAGER
            .call_method(py, "instantiate", (), Some(kwargs))?
            .extract(py)?;
        Ok(handle)
    };

    match get_instance() {
        Err(e) => {
            e.print_and_set_sys_last_vars(py);
            // TODO log error message
            None
        }
        Ok(h) => Some(Box::into_raw(Box::new(h))),
    }
}

#[allow(non_snake_case)]
pub extern "C" fn fmi2DoStep(
    c: Fmi2Component,
    current_communication_point: Fmi2Real,
    communication_step_size: Fmi2Real,
    no_set_fmu_state_prior_to_current_point: Fmi2Boolean,
) -> Fmi2Status {
    match c {
        None => Fmi2Status::Fmi2Error, // TODO add logging
        Some(c) => {
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

            Fmi2Status::try_from(status).expect(&format!(
                "status {} returned from do_step is not a valid FMI2 status code.",
                status
            ))
        }
    }
}

#[no_mangle]
pub extern "C" fn fmi2FreeInstance(c: Fmi2Component) {
    let gil = Python::acquire_gil();
    let py = gil.python();
    let free_instance = || match c {
        None => panic!("unable to free instance, handle is null"),

        Some(c) => {
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
    };

    free_instance();
}

#[cfg(test)]
mod tests {
    // Note this useful idiom: importing names from outer (for mod tests) scope.
    use super::*;
    #[test]
    fn instantiate_works() {
        // see documentation of Cstring.as_ptr
        let instance_name = CString::new("a").unwrap();
        let instance_name_ptr = instance_name.as_ptr();

        let fmu_type = Fmi2Type::Fmi2CoSimulation;
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

        let h1 = fmi2Instantiate(
            instance_name_ptr,
            fmu_type,
            guid_ptr,
            fmu_resources_path_ptr,
            functions,
            visible,
            logging_on,
        );

        assert_ne!(h1, None);

        let status = fmi2DoStep(h1, 0.0, 10.0, 0);

        let references = &[0, 1];
        let mut values = [10.0, 20.0];

        let references_ptr = references.as_ptr();
        let values_ptr = values.as_mut_ptr();

        // let logAll = CString::new("logAll").unwrap();
        // let categories = [];
        // let categories_ptr = categories.as_ptr();

        // assert_eq!(
        //     fmi2SetDebugLogging(h1, 0, 1, categories_ptr),
        //     Fmi2Status::Fmi2OK
        // );

        assert_eq!(
            fmi2SetReal(h1, references_ptr, 2, values_ptr),
            Fmi2Status::Fmi2OK
        );

        assert_eq!(
            fmi2GetReal(h1, references_ptr, 2, values_ptr),
            Fmi2Status::Fmi2OK
        );
        assert_eq!(values, [10.0, 20.0]);

        let references = &[2];
        let references_ptr = references.as_ptr();

        assert_eq!(
            fmi2GetReal(h1, references_ptr, 1, values_ptr),
            Fmi2Status::Fmi2OK
        );

        assert_eq!(values[0], 30.0);

        fmi2FreeInstance(h1);

        assert_eq!(status, Fmi2Status::Fmi2OK)
    }
}
