project(foo)

add_library(${PROJECT_NAME} SHARED foo.cpp)

target_include_directories(${PROJECT_NAME} INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})