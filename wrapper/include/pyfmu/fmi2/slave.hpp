#pragma once
/**
 * @file slave.hpp
 * @author Christian Møldrup Legaard (CML@eng.au.dk)
 * @brief defines the C++ interface of a fmi2 slave.
 * @version 0.1
 * @date 2020-04-29
 *
 * @copyright Copyright (c) 2020
 *
 */
#include <optional>
#include <string>
#include <vector>

#include "spec/fmi2/fmi2Functions.h"

namespace pyfmu::fmi2 {

enum Fmi2DataType {
  real,
  integer,
  boolean,
  string,
};

template <typename T> using Values = const std::vector<T>;

/**
 * @brief list of indices used to refer to a FMUs variables.
 *
 */
using VRefs = Values<fmi2ValueReference>;

using RealValues = Values<fmi2Real>;
using BooleanValues = Values<fmi2Boolean>;
using IntegerValues = Values<fmi2Integer>;
using StringValues = Values<fmi2String>;
template <typename T>
using Fmi2GetterResult = std::tuple<Values<T>, fmi2Status>;

class Slave {

public:
  virtual fmi2Status setupExperiment(fmi2Real startTime,
                                     std::optional<fmi2Real> tolerance,
                                     std::optional<fmi2Real> stopTime) = 0;

  virtual fmi2Status enterInitializationMode() = 0;

  virtual fmi2Status exitInitializationMode() = 0;

  virtual fmi2Status doStep(fmi2Real currentTime, fmi2Real stepSize,
                            fmi2Boolean noSetFMUStatePriorToCurrentPoint) = 0;

  virtual fmi2Status reset() = 0;

  virtual fmi2Status terminate() = 0;

  virtual Fmi2GetterResult<fmi2Real> getReal(VRefs references) = 0;
  virtual Fmi2GetterResult<fmi2Integer> getInteger(VRefs references) = 0;
  virtual Fmi2GetterResult<fmi2Boolean> getBoolean(VRefs references) = 0;
  virtual Fmi2GetterResult<fmi2String> getString(VRefs references) = 0;

  virtual fmi2Status setReal(VRefs references, RealValues values) = 0;
  virtual fmi2Status setInteger(VRefs references, IntegerValues values) = 0;
  virtual fmi2Status setBoolean(VRefs references, BooleanValues values) = 0;
  virtual fmi2Status setString(VRefs references, StringValues) = 0;
};
}; // namespace pyfmu::fmi2