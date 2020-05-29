"""
This module contains functionality to the creation of Python FMU projects
"""
from os import makedirs
from os.path import join, dirname, exists, isfile
from pathlib import Path
from shutil import rmtree
import json

from jinja2 import Template

from pyfmu.resources import Resources
from pyfmu.types import AnyPath


def _create_config(config_path: str, class_name: str, relative_script_path: str):

    with open(config_path, "w") as f:
        json.dump(
            {"slave_script": relative_script_path, "slave_class": class_name},
            f,
            indent=4,
        )


def read_configuration(config_path: str) -> object:

    print(f"configuration path is {config_path}")
    if not exists(config_path):
        raise FileNotFoundError("Failed to read configuration, the file does not exist")

    if not isfile(config_path):
        raise FileNotFoundError(
            "Failed to read configuration, the specified path does not point to a file"
        )

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except Exception:
        raise RuntimeError(
            "Failed to parse project configuration file. Ensure that it is well formed json"
        )

    # TODO use json schema
    _ = hasattr(config, "slave_script") and hasattr(config, "class_name")

    return config


class PyfmuProject:
    """Object representing an pyfmu project.
    """

    def __init__(
        self,
        root: Path,
        slave_class: str = None,
        slave_script: str = None,
        slave_script_path: Path = None,
        project_configuration: dict = None,
        project_configuration_path: Path = None,
        resources_dir: Path = None,
    ):

        self.slave_class = slave_class
        self.slave_script = slave_script
        self.slave_script_path = slave_script_path
        self.project_configuration = project_configuration
        self.project_configuration_path = project_configuration_path
        self.resources_dir = resources_dir
        self.root = root

    def __fspath__(self):
        return self.root

    @staticmethod
    def from_existing(p: AnyPath) -> "PyfmuProject":
        """Instantiates an object representation based on an existing project

        Arguments:
            p {Path} -- path to the root of the project
        """
        try:
            p = Path(p)

        except Exception:
            raise RuntimeError(
                "Unable to load project. The specified argument could not be converted to a path"
            )

        if not p.is_dir():
            raise FileNotFoundError(
                f"Unable to load project. The specified path does not appear to be a directory: {p}"
            )

        # Verify that path points to a valid pyfmu project.

        # 1. Should be directory
        if not Path.is_dir:
            raise ValueError(
                "Specified path does not point to a directory, ensure that the path is correct."
            )

        # 2. Should contain a 'project.json' in the root
        has_project_json = (p / "project.json").is_file()

        if not has_project_json:
            raise ValueError('The directory does not contain a "project.json" file.')

        with open(p / "project.json") as f:
            project_json = json.load(f)

        # 2+ TODO validate using json schema
        slave_script = project_json["slave_script"]
        slave_class = project_json["slave_class"]
        slave_script_path = p / "resources" / slave_script
        project_configuration_path = p / "project.json"
        project_configuration = project_json
        resources_dir = p / "resources"

        # 3. Should contain resources folder
        has_resources = resources_dir.is_dir()

        if not has_resources:
            raise ValueError("The directory does not contain a resource folder.")

        # 4. slave script should exist inside resources.
        has_slave_script = (p / "resources" / slave_script).is_file()

        if not has_slave_script:
            raise ValueError(
                f'The main python script: {slave_script} could not be found in the resources folder. Ensure that the "project.json" defines the correct script.'
            )

        # 5. TODO slave class should be defined by slave script

        project = PyfmuProject(
            root=p,
            slave_script=slave_script,
            slave_class=slave_class,
            slave_script_path=slave_script_path,
            project_configuration=project_configuration,
            project_configuration_path=project_configuration_path,
            resources_dir=resources_dir,
        )

        return project


def _create_dirs(project_path: str, exist_ok: bool = True):
    resources_path = join(project_path, "resources")

    try:
        makedirs(resources_path, exist_ok=True)
    except OSError:
        raise Exception(
            "Project with identical name already exists in that location. Please specify a new name, another directory or remove the old project."
        )
    except Exception:
        raise Exception("Failed to create directories for the Python project")


def _generate_fmu_template(
    template_path: str, slave_class_name: str, script_output_path: str
) -> None:

    r = None
    with open(template_path, "r") as f:
        s = f.read()
        template = Template(s)

        r = template.render(
            {
                "class_name": slave_class_name,
                "description": "",
                "model_name": slave_class_name,
                "author": "",
            }
        )

    makedirs(dirname(script_output_path), exist_ok=True)

    with open(script_output_path, "w") as f:
        f.write(r)


def _write_templateScript_to_project(project: PyfmuProject):

    resource_scriptTemplate_path = Resources.get().scriptTemplate_path

    with open(resource_scriptTemplate_path, "r") as f:
        s = f.read()
        template = Template(s)

        r = template.render(
            {
                "class_name": project.slave_class,
                "description": "",
                "model_name": project.slave_class,
                "author": "",
            }
        )

    project_scriptTemplate_path = project.root / "resources" / project.slave_script

    makedirs(project_scriptTemplate_path.parent, exist_ok=True)

    with open(project_scriptTemplate_path, "w") as f:
        f.write(r)

    project.slave_script_path = project_scriptTemplate_path


def _write_projectConfig_to_project(project: PyfmuProject):

    project_configuration_path = project.root / "project.json"

    config = {"slave_class": project.slave_class, "slave_script": project.slave_script}

    with open(project_configuration_path, "w") as f:
        json.dump(config, f)

    project.project_configuration = config
    project.project_configuration_path = project_configuration_path


def create_project(
    project_path: str, slave_class_name: str, overwrite=True
) -> PyfmuProject:
    """Creates a new PyFMU project at the specified path.

    Parameters
    ----------
    project_path : str
        output path of the project
    slave_class_name : str
        name of the slave script 
    overwrite : bool, optional
        if true overwrite any existing files at the specified output path, by default True

    Returns
    -------
    PyfmuProject
        An object representing the exported project. 
        This may be used to access the paths of the various project artifacts.
    """
    project_path = Path(project_path)

    if overwrite and exists(project_path):
        rmtree(project_path)

    # TODO validate script names
    slave_script = slave_class_name.lower() + ".py"
    project = PyfmuProject(
        project_path, slave_class=slave_class_name, slave_script=slave_script
    )

    # _copy_pyfmu_to_project(project)
    _write_templateScript_to_project(project)
    _write_projectConfig_to_project(project)

    return project
