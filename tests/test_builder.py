import json
import os
from os.path import exists, isdir, isfile, join
from pathlib import Path
from tempfile import TemporaryDirectory

import lxml.etree as ET
import pytest

from pyfmu.builder import validate_fmu
from pyfmu.builder.export import export_project
from pyfmu.builder.generate import generate_project

from .utils import ExampleArchive, get_all_examples, get_example_project


class TestGenerate:
    def test_returnsProject_pathsAreCorrect(self, tmpdir):

        tmpdir = Path(tmpdir)

        outdir = tmpdir / "Adder"
        p = generate_project(outdir, "Adder")

        assert (outdir / "project.json").is_file()
        assert (outdir / "resources" / "adder.py").is_file()


class TestExport:
    def test_export(self, tmpdir):

        output_path = Path(tmpdir) / "Adder"

        project = get_example_project("Adder")

        export_project(project_or_path=project, output_path=output_path, compress=False)

        assert (output_path / "modelDescription.xml").is_file()
        assert (output_path / "binaries" / "win64" / "pyfmu.dll").is_file()
        assert (output_path / "binaries" / "linux64" / "pyfmu.so").is_file()
        assert (output_path / "resources" / "Adder.py").is_file()
