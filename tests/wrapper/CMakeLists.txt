project(tests)



add_executable(${PROJECT_NAME}
    src/tests.cpp
    src/example_finder.cpp
    src/tmpdir.cpp
)
target_include_directories(${PROJECT_NAME} PRIVATE include)

target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_20")

target_link_libraries(${PROJECT_NAME} PRIVATE 
    libpyfmu
    ${CONAN_LIBS}
)