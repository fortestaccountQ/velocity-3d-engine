#pragma once

#include "engine/node3d.hpp"
#include "contracts/phase2_materials_contracts.h"
#include <glm/glm.hpp>
#include <string>

namespace engine {

enum class LightType : uint8_t {
    Directional = 0,
    Point = 1,
    Spot = 2,
    Hemisphere = 3,
    Ambient = 4
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
    bool cast_shadow{true};

    DirectionalLight(const std::string& name = "DirectionalLight")
        : Light(name, LightType::Directional) {}

    DirectionalLight(const std::string& name, const glm::vec3& dir, const glm::vec3& col = glm::vec3(1.0f), float intens = 1.0f)
        : Light(name, LightType::Directional) {
        set_direction(dir.x, dir.y, dir.z);
        color = col;
        intensity = intens;
    }
};

class PointLight : public Light {
public:
    float decay{2.0f};

    PointLight(const std::string& name = "PointLight", const glm::vec3& col = glm::vec3(1.0f), float intens = 1.0f, float rng = 10.0f, float dec = 2.0f)
        : Light(name, LightType::Point), decay(dec) {
        color = col;
        intensity = intens;
        range = rng;
    }
};

class SpotLight : public Light {
public:
    float inner_cone_angle{0.349066f}; // ~20 degrees in radians
    float outer_cone_angle{0.523599f}; // ~30 degrees in radians
    float penumbra{0.0f};
    bool cast_shadow{false};

    SpotLight(const std::string& name = "SpotLight", const glm::vec3& col = glm::vec3(1.0f), float intens = 1.0f, float rng = 15.0f)
        : Light(name, LightType::Spot) {
        color = col;
        intensity = intens;
        range = rng;
        direction = glm::vec3(0.0f, -1.0f, 0.0f);
    }

    void set_cone_angles(float inner_rad, float outer_rad) {
        inner_cone_angle = inner_rad;
        outer_cone_angle = outer_rad;
    }
};

class HemisphereLight : public Light {
public:
    glm::vec3 sky_color{0.6f, 0.7f, 0.9f};
    glm::vec3 ground_color{0.3f, 0.25f, 0.2f};

    HemisphereLight(const std::string& name = "HemisphereLight", const glm::vec3& sky = glm::vec3(0.6f, 0.7f, 0.9f), const glm::vec3& ground = glm::vec3(0.3f, 0.25f, 0.2f), float intens = 1.0f)
        : Light(name, LightType::Hemisphere), sky_color(sky), ground_color(ground) {
        intensity = intens;
    }
};

class AmbientLight : public Light {
public:
    AmbientLight(const std::string& name = "AmbientLight", const glm::vec3& col = glm::vec3(1.0f), float intens = 0.2f)
        : Light(name, LightType::Ambient) {
        color = col;
        intensity = intens;
    }
};

} // namespace engine
