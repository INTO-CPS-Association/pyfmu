#pragma once
#include <filesystem>
#include <string>

#include <nlohmann/json.hpp>

#include "pyfmu/fmi2/logging.hpp"

namespace pyfmu::fmi2 {

// For automatic serializiation of objects see
// https://github.com/nlohmann/json#arbitrary-types-conversions
namespace pyconfiguration {
struct PyConfiguration {
  std::string main_class;
  std::string main_script;
  std::string module_name;
};

void to_json(nlohmann::json &j, const pyconfiguration::PyConfiguration &p);

void from_json(const nlohmann::json &j, pyconfiguration::PyConfiguration &p);
} // namespace pyconfiguration

/**
 * @brief read and parse configuration file and return a object containing the
 * results
 *
 * @param config_path path to the configuration file
 * @return PyConfigruation
 */
pyconfiguration::PyConfiguration
read_configuration(const std::filesystem::path &config_path, Logger *logger);

} // namespace pyfmu::fmi2
