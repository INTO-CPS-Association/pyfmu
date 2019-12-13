
#ifndef PYTHONFMU_PYOBJECTWRAPPER_HPP
#define PYTHONFMU_PYOBJECTWRAPPER_HPP

#include "fmi/fmi2TypesPlatform.h"
#include "Python.h"
#include "Logger.hpp"
#include <string>
#include <memory>

extern "C"
{
    int foo();
}


namespace pythonfmu
{

class PyObjectWrapper
{

public:

    explicit PyObjectWrapper(const fmi2String resources, std::unique_ptr<Logger> logger);

    void setupExperiment(double startTime);

    void enterInitializationMode();

    void exitInitializationMode();

    bool doStep(double currentTime, double stepSize);

    void reset();

    void terminate();

    void getInteger(const fmi2ValueReference *vr, std::size_t nvr, fmi2Integer *value) const;

    void getReal(const fmi2ValueReference *vr, std::size_t nvr, fmi2Real *value) const;

    void getString(const fmi2ValueReference *vr, std::size_t nvr, fmi2String *value) const;

    void getBoolean(const fmi2ValueReference *vr, std::size_t nvr, fmi2Boolean *value) const;

    void setReal(const fmi2ValueReference *vr, std::size_t nvr, const fmi2Real *value);

    void setInteger(const fmi2ValueReference *vr, std::size_t nvr, const fmi2Integer *value);

    void setBoolean(const fmi2ValueReference *vr, std::size_t nvr, const fmi2Boolean *value);

    void setString(const fmi2ValueReference *vr, std::size_t nvr, const fmi2String *value);

    ~PyObjectWrapper();

private:
    PyObject *pModule_;
    PyObject *pClass_;
    PyObject *pInstance_;

    std::unique_ptr<Logger> logger;

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

};

} // namespace pythonfmu

#endif //PYTHONFMU_PYOBJECTWRAPPER_HPP
