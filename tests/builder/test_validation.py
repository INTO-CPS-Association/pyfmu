from os.path import join, dirname

from ..examples.example_finder import get_example_project, get_available_examples

from pybuilder.libs.builder.validate import validate, validate_modelDescription
from pybuilder.libs.builder.export import export_project

def vdmcheck_no_errors(results):
    """ Returns true if VDMCheck finds has found no errors.
    """
    return results.stdout == b'No errors found.\n'

def test_validation(tmp_path):
    p = get_example_project('SineGenerator')
    
    outdir = join(dirname(tmp_path),'SineGenerator')

    export_project(p,outdir,store_compressed=False)

    is_valid = validate(outdir)

    assert(is_valid == None)

def test_validate_vdmcheck(tmpdir):
    
    for pname in get_available_examples():
        p = get_example_project(pname)    
        outdir = tmpdir / pname
        archive = export_project(p,outdir, store_compressed=False)
        results = validate_modelDescription(archive.model_description, use_vdmcheck=True)
        assert(vdmcheck_no_errors(results['VDMCheck']))

    
    

    