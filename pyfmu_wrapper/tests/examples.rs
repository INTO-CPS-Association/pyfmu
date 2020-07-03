use std::ffi::CStr;
use std::ffi::CString;
use std::mem::MaybeUninit;
use std::os::raw::c_char;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_void;
use std::ptr::null_mut;
use std::slice::from_raw_parts;
use std::str::Utf8Error;

use pyfmu;
use pyfmu::common::Fmi2Status;
use pyfmu::fmi2DoStep;
use pyfmu::fmi2EnterInitializationMode;
use pyfmu::fmi2ExitInitializationMode;
use pyfmu::fmi2FreeInstance;
use pyfmu::fmi2GetReal;
use pyfmu::fmi2GetString;
use pyfmu::fmi2Instantiate;
use pyfmu::fmi2SetDebugLogging;
use pyfmu::fmi2SetReal;
use pyfmu::fmi2SetupExperiment;
use pyfmu::utils::cstr_to_string;
use pyfmu::utils::get_example_resources_uri;
use pyfmu::Fmi2CallbackFunctions;
use pyfmu::*;

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

#[test]
fn types_fmu() {
    // see documentation of Cstring.as_ptr
    let instance_name = CString::new("a").unwrap();
    let instance_name_ptr = instance_name.as_ptr();

    let fmu_type = 1;
    let guid = CString::new("1234").unwrap();
    let guid_ptr = guid.as_ptr();

    let fmu_resources_path = CString::new(get_example_resources_uri("FmiTypes")).unwrap();
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

    let val_string_in_vec: Vec<String> = vec!["a", "b"].iter().map(|e| e.to_string()).collect(); // TODO convert this to val_string_in
    let val_string_in: [*const c_char; 2] = [val_str_in_str_a.as_ptr(), val_str_in_str_b.as_ptr()];

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
    // panic!("TODO check string return is correct");

    pub unsafe fn convert_double_pointer_to_vec<'a>(
        data: *const *const c_char,
        len: usize,
    ) -> Result<Vec<String>, Utf8Error> {
        from_raw_parts(data, len)
            .iter()
            .map(|arg| CStr::from_ptr(*arg).to_str().map(ToString::to_string))
            .collect()
    }

    let val_string_out_vec = unsafe {
        convert_double_pointer_to_vec(*val_str_out_cstr as *const _, val_string_in.len())
    }
    .unwrap();

    assert_eq!(val_string_in_vec, val_string_out_vec);
    assert_eq!(fmi2Terminate(h1), Fmi2Status::Fmi2OK.into());
    assert_eq!(fmi2Reset(h1), Fmi2Status::Fmi2OK.into());
    fmi2FreeInstance(h1);
}
