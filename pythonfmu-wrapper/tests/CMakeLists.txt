cmake_minimum_required(VERSION 3.16)
project(tests)


include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)



set(sources
        src/main.cpp
        )


add_executable(tests ${sources})

set_target_properties(tests PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")