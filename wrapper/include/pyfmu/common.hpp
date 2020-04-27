#pragma once

#if defined(_MSC_VER)
#if (PY_MAJOR_VERSION == 3 && PY_MINOR_VERSION < 4)
#define HAVE_ROUND 1
#endif
#if defined(_DEBUG) && !defined(Py_DEBUG)
#define PYBIND11_DEBUG_MARKER
#undef _DEBUG
#endif
#endif

#include <Python.h>