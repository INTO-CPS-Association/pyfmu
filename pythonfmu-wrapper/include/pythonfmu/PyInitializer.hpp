
#include <Python.h>
#include <iostream>

#ifndef PYTHONFMU_PYTHONSTATE_HPP
#define PYTHONFMU_PYTHONSTATE_HPP

namespace pythonfmu
{

class PyInitializer
{
public:
    PyInitializer(std::wstring module_path = L"")
    {

        printf("Setting up module path\n");
        if (!module_path.empty())
        {
            printf("Module path not empty\n");
            Py_SetPath(module_path.c_str());
        }

        wchar_t *p = L"C:\\ProgramData\\Miniconda3\\Lib";
        Py_SetPath(p);
        printf("initializing Python interpreter\n");
        Py_Initialize();

        if (!Py_IsInitialized())
        {
            printf("Could not instantiate Python Interpreter");
            throw std::runtime_error("Failed to initialize Python interpreter");
        }
    }

    ~PyInitializer()
    {
        Py_Finalize();
    }
};

} // namespace pythonfmu

#endif //PYTHONFMU_PYTHONSTATE_HPP
