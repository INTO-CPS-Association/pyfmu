
#include "fmi/fmi2Functions.h"
#include <string>

#ifndef LOGGER_HPP
#define LOGGER_HPP

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
  explicit Logger(fmi2ComponentEnvironment componentEnvironment, fmi2CallbackLogger loggerCallback, std::string instanceName);

  /**
   * @brief Logs message from FMU instance in a specific category
   * 
   * @param status status of the fmu at the time of logging
   * @param category the category the message is published under
   * @param message the message logged that is logged
   */
  void log(fmi2Status status, std::string category,
           std::string message);

  void log_(
      fmi2Status status,
      const std::string& category,
      const std::string& format,
      fmt::format_args args)
  {
    
    std::string msg = fmt::vformat(format, args);
    
    size_t n_m = msg.length();
    auto msg_cstr = new char[n_m+1];
    msg.copy(msg_cstr, n_m);
    msg_cstr[n_m] = '\0';

    size_t n_c = category.length();
    auto cat_cstr = new char[n_c+1];
    category.copy(cat_cstr, n_c);
    cat_cstr[n_c] = '\0';

    size_t n_n = instanceName.length();
    char *n_cstr = new char[n_n+1];
    instanceName.copy(n_cstr, n_n);
    n_cstr[n_n] = '\0';

    loggerCallback(componentEnvironment, n_cstr, status, cat_cstr, msg_cstr);
  }

  template <typename... Args>
  void ok(const std::string& category, const std::string& message, const Args &... args)
  {
    log_(fmi2Status::fmi2OK, category, message, fmt::make_format_args(args...));
  }

  template <typename... Args>
  void warning(const std::string& category, const std::string& message, const Args &... args)
  {
    log_(fmi2Status::fmi2Warning, category, message, fmt::make_format_args(args...));
  }

  template <typename... Args>
  void discard(const std::string& category, const std::string& message, const Args &... args)
  {
    log_(fmi2Status::fmi2Discard, category, message, fmt::make_format_args(args...));
  }

  template <typename... Args>
  void error(const std::string& category, const std::string& message, const Args &... args)
  {
    log_(fmi2Status::fmi2Error, category, message, fmt::make_format_args(args...));
  }

  template <typename... Args>
  void fatal(const std::string& category, const std::string& message, const Args &... args)
  {
    log_(fmi2Status::fmi2Fatal, category, message, fmt::make_format_args(args...));
  }

  template <typename... Args>
  void pending(const std::string& category, const std::string& message, const Args &... args)
  {
    log_(fmi2Status::fmi2Pending, category, message, fmt::make_format_args(args...));
  }

private:
  std::string instanceName;
  fmi2CallbackLogger loggerCallback;
  fmi2ComponentEnvironment componentEnvironment;
};

#endif // LOGGER_HPP
