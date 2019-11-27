#include <string>
#include <iostream>

#include "pythonfmu/PyObjectWrapper.hpp"
#include "pythonfmu/PyState.hpp"
#include "foo.hpp"

#include <string>

using namespace pythonfmu;
using namespace std;

int main(int argc, char **argv)
{

    const wchar_t *python_path = L"C:\\ProgramData\\Miniconda3\\Lib";
    // Py_SetPath(python_path);
    // auto test = Py_GetPath();
    // Py_Initialize();

    // PyState state();
    const std::string path = "resources/adder/";
    // PyObjectWrapper wrapper("test");
    // if (!Py_IsInitialized)
    //     auto test = 0;

    foo();

    printf("Foo executed");

    return 0;
}