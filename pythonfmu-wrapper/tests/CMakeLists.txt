project(tests)

set(test_source src/tests.cpp)


add_executable(${PROJECT_NAME} ${test_source})
target_link_libraries(${PROJECT_NAME} pyfmuwrapper)
target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")

target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

file(COPY resources DESTINATION ${CMAKE_BINARY_DIR})
