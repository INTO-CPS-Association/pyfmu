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
using ValueReferences = Values<fmi2ValueReference>;
using RealValues = Values<fmi2Real>;
using BooleanValues = Values<bool>;
using IntegerValues = Values<fmi2Integer>;
using StringValues = Values<const std::string>;
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

  virtual Fmi2GetterResult<fmi2Real> getReal(ValueReferences references) = 0;
  virtual Fmi2GetterResult<fmi2Integer>
  getInteger(ValueReferences references) = 0;
  virtual Fmi2GetterResult<fmi2Boolean>
  getBoolean(ValueReferences references) = 0;
  virtual Fmi2GetterResult<fmi2String>
  getString(ValueReferences references) = 0;

  virtual fmi2Status setReal(ValueReferences references, RealValues values) = 0;
  virtual fmi2Status setInteger(ValueReferences references,
                                IntegerValues values) = 0;
  virtual fmi2Status setBoolean(ValueReferences references,
                                BooleanValues values) = 0;
  virtual fmi2Status setString(ValueReferences references, StringValues) = 0;
};
}; // namespace pyfmu::fmi2