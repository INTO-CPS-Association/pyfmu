#include <iostream>
#include <stdexcept>

#include <fmt/format.h>

#include "pyfmu/Logger.hpp"

using namespace std;
using namespace fmt;

Logger::Logger(fmi2ComponentEnvironment componentEnvironment, fmi2CallbackLogger loggerCallback, string instanceName)
    : instanceName(instanceName), loggerCallback(loggerCallback),
      componentEnvironment(componentEnvironment)
{
  if (loggerCallback == NULL)
    throw invalid_argument("loggerCallback");
}

void Logger::log(fmi2Status status, string category, string message)
{
  string msg = format("{}:{}:{}:{}\n",instanceName,status,category,message);
  cerr << msg;

  this->loggerCallback(this->componentEnvironment, this->instanceName.c_str(),
                       status, category.c_str(), message.c_str());
}
