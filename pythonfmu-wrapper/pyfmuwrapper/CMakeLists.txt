cmake_minimum_required(VERSION 3.16)
project(pyfmuwrapper)

# include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

set(sources
        src/cppfmu_cs.cpp
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        src/SlaveInstance.cpp
        src/thread_worker.cpp
        )


add_library(pyfmuwrapper ${sources})
target_compile_features(pyfmuwrapper PUBLIC "cxx_std_17")
target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(pyfmuwrapper PUBLIC Python3::Python)



set_target_properties(pyfmuwrapper PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")