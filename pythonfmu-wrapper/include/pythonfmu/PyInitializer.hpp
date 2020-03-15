#include <iostream>
#include <stdlib.h>

#include <Python.h>

#include "utility/utils.hpp"

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


        log->ok("initializing Python interpreter\n");
        Py_Initialize();


        const wchar_t *home = Py_GetPythonHome() ? Py_GetPythonHome() : L"";
        const wchar_t *path = Py_GetPath() ? Py_GetPath() : L"";

        std::string home_str = ws2s(std::wstring(home));
        std::string path_str = ws2s(std::wstring(path));

        log->ok(fmt::format("Python home is: {} and path is {}", home_str, path_str));

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
