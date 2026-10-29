#pragma once

#include "engine/node3d.hpp"
#include "engine/mesh.hpp"
#include "engine/material.hpp"
#include "engine/animation.hpp"
#include <glm/glm.hpp>
#include <memory>
#include <vector>

namespace engine {

class SkinnedMesh : public Node3D {
public:
    std::shared_ptr<Mesh> mesh{nullptr};
    std::shared_ptr<Skeleton> skeleton{nullptr};
    std::shared_ptr<Material> material{nullptr};
    glm::vec4 color{1.0f};

    glm::mat4 bind_matrix{1.0f};
    glm::mat4 bind_matrix_inverse{1.0f};

    std::vector<Vertex> base_vertices;

    SkinnedMesh(std::shared_ptr<Mesh> mesh = nullptr,
                std::shared_ptr<Skeleton> skeleton = nullptr,
                std::shared_ptr<Material> material = nullptr);
    ~SkinnedMesh() override = default;

    void bind(std::shared_ptr<Skeleton> skel, const glm::mat4& b_matrix = glm::mat4(1.0f));
    void pose();
    void compute_cpu_skinning();

    AABB world_aabb() const override;
    glm::mat4 world_normal_matrix() const;
};

} // namespace engine
