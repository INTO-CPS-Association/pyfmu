cmake_minimum_required(VERSION 3.16)
project(pythonfmu-wrapper VERSION 0.0.1)

# ==============================================================================
# Build settings
# ==============================================================================

set(BUILD_SHARED_LIBS ON)

# ==============================================================================
# Global internal configuration
# ==============================================================================

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
    foreach(CompilerFlag ${CompilerFlags})
        string(REPLACE "/MD" "/MT" ${CompilerFlag} "${${CompilerFlag}}")
    endforeach()
endif()

# Automatically export all symbols in Windows DLLs.
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)

# ==============================================================================
# Dependencies
# ==============================================================================

find_package(JNI REQUIRED)

set(Python_FIND_ABI "OFF" "ANY" "ANY") # FORCE cmake to link against RELEASE LIBRARIES
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)




set(sources
        src/cppfmu_cs.cpp
        src/fmi_functions.cpp
        src/model_description_provider.cpp
        src/PyObjectWrapper.cpp
        src/SlaveInstance.cpp
        src/thread_worker.cpp
        )

add_library(pythonfmu-wrapper ${sources})
target_compile_features(pythonfmu-wrapper PUBLIC "cxx_std_17")
target_include_directories(pythonfmu-wrapper
        PUBLIC
        "$<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>"
        PRIVATE
        "${JNI_INCLUDE_DIRS}"
        "${CMAKE_CURRENT_SOURCE_DIR}"
        )

target_link_libraries(pythonfmu-wrapper
        PRIVATE
        "${JNI_LIBRARIES}"
        Python3::Python
        )

set_target_properties(pythonfmu-wrapper PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")

if (WIN32)
  set_target_properties(pythonfmu-wrapper
          PROPERTIES
          RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/../pythonfmu-builder/src/main/resources/binaries/win64"
          )
elseif (UNIX)
  set_target_properties(pythonfmu-wrapper
          PROPERTIES
          LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/../pythonfmu-builder/src/main/resources/binaries/linux64"
          )
endif ()
