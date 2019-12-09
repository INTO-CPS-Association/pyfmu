cmake_minimum_required(VERSION 3.16)
project(pyfmuwrapper VERSION 0.0.1 LANGUAGES CXX)

set(BUILD_SHARED_LIBS ON)


# Typically you don't care so much for a third party library's tests to be
# run from your own project's code.
set(JSON_BuildTests OFF CACHE INTERNAL "")
add_subdirectory(external/json)


# Ensure only standard C and CXX is used
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

set(Python_FIND_ABI "OFF" "ANY" "ANY") # FORCE cmake to link against RELEASE LIBRARIES
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)


add_subdirectory(wrapper)
add_subdirectory(tests)