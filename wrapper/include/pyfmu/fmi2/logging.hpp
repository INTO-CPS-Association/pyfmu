#pragma once

#include <string>
#include <ostream>
#include <optional>
#include <regex>

#include <fmt/format.h>
#include <spdlog/spdlog.h>

#include "spec/fmi2/fmi2Functions.h"

namespace pyfmu::fmi2
{

/**
 * @brief Wrapper class for FMI2 logging callback
 *
 */
class Logger
{
public:
  /**
   * @brief Constructs a wrapper around the FMI2 standards callback function
   * The purpose of this wrapper is to facilitate
   *
   * @param loggerCallback callback supplied when fmu was instantiated.
   * @param instanceName name of the fmu instance to which the logger is associated
   */
  explicit Logger(fmi2ComponentEnvironment componentEnvironment,
                  fmi2CallbackLogger loggerCallback,
                  std::string instanceName) : instanceName(instanceName),
                                              loggerCallback(loggerCallback),
                                              componentEnvironment(componentEnvironment)
  {
    if (loggerCallback == nullptr)
    {
      throw std::invalid_argument("log callback function is null");
    }
  }

  /**
   * @brief Logs a message to the tool running the FMU.
   * 
   * @param status status of the fmu at the time the message was logged
   * @param category the category to which the 
   * @param format format string
   * @param args values inserted into the string
   * 
   * @example
   * mylog.log(fmi2Error,"wrapper","something failed due to : {}",err_msg)
   */
  template <typename... Args>
  void log(
      fmi2Status status,
      const std::string &category,
      const std::string &format,
      const Args &... args)
  {

    std::string msg = fmt::format(format, args...);

    loggerCallback(componentEnvironment, instanceName.c_str(), status, category.c_str(), msg.c_str());
  }

  template <typename... Args>
  void ok(const std::string &category, const std::string &message, const Args &... args)
  {
    log(fmi2Status::fmi2OK, category, message, args...);
  }

  template <typename... Args>
  void warning(const std::string &category, const std::string &message, const Args &... args)
  {
    log(fmi2Status::fmi2Warning, category, message, args...);
  }

  template <typename... Args>
  void discard(const std::string &category, const std::string &message, const Args &... args)
  {
    log(fmi2Status::fmi2Discard, category, message, args...);
  }

  template <typename... Args>
  void error(const std::string &category, const std::string &message, const Args &... args)
  {
    log(fmi2Status::fmi2Error, category, message, args...);
  }

  template <typename... Args>
  void fatal(const std::string &category, const std::string &message, const Args &... args)
  {
    log(fmi2Status::fmi2Fatal, category, message, args...);
  }

  template <typename... Args>
  void pending(const std::string &category, const std::string &message, const Args &... args)
  {
    log(fmi2Status::fmi2Pending, category, message, args...);
  }

private:
  std::string instanceName;
  fmi2CallbackLogger loggerCallback;
  fmi2ComponentEnvironment componentEnvironment;
};

} // namespace pyfmu::fmi2