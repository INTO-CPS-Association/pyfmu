#include <pybind11/embed.h>

#include "pyfmu/fmi2/configuration.hpp"
#include "pyfmu/fmi2/embeddedSlave.hpp"
#include "pyfmu/fmi2/slaveAdapter.hpp"
#include "pyfmu/fmi2/slaveFactory.hpp"

namespace pyfmu::fmi2 {

namespace py = pybind11;

SlaveAdapter *SlaveFactory::createSlaveForConfiguration(
    pyconfiguration::PyConfiguration config, Logger *logger) {

  if (!Py_IsInitialized()) {
    py::initialize_interpreter();
  }

  py::module("sys").attr("path").cast<py::list>().append(config.resources);

  auto slave = new EmbeddedSlave(config.main_script, config.main_class, logger);
  auto adapter = new SlaveAdapter(slave);

  return adapter;
}
} // namespace pyfmu::fmi2
