#define CATCH_CONFIG_MAIN

#include "catch2/catch.hpp"
#include <filesystem>

#include "fmi/fmi2Functions.h"

using namespace std;
using namespace filesystem;

void logger(void *env, const char *str1, fmi2Status s, const char *str2,
            const char *str3, ...) {}

void stepFinished(fmi2ComponentEnvironment componentEnvironment, fmi2Status status)
{

}

TEST_CASE("PyObjectWrapper")
{
  SECTION("multiplier") {
    //auto p = path("examples") / "multiplier" / "resources";

    path p = path("file:///home/clegaard/Desktop/python2fmu/pythonfmu-wrapper/examples/multiplier/resources");

    const char *resources_path = p.c_str();

    fmi2CallbackFunctions callbacks = {.logger = logger,
                                       .allocateMemory = calloc,
                                       .freeMemory = free,
                                       .stepFinished = stepFinished,
                                       .componentEnvironment = nullptr};

    fmi2Component c =
        fmi2Instantiate("multiplier", fmi2Type::fmi2CoSimulation, "check?",
                        resources_path, &callbacks, fmi2False, fmi2True);

    REQUIRE(c != nullptr);

    fmi2Real start_time = 0;
    fmi2Real end_time = 10;
    fmi2Real step_size = 0.1;

    fmi2Status s;

    s = fmi2SetupExperiment(c, fmi2False, 0.0, start_time, fmi2True, end_time);
    REQUIRE(s == fmi2OK);

    unsigned int set_refs[] = {0, 1};
    double set_vals[] = {5, 10};
    s = fmi2SetReal(c, set_refs, 2, set_vals);
    REQUIRE(s == fmi2OK);

    unsigned int get_refs[] = {2};
    double get_vals[] = {0};
    s = fmi2GetReal(c, get_refs, 1, get_vals);
    REQUIRE(s == fmi2OK);
    REQUIRE(get_vals[0] == 0);

    s = fmi2DoStep(c, 0, 1, false);
    REQUIRE(s == fmi2OK);

    s = fmi2GetReal(c, get_refs, 1, get_vals);
    REQUIRE(s == fmi2OK);
    REQUIRE(get_vals[0] == 50);
  }
}