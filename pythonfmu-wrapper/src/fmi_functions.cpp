#include <exception>
#include <limits>
#include <memory>
#include <map>
#include <vector>
#include <optional>

#include "Python.h"
#include "fmt/format.h"

#include "fmi/fmi2Functions.h"
#include "pythonfmu/Logger.hpp"
#include "pythonfmu/PyInitializer.hpp"
#include "pythonfmu/PyObjectWrapper.hpp"
#include "utility/utils.hpp"

using namespace fmt;
using namespace std;

std::optional<string> validate_fmi2callbackFunctions(const fmi2CallbackFunctions *functions)
{

  string msg = "";

  if (functions == nullptr)
  {
    return msg + "pointer to callback function points was a nullptr\n.";
  }

  bool hasAllocateMemory = functions->allocateMemory != nullptr;
  bool hasFreeMemory = functions->freeMemory != nullptr;
  bool hasLogger = functions->logger != nullptr;
  bool hasStepFinished = functions->stepFinished != nullptr;

  //bool isValid = hasAllocateMemory && hasFreeMemory && hasLogger && hasStepFinished;
  bool isValid = hasAllocateMemory && hasFreeMemory && hasLogger;

  if (isValid)
    return {};

  if (!hasLogger)
    msg.append(" no allocate memory function was specified ");
  if (!hasFreeMemory)
    msg.append(" no free memory function was specified ");

  if (!hasLogger)
    msg.append(" no free memory function was specified ");

  if (!hasStepFinished)
    msg.append(" no step finished function was specified");

  return msg;
}

// FMI functions
extern "C" {

// =============================================================================
// FMI 2.0 functions
// =============================================================================

const char *fmi2GetTypesPlatform() { return fmi2TypesPlatform; }

const char *fmi2GetVersion() { return "2.0"; }

using namespace pythonfmu;
using namespace std;

vector<PyObjectWrapper> components;
PyObjectWrapper *component = nullptr;
PyInitializer *pyInitializer = nullptr;

bool loggingOn_ = false;

fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType,
                              fmi2String fmuGUID,
                              fmi2String fmuResourceLocation,
                              const fmi2CallbackFunctions *functions,
                              fmi2Boolean visible, fmi2Boolean loggingOn)
{

  auto callbacksValid = validate_fmi2callbackFunctions(functions);

  if (callbacksValid.has_value())
  {
    print(stderr, "Failed to instantiate FMU, supplied callback functions were invalid due to: {}", callbacksValid.value());
    return NULL;
  }

  Logger *logger = new Logger(functions->componentEnvironment, functions->logger, instanceName);

  logger->log(fmi2Status::fmi2OK, "Info", "Instantiating FMU\n");

  logger->log(fmi2Status::fmi2OK, "Info", "Initializing Python interpreter\n");

  try
  {
    pyInitializer = new PyInitializer(logger);
  }
  catch (exception)
  {
    logger->log(fmi2Status::fmi2Fatal, "error", "failed to initialize embedded Python interpreter\n");
    return NULL;
  }

  logger->log(fmi2Status::fmi2OK, "Info",
              "Successfully initialized Python interpreter\n");

  logger->log(fmi2Status::fmi2OK, "Info", "Initializing Python FMU wrapper\n");

  auto fmuResourceLocationPath = getPathFromFileUri(fmuResourceLocation);

  try
  {
    component = new PyObjectWrapper(fmuResourceLocationPath, move(logger));

    return component;
  }
  catch (exception)
  {
    //logger->log(fmi2Status::fmi2Fatal, "Error", "failed to load main script\n");
    return NULL;
  }
}

void fmi2FreeInstance(fmi2Component c)
{
  // TODO implement correctly
}

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,
                               size_t nCategories,
                               const fmi2String categories[])
{
  
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    const char* arr[] = {"test"};
    cc->setDebugLogging(true,1,categories);
  }
  catch (const exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined,
                               fmi2Real tolerance, fmi2Real startTime,
                               fmi2Boolean stopTimeDefined, fmi2Real stopTime)
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->setupExperiment(startTime);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c)
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->enterInitializationMode();
  }
  catch (const exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2ExitInitializationMode(fmi2Component c)
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->exitInitializationMode();
  }
  catch (const exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2Terminate(fmi2Component c)
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->terminate();
  }
  catch (const exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2Reset(fmi2Component c)
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->reset();
  }
  catch (const exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, fmi2Real value[])
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->getReal(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Integer value[])
{
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->getInteger(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Boolean value[])
{
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->getBoolean(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, fmi2String value[])
{
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->getString(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, const fmi2Real value[])
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->setReal(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Integer value[])
{
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->setInteger(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Boolean value[])
{
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->setBoolean(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, const fmi2String value[])
{
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->setString(vr, nvr, value);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate *)
{
  return fmi2Error;
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate) { return fmi2Error; }

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate *)
{
  return fmi2Error;
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate, size_t *)
{
  return fmi2Error;
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate, fmi2Byte[],
                                 size_t)
{
  return fmi2Error;
}

fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte[], size_t,
                                   fmi2FMUstate *)
{
  return fmi2Error;
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
                      fmi2Real communicationStepSize, fmi2Boolean)
{

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try
  {
    cc->doStep(currentCommunicationPoint, communicationStepSize);
  }
  catch (exception)
  {
    return fmi2Error;
  }

  return fmi2OK;
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
