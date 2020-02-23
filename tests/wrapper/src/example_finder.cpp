#include <cstdlib>
#include <stdexcept>
#include <set>
#include <iostream>

#include <fmt/format.h>

#include "example_finder.hpp"



using namespace std;
namespace fs = filesystem;


/**
 * Returns the path to the tool for generating and exporting Python FMUs
*/
/*std::filesystem path getPathToBuilder()
{
    return nullptr;
}
*/

set<string> examples = {
    "Adder",
};

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
    if(examples.find(exampleName) == examples.end())
    {
        throw std::runtime_error("Example is not recognized.");
    }

    // Check if necessary tools for exporting Python FMU are available
    int retValue = std::system("python3 -c 'import sys; found = 0 if (sys.version_info >= (3,0)) else -1; sys.exit(found)'");
    int isPython3 = retValue >= 0 && WEXITSTATUS(retValue) == 0;
    

    if(isPython3 < 0)
    {
        throw runtime_error("python3 program was not found in path");
    }

    // Export to tmp directory

    fs::path examplePath = projectPath / exampleName;
    fs::path exportPath = this->getRoot();

    //string exportCommand = fmt::format("python3 {} export ")

    //std::system(exportCommand);

}


fs::path ExampleArchive::getRoot()
{
    
    return this->td.root;
}




