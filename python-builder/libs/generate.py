"""
This module contains functionality to the creation of Python FMU projects
"""
from os import makedirs
from os.path import join, curdir, realpath, dirname
from shutil import copy
from jinja2 import Template


def _create_dirs(project_path: str, exist_ok: bool = True):
    source_path = join(project_path, "source")

    try:
        makedirs(project_path, exist_ok=True)
        makedirs(source_path, exist_ok=True)
    except OSError:
        raise Exception(
            "Project with identical name already exists in that location. Please specify a new name, another directory or remove the old project.")
    except Exception as e:
        raise Exception("Failed to create directories for the Python project")

def _generate_fmu_template(project_path: str, source_path: str, template_path: str, main_class_name: str):

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

    python_fmu_path = join(source_path, main_class_name + ".py")

    with open(python_fmu_path, 'w') as f:
        f.write(r)

def _copy_python_library_to_sources(python_lib_path : str, source_path: str):
    
    python_script_path = join(python_lib_path, "fmi2slave.py")

    copy(python_script_path,source_path)

def create_project(project_path: str, main_class_name: str):

    cur_dir = dirname(realpath(__file__))

    template_path = join(cur_dir, "resources",
                         "templates", "fmu.py.j2")

    source_path = join(project_path, "source")

    python_lib_path = join(cur_dir,"resources","scripts")
    
    
    _create_dirs(project_path)

    _generate_fmu_template(project_path, source_path,
                           template_path, main_class_name)


    _copy_python_library_to_sources(python_lib_path, source_path)
