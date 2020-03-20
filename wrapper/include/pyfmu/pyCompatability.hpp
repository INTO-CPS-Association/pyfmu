#ifndef PYCOMPATABILITY_HPP
#define PYCOMPATABILITY_HPP

/**
 * @file pyCompatability.hpp
 * @author Christian Møldrup Legaard (cml@eng.au.dk)
 * @brief Provides functions missing in the stable Python API
 * @version 0.0.1
 * @date 2020-03-17
 * 
 * @copyright Copyright (c) 2020
 * 
 */

#include <Python.h>

#include "utils.hpp"

namespace pyfmu
{

/**
 * @brief defines replacements for several functions unavailable in the stable python API
 * 
 */
namespace pyCompat
{

/**
 * @brief Replacement for PyRun_SimpleString not present in the stable API
 * 
 * @param command 
 * @return int -1 on failure, 0 otherwise
 */
static inline int PyRun_SimpleString(const char *command)
{
    PyObject *globals, *code, *result;

    globals = PyDict_New();
    PyDict_SetItemString(globals, "__builtins__", PyEval_GetBuiltins());

    code = Py_CompileString(command, "", Py_file_input);
    if (!code)
    {
        PyErr_Print();
        return 0;
    }

    result = PyEval_EvalCode(code, globals, 0);
    Py_DECREF(code);
    if (!result)
    {
        PyErr_Print();
        return -1;
    }
    else
    {
        Py_DECREF(result);
        return 0;
    }
}

static inline const char *PyUnicode_AsUTF8(PyObject *object)
{
    wchar_t *wchar_str = PyUnicode_AsWideCharString(object, nullptr);
    std::string str = ws2s(wchar_str);
    PyMem_Free(wchar_str);

    char *cstr = new char[str.length() + 1];
    str.copy(cstr, str.length() + 1);

    return cstr;
}
} // namespace pyCompat

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
    explicit PyGIL() : state(PyGILState_Ensure())
    {
    }

    ~PyGIL()
    {
        PyGILState_Release(this->state);
    }

private:
    PyGILState_STATE state;
};

} // namespace pyfmu

#endif // PYCOMPATABILITY_PY