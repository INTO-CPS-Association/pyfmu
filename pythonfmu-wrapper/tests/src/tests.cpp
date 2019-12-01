#define CATCH_CONFIG_MAIN
#include "catch.hpp"
#include <filesystem>

#include "pythonfmu/PyInitializer.hpp"
#include "pythonfmu/PyObjectWrapper.hpp"

#include "fmi/fmi2Functions.h"

using namespace std;
using namespace filesystem;
using namespace pythonfmu;

void logger(void *env, const char *str1, fmi2Status s, const char *str2,
            const char *str3, ...) {}

TEST_CASE("PyObjectWrapper") {
  /*
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
  */

  SECTION("fmi") {


    const char* resources_path = (path("resources") / "adder").c_str();

    fmi2CallbackFunctions callbacks = {.logger = logger,
                                       .allocateMemory = calloc,
                                       .freeMemory = free,
                                       .stepFinished = nullptr,
                                       .componentEnvironment = nullptr};

    fmi2Component c = fmi2Instantiate("adder", fmi2Type::fmi2CoSimulation, "check?", resources_path,
                             &callbacks, fmi2False, fmi2True);

    REQUIRE(c != nullptr);

    fmi2Real start_time = 0;
    fmi2Real end_time = 10;
    fmi2Real step_size = 0.1;

    fmi2SetupExperiment(c, fmi2False, 0.0, start_time, fmi2True, end_time);

    unsigned int set_refs[] = {0, 1};
    double set_vals[] = {5, 10};

    fmi2SetReal(c, set_refs, 2, set_vals);

    unsigned int get_refs[] = {2};
    double get_vals[] = {0};

    fmi2GetReal(c, get_refs, 1, get_vals);

    REQUIRE(get_vals[0] == 0);

    fmi2DoStep(c, 0, 1, false);
  }
}
