#include <exception>
#include <filesystem>
#include <fstream>
#include <string.h>

#include <fmt/format.h>

#include "pyfmu/fmi2/configuration.hpp"
#include "pyfmu/fmi2/logging.hpp"

using namespace std;
using namespace fmt;
using nlohmann::json;
using std::filesystem::path;

namespace pyfmu::fmi2 {
namespace pyconfiguration {

void to_json(json &j, const PyConfiguration &p) {
  j = json{{"main_class", p.main_class}, {"main_script", p.main_script}};
}

void from_json(const json &j, PyConfiguration &p) {
  j.at("main_class").get_to(p.main_class);
  j.at("main_script").get_to(p.main_script);
}
} // namespace pyconfiguration

using pyconfiguration::PyConfiguration;

PyConfiguration read_configuration(const path &config_path, Logger *log) {

  PyConfiguration config;

  log->ok("wrapper", "Reading configuration file from: {}",
          config_path.string());

  ifstream is(config_path, ios::in);

  if (!is.is_open()) {
    const char *err = strerror(errno);
    std::string msg = format(
        "Could not open to read configuration file used to locate correct "
        "Python script on startup. Ensure that a slave_configuration.json file "
        "is located in the 'resources' folder of the FMU.\n Inner error is: {}",
        err);
    throw runtime_error(msg);
  }

  log->ok("wrapper", "Sucessfully read file");

  json j;

  try {
    is >> j;
    config = j.get<pyconfiguration::PyConfiguration>();
    config.resources = config_path.parent_path();
  } catch (const std::exception &e) {
    throw runtime_error(format(
        "failed to parse configuration file used to locate correct Python "
        "script on startup. Ensure that the slave_configuration.json file is "
        "well formed. Exception was: {}",
        e.what()));
  }

  // module name is the script's name stripped of extension: myscript.py ->
  // myscript
  config.module_name =
      (path(config.main_script).filename().replace_extension("")).string();

  return config;
}
} // namespace pyfmu::fmi2
