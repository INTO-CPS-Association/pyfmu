use anyhow::Error;
use std::marker::Sync;
use std::os::raw::c_char;
use std::os::raw::c_int;
use std::os::raw::c_ulonglong;
use std::os::raw::c_void;

use num_enum::IntoPrimitive;
use num_enum::TryFromPrimitive;

#[derive(Debug, TryFromPrimitive, IntoPrimitive, PartialEq, Eq)]
#[repr(i32)]
pub enum Fmi2Status {
    Fmi2OK,
    Fmi2Warning,
    Fmi2Discard,
    Fmi2Error,
    Fmi2Fatal,
    Fmi2Pending,
}

#[derive(Debug, TryFromPrimitive, PartialEq, Eq)]
#[repr(i32)]
pub enum Fmi2StatusKind {
    Fmi2DoStepStatus = 0,
    Fmi2PendingStatus = 1,
    Fmi2LastSuccessfulTime = 2,
    Fmi2Terminated = 3,
}

#[derive(Debug, TryFromPrimitive, PartialEq, Eq)]
#[repr(i32)]
pub enum Fmi2Type {
    Fmi2ModelExchange = 0,
    Fmi2CoSimulation = 1,
}

pub type Fmi2CallbackLogger = extern "C" fn(
    component_environment: *mut c_void,
    instance_name: *const c_char,
    status: c_int,
    category: *const c_char,
    message: *const c_char,
    // ... variadic functions support in rust seems to be unstable
);
pub type Fmi2CallbackAllocateMemory = extern "C" fn(nobj: c_ulonglong, size: c_ulonglong);
pub type Fmi2CallbackFreeMemory = extern "C" fn(obj: *const c_void);
pub type Fmi2StepFinished = extern "C" fn(component_environment: *mut c_void, status: Fmi2Status);

#[repr(C)]
#[derive(Copy, Clone)]
pub struct Fmi2CallbackFunctions {
    logger: Option<Fmi2CallbackLogger>,
    allocate_memory: Option<Fmi2CallbackAllocateMemory>,
    free_memory: Option<Fmi2CallbackFreeMemory>,
    step_finished: Option<Fmi2StepFinished>,
    component_environment: Option<*mut c_void>,
}

/// Represents an manager of multiple Python slave instances.
/// Each instance is accessed using their *instance name* which is unique within the simulation context of a specific FMU.
///
///
///

pub trait PyFmuBackend {
    fn instantiate(
        self,
        instance_name: &str,
        fmu_type: Fmi2Type,
        fmu_guid: &str,
        resource_location: &str,
        callback_functions: *const c_void,
        visible: bool,
        logging_on: bool,
    ) -> Result<(), Error>;
    // fn fmi2SetDebugLogging(self) -> Result<c_int, Error>;
    // fn fmi2SetupExperiment(self) -> Result<c_int, Error>;
    // fn fmi2EnterInitializationMode(self) -> Result<c_int, Error>;
    // fn fmi2ExitInitializationMode(self) -> Result<c_int, Error>;
    // fn fmi2Terminate(self) -> Result<c_int, Error>;
    // fn fmi2Reset(self) -> Result<c_int, Error>;
    // fn fmi2GetXXX(self) -> Result<c_int, Error>;
    // fn fmi2SetXXX(self) -> Result<c_int, Error>;
    // fn fmi2SetRealInputDerivatives(self) -> Result<c_int, Error>;
    // fn fmi2GetRealOutputDerivatives(self) -> Result<c_int, Error>;
    // fn fmi2DoStep(self) -> Result<c_int, Error>;
}
