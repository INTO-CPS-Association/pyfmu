from libs.builder.export import export_project

from libs.builder.generate import create_project

from os.path import join, basename, isdir, isfile, realpath
import os

def get_multiplier_project():
    pass

def test_export(tmp_path_factory):

    working_dir = os.getcwd()

    project_dir = tmp_path_factory.mktemp('project')
    archive_dir = tmp_path_factory.mktemp('archive')

    create_project(working_dir,project_dir,'Adder')
    export_project(working_dir,project_dir,archive_dir,compress=False)

    # resources
    main_script_path = join(archive_dir,'resources','adder.py')
    pylib_dir = join(archive_dir,'resources','pyfmu')
    config_path = join(archive_dir,'slavemodule.txt')


    # binary directories for different platforms
    binaries_path = join(archive_dir,'binaries')
    binaries_win64_path = join(binaries_path,'win64','libpyfmu.dll')
    binaries_linux64_path = join(binaries_path,'linux64','libpyfmu.so')
    

    assert(isfile(binaries_win64_path))
    assert(isfile(binaries_linux64_path))
    assert(isfile(main_script_path))
    assert(isdir(pylib_dir))
    assert(isfile(config_path))
