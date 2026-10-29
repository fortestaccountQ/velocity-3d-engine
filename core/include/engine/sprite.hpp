#pragma once

#include "engine/node3d.hpp"
#include "engine/material.hpp"
#include "engine/camera.hpp"
#include "engine/mesh.hpp"
#include <glm/glm.hpp>
#include <memory>

namespace engine {

class SpriteMaterial : public Material {
public:
    float rotation{0.0f};
    bool size_attenuation{true};

    SpriteMaterial(std::shared_ptr<Texture> tex = nullptr, const glm::vec4& col = glm::vec4(1.0f));
    ~SpriteMaterial() override = default;

    MaterialType type() const override { return MaterialType::Unlit; }
};

class Sprite : public Node3D {
public:
    std::shared_ptr<SpriteMaterial> material{nullptr};
    glm::vec2 center{0.5f, 0.5f};

    Sprite(std::shared_ptr<SpriteMaterial> mat = nullptr);
    ~Sprite() override = default;

    glm::mat4 compute_billboard_matrix(const Camera& camera) const;
    AABB world_aabb() const override;

    static std::shared_ptr<Mesh> quad_mesh();
};

} // namespace engine
