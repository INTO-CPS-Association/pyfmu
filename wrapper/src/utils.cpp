#include <string>
#include <filesystem>
#include <locale>
#include <codecvt>

#include <uriparser/Uri.h>
#include <fmt/format.h>

using namespace std;
using namespace filesystem;
using namespace fmt;

// Works on windows
int win_parse_uriparserV1(const char *uri, char *filenname)
{
  UriUriA uri1;
  int err = uriParseSingleUriA(&uri1, uri, nullptr);
  if (err != 0)
    return err;

  auto path1_cstr = uri1.pathHead->text.first;

  strcpy(filenname, path1_cstr);

  uriFreeUriMembersA(&uri1);
  return err;
}

/**
 * @brief Seems to fail on windows if only a single drive letter
 * is used
 * 
 * @param uri 
 * @param filenname 
 */
int win_parse_uriparserV2(const char *uri, char *filenname)
{
  return uriUriStringToWindowsFilenameA(uri, filenname);
}

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

  size_t scheme_len = uri_s.scheme.afterLast - uri_s.scheme.first;
  std::string scheme(uri_s.scheme.first, scheme_len);

  if (scheme != "file")
  {
    uriFreeUriMembersA(&uri_s);
    throw runtime_error(format("Unable to parse URI string: {}, only file-URI's are supported", uri));
  }

  uriFreeUriMembersA(&uri_s);

#ifdef WIN32
  const size_t bytesNeeded = uri.length() + 1;
#else
  const size_t bytesNeeded = uri.length() + 1;
#endif

  char *absUri = new char[bytesNeeded];

#ifdef WIN32
  err = win_parse_uriparserV1(uri_cstr, absUri);

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
  int err = uriUnixFilenameToUriStringA(p.string().c_str(), absUri);
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