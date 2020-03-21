from os.path import join, dirname

from pyfmu.tests import get_example_project, get_all_examples, ExampleArchive
from pyfmu.builder import validate, validate_modelDescription
from fmpy import simulate_fmu


def test_validate_md_VDMCheck(tmpdir):

    for pname in get_all_examples():

        with ExampleArchive(pname) as archive:
            results = validate_modelDescription(
                archive.model_description, use_vdmcheck=True)
            assert(results.valid == True)
