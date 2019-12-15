from os.path import join, dirname


from ..examples.example_finder import get_example_project

from pybuilder.libs.builder.validate import validate
from pybuilder.libs.builder.export import export_project


def test_validation(tmp_path):
    p = get_example_project('SineGenerator')
    
    outdir = join(dirname(tmp_path),'SineGenerator')

    export_project(p,outdir,store_compressed=False)

    is_valid = validate(outdir)

    assert(is_valid)