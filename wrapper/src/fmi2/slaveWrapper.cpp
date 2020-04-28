#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <utility>
#include <regex>

#include "fmt/format.h"

#include "spec/fmi2/fmi2TypesPlatform.h"
#include "pyfmu/fmi2/slaveWrapper.hpp"
#include "pyfmu/fmi2/configuration.hpp"
#include "pyfmu/fmi2/logging.hpp"

using namespace fmt;
using namespace std;

using path = filesystem::path;

namespace pyfmu::fmi2
{

/**
 * @brief Callaback function used by the Python slave to do logging.
 * This function must be a free function. As such the logger is injected using a PyCapsule.
 * 
 * @param self a PyCapsule object used to pass a point
 * @param args a python tuple of status,category and string (int,string,string)
 * @return PyObject* 
 */
// static PyObject *logCallback(PyObject *self, PyObject *args)
// {
//   PyGIL g;

//   // extract logging context from capsule
//   Logger *logger = (Logger *)PyCapsule_GetPointer(self, nullptr);

//   fmi2Status status;
//   const char *message;
//   const char *category;
//   int s = PyArg_Parse(args, "(iss)", &status, &category, &message);

//   if (s == 0)
//   {
//     logger->warning("Logger callback called, but wrapper was unable to parse arguments : {}.", get_py_exception());
//   }
//   else
//   {
//     // Escape { and } with {{ and }} to avoid issues with fmt
//     std::regex left("\\{");
//     std::regex right("\\}");

//     std::string messageStr(message);
//     std::string categoryStr(category);

//     messageStr = std::regex_replace(messageStr, left, "{{");
//     messageStr = std::regex_replace(messageStr, right, "}}");
//     categoryStr = std::regex_replace(categoryStr, left, "{{");
//     categoryStr = std::regex_replace(categoryStr, right, "}}");

//     logger->log(status, categoryStr, messageStr);
//   }

//   Py_RETURN_NONE;
// }

// /**
//  * @brief Appends path of resources folder to the Python interpreter path. This
//  * allows the interpreter to locate and load the slave script.
//  *
//  * @param resource_path path to the resources dir supplied when FMU is
//  * initialized
//  */
// void append_resources_folder_to_python_path(path &resource_path)
// {
//   PyGIL g;

//   ostringstream oss;
//   oss << "import sys\n";
//   oss << "sys.path.append(r'" << resource_path.string() << "')\n";

//   string str = oss.str();
//   const char *cstr = str.c_str();

//   int err = pyfmu::pyCompat::PyRun_SimpleString(cstr);

//   if (err != 0)
//     throw runtime_error("Failed to append folder to python path\n");
// }

// void SlaveWrapper::instantiate_main_class(string module_name,
//                                              string main_class)
// {
//   PyGIL g;

//   logger->ok("wrapper", "importing Python module: {}, into the interpreter", module_name);

//   pModule_ = PyImport_ImportModule(module_name.c_str());

//   if (pModule_ == NULL)
//   {

//     auto pyErr = get_py_exception();
//     auto msg = format("module could not be imported. Ensure that slave script "
//                       "defined inside the wrapper configuration matches a "
//                       "Python script. Error from python was:\n{}",
//                       pyErr);
//     logger->fatal("wrapper", msg);
//     throw runtime_error(msg);
//   }

//   logger->ok("wrapper", "module: {} was successfully imported, attempting to read definition of slave class : {} from the module.", module_name, main_class);

//   pClass_ = PyObject_GetAttrString(pModule_, main_class.c_str());

//   if (pClass_ == nullptr)
//   {
//     auto pyErr = get_py_exception();
//     auto msg = format("Python module: {} was successfully loaded, but the defintion "
//                       "of the slave class {} could not be loaded. Ensure that the "
//                       "specified module contains a definition of the class. Python error was:\n{}\n",
//                       module_name, main_class, pyErr);
//     logger->fatal("wrapper", msg);
//     throw runtime_error(msg);
//   }

//   logger->ok("wrapper", "Definition of class {} was successfully read, attempting create an instance.", main_class);

//   // pass logging function to python slave
//   // since the callback must be a free function, we need to somehow pass a pointer to the concrete logger instance
//   // for this we use "capsules" which allow opaque pointers to be passed between modules.

//   pCallbackDef = {
//       "logCallback",
//       logCallback,
//       METH_VARARGS | METH_KEYWORDS,
//       ""};

//   auto loggerCapsule = PyCapsule_New(logger, nullptr, nullptr);
//   pCallbackFunc = PyCFunction_New(&pCallbackDef, loggerCapsule);
//   //auto f = PyObject_CallMethod(pInstance_, "_register_log_callback", "(O)", pCallbackFunc);

//   //PyObject* PyObject_Call(PyObject *callable, PyObject *args, PyObject *kwargs) https://docs.python.org/3/c-api/object.html

//   auto args = Py_BuildValue("()");
//   auto kwargs = Py_BuildValue("{s:O}", "logging_callback", pCallbackFunc);
//   //kwargs = Py_BuildValue("{}");

//   pInstance_ = PyObject_Call(pClass_, args, kwargs);

//   //pInstance_ = PyObject_CallFunctionObjArgs(pClass_, nullptr);

//   if (pInstance_ == nullptr)
//   {
//     auto pyErr = get_py_exception();
//     auto msg = format("Failed to instantiate class: {}, ensure that the Python script is valid and that defines a parameterless constructor. Python error was:\n{}\n", main_class, pyErr);
//     logger->fatal("wrapper", msg);
//     throw runtime_error(msg);
//   }

//   // if(f == nullptr)
//   // {
//   //   string msg = fmt::format("wrapper", "Failed to register callback for logging. An exception was thrown in Python: {}", get_py_exception());
//   //   logger->error(PYFMU_WRAPPER_LOG_CATEGORY,msg);
//   //   throw runtime_error(msg);
//   // }

//   logger->ok("wrapper", "Successfully created an instance of class: {} defined in module: {}", main_class, module_name);
// }

SlaveWrapper::SlaveWrapper(path resource_path, Logger *logger) : logger(logger)
{
  path path_to_config(resource_path / "slave_configuration.json");
}

} // namespace pyfmu::fmi2
