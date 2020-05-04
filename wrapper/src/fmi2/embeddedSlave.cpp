#include <filesystem>
#include <fstream>
#include <iostream>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <utility>

#include "fmt/format.h"
#include "pybind11/embed.h"

#include "pyfmu/fmi2/configuration.hpp"
#include "pyfmu/fmi2/embeddedSlave.hpp"
#include "pyfmu/fmi2/logging.hpp"
#include "spec/fmi2/fmi2TypesPlatform.h"

using namespace fmt;
using namespace std;

using path = filesystem::path;

namespace pyfmu::fmi2 {

enum Fmi2Status {
  ok,
  warning,
  discard,
  error,
  fatal,
  pending,
};

EmbeddedSlave::EmbeddedSlave(const std::string &slaveModule,
                             const std::string &slaveClass, Logger *logger)
    : logger(logger) {

  if (!Py_IsInitialized())
    runtime_error("Python interpeter must be instantiated prior to creating an "
                  "instance of the wrapper");

  try {

    slaveInstance = pybind11::module::import(slaveModule.c_str())
                        .attr(slaveClass.c_str())();

    method_getxxx = slaveInstance.attr("_get_xxx");
    method_setxxx = slaveInstance.attr("_set_xxx");
    method_setDebugLogging = slaveInstance.attr("_set_debug_logging");
    method_enterInitializationMode =
        slaveInstance.attr("_enter_initialization_mode");
    method_exitInitializationMode =
        slaveInstance.attr("_exit_initialization_mode");
    method_reset = slaveInstance.attr("_reset");
    method_terminate = slaveInstance.attr("_terminate");
    method_setupExperiment = slaveInstance.attr("_setup_experiment");
    method_dostep = slaveInstance.attr("_do_step");

  } catch (const std::exception &e) {
    logger->fatal(
        "wrapper",
        "Unable to instantiate slave class, an exception was raised:\n{}",
        e.what());
  }
}

fmi2Status EmbeddedSlave::setupExperiment(fmi2Real startTime,
                                          std::optional<fmi2Real> tolerance,
                                          std::optional<fmi2Real> stopTime) {
  return fmi2Fatal;
}

fmi2Status EmbeddedSlave::enterInitializationMode() {
  return method_enterInitializationMode().cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::exitInitializationMode() {
  return method_exitInitializationMode().cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::doStep(fmi2Real currentTime, fmi2Real stepSize,
                                 fmi2Boolean noSetFMUStatePriorToCurrentPoint) {

  return method_dostep(currentTime, stepSize, noSetFMUStatePriorToCurrentPoint)
      .cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::reset() { return fmi2Fatal; }

fmi2Status EmbeddedSlave::terminate() {
  return method_terminate().cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::setDebugLogging(bool loggingOn,
                                          StringValues categories) {
  auto test = method_setDebugLogging(loggingOn, categories);
  return test.cast<fmi2Status>();
}

Fmi2GetterResult<fmi2Real> EmbeddedSlave::getReal(VRefs references) {
  return method_getxxx(references, Fmi2DataType::real)
      .cast<Fmi2GetterResult<fmi2Real>>();
}
Fmi2GetterResult<fmi2Integer> EmbeddedSlave::getInteger(VRefs references) {
  return method_getxxx(references, Fmi2DataType::integer)
      .cast<Fmi2GetterResult<fmi2Integer>>();
}
Fmi2GetterResult<fmi2Boolean> EmbeddedSlave::getBoolean(VRefs references) {
  return method_getxxx(references, Fmi2DataType::boolean)
      .cast<Fmi2GetterResult<fmi2Boolean>>();
}
Fmi2GetterResult<fmi2String> EmbeddedSlave::getString(VRefs references) {
  return method_getxxx(references, Fmi2DataType::string)
      .cast<Fmi2GetterResult<fmi2String>>();
}

fmi2Status EmbeddedSlave::setReal(VRefs references, RealValues values) {
  return method_setxxx(references, values, Fmi2DataType::real)
      .cast<fmi2Status>();
}
fmi2Status EmbeddedSlave::setInteger(VRefs references, IntegerValues values) {
  return method_setxxx(references, values, Fmi2DataType::integer)
      .cast<fmi2Status>();
}
fmi2Status EmbeddedSlave::setBoolean(VRefs references, BooleanValues values) {
  return method_setxxx(references, values, Fmi2DataType::boolean)
      .cast<fmi2Status>();
}
fmi2Status EmbeddedSlave::setString(VRefs references, StringValues values) {
  return method_setxxx(references, values, Fmi2DataType::string)
      .cast<fmi2Status>();
}

EmbeddedSlave::~EmbeddedSlave() {}

} // namespace pyfmu::fmi2
