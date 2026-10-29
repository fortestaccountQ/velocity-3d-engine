#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <glm/glm.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// Camera Projection & Viewport Contracts
// ---------------------------------------------------------------------------
struct ViewportRect {
    float x{0.0f};
    float y{0.0f};
    float width{1.0f};   // 0.0 to 1.0 normalized or absolute pixels
    float height{1.0f};
    bool is_normalized{true};
};

enum class CameraType : uint8_t {
    Perspective = 0,
    Orthographic = 1
};

// ---------------------------------------------------------------------------
// Render Target Color Format
// ---------------------------------------------------------------------------
enum class RenderTargetFormat : uint8_t {
    RGBA8 = 0,
    RGBA16F = 1
};

// ---------------------------------------------------------------------------
// Tonemapping Modes for Post-Processing
// ---------------------------------------------------------------------------
enum class TonemappingMode : uint8_t {
    Linear = 0,
    Reinhard = 1,
    ACESFilmic = 2,
    AgX = 3
};

} // namespace engine
