project(pyfmu LANGUAGES C CXX)
cmake_minimum_required(VERSION 3.10)

set(BUILD_SHARED_LIBS ON)

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
endif ()

# Automatically export all symbols in Windows DLLs.
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

# The project relies on several external libraries.
# These are managed by the Conan package manager (https://conan.io/)
# Conan provides a way to launch conan directly from cmake: (https://docs.conan.io/en/latest/howtos/cmake_launch.html)
if(NOT EXISTS "${CMAKE_BINARY_DIR}/conan.cmake")
   message(STATUS "Downloading conan.cmake from https://github.com/conan-io/cmake-conan")
   file(DOWNLOAD "https://github.com/conan-io/cmake-conan/raw/v0.15/conan.cmake"
                 "${CMAKE_BINARY_DIR}/conan.cmake")
endif()

include(${CMAKE_BINARY_DIR}/conan.cmake)

conan_cmake_run(REQUIRES 

                Poco/1.9.4@pocoproject/stable
                catch2/2.5.0@bincrafters/stable
                fmt/6.1.1
                spdlog/[>=1.4.1]
                nlohmann_json/3.7.3
                
                BASIC_SETUP 
                BUILD missing)


# end of external packages

add_subdirectory(pythonfmu-wrapper)
add_subdirectory(tests/wrapper)