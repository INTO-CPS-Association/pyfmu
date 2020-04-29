#pragma once

namespace pyfmu::interpreter {

/**
 * @brief Handles the initialization and teardown of the Python interpreter.
 *
 * @details The fact that the executeable such as FMPy, may also be using
 * interpeter necessitates that the manager distinguishes the two cases. To deal
 * with this the manager can run in two modes:
 *
 * 1. shared: if the interpreter is already running reuse it, otherwise start
 * it. The interpeter MAY be initialized before this.
 *
 * 2. exclusive: if the interpreter is not running, instantiate it.
 * The interpeter MUST NOT be initialized before to this.
 *
 * In case the interpeter is still in use after PyFMU has been unloaded it
 * is possible to define whether or not the interpreter should be finalized or
 * not. The following options are available.
 *
 * 1. never: do not finalize.
 * 2. always: finalize irregardless of running in shared or exclusive.
 * 3. ifExclusive: finalize if and only if started in exclusive mode.
 *
 */
class CPythonManager {

  enum Mode { shared, standalone };

  enum Finalize {
    never,
    always,
    ifExclusive,
  };

  /**
   * @brief Initialize the CPython interpreter using the specified mode.
   *
   * @param mode defines if the interpreter is shared with the calling module.
   * @param finalizeStrategy defines whether or not the interpreter should be
   * finalized.
   */
  CPythonManager(Mode mode, Finalize finalizeStrategy);

  ~CPythonManager();

private:
  Mode mode;
  Finalize finalize;
};
} // namespace pyfmu::interpreter
