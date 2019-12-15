cmake_minimum_required(VERSION 3.10)
project(pyfmu LANGUAGES C CXX)

set(BUILD_SHARED_LIBS ON)


set(Python_FIND_ABI "OFF" "ANY" "ANY") # FORCE cmake to link against RELEASE LIBRARIES
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)

add_library(${PROJECT_NAME}
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        src/PyConfiguration.cpp
        src/Logger.cpp
)
target_include_directories(${PROJECT_NAME} PUBLIC include)
target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")
target_link_libraries(${PROJECT_NAME} PUBLIC 
        Python3::Python        
)
target_link_libraries(${PROJECT_NAME} PRIVATE ${CONAN_LIBS})
