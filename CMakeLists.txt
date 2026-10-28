cmake_minimum_required(VERSION 3.24)
project(VelocityEngine VERSION 0.2.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
add_compile_definitions(GLM_FORCE_DEPTH_ZERO_TO_ONE)

# ---------------------------------------------------------------------------
# Sokol Dependency (Local fallback -> FetchContent)
# ---------------------------------------------------------------------------
set(LOCAL_SOKOL_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/sokol")
if (EXISTS "${LOCAL_SOKOL_DIR}/sokol_app.h")
    message(STATUS "Using local Sokol headers from: ${LOCAL_SOKOL_DIR}")
    set(SOKOL_INCLUDE_DIR "${LOCAL_SOKOL_DIR}")
else()
    message(STATUS "Fetching Sokol via FetchContent...")
    include(FetchContent)
    FetchContent_Declare(
        sokol
        GIT_REPOSITORY https://github.com/floooh/sokol.git
        GIT_TAG master
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(sokol)
    set(SOKOL_INCLUDE_DIR "${sokol_SOURCE_DIR}")
endif()

# ---------------------------------------------------------------------------
# GLM Dependency (Local fallback -> FetchContent)
# ---------------------------------------------------------------------------
set(LOCAL_GLM_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/glm")
if (EXISTS "${LOCAL_GLM_DIR}/glm/glm.hpp")
    message(STATUS "Using local GLM headers from: ${LOCAL_GLM_DIR}")
    add_library(glm INTERFACE)
    target_include_directories(glm INTERFACE "${LOCAL_GLM_DIR}")
    add_library(glm::glm ALIAS glm)
else()
    message(STATUS "Fetching GLM via FetchContent...")
    include(FetchContent)
    FetchContent_Declare(
        glm
        GIT_REPOSITORY https://github.com/g-truc/glm.git
        GIT_TAG 1.0.1
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(glm)
endif()

# ---------------------------------------------------------------------------
# Third Party Dependencies (STB, cgltf, miniaudio, imgui)
# ---------------------------------------------------------------------------
set(STB_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/stb")
set(CGLTF_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/cgltf")
set(MINIAUDIO_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/miniaudio")
set(IMGUI_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/imgui")

# ---------------------------------------------------------------------------
# Python & Nanobind
# ---------------------------------------------------------------------------
find_package(Python 3.10 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(nanobind CONFIG QUIET)

if (NOT nanobind_FOUND)
    message(STATUS "nanobind not found in system/venv, fetching via FetchContent...")
    include(FetchContent)
    FetchContent_Declare(
        nanobind
        GIT_REPOSITORY https://github.com/wjakob/nanobind.git
        GIT_TAG v2.4.0
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(nanobind)
else()
    message(STATUS "Found nanobind: ${nanobind_DIR}")
endif()

# ---------------------------------------------------------------------------
# Core Engine Static Library (velocity_engine_core)
# ---------------------------------------------------------------------------
add_library(velocity_engine_core STATIC
    core/src/sokol_impl.cpp
    core/src/texture.cpp
    core/src/mesh.cpp
    core/src/scene.cpp
    core/src/model_loader.cpp
    core/src/input.cpp
    core/src/audio.cpp
    core/src/editor.cpp
    core/src/app.cpp
    third_party/imgui/imgui.cpp
    third_party/imgui/imgui_draw.cpp
    third_party/imgui/imgui_tables.cpp
    third_party/imgui/imgui_widgets.cpp
    third_party/imgui/ImGuizmo.cpp
)

# Alias for backwards compatibility if needed
add_library(engine_core ALIAS velocity_engine_core)

target_include_directories(velocity_engine_core PUBLIC
    core/include
    ${SOKOL_INCLUDE_DIR}
    ${STB_INCLUDE_DIR}
    ${CGLTF_INCLUDE_DIR}
    ${MINIAUDIO_INCLUDE_DIR}
    ${IMGUI_INCLUDE_DIR}
)

target_link_libraries(velocity_engine_core PUBLIC glm::glm)
target_compile_features(velocity_engine_core PUBLIC cxx_std_20)

# Platform-specific configurations
if (WIN32)
    target_compile_definitions(velocity_engine_core PUBLIC
        SOKOL_D3D11
        SOKOL_NO_ENTRY
        WIN32_LEAN_AND_MEAN
        NOMINMAX
    )
    target_link_libraries(velocity_engine_core PUBLIC d3d11 dxgi d3dcompiler)
elseif (APPLE)
    target_compile_definitions(velocity_engine_core PUBLIC
        SOKOL_METAL
        SOKOL_NO_ENTRY
    )
    target_link_libraries(velocity_engine_core PUBLIC
        "-framework Metal"
        "-framework MetalKit"
        "-framework Cocoa"
        "-framework QuartzCore"
    )
elseif (EMSCRIPTEN)
    target_compile_definitions(velocity_engine_core PUBLIC
        SOKOL_GLES3
        SOKOL_NO_ENTRY
    )
    target_link_options(velocity_engine_core PUBLIC "-sUSE_WEBGL2=1")
else() # Linux / Unix
    target_compile_definitions(velocity_engine_core PUBLIC
        SOKOL_GLCORE
        SOKOL_NO_ENTRY
    )
    find_package(X11 REQUIRED)
    target_link_libraries(velocity_engine_core PUBLIC
        ${X11_LIBRARIES}
        GL
        dl
        pthread
        m
    )
endif()

# ---------------------------------------------------------------------------
# Python Extension Module (_VelocityEngine_core)
# ---------------------------------------------------------------------------
nanobind_add_module(_VelocityEngine_core
    NB_STATIC
    bindings/bindings.cpp
)

target_link_libraries(_VelocityEngine_core PRIVATE velocity_engine_core)

# Output compiled binary directly into VelocityEngine and engine package folders
set(VELOCITY_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/python/VelocityEngine")
set(ENGINE_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/python/engine")

set_target_properties(_VelocityEngine_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${VELOCITY_OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${VELOCITY_OUTPUT_DIR}"
    ARCHIVE_OUTPUT_DIRECTORY "${VELOCITY_OUTPUT_DIR}"
)

if (CMAKE_CONFIGURATION_TYPES)
    foreach(CONFIG ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${CONFIG} CONFIG_UPPER)
        set_target_properties(_VelocityEngine_core PROPERTIES
            LIBRARY_OUTPUT_DIRECTORY_${CONFIG_UPPER} "${VELOCITY_OUTPUT_DIR}"
            RUNTIME_OUTPUT_DIRECTORY_${CONFIG_UPPER} "${VELOCITY_OUTPUT_DIR}"
            ARCHIVE_OUTPUT_DIRECTORY_${CONFIG_UPPER} "${VELOCITY_OUTPUT_DIR}"
        )
    endforeach()
endif()

# Post-build copy to python/engine for backwards compatibility
add_custom_command(TARGET _VelocityEngine_core POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory "${ENGINE_OUTPUT_DIR}"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "$<TARGET_FILE:_VelocityEngine_core>" "${ENGINE_OUTPUT_DIR}/"
)

# Installation rules for pip / scikit-build-core
install(TARGETS _VelocityEngine_core DESTINATION VelocityEngine)
