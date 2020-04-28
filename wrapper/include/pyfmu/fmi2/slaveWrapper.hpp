#pragma once

#include <string>
#include <memory>
#include <filesystem>

#include "pybind11/embed.h"
#include "pybind11/stl.h"

#include <fmt/ranges.h>

#include "spec/fmi2/fmi2TypesPlatform.h"
#include "pyfmu/fmi2/logging.hpp"

// Log category
#define PYFMU_WRAPPER_LOG_CATEGORY "wrapper"

namespace pyfmu::fmi2
{

template <typename T>
using Values = const std::vector<T>;
using ValueReferences = Values<fmi2ValueReference>;
using RealValues = Values<fmi2Real>;
using BooleanValues = Values<bool>;
using IntegerValues = Values<fmi2Integer>;
using StringValues = Values<const std::string>;
namespace py = pybind11;

template <typename T>
using Fmi2GetterResult = std::tuple<Values<T>, fmi2Status>;

class SlaveWrapper
{

public:
    explicit SlaveWrapper(const std::filesystem::path resources, Logger *logger);

    fmi2Status setupExperiment(fmi2Boolean toleranceDefined,
                               fmi2Real tolerance,
                               fmi2Real startTime,
                               fmi2Boolean stopTimeDefined,
                               fmi2Real stopTime);

    fmi2Status enterInitializationMode();

    fmi2Status exitInitializationMode();

    fmi2Status doStep(fmi2Real currentTime,
                      fmi2Real stepSize,
                      fmi2Boolean noSetFMUStatePriorToCurrentPoint);

    fmi2Status reset();

    fmi2Status terminate();

    Fmi2GetterResult<fmi2Integer> getInteger(ValueReferences valueReferences) const noexcept;

    Fmi2GetterResult<fmi2Real> getReal(ValueReferences valueReferences) const noexcept;

    Fmi2GetterResult<fmi2String> getString(ValueReferences valueReferences) const noexcept;

    Fmi2GetterResult<fmi2Boolean> getBoolean(ValueReferences valueReferences) const noexcept;

    fmi2Status setDebugLogging(fmi2Boolean loggingOn, std::vector<std::string> loggingCategories) const noexcept;

    fmi2Status setReal(ValueReferences valueReferences, RealValues values) noexcept;

    fmi2Status setInteger(ValueReferences valueReferences, IntegerValues values) noexcept;

    fmi2Status setBoolean(ValueReferences valueReferences, BooleanValues values) noexcept;

    fmi2Status setString(ValueReferences valueReferences, StringValues values) noexcept;

    ~SlaveWrapper();

private:
    py::object slaveInstance;

    Logger *logger;
    PyMethodDef pCallbackDef;
    PyObject *pCallbackFunc;

    template <typename T>
    fmi2Status setXXXFunction(
        const std::string &setter_name,
        ValueReferences valueReferences,
        Values<T> values) noexcept
    {

        logger->ok(PYFMU_WRAPPER_LOG_CATEGORY, "Setting the variables: {} to: {}", valueReferences, values);
        return 0;
    }

    template <typename T>
    Fmi2GetterResult<T> getXXXFunction(
        ValueReferences references,
        const std::string &type_hint) noexcept
    {
        logger->ok(PYFMU_WRAPPER_LOG_CATEGORY, "Getting values of the variables: {}", valueReferences);

        try
        {
            auto res = slaveInstance.attr("_get_xxx")(references, type_hint);
            return res.cast<Fmi2GetterResults<T>>();
        }
        catch (const std::exception &e)
        {
            logger->log(fmi2Fatal, PYFMU_WRAPPER_LOG_CATEGORY, "read failed, an exception was raised: {}", e.what());
            return Fmi2GetterResult(nullptr, fmi2Fatal);
        };

        return results;
    }
};

} // namespace pyfmu::fmi2