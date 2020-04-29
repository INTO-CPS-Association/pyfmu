/**
 * @file slaveFactory.hpp
 * @author Christian Møldrup Legaard (cml@eng.au.dk)
 * @brief Defines factory pattern for creating a wrapper based on the contents
 * of the FMUs configuration.
 *
 * @version 0.1
 * @date 2020-04-29
 *
 * @copyright Copyright (c) 2020
 *
 */

#pragma once
#include <filesystem>

#include "pyfmu/fmi2/configuration.hpp"
#include "pyfmu/fmi2/slaveAdapter.hpp"

namespace pyfmu::fmi2 {

/**
 * @brief Encapsulates how to create a slave for a particular configration.
 * In addition, the factory ensures that global resources such as the Python
 * interpreter are ready for use by the produced slave instances.
 *
 */
class SlaveFactory {

public:
  /**
   * @brief Instantiate a new slave object based on the provided configuration.
   * Note that it is the callers responsibility to de-allocate the slave.
   *
   * @param config
   * @return Slave*
   */
  SlaveAdapter *
  createSlaveForConfiguration(pyconfiguration::PyConfiguration config,
                              Logger *logger);
};
} // namespace pyfmu::fmi2
