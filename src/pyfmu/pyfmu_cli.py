from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from sys import stdout

import zmq

from pyfmu.builder.export import export_project
from pyfmu.builder.generate import generate_project
from pyfmu.builder.utils import instantiate_slave
from pyfmu.config import (
    auto_configure,
    get_config_path,
    reset_config,
    config_set_val,
    get_configuration,
)
from pyfmu.fmi2.types import Fmi2Status

logger = logging.getLogger(__file__)


# ==================== utility ========================================

# credits https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")


# ==================== setup argparse subcommands ====================


def config_config_subprogram(subparsers, parents) -> None:

    config_parser = subparsers.add_parser(
        "config",
        help="Modify settings used by the FMUs during execution",
        parents=parents,
    )

    config_exclusive = config_parser.add_mutually_exclusive_group(required=True)

    config_exclusive.add_argument(
        "--set",
        metavar=("key", "value"),
        dest="key_val",
        type=str,
        nargs=2,
        help="sets the key to specified value, within the configuration file",
    )

    config_exclusive.add_argument(
        "--get-path",
        dest="get_path",
        action="store_true",
        help="get path to configuration file",
    )

    config_exclusive.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="lists the current key value pairs of the configuration",
    )

    config_exclusive.add_argument(
        "--auto-detect",
        help="attempt to detect the appropriate settings for the host system, such as the path to the Python executable",
        action="store_true",
    )

    config_exclusive.add_argument(
        "-r",
        "--reset",
        help="resets configuration using a combination of default values and auto-detected settings",
        action="store_true",
    )


def config_generate_subprogram(subparsers, parents) -> None:
    parser_gen = subparsers.add_parser(
        "generate", help="Generate a new project.", parents=parents,
    )

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


def config_export_subprogram(subparsers, parents) -> None:
    parser_export = subparsers.add_parser(
        "export", help="Export project as FMU.", parents=parents,
    )

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


def config_validate_subprogram(subparsers, parents) -> None:

    parser_validate = subparsers.add_parser(
        "validate", help="Static and functional verification of FMU.", parents=parents,
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


def config_launch_subprogram(subparsers, parents) -> None:
    parser = subparsers.add_parser(
        "launch",
        help="launch proxy of a specified FMU (mainly for internal use)",
        parents=parents,
    )

    parser.add_argument(
        "fmu", help="path to a FMU created by PyFMU", type=str,
    )

    parser.add_argument(
        "instance_name",
        metavar="instance-name",
        help="instance name used to distinguish multiple instances of the same FMU",
    )

    parser.add_argument(
        "handshake_port",
        metavar="handshake-port",
        type=int,
        help="port used by the slave to confirm that the slave is instantiated",
    )

    parser.add_argument(
        "command_port",
        metavar="command-port",
        type=int,
        help="port used by the master to publish commands to slave",
    )

    parser.add_argument(
        "logging_port",
        metavar="logging-port",
        type=int,
        help="port used by the slave to publish log messages to master",
    )


# ==================== handlers called for each subprogram ====================


def handle_config(args):

    if not args.reset:

        config = get_configuration()

    # ------------------- reset configuration -------------
    if args.reset:
        reset_config()

    # --------------- config location -----------
    if args.get_path:
        stdout.write((get_config_path().__fspath__()))

    # ----------------- set keys --------------------
    if args.key_val:

        key, val = args.key_val
        config_set_val(key=key, val=val)

    # ---------------- list keys ---------------------
    if args.list:

        # make git "config --list"-style string
        l = [f"{k}={v}" for k, v in get_configuration().items()]

        stdout.write("\n".join(l))

    # -------------- auto detect ---------------------

    if args.auto_detect:

        if query_yes_no(
            "Do you want to overwrite the existing configuration with the results from the auto-detection?"
        ):
            auto_configure()


def handle_export(args):

    project_path = args.project

    archive_path = args.output

    export_project(project_path, archive_path, compress=False)


def handle_generate(args):

    from os.path import join, curdir, basename, normpath

    project_path = join(curdir, args.output)

    main_class_name = (
        args.name if args.name is not None else basename(normpath(project_path))
    )

    generate_project(project_path, main_class_name)


def handle_launch(args):

    global logger

    config = get_configuration()
    active_backend = config["backend.active"]

    logger.info(f"launching FMU: {args.fmu} using backend: '{active_backend}'")

    logger = logging.getLogger(f"slave_process.py:{args.instance_name}")

    logger.info("Slave process started")

    context = zmq.Context()

    # 1. create sockets
    handshake_socket = context.socket(zmq.PUSH)
    command_socket = context.socket(zmq.REP)
    logging_socket = context.socket(zmq.PUSH)

    print(args)

    # 2. bind to master

    logger.info(
        f"binding to master, handshake_port: {args.handshake_port}, command_port: {args.command_port}, logging_port: {args.logging_port}"
    )
    handshake_socket.connect(f"tcp://localhost:{args.handshake_port}")
    command_socket.connect(f"tcp://localhost:{args.command_port}")
    logging_socket.connect(f"tcp://localhost:{args.logging_port}")

    logger.info("Connected to master, performing handshake!")
    handshake_socket.send_pyobj("heres a string for you")

    # 3. instantiate slave

    logger.info(f"Creating slave")

    # append resources directory to path such that local modules can
    # be imported seamlessly
    fmu_path = Path(args.fmu)

    slave_config = None
    with open(fmu_path / "resources" / "slave_configuration.json", "r") as f:
        slave_config = json.load(f)

    resources_dir = fmu_path / "resources"

    slave_script_path = resources_dir / slave_config["slave_script"]
    slave_class = slave_config["slave_class"]

    sys.path.append(resources_dir.__fspath__())

    slave = instantiate_slave(slave_class, slave_script_path, slave_script_path.stem)

    logger.info(f"Slave instantiated")

    # 4. read and execute commands

    def free_instance():
        return Fmi2Status.ok

    command_to_methods = {
        0: slave.set_debug_logging,
        1: slave.setup_experiment,
        2: slave.enter_initialization_mode,
        3: slave.exit_initialization_mode,
        4: slave.terminate,
        5: slave.reset,
        6: slave.set_xxx,
        7: slave.get_xxx,
        8: slave.do_step,
        9: free_instance,
    }

    while True:

        try:
            kind, *args = command_socket.recv_pyobj()
            logger.info(
                f"Received command of kind: {command_to_methods[kind].__name__}, with arguments {args}"
            )

            if kind in command_to_methods:
                res = command_to_methods[kind](*args)
                logger.info(f"Command executed with result: {res}")
                command_socket.send_pyobj(res)

                if kind == 9:
                    logger.info(
                        f"Slave process shutting down gracefully due to request from backend"
                    )
                    sys.exit(0)
            else:
                logger.info(f"Received unrecognized command code {kind}")
                command_socket.send_pyobj(Fmi2Status.error)
        except Exception:
            logging.error(
                "An exception was raised by the slave and was not caught.",
                exc_info=True,
            )
            command_socket.send_pyobj(Fmi2Status.error)
            sys.exit(1)


def handle_validate(args):

    raise NotImplementedError("TODO Parse arguments related to validation tools")


# ==================== main program invoked as CLI ====================


def main():

    try:

        description_text = """Create Python based Functional Mock-up Units (FMUs).
The program provides several commands, each related to a specific part of the workflow.
Use the '--help' argument to see the uses of each command.
        """

        # trick to sharing common arguments
        # https://stackoverflow.com/questions/33645859/how-to-add-common-arguments-to-argparse-subcommands
        parent_parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description=description_text,
            add_help=False,
        )

        # general arguments
        parent_parser.add_argument(
            "--log-level",
            dest="log_level",
            default="critical",
            choices=["debug", "info", "warning", "error", "critical"],
            help="defines the verbosity of the output",
        )

        # subcommands
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers(dest="subprogram", required=True)

        config_config_subprogram(subparsers, [parent_parser])
        config_export_subprogram(subparsers, [parent_parser])
        config_launch_subprogram(subparsers, [parent_parser])
        config_generate_subprogram(subparsers, [parent_parser])

        config_validate_subprogram(subparsers, [parent_parser])

        args = parser.parse_args()

        logging.basicConfig(level=args.log_level.upper(), format="%(message)s")

        if args.subprogram == "config":
            handle_config(args)
        elif args.subprogram == "export":
            handle_export(args)
        elif args.subprogram == "generate":
            handle_generate(args)
        elif args.subprogram == "launch":
            handle_launch(args)
        elif args.subprogram == "validate":
            handle_validate(args)
        else:
            raise Exception("Not implemented")

    except Exception:
        logger.critical("Program failed due to an unhandled exception", exc_info=True)
        exit(1)
