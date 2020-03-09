
#include <Python.h>
#include <iostream>

#ifndef PYTHONFMU_PYTHONSTATE_HPP
#define PYTHONFMU_PYTHONSTATE_HPP

namespace pythonfmu
{

class PyInitializer
{
public:
    PyInitializer(Logger *log, std::wstring module_path = L"")
    {
        log->ok("Setting up module path\n");

        if (!module_path.empty())
        {
            log->ok("Using explicitly defined module path\n");
            Py_SetPath(module_path.c_str());
        }

        wchar_t *p = L"C:\\ProgramData\\Miniconda3\\Lib";
        Py_SetPath(p);
        log->ok("initializing Python interpreter\n");
        Py_Initialize();

        if (!Py_IsInitialized())
        {
            log->ok("Failed to initialize Python Interpreter");
            throw std::runtime_error("Failed to initialize Python interpreter");
        }

        log->ok("Python interpreter initialized");
    }

    ~PyInitializer()
    {
        Py_Finalize();
    }
};

} // namespace pythonfmu

#endif //PYTHONFMU_PYTHONSTATE_HPP
