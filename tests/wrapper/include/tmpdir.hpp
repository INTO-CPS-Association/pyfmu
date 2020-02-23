#pragma once

#include <filesystem>

/**
 * RAII wrapper around a temporary directory
*/
class TmpDir
{
    public:

    TmpDir();

    ~TmpDir();

    std::filesystem::path root;
};