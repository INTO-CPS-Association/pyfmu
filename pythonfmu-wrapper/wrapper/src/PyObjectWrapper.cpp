
#include <pythonfmu/PyObjectWrapper.hpp>

#include "fmi/fmi2TypesPlatform.h"
#include "pythonfmu/PyConfiguration.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <pythonfmu/PyException.hpp>
#include <sstream>
#include <utility>

using namespace std;
using namespace filesystem;
using namespace pyconfiguration;

extern "C" {
int foo() 
    {   
      int a = 100;


      int b = 100*20;

      return 10; 
    }
}

namespace pythonfmu {

/**
 * @brief Appends path of resources folder to the Python interpreter path. This
 * allows the interpreter to locate and load the main script.
 *
 * @param resource_path path to the resources dir supplied when FMU is
 * initialized
 */
void append_resources_folder_to_python_path(string &resource_path) {

  ostringstream oss;
  oss << "import sys\n";
  oss << "sys.path.append(r'" << resource_path << "')\n";

  string str = oss.str();
  const char *cstr = str.c_str();


  int err = PyRun_SimpleString(cstr);



  if(err != 0)
    throw runtime_error("Failed to append folder to python path\n"); 

}

string get_python_module_name(string resource_path) {
  path script_path = path(resource_path) / "script_config.txt";

  ifstream config(script_path);

  if (!config) {
    ostringstream oss;
    oss << "Could not locate configuration file pointing to the main Python "
           "class. \nThe file following file does not exist: "
        << script_path << ", in the current path: " << current_path();
    throw runtime_error(oss.str().c_str());
  }

  string moduleName;
  getline(config, moduleName, '/');

  return moduleName;
}

void PyObjectWrapper::instantiate_main_class(string module_name,
                                             string main_class) {


   pModule_ = PyImport_ImportModule(module_name.c_str());


  if (pModule_ == NULL) {
    PyErr_Print();
    auto err = get_py_exception();
    ostringstream oss;
    oss << "Python module defining containing main Python class could not be "
           "loaded. Ensure that a file named slave_configuration.json exists "
           "in the resource folder."
        << "\nThis file must contain a single line defining the name of the "
           "module containing this class. For example if the given module is "
           "named adder.py the file should contain the line adder\n"
        << "Error message from Python is:\n"
        << err;

    throw runtime_error(oss.str());
  }

  pClass_ = PyObject_GetAttrString(pModule_, main_class.c_str());

  if (pClass_ == nullptr) {
    auto err = get_py_exception();
    ostringstream oss;
    oss << "Main Python class name, " << main_class
        << ", does not match any class exported by the module. Ensure that the "
           "'slave_class' property is set to a class defined in that module."
        << "Error message from Python is:\n"
        << err;

    throw runtime_error(oss.str());
  }

  pInstance_ = PyObject_CallFunctionObjArgs(pClass_, nullptr);

  if (pInstance_ == nullptr) {
    auto err = get_py_exception();
    ostringstream oss;
    oss << "Failed to instantiate main Python class. Ensure that the class "
           "defines a constructor which accepts no parameters\n."
        << "Error message from python is:\n"
        << err;
    throw runtime_error(oss.str());
  }
}

PyObjectWrapper::PyObjectWrapper(fmi2String resource_path, unique_ptr<Logger> logger) :  logger(move(logger)){


  auto state = PyGILState_Ensure();  

  if (!Py_IsInitialized()) {
    throw runtime_error(
        "The Python object cannot be instantiated due to the python intrepeter "
        "not being instantiated. Ensure that Py_Initialize() is invoked "
        "successfully prior to the invoking the constructor.");
  }


  string resource_path_str = resource_path;
  string config_path = path(resource_path) / "slave_configuration.json";



  append_resources_folder_to_python_path(resource_path_str);

  auto config = read_configuration(config_path);

  string module_name =
      path(config.main_script).filename().replace_extension("");


  instantiate_main_class(module_name, config.main_class);

  PyGILState_Release(state);

}

void PyObjectWrapper::setupExperiment(double startTime) {
  auto f =
      PyObject_CallMethod(pInstance_, "setup_experiment", "(d)", startTime);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);
}

void PyObjectWrapper::enterInitializationMode() {
  auto f =
      PyObject_CallMethod(pInstance_, "enter_initialization_mode", nullptr);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);
}

void PyObjectWrapper::exitInitializationMode() {
  auto f = PyObject_CallMethod(pInstance_, "exit_initialization_mode", nullptr);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);
}

bool PyObjectWrapper::doStep(double currentTime, double stepSize) {
  auto f =
      PyObject_CallMethod(pInstance_, "do_step", "(dd)", currentTime, stepSize);
  if (f == nullptr) {
    handle_py_exception();
  }
  bool status = static_cast<bool>(PyObject_IsTrue(f));
  Py_DECREF(f);
  return status;
}

void PyObjectWrapper::reset() {
  auto f = PyObject_CallMethod(pInstance_, "reset", nullptr);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);
}

void PyObjectWrapper::terminate() {
  auto f = PyObject_CallMethod(pInstance_, "terminate", nullptr);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);
}

void PyObjectWrapper::getInteger(const fmi2ValueReference *vr, std::size_t nvr,
                                 fmi2Integer *values) const {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("i", 0));
  }
  auto f =
      PyObject_CallMethod(pInstance_, "__get_integer__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);

  for (int i = 0; i < nvr; i++) {
    PyObject *value = PyList_GetItem(refs, i);
    values[i] = static_cast<int>(PyLong_AsLong(value));
  }

  Py_DECREF(refs);
}

void PyObjectWrapper::getReal(const fmi2ValueReference *vr, std::size_t nvr,
                              fmi2Real *values) const {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("d", 0.0));
  }

  auto f = PyObject_CallMethod(pInstance_, "__get_real__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);

  for (int i = 0; i < nvr; i++) {
    PyObject *value = PyList_GetItem(refs, i);
    values[i] = PyFloat_AsDouble(value);
  }

  Py_DECREF(refs);
}

void PyObjectWrapper::getBoolean(const fmi2ValueReference *vr, std::size_t nvr,
                                 fmi2Boolean *values) const {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("i", 0));
  }
  auto f =
      PyObject_CallMethod(pInstance_, "__get_boolean__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);

  for (int i = 0; i < nvr; i++) {
    PyObject *value = PyList_GetItem(refs, i);
    values[i] = PyObject_IsTrue(value);
  }

  Py_DECREF(refs);
}

void PyObjectWrapper::getString(const fmi2ValueReference *vr, std::size_t nvr,
                                fmi2String *values) const {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("s", ""));
  }
  auto f = PyObject_CallMethod(pInstance_, "__get_string__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);

  for (int i = 0; i < nvr; i++) {
    PyObject *value = PyList_GetItem(refs, i);
    values[i] = PyUnicode_AsUTF8(value);
  }

  Py_DECREF(refs);
}

void PyObjectWrapper::setInteger(const fmi2ValueReference *vr, std::size_t nvr,
                                 const fmi2Integer *values) {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("i", values[i]));
  }

  auto f =
      PyObject_CallMethod(pInstance_, "__set_integer__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  Py_DECREF(refs);

  if (f == nullptr) {
    handle_py_exception();
  }

  Py_DECREF(f);
}

void PyObjectWrapper::setReal(const fmi2ValueReference *vr, std::size_t nvr,
                              const fmi2Real *values) {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("d", values[i]));
  }

  auto f = PyObject_CallMethod(pInstance_, "__set_real__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  Py_DECREF(refs);

  if (f == nullptr) {
    auto err = get_py_exception();
    ostringstream oss;
    oss << "Failed to set real values of the python instance. Ensure that the "
           "script implements the '__set__real__' method correctly, for "
           "example by inheriting from 'FMI2Slave'.\n"
        << "Python error is:\n"
        << err;
    throw runtime_error(oss.str());
  }

  Py_DECREF(f);
}

void PyObjectWrapper::setBoolean(const fmi2ValueReference *vr, std::size_t nvr,
                                 const fmi2Boolean *values) {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, PyBool_FromLong(values[i]));
  }

  auto f =
      PyObject_CallMethod(pInstance_, "__set_boolean__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  Py_DECREF(refs);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);
}

void PyObjectWrapper::setString(const fmi2ValueReference *vr, std::size_t nvr,
                                const fmi2String *value) {
  PyObject *vrs = PyList_New(nvr);
  PyObject *refs = PyList_New(nvr);
  for (int i = 0; i < nvr; i++) {
    PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
    PyList_SetItem(refs, i, Py_BuildValue("s", value[i]));
  }

  auto f = PyObject_CallMethod(pInstance_, "__set_string__", "(OO)", vrs, refs);
  Py_DECREF(vrs);
  Py_DECREF(refs);
  if (f == nullptr) {
    handle_py_exception();
  }
  Py_DECREF(f);
}

PyObjectWrapper::~PyObjectWrapper() {
  Py_XDECREF(pInstance_);
  Py_XDECREF(pClass_);
  Py_XDECREF(pModule_);
}

} // namespace pythonfmu
