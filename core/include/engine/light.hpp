#pragma once

#include <glm/glm.hpp>

namespace engine {

struct DirectionalLight {
    glm::vec3 direction{-0.6f, -1.0f, -0.8f};
    glm::vec3 color{1.0f, 0.98f, 0.92f};
    float intensity{1.1f};
    glm::vec3 ambient{0.25f, 0.25f, 0.32f};
    float shininess{32.0f};

    void set_direction(float x, float y, float z) { direction = glm::normalize(glm::vec3(x, y, z)); }
    void set_color(float r, float g, float b) { color = { r, g, b }; }
    void set_ambient(float r, float g, float b) { ambient = { r, g, b }; }
};

} // namespace engine
