project(tests)



add_executable(${PROJECT_NAME}
    src/tests.cpp
)
target_include_directories(${PROJECT_NAME} PUBLIC include)
target_include_directories(${PROJECT_NAME} PRIVATE src)

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")

target_link_libraries(${PROJECT_NAME} PRIVATE pyfmuwrapper)
target_link_libraries(${PROJECT_NAME} PRIVATE mylib)

# Copy test files to output folder
file(COPY resources DESTINATION ${CMAKE_BINARY_DIR})
