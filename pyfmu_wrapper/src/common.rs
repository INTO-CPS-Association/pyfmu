use crate::Fmi2CallbackLogger;
use anyhow::Error;
use num_enum::IntoPrimitive;
use num_enum::TryFromPrimitive;
use std::os::raw::c_double;
use std::os::raw::c_int;
use std::os::raw::c_uint;

/// Represents the possible status codes which are returned from the slave
#[derive(Debug, TryFromPrimitive, IntoPrimitive, PartialEq, PartialOrd, Eq)]
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

#[derive(Debug, TryFromPrimitive, IntoPrimitive, PartialEq, Eq)]
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
    // ------------ Lifecycle --------------

    fn instantiate(
        &self,
        instance_name: &str,
        fmu_type: Fmi2Type,
        fmu_guid: &str,
        resource_location: &str,
        callback_functions: Fmi2CallbackLogger,
        visible: bool,
        logging_on: bool,
    ) -> Result<SlaveHandle, Error>;
    fn set_debug_logging(
        &self,
        handle: SlaveHandle,
        logging_on: bool,
        categories: Vec<&str>,
    ) -> Result<Fmi2Status, Error>;
    fn setup_experiment(
        &self,
        handle: SlaveHandle,
        start_time: f64,
        tolerance: Option<f64>,
        stop_time: Option<f64>,
    ) -> Result<Fmi2Status, Error>;
    fn enter_initialization_mode(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error>;
    fn exit_initialization_mode(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error>;
    fn terminate(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error>;
    fn reset(&self, handle: SlaveHandle) -> Result<Fmi2Status, Error>;

    // ------------ Getters --------------

    fn get_real(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<f64>>), Error>;
    fn get_integer(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<i32>>), Error>;
    fn get_boolean(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<bool>>), Error>;
    fn get_string(
        &self,
        handle: SlaveHandle,
        references: &[u32],
    ) -> Result<(Fmi2Status, Option<Vec<String>>), Error>;

    // ------------ Setters --------------
    fn set_real(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[f64],
    ) -> Result<Fmi2Status, Error>;

    fn set_integer(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[i32],
    ) -> Result<Fmi2Status, Error>;

    fn set_boolean(
        &self,
        handle: SlaveHandle,
        references: &[u32],
        values: &[bool],
    ) -> Result<Fmi2Status, Error>;

    fn set_string(
        &self,
        handle: SlaveHandle,
        references: &[c_uint],
        values: &[&str],
    ) -> Result<Fmi2Status, Error>;

    // fn fmi2SetRealInputDerivatives(&self) -> Result<Fmi2Status, Error>;
    // fn fmi2GetRealOutputDerivatives(&self) -> Result<Fmi2Status, Error>;
    fn do_step(
        &self,
        handle: SlaveHandle,
        current_communication_point: f64,
        communication_step: f64,
        no_set_fmu_state_prior_to_current_point: bool,
    ) -> Result<Fmi2Status, Error>;
}
