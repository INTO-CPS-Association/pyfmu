#include "pyfmu/fmi2/slaveAdapter.hpp"

namespace pyfmu::fmi2 {

SlaveAdapter::SlaveAdapter(Slave *slave) : slave(slave) {}

SlaveAdapter::~SlaveAdapter() { delete slave; }

fmi2Status SlaveAdapter::setupExperiment(fmi2Boolean toleranceDefined,
                                         fmi2Real tolerance, fmi2Real startTime,
                                         fmi2Boolean stopTimeDefined,
                                         fmi2Real stopTime) {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::enterInitializationMode() { return fmi2Fatal; }

fmi2Status SlaveAdapter::exitInitializationMode() { return fmi2Fatal; }

fmi2Status SlaveAdapter::doStep(fmi2Real currentTime, fmi2Real stepSize,
                                fmi2Boolean noSetFMUStatePriorToCurrentPoint) {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::reset() { return fmi2Fatal; }

fmi2Status SlaveAdapter::terminate() { return fmi2Fatal; }

fmi2Status SlaveAdapter::getInteger(const fmi2ValueReference *vr, size_t nvr,
                                    fmi2Integer *value) const {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::getReal(const fmi2ValueReference *vr, size_t nvr,
                                 fmi2Real *value) const {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::getString(const fmi2ValueReference *vr, size_t nvr,
                                   fmi2String *value) const {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::getBoolean(const fmi2ValueReference *vr, size_t nvr,
                                    fmi2Boolean *value) const {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::setDebugLogging(fmi2Boolean loggingOn,
                                         size_t nCategories,
                                         const char *const categories[]) const {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::setReal(const fmi2ValueReference *vr, size_t nvr,
                                 const fmi2Real *value) {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::setInteger(const fmi2ValueReference *vr, size_t nvr,
                                    const fmi2Integer *value) {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::setBoolean(const fmi2ValueReference *vr, size_t nvr,
                                    const fmi2Boolean *value) {
  return fmi2Fatal;
}

fmi2Status SlaveAdapter::setString(const fmi2ValueReference *vr, size_t nvr,
                                   const fmi2String *value) {
  return fmi2Fatal;
}
} // namespace pyfmu::fmi2