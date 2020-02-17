from enum import Enum
from pathlib import Path

class BuilderResources(Enum):
    """Enum defining the resources available to the builder.
    """
    vdmcheck2_dir = "vdmcheck2_dir"
    vdmcheck2_ps = "vdmcheck_ps"
    vdmcheck2_sh = "vdmcheck_sh"

    vdmcheck3_dir = "vdmcheck3_dir"
    vdmcheck3_ps = "vdmcheck3_ps"
    vdmcheck3_sh = "vdmcheck3_sh"
    
    pyfmu = "pyfmu"


_resources = {}

def _register_resource(resource : BuilderResources, path: Path):

    if(True not in {path.is_file(), path.is_dir()}):
        raise ValueError("Unable to register resource, the path points to neither file nor directory.")

    _resources[resource] = path

def _init_resources():

    basepath = Path(__file__).parent

    _register_resource(
        BuilderResources.vdmcheck2_dir,
        basepath / 'validation' / 'vdmcheck-0.0.2'
        )

    _register_resource(
        BuilderResources.vdmcheck2_ps,
        get_resource(BuilderResources.vdmcheck2_dir) / 'VDMCheck2.ps1'
    )

    _register_resource(
        BuilderResources.vdmcheck2_sh,
        get_resource(BuilderResources.vdmcheck2_dir) / 'VDMCheck2.sh'
    )

    _register_resource(
        BuilderResources.vdmcheck3_dir,
        basepath / 'validation' / 'vdmcheck-0.0.3'
        )

    _register_resource(
        BuilderResources.vdmcheck3_ps,
        get_resource(BuilderResources.vdmcheck3_dir) / 'VDMCheck3.ps1'
    )

    _register_resource(
        BuilderResources.vdmcheck3_sh,
        get_resource(BuilderResources.vdmcheck3_dir) / 'VDMCheck3.sh'
    )



def get_resource(resource : BuilderResources):
    """Returns paths to various resources used by the builder
    
    Arguments:
        resource {BuilderResources} -- the resource to locate
    
    Raises:
        ValueError: raised if resource is not located
    
    Returns:
        [Path] -- Path object representing the resource
    """
    
    if(resource in _resources):
        return _resources.get(resource)

    else:
        raise ValueError(f"Unable to locate resource specified resource, the specified resource: {resource} is not recognized.")


if(_resources == {}):
    _init_resources()