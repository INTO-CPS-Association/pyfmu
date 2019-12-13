project(tests)



add_executable(${PROJECT_NAME}
    src/tests.cpp
)
target_include_directories(${PROJECT_NAME} PUBLIC include)
target_include_directories(${PROJECT_NAME} PRIVATE src)

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")

target_link_libraries(${PROJECT_NAME} PRIVATE pyfmu)



# Copy test resource files to output folder
file(COPY examples DESTINATION ${CMAKE_BINARY_DIR}/${PROJECT_NAME})