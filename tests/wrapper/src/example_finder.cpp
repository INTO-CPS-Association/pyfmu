#include "example_finder.hpp"


namespace fs = std::filesystem;


ExampleArchive::ExampleArchive(std::string exampleName)
{
    this->root = fs::current_path();
}




