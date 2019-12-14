
#include "fmi/fmi2Functions.h"
#include <string>

#ifndef LOGGER_HPP
#define LOGGER_HPP

/**
 * @brief Wrapper class for FMI2 logging callback
 *
 */
class Logger {
public:
  /**
   * @brief Constructs a wrapper around the FMI2 standards callback function
   * The purpose of this wrapper is to facilitate
   *
   * @param loggerCallback callback supplied when fmu was instantiated.
   * @param instanceName name of the fmu instance to which the logger is associated
   */
  explicit Logger(fmi2ComponentEnvironment componentEnvironment,fmi2CallbackLogger loggerCallback,std::string instanceName);

  /**
   * @brief Logs message from FMU instance in a specific category
   * 
   * @param status status of the fmu at the time of logging
   * @param category the category the message is published under
   * @param message the message logged that is logged
   */
  void log(fmi2Status status, std::string category,
           std::string message);

private:
 std::string instanceName;
 fmi2CallbackLogger loggerCallback;
 fmi2ComponentEnvironment componentEnvironment;
};

#endif // LOGGER_HPP
