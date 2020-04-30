#include <filesystem>
#include <fstream>
#include <iostream>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <utility>

#include "fmt/format.h"
#include "pybind11/embed.h"

#include "pyfmu/fmi2/configuration.hpp"
#include "pyfmu/fmi2/embeddedSlave.hpp"
#include "pyfmu/fmi2/logging.hpp"
#include "spec/fmi2/fmi2TypesPlatform.h"

using namespace fmt;
using namespace std;

using path = filesystem::path;

namespace pyfmu::fmi2 {

/**
 * @brief Callaback function used by the Python slave to do logging.
 * This function must be a free function. As such the logger is injected using a
 * PyCapsule.
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
//     logger->warning("Logger callback called, but wrapper was unable to parse
//     arguments : {}.", get_py_exception());
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
//  * @brief Appends path of resources folder to the Python interpreter path.
//  This
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

//   logger->ok("wrapper", "importing Python module: {}, into the interpreter",
//   module_name);

//   pModule_ = PyImport_ImportModule(module_name.c_str());

//   if (pModule_ == NULL)
//   {

//     auto pyErr = get_py_exception();
//     auto msg = format("module could not be imported. Ensure that slave script
//     "
//                       "defined inside the wrapper configuration matches a "
//                       "Python script. Error from python was:\n{}",
//                       pyErr);
//     logger->fatal("wrapper", msg);
//     throw runtime_error(msg);
//   }

//   logger->ok("wrapper", "module: {} was successfully imported, attempting to
//   read definition of slave class : {} from the module.", module_name,
//   main_class);

//   pClass_ = PyObject_GetAttrString(pModule_, main_class.c_str());

//   if (pClass_ == nullptr)
//   {
//     auto pyErr = get_py_exception();
//     auto msg = format("Python module: {} was successfully loaded, but the
//     defintion "
//                       "of the slave class {} could not be loaded. Ensure that
//                       the " "specified module contains a definition of the
//                       class. Python error was:\n{}\n", module_name,
//                       main_class, pyErr);
//     logger->fatal("wrapper", msg);
//     throw runtime_error(msg);
//   }

//   logger->ok("wrapper", "Definition of class {} was successfully read,
//   attempting create an instance.", main_class);

//   // pass logging function to python slave
//   // since the callback must be a free function, we need to somehow pass a
//   pointer to the concrete logger instance
//   // for this we use "capsules" which allow opaque pointers to be passed
//   between modules.

//   pCallbackDef = {
//       "logCallback",
//       logCallback,
//       METH_VARARGS | METH_KEYWORDS,
//       ""};

//   auto loggerCapsule = PyCapsule_New(logger, nullptr, nullptr);
//   pCallbackFunc = PyCFunction_New(&pCallbackDef, loggerCapsule);
//   //auto f = PyObject_CallMethod(pInstance_, "_register_log_callback", "(O)",
//   pCallbackFunc);

//   //PyObject* PyObject_Call(PyObject *callable, PyObject *args, PyObject
//   *kwargs) https://docs.python.org/3/c-api/object.html

//   auto args = Py_BuildValue("()");
//   auto kwargs = Py_BuildValue("{s:O}", "logging_callback", pCallbackFunc);
//   //kwargs = Py_BuildValue("{}");

//   pInstance_ = PyObject_Call(pClass_, args, kwargs);

//   //pInstance_ = PyObject_CallFunctionObjArgs(pClass_, nullptr);

//   if (pInstance_ == nullptr)
//   {
//     auto pyErr = get_py_exception();
//     auto msg = format("Failed to instantiate class: {}, ensure that the
//     Python script is valid and that defines a parameterless constructor.
//     Python error was:\n{}\n", main_class, pyErr); logger->fatal("wrapper",
//     msg); throw runtime_error(msg);
//   }

//   // if(f == nullptr)
//   // {
//   //   string msg = fmt::format("wrapper", "Failed to register callback for
//   logging. An exception was thrown in Python: {}", get_py_exception());
//   //   logger->error(PYFMU_WRAPPER_LOG_CATEGORY,msg);
//   //   throw runtime_error(msg);
//   // }

//   logger->ok("wrapper", "Successfully created an instance of class: {}
//   defined in module: {}", main_class, module_name);
// }

enum Fmi2Status {
  ok,
  warning,
  discard,
  error,
  fatal,
  pending,
};

EmbeddedSlave::EmbeddedSlave(const std::string &slaveModule,
                             const std::string &slaveClass, Logger *logger)
    : logger(logger) {

  if (!Py_IsInitialized())
    runtime_error("Python interpeter must be instantiated prior to creating an "
                  "instance of the wrapper");

  try {

    slaveInstance = pybind11::module::import(slaveModule.c_str())
                        .attr(slaveClass.c_str())();

    method_getxxx = slaveInstance.attr("_get_xxx");
    method_setxxx = slaveInstance.attr("_set_xxx");
    method_setDebugLogging = slaveInstance.attr("_set_debug_logging");
    method_enterInitializationMode =
        slaveInstance.attr("_enter_initialization_mode");
    method_exitInitializationMode =
        slaveInstance.attr("_exit_initialization_mode");
    method_reset = slaveInstance.attr("_reset");
    method_terminate = slaveInstance.attr("_terminate");
    method_setupExperiment = slaveInstance.attr("_setup_experiment");
    method_dostep = slaveInstance.attr("_do_step");

  } catch (const std::exception &e) {
    logger->fatal(
        "wrapper",
        "Unable to instantiate slave class, an exception was raised:\n{}",
        e.what());
  }
}

fmi2Status EmbeddedSlave::setupExperiment(fmi2Real startTime,
                                          std::optional<fmi2Real> tolerance,
                                          std::optional<fmi2Real> stopTime) {
  return fmi2Fatal;
}

fmi2Status EmbeddedSlave::enterInitializationMode() {
  return method_enterInitializationMode().cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::exitInitializationMode() {
  return method_exitInitializationMode().cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::doStep(fmi2Real currentTime, fmi2Real stepSize,
                                 fmi2Boolean noSetFMUStatePriorToCurrentPoint) {

  return method_dostep(currentTime, stepSize, noSetFMUStatePriorToCurrentPoint)
      .cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::reset() { return fmi2Fatal; }

fmi2Status EmbeddedSlave::terminate() {
  return method_terminate().cast<fmi2Status>();
}

fmi2Status EmbeddedSlave::setDebugLogging(bool loggingOn,
                                          StringValues categories) {
  auto test = method_setDebugLogging(loggingOn, categories);
  return test.cast<fmi2Status>();
}

Fmi2GetterResult<fmi2Real> EmbeddedSlave::getReal(VRefs references) {
  return method_getxxx(references, Fmi2DataType::real)
      .cast<Fmi2GetterResult<fmi2Real>>();
}
Fmi2GetterResult<fmi2Integer> EmbeddedSlave::getInteger(VRefs references) {
  return method_getxxx(references, Fmi2DataType::integer)
      .cast<Fmi2GetterResult<fmi2Integer>>();
}
Fmi2GetterResult<fmi2Boolean> EmbeddedSlave::getBoolean(VRefs references) {
  return method_getxxx(references, Fmi2DataType::boolean)
      .cast<Fmi2GetterResult<fmi2Boolean>>();
}
Fmi2GetterResult<fmi2String> EmbeddedSlave::getString(VRefs references) {
  return method_getxxx(references, Fmi2DataType::string)
      .cast<Fmi2GetterResult<fmi2String>>();
}

fmi2Status EmbeddedSlave::setReal(VRefs references, RealValues values) {
  return method_setxxx(references, values, Fmi2DataType::real)
      .cast<fmi2Status>();
}
fmi2Status EmbeddedSlave::setInteger(VRefs references, IntegerValues values) {
  return method_setxxx(references, values, Fmi2DataType::integer)
      .cast<fmi2Status>();
}
fmi2Status EmbeddedSlave::setBoolean(VRefs references, BooleanValues values) {
  return method_setxxx(references, values, Fmi2DataType::boolean)
      .cast<fmi2Status>();
}
fmi2Status EmbeddedSlave::setString(VRefs references, StringValues values) {
  return method_setxxx(references, values, Fmi2DataType::string)
      .cast<fmi2Status>();
}

EmbeddedSlave::~EmbeddedSlave() {}

} // namespace pyfmu::fmi2
