/* Copyright 2016-2019, SINTEF Ocean.
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#include "fmi/fmi2Functions.h"
#include "pythonfmu/PyInitializer.hpp"
#include "pythonfmu/PyObjectWrapper.hpp"

#include <exception>
#include <limits>

// FMI functions
extern "C" {

// =============================================================================
// FMI 2.0 functions
// =============================================================================

const char *fmi2GetTypesPlatform() { return fmi2TypesPlatform; }

const char *fmi2GetVersion() { return "2.0"; }

using namespace pythonfmu;
using namespace std;

PyObjectWrapper *component = nullptr;
PyInitializer *pyInitializer = nullptr;


bool loggingOn_ = false;
fmi2CallbackLogger logger = nullptr;

void fmi2Log(fmi2ComponentEnvironment env, fmi2String instanceName, fmi2Status status, fmi2String category, fmi2String message, ...) {

  if(logger == nullptr)
  {
    return;
  }

  if(!loggingOn_)
  {
    return;
  }

  // TODO find way to support pass variable amount of arguments
  logger(env,instanceName,status,category,message, message, nullptr);


}

fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType,
                              fmi2String fmuGUID,
                              fmi2String fmuResourceLocation,
                              const fmi2CallbackFunctions *functions,
                              fmi2Boolean visible, fmi2Boolean loggingOn) {

  if (component != nullptr) {
    throw runtime_error(
        "Failed FMU may only be instantiated once per process!");
  }

  try {
    pyInitializer = new PyInitializer();
    component = new PyObjectWrapper(fmuResourceLocation);
  }
  catch (exception &e){
    return nullptr;
  }

  logger = functions->logger;
  loggingOn_ = loggingOn;

  return component;
}

void fmi2FreeInstance(fmi2Component c) 
{
  if(component != nullptr)
  {
    delete component;
  }

  if(pyInitializer != nullptr)
  {
    delete pyInitializer;
  }
}

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,
                               size_t nCategories,
                               const fmi2String categories[]) {

  return fmi2OK;
}

fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined,
                               fmi2Real tolerance, fmi2Real startTime,
                               fmi2Boolean stopTimeDefined, fmi2Real stopTime) {
  
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->setupExperiment(startTime);
  }
  catch (exception &e)
  {
    return fmi2Error;
  }
  
  return fmi2OK;
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c) { return fmi2OK; }

fmi2Status fmi2ExitInitializationMode(fmi2Component c) { return fmi2OK; }

fmi2Status fmi2Terminate(fmi2Component c) { return fmi2OK; }

fmi2Status fmi2Reset(fmi2Component c) { return fmi2OK; }

fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, fmi2Real value[]) {
  
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);
  
  try{
    cc->getReal(vr,nvr,value);
  }
  catch (exception &e){
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Integer value[]) {
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->getInteger(vr,nvr,value);
  }
  catch (exception &e)
  {
    return fmi2Error;
  }
  
  return fmi2OK;
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, fmi2Boolean value[]) {
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->getBoolean(vr,nvr,value);
  }
  catch (exception &e)
  {
    return fmi2Error;
  }
  
  return fmi2OK;
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, fmi2String value[]) {
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->getString(vr,nvr,value);
  }
  catch (exception &e)
  {
    return fmi2Error;
  }
  
  return fmi2OK;
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[],
                       size_t nvr, const fmi2Real value[]) {

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->setReal(vr, nvr, value);
  } catch (exception &e) {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Integer value[]) {
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->setInteger(vr,nvr,value);
  }
  catch (exception &e)
  {
    return fmi2Error;
  }
  
  return fmi2OK;
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[],
                          size_t nvr, const fmi2Boolean value[]) {
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->setBoolean(vr,nvr,value);
  }
  catch (exception &e)
  {
    return fmi2Error;
  }
  
  return fmi2OK;
}

fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[],
                         size_t nvr, const fmi2String value[]) {
  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->setString(vr,nvr,value);
  }
  catch (exception &e)
  {
    return fmi2Error;
  }
  
  return fmi2OK;
}

fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate *) {
  return fmi2Error;
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate) { return fmi2Error; }

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate *) {
  return fmi2Error;
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate, size_t *) {
  return fmi2Error;
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate, fmi2Byte[],
                                 size_t) {
  return fmi2Error;
}

fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte[], size_t,
                                   fmi2FMUstate *) {
  return fmi2Error;
}

fmi2Status fmi2GetDirectionalDerivative(fmi2Component c,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2Real[], fmi2Real[]) {
  return fmi2Error;
}

fmi2Status fmi2SetRealInputDerivatives(fmi2Component c,
                                       const fmi2ValueReference[], size_t,
                                       const fmi2Integer[], const fmi2Real[]) {
  return fmi2Error;
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c,
                                        const fmi2ValueReference[], size_t,
                                        const fmi2Integer[], fmi2Real[]) {
  return fmi2Error;
}

fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint,
                      fmi2Real communicationStepSize, fmi2Boolean) {

  auto cc = reinterpret_cast<PyObjectWrapper *>(c);

  try {
    cc->doStep(currentCommunicationPoint, communicationStepSize);
  } catch (exception &e) {
    return fmi2Error;
  }

  return fmi2OK;
}

fmi2Status fmi2CancelStep(fmi2Component c) 
{ return fmi2Error; }

fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind, fmi2Status *) {
  return fmi2Error;
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s,
                             fmi2Real *value) {
  return fmi2Error;
}
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind,
                                fmi2Integer *) {
  return fmi2Error;
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind,
                                fmi2Boolean *) {
  return fmi2Error;
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind,
                               fmi2String *) {
  return fmi2Error;
}
