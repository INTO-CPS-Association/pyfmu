project(pyfmuwrapper LANGUAGES C CXX)




add_library(${PROJECT_NAME}
        src/fmi_functions.cpp
        src/PyObjectWrapper.cpp
        src/PyConfiguration.cpp
        include/pythonfmu/PyInitializer.hpp
)



target_include_directories(${PROJECT_NAME} PUBLIC include)

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")

target_link_libraries(${PROJECT_NAME} PUBLIC 
        Python3::Python
        nlohmann_json::nlohmann_json        
)


