use pyo3::prelude::*;
use pyo3::types::IntoPyDict;

fn run() -> Result<(), ()> {
    let gil = Python::acquire_gil();
    let py = gil.python();
    run_(py).map_err(|e| {
        // We can't display python error type via ::std::fmt::Display,
        // so print error here manually.
        e.print_and_set_sys_last_vars(py);
    })
}

fn run_(py: Python) -> PyResult<()> {
    let sys = py.import("sys")?;
    let version: String = sys.get("version")?.extract()?;
    let locals = [("os", py.import("os")?)].into_py_dict(py);
    let code = "os.getenv('USER') or os.getenv('USERNAME') or 'Unknown'";
    let user: String = py.eval(code, None, Some(&locals))?.extract()?;
    println!("Hello {}, I'm Python {}", user, version);
    Ok(())
}

#[test]
fn run_func() {
    run();
}
