#include "pythonfmu/Logger.hpp"
#include <iostream>
#include <stdexcept>

using namespace std;

Logger::Logger(fmi2CallbackLogger loggerCallback, string instanceName)
    : instanceName(instanceName), loggerCallback(loggerCallback) {
  if (loggerCallback == NULL)
    throw invalid_argument("loggerCallback");
}

void Logger::log(fmi2ComponentEnvironment componentEnvironment,
                 fmi2Status status, std::string category, std::string message) {
  cerr << category << ": "
       << "instance: " << this->instanceName << " status: " << status
       << " message: " << message << std::endl;

  this->loggerCallback(componentEnvironment, this->instanceName.c_str(), status,
                       category.c_str(), message.c_str());
}