##****************************************************************************
## Copyright © 2019 Jan Erik Breimo. All rights reserved.
## Created by Jan Erik Breimo on 2019-12-24.
##
## This file is distributed under the BSD License.
## License text is included with the source distribution.
##****************************************************************************
cmake_minimum_required(VERSION 3.13)

set_property(GLOBAL
    PROPERTY
        cppembed_cmake_module_dir "${CMAKE_CURRENT_LIST_DIR}/..")

function(create_unique_target_name parent_target_name context temp_target_name)
    string(UUID _TEMP_NAME NAMESPACE 00000000-0000-0000-0000-000000000000 NAME "${parent_target_name}:${context}" TYPE SHA1)
    set(${temp_target_name} "${target_name}_${_TEMP_NAME}" PARENT_SCOPE)
endfunction()

function(target_embed_cpp_data target_name)
    find_package(Python3 COMPONENTS Interpreter REQUIRED)

    cmake_parse_arguments(ARG "" "FILE_EXTENSION" "INCLUDE_DIRS;FILES" ${ARGN})

    foreach (INCLUDE_PATH IN LISTS ARG_INCLUDE_DIRS)
        file(REAL_PATH "${INCLUDE_PATH}" REAL_INCLUDE_PATH)
        list(APPEND INCLUDE_OPTIONS "-i")
        list(APPEND INCLUDE_OPTIONS "${REAL_INCLUDE_PATH}")
    endforeach ()

    if (DEFINED ARG_FILE_EXTENSION)
        set(FILE_EXTENSION "${FILE_EXTENSION}")
    else ()
        set(FILE_EXTENSION ".h")
    endif ()

    set(ADD_INCLUDE_DIR OFF)
    foreach (INPUT_PATH IN LISTS ARG_FILES)
        file(REAL_PATH "${INPUT_PATH}" REAL_INPUT_PATH)
        get_filename_component(INPUT_EXTENSION ${INPUT_PATH} LAST_EXT)
        get_filename_component(INPUT_NAME ${INPUT_PATH} NAME_WLE)
        if (NOT INPUT_EXTENSION STREQUAL ".in")
            set(INPUT_NAME "${INPUT_NAME}${FILE_EXTENSION}")
        endif ()
        set(OUTPUT_PATH "${CMAKE_CURRENT_BINARY_DIR}/cppembed_include/${INPUT_NAME}")
        get_property(SCRIPT_DIR GLOBAL PROPERTY cppembed_cmake_module_dir)
        set(SCRIPT_PATH ${SCRIPT_DIR}/cppembed.py)

        execute_process(COMMAND "${Python3_EXECUTABLE}" ${SCRIPT_PATH} ${INCLUDE_OPTIONS} "${REAL_INPUT_PATH}" --list-files
            OUTPUT_VARIABLE DEP_FILES
            OUTPUT_STRIP_TRAILING_WHITESPACE
        )

        string(REPLACE "\n" ";" DEP_FILES "${DEP_FILES}")

        add_custom_command(OUTPUT "${OUTPUT_PATH}"
            COMMAND "${Python3_EXECUTABLE}" ${SCRIPT_PATH} ${INCLUDE_OPTIONS} "${REAL_INPUT_PATH}" -o "${OUTPUT_PATH}"
            DEPENDS "${REAL_INPUT_PATH}" ${DEP_FILES}
        )
        list(APPEND OUTPUT_FILES "${OUTPUT_PATH}")
        get_filename_component(OUTPUT_EXTENSION ${OUTPUT_PATH} LAST_EXT)
        message(STATUS "Output extension: ${OUTPUT_EXTENSION}")
        string(REGEX MATCH ".*\.[cC][+cCpP]*$" IS_CPP_FILE "${OUTPUT_EXTENSION}")
        if (IS_CPP_FILE)
            message(STATUS "Adding source to ${target_name}: ${OUTPUT_PATH}")
            target_sources(${target_name} PRIVATE "${OUTPUT_PATH}")
        else ()
            set(ADD_INCLUDE_DIR ON)
        endif ()
    endforeach ()

    create_unique_target_name(${target_name} "${OUTPUT_FILES}" temp_target_name)
    add_custom_target(${temp_target_name} ALL
        DEPENDS ${OUTPUT_FILES}
    )

    add_dependencies(${target_name} ${temp_target_name})

    if (ADD_INCLUDE_DIR)
        set(INCLUDE_DIR "${CMAKE_CURRENT_BINARY_DIR}/cppembed_include")
        message(STATUS "Adding include dir to ${target_name}: ${INCLUDE_DIR}")
        target_include_directories(${target_name} BEFORE
            PRIVATE
                $<BUILD_INTERFACE:${INCLUDE_DIR}>
        )
    endif ()
endfunction()
