from os.path import join, dirname


from ..examples.example_finder import get_example_project

from pybuilder.libs.builder.validate import validate, validate_modelDescription
from pybuilder.libs.builder.export import export_project



def test_validation(tmp_path):
    p = get_example_project('SineGenerator')
    
    outdir = join(dirname(tmp_path),'SineGenerator')

    export_project(p,outdir,store_compressed=False)

    is_valid = validate(outdir)

    assert(is_valid == None)

def test_validate_vdmcheck(tmpdir):
    
    p = get_example_project('SineGenerator')
    
    outdir = tmpdir / 'SineGenerator'

    archive = export_project(p,outdir, store_compressed=False)


    result = validate_modelDescription(archive.model_description, use_vdmcheck=True)

    
    assert(False)