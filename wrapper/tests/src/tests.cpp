#define CATCH_CONFIG_MAIN

#include <filesystem>
#include <map>

#include "catch2/catch.hpp"
#include "fmt/format.h"
#include "spdlog/spdlog.h"

#include "fmi/fmi2Functions.h"
#include "example_finder.hpp"
#include "pyfmu/utils.hpp"

using namespace std;
using namespace filesystem;
using namespace fmt;
namespace fs = std::filesystem;


const std::map<fmi2Status,spdlog::level::level_enum>fmi_to_spdlog = {
    {fmi2OK,spdlog::level::info},
    {fmi2Warning,spdlog::level::warn},
    {fmi2Discard,spdlog::level::warn},
    {fmi2Error,spdlog::level::err},
    {fmi2Error,spdlog::level::critical},
    {fmi2Pending,spdlog::level::info}
};

void logger(void *env, const char *instance, fmi2Status status, const char *category,
            const char *message, ...)
{
  
  auto cat = fmi_to_spdlog.at(status);
  spdlog::log(cat,"{}:{}:{}:{}",instance,status,category,message);
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
    
    s = fmi2SetDebugLogging(c,true,1,categories);
    REQUIRE(s == fmi2OK);
    s = fmi2SetupExperiment(c, fmi2False, 0.0, start_time, fmi2True, end_time);
    REQUIRE(s == fmi2OK);
    s = fmi2EnterInitializationMode(c);
    REQUIRE(s == fmi2OK);
    s = fmi2ExitInitializationMode(c);
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

  SECTION("FmiTypes")
  {

    auto a = ExampleArchive("FmiTypes");
    string resources_uri = a.getResourcesURI();
    const char *resources_cstr = resources_uri.c_str();


    fmi2CallbackFunctions callbacks = {.logger = logger,
                                       .allocateMemory = calloc,
                                       .freeMemory = free,
                                       .stepFinished = stepFinished,
                                       .componentEnvironment = nullptr};

    fmi2Component c = fmi2Instantiate("fmu", fmi2Type::fmi2CoSimulation, "check?", resources_cstr, &callbacks, fmi2False, fmi2True);

    REQUIRE(c != nullptr);

    fmi2Real start_time = 0;
    fmi2Real end_time = 10;
    fmi2Real step_size = 0.1;

    fmi2Status s;
    const char* categories[] = {"logAll"};
    
    s = fmi2SetDebugLogging(c,true,1,categories);
    REQUIRE(s == fmi2OK);
    s = fmi2SetupExperiment(c, fmi2False, 0.0, start_time, fmi2True, end_time);
    REQUIRE(s == fmi2OK);
    s = fmi2EnterInitializationMode(c);
    REQUIRE(s == fmi2OK);
    s = fmi2ExitInitializationMode(c);
    REQUIRE(s == fmi2OK);
    fmi2DoStep(c,0,1,false);
    REQUIRE(s == fmi2OK);

    // Ordering is
    // real_in, real_out, integer_in, integer_out, ...
    {
      fmi2ValueReference set_refs[] = {0};
      fmi2Real set_vals[] = {1};
      s = fmi2SetReal(c, set_refs, 1, set_vals);
      REQUIRE(s == fmi2OK);

      s = fmi2DoStep(c,0,1,false);
      REQUIRE(s == fmi2OK);

      fmi2ValueReference get_refs[] = {1};
      fmi2Real get_vals[] = {0};
      s = fmi2GetReal(c,get_refs,1,get_vals);
      REQUIRE(s == fmi2OK);
      REQUIRE(get_vals[0] == 1);
    }

    // integer_in, integer_out
    {
      fmi2ValueReference set_refs[] = {2};
      fmi2Integer set_vals[] = {1};
      s = fmi2SetInteger(c, set_refs, 1, set_vals);
      REQUIRE(s == fmi2OK);

      s = fmi2DoStep(c,0,1,false);
      REQUIRE(s == fmi2OK);

      fmi2ValueReference get_refs[] = {3};
      fmi2Integer get_vals[] = {0};
      s = fmi2GetInteger(c,get_refs,1,get_vals);
      REQUIRE(s == fmi2OK);
      REQUIRE(get_vals[0] == 1);
    }

    // boolean_in, boolean_out
    {
      fmi2ValueReference set_refs[] = {4};
      fmi2Boolean set_vals[] = {true};
      s = fmi2SetBoolean(c, set_refs, 1, set_vals);
      REQUIRE(s == fmi2OK);

      s = fmi2DoStep(c,0,1,false);
      REQUIRE(s == fmi2OK);

      fmi2ValueReference get_refs[] = {5};
      fmi2Boolean get_vals[] = {0};
      s = fmi2GetBoolean(c,get_refs,1,get_vals);
      REQUIRE(s == fmi2OK);
      REQUIRE(get_vals[0] == true);
    }
    
      // string_in, string_out
    {
      fmi2ValueReference set_refs[] = {6};
      fmi2String set_vals[] = {"hello world!"};
      s = fmi2SetString(c, set_refs, 1, set_vals);
      REQUIRE(s == fmi2OK);

      s = fmi2DoStep(c,0,1,false);
      REQUIRE(s == fmi2OK);

      fmi2ValueReference get_refs[] = {7};
      fmi2String get_vals[] = {0};
      s = fmi2GetString(c,get_refs,1,get_vals);
      REQUIRE(s == fmi2OK);
      REQUIRE(string(get_vals[0]) == "hello world!");
    }
    
    
    

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
