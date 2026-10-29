#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <glm/glm.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// Material Blending & Culling Modes
// ---------------------------------------------------------------------------
enum class SideMode : uint8_t {
    Front = 0,
    Back = 1,
    Double = 2
};

enum class BlendMode : uint8_t {
    Opaque = 0,
    Alpha = 1,
    Additive = 2,
    Multiply = 3
};

enum class TextureFilter : uint8_t {
    Nearest = 0,
    Linear = 1
};

enum class TextureWrap : uint8_t {
    Repeat = 0,
    ClampToEdge = 1,
    MirroredRepeat = 2
};

// ---------------------------------------------------------------------------
// GPU Multi-Light Uniform Buffer (Strict 16-byte Alignment)
// Up to 4 Directional, 16 Point, 8 Spot lights
// ---------------------------------------------------------------------------
struct GPUDirectionalLight {
    glm::vec4 direction_and_cast_shadow; // xyz = dir, w = cast_shadow (1.0 or 0.0)
    glm::vec4 color_and_intensity;       // rgb = color, w = intensity
};

struct GPUPointLight {
    glm::vec4 position_and_range;        // xyz = pos, w = range
    glm::vec4 color_and_intensity;       // rgb = color, w = intensity
    glm::vec4 params;                    // x = decay, yzw = padding
};

struct GPUSpotLight {
    glm::vec4 position_and_range;        // xyz = pos, w = range
    glm::vec4 direction_and_cast_shadow; // xyz = dir, w = cast_shadow (1.0 or 0.0)
    glm::vec4 color_and_intensity;       // rgb = color, w = intensity
    glm::vec4 cone_params;               // x = cos_inner, y = cos_outer, z = penumbra, w = padding
};

struct alignas(16) LightParamsUBO {
    glm::vec4 ambient_and_count;         // rgb = ambient color * intensity, w = num_dir_lights
    glm::vec4 light_counts;              // x = num_point_lights, y = num_spot_lights, zw = unused
    glm::vec4 hemi_sky;                  // rgb = sky, w = intensity
    glm::vec4 hemi_ground;               // rgb = ground, w = padding

    GPUDirectionalLight dir_lights[4];
    GPUPointLight point_lights[16];
    GPUSpotLight spot_lights[8];
};

} // namespace engine
