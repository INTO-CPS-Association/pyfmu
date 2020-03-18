from os.path import join, exists, isdir, isfile
import os
import json
from tempfile import TemporaryDirectory
from pathlib import Path

from pyfmu.builder.generate import create_project


class TestGenerate():

    def test_returnsProject_pathsAreCorrect(self, tmpdir):

        tmpdir = Path(tmpdir)

        p = create_project(tmpdir, 'Adder')

        assert p.root.samefile(tmpdir)
        assert p.project_configuration_path.samefile(tmpdir / 'project.json')

    def test_generate_mainScriptTemplateAdded(self, tmpdir):

        p = create_project(tmpdir, 'Adder')

        assert p.main_script == 'adder.py'
        assert p.main_class == 'Adder'
        assert p.main_script_path == p.root / 'resources' / 'adder.py'


    def test_generate_configurationAdded(self, tmpdir):
        p = create_project(tmpdir, 'Adder')

        assert p.project_configuration_path.is_file()

        with open(p.project_configuration_path, 'r') as f:
            c = json.load(f)
            assert c['main_class'] == 'Adder'
            assert c['main_script'] == 'adder.py'
