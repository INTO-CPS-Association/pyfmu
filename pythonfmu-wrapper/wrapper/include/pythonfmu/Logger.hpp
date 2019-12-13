
#include "fmi/fmi2Functions.h"
#include <string>

#ifndef LOGGER_HPP
#define LOGGER_HPP

/**
 * @brief Wrapper class for FMI logging callback
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
  explicit Logger(fmi2CallbackLogger loggerCallback,
                  std::string instanceName);

  void log(fmi2ComponentEnvironment componentEnvironment, fmi2Status status, std::string category,
           std::string message);

private:
 std::string instanceName;
 fmi2CallbackLogger loggerCallback;
};

#endif // LOGGER_HPP
