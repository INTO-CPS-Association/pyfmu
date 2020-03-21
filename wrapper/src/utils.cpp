#include <string>
#include <filesystem>
#include <locale>
#include <codecvt>

#include <uriparser/Uri.h>
#include <fmt/format.h>

using namespace std;
using namespace filesystem;
using namespace fmt;

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

path getPathFromFileUri(string uri)
{
  // see parser docs https://uriparser.github.io/doc/api/latest/
  const char *uri_cstr = uri.c_str();

  UriUriA uri_s;

  int err = uriParseSingleUriA(&uri_s, uri_cstr, NULL);

  if (err)
  {
    throw runtime_error(format("Unable to parse URI string : {}. Ensure that the uri is valid.", uri));
  }

  uriFreeUriMembersA(&uri_s);

#ifdef WIN32
  const size_t bytesNeeded = uri.length() + 1;
#else
  const size_t bytesNeeded = uri.length() + 1;
#endif

  char *absUri = new char[bytesNeeded];

#ifdef WIN32
  err = uriUriStringToWindowsFilenameA(uri_cstr, absUri);
#else
  err = uriUriStringToUnixFilenameA(uri_cstr, absUri);
#endif

  if (err != URI_SUCCESS)
  {
    delete[] absUri;
    throw runtime_error("Failed to parse extract host specific path from URI.");
  }

  path p = weakly_canonical(path(absUri));
  delete[] absUri;

  return p;
}

string getFileUriFromPath(path p)
{

#ifdef WIN32
  const size_t bytesNeeded = 8 + (3 * p.string().length() + 1);
#else
  const size_t bytesNeeded = 7 + (3 * p.string().length() + 1);
#endif

  char *absUri = new char[bytesNeeded];

#ifdef WIN32
  int err = uriWindowsFilenameToUriStringA(p.string().c_str(), absUri);
#else
  int err = uriUnixFilenameToUriStringA(p.string() c_str(), absUri);
#endif

  if (err != URI_SUCCESS)
  {
    delete[] absUri;
    throw runtime_error("Failed to parse extract host specific path from URI.");
  }

  string s(absUri);
  delete[] absUri;

  return s;
}

/**
 * Convert a string to a wide string
**/
wstring s2ws(const string &str)
{
  using convert_typeX = std::codecvt_utf8<wchar_t>;
  wstring_convert<convert_typeX, wchar_t> converterX;

  return converterX.from_bytes(str);
}

/**
 * Convert a wide string to a string
**/
string ws2s(const wstring &wstr)
{
  using convert_typeX = codecvt_utf8<wchar_t>;
  wstring_convert<convert_typeX, wchar_t> converterX;
  return converterX.to_bytes(wstr);
}