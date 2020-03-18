#include "utility/py_compatability.hpp"


int PyCompat::PyRun_SimpleString(const char* command)
{
    PyObject *globals, *code, *result;

    globals = PyDict_New();
    PyDict_SetItemString(globals,"__builtins__",PyEval_GetBuiltins());

    code = Py_CompileString(command, "", Py_file_input);
    if(!code) {
        PyErr_Print();
        return 0;
    }
    
    result = PyEval_EvalCode(code,globals,0);
    Py_DECREF(code);
    if(!result) {
        PyErr_Print();
        return -1;
    } else {
        Py_DECREF(result);
        return 0;
    }
}

const char* PyCompat::PyUnicode_AsUTF8(PyObject* object)
{
    wchar_t *wchar_str = PyUnicode_AsWideCharString(object, nullptr);
    std::string str = ws2s(wchar_str);
    PyMem_Free(wchar_str);

    char* cstr = new char[str.length()+1];
    str.copy(cstr,str.length()+1);

    std::string test(cstr);

    return cstr;
}