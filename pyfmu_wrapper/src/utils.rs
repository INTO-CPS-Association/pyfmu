use pyo3::types::PyModule;
use pyo3::Python;
use libc;

pub fn get_example_resources_uri(example_name: &str) -> String {
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

pub fn init() {
    
    extern "C" {
        fn dlopen(filename: *const libc::c_char, flags: libc::c_int) -> *mut libc::c_void;
        fn dlclose(handle: *mut libc::c_void) -> libc::c_int;
    }

    const RTLD_GLOBAL: libc::c_int = 0x00100;
    const RTLD_LAZY: libc::c_int = 0x00001;

    // make sure this path is null-terminated
    const LIBPYTHON: &'static str = "libpython3.8.so\0";
    unsafe {
        let handle = dlopen(LIBPYTHON.as_ptr() as *const i8, RTLD_GLOBAL | RTLD_LAZY);
        assert!(!handle.is_null());
    }
}