cmake_minimum_required(VERSION 3.10)
project(pyfmu-wrapper
        VERSION 0.0.1
        LANGUAGES C CXX
)

#set(BUILD_SHARED_LIBS ON)
######################################## WINDOWS COMPATABILITY ########################################
if (MSVC)
  # https://stackoverflow.com/questions/14172856/compile-with-mt-instead-of-md-using-cmake
  set(CompilerFlags
          CMAKE_CXX_FLAGS
          CMAKE_CXX_FLAGS_DEBUG
          CMAKE_CXX_FLAGS_RELEASE
          CMAKE_C_FLAGS
          CMAKE_C_FLAGS_DEBUG
          CMAKE_C_FLAGS_RELEASE
          )
  foreach (CompilerFlag ${CompilerFlags})
    string(REPLACE "/MD" "/MT" ${CompilerFlag} "${${CompilerFlag}}")
  endforeach ()

  # Python defines its own snprintf function in case the system does not provide one.
  # Unfortunately this clashes with std::snprintf. The flag HAVE_SNPRINTF determines this behavior.
  # In GCC this seems to be correctly set, however it does not seem to be the case for MSVC.
  # The symptom of this shows where snprintf is used such as by nlohman@json:
  # https://github.com/nlohmann/json/issues/1408 , https://github.com/boostorg/system/issues/32
  add_compile_definitions(HAVE_SNPRINTF ON)

endif ()

# Automatically export all symbols in Windows DLLs.
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

######################################## EXTERNAL DEPENDENCIES ########################################
# The project relies on several external libraries managed either by:
# 1. Conan package manager (https://conan.io/)
#   * catch2, fmt, spdlog, nlohman_json
# 2. Grafted into the source tree:
#   * uriparser
#
# Any packages that are available should use conan for greatest ease of installation.
#
# 1. Conan packages:
#
# Conan provides a way to launch conan directly from cmake: (https://docs.conan.io/en/latest/howtos/cmake_launch.html)
if(NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake")
   message(STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan")
   file(DOWNLOAD "https://github.com/conan-io/cmake-conan/raw/v0.15/conan.cmake"
                 "${CMAKE_BINARY_DIR}/conan.cmake")
endif()

include(${CMAKE_BINARY_DIR}/conan.cmake)
conan_cmake_run(REQUIRES 
                
                catch2/2.5.0@bincrafters/stable
                fmt/6.1.1
                spdlog/[>=1.4.1]
                nlohmann_json/3.7.3
                
                BASIC_SETUP 
                BUILD missing
                # fix to keep conan from overwriting output dirs on UNIX, seems to be a bug
                # https://github.com/conan-io/conan/issues/1982
                NO_OUTPUT_DIRS 
                )

# 2. source tree packages
add_subdirectory(uriparser)
set(EXTERNAL_LIBS uriparser)

######################################## LOCATE PYTHON ########################################

find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
if (WIN32)
  set(Python3_LIBRARIES ${Python3_LIBRARY_DIRS}/python3.lib)
endif ()

set(Python3_USE_STATIC_LIBS TRUE)

######################################## WRAPPER ########################################


add_library(pyfmu SHARED
        wrapper/src/fmi2Functions.cpp
        wrapper/src/fmi2PySlave.cpp
        wrapper/src/fmi2PySlaveConfiguration.cpp
        wrapper/src/utils.cpp
)

target_include_directories(pyfmu
        PUBLIC
        wrapper/include
        ${Python3_INCLUDE_DIRS}
        )

target_compile_features(pyfmu PUBLIC "cxx_std_20")


target_compile_definitions(pyfmu 
        PRIVATE 
        # use stable Python ABI to maximize portability between python versions
        # https://docs.python.org/3/c-api/stable.html
        Py_LIMITED_API

        # The CODECVT header is being deprecated:
        # The wrapper uses this to convert pythons representation of string which are "widestrings" to std::strings.
        #
        # However, as there is no replacement the standard as of the time of writing, it will be "annexed" until a replacement is found.
        # http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2017/p0618r0.html
        _SILENCE_CXX17_CODECVT_HEADER_DEPRECATION_WARNING
)

target_link_libraries(pyfmu
        PUBLIC 
        ${Python3_LIBRARIES}
        PRIVATE
        ${CONAN_LIBS}
        ${EXTERNAL_LIBS}
        )

######################################## WRAPPER-TESTS ########################################

add_executable(wrapper-tests
        wrapper/tests/src/tests.cpp
        wrapper/tests/src/example_finder.cpp
        wrapper/tests/src/tmpdir.cpp
)

target_include_directories(wrapper-tests 
        PRIVATE 
        wrapper/tests/include
)
target_compile_features(wrapper-tests
        PUBLIC
        "cxx_std_20"
)
target_link_libraries(wrapper-tests 
        PRIVATE 
        pyfmu
        ${CONAN_LIBS}
)

# multi-configuration generators such as MSVC puts different builds in seperate folders
# we dumpy them in the root of the build to be able to copy them more easily.
if(MSVC)
    set_target_properties(pyfmu PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/$<$<CONFIG:Debug>:>)
    set_target_properties(pyfmu PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/$<$<CONFIG:Release>:>)

elseif(UNIX)
    
    set_target_properties(pyfmu PROPERTIES 
        PREFIX ""
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}
        )

endif()

