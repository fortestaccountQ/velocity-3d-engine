#pragma once

#include "engine/node3d.hpp"
#include <glm/glm.hpp>
#include <string>

namespace engine {

enum class LightType : uint8_t {
    Directional = 0,
    Point = 1,
    Spot = 2
};

class Light : public Node3D {
public:
    LightType type{LightType::Directional};
    glm::vec3 direction{-0.4f, -0.8f, -0.4f};
    glm::vec3 color{1.10f, 1.05f, 0.95f}; // warm golden sunlight
    float intensity{1.25f};
    glm::vec3 ambient{0.35f, 0.40f, 0.50f};
    glm::vec3 ambient_sky{0.50f, 0.60f, 0.75f};    // Sky ambient (top)
    glm::vec3 ambient_ground{0.25f, 0.22f, 0.20f}; // Earth bounce (bottom)
    float shininess{32.0f};
    float range{10.0f};

    Light(const std::string& light_name = "Light", LightType l_type = LightType::Directional)
        : Node3D(light_name), type(l_type) {
        set_direction(direction.x, direction.y, direction.z);
    }

    void set_direction(float x, float y, float z) {
        direction = glm::normalize(glm::vec3(x, y, z));
        transform.set_orientation(quat_look_rotation(direction, glm::vec3(0.0f, 1.0f, 0.0f)));
        invalidate_world_matrix();
    }

    glm::vec3 get_world_direction() const {
        return world_direction();
    }

    glm::vec3 get_world_position() const {
        return world_position();
    }

    void set_color(float r, float g, float b) { color = { r, g, b }; }
    void set_ambient(float r, float g, float b) { ambient = { r, g, b }; }
    void set_hemispheric_ambient(float sr, float sg, float sb, float gr, float gg, float gb) {
        ambient_sky = { sr, sg, sb };
        ambient_ground = { gr, gg, gb };
    }
};

class DirectionalLight : public Light {
public:
    DirectionalLight(const std::string& name = "DirectionalLight")
        : Light(name, LightType::Directional) {}
};

} // namespace engine
