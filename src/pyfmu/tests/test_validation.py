from pyfmu.tests import get_all_examples, ExampleArchive
from pyfmu.builder import validate_fmu


def test_validate_VDMCheck(tmpdir):

    for pname in get_all_examples():

        with ExampleArchive(pname) as archive:

            results = validate_fmu(archive.root, use_vdmcheck=True)

            assert results.valid is True


def test_validate_fmuCheck():
    for pname in get_all_examples():

        with ExampleArchive(pname) as archive:

            results = validate_fmu(archive.root, use_fmucheck=True)

            assert results.valid is True
