import argparse
import sys
from os.path import join, dirname, realpath, normpath

from pyfmu.builder.generate import create_project
from pyfmu.builder.export import export_project
from pyfmu.builder.validate import validate


def config_generate_subprogram(subparsers: argparse.ArgumentParser) -> None:
    parser_gen = subparsers.add_parser(
        'generate', help="Generate new Python projects from scratch or based on existing resources such as Model Descriptions and reference FMUs.")

    file_project_group = parser_gen.add_mutually_exclusive_group(required=True)

    file_project_group.add_argument(
        '--path', '-p', type=str, help="Path to the project that will be generated")

    file_project_group.add_argument(
        '--file', '-f', type=str, help="Path to either a model description file or a FMU archive")

    parser_gen.add_argument(
        '--name', '-n', type=str, required=False, help="Name of the project to be generated. If not specified this information will be extracted from either the path or a model description")


def config_export_subprogram(subparsers: argparse.ArgumentParser) -> None:
    parser_export = subparsers.add_parser(
        'export',
        help="Export Python projects as FMUs",
    )

    parser_export.add_argument(
        "--project", "-p", required=True, help="path to Python project")

    parser_export.add_argument(
        "--output", '-o', required=True, help="output path of the exported archive")

    parser_export.add_argument(
        '--overwrite', '-ow', action='store_true', help='allow overwriting of existing files')

    group_bundle = parser_export.add_argument_group('bundle')

    help_bundle_interpreter = """Bundle a Python Interpreter in the FMU. 
    This will allow standalone execution on platforms where a suitable Python interpreter is not available, at the cost of an increase in archive size.
    Note that a interpreter is bundled for each supported platform.
    """
    group_bundle.add_argument(
        "-bi", type=bool, default=False, help=help_bundle_interpreter)

    help_bundle_libs = """Bundle current Python environment Libraries in the FMU. 
    """
    group_bundle.add_argument(
        "-bl", type=bool, default=True, help=help_bundle_libs)

    help_prune_libs = """ Decrease size of the included libraries by only including those used by the FMU.
    Note that this relies on analyzing static analysis of the Python files and may fail to discover all dependencies.
    """
    group_bundle.add_argument(
        "-bp", type=bool, default=False, help=help_prune_libs)


def config_validate_subprogram(subparsers: argparse.ArgumentParser) -> None:

    parser_validate = subparsers.add_parser(
        'validate', help="Static and functional verification of fmu archives")
    parser_validate.add_argument(
        'fmu', help='Path to the FMU. This may either be an zip archive or an uncompressed version of the archive')
    parser_validate.add_argument(
        '--fmpy', action='store_true', help='validate the fmu using fmpy')
    parser_validate.add_argument(
        '--vdmcheck', action='store_true', help='validate the fmu using vdmcheck')


def handle_generate(args):

    from os.path import join, curdir, dirname, basename, normpath

    if(args.file is not None):
        raise Exception("Currently generation from file is not supported")

    project_path = join(curdir, args.path)

    main_class_name = args.name if args.name is not None else basename(
        normpath(project_path))

    create_project(project_path, main_class_name)


def handle_export(args):

    project_path = args.project

    archive_path = args.output

    export_project(project_path, archive_path)


def handle_validate(args):

    fmu = args.fmu
    validate(fmu)


def main():

    description_text = """Utility program to facility the development of Functional Mock-up Units (FMUs) using Python code.
    """

    example_text = '''examples:

these are common commands for various situations:

generating a new Python project from scratch
    python py2fmu generate -n engine

generating a new Python project based on a model description file or reference FMU.
    python py2fmu generate -f modelDescription.xml
    python py2fmu generate -f engine.fmu

exporting a Python project as an FMU
    python py2fmu export -p engine
    python py2fmu export -p engine -c MyEngineClass

validating an fmu
    python py2fmu validate engine.fmu --fmpy --vdmcheck --fmicheck

re-configuring an existing project
    python py2fmu configure -p engine --bundle-interpreter
    '''

    parser = argparse.ArgumentParser(
        epilog=example_text, formatter_class=argparse.RawDescriptionHelpFormatter, description=description_text)

    subparsers = parser.add_subparsers(dest="subprogram", required=True)

    config_generate_subprogram(subparsers)
    config_export_subprogram(subparsers)
    config_validate_subprogram(subparsers)

    args = parser.parse_args()

    if(args.subprogram == "generate"):
        handle_generate(args)
    elif(args.subprogram == "export"):
        handle_export(args)
    elif(args.subprogram == 'validate'):
        handle_validate(args)
    else:
        raise Exception("Not implemented")
