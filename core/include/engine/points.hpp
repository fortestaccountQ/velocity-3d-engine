#pragma once

#include "engine/node3d.hpp"
#include "engine/mesh.hpp"
#include "engine/material.hpp"
#include <glm/glm.hpp>
#include <memory>
#include <vector>

namespace engine {

class PointsMaterial : public Material {
public:
    float size{1.0f};
    bool size_attenuation{true};

    PointsMaterial(float pt_size = 1.0f, const glm::vec4& col = glm::vec4(1.0f))
        : Material(nullptr, 1.0f, 0.0f), size(pt_size) {
        base_color = col;
    }
    ~PointsMaterial() override = default;

    MaterialType type() const override { return MaterialType::Unlit; }
};

class Points : public Node3D {
public:
    std::shared_ptr<Mesh> mesh{nullptr};
    std::shared_ptr<Material> material{nullptr};
    float size{1.0f};
    bool size_attenuation{true};

    Points(std::shared_ptr<Mesh> geom = nullptr, std::shared_ptr<Material> mat = nullptr);
    ~Points() override = default;

    void set_positions_from_numpy(const float* data, size_t count);
    void set_colors_from_numpy(const float* data, size_t count);
    void set_positions(const std::vector<float>& coords);
    void set_colors(const std::vector<float>& colors);

    AABB world_aabb() const override;
};

} // namespace engine
