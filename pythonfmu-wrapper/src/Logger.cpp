#include "pythonfmu/Logger.hpp"
#include <iostream>
#include <stdexcept>
#include "fmt/format.h"

using namespace std;
using namespace fmt;

Logger::Logger(fmi2ComponentEnvironment componentEnvironment,fmi2CallbackLogger loggerCallback,std::string instanceName)
    : instanceName(instanceName), loggerCallback(loggerCallback),
      componentEnvironment(componentEnvironment) {
  if (loggerCallback == NULL)
    throw invalid_argument("loggerCallback");
}

void Logger::log(fmi2Status status, std::string category, std::string message) {
  cerr << category << ": " << "instance: " << this->instanceName << " status: " << status << " message: " << message << std::endl;

  this->loggerCallback(this->componentEnvironment, this->instanceName.c_str(),
                       status, category.c_str(), message.c_str());
}