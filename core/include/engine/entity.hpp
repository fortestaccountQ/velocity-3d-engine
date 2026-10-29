#pragma once

#include "engine/node3d.hpp"
#include "engine/transform.hpp"
#include "engine/mesh.hpp"
#include "engine/material.hpp"
#include <string>
#include <memory>
#include <array>

namespace engine {

class Entity : public Node3D {
public:
    glm::mat4 local_matrix{1.0f};
    std::shared_ptr<Entity> parent{nullptr};

    std::shared_ptr<Mesh> mesh{nullptr};
    std::shared_ptr<Material> material{nullptr};
    glm::vec4 color{1.0f, 1.0f, 1.0f, 1.0f};
    std::string script_path{""};

    bool has_collision{true};
    float collision_scale{1.0f};
    glm::vec3 collision_padding{0.0f};

    Entity(uint32_t ent_id = 0, const std::string& ent_name = "Entity")
        : Node3D(ent_name) {
        if (ent_id != 0) {
            id = ent_id;
        }
    }

    Entity(const std::string& ent_name)
        : Node3D(ent_name) {}

    glm::mat4 world_model_matrix() const {
        glm::mat4 self_m = transform.model_matrix() * local_matrix;
        if (parent) {
            return parent->world_model_matrix() * self_m;
        }
        if (parent_) {
            return parent_->world_model_matrix() * self_m;
        }
        return self_m;
    }

    glm::mat4 world_normal_matrix() const {
        glm::mat3 m3 = glm::mat3(world_model_matrix());
        return glm::mat4(glm::transpose(glm::inverse(m3)));
    }

    AABB local_collision_box() const {
        if (!mesh || !mesh->local_aabb.is_valid()) {
            return AABB{};
        }
        AABB box = mesh->local_aabb;
        if (collision_scale != 1.0f) {
            box = box.scaled(collision_scale);
        }
        if (collision_padding.x != 0.0f || collision_padding.y != 0.0f || collision_padding.z != 0.0f) {
            box.min_point += collision_padding;
            box.max_point -= collision_padding;
        }
        return box;
    }

    std::array<glm::vec3, 8> world_obb_corners() const {
        AABB lbox = local_collision_box();
        std::array<glm::vec3, 8> corners{};
        if (!lbox.is_valid()) return corners;

        glm::vec3 min_p = lbox.min_point;
        glm::vec3 max_p = lbox.max_point;

        glm::vec3 lc[8] = {
            { min_p.x, min_p.y, min_p.z }, { max_p.x, min_p.y, min_p.z },
            { max_p.x, max_p.y, min_p.z }, { min_p.x, max_p.y, min_p.z },
            { min_p.x, min_p.y, max_p.z }, { max_p.x, min_p.y, max_p.z },
            { max_p.x, max_p.y, max_p.z }, { min_p.x, max_p.y, max_p.z }
        };

        glm::mat4 model = world_model_matrix();
        for (int i = 0; i < 8; ++i) {
            corners[i] = glm::vec3(model * glm::vec4(lc[i], 1.0f));
        }
        return corners;
    }

    AABB world_aabb() const override {
        AABB lbox = local_collision_box();
        if (!lbox.is_valid()) {
            return AABB{ world_position(), world_position() };
        }
        return lbox.transformed(world_model_matrix());
    }

    BoundingSphere world_bounding_sphere() const {
        AABB w_aabb = world_aabb();
        return BoundingSphere::from_aabb(w_aabb);
    }

    void set_color(float r, float g, float b, float a = 1.0f) {
        color = { r, g, b, a };
        if (material) {
            material->set_color(r, g, b, a);
        }
    }
};

} // namespace engine
