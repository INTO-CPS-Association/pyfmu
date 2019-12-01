
#ifndef PYTHONFMU_PYOBJECTWRAPPER_HPP
#define PYTHONFMU_PYOBJECTWRAPPER_HPP

#include "fmi/fmi2TypesPlatform.h"
#include <Python.h>

namespace pythonfmu
{

class PyObjectWrapper
{

public:

    explicit PyObjectWrapper(const fmi2String resources);

    void setupExperiment(double startTime);

    void enterInitializationMode();

    void exitInitializationMode();

    bool doStep(double currentTime, double steSize);

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
};

} // namespace pythonfmu

#endif //PYTHONFMU_PYOBJECTWRAPPER_HPP
