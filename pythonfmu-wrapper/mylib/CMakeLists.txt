project(mylib)


add_library(${PROJECT_NAME}
    src/foo.cpp
)

target_include_directories(${PROJECT_NAME} PUBLIC include)
target_include_directories(${PROJECT_NAME} PRIVATE src)

