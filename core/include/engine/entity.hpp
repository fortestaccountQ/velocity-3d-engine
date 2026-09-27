#pragma once

#include "engine/transform.hpp"
#include "engine/mesh.hpp"
#include "engine/material.hpp"
#include <string>
#include <memory>

namespace engine {

class Entity {
public:
    uint32_t id{0};
    std::string name{"Entity"};
    Transform transform;
    glm::mat4 local_matrix{1.0f};
    std::shared_ptr<Entity> parent{nullptr};

    std::shared_ptr<Mesh> mesh{nullptr};
    std::shared_ptr<Material> material{nullptr};
    glm::vec4 color{1.0f, 1.0f, 1.0f, 1.0f};
    bool visible{true};

    Entity(uint32_t id, const std::string& name = "Entity")
        : id(id), name(name) {}

    glm::mat4 world_model_matrix() const {
        glm::mat4 self_m = transform.model_matrix() * local_matrix;
        if (parent) {
            return parent->world_model_matrix() * self_m;
        }
        return self_m;
    }

    glm::mat4 world_normal_matrix() const {
        glm::mat3 m3 = glm::mat3(world_model_matrix());
        return glm::mat4(glm::transpose(glm::inverse(m3)));
    }

    void set_color(float r, float g, float b, float a = 1.0f) {
        color = { r, g, b, a };
        if (material) {
            material->set_color(r, g, b, a);
        }
    }
};

} // namespace engine
