#include "Python.h"

#pragma once

/**
 * @brief RAII wrapper which manages acquires and releases the "global interpreter lock" (GIL) used py CPython.
 * 
 * This is necessary to ensure safe operation if the process calling the FMU also uses Python.
 * The lock MUST be taken before any calls to the Python c-api.
 * 
 * @note
 * See CPythons c-api documentation for details:
 * https://docs.python.org/3/c-api/init.html#thread-state-and-the-global-interpreter-lock
 * 
 * @example
 * PyGIL g;
 * f = PyObject_CallMethod(instance,"foo","i",10)
 */
class PyGIL
{

    public:

    explicit PyGIL(): state(PyGILState_Ensure()) 
    {
        
    }

    ~PyGIL()
    {
        PyGILState_Release(this->state);
    }
    
    private:
    
    PyGILState_STATE state;
};