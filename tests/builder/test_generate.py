from os.path import join, exists, isdir, isfile
import os
import json

from pybuilder.libs.builder.generate import create_project

def test_generate(tmp_path):
    
    working_dir = os.getcwd()
    create_project(working_dir,tmp_path,"Adder")


    main_script_path = join(tmp_path,'resources','adder.py')
    lib_pyfmu_path = join(tmp_path,'resources','pyfmu')
    config_path = join(tmp_path,'project.json')


    main_script_ok = isfile(main_script_path)
    lib_pyfmu_ok = isdir(lib_pyfmu_path)
    config_ok = isfile(config_path)

    assert(main_script_ok)
    assert(lib_pyfmu_ok)
    assert(config_ok)

    main_class = None
    main_script = None

    with open(config_path,'r') as f:
        c = json.load(f)
        main_class = c['main_class']
        main_script = c['main_script']

    assert(main_class == 'Adder')
    assert(main_script == 'adder.py')

