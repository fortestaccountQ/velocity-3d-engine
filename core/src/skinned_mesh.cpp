#include "engine/skinned_mesh.hpp"
#include <algorithm>

namespace engine {

SkinnedMesh::SkinnedMesh(std::shared_ptr<Mesh> m,
                         std::shared_ptr<Skeleton> skel,
                         std::shared_ptr<Material> mat)
    : Node3D("SkinnedMesh"), mesh(m), skeleton(skel), material(mat) {
    if (mesh) {
        base_vertices = mesh->cpu_vertices;
        mesh->mark_dynamic();
    }
    if (skeleton) {
        bind(skeleton);
    }
}

void SkinnedMesh::bind(std::shared_ptr<Skeleton> skel, const glm::mat4& b_matrix) {
    skeleton = skel;
    bind_matrix = b_matrix;
    bind_matrix_inverse = glm::inverse(bind_matrix);
    if (mesh && base_vertices.empty()) {
        base_vertices = mesh->cpu_vertices;
        mesh->mark_dynamic();
    }
}

void SkinnedMesh::pose() {
    if (skeleton) {
        skeleton->pose();
    }
}

void SkinnedMesh::compute_cpu_skinning() {
    if (!skeleton || !mesh || base_vertices.empty()) return;

    glm::mat4 inv_world = glm::inverse(world_model_matrix());
    skeleton->compute_bone_matrices(inv_world);

    const auto& bone_mats = skeleton->bone_matrices;
    if (bone_mats.empty()) return;

    size_t n = base_vertices.size();
    if (mesh->cpu_vertices.size() != n) {
        mesh->cpu_vertices.resize(n);
    }

    for (size_t i = 0; i < n; ++i) {
        const auto& base_v = base_vertices[i];
        const glm::vec4& joints = base_v.joints;
        const glm::vec4& weights = base_v.weights;

        glm::vec4 skinned_pos(0.0f);
        glm::vec3 skinned_norm(0.0f);

        float total_weight = weights.x + weights.y + weights.z + weights.w;
        if (total_weight > 0.0001f) {
            for (int j = 0; j < 4; ++j) {
                int b_idx = static_cast<int>(joints[j]);
                float w = weights[j];
                if (w > 0.0f && b_idx >= 0 && b_idx < static_cast<int>(bone_mats.size())) {
                    const glm::mat4& bm = bone_mats[b_idx];
                    skinned_pos += w * (bm * glm::vec4(base_v.position, 1.0f));
                    skinned_norm += w * (glm::mat3(bm) * base_v.normal);
                }
            }
        } else {
            skinned_pos = glm::vec4(base_v.position, 1.0f);
            skinned_norm = base_v.normal;
        }

        mesh->cpu_vertices[i].position = glm::vec3(skinned_pos);
        float norm_len = glm::length(skinned_norm);
        mesh->cpu_vertices[i].normal = norm_len > 1e-6f ? (skinned_norm / norm_len) : base_v.normal;
        mesh->cpu_vertices[i].uv = base_v.uv;
        mesh->cpu_vertices[i].color = base_v.color;
        mesh->cpu_vertices[i].tangent = base_v.tangent;
        mesh->cpu_vertices[i].joints = base_v.joints;
        mesh->cpu_vertices[i].weights = base_v.weights;
    }

    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
}

AABB SkinnedMesh::world_aabb() const {
    if (!mesh || !mesh->local_aabb.is_valid()) {
        return Node3D::world_aabb();
    }
    return mesh->local_aabb.transformed(world_matrix());
}

glm::mat4 SkinnedMesh::world_normal_matrix() const {
    glm::mat3 m3 = glm::mat3(world_matrix());
    return glm::mat4(glm::transpose(glm::inverse(m3)));
}

} // namespace engine
