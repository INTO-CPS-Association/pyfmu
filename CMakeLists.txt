project(pyfmu LANGUAGES C CXX)
cmake_minimum_required(VERSION 3.10)




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
                nlohmann_json/3.7.3
                
                BASIC_SETUP 
                BUILD missing)


# end of external packages

add_subdirectory(pythonfmu-wrapper)
add_subdirectory(tests/wrapper)

# update wrapper in pybuilder resource folder on build
add_custom_target(copy_wrapper_to_resources ALL
    COMMAND ${CMAKE_COMMAND} -E echo "Copying binaries into pybuilder resources\n"
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:pyfmu> ${CMAKE_SOURCE_DIR}/pybuilder/resources/wrapper/binaries/linux64/$<TARGET_FILE_NAME:pyfmu>
)
add_dependencies(copy_wrapper_to_resources pyfmu)