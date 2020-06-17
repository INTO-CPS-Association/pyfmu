#include <exception>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <vector>

//#include <Python.h>

#include <fmt/format.h>
#include <pybind11/embed.h>

#include "spec/fmi2/fmi2Functions.h"

inline pybind11::object slaveContext;
inline std::mutex mutex;
inline bool initialized = false;

using lock = std::scoped_lock<std::mutex>;

// FMI functions
extern "C" {

// =============================================================================
// FMI 2.0 functions
// =============================================================================

const char *fmi2GetTypesPlatform() { return fmi2TypesPlatform; }

const char *fmi2GetVersion() { return "2.0"; }

fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType,
                              fmi2String fmuGUID,
                              fmi2String fmuResourceLocation,
                              const fmi2CallbackFunctions *functions,
                              fmi2Boolean visible, fmi2Boolean loggingOn) {

  try {
    lock l(mutex);

    if (!Py_IsInitialized()) {
      pybind11::initialize_interpreter();
    }

    pybind11::gil_scoped_acquire gil;

    if (!initialized) {
      slaveContext = pybind11::module::import("pyfmu.fmi2.slaveContext")
                         .attr("Fmi2SlaveContext")();
    }
    int fmuTypeInt = fmuType;
    auto handle =
        slaveContext
            .attr("instantiate")(instanceName, fmuTypeInt, fmuGUID,
                                 fmuResourceLocation, nullptr, visible)
            .cast<int>();
    return new int(handle);

  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return nullptr;
  }
}

void fmi2FreeInstance(fmi2Component c) {
  std::lock_guard lock(mutex);
  try {

    slaveContext.attr("free_instance")(*static_cast<int *>(c));
    delete c;
  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
  }
}

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,
                               size_t nCategories,
                               const fmi2String categories[]) {

  try {
    std::lock_guard lock(mutex);
    pybind11::gil_scoped_acquire gil;

    bool loggingOnBool = loggingOn;
    std::vector<std::string> categories_vector(categories,
                                               categories + nCategories);

    return slaveContext
        .attr("set_debug_logging")(categories_vector, loggingOnBool)
        .cast<fmi2Status>();

  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return fmi2Status::fmi2Error;
  }
}

fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined,
                               fmi2Real tolerance, fmi2Real startTime,
                               fmi2Boolean stopTimeDefined, fmi2Real stopTime) {
  return fmi2Fatal;
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c) { return fmi2Fatal; }

fmi2Status fmi2ExitInitializationMode(fmi2Component c) { return fmi2Fatal; }

fmi2Status fmi2Terminate(fmi2Component c) { return fmi2Fatal; }

fmi2Status fmi2Reset(fmi2Component c) { return fmi2Fatal; }

fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, fmi2Real value[]) {

  try {
    std::lock_guard lock(mutex);
    pybind11::gil_scoped_acquire gil;

    std::vector reference_vector(vr, vr + nvr);
    auto values = slaveContext.attr("get_xxx")().cast<std::vector<fmi2Real>>();

    return fmi2OK;

  } catch (const std::exception &e) {
    std::cerr << e.what() << '\n';
    return fmi2Fatal;
  }
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Integer value[]) {
  return fmi2Fatal;
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Boolean value[]) {

  return fmi2Fatal;
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, fmi2String value[]) {
  return fmi2Fatal;
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, const fmi2Real value[]) {
  return fmi2Fatal;
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Integer value[]) {
  return fmi2Fatal;
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Boolean value[]) {

  return fmi2Fatal;
}

fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, const fmi2String value[]) {

  return fmi2Fatal;
}

fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate *) {
  return fmi2Discard;
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate) { return fmi2Fatal; }

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate *) {
  return fmi2Discard;
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate, size_t *) {
  return fmi2Discard;
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate, fmi2Byte[],
                                 size_t) {
  return fmi2Discard;
}

fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte[], size_t,
                                   fmi2FMUstate *) {
  return fmi2Discard;
}

fmi2Status fmi2GetDirectionalDerivative(fmi2Component c,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2Real[], fmi2Real[]) {
  return fmi2Error;
}

fmi2Status fmi2SetRealInputDerivatives(fmi2Component c,
                                       const fmi2ValueReference[], size_t,
                                       const fmi2Integer[], const fmi2Real[]) {
  return fmi2Error;
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2Integer[], fmi2Real[]) {
  return fmi2Error;
}

fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint,
                      fmi2Real communicationStepSize,
                      fmi2Boolean noSetFMUStatePriorToCurrentPoint) {
  return fmi2Fatal;
}

fmi2Status fmi2CancelStep(fmi2Component c) { return fmi2Error; }

fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind, fmi2Status *) {
  return fmi2Error;
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s,
                             fmi2Real *value) {
  return fmi2Error;
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind,
                                fmi2Integer *) {
  return fmi2Error;
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind,
                                fmi2Boolean *) {
  return fmi2Error;
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind,
                               fmi2String *) {
  return fmi2Error;
}
}