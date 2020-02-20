from os.path import join, basename, isdir, isfile, realpath
import os

from pybuilder.libs.builder.export import export_project, PyfmuProject
from pybuilder.libs.builder.generate import create_project


from ..examples.example_finder import get_example_project

def test_export(tmp_path_factory):


    project_dir = tmp_path_factory.mktemp('project')
    archive_dir = tmp_path_factory.mktemp('archive')

    create_project(project_dir,'Adder')
    export_project(project_dir,archive_dir,compress=False)

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


class TestCopyPyfmuLibToArchive:
    def test_copy_from_resources(self):
        assert False

    def test_copy_from_project_archive_present(self):
        assert False

    def test_copy_from_project_archive_not_present(self):
        assert False

class TestPyfmuProject():
    
    def test_from_existing(self):
        
        p = get_example_project('Adder')

        project = PyfmuProject.from_existing(p)

        assert project.root == p
        assert project.main_class == 'Adder'
        assert project.main_script == 'adder.py'
        