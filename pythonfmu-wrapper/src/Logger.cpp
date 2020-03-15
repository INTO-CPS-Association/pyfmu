#include <iostream>
#include <stdexcept>

#include <fmt/format.h>

#include "pythonfmu/Logger.hpp"

using namespace std;
using namespace fmt;

Logger::Logger(fmi2ComponentEnvironment componentEnvironment, fmi2CallbackLogger loggerCallback, std::string instanceName)
    : instanceName(instanceName), loggerCallback(loggerCallback),
      componentEnvironment(componentEnvironment)
{
  if (loggerCallback == NULL)
    throw invalid_argument("loggerCallback");
}

void Logger::log(fmi2Status status, std::string category, std::string message)
{
  std::string msg = format("{}:{}:{}:{}\n",instanceName,status,category,message);
  cerr << msg;

  this->loggerCallback(this->componentEnvironment, this->instanceName.c_str(),
                       status, category.c_str(), message.c_str());
}

void Logger::ok(std::string message)
{
  log(fmi2Status::fmi2OK, "wrapper", message);
}
void Logger::warning(std::string message)
{
  log(fmi2Status::fmi2Warning, "wrapper", message);
}
void Logger::discard(std::string message)
{
  log(fmi2Status::fmi2Discard, "wrapper", message);
}
void Logger::error(std::string message)
{
  log(fmi2Status::fmi2Error, "wrapper", message);
}
void Logger::fatal(std::string message)
{
  log(fmi2Status::fmi2Fatal, "wrapper", message);
}
