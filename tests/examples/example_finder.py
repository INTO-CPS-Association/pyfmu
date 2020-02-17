from os.path import dirname, join

def get_available_examples():
    """Returns the set of available examples.
    
    Returns:
        [Set] -- The set of available examples
    """
    return {
        'Adder',
        'Constant'
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
