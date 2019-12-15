#include "Python.h"

#pragma once

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