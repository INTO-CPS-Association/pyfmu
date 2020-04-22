from os import makedirs
from pathlib import Path

from pyfmu.builder.utils import compress


class TestCompress:
    def test_explicitly_defined_output(self, tmpdir):

        tmpdir = Path(tmpdir)

        input_directory = tmpdir / "mydir"

        makedirs(input_directory)
        with open(input_directory / "test.txt", "w+") as f:
            f.write("hello world!")

        # absolute path, extension should be inferred
        outdir = tmpdir / "archive_0"
        compress(input_directory, outdir)
        assert (tmpdir / "archive_0.zip").is_file()

        compress(input_directory, tmpdir / "archive_1", extension="fmu")
        assert (tmpdir / "archive_1.fmu").is_file()

    def test_default_output_directory(self, tmpdir):

        tmpdir = Path(tmpdir)

        with open(tmpdir / "test.txt", "w") as f:
            f.write("hello world!")

        compress(tmpdir, format="zip")

        tmpdir_parent = tmpdir.parent
        expected_archive_path = tmpdir_parent / f"{tmpdir.name}.zip"

        assert expected_archive_path.is_file()
        assert expected_archive_path.suffix == ".zip"

    def test_points_to_archive(self, tmpdir):

        input_directory = Path(tmpdir) / "mydir"

        makedirs(input_directory)
        with open(input_directory / "test.txt", "w") as f:
            f.write("hello world!")

        actual_path = compress(input_directory)

        expected_path = Path(tmpdir) / "mydir.zip"

        assert actual_path.samefile(expected_path)
