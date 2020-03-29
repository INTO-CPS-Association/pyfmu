#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <utility>
#include <regex>

#include "fmt/format.h"

#include "fmi/fmi2TypesPlatform.h"
#include "pyfmu/fmi2PySlave.hpp"
#include "pyfmu/fmi2PySlaveConfiguration.hpp"
#include "pyfmu/fmi2PySlaveLogging.hpp"
#include "pyfmu/pyCompatability.hpp"

using namespace fmt;
using namespace pyconfiguration;
using namespace std;
using namespace filesystem;

namespace pyfmu
{

/**
 * @brief Converts the a long into a fmi2Status. Uses pass by reference to return the status.
 * 
 * @param longStatus long representing the status of the FMU
 * @param status reference to the status
 * @return true if long can be converted into valid fmi2Status
 * @return false if unable to convert the long into a valid fmi2Status
 */
bool longToFmiStatus(long longStatus, fmi2Status &status)
{

  if (longStatus < fmi2Status::fmi2OK || longStatus > fmi2Status::fmi2Pending)
  {
    return false;
  }

  status = (fmi2Status)longStatus;
  return true;
}

/**
 * @brief Appends path of resources folder to the Python interpreter path. This
 * allows the interpreter to locate and load the main script.
 *
 * @param resource_path path to the resources dir supplied when FMU is
 * initialized
 */
void append_resources_folder_to_python_path(path &resource_path)
{
  PyGIL g;

  ostringstream oss;
  oss << "import sys\n";
  oss << "sys.path.append(r'" << resource_path.string() << "')\n";

  string str = oss.str();
  const char *cstr = str.c_str();

  int err = pyfmu::pyCompat::PyRun_SimpleString(cstr);

  if (err != 0)
    throw runtime_error("Failed to append folder to python path\n");
}

void PyObjectWrapper::instantiate_main_class(string module_name,
                                             string main_class)
{
  PyGIL g;

  logger->ok("wrapper", "importing Python module: {}, into the interpreter", module_name);

  pModule_ = PyImport_ImportModule(module_name.c_str());

  if (pModule_ == NULL)
  {

    auto pyErr = get_py_exception();
    auto msg = format("module could not be imported. Ensure that main script "
                      "defined inside the wrapper configuration matches a "
                      "Python script. Error from python was:\n{}",
                      pyErr);
    logger->fatal("wrapper", msg);
    throw runtime_error(msg);
  }

  logger->ok("wrapper", "module: {} was successfully imported, attempting to read definition of main class : {} from the module.", module_name, main_class);

  pClass_ = PyObject_GetAttrString(pModule_, main_class.c_str());

  if (pClass_ == nullptr)
  {
    auto pyErr = get_py_exception();
    auto msg = format("Python module: {} was successfully loaded, but the defintion "
                      "of the main class {} could not be loaded. Ensure that the "
                      "specified module contains a definition of the class. Python error was:\n{}\n",
                      module_name, main_class, pyErr);
    logger->fatal("wrapper", msg);
    throw runtime_error(msg);
  }

  logger->ok("wrapper", "Definition of class {} was successfully read, attempting create an instance.", main_class);

  pInstance_ = PyObject_CallFunctionObjArgs(pClass_, nullptr);

  if (pInstance_ == nullptr)
  {
    auto pyErr = get_py_exception();
    auto msg = format("Failed to instantiate class: {}, ensure that the Python script is valid and that defines a parameterless constructor. Python error was:\n{}\n", main_class, pyErr);
    logger->fatal("wrapper", msg);
    throw runtime_error(msg);
  }

  propagate_python_log_messages();
  logger->ok("wrapper", "Sucessfully created an instance of class: {} defined in module: {}", main_class, module_name);
}

PyObjectWrapper::PyObjectWrapper(path resource_path, Logger *logger) : logger(logger)
{

  PyGIL g;

  if (!Py_IsInitialized())
  {
    throw runtime_error(
        "The Python object cannot be instantiated due to the python intrepeter "
        "not being instantiated. Ensure that Py_Initialize() is invoked "
        "successfully prior to the invoking the constructor.");
  }

  logger->ok("wrapper", "Appending resource folder : {} to python interpreter's path", resource_path.string());

  try
  {
    append_resources_folder_to_python_path(resource_path);
  }
  catch (const std::exception &)
  {
    logger->fatal("wrapper", "Failed appending resources directory to interpreter's path.");
    throw;
  }

  logger->ok("wrapper", "Resources directory was appended to interpreter's path");

  auto config_path = resource_path / "slave_configuration.json";

  logger->ok("wrapper", "Reading configuration file located at: {} to locate the main python class.", config_path.string());

  PyConfiguration config;
  try
  {
    config = read_configuration(config_path, logger);

    logger->ok("wrapper", "successfully read configuration file, specifying the following: main script is: {} and main class is: {}", config.main_script, config.main_class);
  }
  catch (const exception &e)
  {
    logger->error("wrapper", "Failed to read configuration file, an expection was thrown : {}", e.what());
    throw;
  }

  logger->ok("wrapper", "Attempting to instantiate main class : {} declared in module {} which is defined by the script : {}", config.main_class, config.module_name, config.main_script);

  try
  {
    instantiate_main_class(config.module_name, config.main_class);
  }
  catch (const exception &e)
  {
    logger->fatal("wrapper", "Instantiation of main class failed with exception : {}", e.what());
    throw;
  }
}

PyObjectWrapper::PyObjectWrapper(PyObjectWrapper &&other) : pModule_(other.pModule_), pClass_(other.pClass_), pInstance_(other.pInstance_), logger(std::move(other.logger))
{
}

fmi2Status PyObjectWrapper::setupExperiment(fmi2Boolean toleranceDefined,
                                            fmi2Real tolerance, fmi2Real startTime,
                                            fmi2Boolean stopTimeDefined, fmi2Real stopTime)
{
  PyGIL g;

  auto f = PyObject_CallMethod(pInstance_, PYFMU_FMI2SLAVE_SETUPEXPERIMENT, "(d)", startTime);

  if (f == nullptr)
  {
    logger->fatal("wrapper", "call to setupExperiment failed with exception : {}", get_py_exception());
    return fmi2Fatal;
  }

  long ls = PyLong_AsLong(f);
  Py_DECREF(f);
  if (ls == -1)
  {
    logger->fatal("wrapper", "call to setupExperiment was succesfull, but return value could not be converted into an long as expected : {}", get_py_exception());
    return fmi2Fatal;
  }

  fmi2Status s;
  bool validStatus = longToFmiStatus(ls, s);

  if (!validStatus)
  {
    logger->fatal("wrapper", "call to setupExperiment was succesfull, return value was a long as expected, but does not match any fmi2Status : {}", validStatus);
  }

  propagate_python_log_messages();
  return fmi2OK;
}

fmi2Status PyObjectWrapper::enterInitializationMode()
{
  PyGIL g;
  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_ENTERINITIALIZATIONMODE, "()");
  return status;
}

fmi2Status PyObjectWrapper::exitInitializationMode()
{
  PyGIL g;
  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_EXITINITIALIZATIONMODE, "()");
  return status;
}

fmi2Status PyObjectWrapper::doStep(fmi2Real currentTime, fmi2Real stepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint)
{
  PyGIL g;
  auto pyNoSetPrior = PyBool_FromLong(noSetFMUStatePriorToCurrentPoint);
  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_DOSTEP, "(ddO)", currentTime, stepSize, pyNoSetPrior);
  Py_DECREF(pyNoSetPrior);
  return status;
}

fmi2Status PyObjectWrapper::reset()
{
  PyGIL g;
  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_RESET, "()");
  return status;
}

fmi2Status PyObjectWrapper::terminate()
{
  PyGIL g;
  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_TERMINATE, "()");
  return status;
}

fmi2Status PyObjectWrapper::getInteger(const fmi2ValueReference *vr, std::size_t nvr,
                                       fmi2Integer *values) const
{
  PyGIL g;

  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++)
  {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("i", 0));
  }

  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_GETINTEGER, "(OO)", vrs, refs);

  if (status > fmi2Discard)
  {
    Py_DECREF(vrs);
    Py_DECREF(refs);
    return status;
  }

  for (int i = 0; i < nvr; i++)
  {
    PyObject *value = PyList_GetItem(refs, i);

    if (value == nullptr)
    {
      logger->fatal("wrapper", "call to getInterger failed, unable to convert to c-types, error : {}", get_py_exception());
      return fmi2Fatal;
    }

    values[i] = static_cast<int>(PyLong_AsLong(value));
  }

  Py_DECREF(vrs);
  Py_DECREF(refs);
  propagate_python_log_messages();
  return status;
}

fmi2Status PyObjectWrapper::getReal(const fmi2ValueReference *vr, std::size_t nvr,
                                    fmi2Real *values) const
{
  PyGIL g;

  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++)
  {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("d", 0.0));
  }

  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_GETREAL, "(OO)", vrs, refs);

  if (status > fmi2Discard)
  {
    Py_DECREF(vrs);
    Py_DECREF(refs);
    return status;
  }

  for (int i = 0; i < nvr; i++)
  {
    PyObject *value = PyList_GetItem(refs, i);
    if (value == nullptr)
    {
      logger->fatal("wrapper", "call to getReal failed, unable to convert to c-types, error : {}", get_py_exception());
      return fmi2Fatal;
    }
    values[i] = PyFloat_AsDouble(value);
  }

  Py_DECREF(vrs);
  Py_DECREF(refs);
  return status;
}

fmi2Status PyObjectWrapper::getBoolean(const fmi2ValueReference *vr, std::size_t nvr,
                                       fmi2Boolean *values) const
{
  PyGIL g;

  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++)
  {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("i", 0));
  }

  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_GETBOOLEAN, "(OO)", vrs, refs);

  if (status > fmi2Discard)
  {
    Py_DECREF(vrs);
    Py_DECREF(refs);
    return status;
  }

  for (int i = 0; i < nvr; i++)
  {
    PyObject *value = PyList_GetItem(refs, i);
    if (value == nullptr)
    {
      logger->fatal("wrapper", "call to getBoolean failed, unable to convert to c-types, error : {}", get_py_exception());
      return fmi2Fatal;
    }
    values[i] = PyObject_IsTrue(value);
  }

  Py_DECREF(vrs);
  Py_DECREF(refs);
  return status;
}

fmi2Status PyObjectWrapper::getString(const fmi2ValueReference *vr, std::size_t nvr,
                                      fmi2String *values) const
{
  PyGIL g;

  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++)
  {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("s", ""));
  }

  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_GETSTRING, "(OO)", vrs, refs);
  if (status > fmi2Discard)
  {
    Py_DECREF(vrs);
    Py_DECREF(refs);
    return status;
  }

  for (int i = 0; i < nvr; i++)
  {
    PyObject *value = PyList_GetItem(refs, i);
    if (value == nullptr)
    {
      logger->fatal("wrapper", "call to getBoolean failed, unable to convert to c-types, error : {}", get_py_exception());
      return fmi2Fatal;
    }
    values[i] = pyfmu::pyCompat::PyUnicode_AsUTF8(value);
  }

  Py_DECREF(refs);
  propagate_python_log_messages();
  return fmi2OK;
}

fmi2Status PyObjectWrapper::setDebugLogging(fmi2Boolean loggingOn, size_t nCategories, const char *const categories[]) const
{
  PyGIL g;
  auto py_categories = PyList_New(nCategories);

  for (int i = 0; i < nCategories; ++i)
  {
    int err = PyList_SetItem(py_categories, i, Py_BuildValue("s", categories[i]));

    if (err != 0)
    {
      logger->error("wrapper", "Call to setDebugLogging failed due to : {}", get_py_exception());
      return fmi2Error;
    }
  }

  auto status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_SETDEBUGLOGGING, "(iO)", loggingOn, py_categories);
  Py_DECREF(py_categories);

  return status;
}


fmi2Status PyObjectWrapper::setInteger(const fmi2ValueReference *vr, std::size_t nvr,
                                       const fmi2Integer *values)
{ 
  auto builder = [](fmi2Integer val) -> PyObject* {return Py_BuildValue("i",val);};
  return InvokeFmiSetFunction<fmi2Integer>(PYFMU_FMI2SLAVE_SETINTEGER,builder,vr,nvr,values);
}

fmi2Status PyObjectWrapper::setReal(const fmi2ValueReference *vr, std::size_t nvr,
                                    const fmi2Real *values)
{
  auto builder = [](fmi2Real val) -> PyObject* {return Py_BuildValue("d",val);};
  return InvokeFmiSetFunction<fmi2Real>(PYFMU_FMI2SLAVE_SETREAL,builder,vr,nvr,values);
}

fmi2Status PyObjectWrapper::setBoolean(const fmi2ValueReference *vr, std::size_t nvr,
                                       const fmi2Boolean *values)
{
    auto builder = [](fmi2Boolean val) -> PyObject* {return PyBool_FromLong((long)val);};
    return InvokeFmiSetFunction<fmi2Boolean>(PYFMU_FMI2SLAVE_SETBOOLEAN,builder,vr,nvr,values);
}

fmi2Status PyObjectWrapper::setString(const fmi2ValueReference *vr, std::size_t nvr,
                                      const fmi2String *values)
{
  auto builder = [](fmi2String val) -> PyObject* {return Py_BuildValue("s",val);};
  return InvokeFmiSetFunction<fmi2String>(PYFMU_FMI2SLAVE_SETSTRING,builder,vr,nvr,values);
}

PyObjectWrapper::~PyObjectWrapper()
{
  PyGIL g;

  Py_XDECREF(pInstance_);
  Py_XDECREF(pClass_);
  Py_XDECREF(pModule_);
}

PyObjectWrapper &PyObjectWrapper::operator=(PyObjectWrapper &&other)
{
  this->pClass_ = other.pClass_;
  this->pModule_ = other.pModule_;
  this->pInstance_ = other.pInstance_;
  this->logger = move(other.logger);
  return *this;
}

void PyObjectWrapper::propagate_python_log_messages() const
{
  PyGIL g;

  auto f = PyObject_CallMethod(pInstance_, PYFMU_FMI2SLAVE_GETLOGSIZE, "()");

  if (f == nullptr)
  {
    logger->error("Failed to read log messages from the Python instance. Call to _get_log_size failed due to : {}", get_py_exception());
    return;
  }
  Py_DECREF(f);
  long n_messages = PyLong_AsLong(f);

  if (n_messages == -1)
  {
    logger->error("Failed to read log messages from the python instance. Call to _get_log_size returned invalid type: {}", get_py_exception());
    return;
  }

  if (n_messages == 0)
    return;

  f = PyObject_CallMethod(pInstance_, PYFMU_FMI2SLAVE_POPLOGMESSAGES, "(i)", n_messages);

  if (f == nullptr)
  {
    logger->error("Failed to read log messages from the python instacnce. Call to __pop_log_messages failed : {}", get_py_exception());
  }

  for (int i = 0; i < n_messages; ++i)
  {
    PyObject *value = PyList_GetItem(f, i);

    if (value == nullptr)
    {
      logger->warning("wrapper", "Failed to parse read log message : {}", get_py_exception());
      return;
    }

    PyObject *py_status = PyTuple_GetItem(value, 0);
    PyObject *py_category = PyTuple_GetItem(value, 1);
    PyObject *py_message = PyTuple_GetItem(value, 2);

    if (py_status == nullptr || py_category == nullptr || py_message == nullptr)
    {
      auto msg = "Failed to read log messages, unable to unpack message tuples";
      logger->warning("wrapper", msg);
    }
    fmi2Status status = (fmi2Status)(PyLong_AsLong(py_status));
    auto category = pyfmu::pyCompat::PyUnicode_AsString(py_category);
    auto message = pyfmu::pyCompat::PyUnicode_AsString(py_message);

    // we need to escape '{' and '}' which are common in Python's output
    auto re_left = std::regex("\\{");
    auto re_right = std::regex("\\}");
    message = std::regex_replace(message, re_left, "{{");
    message = std::regex_replace(message, re_right, "}}");

    logger->log(status, category, message);
  }
}

} // namespace pyfmu
