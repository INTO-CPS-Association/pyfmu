use std::env::current_dir;

pub fn get_example_resources_uri(example_name: &str) -> String {
    let cd = current_dir().expect("unable to read current working directory");

    let resources_dir = cd
        .parent()
        .unwrap()
        .join("examples")
        .join("exported")
        .join(example_name)
        .join("resources")
        .as_path()
        .canonicalize()
        .unwrap();

    format!("file:///{}", resources_dir.to_str().unwrap())
}
