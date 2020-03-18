#include <string>
#include <filesystem>
#include <locale>
#include <codecvt>

#include <Python.h>
#include <Poco/URI.h>
#include <fmt/format.h>

#include "pythonfmu/Logger.hpp"

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

std::filesystem::path getPathFromFileUri(std::string uri)
{
  auto u = Poco::URI(uri);

  auto s = u.getScheme();

  if (s.empty())
    throw std::invalid_argument(fmt::format("URI could not be converted into a file path, the scheme of the specified URI could not be determined"));

  else if (s != "file")
    throw std::invalid_argument(fmt::format("uri could not be converted to path, the scheme should be 'file', but was {}", s));

  auto test_path = std::filesystem::path(__FILE__).parent_path() / "tests" / "foo";

  std::string path = u.getPath();

#ifdef WIN32
  path = path.substr(1);
#endif

  auto p = std::filesystem::weakly_canonical(std::filesystem::path(path));

  return p;
}

/**
 * Convert a string to a wide string
**/
std::wstring s2ws(const std::string &str)
{
  using convert_typeX = std::codecvt_utf8<wchar_t>;
  std::wstring_convert<convert_typeX, wchar_t> converterX;

  return converterX.from_bytes(str);
}

/**
 * Convert a wide string to a string
**/
std::string ws2s(const std::wstring &wstr)
{
  using convert_typeX = std::codecvt_utf8<wchar_t>;
  std::wstring_convert<convert_typeX, wchar_t> converterX;
  return converterX.to_bytes(wstr);
}