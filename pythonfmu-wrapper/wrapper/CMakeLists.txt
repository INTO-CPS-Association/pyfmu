project(pyfmuwrapper)



add_library(${PROJECT_NAME}
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        include/pythonfmu/PyInitializer.hpp
)

target_include_directories(${PROJECT_NAME} PUBLIC include)
target_include_directories(${PROJECT_NAME} PRIVATE src)

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")

target_link_libraries(${PROJECT_NAME} PUBLIC Python3::Python)

