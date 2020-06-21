from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location


import pytest

from pyfmu.builder.export import export_project
from pyfmu.builder.generate import generate_project

from .utils import get_example_project


class TestGenerate:
    def test_returnsProject_pathsAreCorrect(self, tmpdir):

        tmpdir = Path(tmpdir)

        slave_class = "Adder"
        outdir = tmpdir / "slave_class"
        generate_project(output_path=outdir, slave_class=slave_class)

        resources_dir = outdir / "resources"
        slave_script = resources_dir / "adder.py"

        assert (outdir / "project.json").is_file()
        assert slave_script.is_file()

        spec = spec_from_file_location(name="Adder", location=slave_script)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        slave = getattr(module, "Adder")()

        slave.a = 10
        slave.b = 20


class TestExport:
    def test_export(self, tmpdir):

        output_path = Path(tmpdir) / "Adder"

        project = get_example_project("Adder")

        export_project(project_or_path=project, output_path=output_path, compress=False)

        assert (output_path / "modelDescription.xml").is_file()
        assert (output_path / "binaries" / "win64" / "pyfmu.dll").is_file()
        assert (output_path / "binaries" / "linux64" / "pyfmu.so").is_file()
        assert (output_path / "resources" / "Adder.py").is_file()
