#include <string>
#include <nlohmann/json.hpp> // pylint: disable=import-error

#ifndef PYCONFIGURATION_HPP
#define PYCONFIGURATION_HPP

// For automatic serializiation of objects see https://github.com/nlohmann/json#arbitrary-types-conversions

namespace pyconfiguration
{
    struct PyConfiguration {
        std::string main_class;
        std::string main_script;
    };

    void to_json(nlohmann::json& j, const pyconfiguration::PyConfiguration& p);

    void from_json(const nlohmann::json& j, pyconfiguration::PyConfiguration& p);
};

/**
 * @brief read and parse configuration file and return a object containing the results
 * 
 * @param config_path path to the configuration file
 * @return PyConfigruation 
 */
pyconfiguration::PyConfiguration read_configuration(const std::string &config_path);

#endif // PYCONFIGURATION_HPP
