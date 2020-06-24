import subprocess

from pyfmu.resources import Resources

from .utils import MaestroExample


def test_BicycleDynamicAndDriver():

    jar_path = Resources.get().VDMCheck2_jar

    with MaestroExample("BicycleDynamicAndDriver") as config:
        results = subprocess.run(
            [
                "java",
                "-jar",
                jar_path,
                "-v",
                "--configuration",
                str(config),
                "--onshot",
                "--starttime",
                "0.0",
                "--endtime",
                "10.0",
            ]
        )

