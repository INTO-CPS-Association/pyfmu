cmake_minimum_required(VERSION 3.10)
project(pyfmu LANGUAGES C CXX)

# Force to use stable Python ABI https://docs.python.org/3/c-api/stable.html
# add_compile_definitions(Py_LIMITED_API)
find_package(Python3 REQUIRED COMPONENTS Interpreter Development)
if (WIN32)
  set(Python3_LIBRARIES ${Python3_LIBRARY_DIRS}/python3.lib)
endif ()


add_library(${PROJECT_NAME}
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        src/PyConfiguration.cpp
        src/Logger.cpp
)
target_include_directories(${PROJECT_NAME} PUBLIC include)
target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_20")
target_link_libraries(${PROJECT_NAME} PUBLIC 
        Python3::Python        
)
target_link_libraries(${PROJECT_NAME} PRIVATE ${CONAN_LIBS})
