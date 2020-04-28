#ifndef PYFMU_PYOBJECTWRAPPER_HPP
#define PYFMU_PYOBJECTWRAPPER_HPP

#include <string>
#include <memory>
#include <filesystem>

#include "pyfmu/common.hpp"

#include <fmt/ranges.h>

#include "fmi/fmi2TypesPlatform.h"
#include "pyfmu/fmi2PySlaveLogging.hpp"
#include "pyfmu/pyCompatability.hpp"

// Names of functions invoked on the slave
// FMI 2
#define PYFMU_FMI2SLAVE_SETUPEXPERIMENT "_setup_experiment"
#define PYFMU_FMI2SLAVE_ENTERINITIALIZATIONMODE "_enter_initialization_mode"
#define PYFMU_FMI2SLAVE_EXITINITIALIZATIONMODE "_exit_initialization_mode"
#define PYFMU_FMI2SLAVE_DOSTEP "_do_step"
#define PYFMU_FMI2SLAVE_RESET "_reset"
#define PYFMU_FMI2SLAVE_TERMINATE "_terminate"
#define PYFMU_FMI2SLAVE_SETDEBUGLOGGING "_set_debug_logging"
#define PYFMU_FMI2SLAVE_SETREAL "_set_real"
#define PYFMU_FMI2SLAVE_SETBOOLEAN "_set_boolean"
#define PYFMU_FMI2SLAVE_SETINTEGER "_set_integer"
#define PYFMU_FMI2SLAVE_SETSTRING "_set_string"
#define PYFMU_FMI2SLAVE_GETREAL "_get_real"
#define PYFMU_FMI2SLAVE_GETBOOLEAN "_get_boolean"
#define PYFMU_FMI2SLAVE_GETINTEGER "_get_integer"
#define PYFMU_FMI2SLAVE_GETSTRING "_get_string"
// LOGGING
#define PYFMU_FMI2SLAVE_GETLOGSIZE "_get_log_size"
#define PYFMU_FMI2SLAVE_POPLOGMESSAGES "_pop_log_messages"

// Log category
#define PYFMU_WRAPPER_LOG_CATEGORY "wrapper"

namespace pyfmu
{

class PyObjectWrapper
{

public:
    explicit PyObjectWrapper(const std::filesystem::path resources, Logger *logger);

    explicit PyObjectWrapper(PyObjectWrapper &&other);

    fmi2Status setupExperiment(fmi2Boolean toleranceDefined, fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime);

    fmi2Status enterInitializationMode();

    fmi2Status exitInitializationMode();

    fmi2Status doStep(fmi2Real currentTime, fmi2Real stepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint);

    fmi2Status reset();

    fmi2Status terminate();

    fmi2Status getInteger(const fmi2ValueReference *vr, std::size_t nvr, fmi2Integer *value) const;

    fmi2Status getReal(const fmi2ValueReference *vr, std::size_t nvr, fmi2Real *value) const;

    fmi2Status getString(const fmi2ValueReference *vr, std::size_t nvr, fmi2String *value) const;

    fmi2Status getBoolean(const fmi2ValueReference *vr, std::size_t nvr, fmi2Boolean *value) const;

    fmi2Status setDebugLogging(fmi2Boolean loggingOn, size_t nCategories, const char *const categories[]) const;

    fmi2Status setReal(const fmi2ValueReference *vr, std::size_t nvr, const fmi2Real *value);

    fmi2Status setInteger(const fmi2ValueReference *vr, std::size_t nvr, const fmi2Integer *value);

    fmi2Status setBoolean(const fmi2ValueReference *vr, std::size_t nvr, const fmi2Boolean *value);

    fmi2Status setString(const fmi2ValueReference *vr, std::size_t nvr, const fmi2String *value);

    ~PyObjectWrapper();

    PyObjectWrapper &operator=(PyObjectWrapper &&rhs);

private:
    PyObject *pModule_;
    PyObject *pClass_;
    PyObject *pInstance_;

    Logger *logger;
    PyMethodDef pCallbackDef;
    PyObject *pCallbackFunc;

    template <typename... Args>
    /**
     * @brief Invokes the specified FMI method on the slave using a format string and a list of arguments
     * 
     * @param name 
     * @param formatStr 
     * @return fmi2Status 
     */
    fmi2Status InvokeFmiOnSlave(const std::string &name, const std::string &formatStr, Args... args) const
    {
        logger->ok(PYFMU_WRAPPER_LOG_CATEGORY, "Calling: {}", name);

        PyObject *f = PyObject_CallMethod(pInstance_, name.c_str(), formatStr.c_str(), args...);

        if (f == nullptr)
        {
            auto err = get_py_exception();
            logger->fatal(PYFMU_WRAPPER_LOG_CATEGORY, "call to {} failed with exception : {}", name, err);
            return fmi2Fatal;
        }
        long ls = PyLong_AsLong(f);
        Py_DECREF(f);
        if (ls == -1)
        {
            logger->fatal(
                PYFMU_WRAPPER_LOG_CATEGORY,
                "call to {} was successful, but return value could not be converted into a long as expected : {}",
                name,
                get_py_exception());

            return fmi2Fatal;
        }

        if (ls < fmi2Status::fmi2OK || ls > fmi2Status::fmi2Pending)
        {
            logger->fatal(
                PYFMU_WRAPPER_LOG_CATEGORY,
                "call to setupExperiment was successful, return value was : {} a long as expected, but does not match any fmi2Status",
                ls);
            return fmi2Fatal;
        }

        fmi2Status s = static_cast<fmi2Status>(ls);
        return s;
    }

    /**
     * @brief Generic implementation of all fmiSetXXX functions
     * 
     * @tparam T 
     * @param build_formatter 
     * @param setter_name 
     * @param vr 
     * @param nvr 
     * @param values 
     * @return fmi2Status 
     */
    template <typename T>
    fmi2Status InvokeFmiSetXXXFunction(
        const std::string &setter_name,
        std::function<PyObject *(T value)> buildValueFunc,
        const fmi2ValueReference *vr,
        std::size_t nvr, const T *values) const
    {
        PyGIL g;

        std::vector<fmi2ValueReference> vrArray(vr, vr + nvr);
        std::vector<T> valuesArray(values, values + nvr);
        logger->ok(
            PYFMU_WRAPPER_LOG_CATEGORY,
            "Calling {} with value references: {} and values: {}", setter_name, vrArray, valuesArray);

        PyObject *vrs = PyList_New(nvr);
        PyObject *refs = PyList_New(nvr);
        for (int i = 0; i < nvr; i++)
        {
            PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
            PyList_SetItem(refs, i, buildValueFunc(values[i]));
        }

        auto status = InvokeFmiOnSlave(setter_name, "(OO)", vrs, refs);
        Py_DECREF(vrs);
        Py_DECREF(refs);
        return status;
    }

    /**
     * @brief Generic implementation of fmi2GetXXX functions.
     * 
     * @tparam T 
     * @param getter_name name of the getter function of the python object
     * @param buildFunc function used to build the elements of the list passed to the python
     * @param getterFunc function used to convert the return python object into C types
     * @param vr value references
     * @param nvr number of variables
     * @param values values which will be overwritten by the values read from the slave.
     * @return fmi2Status 
     */
    template <typename T>
    fmi2Status InvokeFmiGetXXXFunction(
        const std::string &getter_name,
        std::function<PyObject *()> buildFunc,
        std::function<T(PyObject *)> convertFunc,
        const fmi2ValueReference *vr,
        std::size_t nvr,
        T *values) const
    {

        std::vector<fmi2ValueReference> vrArray(vr, vr + nvr);
        std::vector<T> valuesArray(values, values + nvr);
        logger->ok(
            PYFMU_WRAPPER_LOG_CATEGORY,
            "Calling {} with value references: {} and values: {}", getter_name, vrArray, valuesArray);

        PyGIL g;

        PyObject *py_refs = PyList_New(nvr);
        PyObject *py_vals = PyList_New(nvr);
        for (int i = 0; i < nvr; i++)
        {
            PyList_SetItem(py_refs, i, Py_BuildValue("i", vr[i]));
            PyList_SetItem(py_vals, i, buildFunc());
        }

        auto status = InvokeFmiOnSlave(getter_name, "(OO)", py_refs, py_vals);

        if (status > fmi2Discard)
        {
            logger->ok(PYFMU_WRAPPER_LOG_CATEGORY,
                       "call executed but returned error: {}, with python exception: {}", status, get_py_exception());

            Py_DECREF(py_refs);
            Py_DECREF(py_vals);
            return status;
        }

        for (int i = 0; i < nvr; i++)
        {
            PyObject *value = PyList_GetItem(py_vals, i);

            if (value == nullptr)
            {
                logger->fatal("wrapper", "call executed and returned ok, but unable to convert results to appropriate c-types, python exception : {}", get_py_exception());
                return fmi2Fatal;
            }

            values[i] = convertFunc(value);
        }

        valuesArray = std::vector<T>(values, values + nvr);
        logger->ok(
            PYFMU_WRAPPER_LOG_CATEGORY,
            "Returned value references: {} and values: {}", vrArray, valuesArray);

        Py_DECREF(py_refs);
        Py_DECREF(py_vals);
        return status;
    }

    /**
     * @brief Import and instantiate slave class in the current Python interpreter.
     * 
     * Note that the module containing the slave class must be in the interpreters path. This can be calling sys.path.append('some_path') on the interpreter.
     * 
     * @param module_name 
     * @param main_class 
     * @return PyObject* 
     * 
     * Examples:
     * 
     * >> auto instance = instantiate_main_class('adder', 'Adder')
     */
    void instantiate_main_class(std::string module_name, std::string main_class);
};

} // namespace pyfmu

#endif //PYFMU_PYOBJECTWRAPPER_HPP