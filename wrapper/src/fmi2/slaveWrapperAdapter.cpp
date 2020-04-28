#include "pyfmu/fmi2/slaveWrapperAdapter.hpp"

namespace pyfmu::fmi2
{

fmi2Status SlaveWrapperAdapter::setupExperiment(fmi2Boolean toleranceDefined, fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime)
{
    return fmi2Fatal;
}

fmi2Status SlaveWrapperAdapter::enterInitializationMode() { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::exitInitializationMode() { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::doStep(fmi2Real currentTime, fmi2Real stepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::reset() { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::terminate() { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::getInteger(const fmi2ValueReference *vr, size_t nvr, fmi2Integer *value) const { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::getReal(const fmi2ValueReference *vr, size_t nvr, fmi2Real *value) const { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::getString(const fmi2ValueReference *vr, size_t nvr, fmi2String *value) const { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::getBoolean(const fmi2ValueReference *vr, size_t nvr, fmi2Boolean *value) const { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::setDebugLogging(fmi2Boolean loggingOn, size_t nCategories, const char *const categories[]) const { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::setReal(const fmi2ValueReference *vr, size_t nvr, const fmi2Real *value) { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::setInteger(const fmi2ValueReference *vr, size_t nvr, const fmi2Integer *value) { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::setBoolean(const fmi2ValueReference *vr, size_t nvr, const fmi2Boolean *value) { return fmi2Fatal; }

fmi2Status SlaveWrapperAdapter::setString(const fmi2ValueReference *vr, size_t nvr, const fmi2String *value) { return fmi2Fatal; }
} // namespace pyfmu::fmi2