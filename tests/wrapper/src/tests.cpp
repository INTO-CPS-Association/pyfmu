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
  spdlog::info(str1);
}

void stepFinished(fmi2ComponentEnvironment componentEnvironment, fmi2Status status)
{
}

/*
TEST_CASE("fmifunctions")
{
  spdlog::set_level(spdlog::level::debug); // Set global log level to debug

  SECTION("fmi2instantiate_calledMultipleTimes_OK")
  {

    string resources_path = get_resource_uri("Adder");
    auto resources_path_cstr = resources_path.c_str();
    spdlog::info("path to resources is:\n{}\n", resources_path);

    fmi2CallbackFunctions callbacks = {.logger = logger,
                                       .allocateMemory = calloc,
                                       .freeMemory = free,
                                       .stepFinished = stepFinished,
                                       .componentEnvironment = nullptr};

    fmi2Component a = fmi2Instantiate("a", fmi2Type::fmi2CoSimulation, "check?",
                                      resources_path_cstr, &callbacks, fmi2False, fmi2True);

    fmi2Component b = fmi2Instantiate("b", fmi2Type::fmi2CoSimulation, "check?",
                                      resources_path_cstr, &callbacks, fmi2False, fmi2True);

    REQUIRE(true);
  }
}
*/

TEST_CASE("PyObjectWrapper")
{

  SECTION("adder")
  {

    auto a = ExampleArchive("Adder");
    spdlog::info("Exported example project Adder, to path: {}", a.getRoot().string());

    string resources_uri = a.getResourcesURI();
    const char *resources_cstr = resources_uri.c_str();

    spdlog::info("resources as cstr {}", resources_cstr);

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

#ifdef WIN32
TEST_CASE("URI parsing on windows")
{

  SECTION("parses_valid_uri")
  {
    string uri = "file:///C:/somedir/resources";
    string expected = "C:\\somedir\\resources";

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
#endif