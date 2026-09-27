#pragma once

#include <glm/glm.hpp>

namespace engine {

struct DirectionalLight {
    glm::vec3 direction{-0.4f, -0.8f, -0.4f};
    glm::vec3 color{1.10f, 1.05f, 0.95f}; // warm golden sunlight
    float intensity{1.25f};
    glm::vec3 ambient{0.35f, 0.40f, 0.50f};
    glm::vec3 ambient_sky{0.50f, 0.60f, 0.75f};    // Sky ambient (top)
    glm::vec3 ambient_ground{0.25f, 0.22f, 0.20f}; // Earth bounce (bottom)
    float shininess{32.0f};

    void set_direction(float x, float y, float z) { direction = glm::normalize(glm::vec3(x, y, z)); }
    void set_color(float r, float g, float b) { color = { r, g, b }; }
    void set_ambient(float r, float g, float b) { ambient = { r, g, b }; }
    void set_hemispheric_ambient(float sr, float sg, float sb, float gr, float gg, float gb) {
        ambient_sky = { sr, sg, sb };
        ambient_ground = { gr, gg, gb };
    }
};

} // namespace engine
