project(pyfmu LANGUAGES C CXX)




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

add_custom_command(TARGET pyfmu POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:pyfmu> ${CMAKE_SOURCE_DIR}/examples/multiplier/binaries/linux64/libpyfmu.so
)