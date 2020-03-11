cmake_minimum_required(VERSION 3.10)
project(pyfmu LANGUAGES C CXX)


# Force to use stable Python ABI https://docs.python.org/3/c-api/stable.html
#add_compile_definitions(Py_LIMITED_API)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
if (WIN32)
  set(Python3_LIBRARIES ${Python3_LIBRARY_DIRS}/python37.lib)
endif ()

set(Python3_USE_STATIC_LIBS TRUE)

add_library(${PROJECT_NAME}
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        src/PyConfiguration.cpp
        src/Logger.cpp
)
target_include_directories(${PROJECT_NAME} 
        PUBLIC
        include
        ${Python3_INCLUDE_DIRS}
        )

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_20")

target_link_libraries(${PROJECT_NAME} 
        PUBLIC 
        ${Python3_LIBRARIES}
        PRIVATE
        ${CONAN_LIBS}
        )

