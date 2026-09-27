cmake_minimum_required(VERSION 3.24)
project(engine_project VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

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
# STB Dependency
# ---------------------------------------------------------------------------
set(STB_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/third_party/stb")

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
# Core Engine Static Library
# ---------------------------------------------------------------------------
add_library(engine_core STATIC
    core/src/sokol_impl.cpp
    core/src/texture.cpp
    core/src/mesh.cpp
    core/src/scene.cpp
    core/src/input.cpp
    core/src/app.cpp
)

target_include_directories(engine_core PUBLIC
    core/include
    ${SOKOL_INCLUDE_DIR}
    ${STB_INCLUDE_DIR}
)

target_link_libraries(engine_core PUBLIC glm::glm)
target_compile_features(engine_core PUBLIC cxx_std_20)

# Platform-specific configurations
if (WIN32)
    target_compile_definitions(engine_core PUBLIC
        SOKOL_D3D11
        SOKOL_NO_ENTRY
        WIN32_LEAN_AND_MEAN
        NOMINMAX
    )
    target_link_libraries(engine_core PUBLIC d3d11 dxgi d3dcompiler)
elseif (APPLE)
    target_compile_definitions(engine_core PUBLIC
        SOKOL_METAL
        SOKOL_NO_ENTRY
    )
    target_link_libraries(engine_core PUBLIC
        "-framework Metal"
        "-framework MetalKit"
        "-framework Cocoa"
        "-framework QuartzCore"
    )
elseif (EMSCRIPTEN)
    target_compile_definitions(engine_core PUBLIC
        SOKOL_GLES3
        SOKOL_NO_ENTRY
    )
    target_link_options(engine_core PUBLIC "-sUSE_WEBGL2=1")
else() # Linux / Unix
    target_compile_definitions(engine_core PUBLIC
        SOKOL_GLCORE
        SOKOL_NO_ENTRY
    )
    find_package(X11 REQUIRED)
    target_link_libraries(engine_core PUBLIC
        ${X11_LIBRARIES}
        GL
        dl
        pthread
        m
    )
endif()

# ---------------------------------------------------------------------------
# Python Extension Module (_engine_core)
# ---------------------------------------------------------------------------
nanobind_add_module(_engine_core
    NB_STATIC
    bindings/bindings.cpp
)

target_link_libraries(_engine_core PRIVATE engine_core)

# Output compiled binary directly into python package folder for local development
set(ENGINE_OUTPUT_DIR "${CMAKE_CURRENT_SOURCE_DIR}/python/engine")
set_target_properties(_engine_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${ENGINE_OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${ENGINE_OUTPUT_DIR}"
    ARCHIVE_OUTPUT_DIRECTORY "${ENGINE_OUTPUT_DIR}"
)

# For multi-config generators (MSVC Visual Studio)
if (CMAKE_CONFIGURATION_TYPES)
    foreach(CONFIG ${CMAKE_CONFIGURATION_TYPES})
        string(TOUPPER ${CONFIG} CONFIG_UPPER)
        set_target_properties(_engine_core PROPERTIES
            LIBRARY_OUTPUT_DIRECTORY_${CONFIG_UPPER} "${ENGINE_OUTPUT_DIR}"
            RUNTIME_OUTPUT_DIRECTORY_${CONFIG_UPPER} "${ENGINE_OUTPUT_DIR}"
            ARCHIVE_OUTPUT_DIRECTORY_${CONFIG_UPPER} "${ENGINE_OUTPUT_DIR}"
        )
    endforeach()
endif()

# Installation rules for pip / scikit-build-core
install(TARGETS _engine_core DESTINATION engine)
