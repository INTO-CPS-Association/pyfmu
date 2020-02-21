from os.path import join, basename, isdir, isfile, realpath
import os
from pathlib import Path
from tempfile import TemporaryDirectory


from pybuilder.libs.builder.export import export_project, PyfmuProject, PyfmuArchive, _copy_pyfmu_lib_to_archive, _copy_sources_to_archive
from pybuilder.libs.builder.generate import create_project, PyfmuProject

import pytest

from ..examples.example_finder import get_example_project, ExampleProject, ExampleArchive

def get_empty_archive(root : Path) -> PyfmuArchive:
    return PyfmuArchive(root,"")

def get_empty_project(root: Path) -> PyfmuProject:
    return PyfmuProject(root,None,None)

def test_export(tmp_path_factory):


    project_dir = tmp_path_factory.mktemp('project')
    archive_dir = tmp_path_factory.mktemp('archive')

    create_project(project_dir,'Adder')
    export_project(project_dir,archive_dir)

    # resources
    main_script_path = join(archive_dir,'resources','adder.py')
    md_path = join(archive_dir,'modelDescription.xml')
    pylib_dir = join(archive_dir,'resources','pyfmu')
    config_path = join(archive_dir,'resources','slave_configuration.json')


    # binary directories for different platforms
    binaries_path = join(archive_dir,'binaries')
    binaries_win64_path = join(binaries_path,'win64','libpyfmu.dll')
    binaries_linux64_path = join(binaries_path,'linux64','libpyfmu.so')
    

    assert(isfile(binaries_win64_path))
    assert(isfile(binaries_linux64_path))
    assert(isfile(main_script_path))
    assert(isfile(md_path))
    assert(isdir(pylib_dir))
    assert(isfile(config_path))


class TestExport():
    
    def test_export_validProject_sourcesCopied(self):
        
        with ExampleArchive('Adder') as a:
            sources_copied = a.main_script_path.is_file()

            assert sources_copied

    def test_export_validProject_binariesCopied(self):
        with ExampleArchive('Adder') as a:


            assert a.binaries_dir.is_dir()
            assert (a.binaries_dir / 'win64' / 'libpyfmu.dll').is_file()
            assert (a.binaries_dir / 'linux64' / 'libpyfmu.so').is_file()

    def test_export_validProject_libCopied(self):
        with ExampleArchive('Adder') as a:

            assert a.pyfmu_dir.is_dir()
            assert (a.pyfmu_dir / 'fmi2slave.py').is_file()
            assert (a.pyfmu_dir / 'fmi2types.py').is_file()
            assert (a.pyfmu_dir / 'fmi2validation.py').is_file()
            assert (a.pyfmu_dir / 'fmi2variables.py').is_file()

    def test_export_validProject_slaveConfigurationGenerated(self):
        with ExampleArchive('Adder') as a:
            slaveConfiguration_generated = a.slave_configuration_path.is_file()

            assert slaveConfiguration_generated

            

    def test_export_validProject_modelDescriptionGenerated(self):

        with ExampleArchive('Adder') as a:
            assert a.model_description != None
            assert a.model_description_path.is_file()
        


class TestCopyPyfmuLibToArchive:
    """Tests related to how the pyfmu library is copied into the exported FMUs.
    """
    def test_copyFromResources_copiedToArchive(self,tmpdir):
        

        a = get_empty_archive(tmpdir)
        
        _copy_pyfmu_lib_to_archive(a)

        pyfmu_folder_exists = (Path(tmpdir) / 'resources' / 'pyfmu').is_dir()

        assert pyfmu_folder_exists

    def test_copyFromPoject_projectExists_copiedToArchive(self,tmpdir):
        
        a = get_empty_archive(Path(tmpdir))

        with ExampleProject('Adder') as p:
            _copy_pyfmu_lib_to_archive(a,p)

        pyfmu_folder_exists = (a.root / 'resources' / 'pyfmu').is_dir()

        assert pyfmu_folder_exists

    def test_copyFromPoject_projectDoesNotExist_throws(self):
        
        with TemporaryDirectory() as tmpdir_p, TemporaryDirectory() as tmpdir_a:
            p = get_empty_project(Path(tmpdir_p))
            a = get_empty_archive(Path(tmpdir_a))
                          

            with pytest.raises(RuntimeError):
                _copy_pyfmu_lib_to_archive(a,p)
      

class TestPyfmuProject():
    
    def test_fromExisting_projectExists_OK(self):
        
        p = get_example_project('Adder')

        project = PyfmuProject.from_existing(p)

        assert project.root == p
        assert project.main_class == 'Adder'
        assert project.main_script == 'adder.py'
    
    def test_fromExisting_emptyDirectory_Throws(self,tmpdir):

        with pytest.raises(ValueError):
            _ = PyfmuProject.from_existing(tmpdir)
