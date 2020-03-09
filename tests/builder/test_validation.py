from os.path import join, dirname

from ..examples.example_finder import get_example_project, get_available_examples, ExampleArchive

from pybuilder.builder.validate import validate, validate_modelDescription


from fmpy import simulate_fmu


def test_validate_md_VDMCheck(tmpdir):
    
    for pname in get_available_examples():
        
        with ExampleArchive(pname) as archive:
            results = validate_modelDescription(archive.model_description, use_vdmcheck=True)
            assert(results.valid == True)
        