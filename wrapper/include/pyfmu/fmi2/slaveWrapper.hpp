#pragma once

#include <filesystem>
#include <memory>
#include <string>

#include "pybind11/embed.h"
#include "pybind11/stl.h"

#include <fmt/ranges.h>

#include "pyfmu/fmi2/logging.hpp"
#include "spec/fmi2/fmi2TypesPlatform.h"

// Log category
#define PYFMU_WRAPPER_LOG_CATEGORY "wrapper"

namespace pyfmu::fmi2 {

template <typename T> using Values = const std::vector<T>;
using ValueReferences = Values<fmi2ValueReference>;
using RealValues = Values<fmi2Real>;
using BooleanValues = Values<bool>;
using IntegerValues = Values<fmi2Integer>;
using StringValues = Values<const std::string>;
namespace py = pybind11;

template <typename T>
using Fmi2GetterResult = std::tuple<Values<T>, fmi2Status>;
using std::filesystem::path;

enum Fmi2DataType {
  real,
  integer,
  boolean,
  string,
};

/**
 * @brief
 *
 */
class SlaveWrapper {

public:
  SlaveWrapper(path resources, Logger *logger);

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

  template <typename T>
  fmi2Status setXXXFunction(ValueReferences valueReferences, Values<T> values,
                            const std::string &type) {

    logger->ok(PYFMU_WRAPPER_LOG_CATEGORY, "Setting the variables: {} to: {}",
               valueReferences, values);
    return 0;
  }

  template <typename T>
  Fmi2GetterResult<T> getXXXFunction(ValueReferences references,
                                     fmi2Type type) {
    logger->ok(PYFMU_WRAPPER_LOG_CATEGORY,
               "Getting values of the variables: {}", valueReferences);

    try {
      auto res = slaveInstance.attr("_get_xxx")(references, type);
      return res.cast<Fmi2GetterResults<T>>();
    } catch (const std::exception &e) {
      logger->log(fmi2Fatal, PYFMU_WRAPPER_LOG_CATEGORY,
                  "read failed, an exception was raised: {}", e.what());
      return Fmi2GetterResult(nullptr, fmi2Fatal);
    };
  }

  ~SlaveWrapper();

private:
  py::object slaveInstance;
  py::object method_getxxx;
  py::object method_setxxx;
  py::object method_enterInitializationMode;
  py::object method_exitInitializationMode;
  py::object method_reset;
  py::object method_terminate;
  py::object method_setupExperiment;
  py::object method_dostep;

  Logger *logger;
  PyMethodDef pCallbackDef;
  PyObject *pCallbackFunc;
};

} // namespace pyfmu::fmi2