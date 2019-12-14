project(tests)



add_executable(${PROJECT_NAME}
    src/tests.cpp
)

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")

target_link_libraries(${PROJECT_NAME} PRIVATE 
    pyfmu 
    ${CONAN_LIBS}
)



# Copy test resource files to output folder
file(COPY examples DESTINATION ${CMAKE_BINARY_DIR}/${PROJECT_NAME})