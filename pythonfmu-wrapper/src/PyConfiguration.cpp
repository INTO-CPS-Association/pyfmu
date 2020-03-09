#include <fstream>
#include <exception>
#include <filesystem>

#include <fmt/format.h>

#include "pythonfmu/Logger.hpp"
#include "pythonfmu/PyConfiguration.hpp"

using namespace std;
using namespace nlohmann;
using namespace pyconfiguration;
using namespace filesystem;
using namespace fmt;

namespace pyconfiguration
{

void to_json(json &j, const PyConfiguration &p)
{
    j = nlohmann::json{{"main_class", p.main_class}, {"main_script", p.main_script}};
}

void from_json(const json &j, PyConfiguration &p)
{
    j.at("main_class").get_to(p.main_class);
    j.at("main_script").get_to(p.main_script);
}
}

PyConfiguration read_configuration(const path &config_path, Logger *log)
{

    PyConfiguration config;

    log->ok(format("Reading configuration file from: {}", config_path.string()));

    ifstream is(config_path);

    if (!is.is_open())
        throw runtime_error("failed to read configuration file used to locate correct Python script on startup. Ensure that a slave_configuration.json file is located in the 'resources' folder of the FMU.");

    log->ok("Sucessfully read file");

    json j;

    try
    {
        is >> j;
        config = j.get<pyconfiguration::PyConfiguration>();
    }
    catch (const std::exception &e)
    {
        throw runtime_error("failed to parse configuration file used to locate correct Python script on startup. Ensure that the slave_configuration.json file is well formed.");
    }

    return config;
}