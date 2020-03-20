#include <stdexcept>

#include "tmpdir.hpp"

const std::string error = "test";

namespace fs = std::filesystem;

TmpDir::TmpDir()
{
    fs::path tmp_dir_path{fs::temp_directory_path() /= std::tmpnam(nullptr)};

    // Attempt to create the directory.
    if (std::filesystem::create_directories(tmp_dir_path))
    {

        // Directory successfully created.
        this->root = tmp_dir_path;
    }
    else
    {

        // Directory could not be created.
        throw std::exception();
    }
}

TmpDir::~TmpDir()
{
    fs::remove_all(this->root);
}