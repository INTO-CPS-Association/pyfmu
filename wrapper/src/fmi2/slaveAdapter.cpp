#include <assert.h>

#include "pyfmu/fmi2/slaveAdapter.hpp"

template <typename T>
const std::vector<T> to_vector(const T *values, size_t size) {
  return std::vector<T>(values, values + size);
}

template <typename T> void copy_to(const std::vector<T> &src, T *dst) {
  for (int i = 0; i < src.size(); ++i)
    dst[i] = src[i];
}

namespace pyfmu::fmi2 {

SlaveAdapter::SlaveAdapter(Slave *slave, Logger *logger)
    : slave(slave), logger(logger) {}

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

fmi2Status SlaveAdapter::getReal(const fmi2ValueReference *vr, size_t nvr,
                                 fmi2Real *value) {
  try {
    const auto references = to_vector(vr, nvr);
    auto result = slave->getReal(references);

    assert(result.values.size() == nvr);

    for (int i = 0; i < nvr; ++i)
      value[i] = result.values[i];

    return result.status;

  } catch (const std::exception &e) {
    logger->fatal("Unable to get real, an exception was raised: {}", e.what());
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::getInteger(const fmi2ValueReference *vr, size_t nvr,
                                    fmi2Integer *value) {

  try {
    const auto references = to_vector(vr, nvr);

    auto result = slave->getInteger(references);
    assert(result.values.size() == nvr);
    copy_to(result.values, value);

    return result.status;

  } catch (const std::exception &) {
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::getString(const fmi2ValueReference *vr, size_t nvr,
                                   fmi2String *value) {
  try {
    const auto references = to_vector(vr, nvr);
    auto result = slave->getString(references);

    assert(result.values.size() == nvr);
    copy_to(result.values, value);

    return result.status;

  } catch (const std::exception &) {
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::getBoolean(const fmi2ValueReference *vr, size_t nvr,
                                    fmi2Boolean *value) {
  try {
    const auto references = to_vector(vr, nvr);
    auto result = slave->getBoolean(references);

    assert(result.values.size() == nvr);
    copy_to(result.values, value);

    return result.status;

  } catch (const std::exception &) {
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::setDebugLogging(fmi2Boolean loggingOn,
                                         size_t nCategories,
                                         const char *const categories[]) {
  try {
    std::vector<fmi2String> values(categories, categories + nCategories);
    return slave->setDebugLogging(loggingOn, values);
  } catch (const std::exception &e) {
    logger->fatal(
        "wrapper",
        "Failed to set logging categories, an exception was raised: {}",
        e.what());
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::setReal(const fmi2ValueReference *vr, size_t nvr,
                                 const fmi2Real *value) {
  try {
    const auto references = to_vector(vr, nvr);
    const auto values = to_vector(value, nvr);
    return slave->setReal(references, values);
  } catch (const std::exception &) {
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::setInteger(const fmi2ValueReference *vr, size_t nvr,
                                    const fmi2Integer *value) {
  try {
    const auto references = to_vector(vr, nvr);
    const auto values = to_vector(value, nvr);
    return slave->setInteger(references, values);
  } catch (const std::exception &) {
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::setBoolean(const fmi2ValueReference *vr, size_t nvr,
                                    const fmi2Boolean *value) {
  try {
    const auto references = to_vector(vr, nvr);
    const auto values = to_vector(value, nvr);
    return slave->setBoolean(references, values);
  } catch (const std::exception &) {
    return fmi2Fatal;
  }
}

fmi2Status SlaveAdapter::setString(const fmi2ValueReference *vr, size_t nvr,
                                   const fmi2String *value) {
  try {
    const auto references = to_vector(vr, nvr);
    const auto values = to_vector(value, nvr);
    return slave->setString(references, values);
  } catch (const std::exception &) {
    return fmi2Fatal;
  }
}
} // namespace pyfmu::fmi2