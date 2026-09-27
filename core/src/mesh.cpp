#include "engine/mesh.hpp"

#include "sokol_gfx.h"

namespace engine {

Mesh::~Mesh() {
    destroy();
}

void Mesh::destroy() {
    if (vbuf_id != 0) {
        if (sg_isvalid()) {
            sg_destroy_buffer(sg_buffer{vbuf_id});
        }
        vbuf_id = 0;
    }
    if (ibuf_id != 0) {
        if (sg_isvalid()) {
            sg_destroy_buffer(sg_buffer{ibuf_id});
        }
        ibuf_id = 0;
    }
}

bool Mesh::ensure_gpu_buffers() {
    if (vbuf_id != 0 && ibuf_id != 0) {
        return true;
    }
    if (!sg_isvalid()) {
        return false;
    }
    if (cpu_vertices.empty() || cpu_indices.empty()) {
        return false;
    }

    sg_buffer_desc vbuf_desc{};
    vbuf_desc.usage.vertex_buffer = true;
    vbuf_desc.data = { cpu_vertices.data(), cpu_vertices.size() * sizeof(Vertex) };
    vbuf_desc.label = "mesh-vbuf";
    sg_buffer vbuf = sg_make_buffer(&vbuf_desc);
    vbuf_id = vbuf.id;

    sg_buffer_desc ibuf_desc{};
    ibuf_desc.usage.index_buffer = true;
    ibuf_desc.data = { cpu_indices.data(), cpu_indices.size() * sizeof(uint16_t) };
    ibuf_desc.label = "mesh-ibuf";
    sg_buffer ibuf = sg_make_buffer(&ibuf_desc);
    ibuf_id = ibuf.id;

    num_indices = static_cast<int>(cpu_indices.size());
    return (vbuf_id != 0 && ibuf_id != 0);
}

std::shared_ptr<Mesh> Mesh::create_cube() {
    auto mesh = std::make_shared<Mesh>();

    // 24 vertices for 6 faces with proper position, normal, UV coordinates and base tint
    mesh->cpu_vertices = {
        // Back face (Z = -1, normal: 0, 0, -1)
        { { -1.0f, -1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Front face (Z = +1, normal: 0, 0, +1)
        { { -1.0f, -1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Left face (X = -1, normal: -1, 0, 0)
        { { -1.0f, -1.0f, -1.0f }, { -1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f, -1.0f }, { -1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f,  1.0f }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f, -1.0f,  1.0f }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Right face (X = +1, normal: +1, 0, 0)
        { {  1.0f, -1.0f, -1.0f }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f, -1.0f }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f,  1.0f }, { 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f,  1.0f }, { 1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Bottom face (Y = -1, normal: 0, -1, 0)
        { { -1.0f, -1.0f, -1.0f }, { 0.0f, -1.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f, -1.0f,  1.0f }, { 0.0f, -1.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f,  1.0f }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f, -1.0f }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Top face (Y = +1, normal: 0, +1, 0)
        { { -1.0f,  1.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f,  1.0f }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f,  1.0f }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
    };

    mesh->cpu_indices = {
        0,  1,  2,    0,  2,  3,
        6,  5,  4,    7,  6,  4,
        8,  9, 10,    8, 10, 11,
       14, 13, 12,   15, 14, 12,
       16, 17, 18,   16, 18, 19,
       22, 21, 20,   23, 22, 20
    };

    mesh->num_indices = 36;
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_plane(float size, float uv_tiling) {
    auto mesh = std::make_shared<Mesh>();
    float half = size * 0.5f;

    // Horizontal plane on XZ (Y = 0) with normal pointing up (0, 1, 0)
    mesh->cpu_vertices = {
        { { -half, 0.0f, -half }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  half, 0.0f, -half }, { 0.0f, 1.0f, 0.0f }, { uv_tiling, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  half, 0.0f,  half }, { 0.0f, 1.0f, 0.0f }, { uv_tiling, uv_tiling }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -half, 0.0f,  half }, { 0.0f, 1.0f, 0.0f }, { 0.0f, uv_tiling }, { 1.0f, 1.0f, 1.0f, 1.0f } },
    };

    mesh->cpu_indices = {
        0, 1, 2,
        0, 2, 3
    };

    mesh->num_indices = 6;
    mesh->ensure_gpu_buffers();
    return mesh;
}

} // namespace engine
