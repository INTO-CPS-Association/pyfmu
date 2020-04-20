#pragma once

#include <string>
#include <filesystem>

/**
 * @brief Convert file uri to a path
 * 
 * @param uri a unique resource identifier pointing to a file
 * @return path extracted from the uri
 * @throw invalid_argument
 * 
 * @example:
 * std::string uri = std::path("file:///fmu_directory/fmu/resources")
 * std::filesystem::path p = getPathFromFileUri(uri)
 */
std::filesystem::path getPathFromFileUri(std::string uri);

/**
 * @brief Returns an file URI pointing to the specified path.
 * 
 * @param path to the file
 * @return file uri encoded as a string
 */
std::string getFileUriFromPath(std::filesystem::path path);


/**
 * Convert a string to a wide string
**/
std::wstring s2ws(const std::string &str);
/**
 * Convert a wide string to a string
**/
std::string ws2s(const std::wstring &wstr);

void loadPythonSharedObject();