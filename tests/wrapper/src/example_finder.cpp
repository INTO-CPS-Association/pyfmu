#include <cstdlib>
#include <stdexcept>
#include <set>
#include <iostream>

#include <fmt/format.h>
#include "spdlog/spdlog.h"
#include <Poco/URI.h>
#include <Poco/Path.h>

#include "example_finder.hpp"

using namespace std;
using namespace fmt;
using namespace spdlog;
namespace fs = filesystem;

constexpr char exporter_script_name[] = "pyfmu";

set<string> examples = {
    "Adder",
    "ConstantSignalGenerator",
    "SineGenerator"};

/**
 * Returns the path to the example projects located in the test directory.
**/
fs::path getProjectsRoot()
{
    fs::path p = fs::path(__FILE__).parent_path().parent_path().parent_path() / "examples" / "projects";
    return p;
}

ExampleArchive::ExampleArchive(std::string exampleName) : exampleName(exampleName)
{
    // Check if the example exists
    if (examples.find(exampleName) == examples.end())
    {
        throw std::runtime_error("Example is not recognized.");
    }

    // Check if necessary tools for exporting Python FMU are available
    info("Checking if a compatible Python interpreter is present");

    int retValue = std::system("python -c \"import sys; found = 0 if (sys.version_info >= (3,0)) else -1; sys.exit(found)\"");
    int isPython3 = retValue >= 0;

    if (isPython3 < 0)
    {
        throw runtime_error("python3 program was not found in path");
    }

    info("Compatible interpreter found");

    // Export to tmp directory

    fs::path examplePath = getProjectsRoot() / exampleName;
    fs::path exportPath = this->getRoot();

    string exportCommand = format("{} export --project {} --out {}", exporter_script_name, examplePath.string(), exportPath.string());

    info("exporting example project {} using command: {}", exampleName, exportCommand);

    int ret = std::system(exportCommand.c_str());

    if (ret != 0)
    {
        throw runtime_error(format("Export of example project failed, command returned {}", ret));
    }
}

fs::path ExampleArchive::getRoot()
{
    return this->td.root / exampleName;
}

fs::path ExampleArchive::getResources()
{
    return getRoot() / "resources";
}

std::string ExampleArchive::getResourcesURI()
{
    Poco::Path p = Poco::Path(getResources().string());

    auto uri = Poco::URI(p);

    return uri.toString();
}