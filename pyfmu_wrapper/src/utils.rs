use std::env::current_dir;
use std::ffi::CStr;
use std::os::raw::c_char;
use std::path::Path;

use anyhow::Error;
use pyo3::types::PyModule;
use pyo3::Python;

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

pub unsafe fn cstr_to_string(cstr: *const c_char) -> String {
    CStr::from_ptr(cstr).to_string_lossy().into_owned()
}

pub fn get_example_resources_uri(example_name: &str) -> String {
    let path = current_dir()
        .unwrap()
        .parent()
        .unwrap()
        .join("examples")
        .join("exported")
        .join(example_name)
        .join("resources");

    format!("file:\\{}", path.to_str().unwrap())
}

pub fn get_example_resources_uri_old(example_name: &str) -> String {
    let gil = Python::acquire_gil();
    let py = gil.python();

    let utils = PyModule::from_code(
        py,
        r#"
from pathlib import Path
def get_example_resources_uri(example_name: str) -> str:
    return Path(
        Path.cwd().parent / "examples" / "exported" / example_name / "resources"
    ).as_uri()
    "#,
        "utils",
        "utils.py",
    )
    .expect("unable to import module");

    utils
        .call1("get_example_resources_uri", (example_name,))
        .unwrap()
        .extract()
        .unwrap()
}
