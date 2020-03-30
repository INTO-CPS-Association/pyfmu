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
#include "pyfmu/fmi2Config.hpp"

using namespace fmt;
using namespace pyconfiguration;
using namespace std;
using namespace filesystem;





namespace pyfmu
{

/**
 * @brief Callaback function used by the Python slave to do logging.
 * This function must be a free function. As such the logger is injected using a PyCapsule.
 * 
 * @param self a PyCapsule object used to pass a point
 * @param args a python tuple of status,category and string (int,string,string)
 * @return PyObject* 
 */
static PyObject* logCallback(PyObject* self, PyObject* args)
{ 
  PyGIL g;

  // extract logging context from capsule
  Logger* logger = (Logger*)PyCapsule_GetPointer(self,nullptr);
  
  fmi2Status status;
  const char* message;
  const char* category;

  int s = PyArg_Parse(args,"(iss)",&status,&category,&message);

  if(s == 0)
  {
    logger->warning("Logger callback called, but wrapper was unable to parse arguments : {}.", get_py_exception());
  }
  else
  {
    logger->log(status,category,message);
  }

  Py_RETURN_NONE;
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
  //PyObject* PyObject_Call(PyObject *callable, PyObject *args, PyObject *kwargs) https://docs.python.org/3/c-api/object.html
  pInstance_ = PyObject_CallFunctionObjArgs(pClass_, nullptr);

  if (pInstance_ == nullptr)
  {
    auto pyErr = get_py_exception();
    auto msg = format("Failed to instantiate class: {}, ensure that the Python script is valid and that defines a parameterless constructor. Python error was:\n{}\n", main_class, pyErr);
    logger->fatal("wrapper", msg);
    throw runtime_error(msg);
  }


  // pass logging function to python slave
  // since the callback must be a free function, we need to somehow pass a pointer to the concrete logger instance
  // for this we use "capsules" which allow opaque pointers to be passed between modules.
  PyMethodDef pCallbackDef = {
    "logCallback",
    logCallback,
    METH_VARARGS,
    ""};
  
  auto loggerCapsule = PyCapsule_New(logger,nullptr,nullptr);
  auto pCallbackFunc = PyCFunction_New(&pCallbackDef,loggerCapsule);
  auto f = PyObject_CallMethod(pInstance_, "_register_log_callback", "(O)", pCallbackFunc);

  if(f == nullptr)
  {
    string msg = fmt::format("wrapper", "Failed to register callback for logging. An exception was thrown in Python: {}", get_py_exception());
    logger->error(PYFMU_WRAPPER_LOG_CATEGORY,msg);
    throw runtime_error(msg);
  }
  
  logger->ok("wrapper", "Successfully created an instance of class: {} defined in module: {}", main_class, module_name);
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
  
  fmi2Status status;
  if(toleranceDefined && stopTimeDefined)
  {
    status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_SETUPEXPERIMENT, "(ddd)",startTime,tolerance,stopTime);
  }
  else if(toleranceDefined)
  {
    status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_SETUPEXPERIMENT, "(ddO)",startTime,tolerance,Py_None);
  }
  else
  {
    status = InvokeFmiOnSlave(PYFMU_FMI2SLAVE_SETUPEXPERIMENT, "(dOd)",startTime,Py_None,stopTime);
  }

  return status;
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

  auto buildFunc = []() -> PyObject* {
    return Py_BuildValue("i", 0);
  };

  auto convertFunc =  [](PyObject* obj) -> fmi2Integer {
    return (fmi2Integer)PyLong_AsLong(obj);
  };
  auto status = InvokeFmiGetXXXFunction<fmi2Integer>(PYFMU_FMI2SLAVE_GETINTEGER,buildFunc,convertFunc,vr,nvr,values);
  return status;
}

fmi2Status PyObjectWrapper::getReal(const fmi2ValueReference *vr, std::size_t nvr,
                                    fmi2Real *values) const
{
  auto buildFunc = []() -> PyObject* {
    return Py_BuildValue("d", 0.0);
  };

  auto convertFunc =  [](PyObject* obj) -> fmi2Real {
    return (fmi2Real)PyFloat_AsDouble(obj);
  };
  auto status = InvokeFmiGetXXXFunction<fmi2Real>(PYFMU_FMI2SLAVE_GETREAL,buildFunc,convertFunc,vr,nvr,values);
  return status;
}

fmi2Status PyObjectWrapper::getBoolean(const fmi2ValueReference *vr, std::size_t nvr,
                                       fmi2Boolean *values) const
{

  auto buildFunc = []() -> PyObject* {
    return PyBool_FromLong(0);
  };

  auto convertFunc =  [](PyObject* obj) -> fmi2Boolean {
    return PyObject_IsTrue(obj);
  };
  auto status = InvokeFmiGetXXXFunction<fmi2Boolean>(PYFMU_FMI2SLAVE_GETBOOLEAN,buildFunc,convertFunc,vr,nvr,values);
  return status;
}

fmi2Status PyObjectWrapper::getString(const fmi2ValueReference *vr, std::size_t nvr,
                                      fmi2String *values) const
{


  auto buildFunc = []() -> PyObject* {
    return Py_BuildValue("s", "");
  };

  auto convertFunc =  [](PyObject* obj) -> fmi2String {
    return pyfmu::pyCompat::PyUnicode_AsUTF8(obj);
  };
  auto status = InvokeFmiGetXXXFunction<fmi2String>(PYFMU_FMI2SLAVE_GETREAL,buildFunc,convertFunc,vr,nvr,values);
  return status;
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
  return InvokeFmiSetXXXFunction<fmi2Integer>(PYFMU_FMI2SLAVE_SETINTEGER,builder,vr,nvr,values);
}

fmi2Status PyObjectWrapper::setReal(const fmi2ValueReference *vr, std::size_t nvr,
                                    const fmi2Real *values)
{
  auto builder = [](fmi2Real val) -> PyObject* {return Py_BuildValue("d",val);};
  return InvokeFmiSetXXXFunction<fmi2Real>(PYFMU_FMI2SLAVE_SETREAL,builder,vr,nvr,values);
}

fmi2Status PyObjectWrapper::setBoolean(const fmi2ValueReference *vr, std::size_t nvr,
                                       const fmi2Boolean *values)
{
    auto builder = [](fmi2Boolean val) -> PyObject* {return PyBool_FromLong((long)val);};
    return InvokeFmiSetXXXFunction<fmi2Boolean>(PYFMU_FMI2SLAVE_SETBOOLEAN,builder,vr,nvr,values);
}

fmi2Status PyObjectWrapper::setString(const fmi2ValueReference *vr, std::size_t nvr,
                                      const fmi2String *values)
{
  auto builder = [](fmi2String val) -> PyObject* {return Py_BuildValue("s",val);};
  return InvokeFmiSetXXXFunction<fmi2String>(PYFMU_FMI2SLAVE_SETSTRING,builder,vr,nvr,values);
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

} // namespace pyfmu
