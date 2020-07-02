use anyhow::Error;
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

/// Callback to envrioment used for logging
pub trait FMI2Logger {
    fn log(self, instance_name: &str, status: Fmi2Status, category: &str, message: &str);
}

/// An identifier that can be used to uniquely identify a slave within the context of a specific backend.
pub type SlaveHandle = i32;

/// Represents an manager of multiple Python slave instances.
/// Each instance is assoicated with an integer handle returned by the function
pub trait PyFmuBackend {
    fn instantiate(
        &self,
        instance_name: &str,
        fmu_type: Fmi2Type,
        fmu_guid: &str,
        resource_location: &str,
        callback_functions: Box<dyn FMI2Logger>,
        visible: bool,
        logging_on: bool,
    ) -> Result<SlaveHandle, Error>;
    // fn fmi2SetDebugLogging(&self) -> Result<c_int, Error>;
    // fn fmi2SetupExperiment(&self) -> Result<c_int, Error>;
    // fn fmi2EnterInitializationMode(&self) -> Result<c_int, Error>;
    // fn fmi2ExitInitializationMode(&self) -> Result<c_int, Error>;
    // fn fmi2Terminate(&self) -> Result<c_int, Error>;
    // fn fmi2Reset(&self) -> Result<c_int, Error>;
    // fn fmi2GetXXX(&self) -> Result<c_int, Error>;
    // fn fmi2SetXXX(&self) -> Result<c_int, Error>;
    // fn fmi2SetRealInputDerivatives(&self) -> Result<c_int, Error>;
    // fn fmi2GetRealOutputDerivatives(&self) -> Result<c_int, Error>;
    // fn fmi2DoStep(&self) -> Result<c_int, Error>;
}
