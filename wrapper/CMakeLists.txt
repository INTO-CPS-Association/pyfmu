cmake_minimum_required(VERSION 3.10)
project(pyfmu-wrapper LANGUAGES C CXX)

# Force to use stable Python ABI https://docs.python.org/3/c-api/stable.html
#add_compile_definitions(Py_LIMITED_API)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
if (WIN32)
  set(Python3_LIBRARIES ${Python3_LIBRARY_DIRS}/python3.lib)
endif ()

set(Python3_USE_STATIC_LIBS TRUE)

add_library(pyfmu
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        src/PyConfiguration.cpp
        src/Logger.cpp
        src/utility/py_compatability.cpp
        src/utility/utils.cpp
)
target_include_directories(pyfmu
        PUBLIC
        include
        ${Python3_INCLUDE_DIRS}
        )

target_compile_features(pyfmu PUBLIC "cxx_std_17")

target_compile_definitions(pyfmu PRIVATE Py_LIMITED_API
)

target_link_libraries(pyfmu
        PUBLIC 
        ${Python3_LIBRARIES}
        PRIVATE
        ${CONAN_LIBS}
        )