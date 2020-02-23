#pragma once
/**
 * Provides functionality related to finding and instantiating example projects
*/
#include <filesystem>




class ExampleProject
{

};

class ExampleArchive
{
    public:

    explicit ExampleArchive(std::string exampleName);

    private:
    
    std::filesystem::path root;
    
};