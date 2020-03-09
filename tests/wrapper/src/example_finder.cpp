#include <cstdlib>
#include <stdexcept>
#include <set>
#include <iostream>

#include <fmt/format.h>
#include <Poco/URI.h>
#include <Poco/Path.h>

#include "example_finder.hpp"

using namespace std;
using namespace fmt;
namespace fs = filesystem;

constexpr char exporter_script_name[] = "py2fmu";

set<string> examples = {
    "Adder",
    "ConstantSignalGenerator",
    "SineGenerator"};

fs::path projectPath;
fs::path builderPath;

void setProjecsDirectory(fs::path p)
{
    projectPath = p;
}

void setBuilderPath(fs::path p)
{
    builderPath = p;
}

ExampleArchive::ExampleArchive(std::string exampleName)
{
    // Check if the example exists
    if (examples.find(exampleName) == examples.end())
    {
        throw std::runtime_error("Example is not recognized.");
    }

    // Check if necessary tools for exporting Python FMU are available
    int retValue = std::system("python -c 'import sys; found = 0 if (sys.version_info >= (3,0)) else -1; sys.exit(found)'");
    int isPython3 = retValue >= 0;

    if (isPython3 < 0)
    {
        throw runtime_error("python3 program was not found in path");
    }

    // Export to tmp directory

    fs::path examplePath = projectPath / exampleName;
    fs::path exportPath = this->getRoot();

    string exportCommand = format("python {} export --project {} --out {}\n", exporter_script_name, examplePath.string(), exportPath.string());

    print(format("exporting example project {} using command:\n{}", exampleName, exportCommand));

    int ret = std::system(exportCommand.c_str());

    if (ret != 0)
    {
        throw runtime_error(format("Export of example project failed, command returned {}", ret));
    }
}

std::string get_resource_uri(std::string example_name)
{
    if (!examples.contains(example_name))
        throw std::runtime_error(fmt::format("Can not get path to resources of project {}, the project does not exist.", example_name));

    Poco::Path p = Poco::Path(__FILE__).parent().parent().parent().append("examples").append("projects").append(example_name).append("resources");

    auto uri = Poco::URI(p);

    return uri.toString();
}

fs::path ExampleArchive::getRoot()
{
    return this->td.root;
}
