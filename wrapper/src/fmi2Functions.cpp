#include <exception>
#include <limits>
#include <memory>
#include <map>
#include <vector>
#include <optional>

#include <Python.h>
#include <fmt/format.h>

#include "fmi/fmi2Functions.h"
#include "pyfmu/fmi2PySlaveLogging.hpp"
#include "pyfmu/fmi2PySlave.hpp"
#include "pyfmu/utils.hpp"


using namespace fmt;
using namespace std;
using namespace filesystem;

// FMI functions
extern "C" {

// =============================================================================
// FMI 2.0 functions
// =============================================================================

const char *fmi2GetTypesPlatform() { return fmi2TypesPlatform; }

const char *fmi2GetVersion() { return "2.0"; }

using namespace pyfmu;
using namespace std;
using namespace filesystem;

bool loggingOn_ = false;

void noOpsLogCallback(fmi2ComponentEnvironment,fmi2String,fmi2Status,fmi2String,fmi2String,...){}

fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType,
                              fmi2String fmuGUID,
                              fmi2String fmuResourceLocation,
                              const fmi2CallbackFunctions *functions,
                              fmi2Boolean visible, fmi2Boolean loggingOn)
{

  bool useLogger = functions != nullptr && functions->logger && loggingOn;

  Logger *logger;

  if (useLogger)
  {
    logger = new Logger(functions->componentEnvironment, functions->logger, instanceName);
  }
  else
  {
    logger = new Logger(functions->componentEnvironment, noOpsLogCallback, instanceName);
  }

  if (!Py_IsInitialized())
  {

    logger->ok("wrapper", "Initializing Python interpreter");
      
    auto var = Py_GetVersion();
    Py_Initialize();
    loadPythonSharedObject();
  
  }
  else
  {
    logger->ok("wrapper", "Python interpreter is already initialized, continuing");
  }

  const wchar_t *home = Py_GetPythonHome() ? Py_GetPythonHome() : L"undefined";
  const wchar_t *path = Py_GetPath() ? Py_GetPath() : L"undefined";

  std::string home_str = ws2s(std::wstring(home));
  std::string path_str = ws2s(std::wstring(path));

  logger->ok("wrapper", "Python interpreter successfully initialized, Python home is : {}, Python path is : {}", home_str, path_str);

  logger->ok("wrapper", "Starting initialization of FMU, attempting to parse URI pointing to the FMUs resource directory");

  filesystem::path resourcesPath("");
  try
  {
    resourcesPath = getPathFromFileUri(fmuResourceLocation);
    logger->ok("wrapper", "Successfully parsed the resource folder URI pointing to : {}", resourcesPath.string());
  }
  catch (const std::exception &)
  {
    logger->fatal("wrapper", "Unable to parse the URI : {} pointing to the python scripts in the resource folder.", fmuResourceLocation);
    return nullptr;
  }

  try
  {
    return new PyObjectWrapper(resourcesPath, move(logger));
  }
  catch (const std::exception &)
  {
    return nullptr;
  }
}

void fmi2FreeInstance(fmi2Component c)
{
  try
  {
    if (c != nullptr)
    {
      auto cc = reinterpret_cast<PyObjectWrapper *>(c);
      delete cc;
    }
  }
  catch (const std::exception &)
  {
    // TODO
  }
}

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,
                               size_t nCategories,
                               const fmi2String categories[])
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->setDebugLogging(true, nCategories, categories);
  }
  catch (const exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined,
                               fmi2Real tolerance, fmi2Real startTime,
                               fmi2Boolean stopTimeDefined, fmi2Real stopTime)
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->setupExperiment(toleranceDefined,tolerance,startTime,stopTimeDefined,stopTime);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c)
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->enterInitializationMode();
  }
  catch (const exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2ExitInitializationMode(fmi2Component c)
{

  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->exitInitializationMode();
  }
  catch (const exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2Terminate(fmi2Component c)
{

  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->terminate();
  }
  catch (const exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2Reset(fmi2Component c)
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->reset();
  }
  catch (const exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, fmi2Real value[])
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->getReal(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Integer value[])
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->getInteger(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Boolean value[])
{

  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->getBoolean(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, fmi2String value[])
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->getString(vr, nvr, value);
  }
  catch (const exception &)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, const fmi2Real value[])
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->setReal(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Integer value[])
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->setInteger(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Boolean value[])
{

  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->setBoolean(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, const fmi2String value[])
{

  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->setString(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate *)
{
  return fmi2Discard;
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate) { return fmi2Fatal; }

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate *)
{
  return fmi2Discard;
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate, size_t *)
{
  return fmi2Discard;
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate, fmi2Byte[],
                                 size_t)
{
  return fmi2Discard;
}

fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte[], size_t,
                                   fmi2FMUstate *)
{
  return fmi2Discard;
}

fmi2Status fmi2GetDirectionalDerivative(fmi2Component c,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2Real[], fmi2Real[])
{
  return fmi2Error;
}

fmi2Status fmi2SetRealInputDerivatives(fmi2Component c,
                                       const fmi2ValueReference[], size_t,
                                       const fmi2Integer[], const fmi2Real[])
{
  return fmi2Error;
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2Integer[], fmi2Real[])
{
  return fmi2Error;
}

fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint,
                      fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint)
{
  try
  {
    auto cc = reinterpret_cast<PyObjectWrapper *>(c);
    return cc->doStep(currentCommunicationPoint, communicationStepSize,noSetFMUStatePriorToCurrentPoint);
  }
  catch (exception)
  {
    return fmi2Fatal;
  }
}

fmi2Status fmi2CancelStep(fmi2Component c) { return fmi2Error; }

fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind, fmi2Status *)
{
  return fmi2Error;
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s,
                             fmi2Real *value)
{
  return fmi2Error;
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind,
                                fmi2Integer *)
{
  return fmi2Error;
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind,
                                fmi2Boolean *)
{
  return fmi2Error;
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind,
                               fmi2String *)
{
  return fmi2Error;
}
}
