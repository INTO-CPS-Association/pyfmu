cmake_minimum_required(VERSION 3.16)
project(pyfmuwrapper VERSION 0.0.1 LANGUAGES CXX)



# Windows Debug stuff
set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
if(MSVC)
    set(CMAKE_DEBUG_POSTFIX "d")
endif()

# Ensure only standard C and CXX is used
set(CMAKE_C_EXTENSIONS OFF)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_POSITION_INDEPENDENT_CODE ON)


set(Python_FIND_ABI "OFF" "ANY" "ANY") # FORCE cmake to link against RELEASE LIBRARIES
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)



set(wrapper_source
        src/cppfmu_cs.cpp
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        src/SlaveInstance.cpp
        src/thread_worker.cpp
        )

add_library(pyfmuwrapper STATIC ${wrapper_source})
target_compile_features(pyfmuwrapper PUBLIC "cxx_std_17")
target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(pyfmuwrapper PUBLIC Python3::Python)


# Tests
set(test_source src/tests.cpp)
add_executable(tests ${test_source})
target_compile_features(tests PUBLIC "cxx_std_17")
target_link_libraries(tests pyfmuwrapper)

set(test_binary_dir "${CMAKE_BINARY_DIR}/bin/tests")
set_target_properties(tests PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${test_binary_dir}")

# copy test samples to output dir. 
# Note that source dir is defined with respect to current project and output with respect to the build dir

file(COPY resources DESTINATION ${test_binary_dir})


