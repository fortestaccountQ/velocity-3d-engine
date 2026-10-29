#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <variant>
#include <glm/glm.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// Background Type Contract
// ---------------------------------------------------------------------------
enum class BackgroundType : uint8_t {
    Color = 0,
    Texture2D = 1,
    CubeMap = 2,
    ProceduralSky = 3
};

// ---------------------------------------------------------------------------
// Shadow Map Configuration Contract (Shadows v2)
// ---------------------------------------------------------------------------
struct ShadowSettings {
    int resolution{2048};               // 1024, 2048, 4096
    float bias{0.0015f};
    float normal_bias{0.02f};
    float ortho_size{40.0f};           // Half-extent of camera-following shadow box
    float near_z{1.0f};
    float far_z{120.0f};
    bool texel_snapping{true};
    bool pcf_16_tap{true};             // Poisson Disk 16-tap filtering
};

// ---------------------------------------------------------------------------
// Procedural Sky Parameters Contract
// ---------------------------------------------------------------------------
struct SkyParams {
    glm::vec3 sun_direction{0.4f, 0.8f, 0.4f};
    glm::vec3 rayleigh_color{0.25f, 0.55f, 0.95f};
    glm::vec3 mie_color{0.95f, 0.90f, 0.80f};
    float turbidity{2.0f};
    float rayleigh{1.0f};
    float mie_coefficient{0.005f};
    float mie_directional_g{0.8f};
    float time_of_day{12.0f};          // 0.0 to 24.0 hours
};

} // namespace engine
