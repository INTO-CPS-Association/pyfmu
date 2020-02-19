from os.path import dirname, join
from tempfile import mkdtemp
from shutil import rmtree
from pathlib import Path


from pybuilder.libs.builder.export import export_project, PyfmuArchive

def get_available_examples():
    """Returns the set of available examples.
    
    Returns:
        [Set] -- The set of available examples
    """
    return {
        'Adder',
        'ConstantSignalGenerator',
        'SineGenerator'
    }

def get_example_project(name: str):
    """ Gets the path to a specific example project, to get an fmu use get_example_fmu(...)
    """
    projects_dir = join(dirname(__file__),"projects")
    return join(projects_dir,name)



def get_exported_example_project(name : str):
    """ Gets the path to a specific example project, to get an fmu use get_example_fmu(...)
    """
    projects_dir = join(dirname(__file__),"export")
    return join(projects_dir,name)

class ExampleProject():
    """Wrapper that encapsulates the exporting of example projects used for automatic testing.

    This allows them to be accessed using a with statements.
    Attributes such as the path to the object can be accessed through the archive object which is returned.
    ```
    with ExampleProject('Adder') as p:
        print(p.modelDescription)
        ...
    ```

    The example project is exported as an FMU to a temporary folder, which is automatically freed after the with statement terminates.   
    """
    def __init__(self, project_name : str):
        
        p = get_example_project(project_name)

        self.tmpdir = mkdtemp()

        outdir = Path(self.tmpdir) / project_name

        self.archive = export_project(p,outdir, store_compressed=False)

    def __enter__(self) -> PyfmuArchive:
        return self.archive

    def __exit__(self, exception_type, exception_value, traceback):
        rmtree(self.tmpdir)