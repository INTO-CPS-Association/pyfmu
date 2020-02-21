from os.path import join, exists, isdir, isfile
import os
import json
from tempfile import TemporaryDirectory
from pathlib import Path

from pybuilder.libs.builder.generate import create_project

class TestGenerate():
    
    def test_generate_mainScriptTemplateAdded(self,tmpdir):
        
        p = create_project(tmpdir,'Adder')

        assert p.main_script == 'adder.py'
        assert p.main_class == 'Adder'
        assert p.main_script_path == p.root / 'resources' / 'adder.py'


    def test_generate_libAdded(self,tmpdir):
        p = create_project(tmpdir,'Adder')

        assert p.pyfmu_dir.is_dir()
        assert (p.pyfmu_dir / 'fmi2slave.py').is_file()
        assert (p.pyfmu_dir / 'fmi2types.py').is_file()
        assert (p.pyfmu_dir / 'fmi2validation.py').is_file()
        assert (p.pyfmu_dir / 'fmi2variables.py').is_file()

    def test_generate_configurationAdded(self,tmpdir):
        p = create_project(tmpdir,'Adder')

        assert p.project_configuration_path.is_file()
        
        with open(p.project_configuration_path,'r') as f:
            c = json.load(f)
            assert c['main_class'] == 'Adder'
            assert c['main_script'] == 'adder.py'

    
        
        

    
    
def test_generate(tmp_path):
    
    create_project(tmp_path,"Adder")


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

