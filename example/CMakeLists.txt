cmake_minimum_required(VERSION 3.13)
project(ExampleProject)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/../cmake")

include(TargetEmbedCppData)

add_executable(ExampleApp
    test.cpp
)

target_embed_cpp_data(ExampleApp
    FILES
        test.h.in
)
