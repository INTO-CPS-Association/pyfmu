import argparse
import sys
from os.path import join, dirname, realpath, normpath
import logging

logger = logging.getLogger(__file__)

from pyfmu.builder.generate import generate_project
from pyfmu.builder.export import export_project
from pyfmu.builder.validate import validate_fmu


def config_generate_subprogram(subparsers: argparse.ArgumentParser) -> None:
    parser_gen = subparsers.add_parser("generate", help="Generate a new project.",)

    parser_gen.add_argument(
        "--name",
        "-n",
        type=str,
        required=False,
        help="Name of the project to be generated.",
    )

    parser_gen.add_argument(
        "--output",
        "-o",
        type=str,
        help="Path to which the generated project is written.",
    )


def config_export_subprogram(subparsers: argparse.ArgumentParser) -> None:
    parser_export = subparsers.add_parser("export", help="Export project as FMU.",)

    parser_export.add_argument(
        "--project", "-p", required=True, help="path to Python project"
    )

    parser_export.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to which the exported archive is written",
    )

    parser_export.add_argument(
        "--overwrite",
        "-ow",
        action="store_true",
        help="allow overwriting of existing files",
    )


def config_validate_subprogram(subparsers: argparse.ArgumentParser) -> None:

    parser_validate = subparsers.add_parser(
        "validate", help="Static and functional verification of FMU."
    )
    parser_validate.add_argument(
        "fmu",
        help="Path to the FMU. This may either be an zip archive or an uncompressed version of the archive",
    )
    parser_validate.add_argument(
        "--fmpy", action="store_true", help="validate the fmu using fmpy"
    )
    parser_validate.add_argument(
        "--vdmcheck", action="store_true", help="validate the fmu using vdmcheck"
    )


def handle_generate(args):

    from os.path import join, curdir, basename, normpath

    if args.file is not None:
        raise Exception("Currently generation from file is not supported")

    project_path = join(curdir, args.path)

    main_class_name = (
        args.name if args.name is not None else basename(normpath(project_path))
    )

    generate_project(project_path, main_class_name)


def handle_export(args):

    project_path = args.project

    archive_path = args.output

    export_project(project_path, archive_path, compress=False)


def handle_validate(args):

    fmu = args.fmu
    raise NotImplementedError("TODO Parse arguments related to validation tools")
    validate_fmu(fmu)


def main():

    try:

        description_text = """Create Python based Functional Mock-up Units (FMUs).
The program provides several commands, each related to a specific part of the workflow.
Use the '--help' argument to see the uses of each command.
        """

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=description_text,
        )

        # general arguments
        parser.add_argument(
            "--log-level",
            dest="log_level",
            default="info",
            choices=["trace", "debug", "info", "warning", "error", "critical"],
            help="defines the verbosity of the output",
        )

        # subcommands
        subparsers = parser.add_subparsers(dest="subprogram", required=True)

        config_generate_subprogram(subparsers)
        config_export_subprogram(subparsers)
        config_validate_subprogram(subparsers)

        args = parser.parse_args()

        logging.basicConfig(level=args.log_level.upper())

        if args.subprogram == "generate":
            handle_generate(args)
        elif args.subprogram == "export":
            handle_export(args)
        elif args.subprogram == "validate":
            handle_validate(args)
        else:
            raise Exception("Not implemented")

    except Exception:
        logger.critical("Program failed due to an unhandled exception", exc_info=True)
        exit(1)

