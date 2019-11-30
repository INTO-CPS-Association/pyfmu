
#include <pythonfmu/PyObjectWrapper.hpp>

#include <cppfmu/cppfmu_common.hpp>

#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <utility>
#include <pythonfmu/PyException.hpp>

using namespace std;
using namespace filesystem;

void append_resources_folder_to_python_interpreter(std::string const &resource_path)
{
    ostringstream oss;
    oss << "import sys\n";
    oss << "sys.path.append(r'" << resource_path << "')\n";

    string path_str = oss.str();
    const char *path_cstr = path_str.c_str();

    int err = PyRun_SimpleString(path_cstr);
}


namespace
{

inline std::string getline(const std::string &fileName)
{
    std::string line;
    std::ifstream infile(fileName);
    std::getline(infile, line);
    return line;
}

inline const char *get_class_name(PyObject *pModule)
{
    auto f = PyObject_GetAttrString(pModule, "slave_class");
    if (f != nullptr)
    {
        return PyUnicode_AsUTF8(f);
    }
    return nullptr;
}

} // namespace

namespace pythonfmu
{

string get_python_module_name(string resource_path)
{
    path script_path = path(resource_path) / "script_config.txt"; 


    ifstream config(script_path);

    if (!config)
    {
        ostringstream oss;
        oss << "Could not locate configuration file pointing to the main Python class. \nThe file following file does not exist: " 
        << script_path << ", in the current path: " << current_path();
        throw runtime_error(oss.str().c_str());
    }

    string moduleName;
    getline(config, moduleName, '/');

    return moduleName;
}

PyObject* load_python_module(std::string const& module_name) 
{
    auto pModule_ = PyImport_ImportModule(module_name.c_str());

    if (pModule_ == nullptr)
    {
        auto err = get_py_exception();
        ostringstream oss;
        oss << "Python module defining containing main Python class could not be loaded. Ensure that a file named script_config.txt exists in the resource folder."
        << "\nThis file must contain a single line defining the name of the module containing this class. For example if the given module is named adder.py the file should contain the line adder\n"
        << "Error message from Python is:\n" << err;

        throw runtime_error(oss.str());
    }

    return pModule_;
}

PyObject* get_main_class(PyObject* pModule)
{
    PyObject* attr = PyObject_GetAttrString(pModule, "slave_class");

    if(attr == nullptr)
    {
        auto err = get_py_exception();
        ostringstream oss;
        oss << "Failed to extract the name of the main Python class from the module. Ensure that the module defines a property named 'slave_class' which is equal to the name of the main Python class, such as 'slave_class = 'Adder'\n"
            << "Error message from Python is:\n" << err;

        throw runtime_error(oss.str());
    }

    
    const char* class_name = PyUnicode_AsUTF8(attr);
    PyObject* pClass = PyObject_GetAttrString(pModule, class_name);

    if(pClass == nullptr)
    {
        auto err = get_py_exception();
        ostringstream oss;
        oss << "Main Python class name, " << class_name << ", does not match any class exported by the module. Ensure that the 'slave_class' property is set to a class defined in that module."
            << "Error message from Python is:\n" << err;

        throw runtime_error(oss.str());
    }

    return pClass;
}

PyObject* instantiate_main_class(PyObject* pClass)
{
    PyObject* pInstance = PyObject_CallFunctionObjArgs(pClass, nullptr);

    if(pInstance == nullptr)
    {
        auto err = get_py_exception();
        ostringstream oss;
        oss << "Failed to instantiate main Python class. Ensure that the class defines a constructor which accepts no parameters\n."
            << "Error message from python is:\n" << err;
        throw runtime_error(oss.str());
    }

    return pInstance;
}

PyObjectWrapper::PyObjectWrapper(const std::string &resource_path)
{
    
    if (!Py_IsInitialized())
    {
        throw runtime_error("The Python object cannot be instantiated due to the python intrepeter not being instantiated. Ensure that Py_Initialize() is invoked successfully prior to the invoking the constructor.");
    }


    string moduleName = get_python_module_name(resource_path);
    
    append_resources_folder_to_python_interpreter(resource_path);

    pModule_ = load_python_module(moduleName);

    pClass_ = get_main_class(pModule_);

    pInstance_ = instantiate_main_class(pClass_);
}

void PyObjectWrapper::setupExperiment(double startTime)
{
    auto f = PyObject_CallMethod(pInstance_, "setup_experiment", "(d)", startTime);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);
}

void PyObjectWrapper::enterInitializationMode()
{
    auto f = PyObject_CallMethod(pInstance_, "enter_initialization_mode", nullptr);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);
}

void PyObjectWrapper::exitInitializationMode()
{
    auto f = PyObject_CallMethod(pInstance_, "exit_initialization_mode", nullptr);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);
}

bool PyObjectWrapper::doStep(double currentTime, double stepSize)
{
    auto f = PyObject_CallMethod(pInstance_, "do_step", "(dd)", currentTime, stepSize);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    bool status = static_cast<bool>(PyObject_IsTrue(f));
    Py_DECREF(f);
    return status;
}

void PyObjectWrapper::reset()
{
    auto f = PyObject_CallMethod(pInstance_, "reset", nullptr);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);
}

void PyObjectWrapper::terminate()
{
    auto f = PyObject_CallMethod(pInstance_, "terminate", nullptr);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);
}

void PyObjectWrapper::getInteger(const cppfmu::FMIValueReference *vr, std::size_t nvr, cppfmu::FMIInteger *values) const
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, Py_BuildValue("i", 0));
    }
    auto f = PyObject_CallMethod(pInstance_, "__get_integer__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);

    for (int i = 0; i < nvr; i++)
    {
        PyObject *value = PyList_GetItem(refs, i);
        values[i] = static_cast<int>(PyLong_AsLong(value));
    }

    Py_DECREF(refs);
}

void PyObjectWrapper::getReal(const cppfmu::FMIValueReference *vr, std::size_t nvr, cppfmu::FMIReal *values) const
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, Py_BuildValue("d", 0.0));
    }

    auto f = PyObject_CallMethod(pInstance_, "__get_real__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);

    for (int i = 0; i < nvr; i++)
    {
        PyObject *value = PyList_GetItem(refs, i);
        values[i] = PyFloat_AsDouble(value);
    }

    Py_DECREF(refs);
}

void PyObjectWrapper::getBoolean(const cppfmu::FMIValueReference *vr, std::size_t nvr, cppfmu::FMIBoolean *values) const
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, Py_BuildValue("i", 0));
    }
    auto f = PyObject_CallMethod(pInstance_, "__get_boolean__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);

    for (int i = 0; i < nvr; i++)
    {
        PyObject *value = PyList_GetItem(refs, i);
        values[i] = PyObject_IsTrue(value);
    }

    Py_DECREF(refs);
}

void PyObjectWrapper::getString(const cppfmu::FMIValueReference *vr, std::size_t nvr, cppfmu::FMIString *values) const
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, Py_BuildValue("s", ""));
    }
    auto f = PyObject_CallMethod(pInstance_, "__get_string__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);

    for (int i = 0; i < nvr; i++)
    {
        PyObject *value = PyList_GetItem(refs, i);
        values[i] = PyUnicode_AsUTF8(value);
    }

    Py_DECREF(refs);
}

void PyObjectWrapper::setInteger(const cppfmu::FMIValueReference *vr, std::size_t nvr, const cppfmu::FMIInteger *values)
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, Py_BuildValue("i", values[i]));
    }

    auto f = PyObject_CallMethod(pInstance_, "__set_integer__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    Py_DECREF(refs);

    if (f == nullptr)
    {
        handle_py_exception();
    }

    Py_DECREF(f);
}

void PyObjectWrapper::setReal(const cppfmu::FMIValueReference *vr, std::size_t nvr, const cppfmu::FMIReal *values)
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, Py_BuildValue("d", values[i]));
    }

    auto f = PyObject_CallMethod(pInstance_, "__set_real__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    Py_DECREF(refs);

    if (f == nullptr)
    {
        auto err = get_py_exception();
        ostringstream oss;
        oss << "Failed to set real values of the python instance. Ensure that the script implements the '__set__real__' method correctly, for example by inheriting from 'FMI2Slave'.\n"
            << "Python error is:\n" << err;
        throw runtime_error(oss.str());
    }

    Py_DECREF(f);
}

void PyObjectWrapper::setBoolean(const cppfmu::FMIValueReference *vr, std::size_t nvr, const cppfmu::FMIBoolean *values)
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, PyBool_FromLong(values[i]));
    }

    auto f = PyObject_CallMethod(pInstance_, "__set_boolean__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    Py_DECREF(refs);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);
}

void PyObjectWrapper::setString(const cppfmu::FMIValueReference *vr, std::size_t nvr, const cppfmu::FMIString *value)
{
    PyObject *vrs = PyList_New(nvr);
    PyObject *refs = PyList_New(nvr);
    for (int i = 0; i < nvr; i++)
    {
        PyList_SetItem(vrs, i, Py_BuildValue("i", vr[i]));
        PyList_SetItem(refs, i, Py_BuildValue("s", value[i]));
    }

    auto f = PyObject_CallMethod(pInstance_, "__set_string__", "(OO)", vrs, refs);
    Py_DECREF(vrs);
    Py_DECREF(refs);
    if (f == nullptr)
    {
        handle_py_exception();
    }
    Py_DECREF(f);
}

PyObjectWrapper::~PyObjectWrapper()
{
    Py_XDECREF(pInstance_);
    Py_XDECREF(pClass_);
    Py_XDECREF(pModule_);
}

} // namespace pythonfmu