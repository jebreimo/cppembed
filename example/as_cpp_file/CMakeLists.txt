list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/../../cmake")

include(TargetEmbedCppData)

add_executable(CppFileExampleApp
    test.cpp
)

target_embed_cpp_data(CppFileExampleApp
    INCLUDE_DIRS
        ../data
    FILES
        data.cpp.in
)
