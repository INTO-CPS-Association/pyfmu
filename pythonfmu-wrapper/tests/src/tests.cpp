#include <string>
#include <iostream>

#include "pythonfmu/PyObjectWrapper.hpp"
#include "pythonfmu/PyInitializer.hpp"
#include "foo.hpp"

#include <string>
#include <filesystem>

using namespace pythonfmu;
using namespace std;
using namespace filesystem;

int main(int argc, char **argv)
{

    // const wchar_t *python_path = L"C:\\ProgramData\\Miniconda3\\Lib";
    
    

    
    path fmu_resource_path("resources/adder/");
    
    auto state = PyInitializer();
    
        
    PyObjectWrapper(fmu_resource_path.string());

    

    printf("Foo executed");

    return 0;
}