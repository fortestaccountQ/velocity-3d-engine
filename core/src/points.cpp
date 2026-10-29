#include "engine/points.hpp"
#include <algorithm>

namespace engine {

Points::Points(std::shared_ptr<Mesh> geom, std::shared_ptr<Material> mat)
    : Node3D("Points"), mesh(geom), material(mat) {
    if (!mesh) {
        mesh = std::make_shared<Mesh>();
        mesh->mark_dynamic();
    } else {
        mesh->mark_dynamic();
    }
    if (!material) {
        material = std::make_shared<PointsMaterial>(1.0f);
    }
}

void Points::set_positions_from_numpy(const float* data, size_t count) {
    if (!data || count == 0) return;
    if (!mesh) {
        mesh = std::make_shared<Mesh>();
        mesh->mark_dynamic();
    }
    mesh->cpu_vertices.resize(count);
    mesh->cpu_indices.resize(count);
    for (size_t i = 0; i < count; ++i) {
        mesh->cpu_vertices[i].position = glm::vec3(data[i * 3 + 0], data[i * 3 + 1], data[i * 3 + 2]);
        mesh->cpu_vertices[i].normal = glm::vec3(0.0f, 1.0f, 0.0f);
        mesh->cpu_vertices[i].uv = glm::vec2(0.0f);
        if (mesh->cpu_vertices[i].color == glm::vec4(0.0f)) {
            mesh->cpu_vertices[i].color = glm::vec4(1.0f);
        }
        mesh->cpu_indices[i] = static_cast<uint16_t>(i);
    }
    mesh->num_indices = static_cast<int>(count);
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
}

void Points::set_colors_from_numpy(const float* data, size_t count) {
    if (!data || count == 0 || !mesh) return;
    size_t n = std::min(count, mesh->cpu_vertices.size());
    for (size_t i = 0; i < n; ++i) {
        mesh->cpu_vertices[i].color = glm::vec4(data[i * 4 + 0], data[i * 4 + 1], data[i * 4 + 2], data[i * 4 + 3]);
    }
    mesh->ensure_gpu_buffers();
}

void Points::set_positions(const std::vector<float>& coords) {
    if (coords.empty()) return;
    set_positions_from_numpy(coords.data(), coords.size() / 3);
}

void Points::set_colors(const std::vector<float>& colors) {
    if (colors.empty()) return;
    if (colors.size() % 4 == 0) {
        set_colors_from_numpy(colors.data(), colors.size() / 4);
    } else if (colors.size() % 3 == 0) {
        size_t count = colors.size() / 3;
        std::vector<float> rgba(count * 4);
        for (size_t i = 0; i < count; ++i) {
            rgba[i * 4 + 0] = colors[i * 3 + 0];
            rgba[i * 4 + 1] = colors[i * 3 + 1];
            rgba[i * 4 + 2] = colors[i * 3 + 2];
            rgba[i * 4 + 3] = 1.0f;
        }
        set_colors_from_numpy(rgba.data(), count);
    }
}

AABB Points::world_aabb() const {
    if (!mesh || !mesh->local_aabb.is_valid()) {
        return Node3D::world_aabb();
    }
    return mesh->local_aabb.transformed(world_matrix());
}

} // namespace engine
