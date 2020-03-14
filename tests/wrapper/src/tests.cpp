#define CATCH_CONFIG_MAIN

#include <filesystem>

#include "catch2/catch.hpp"
#include "fmt/format.h"
#include "spdlog/spdlog.h"

#include "fmi/fmi2Functions.h"
#include "example_finder.hpp"
#include "utility/utils.hpp"

using namespace std;
using namespace filesystem;
using namespace fmt;
namespace fs = std::filesystem;

void logger(void *env, const char *str1, fmi2Status s, const char *str2,
            const char *str3, ...)
{
  //spdlog::info(str1);
}

void stepFinished(fmi2ComponentEnvironment componentEnvironment, fmi2Status status)
{
}





TEST_CASE("PyObjectWrapper")
{
  spdlog::set_level(spdlog::level::debug); // Set global log level to debug

  SECTION("adder")
  {

    auto a = ExampleArchive("Adder");
    string resources_uri = a.getResourcesURI();
    const char *resources_cstr = resources_uri.c_str();


    fmi2CallbackFunctions callbacks = {.logger = logger,
                                       .allocateMemory = calloc,
                                       .freeMemory = free,
                                       .stepFinished = stepFinished,
                                       .componentEnvironment = nullptr};

    fmi2Component c = fmi2Instantiate("adder", fmi2Type::fmi2CoSimulation, "check?", resources_cstr, &callbacks, fmi2False, fmi2True);

    REQUIRE(c != nullptr);

    fmi2Real start_time = 0;
    fmi2Real end_time = 10;
    fmi2Real step_size = 0.1;

    fmi2Status s;
    const char* categories[] = {"logAll"};
    

    s = fmi2SetupExperiment(c, fmi2False, 0.0, start_time, fmi2True, end_time);
    REQUIRE(s == fmi2OK);
    s = fmi2EnterInitializationMode(c);
    REQUIRE(s == fmi2OK);
    s = fmi2ExitInitializationMode(c);
    REQUIRE(s == fmi2OK);
    s = fmi2SetDebugLogging(c,true,1,categories);
    REQUIRE(s == fmi2OK);
    fmi2DoStep(c,0,1,false);
    REQUIRE(s == fmi2OK);

    unsigned int set_refs[] = {1, 2};
    double set_vals[] = {5, 10};
    s = fmi2SetReal(c, set_refs, 2, set_vals);
    REQUIRE(s == fmi2OK);

    unsigned int get_refs[] = {0};
    double get_vals[] = {0};
    s = fmi2GetReal(c, get_refs, 1, get_vals);
    REQUIRE(s == fmi2OK);
    REQUIRE(get_vals[0] == 0);

    s = fmi2DoStep(c, 0, 1, false);
    REQUIRE(s == fmi2OK);

    s = fmi2GetReal(c, get_refs, 1, get_vals);
    REQUIRE(s == fmi2OK);
    REQUIRE(get_vals[0] == 15);
  }

  

}

/**
 * @brief Tests the logging mechanism implemented in the wrapper.
 * 
 * The two main areas are:
 * 
 * 1. Only messages the active log categories are logged
 * 2. Errors from originating from failure in the c-to-python call interface are logged.
 * 3. Errors originating from inside the FMU are also logged.
 */
TEST_CASE("Logging")
{
  SECTION("LoggerFMU")
  {
    ExampleArchive a("LoggerFMU");

    string resources_uri = a.getResourcesURI();
    const char *resources_cstr = resources_uri.c_str();

    spdlog::info("resources as cstr {}", resources_cstr);

    fmi2CallbackFunctions callbacks = {.logger = logger,
                                       .allocateMemory = calloc,
                                       .freeMemory = free,
                                       .stepFinished = stepFinished,
                                       .componentEnvironment = nullptr};

    fmi2Component c = fmi2Instantiate("logger", fmi2Type::fmi2CoSimulation, "check?", resources_cstr, &callbacks, fmi2False, fmi2True);

    REQUIRE(c != nullptr);

    fmi2Real start_time = 0;
    fmi2Real end_time = 10;
    fmi2Real step_size = 0.1;

    int s = 0;
    const char* categories[] = {"logAll","test"};
    s = fmi2SetDebugLogging(c,true,1,categories);
    REQUIRE(s == fmi2OK);
    fmi2DoStep(c,0,1,false);
    REQUIRE(s == fmi2OK);
    fmi2DoStep(c,0,1,false);
    REQUIRE(s == fmi2OK);
  }
}

/**
 * @brief 
 * Tests related to the initialisation and deallocation of FMUs.
 * 
 * @details The targets are the fmi functions used to allocate and deallocate FMUs:
 * * fmi2Instantiate
 * * fmi2FreeInstance
 * * fmi2FreeState
 */
TEST_CASE("Instantiation and Deallocation")
{
  SECTION("fmi2instantiate_calledMultipleTimesWithDifferentInstanceNames_OK")
  {
    auto archive = ExampleArchive("Adder");
    string resources_uri = archive.getResourcesURI();
    const char *resources_cstr = resources_uri.c_str();

    fmi2CallbackFunctions callbacks = {.logger = logger,
                                       .allocateMemory = calloc,
                                       .freeMemory = free,
                                       .stepFinished = stepFinished,
                                       .componentEnvironment = nullptr};

    fmi2Component a = fmi2Instantiate("a", fmi2Type::fmi2CoSimulation, "check?",
                                      resources_cstr, &callbacks, fmi2False, fmi2True);

    fmi2Component b = fmi2Instantiate("b", fmi2Type::fmi2CoSimulation, "check?",
                                      resources_cstr, &callbacks, fmi2False, fmi2True);

    REQUIRE(true);
  }
}


/**
 * @brief Tests the URI parsing on different platforms.
 * 
 */
TEST_CASE("URI Parsing")
{


  SECTION("parses_valid_uri")
  {
    
    
    #ifdef WIN32
    // Windows uses drive letters, e.g. C:
    string uri = "file:///C:/somedir/resources";
    string expected = "C:\\somedir\\resources";
    #else
    // Linux does not use drive letters
    string uri = "file:///somedir/resources";
    string expected = "/somedir/resources";
    #endif
    
    string actual = getPathFromFileUri(uri).string();

    REQUIRE(actual == expected);
  }

  SECTION("Does not accept other schemes than file")
  {

    REQUIRE_THROWS([]() {
      string invalid_uri = "otherscheme:///C:/somedir/resources";

      getPathFromFileUri(invalid_uri);
    }());
  }

}
