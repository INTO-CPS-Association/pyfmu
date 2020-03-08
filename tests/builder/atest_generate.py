from os.path import join, exists, isdir, isfile
import os
import json
from tempfile import TemporaryDirectory
from pathlib import Path

from pybuilder.builder.generate import create_project

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