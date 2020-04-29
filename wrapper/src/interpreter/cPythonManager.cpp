#include "pyfmu/interpreter/cPythonManager.hpp"
#include "pybind11/embed.h"

namespace pyfmu::interpreter {

CPythonManager::CPythonManager(bool shouldFinalize)
    : shouldFinalize(shouldFinalize) {

  if (Py_IsInitialized()) {
    return;
  } else {
    pybind11::initialize_interpreter();
  }
}

CPythonManager::~CPythonManager() {}
} // namespace pyfmu::interpreter