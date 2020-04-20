#include <string>
#include <filesystem>
#include <locale>
#include <codecvt>

#include <uriparser/Uri.h>
#include <fmt/format.h>

#include "pyfmu/pyCompatability.hpp"
#include "pyfmu/fmi2PySlaveLogging.hpp"

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

  size_t scheme_len = uri_s.scheme.afterLast -uri_s.scheme.first;
  std::string scheme(uri_s.scheme.first,scheme_len);

  if(scheme != "file")
  {
    uriFreeUriMembersA(&uri_s);
    throw runtime_error(format("Unable to parse URI string: {}, only file-URI's are supported",uri));
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



#ifdef WIN32
  // TODO
#else

#include <dlfcn.h>
/**
 * @brief In order to support loading of extension modules such as Numpy it is necessary load libpython3.x.so
 * Since it 
 * 
 */
void loadPythonSharedObject()
{
  
  //sysconfig.get_config_var('INSTSONAME');
  pyfmu::pyCompat::PyRun_SimpleString("import sysconfig");
  
  
    auto sysconfig_module = PyImport_ImportModule("sysconfig");
    auto lib_obj = PyObject_CallMethod(sysconfig_module,"get_config_var","(s)","INSTSONAME");
    //auto lib_obj = PyEval_CallFunction(get_config_var_func,"INSTSONAME");
    
    const char* libpython_name;
    int s = PyArg_Parse(lib_obj,"s",&libpython_name);
    auto msg = pyfmu::get_py_exception();

  
    // auto handle = dlopen("libpython3.7m.so.1.0", RTLD_LAZY | RTLD_GLOBAL);
    auto handle = dlopen(libpython_name, RTLD_LAZY | RTLD_GLOBAL);

  if(!handle)
  {
      fprintf(stderr, " Failed to open library: %s\n", dlerror());
      exit(EXIT_FAILURE);
  }
}

#endif