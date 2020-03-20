
#ifndef PYFMU_EXPORT_PYEXCEPTION_HPP
#define PYFMU_EXPORT_PYEXCEPTION_HPP

#include <Python.h>
#include <iostream>
#include <sstream>

#include "utility/utils.hpp"
#include "utility/py_compatability.hpp"

namespace pyfmu
{

inline std::string get_py_exception()
{
    auto err = PyErr_Occurred();

    if (err != nullptr)
    {

        PyObject *pExcType, *pExcValue, *pExcTraceback;
        PyErr_Fetch(&pExcType, &pExcValue, &pExcTraceback);

        std::ostringstream oss;
        oss << "Fatal py exception encountered: ";
        if (pExcValue != nullptr)
        {
            PyObject *pRepr = PyObject_Repr(pExcValue);
            oss << PyCompat::PyUnicode_AsUTF8(pRepr);
            Py_DECREF(pRepr);
        }
        else
        {
            oss << "unknown error";
        }

        PyErr_Clear();

        Py_XDECREF(pExcType);
        Py_XDECREF(pExcValue);
        Py_XDECREF(pExcTraceback);

        auto msg = oss.str();

        return msg;
    }
    else
    {
        return "";
    }
}

inline void handle_py_exception()
{
    throw std::runtime_error(get_py_exception().c_str());
}

} // namespace pyfmu
#endif
