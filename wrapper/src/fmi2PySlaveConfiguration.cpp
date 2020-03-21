#include <fstream>
#include <exception>
#include <filesystem>
#include <string.h>

#include <fmt/format.h>

#include "pyfmu/fmi2PySlaveLogging.hpp"
#include "pyfmu/fmi2PySlaveConfiguration.hpp"

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

PyConfiguration read_configuration(const path &config_path, pyfmu::Logger *log)
{

    PyConfiguration config;

    log->ok("wrapper", "Reading configuration file from: {}", config_path.string());

    ifstream is(config_path, ios::in);

    if (!is.is_open())
    {

// MSVC is missing the strerrorlen_s method, however error messages can at most be 94 characters long:
// https://docs.microsoft.com/en-us/cpp/c-runtime-library/reference/strerror-s-strerror-s-wcserror-s-wcserror-s?view=vs-2019
#ifdef _MSC_VER
        constexpr size_t errmsglen = 94 + 1;
#else
        size_t errmsglen = strerrorlen_s(errno) + 1;
#endif

        char *errmsg = new char[errmsglen];
        strerror_s(errmsg, errmsglen, errno);

        std::string msg = format("Could not open to read configuration file used to locate correct Python script on startup. Ensure that a slave_configuration.json file is located in the 'resources' folder of the FMU.\n Inner error is: {}", errmsg);

        delete[] errmsg;
        throw runtime_error(msg);
    }

    log->ok("wrapper", "Sucessfully read file");

    json j;

    try
    {
        is >> j;
        config = j.get<pyconfiguration::PyConfiguration>();
    }
    catch (const std::exception &e)
    {
        throw runtime_error(format("failed to parse configuration file used to locate correct Python script on startup. Ensure that the slave_configuration.json file is well formed. Exception was: {}", e.what()));
    }

    // module name is the script's name stripped of extension: myscript.py -> myscript
    config.module_name = (path(config.main_script).filename().replace_extension("")).string();

    return config;
}