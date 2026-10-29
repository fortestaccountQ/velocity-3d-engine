#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// Skeletal Animation Constants & Contracts
// ---------------------------------------------------------------------------
constexpr size_t MAX_BONES = 128;

enum class InterpolationMode : uint8_t {
    Linear = 0,
    Step = 1,
    CubicSpline = 2
};

struct KeyframeTrack {
    std::string name{};
    std::string property{}; // "translation", "rotation", "scale"
    InterpolationMode interpolation{InterpolationMode::Linear};
    std::vector<float> times;
    std::vector<float> values; // vec3 for pos/scale (3 floats), quat for rot (4 floats)
};

// ---------------------------------------------------------------------------
// Particle System Contracts
// ---------------------------------------------------------------------------
struct Particle {
    glm::vec3 position{0.0f};
    glm::vec3 velocity{0.0f};
    glm::vec4 color{1.0f};
    glm::vec4 start_color{1.0f};
    glm::vec4 end_color{1.0f};
    float size{1.0f};
    float start_size{1.0f};
    float end_size{0.0f};
    float age{0.0f};
    float lifetime{1.0f};
    bool alive{false};
};

} // namespace engine
