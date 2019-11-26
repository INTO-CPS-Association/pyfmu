cmake_minimum_required(VERSION 3.16)
project(tests)


include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

set(sources
        src/main.cpp
        )


add_executable(tests ${sources})
target_link_libraries(${PROJECT_NAME} pyfmuwrapper)
target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")

set(outputDir "${CMAKE_BINARY_DIR}/bin/${PROJECT_NAME}")
set_target_properties(tests PROPERTIES RUNTIME_OUTPUT_DIRECTORY "${outputDir}")

target_link_libraries(${PROJECT_NAME} foo)






# copy test samples to output dir. 
# Note that source dir is defined with respect to current project and output with respect to the build dir
file(COPY resources DESTINATION ${outputDir})