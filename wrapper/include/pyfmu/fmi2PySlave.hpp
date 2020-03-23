#ifndef PYFMU_PYOBJECTWRAPPER_HPP
#define PYFMU_PYOBJECTWRAPPER_HPP

#include <string>
#include <memory>
#include <filesystem>

#include <Python.h>

#include "fmi/fmi2TypesPlatform.h"
#include "pyfmu/fmi2PySlaveLogging.hpp"
#include "pyfmu/pyCompatability.hpp"

#define PYFMU_FMI2SLAVE_SETUPEXPERIMENT "_setup_experiment"
#define PYFMU_FMI2SLAVE_ENTERINITIALIZATIONMODE "_enter_initialization_mode"
#define PYFMU_FMI2SLAVE_EXITINITIALIZATIONMODE "__exit_initialization_mode"
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

namespace pyfmu
{


class PyObjectWrapper
{

public:
    explicit PyObjectWrapper(const std::filesystem::path resources, Logger *logger);

    explicit PyObjectWrapper(PyObjectWrapper &&other);

    fmi2Status setupExperiment(fmi2Boolean toleranceDefined,fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime);

    fmi2Status enterInitializationMode();

    fmi2Status exitInitializationMode();

    fmi2Status doStep(fmi2Real currentTime, fmi2Real stepSize,fmi2Boolean noSetFMUStatePriorToCurrentPoint);

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

    /**
     * @brief Import and instantiate main class in the current Python interpreter.
     * 
     * Note that the module containing the main class must be in the interpreters path. This can be calling sys.path.append('some_path') on the interpreter.
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

    /**
    * @brief Pass log messages generated by the Python code to the FMI interface using the log callback function.
    * 
    * @details Two methods are __get_log_size__ and __get_log_messages__ are defined in the FMI2Slave classes.
    */
    void propagate_python_log_messages() const;


    //fmi2Status call_py_func(std::string function_name, PyObject* args, PyObject* kwargs);
};

} // namespace pyfmu

#endif //PYFMU_PYOBJECTWRAPPER_HPP