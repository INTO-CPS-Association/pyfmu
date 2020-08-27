#![allow(dead_code)]
#![allow(unreachable_code)]
#![allow(unused_variables)]
#![allow(unused_imports)]

use crate::common::Fmi2Status;
use crate::common::Fmi2Type;
use crate::common::PyFmuBackend;
use crate::common::SlaveConfiguration;
use crate::common::SlaveHandle;
use crate::Fmi2CallbackLogger;
use anyhow::anyhow;
use anyhow::Error;
use lazy_static::lazy_static;
use serde_json;
use std::collections::HashMap;
use std::collections::HashSet;
use std::convert::TryFrom;
use std::fs::File;
use std::io::BufReader;
use std::sync::Mutex;
use std::sync::RwLock;
use url::Url;

use std::process::Command;
use subprocess::Exec;
use subprocess::Popen;
use subprocess::PopenConfig;

use num_enum::IntoPrimitive;
use serde::{Deserialize, Serialize};
use serde_pickle;

// see interpreter_backend.md for list of ids

#[derive(Debug, IntoPrimitive)]
#[repr(i32)]
enum CommandIds {
    SetDebugLogging = 0,
    SetupExperiment = 1,
    EnterInitializationMode = 2,
    ExitInitializationMode = 3,
    Terminate = 4,
    Reset = 5,
    SetValues = 6,
    GetValues = 7,
    // SetRealInputDerivatives = 8,
    // GetRealOutputDerivatives = 9,
    DoStep = 8,
    FreeInstance = 9,
}

// --------------------- Message Queue --------------------------

lazy_static! {
    static ref CONTEXT: zmq::Context = zmq::Context::new();
}

trait BindToRandom {
    /// Quality of life function inspired by
    /// https://pyzmq.readthedocs.io/en/latest/api/zmq.html?highlight=bind_random#zmq.Socket.bind_to_random_port
    fn bind_to_random_port(&self, addr: &str) -> Result<i32, Error>;
}

impl BindToRandom for zmq::Socket {
    fn bind_to_random_port(&self, addr: &str) -> Result<i32, Error> {
        let connection_str = format!("tcp://{}:*", addr);
        self.bind(&connection_str).unwrap();

        let endpoint = self.get_last_endpoint().unwrap().unwrap();
        let port: &str = endpoint.split(":").collect::<Vec<&str>>()[2];
        let port: i32 = port.parse().unwrap();
        return Ok(port);
    }
}

// impl BindToRandom for zmq::Socket {
//     fn bind_to_random_port(&self, addr: &str) -> Result<i32, Error> {
//         for port in 1025..65535 {
//             let connection_str = format!("tcp://{}:{}", addr, port);
//             match self.bind(&connection_str) {
//                 Ok(_) => {
//                     let port: Vec<&str> = self
//                         .get_last_endpoint()
//                         .unwrap()
//                         .unwrap()
//                         .split(":")
//                         .collect();
//                     assert_eq!(&port.len(), 2);

//                     let port: i32 = port[1].parse().unwrap();
//                     return Ok(port);
//                 }
//                 _ => {}
//             }
//         }

//         Err(anyhow::anyhow!("unable to bind to random socket"))
//     }
// }

// --------------------- Pickling Traits --------------------------

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

// --------------------------- Backend -----------------------------------

/// Spawns Python slaves as isolated processes by invoking the environments python-interpreter.
///
/// This is equivalent to starting a script from the command line: python slave_process.py --instance_name="myfmu" ...
///
/// Commands such as stepping, setting and reading variables are issues through a message queue.
pub struct InterpreterBackend {
    handle_to_command_sockets: HashMap<SlaveHandle, Mutex<zmq::Socket>>,
    handle_to_logging_sockets: HashMap<SlaveHandle, Mutex<zmq::Socket>>,
    handle_to_pid: HashMap<SlaveHandle, Mutex<Popen>>,
    active_handles: Mutex<HashSet<SlaveHandle>>,
    interpreter_name: String,
}

impl InterpreterBackend {
    pub fn new(interpreter_name: &str) -> Result<Self, Error> {
        // test that interpreter exists
        Popen::create(&[interpreter_name, "--version"], PopenConfig::default())?.wait()?;
        Ok(Self {
            handle_to_command_sockets: HashMap::new(),
            handle_to_logging_sockets: HashMap::new(),
            handle_to_pid: HashMap::new(),
            active_handles: Mutex::new(HashSet::new()),
            interpreter_name: interpreter_name.to_owned(),
        })
    }

    /// Returns a handle that is not associated with any existing process.
    fn get_free_handle(&self) -> SlaveHandle {
        let mut cnt: SlaveHandle = 0;
        let mut handles = self.active_handles.lock().unwrap();

        while handles.contains(&cnt) {
            cnt += 1;
        }
        assert!(!handles.contains(&cnt));
        handles.insert(cnt);
        cnt
    }

    /// Execute command on specified slave and parse the response
    fn invoke_command_on<'a, T, V>(&self, handle: SlaveHandle, args: T) -> V
    where
        T: serde::ser::Serialize,
        V: serde::de::Deserialize<'a>,
    {
        let socket = self
            .handle_to_command_sockets
            .get(&handle)
            .unwrap()
            .lock()
            .unwrap();

        socket.send_as_pickle(args).unwrap();

        socket
            .recv_from_pickle()
            .expect("Slave process responded with unexpected type to issued command")
    }

    fn log(&self, log_level: i32, category: &str, message: &str) {
        println!("{}", message);
    }
}

// --------------------------- FMI Functions -----------------------------------

impl PyFmuBackend for InterpreterBackend {
    // ------------ Lifecycle --------------

    fn instantiate(
        &mut self,
        instance_name: &str,
        fmu_type: Fmi2Type,
        fmu_guid: &str,
        resource_location: &str,
        callback_functions: Fmi2CallbackLogger,
        visible: bool,
        logging_on: bool,
    ) -> Result<SlaveHandle, Error> {
        let handle = self.get_free_handle();

        // 1. create sockets
        let handshake_socket = CONTEXT.socket(zmq::PULL).unwrap();
        let command_socket = CONTEXT.socket(zmq::REQ).unwrap();
        let logging_socket = CONTEXT.socket(zmq::PULL).unwrap();

        // 2. bind socket, TODO create unique port for each slave
        //let handshake_port = "54200";
        //let command_port = "54201";
        //let logging_port = "54202";
        //handshake_socket.bind("tcp://*:54200").unwrap();
        //command_socket.bind("tcp://*:54201").unwrap();
        //logging_socket.bind("tcp://*:54202").unwrap();

        let handshake_port = handshake_socket.bind_to_random_port("*").unwrap();
        let command_port = command_socket.bind_to_random_port("*").unwrap();
        let logging_port = logging_socket.bind_to_random_port("*").unwrap();

        // 3. start slave process
        println!("resource uri {:?}", resource_location);
        let resources_dir = Url::parse(resource_location)?
            .to_file_path()
            .map_err(|e| anyhow::anyhow!("Unable to convert URI into path {:?}", e))?;

        let file = File::open(&resources_dir.join("slave_configuration.json"))?;
        let reader = BufReader::new(file);

        let config: SlaveConfiguration =
            serde_json::from_reader(reader).expect("JSON was not well-formatted");
        let script_path = resources_dir.join(&config.slave_script);
        println!("Config is {:?}", &config);

        let args = [
            &self.interpreter_name,
            "slave_process.py",
            "--slave-script",
            &script_path.to_str().unwrap(),
            "--slave-class",
            &config.slave_class,
            "--instance-name",
            instance_name,
            "--handshake-port",
            &handshake_port.to_string(),
            "--command-port",
            &command_port.to_string(),
            "--logging-port",
            &logging_port.to_string(),
        ];

        // Start process and store process ids for porential termination
        let pid = Popen::create(&args, PopenConfig::default())
            .expect("Failed instantiating FMU, unable to start a new Python process");
        self.handle_to_pid.insert(handle, Mutex::new(pid));

        //pid.terminate().expect("unable to terminate slave process");

        println!("Waiting for handshake from slave");

        // 4 wait for handshake
        let msg: String = handshake_socket.recv_from_pickle().unwrap();

        println!("Got handshake");

        self.handle_to_command_sockets
            .insert(handle, Mutex::new(command_socket));

        self.handle_to_logging_sockets
            .insert(handle, Mutex::new(logging_socket));

        Ok(handle)
    }

    fn free_instance(&mut self, handle: SlaveHandle) -> Result<(), Error> {
        let status: i32 = self.invoke_command_on(handle, (CommandIds::FreeInstance as i32,));
        self.active_handles.lock().unwrap().remove(&handle);
        self.handle_to_command_sockets.remove(&handle);
        self.handle_to_logging_sockets.remove(&handle);

        Ok(())
    }

    fn set_debug_logging(
        &self,
        handle: SlaveHandle,
        logging_on: bool,
        categories: Vec<&str>,
    ) -> Result<Fmi2Status, Error> {
        let status: i32 = self.invoke_command_on(
            handle,
            (CommandIds::SetDebugLogging as i32, categories, logging_on),
        );
        Ok(Fmi2Status::try_from(status)?)
    }
    fn setup_experiment(
        &self,
        handle: SlaveHandle,
        start_time: f64,
        tolerance: Option<f64>,
        stop_time: Option<f64>,
    ) -> Result<Fmi2Status, Error> {
        let status: i32 = self.invoke_command_on(
            handle,
            (
                CommandIds::SetupExperiment as i32,
                start_time,
                tolerance,
                stop_time,
            ),
        );
        Ok(Fmi2Status::try_from(status)?)
    }
    fn enter_initialization_mode(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        let status: i32 =
            self.invoke_command_on(handle, (CommandIds::EnterInitializationMode as i32,));
        Ok(Fmi2Status::try_from(status)?)
    }
    fn exit_initialization_mode(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        let status: i32 =
            self.invoke_command_on(handle, (CommandIds::ExitInitializationMode as i32,));
        Ok(Fmi2Status::try_from(status)?)
    }
    fn terminate(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        let status: i32 = self.invoke_command_on(handle, (CommandIds::Terminate as i32,));
        Ok(Fmi2Status::try_from(status)?)
    }
    fn reset(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error> {
        let status: i32 = self.invoke_command_on(handle, (CommandIds::Reset as i32,));
        Ok(Fmi2Status::try_from(status)?)
    }

    // ------------ Getters --------------

    fn get_real(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<f64>>), Error> {
        let (status, values): (i32, Option<Vec<f64>>) =
            self.invoke_command_on(handle, (CommandIds::GetValues as i32, references));

        println!("Got these values: {:?}", values);
        Ok((Fmi2Status::try_from(status)?, values))
    }
    fn get_integer(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<i32>>), Error> {
        let (status, values): (i32, Option<Vec<i32>>) =
            self.invoke_command_on(handle, (CommandIds::GetValues as i32, references));

        Ok((Fmi2Status::try_from(status)?, values))
    }
    fn get_boolean(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<bool>>), Error> {
        let (status, values): (i32, Option<Vec<bool>>) =
            self.invoke_command_on(handle, (CommandIds::GetValues as i32, references));

        Ok((Fmi2Status::try_from(status)?, values))
    }
    fn get_string(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<String>>), Error> {
        let (status, values): (i32, Option<Vec<String>>) =
            self.invoke_command_on(handle, (CommandIds::GetValues as i32, references));

        Ok((Fmi2Status::try_from(status)?, values))
    }

    // ------------ Setters --------------
    fn set_real(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[f64],
    ) -> Result<Fmi2Status, Error> {
        let status: i32 =
            self.invoke_command_on(handle, (CommandIds::SetValues as i32, references, values));
        Ok(Fmi2Status::try_from(status)?)
    }

    fn set_integer(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[i32],
    ) -> Result<Fmi2Status, Error> {
        let status: i32 =
            self.invoke_command_on(handle, (CommandIds::SetValues as i32, references, values));
        Ok(Fmi2Status::try_from(status)?)
    }

    fn set_boolean(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[bool],
    ) -> Result<Fmi2Status, Error> {
        let status: i32 =
            self.invoke_command_on(handle, (CommandIds::SetValues as i32, references, values));
        Ok(Fmi2Status::try_from(status)?)
    }

    fn set_string(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[&str],
    ) -> Result<Fmi2Status, Error> {
        let status: i32 =
            self.invoke_command_on(handle, (CommandIds::SetValues as i32, references, values));
        Ok(Fmi2Status::try_from(status)?)
    }

    // fn fmi2SetRealInputDerivatives(&self) -> Result<Fmi2Status, Error> {todo!();}
    // fn fmi2GetRealOutputDerivatives(&self) -> Result<Fmi2Status, Error> {todo!();}
    fn do_step(
        &self,
        handle: SlaveHandle,
        current_communication_point: f64,
        communication_step: f64,
        no_set_fmu_state_prior_to_current_point: bool,
    ) -> Result<Fmi2Status, Error> {
        let status: i32 = self.invoke_command_on(
            handle,
            (
                CommandIds::DoStep as i32,
                current_communication_point,
                communication_step,
                no_set_fmu_state_prior_to_current_point,
            ),
        );
        Ok(Fmi2Status::try_from(status)?)
    }
}

impl Drop for InterpreterBackend {
    fn drop(&mut self) {
        for pid in self.handle_to_pid.values() {
            pid.lock()
                .unwrap()
                .terminate()
                .expect("Unable to terminate slave process");
        }
    }
}
