#pragma once
/**
 * @file fmi2WrapperAdapter.hpp
 * @author Christian Møldrup Legaard (cml@eng.au.dk)
 * @brief Adapts FMI2 C-style to C++ style interface.
 * @date 2020-04-28
 *
 * @copyright Copyright (c) 2020
 *
 */

#include "pyfmu/fmi2/slave.hpp"

namespace pyfmu::fmi2 {

/**
 * @brief Adaptor from the C-style FMI interface to a C++-style interface that
 * makes use of STL containers. This eases the conversion of types by pybind11
 * and logging of values by fmt.
 */
class SlaveAdapter {
public:
  SlaveAdapter(Slave *slave);

  ~SlaveAdapter();

  fmi2Status setupExperiment(fmi2Boolean toleranceDefined, fmi2Real tolerance,
                             fmi2Real startTime, fmi2Boolean stopTimeDefined,
                             fmi2Real stopTime);

  fmi2Status enterInitializationMode();

  fmi2Status exitInitializationMode();

  fmi2Status doStep(fmi2Real currentTime, fmi2Real stepSize,
                    fmi2Boolean noSetFMUStatePriorToCurrentPoint);

  fmi2Status reset();

  fmi2Status terminate();

  fmi2Status getInteger(const fmi2ValueReference *vr, size_t nvr,
                        fmi2Integer *value) const;

  fmi2Status getReal(const fmi2ValueReference *vr, size_t nvr,
                     fmi2Real *value) const;

  fmi2Status getString(const fmi2ValueReference *vr, size_t nvr,
                       fmi2String *value) const;

  fmi2Status getBoolean(const fmi2ValueReference *vr, size_t nvr,
                        fmi2Boolean *value) const;

  fmi2Status setDebugLogging(fmi2Boolean loggingOn, size_t nCategories,
                             const char *const categories[]) const;

  fmi2Status setReal(const fmi2ValueReference *vr, size_t nvr,
                     const fmi2Real *value);

  fmi2Status setInteger(const fmi2ValueReference *vr, size_t nvr,
                        const fmi2Integer *value);

  fmi2Status setBoolean(const fmi2ValueReference *vr, size_t nvr,
                        const fmi2Boolean *value);

  fmi2Status setString(const fmi2ValueReference *vr, size_t nvr,
                       const fmi2String *value);

private:
  const Slave *slave;
};

} // namespace pyfmu::fmi2
