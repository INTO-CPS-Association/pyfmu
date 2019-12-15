from os.path import dirname, join

def get_example_project(name : str):
    """ Gets the path to a specific example project, to get an fmu use get_example_fmu(...)
    """
    projects_dir = join(dirname(__file__),"examples","projects")

    if(name.lower() == "adder"):
        return join(projects_dir,"Adder")

    else:
        raise RuntimeError(f'no example fmu matching the specified')


