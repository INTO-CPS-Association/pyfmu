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
 * auto uri = std::path("file:///fmu_directory/fmu/resources")
 * auto path = getPathFromFileUri(uri)
 */
std::filesystem::path getPathFromFileUri(std::string uri);

/**
 * Convert a string to a wide string
**/
std::wstring s2ws(const std::string &str);
/**
 * Convert a wide string to a string
**/
std::string ws2s(const std::wstring &wstr);