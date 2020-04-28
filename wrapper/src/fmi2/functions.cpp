#include <exception>
#include <limits>
#include <memory>
#include <map>
#include <vector>
#include <optional>

#include <fmt/format.h>

#include "spec/fmi2/fmi2Functions.h"

#include "pyfmu/fmi2/logging.hpp"
#include "pyfmu/fmi2/slaveWrapperAdapter.hpp"
#include "pyfmu/utils.hpp"

using namespace fmt;
using namespace std;
using namespace filesystem;

// FMI functions
extern "C"
{

  // =============================================================================
  // FMI 2.0 functions
  // =============================================================================

  const char *fmi2GetTypesPlatform() { return fmi2TypesPlatform; }

  const char *fmi2GetVersion() { return "2.0"; }

  using namespace pyfmu::fmi2;
  using namespace std;
  using std::filesystem::path;

  bool loggingOn_ = false;

  void noOpsLogCallback(fmi2ComponentEnvironment, fmi2String, fmi2Status, fmi2String, fmi2String, ...) {}

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

    logger->ok("wrapper", "Initializing Python interpreter");

    logger->ok("wrapper", "Python interpreter successfully initialized, Python home is : {}, Python path is : {}", "TODO", "TODO");

    logger->ok("wrapper", "Starting initialization of FMU, attempting to parse URI pointing to the FMUs resource directory");

    try
    {
      path resourcesPath = getPathFromFileUri(fmuResourceLocation);
      logger->ok("wrapper", "Successfully parsed the resource folder URI pointing to : {}", resourcesPath.string());
      //return new SlaveWrapperAdapter(resourcesPath, logger);
      return nullptr; // TODO
    }
    catch (const std::exception &e)
    {
      logger->fatal("wrapper", "Failed to instantiate the FMU, an error was raised: {}.", e.what());
      return nullptr;
    }
  }

  void fmi2FreeInstance(fmi2Component c)
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    delete cc;
  }

  fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,
                                 size_t nCategories,
                                 const fmi2String categories[])
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->setDebugLogging(true, nCategories, categories);
  }

  fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined,
                                 fmi2Real tolerance, fmi2Real startTime,
                                 fmi2Boolean stopTimeDefined, fmi2Real stopTime)
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->setupExperiment(toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime);
  }

  fmi2Status fmi2EnterInitializationMode(fmi2Component c)
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->enterInitializationMode();
  }

  fmi2Status fmi2ExitInitializationMode(fmi2Component c)
  {

    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->exitInitializationMode();
  }

  fmi2Status fmi2Terminate(fmi2Component c)
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->terminate();
  }

  fmi2Status fmi2Reset(fmi2Component c)
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->reset();
  }

  fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, fmi2Real value[])
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->getReal(vr, nvr, value);
  }

  fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[],
                            size_t nvr, fmi2Integer value[])
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->getInteger(vr, nvr, value);
  }

  fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                            size_t nvr, fmi2Boolean value[])
  {

    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->getBoolean(vr, nvr, value);
  }

  fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[],
                           size_t nvr, fmi2String value[])
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->getString(vr, nvr, value);
  }

  fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, const fmi2Real value[])
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->setReal(vr, nvr, value);
  }

  fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[],
                            size_t nvr, const fmi2Integer value[])
  {
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->setInteger(vr, nvr, value);
  }

  fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                            size_t nvr, const fmi2Boolean value[])
  {

    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->setBoolean(vr, nvr, value);
  }

  fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[],
                           size_t nvr, const fmi2String value[])
  {

    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->setString(vr, nvr, value);
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
    auto cc = reinterpret_cast<SlaveWrapperAdapter *>(c);
    return cc->doStep(currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint);
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
