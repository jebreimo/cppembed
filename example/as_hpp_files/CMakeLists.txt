list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_LIST_DIR}/../../cmake")

include(TargetEmbedCppData)

add_executable(HppFileExampleApp
    test.cpp
)

target_embed_cpp_data(HppFileExampleApp
    FILES
        pdf_data.hpp.in
)

target_embed_cpp_data(HppFileExampleApp
    FILES
        txt_data.hpp.in
)
