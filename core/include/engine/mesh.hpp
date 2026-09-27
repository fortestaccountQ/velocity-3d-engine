#pragma once

#include <glm/glm.hpp>
#include <memory>
#include <cstdint>
#include <vector>

#include "engine/physics.hpp"

namespace engine {

struct Vertex {
    glm::vec3 position;
    glm::vec3 normal;
    glm::vec2 uv;
    glm::vec4 color;
};

class Mesh {
public:
    Mesh() = default;
    ~Mesh();

    uint32_t vbuf_id{0};
    uint32_t ibuf_id{0};
    int num_indices{0};

    std::vector<Vertex> cpu_vertices;
    std::vector<uint16_t> cpu_indices;

    AABB local_aabb;

    void calculate_aabb() {
        local_aabb = AABB{};
        for (const auto& v : cpu_vertices) {
            local_aabb.expand(v.position);
        }
    }

    bool ensure_gpu_buffers();
    void destroy();

    static std::shared_ptr<Mesh> create_cube();
    static std::shared_ptr<Mesh> create_plane(float size = 10.0f, float uv_tiling = 5.0f);
};

} // namespace engine
