use pyo3::types::PyModule;
use pyo3::Python;

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
