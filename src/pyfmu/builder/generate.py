"""
This module contains functionality to the creation of Python FMU projects
"""
from os import makedirs
from os.path import basename, curdir, isdir, join, realpath, dirname, exists, normpath
from os.path import exists, isfile
from pathlib import Path
from shutil import copy, copytree, rmtree
import json

from jinja2 import Template

from pyfmu.resources import Resources




def _create_config(config_path: str, class_name: str, relative_script_path: str):
        
    with open(config_path, 'w') as f:
        json.dump({
            "main_script" : relative_script_path,
            "main_class": class_name
        }, f,indent=4)


def read_configuration(config_path : str) -> object:

    print(f"configuration path is {config_path}")
    if(not exists(config_path)):
        raise FileNotFoundError("Failed to read configuration, the file does not exist")

    if(not isfile(config_path)):
        raise FileNotFoundError("Failed to read configuration, the specified path does not point to a file")


    try:
        with open(config_path,'r') as f:
            config = json.load(f)
    except Exception as e:
        raise RuntimeError("Failed to parse project configuration file. Ensure that it is well formed json")
    
    # TODO use json schema
    isWellFormed = hasattr(config,'main_script') and hasattr(config,'class_name')

    return config
        


class PyfmuProject():
    """Object representing an pyfmu project.
    """

    def __init__(self,
                 root: Path,
                 main_class: str = None,
                 main_script: str = None,
                 main_script_path: Path = None,
                 project_configuration: dict = None,
                 project_configuration_path: Path = None,
                 pyfmu_dir: Path = None,
                 ):

        self.main_class = main_class
        self.main_script = main_script
        self.main_script_path = main_script_path
        self.project_configuration = project_configuration
        self.project_configuration_path = project_configuration_path
        self.pyfmu_dir = pyfmu_dir
        self.root = root

    @staticmethod
    def from_existing(p: Path):
        """Instantiates an object representation based on an existing project

        Arguments:
            p {Path} -- path to the root of the project
        """
        try:
            p = Path(p)

        except Exception:
            raise RuntimeError(
                'Unable to load project. The specified argument could not be converted to a path')

        if(not p.is_dir()):
            raise FileNotFoundError(
                f'Unable to load project. The specified path does not appear to be a directory: {p}')

        # Verify that path points to a valid pyfmu project.

        # 1. Should be directory
        if(not Path.is_dir):
            raise ValueError(
                'Specified path does not point to a directory, ensure that the path is correct.')

        # 2. Should contain a 'project.json' in the root
        has_project_json = (p / 'project.json').is_file()

        if(not has_project_json):
            raise ValueError(
                'The directory does not contain a "project.json" file.')

        with open(p/'project.json') as f:
            project_json = json.load(f)

        # 2+ TODO validate using json schema
        main_script = project_json['main_script']
        main_class = project_json['main_class']
        main_script_path = p / 'resources' / main_script
        project_configuration_path = p / 'project.json'
        project_configuration = project_json
        pyfmu_dir = p / 'resources' / 'pyfmu'

        # 3. Should contain resources folder
        has_resources = (p / 'resources').is_dir()

        if(not has_resources):
            raise ValueError(
                'The directory does not contain a resource folder.')

        # 4. main script should exist inside resources.
        has_main_script = (p / 'resources' / main_script).is_file()

        if(not has_main_script):
            raise ValueError(
                f'The main python script: {main_script} could not be found in the resources folder. Ensure that the "project.json" defines the correct script.')

        # 5. TODO main class should be defined by main script

        project = PyfmuProject(root=p,
                               main_script=main_script,
                               main_class=main_class,
                               main_script_path=main_script_path,
                               project_configuration=project_configuration,
                               project_configuration_path=project_configuration_path,
                               pyfmu_dir=pyfmu_dir
                               )

        return project


def _create_dirs(project_path: str, exist_ok: bool = True):
    resources_path = join(project_path, "resources")

    try:
        makedirs(resources_path, exist_ok=True)
    except OSError:
        raise Exception(
            "Project with identical name already exists in that location. Please specify a new name, another directory or remove the old project.")
    except Exception as e:
        raise Exception("Failed to create directories for the Python project")


def _generate_fmu_template(template_path: str, main_class_name: str, script_output_path: str) -> None:

    r = None
    with open(template_path, 'r') as f:
        s = f.read()
        template = Template(s)

        r = template.render(
            {
                "class_name": main_class_name,
                "description": "",
                "model_name": main_class_name,
                "author": ""
            }
        )

    makedirs(dirname(script_output_path), exist_ok=True)

    with open(script_output_path, 'w') as f:
        f.write(r)


def _copy_pyfmu_to_project(project: PyfmuProject) -> PyfmuProject:

    resource_pyfmu_dir = Resources.get().pyfmu_dir

    project_pyfmu_dir = project.root / 'resources' / 'pyfmu'

    try:
        copytree(resource_pyfmu_dir, project_pyfmu_dir)
    except Exception as e:
        raise RuntimeError(
            "pyfmu library exists but could not be copied the generated project.") from e

    project.pyfmu_dir = project_pyfmu_dir

    return project


def _write_templateScript_to_project(project: PyfmuProject):

    resource_scriptTemplate_path = Resources.get().scriptTemplate_path

    with open(resource_scriptTemplate_path, 'r') as f:
        s = f.read()
        template = Template(s)

        r = template.render(
            {
                "class_name": project.main_class,
                "description": "",
                "model_name": project.main_class,
                "author": ""
            }
        )

    project_scriptTemplate_path = project.root / 'resources' / project.main_script

    makedirs(project_scriptTemplate_path.parent, exist_ok=True)

    with open(project_scriptTemplate_path, 'w') as f:
        f.write(r)

    project.main_script_path = project_scriptTemplate_path


def _write_projectConfig_to_project(project: PyfmuProject):

    project_configuration_path = project.root / 'project.json'

    config = {
        "main_class": project.main_class,
        "main_script": project.main_script
    }

    with open(project_configuration_path, 'w') as f:
        json.dump(config, f)

    project.project_configuration = config
    project.project_configuration_path = project_configuration_path


def create_project(project_path: str, main_class_name: str, overwrite=True) -> PyfmuProject:
    """Creates a new PyFMU project at the specified path.

    Parameters
    ----------
    project_path : str
        output path of the project
    main_class_name : str
        name of the main script 
    overwrite : bool, optional
        if true overwrite any existing files at the specified output path, by default True

    Returns
    -------
    PyfmuProject
        An object representing the exported project. 
        This may be used to access the paths of the various project artifacts.
    """
    project_path = Path(project_path)

    if(overwrite and exists(project_path)):
        rmtree(project_path)

    # TODO validate script names
    main_script = main_class_name.lower() + '.py'
    project = PyfmuProject(
        project_path, main_class=main_class_name, main_script=main_script)

    #_copy_pyfmu_to_project(project)
    _write_templateScript_to_project(project)
    _write_projectConfig_to_project(project)

    return project
