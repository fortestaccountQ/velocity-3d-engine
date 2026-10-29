#pragma once

#include "engine/entity.hpp"
#include "engine/skinned_mesh.hpp"
#include <string>
#include <vector>
#include <memory>

namespace engine {

class AnimationClip;
class Skeleton;

class Model {
public:
    std::string name;
    std::shared_ptr<Entity> root_entity;
    std::vector<std::shared_ptr<Entity>> meshes;
    std::vector<std::shared_ptr<AnimationClip>> animations;
    std::shared_ptr<Skeleton> skeleton{nullptr};
    std::vector<std::shared_ptr<SkinnedMesh>> skinned_meshes;

    Model(std::shared_ptr<Entity> root, const std::string& name = "Model")
        : root_entity(root), name(name) {}

    Transform& transform() { return root_entity->transform; }
    const Transform& transform() const { return root_entity->transform; }

    void set_position(float x, float y, float z) { root_entity->transform.set_position(x, y, z); }
    void set_rotation(float rx, float ry, float rz) { root_entity->transform.set_rotation(rx, ry, rz); }
    void set_scale(float sx, float sy, float sz) { root_entity->transform.set_scale(sx, sy, sz); }

    void set_visible(bool v) {
        root_entity->visible = v;
        for (auto& m : meshes) {
            if (m) m->visible = v;
        }
        for (auto& sm : skinned_meshes) {
            if (sm) sm->visible = v;
        }
    }

    bool is_visible() const { return root_entity->visible; }

    AABB world_aabb() const {
        AABB box;
        for (const auto& m : meshes) {
            if (m && m->visible) {
                box.expand(m->world_aabb());
            }
        }
        for (const auto& sm : skinned_meshes) {
            if (sm && sm->visible) {
                box.expand(sm->world_aabb());
            }
        }
        return box;
    }

    float collision_scale() const {
        return meshes.empty() ? 1.0f : meshes[0]->collision_scale;
    }

    void set_collision_scale(float scale) {
        for (auto& m : meshes) {
            if (m) m->collision_scale = scale;
        }
    }

    void set_collision_padding(float px, float py, float pz) {
        for (auto& m : meshes) {
            if (m) m->collision_padding = { px, py, pz };
        }
    }

    void set_cast_shadows(bool cast) {
        for (auto& m : meshes) {
            if (m) m->cast_shadows = cast;
        }
    }
};

} // namespace engine
