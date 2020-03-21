from pathlib import Path

import pytest

from pyfmu.builder.export import PyfmuProject, PyfmuArchive
from pyfmu.tests import get_example_project, ExampleArchive, get_all_examples


def get_empty_archive(root: Path) -> PyfmuArchive:
    return PyfmuArchive(root, "")


def get_empty_project(root: Path) -> PyfmuProject:
    return PyfmuProject(root, None, None)


def test_sourcesCopied():

    with ExampleArchive('Adder') as a:
        sources_copied = a.main_script_path.is_file()

        assert sources_copied


def test_binariesCopied():
    with ExampleArchive('Adder') as a:

        assert a.binaries_dir.is_dir()
        assert (a.binaries_dir / 'win64' / 'pyfmu.dll').is_file()
        assert (a.binaries_dir / 'linux64' / 'pyfmu.so').is_file()


def test_slaveConfigurationGenerated():
    with ExampleArchive('Adder') as a:
        slaveConfiguration_generated = a.slave_configuration_path.is_file()

        assert slaveConfiguration_generated


def test_modelDescriptionGenerated():

    with ExampleArchive('Adder') as a:
        assert a.model_description is not None
        assert a.model_description_path.is_file()


def test_export_multipleInRow_modelDescriptionCorrect():

    fnames = get_all_examples()
    mds = []
    for f in fnames:
        with ExampleArchive(f) as a:
            assert a.model_description_path.is_file()
            mds.append(a.model_description)


def test_fromExisting_projectExists_OK():

    p = get_example_project('Adder')

    project = PyfmuProject.from_existing(p)

    assert project.root == p
    assert project.main_class == 'Adder'
    assert project.main_script == 'adder.py'


def test_fromExisting_emptyDirectory_Throws(tmpdir):

    with pytest.raises(ValueError):
        PyfmuProject.from_existing(tmpdir)
