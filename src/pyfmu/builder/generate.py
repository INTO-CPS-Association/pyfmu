"""
This module contains functionality to the creation of Python FMU projects
"""
from os.path import exists, isfile
from os import makedirs
from pathlib import Path
import json
import logging
from tempfile import TemporaryDirectory
from shutil import copytree


from jinja2 import Template

from pyfmu.resources import Resources
from pyfmu.types import AnyPath


logger = logging.getLogger(__file__)


class PyfmuProject:
    """Object representing an pyfmu project.
    """

    def __init__(
        self,
        root: AnyPath,
        slave_class: str,
        slave_script: str,
        slave_script_path: AnyPath,
        project_configuration_path: AnyPath,
        resources_dir: AnyPath,
    ):

        self.slave_class = slave_class
        self.slave_script = slave_script
        self.slave_script_path = Path(slave_script_path)
        self.project_configuration_path = Path(project_configuration_path)
        self.resources_dir = Path(resources_dir)
        self.root = Path(root)

    def __fspath__(self):
        return self.root

    @staticmethod
    def from_existing(p: AnyPath) -> "PyfmuProject":
        """Instantiates an object representation based on an existing project

        Arguments:
            p {Path} -- path to the root of the project
        """
        try:
            root_path = Path(p)

        except Exception:
            raise RuntimeError(
                "Unable to load project. The specified argument could not be converted to a path"
            )

        if not root_path.is_dir():
            raise FileNotFoundError(
                f"Unable to load project. The specified path does not appear to be a directory: {p}"
            )

        # Verify that path points to a valid pyfmu project.

        # 1. Should be directory
        if not root_path.is_dir:
            raise ValueError(
                "Specified path does not point to a directory, ensure that the path is correct."
            )

        # 2. Should contain a 'project.json' in the root
        has_project_json = (root_path / "project.json").is_file()

        if not has_project_json:
            raise ValueError('The directory does not contain a "project.json" file.')

        with open(root_path / "project.json") as f:
            project_json = json.load(f)

        # 2+ TODO validate using json schema
        slave_script = project_json["slave_script"]
        slave_class = project_json["slave_class"]
        slave_script_path = root_path / "resources" / slave_script
        project_configuration_path = root_path / "project.json"
        project_configuration = project_json
        resources_dir = root_path / "resources"

        # 3. Should contain resources folder
        has_resources = resources_dir.is_dir()

        if not has_resources:
            raise ValueError("The directory does not contain a resource folder.")

        # 4. slave script should exist inside resources.
        has_slave_script = (root_path / "resources" / slave_script).is_file()

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
            project_configuration_path=project_configuration_path,
            resources_dir=resources_dir,
        )

        return project


def generate_project(output_path: AnyPath, slave_class: str) -> PyfmuProject:
    """Creates a new PyFMU project at the specified path.

    Parameters
    ----------
    output_path : str
        output path of the project
    slave_class : str
        name of the slave script 

    Returns
    -------
    PyfmuProject
        An object representing the exported project. 
        This may be used to access the paths of the various project artifacts.
    """
    logger.debug(
        f"Creating a new project to {output_path} with slave class {slave_class}"
    )
    output: Path = Path(output_path)

    with TemporaryDirectory() as tmpdir:

        tmpdir = Path(tmpdir)

        # generate placeholder script
        slave_script = slave_class.lower() + ".py"
        logger.debug(f"Writing placeholder for slave class to {slave_script}")
        resource_scriptTemplate_path = Resources.get().scriptTemplate_path

        with open(resource_scriptTemplate_path, "r") as f:
            s = f.read()
            template = Template(s)

            r = template.render(
                {
                    "class_name": slave_class,
                    "description": "",
                    "model_name": slave_class,
                    "author": "",
                }
            )

        project_template_path = tmpdir / "resources" / slave_script
        makedirs(project_template_path.parent, exist_ok=True)

        with open(project_template_path, "w") as f:
            f.write(r)

        # write configuration to project
        logging.debug(f"Writing project configuration to {project_template_path}")
        project_configuration_path = tmpdir / "project.json"

        config = {
            "slave_class": slave_class,
            "slave_script": slave_script,
        }

        with open(project_configuration_path, "w") as f:
            json.dump(config, f)

        # copy to output
        logging.debug(
            f"Copying temporary directory {tmpdir} to output directory {output}"
        )

        copytree(src=tmpdir, dst=output)

        return PyfmuProject(
            root=output,
            slave_class=slave_class,
            slave_script=slave_script,
            slave_script_path=output / "resources" / slave_script,
            project_configuration_path=output,
            resources_dir=output / "resources",
        )
