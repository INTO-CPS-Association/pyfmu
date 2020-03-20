import os
from os.path import dirname, join
from tempfile import mkdtemp
from shutil import rmtree, copytree
from pathlib import Path
import stat


from pyfmu.builder.export import export_project, PyfmuProject, PyfmuArchive



_correct_example = {
    'Adder',
    'ConstantSignalGenerator',
    'SineGenerator',
    'LoggerFMU',
    "BicycleKinematic",
    "LivePlotting"
}

_incorrect_examples = {
    'NoneReturner'
}


def get_example_directory() -> Path:
    """
    Returns the path to the example projects
    """
    p = Path(__file__).parent.parent.parent.parent / 'examples' / 'projects'
    if(not p.is_dir()):
        raise FileNotFoundError('Expected example directory : {p} does not appear to exist. Ensure the directory exists at the specified path or update this function.')
    
    return p 

def get_incorrect_examples():
    """Returns the set of examples that are expected to fail

    Returns:
        [Set] -- The set of all examples which are designed to cause faults.
    """

    return _incorrect_examples

def get_correct_examples():
    """Returns the set of examples that are expected to work correctly.

    Returns:
        [Set] -- The set of all examples which should function correctly.
    """
    return _correct_example

def get_all_examples():
    """Returns the set of all available examples including the ones that are expected to fail.

    Returns:
        [Set] -- The set of all available examples
    """
    return get_correct_examples() | get_incorrect_examples()



def get_example_project(name: str) -> Path:
    """ Gets the path to a specific example project, to get an fmu use get_example_fmu(...)
    """
    if(name not in get_all_examples()):
        raise ValueError(
            f'Failed to resolve the path to the example project. The project {name} does not exist.')

    p = get_example_directory() / name

    return p


def get_exported_example_project(name: str):
    """ Gets the path to a specific example project, to get an fmu use get_example_fmu(...)
    """
    projects_dir = join(dirname(__file__), "export")
    return join(projects_dir, name)


class ExampleProject():
    """Wrapper that encapsulates the creation of example projects used for automatic testing.

    Wrapper that encapsulates the exporting of example archives used for automatic testing.

    This allows them to be accessed using a with statements.
    Attributes such as the path to the object can be accessed through the archive object which is returned.
    ```
    with ExampleProject('Adder') as p:
        print(p.modelDescription)
        ...
    ```

    The example project generated as a copy of an example project inside a temporary folder, which is freed after the with statement terminates.   
    Modifications of properties such as its model description can be made through its properties:
    ```
    with ExampleProject('Adder') as p:
        p.modelDescription = "invalid model description"
        ...
    ```
    """

    def __init__(self, project_name: str):

        if(project_name not in get_all_examples()):
            raise ValueError(
                f'Unable to read the example project. The specified project {project_name} could not be found.')

        project_path = get_example_project(project_name)

        # copy project to temporary directory
        self.tmpdir = mkdtemp()
        outdir = (Path(self.tmpdir) / project_name)
        copytree(project_path, outdir)

        # instantiate object representation of project
        self.project = PyfmuProject.from_existing(outdir)

    def __enter__(self) -> PyfmuProject:
        return self.project

    def __exit__(self, exception_type, exception_value, traceback):
        rmtree(self.tmpdir)


class ExampleArchive():
    """Wrapper that encapsulates the exporting of example archives used for automatic testing.

    This allows them to be accessed using a with statements.
    Attributes such as the path to the object can be accessed through the archive object which is returned.
    ```
    with ExampleArchive('Adder') as p:
        print(p.modelDescription)
        ...
    ```

    The example project is exported as an FMU to a temporary folder, which is automatically freed after the with statement terminates.   
    """

    def __init__(self, project_name: str):

        self.tmpdir = mkdtemp()

        outdir = Path(self.tmpdir) / project_name

        with ExampleProject(project_name) as p:
            self.archive = export_project(p, outdir, store_compressed=False)

    def __enter__(self) -> PyfmuArchive:
        return self.archive

    def __exit__(self, exception_type, exception_value, traceback):

        import platform

        # TODO
        # Currently the clean up mechanism does not work with FMPy on windows
        # It seems like the dll is still loaded when the function is called, resulting in a windows "access denied" error when trying to delete it.
        if(platform.system() == "Windows"):
            return

        for root, dirs, files in os.walk(self.tmpdir, topdown=False):
            for name in files:
                filename = os.path.join(root, name)
                os.chmod(filename, stat.S_IWUSR)
                os.remove(filename)
            for name in dirs:
                os.rmdir(os.path.join(root, name))
