#include <fstream>
#include <exception>
#include "pythonfmu/PyConfiguration.hpp"
#include <filesystem>

using namespace std;
using namespace nlohmann;
using namespace pyconfiguration;
using namespace filesystem;

namespace pyconfiguration 
{

    void to_json(json& j, const PyConfiguration& p) {
        j = nlohmann::json{{"main_class", p.main_class}, {"main_script", p.main_script}};
    }

    void from_json(const json& j, PyConfiguration& p) {
        j.at("main_class").get_to(p.main_class);
        j.at("main_script").get_to(p.main_script);
    }
}


PyConfiguration read_configuration(const string &config_path)
{


    PyConfiguration config;

    ifstream is(config_path);
    
    
    if(!is.is_open())
        throw new runtime_error("failed to read configuration file used to locate correct Python script on startup. Ensure that a slave_configuration.json file is located in the 'resources' folder of the FMU.");


    json j;

    try
    {
        is >> j;
        config = j.get<pyconfiguration::PyConfiguration>();
    }
    catch (const std::exception& e)
    {
        throw new runtime_error("failed to parse configuration file used to locate correct Python script on startup. Ensure that the slave_configuration.json file is well formed.");
    }
    

    return config;
}