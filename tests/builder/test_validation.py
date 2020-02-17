from os.path import join, dirname

from ..examples.example_finder import get_example_project, get_available_examples

from pybuilder.libs.builder.validate import validate, validate_modelDescription
from pybuilder.libs.builder.export import export_project

from fmpy import simulate_fmu

def test_validate_md_VDMCheck(tmpdir):
    
    for pname in get_available_examples():
        p = get_example_project(pname)    
        outdir = tmpdir / pname
        archive = export_project(p,outdir, store_compressed=False)

        results = validate_modelDescription(archive.model_description, use_vdmcheck=True)

        assert(results.valid == True)
    