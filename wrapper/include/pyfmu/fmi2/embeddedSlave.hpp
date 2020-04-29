#pragma once

#include <memory>
#include <string>

#include "pybind11/embed.h"
#include "pybind11/stl.h"

#include <fmt/ranges.h>

#include "pyfmu/fmi2/logging.hpp"
#include "pyfmu/fmi2/slave.hpp"
#include "spec/fmi2/fmi2TypesPlatform.h"

// Log category
#define PYFMU_WRAPPER_LOG_CATEGORY "wrapper"

namespace pyfmu::fmi2 {

/**
 * @brief Slave which uses an CPython-embedding to execute Python code inside an
 * FMU.
 *
 * @details The C-code is bound to Python using pybind11, which provides an C++
 * alternative to CPython's C-API.
 */
class EmbeddedSlave : public Slave {

public:
  /**
   * @brief Constructs a Python slave from the specified module and class.
   *
   * @note The CPython interpreter MUST be instantiated when the constructor is
   * called. Also, the folder containing the slave script MUST be in
   * Python's path at the time the constructor is called.
   *
   * @param slaveModule
   * @param slaveClass
   * @param logger
   */
  EmbeddedSlave(const std::string slaveModule, const std::string slaveClass,
                Logger *logger);

  fmi2Status setupExperiment(fmi2Real startTime,
                             std::optional<fmi2Real> tolerance,
                             std::optional<fmi2Real> stopTime);

  fmi2Status enterInitializationMode();

  fmi2Status exitInitializationMode();

  fmi2Status doStep(fmi2Real currentTime, fmi2Real stepSize,
                    fmi2Boolean noSetFMUStatePriorToCurrentPoint);

  fmi2Status reset();

  fmi2Status terminate();

  fmi2Status setDebugLogging(fmi2Boolean loggingOn,
                             std::vector<std::string> loggingCategories) const;

  virtual Fmi2GetterResult<fmi2Real> getReal(VRefs references);
  virtual Fmi2GetterResult<fmi2Integer> getInteger(VRefs references);
  virtual Fmi2GetterResult<fmi2Boolean> getBoolean(VRefs references);
  virtual Fmi2GetterResult<fmi2String> getString(VRefs references);

  virtual fmi2Status setReal(VRefs references, RealValues values);
  virtual fmi2Status setInteger(VRefs references, IntegerValues values);
  virtual fmi2Status setBoolean(VRefs references, BooleanValues values);
  virtual fmi2Status setString(VRefs references, StringValues);

  ~EmbeddedSlave();

private:
  pybind11::object slaveInstance;
  pybind11::object method_getxxx;
  pybind11::object method_setxxx;
  pybind11::object method_enterInitializationMode;
  pybind11::object method_exitInitializationMode;
  pybind11::object method_reset;
  pybind11::object method_terminate;
  pybind11::object method_setupExperiment;
  pybind11::object method_dostep;

  Logger *logger;
  PyMethodDef pCallbackDef;
  PyObject *pCallbackFunc;
};

} // namespace pyfmu::fmi2