project(pyfmu LANGUAGES C CXX)
cmake_minimum_required(VERSION 3.10)


# setup conan package manager
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_subdirectory(pythonfmu-wrapper)
add_subdirectory(tests/wrapper)

# update wrapper in pybuilder resource folder on build
add_custom_target(copy_wrapper_to_resources ALL
    COMMAND ${CMAKE_COMMAND} -E echo "Copying binaries into pybuilder resources\n"
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:pyfmu> ${CMAKE_SOURCE_DIR}/pybuilder/resources/wrapper/binaries/linux64/$<TARGET_FILE_NAME:pyfmu>
)
add_dependencies(copy_wrapper_to_resources pyfmu)