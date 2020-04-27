# Loading extension modules

## Showing dynamic symbols
https://unix.stackexchange.com/questions/282616/why-nm-shows-no-symbols-for-lib-i386-linux-gnu-libc-so-6

## Linker scripts
https://stackoverflow.com/questions/22764734/linux-equivalent-of-windows-dll-forwarders-or-macos-reexport-library

## SO-numbers
https://unix.stackexchange.com/questions/282616/why-nm-shows-no-symbols-for-lib-i386-linux-gnu-libc-so-6

## BUg static linking
https://bugs.python.org/issue21536

## GCC Linker options
https://gcc.gnu.org/onlinedocs/gcc/Link-Options.html

## Possible changes in 3.8
https://docs.python.domainunion.de/3.8/whatsnew/3.8.html
On Unix, C extensions are no longer linked to libpython except on Android and Cygwin.
It is now possible for a statically linked Python to load a C extension built using a shared library Python.
 (Contributed by Victor Stinner in bpo-21536.)

# Distributing a Python interpreter
https://gregoryszorc.com/blog/2018/12/18/distributing-standalone-python-applications/

## Compiling CPython on windows
https://cpython-core-tutorial.readthedocs.io/en/latest/getting_help.html

# Compiler options
https://stackoverflow.com/questions/13562708/numpy-import-fails-when-embedding-python-in-c
https://www.unix.com/programming/28753-export-dynamic.html

 


# Limited API

## Seems like there is an issue on Windows with limited API
```
fatal error C1189: #error:  Py_LIMITED_API is incompatible with Py_DEBUG, Py_TRACE_REFS, and Py_REF_DEBUG
```
https://bitbucket.org/cffi/cffi/issues/350/issue-with-py_limited_api-on-windows


## Discusses how boost solves this
https://github.com/pybind/pybind11/issues/1295

# Python extensions
https://github.com/paulross/PythonExtensionPatterns

