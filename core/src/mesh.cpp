#include "engine/mesh.hpp"

#include "sokol_gfx.h"

namespace engine {

Mesh::~Mesh() {
    destroy();
}

void Mesh::destroy() {
    if (vbuf_id != 0) {
        sg_destroy_buffer(sg_buffer{vbuf_id});
        vbuf_id = 0;
    }
    if (ibuf_id != 0) {
        sg_destroy_buffer(sg_buffer{ibuf_id});
        ibuf_id = 0;
    }
}

std::shared_ptr<Mesh> Mesh::create_cube() {
    auto mesh = std::make_shared<Mesh>();

    // 24 vertices with distinct positions, normals and base colors for 6 faces
    const Vertex vertices[24] = {
        // Back face (Z = -1, normal: 0, 0, -1)
        { { -1.0f, -1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f, -1.0f }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Front face (Z = +1, normal: 0, 0, +1)
        { { -1.0f, -1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f,  1.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Left face (X = -1, normal: -1, 0, 0)
        { { -1.0f, -1.0f, -1.0f }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f, -1.0f }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f,  1.0f }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f, -1.0f,  1.0f }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Right face (X = +1, normal: +1, 0, 0)
        { {  1.0f, -1.0f, -1.0f }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f, -1.0f }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f,  1.0f }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f,  1.0f }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Bottom face (Y = -1, normal: 0, -1, 0)
        { { -1.0f, -1.0f, -1.0f }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f, -1.0f,  1.0f }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f,  1.0f }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f, -1.0f, -1.0f }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Top face (Y = +1, normal: 0, +1, 0)
        { { -1.0f,  1.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -1.0f,  1.0f,  1.0f }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f,  1.0f }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  1.0f,  1.0f, -1.0f }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
    };

    const uint16_t indices[36] = {
        0,  1,  2,    0,  2,  3,
        6,  5,  4,    7,  6,  4,
        8,  9, 10,    8, 10, 11,
       14, 13, 12,   15, 14, 12,
       16, 17, 18,   16, 18, 19,
       22, 21, 20,   23, 22, 20
    };

    sg_buffer_desc vbuf_desc{};
    vbuf_desc.usage.vertex_buffer = true;
    vbuf_desc.data = SG_RANGE(vertices);
    vbuf_desc.label = "cube-mesh-vbuf";
    sg_buffer vbuf = sg_make_buffer(&vbuf_desc);
    mesh->vbuf_id = vbuf.id;

    sg_buffer_desc ibuf_desc{};
    ibuf_desc.usage.index_buffer = true;
    ibuf_desc.data = SG_RANGE(indices);
    ibuf_desc.label = "cube-mesh-ibuf";
    sg_buffer ibuf = sg_make_buffer(&ibuf_desc);
    mesh->ibuf_id = ibuf.id;

    mesh->num_indices = 36;
    return mesh;
}

} // namespace engine
