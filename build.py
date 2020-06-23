"""Script for building the C++ code and copying it to the resources
"""
import argparse
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from shutil import copy

from tqdm import tqdm

from tests.utils.example_finder import (
    get_all_examples,
    get_example_directory,
    get_example_project,
)
from pyfmu.builder import export_project
from pyfmu.resources import Resources


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__file__)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Script to ease the process of build the wrapper and updating the resources of PyFMU"
    )

    parser.add_argument(
        "--update_wrapper",
        "-u",
        action="store_true",
        help="Overwrite the existing wrapper library with the newly built one.",
    )

    parser.add_argument(
        "--export_examples",
        "-e",
        action="store_true",
        help="Exports all example projects as FMUs with the built wrapper.",
    )

    parser.add_argument(
        "--rust-tests",
        action="store_true",
        dest="rust_tests",
        help="Run rust tests using cargo",
    )

    parser.add_argument(
        "--python-tests",
        action="store_true",
        dest="python_tests",
        help="Run integration tests in Python",
    )

    args = parser.parse_args()

    root_dir = Path(__file__).parent.absolute()
    wrapper_dir = root_dir / "pyfmu_wrapper"

    if args.update_wrapper:


        logger.info(f"Building wrapper using cargo, changing directory to {wrapper_dir}.")
        os.chdir(wrapper_dir)
        logger.info("Invoking cargo build")
        res = subprocess.run(["cargo", "build"]).check_returncode()
        logger.info(f"Changing directory back to {root_dir}")
        os.chdir(root_dir)

        sys = platform.system()
        sys_fmi = {"Windows": "win", "Linux": "linux", "Darwin": "darwin"}[sys]

        # arch will be either "32bit" or "64bit", take either 32 or 64
        arch = (platform.architecture())[0][:2]

        # merge parts to form: windows64, linux64
        identifier = (sys_fmi + arch).lower()

        # TODO
        binary_in_name = "pyfmu.dll" if sys == "Windows" else "libpyfmu.so"
        binary_name_out = binary_in_name if sys == "Windows" else "pyfmu.so"
        input_dir = root_dir / "pyfmu_wrapper" / "target" / "debug" / binary_in_name
        output_dir = Resources.get().binaries_dir / identifier / binary_name_out
        logger.info(
            f"wrapper sucessfully build, copying binaries form {input_dir} into resources {output_dir}"
        )

        copy(input_dir, output_dir)

    if args.export_examples:
        logger.info("Exporting example projects")

        for example in [get_example_project(name) for name in get_all_examples()]:
            export_project(
                project_or_path=example,
                output_path=root_dir / "examples" / "exported" / example.stem,
                compress=False,
                overwrite=True,
            )

    if args.rust_tests:
        os.chdir(wrapper_dir)
        logger.info("Running rust tests")
        subprocess.run(
            ["cargo", "test", "--", "--nocapture", "--test-threads=1"]
        ).check_returncode()
        os.chdir(root_dir)

    if args.python_tests:
        logger.info("Executing python integration test suite")
        subprocess.run(["pytest"]).check_returncode()

