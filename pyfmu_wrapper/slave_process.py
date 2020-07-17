from __future__ import annotations
from argparse import ArgumentParser
import zmq
import logging
import sys
import numpy
import scipy

import sys
from pathlib import Path

from pyfmu.fmi2 import Fmi2Status
from pyfmu.builder.utils import instantiate_slave


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("slave_process.py")

    logger.info("Slave process started")

    parser = ArgumentParser()

    parser.add_argument(
        "--handshake-port",
        required=True,
        dest="handshake_port",
        type=int,
        help="port used by the slave to confirm that the slave is instantiated",
    )

    parser.add_argument(
        "--command-port",
        required=True,
        dest="command_port",
        type=int,
        help="port use by the master to publish commands to slave",
    )
    parser.add_argument(
        "--logging-port",
        required=True,
        dest="logging_port",
        type=int,
        help="port use by the slave to publish log messages to master",
    )

    parser.add_argument(
        "--slave-script",
        required=True,
        dest="slave_script",
        type=str,
        help="absolute path to the slave script",
    )
    parser.add_argument(
        "--slave-class",
        required=True,
        dest="slave_class",
        type=str,
        help="class which is used to create an instance of the slave",
    )

    parser.add_argument(
        "--instance-name",
        required=True,
        dest="instance_name",
        type=str,
        help="name of the slave instance",
    )

    args = parser.parse_args()

    context = zmq.Context()

    # 1. create sockets
    handshake_socket = context.socket(zmq.PUSH)
    command_socket = context.socket(zmq.REP)
    logging_socket = context.socket(zmq.PUSH)

    # 2. bind to master

    logger.info(
        f"binding to master, command_port: {args.command_port}, logging_port: {args.logging_port}"
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
    slave_script = Path(args.slave_script)
    sys.path.append(str(slave_script.parent))

    #
    module_name = slave_script.stem
    slave = instantiate_slave(args.slave_class, slave_script, module_name)

    # 4. read and execute commands

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
    }

    while True:

        try:
            kind, *args = command_socket.recv_pyobj()
            logger.info(f"Received command of kind: {kind}, with arguments {args}")

            if kind in command_to_methods:
                res = command_to_methods[kind](*args)
                logger.info(f"Command executed with result: {res}")
                command_socket.send_pyobj(res)

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

