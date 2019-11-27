project(pyfmuwrapper)

# set(wrapper_source
#         src/cppfmu_cs.cpp
#         src/fmi_functions.cpp
#         src/PyObjectWrapper.cpp
#         src/SlaveInstance.cpp
#         src/thread_worker.cpp
#         )

set(wrapper_source src/foo.cpp)

add_library(${PROJECT_NAME} SHARED ${wrapper_source})
target_compile_features(${PROJECT_NAME} PUBLIC "cxx_std_17")
target_include_directories(${PROJECT_NAME} PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
target_link_libraries(${PROJECT_NAME} PUBLIC Python3::Python)