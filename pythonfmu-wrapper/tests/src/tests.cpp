#include <string>
#include <iostream>
// #include "pythonfmu/PyObjectWrapper.hpp"
// #include "pythonfmu/PyState.hpp"
#include <string>
#include "Python.h"
#include "foo.hpp"

// using namespace pythonfmu;
using namespace std;

int main(int argc, char **argv)
{

    const wchar_t *python_path = L"C:\\ProgramData\\Miniconda3\\Lib";
    Py_SetPath(python_path);
    auto test = Py_GetPath();
    Py_Initialize();

    std::string path = "resources/adder/";
    // PyObjectWrapper wrapper(path);
    foo();
    // if (!Py_IsInitialized)
    //     auto test = 0;

    return 0;
}