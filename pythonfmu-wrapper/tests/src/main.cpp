#include "pythonfmu/PyObjectWrapper.hpp"
#include "foo.hpp"
#include <string>

int main(int argc, char **argv)
{

    const std::string adderConfig = "resources/adder/script_config.py";
    //pythonfmu::PyObjectWrapper adder(adderConfig);
    foo(10);
    //test();
    //pythonfmu::PyObjectWrapper t();
    return 0;
}