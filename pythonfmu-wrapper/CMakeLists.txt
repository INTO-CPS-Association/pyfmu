cmake_minimum_required(VERSION 3.10)
project(libpyfmu LANGUAGES C CXX)


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

message(STATUS ${Python3_LIBRARIES})
message(STATUS !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!)

target_link_libraries(${PROJECT_NAME} 
        PUBLIC 
        ${Python3_LIBRARIES}
        PRIVATE
        ${CONAN_LIBS}
        )




# we are trying to link to the static Python library py3x.lib
#set_property(TARGET ${PROJECT_NAME} PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
#set_property(TARGET ${PROJECT_NAME} PROPERTY MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Release>:Release>")
