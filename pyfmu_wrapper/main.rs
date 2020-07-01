use lazy_static::lazy_static;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::process::Command;
use subprocess::Popen;
use subprocess::PopenConfig;
use zmq::Context;
use zmq::Error;

use serde::{Deserialize, Serialize};
use serde_pickle;

// see interpreter_backend.md for list of ids
enum CommandIds {
    SetDebugLogging = 0,
    fmi2SetupExperiment = 1,
    fmi2EnterInitializationMode = 2,
    fmi2ExitInitializationMode = 3,
    fmi2Terminate = 4,
    fmi2Reset = 5,
    fmi2GetXXX = 6,
    fmi2SetXXX = 7,
    fmi2SetRealInputDerivatives = 8,
    fmi2GetRealOutputDerivatives = 9,
    fmi2DoStep = 10,
}

lazy_static! {
    static ref CONTEXT: Context = zmq::Context::new();
}

trait PickleSender<T> {
    fn send_as_pickle(&self, value: T) -> Result<(), zmq::Error>;
}

trait PickleReceiver<T> {
    fn recv_from_pickle(&self) -> Result<T, zmq::Error>;
}

impl<T> PickleSender<T> for zmq::Socket
where
    T: serde::ser::Serialize,
{
    fn send_as_pickle(&self, value: T) -> Result<(), zmq::Error> {
        let pickle = serde_pickle::to_vec(&value, true).expect("unable to pickle object");
        self.send(&pickle, 0)
    }
}

impl<'a, T> PickleReceiver<T> for zmq::Socket
where
    T: serde::de::Deserialize<'a>,
{
    fn recv_from_pickle(&self) -> Result<T, zmq::Error> {
        let bytes = self.recv_bytes(0)?;

        let value: T = serde_pickle::from_slice(&bytes).expect("unable to un-pickle object");
        std::result::Result::Ok(value)
    }
}

fn main_bak() {
    // 1. create sockets
    let handshake_socket = CONTEXT.socket(zmq::PULL).unwrap();
    let command_socket = CONTEXT.socket(zmq::REQ).unwrap();
    let logging_socket = CONTEXT.socket(zmq::PULL).unwrap();

    // 2. bind sockets

    let handshake_port = "54200";
    let command_port = "54201";
    let logging_port = "54202";
    handshake_socket.bind("tcp://*:54200").unwrap();
    command_socket.bind("tcp://*:54201").unwrap();
    logging_socket.bind("tcp://*:54202").unwrap();

    // 3. start slave process

    let args = [
        "python",
        "slave_process.py",
        "--slave-script",
        "TODO",
        "--instance-name",
        "TODO",
        "--handshake-port",
        handshake_port,
        "--command-port",
        command_port,
        "--logging-port",
        logging_port,
    ];

    let mut pid = Popen::create(&args, PopenConfig::default()).unwrap();

    let mut msg = zmq::Message::new();
    println!("waiting for handshake");

    // handshake_socket.recv(&mut msg, 0).unwrap();
    let handshake_response: String = handshake_socket.recv_from_pickle().unwrap();
    println!("got handshake with msg: {}", handshake_response);

    for i in 0..1000 {
        command_socket
            .send_as_pickle((0, 0.0, 1.0, true))
            .expect("Failed sending do_step command");

        let status: i32 = command_socket.recv_from_pickle().unwrap();
        // println!("return status of command was: {}", status)
    }

    command_socket.send_as_pickle((2, &"terminate")).unwrap();

    println!("Send termination command, waiting for child process to terminate");

    match pid.wait_timeout(std::time::Duration::from_millis(500)) {
        Err(_) => println!("Child process did not terminate"),

        Ok(status) => println!(
            "Child process finished and with status code == 0: {}",
            status.unwrap().success()
        ),
    }
}
