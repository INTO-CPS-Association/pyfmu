"""
This module contains functionality to the creation of Python FMU projects
"""
from os import makedirs
from os.path import  basename, curdir, isdir, join, realpath, dirname, exists
from shutil import copy, copytree, rmtree
from jinja2 import Template

from .configure import _create_config

def _create_dirs(project_path: str, exist_ok: bool = True):
    resources_path = join(project_path, "resources")

    try:
        makedirs(resources_path, exist_ok=True)
    except OSError:
        raise Exception(
            "Project with identical name already exists in that location. Please specify a new name, another directory or remove the old project.")
    except Exception as e:
        raise Exception("Failed to create directories for the Python project")

def _generate_fmu_template(template_path: str, main_class_name: str, script_output_path : str) -> None:

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

def _copy_python_library_to_sources(python_lib_path : str, project_resources_path: str):

    

    python_lib_available = isdir(python_lib_path)

    if(not python_lib_available):
        raise FileNotFoundError(f'Could not copy pyfmu library to the project, directory containing library was not found at {python_lib_path}.')

    project_lib_path = join(project_resources_path, basename(python_lib_path))

    try:
        copytree(python_lib_path, project_lib_path)
    except Exception as e:
        raise RuntimeError("pyfmu library exists but could not be copied the generated project.") from e




def create_project(working_dir: str, project_path: str, main_class_name: str, overwrite = True):

    if(overwrite and exists(project_path)):
        rmtree(project_path)
    

    builder_template_path = join(working_dir, "resources",
                         "templates", "fmu.py.j2")
    builder_pylib_path = join(working_dir,"libs","pyfmu")

    main_script_name = main_class_name.lower() + ".py"
    project_config_path = join(project_path,"project.json")
    project_resource_path = join(project_path, "resources")
    project_main_script_path = join(project_resource_path, main_script_name)    
    
    _generate_fmu_template(builder_template_path, main_class_name, project_main_script_path)


    _copy_python_library_to_sources(builder_pylib_path, project_resource_path)

    _create_config(project_config_path, main_class_name, main_script_name)

