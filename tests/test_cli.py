from pathlib import Path
import subprocess


def test_generate(tmpdir):
    tmpdir = Path(tmpdir)

    output_path = str((tmpdir / "MyFMU").absolute())

    assert subprocess.run(["pyfmu", "generate", "--name", "MyFMU"]).returncode != 0
    assert (
        subprocess.run(
            ["pyfmu", "generate", "--name", "MyFMU", "--output", output_path]
        ).returncode
        == 0
    )


def test_export(tmpdir):
    tmpdir = Path(tmpdir)

    project_path = str((tmpdir / "MyFMU").absolute())
    export_path = str((tmpdir / "MyFMU_Exported").absolute())

    assert (
        subprocess.run(
            ["pyfmu", "generate", "--name", "MyFMU", "--output", project_path]
        ).returncode
        == 0
    )

    assert (
        subprocess.run(
            ["pyfmu", "export", "--project", project_path, "--output", export_path]
        ).returncode
        == 0
    )

