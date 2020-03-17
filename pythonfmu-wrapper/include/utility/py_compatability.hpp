#pragma once
/**
 * @file py_compatability.hpp
 * @author Christian Møldrup Legaard (cml@eng.au.dk)
 * @brief Provides functions missing in the stable Python API
 * @version 0.0.1
 * @date 2020-03-17
 * 
 * @copyright Copyright (c) 2020
 * 
 */

#include <Python.h>

#include "utility/utils.hpp"

namespace PyCompat
{
    int PyRun_SimpleString(const char* command);

    const char* PyUnicode_AsUTF8(PyObject* object);
}