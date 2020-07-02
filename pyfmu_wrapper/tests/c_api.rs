// Note this useful idiom: importing names from outer (for mod tests) scope.
use pyfmu::fmi2DoStep;
use pyfmu::fmi2EnterInitializationMode;
use pyfmu::fmi2ExitInitializationMode;
use pyfmu::fmi2FreeInstance;
use pyfmu::fmi2GetReal;
use pyfmu::fmi2Instantiate;
use pyfmu::fmi2SetDebugLogging;
use pyfmu::fmi2SetReal;
use pyfmu::fmi2SetupExperiment;
use std::ffi::CString;
use std::os::raw::c_char;
use std::os::raw::c_int;
use std::os::raw::c_void;
use std::ptr::null_mut;

use pyfmu;
use pyfmu::common::Fmi2Status;
use pyfmu::utils::cstr_to_string;
use pyfmu::utils::get_example_resources_uri;
use pyfmu::Fmi2CallbackFunctions;

#[allow(unused_variables, dead_code)] // linter does not detect tests use of this code
extern "C" fn logger(
    component_environment: *mut c_void,
    instance_name: *const c_char,
    status: c_int,
    category: *const c_char,
    message: *const c_char,
) {
    let instance_name = unsafe { cstr_to_string(instance_name) };
    let category = unsafe { cstr_to_string(category) };
    let message = unsafe { cstr_to_string(message) };
    println!(
        "Callback:{}:{}:{}:{}",
        instance_name, category, status, message
    )
}

#[test]
fn adder_fmu() {
    // see documentation of Cstring.as_ptr
    let instance_name = CString::new("a").unwrap();
    let instance_name_ptr = instance_name.as_ptr();

    let fmu_type = 1;
    let guid = CString::new("1234").unwrap();
    let guid_ptr = guid.as_ptr();

    let fmu_resources_path = CString::new(get_example_resources_uri("Adder")).unwrap();
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
        Fmi2Status::Fmi2OK as c_int
    );

    assert_eq!(values[0], 30.0);

    fmi2FreeInstance(h1);

    assert_eq!(status, Fmi2Status::Fmi2OK.into())
}
