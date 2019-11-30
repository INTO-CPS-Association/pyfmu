#define CATCH_CONFIG_MAIN
#include "catch.hpp"
#include <filesystem>

#include "pythonfmu/PyObjectWrapper.hpp"
#include "pythonfmu/PyInitializer.hpp"

using namespace std;
using namespace filesystem;
using namespace pythonfmu;


TEST_CASE("PyObjectWrapper")
{
    SECTION("FMUS")
    {
        path fmu_resource_path("resources/adder/");
        auto state = PyInitializer();

        SECTION("Adder")
        {
            auto wrapped = PyObjectWrapper(fmu_resource_path.string());
            
            unsigned int set_refs[] = {0,1};
            double set_vals[] = {5,10};
            wrapped.setReal(set_refs,2,set_vals);

            

            wrapped.doStep(0,1);

            unsigned int get_refs[] = {2};
            double get_vals[] = {0};
            wrapped.getReal(get_refs,1,get_vals);   


            REQUIRE(get_vals[0] == 15);
        }
    }
}
