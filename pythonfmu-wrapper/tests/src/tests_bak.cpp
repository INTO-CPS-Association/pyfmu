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

        
    auto wrapped = PyObjectWrapper(fmu_resource_path.string());

    
    

    unsigned int set_refs[] = {0,1};
    double set_vals[] = {5,10};

    wrapped.setReal(set_refs,2,set_vals);

    unsigned int get_refs[] = {2};
    double get_vals[] = {0};

    wrapped.doStep(0,1);
    
    wrapped.getReal(get_refs,1,get_vals);

    

    cout << "Values are: " << get_vals[0] << std::endl;

    return 0;
}