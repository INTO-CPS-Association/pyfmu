project(pyfmu LANGUAGES C CXX)
cmake_minimum_required(VERSION 3.10)


add_subdirectory(pythonfmu-wrapper)

add_custom_target(copy_wrapper_to_resources ALL
    COMMAND ${CMAKE_COMMAND} -E echo "Copying binaries into pybuilder resources\n."
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:pythonfmu-wrapper> ${CMAKE_SOURCE_DIR}/pybuilder/resources/wrapper/binaries/linux64/libpyfmu.so
)
add_dependencies(copy_binaries pyfmuwrapper)


