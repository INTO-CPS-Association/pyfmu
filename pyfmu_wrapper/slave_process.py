from __future__ import annotations
from argparse import ArgumentParser
import zmq
import logging
import sys
import numpy
import scipy


class MySlave:
    def do_step(self, start_time: float, step_size: float, no_step_prior: bool):
        return 0

    def set_xxx(self, references: list[int], values):
        return 0


if __name__ == "__main__":

    logging.basicConfig(level=logging.CRITICAL)
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
    slave = MySlave()

    # 4. read and execute commands

    command_to_methods = {0: slave.do_step, 1: slave.set_xxx}

    while True:

        kind, *args = command_socket.recv_pyobj()
        logger.info(f"Received command of kind: {kind}, with arguments {args}")

        if kind in command_to_methods:
            command_socket.send_pyobj(command_to_methods[kind](*args))

        elif kind == 2:
            logging.info("Received terminate signal")
            # context.destroy()
            sys.exit(0)

