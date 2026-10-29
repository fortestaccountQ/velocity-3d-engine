#include "engine/mesh.hpp"
#include "engine/curve.hpp"

#include "sokol_gfx.h"
#include <cmath>
#include <algorithm>

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
    if (is_dynamic) {
        vbuf_desc.usage.dynamic_update = true;
    }
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

void Mesh::update_vertices_raw(const float* raw_data, size_t num_floats) {
    if (!raw_data || num_floats == 0) return;
    mark_dynamic();
    size_t byte_size = num_floats * sizeof(float);

    if (vbuf_id == 0) {
        size_t vert_count = byte_size / sizeof(Vertex);
        if (cpu_vertices.size() < vert_count) {
            cpu_vertices.resize(vert_count);
        }
        std::memcpy(cpu_vertices.data(), raw_data, byte_size);
        ensure_gpu_buffers();
    } else if (sg_isvalid()) {
        sg_range range{ raw_data, byte_size };
        sg_update_buffer(sg_buffer{ vbuf_id }, &range);
    }
}

std::shared_ptr<Mesh> Mesh::create_box(float width, float height, float depth) {
    auto mesh = std::make_shared<Mesh>();
    float hw = width * 0.5f;
    float hh = height * 0.5f;
    float hd = depth * 0.5f;

    // 24 vertices for 6 faces with proper position, normal, UV coordinates, base tint, and analytical tangents
    mesh->cpu_vertices = {
        // Front face (Z = +hd, normal: 0, 0, +1)
        { { -hw, -hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { {  hw, -hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { {  hw,  hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { { -hw,  hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },

        // Back face (Z = -hd, normal: 0, 0, -1)
        { {  hw, -hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { -1.0f, 0.0f, 0.0f, 1.0f } },
        { { -hw, -hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { -1.0f, 0.0f, 0.0f, 1.0f } },
        { { -hw,  hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { -1.0f, 0.0f, 0.0f, 1.0f } },
        { {  hw,  hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { -1.0f, 0.0f, 0.0f, 1.0f } },

        // Left face (X = -hw, normal: -1, 0, 0)
        { { -hw, -hh, -hd }, { -1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, 1.0f, 1.0f } },
        { { -hw, -hh,  hd }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, 1.0f, 1.0f } },
        { { -hw,  hh,  hd }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, 1.0f, 1.0f } },
        { { -hw,  hh, -hd }, { -1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, 1.0f, 1.0f } },

        // Right face (X = +hw, normal: +1, 0, 0)
        { {  hw, -hh,  hd }, { 1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, -1.0f, 1.0f } },
        { {  hw, -hh, -hd }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, -1.0f, 1.0f } },
        { {  hw,  hh, -hd }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, -1.0f, 1.0f } },
        { {  hw,  hh,  hd }, { 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 0.0f, 0.0f, -1.0f, 1.0f } },

        // Top face (Y = +hh, normal: 0, +1, 0)
        { { -hw,  hh,  hd }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { {  hw,  hh,  hd }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { {  hw,  hh, -hd }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { { -hw,  hh, -hd }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },

        // Bottom face (Y = -hh, normal: 0, -1, 0)
        { { -hw, -hh, -hd }, { 0.0f, -1.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { {  hw, -hh, -hd }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { {  hw, -hh,  hd }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
        { { -hw, -hh,  hd }, { 0.0f, -1.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } },
    };

    mesh->cpu_indices = {
         0,  1,  2,    0,  2,  3,
         4,  5,  6,    4,  6,  7,
         8,  9, 10,    8, 10, 11,
        12, 13, 14,   12, 14, 15,
        16, 17, 18,   16, 18, 19,
        20, 21, 22,   20, 22, 23
    };

    mesh->num_indices = 36;
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_cube() {
    return create_box(2.0f, 2.0f, 2.0f);
}

std::shared_ptr<Mesh> Mesh::create_sphere(float radius, int rings, int sectors) {
    auto mesh = std::make_shared<Mesh>();
    if (rings < 2) rings = 2;
    if (sectors < 3) sectors = 3;

    mesh->cpu_vertices.reserve((rings + 1) * (sectors + 1));
    mesh->cpu_indices.reserve((rings - 1) * sectors * 6);

    const float pi = 3.14159265358979323846f;
    for (int r = 0; r <= rings; ++r) {
        float v = static_cast<float>(r) / static_cast<float>(rings);
        float phi = v * pi; // 0 (north pole, +Y) to pi (south pole, -Y)
        float cos_phi = std::cos(phi);
        float sin_phi = std::sin(phi);

        for (int s = 0; s <= sectors; ++s) {
            float u = static_cast<float>(s) / static_cast<float>(sectors);
            float theta = u * 2.0f * pi; // 0 to 2*pi

            float cos_theta = std::cos(theta);
            float sin_theta = std::sin(theta);

            glm::vec3 normal(sin_phi * cos_theta, cos_phi, sin_phi * sin_theta);
            glm::vec3 position = normal * radius;
            glm::vec2 uv(u, 1.0f - v);
            glm::vec4 tangent(-sin_theta, 0.0f, cos_theta, 1.0f);

            mesh->cpu_vertices.push_back({ position, normal, uv, glm::vec4(1.0f), tangent });
        }
    }

    for (int r = 0; r < rings; ++r) {
        for (int s = 0; s < sectors; ++s) {
            uint16_t i0 = static_cast<uint16_t>(r * (sectors + 1) + s);
            uint16_t i1 = static_cast<uint16_t>(i0 + 1);
            uint16_t i2 = static_cast<uint16_t>((r + 1) * (sectors + 1) + s);
            uint16_t i3 = static_cast<uint16_t>(i2 + 1);

            if (r != 0) {
                mesh->cpu_indices.push_back(i0);
                mesh->cpu_indices.push_back(i1);
                mesh->cpu_indices.push_back(i2);
            }
            if (r != rings - 1) {
                mesh->cpu_indices.push_back(i1);
                mesh->cpu_indices.push_back(i3);
                mesh->cpu_indices.push_back(i2);
            }
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_cylinder(float radius, float height, int segments, bool capped) {
    auto mesh = std::make_shared<Mesh>();
    if (segments < 3) segments = 3;

    float half_h = height * 0.5f;
    const float pi = 3.14159265358979323846f;

    // Side wall vertices
    // We create (segments + 1) pairs of vertices for proper UV wrapping at u=0 and u=1
    for (int s = 0; s <= segments; ++s) {
        float u = static_cast<float>(s) / static_cast<float>(segments);
        float theta = u * 2.0f * pi;
        float cos_theta = std::cos(theta);
        float sin_theta = std::sin(theta);

        glm::vec3 normal(cos_theta, 0.0f, sin_theta);
        glm::vec3 pos_top(radius * cos_theta,  half_h, radius * sin_theta);
        glm::vec3 pos_bot(radius * cos_theta, -half_h, radius * sin_theta);
        glm::vec4 tangent(-sin_theta, 0.0f, cos_theta, 1.0f);

        mesh->cpu_vertices.push_back({ pos_top, normal, { u, 1.0f }, glm::vec4(1.0f), tangent });
        mesh->cpu_vertices.push_back({ pos_bot, normal, { u, 0.0f }, glm::vec4(1.0f), tangent });
    }

    // Side indices
    for (int s = 0; s < segments; ++s) {
        uint16_t tl = static_cast<uint16_t>(s * 2);
        uint16_t bl = static_cast<uint16_t>(tl + 1);
        uint16_t tr = static_cast<uint16_t>((s + 1) * 2);
        uint16_t br = static_cast<uint16_t>(tr + 1);

        // Triangle 1: TL -> TR -> BL
        mesh->cpu_indices.push_back(tl);
        mesh->cpu_indices.push_back(tr);
        mesh->cpu_indices.push_back(bl);

        // Triangle 2: TR -> BR -> BL
        mesh->cpu_indices.push_back(tr);
        mesh->cpu_indices.push_back(br);
        mesh->cpu_indices.push_back(bl);
    }

    if (capped) {
        // Top Cap (+Y)
        uint16_t top_center_idx = static_cast<uint16_t>(mesh->cpu_vertices.size());
        mesh->cpu_vertices.push_back({ { 0.0f, half_h, 0.0f }, { 0.0f, 1.0f, 0.0f }, { 0.5f, 0.5f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } });

        uint16_t top_ring_start = static_cast<uint16_t>(mesh->cpu_vertices.size());
        for (int s = 0; s <= segments; ++s) {
            float u = static_cast<float>(s) / static_cast<float>(segments);
            float theta = u * 2.0f * pi;
            float cos_theta = std::cos(theta);
            float sin_theta = std::sin(theta);
            glm::vec3 pos(radius * cos_theta, half_h, radius * sin_theta);
            glm::vec2 uv(0.5f + 0.5f * cos_theta, 0.5f + 0.5f * sin_theta);
            mesh->cpu_vertices.push_back({ pos, { 0.0f, 1.0f, 0.0f }, uv, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } });
        }

        for (int s = 0; s < segments; ++s) {
            uint16_t v0 = static_cast<uint16_t>(top_ring_start + s);
            uint16_t v1 = static_cast<uint16_t>(top_ring_start + s + 1);
            // CCW looking from +Y: Center -> v1 -> v0
            mesh->cpu_indices.push_back(top_center_idx);
            mesh->cpu_indices.push_back(v1);
            mesh->cpu_indices.push_back(v0);
        }

        // Bottom Cap (-Y)
        uint16_t bot_center_idx = static_cast<uint16_t>(mesh->cpu_vertices.size());
        mesh->cpu_vertices.push_back({ { 0.0f, -half_h, 0.0f }, { 0.0f, -1.0f, 0.0f }, { 0.5f, 0.5f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } });

        uint16_t bot_ring_start = static_cast<uint16_t>(mesh->cpu_vertices.size());
        for (int s = 0; s <= segments; ++s) {
            float u = static_cast<float>(s) / static_cast<float>(segments);
            float theta = u * 2.0f * pi;
            float cos_theta = std::cos(theta);
            float sin_theta = std::sin(theta);
            glm::vec3 pos(radius * cos_theta, -half_h, radius * sin_theta);
            glm::vec2 uv(0.5f + 0.5f * cos_theta, 0.5f - 0.5f * sin_theta);
            mesh->cpu_vertices.push_back({ pos, { 0.0f, -1.0f, 0.0f }, uv, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } });
        }

        for (int s = 0; s < segments; ++s) {
            uint16_t v0 = static_cast<uint16_t>(bot_ring_start + s);
            uint16_t v1 = static_cast<uint16_t>(bot_ring_start + s + 1);
            // CCW looking from -Y: Center -> v0 -> v1
            mesh->cpu_indices.push_back(bot_center_idx);
            mesh->cpu_indices.push_back(v0);
            mesh->cpu_indices.push_back(v1);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_plane(float width, float depth, int subdivisions_x, int subdivisions_z) {
    auto mesh = std::make_shared<Mesh>();
    if (subdivisions_x < 1) subdivisions_x = 1;
    if (subdivisions_z < 1) subdivisions_z = 1;

    float hw = width * 0.5f;
    float hd = depth * 0.5f;
    float dx = width / static_cast<float>(subdivisions_x);
    float dz = depth / static_cast<float>(subdivisions_z);

    mesh->cpu_vertices.reserve((subdivisions_x + 1) * (subdivisions_z + 1));
    mesh->cpu_indices.reserve(subdivisions_x * subdivisions_z * 6);

    for (int iz = 0; iz <= subdivisions_z; ++iz) {
        float z = -hd + iz * dz;
        float v = static_cast<float>(iz) / static_cast<float>(subdivisions_z);

        for (int ix = 0; ix <= subdivisions_x; ++ix) {
            float x = -hw + ix * dx;
            float u = static_cast<float>(ix) / static_cast<float>(subdivisions_x);

            mesh->cpu_vertices.push_back({
                { x, 0.0f, z },
                { 0.0f, 1.0f, 0.0f },
                { u, v },
                { 1.0f, 1.0f, 1.0f, 1.0f },
                { 1.0f, 0.0f, 0.0f, 1.0f }
            });
        }
    }

    for (int iz = 0; iz < subdivisions_z; ++iz) {
        for (int ix = 0; ix < subdivisions_x; ++ix) {
            uint16_t i0 = static_cast<uint16_t>(iz * (subdivisions_x + 1) + ix);
            uint16_t i1 = static_cast<uint16_t>(i0 + 1);
            uint16_t i2 = static_cast<uint16_t>((iz + 1) * (subdivisions_x + 1) + ix);
            uint16_t i3 = static_cast<uint16_t>(i2 + 1);

            // Triangle 1: i0 -> i2 -> i1
            mesh->cpu_indices.push_back(i0);
            mesh->cpu_indices.push_back(i2);
            mesh->cpu_indices.push_back(i1);

            // Triangle 2: i1 -> i2 -> i3
            mesh->cpu_indices.push_back(i1);
            mesh->cpu_indices.push_back(i2);
            mesh->cpu_indices.push_back(i3);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_custom(
    const float* vertex_data, size_t vertex_count,
    const uint16_t* index_data, size_t index_count,
    size_t stride_bytes
) {
    auto mesh = std::make_shared<Mesh>();
    if (!vertex_data || vertex_count == 0 || !index_data || index_count == 0) {
        return mesh;
    }

    if (stride_bytes == 0 || stride_bytes == sizeof(Vertex)) {
        mesh->cpu_vertices.resize(vertex_count);
        std::memcpy(mesh->cpu_vertices.data(), vertex_data, vertex_count * sizeof(Vertex));
    } else {
        mesh->cpu_vertices.reserve(vertex_count);
        const uint8_t* ptr = reinterpret_cast<const uint8_t*>(vertex_data);
        for (size_t i = 0; i < vertex_count; ++i) {
            const float* vf = reinterpret_cast<const float*>(ptr + i * stride_bytes);
            Vertex v{};
            v.position = glm::vec3(vf[0], vf[1], vf[2]);
            if (stride_bytes >= 6 * sizeof(float)) {
                v.normal = glm::vec3(vf[3], vf[4], vf[5]);
            } else {
                v.normal = glm::vec3(0.0f, 1.0f, 0.0f);
            }
            if (stride_bytes >= 8 * sizeof(float)) {
                v.uv = glm::vec2(vf[6], vf[7]);
            } else {
                v.uv = glm::vec2(0.0f, 0.0f);
            }
            if (stride_bytes >= 12 * sizeof(float)) {
                v.color = glm::vec4(vf[8], vf[9], vf[10], vf[11]);
            } else {
                v.color = glm::vec4(1.0f);
            }
            if (stride_bytes >= 16 * sizeof(float)) {
                v.tangent = glm::vec4(vf[12], vf[13], vf[14], vf[15]);
            } else {
                v.tangent = glm::vec4(1.0f, 0.0f, 0.0f, 1.0f);
            }
            mesh->cpu_vertices.push_back(v);
        }
    }

    mesh->cpu_indices.assign(index_data, index_data + index_count);
    mesh->num_indices = static_cast<int>(index_count);
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_capsule(float radius, float length, int cap_segments, int radial_segments) {
    auto mesh = std::make_shared<Mesh>();
    if (cap_segments < 2) cap_segments = 2;
    if (radial_segments < 3) radial_segments = 3;
    if (length < 0.0f) length = 0.0f;

    const float pi = 3.14159265358979323846f;
    float half_len = length * 0.5f;
    int total_rings = cap_segments * 2 + 2;
    mesh->cpu_vertices.reserve(total_rings * (radial_segments + 1));

    for (int r = 0; r < total_rings; ++r) {
        float phi, y_center;
        if (r <= cap_segments) {
            float t = static_cast<float>(r) / static_cast<float>(cap_segments);
            phi = t * (pi * 0.5f);
            y_center = half_len;
        } else {
            float t = static_cast<float>(r - (cap_segments + 1)) / static_cast<float>(cap_segments);
            phi = (pi * 0.5f) + t * (pi * 0.5f);
            y_center = -half_len;
        }

        float cos_phi = std::cos(phi);
        float sin_phi = std::sin(phi);
        float y = y_center + radius * cos_phi;
        float ring_r = radius * sin_phi;
        float v = 1.0f - static_cast<float>(r) / static_cast<float>(total_rings - 1);

        for (int s = 0; s <= radial_segments; ++s) {
            float u = static_cast<float>(s) / static_cast<float>(radial_segments);
            float theta = u * 2.0f * pi;
            float cos_theta = std::cos(theta);
            float sin_theta = std::sin(theta);

            glm::vec3 normal(sin_phi * cos_theta, cos_phi, sin_phi * sin_theta);
            glm::vec3 pos(ring_r * cos_theta, y, ring_r * sin_theta);
            glm::vec4 tangent(-sin_theta, 0.0f, cos_theta, 1.0f);

            mesh->cpu_vertices.push_back({ pos, normal, { u, v }, glm::vec4(1.0f), tangent });
        }
    }

    for (int r = 0; r < total_rings - 1; ++r) {
        for (int s = 0; s < radial_segments; ++s) {
            uint16_t i0 = static_cast<uint16_t>(r * (radial_segments + 1) + s);
            uint16_t i1 = static_cast<uint16_t>(i0 + 1);
            uint16_t i2 = static_cast<uint16_t>((r + 1) * (radial_segments + 1) + s);
            uint16_t i3 = static_cast<uint16_t>(i2 + 1);

            mesh->cpu_indices.push_back(i0);
            mesh->cpu_indices.push_back(i1);
            mesh->cpu_indices.push_back(i2);

            mesh->cpu_indices.push_back(i1);
            mesh->cpu_indices.push_back(i3);
            mesh->cpu_indices.push_back(i2);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_cone(float radius, float height, int radial_segments, bool open_ended) {
    auto mesh = std::make_shared<Mesh>();
    if (radial_segments < 3) radial_segments = 3;
    float half_h = height * 0.5f;
    const float pi = 3.14159265358979323846f;
    float slant_len = std::sqrt(radius * radius + height * height);
    float normal_y = radius / slant_len;
    float normal_r = height / slant_len;

    for (int s = 0; s <= radial_segments; ++s) {
        float u = static_cast<float>(s) / static_cast<float>(radial_segments);
        float theta = u * 2.0f * pi;
        float cos_t = std::cos(theta);
        float sin_t = std::sin(theta);

        glm::vec3 n(normal_r * cos_t, normal_y, normal_r * sin_t);
        glm::vec4 tan(-sin_t, 0.0f, cos_t, 1.0f);

        mesh->cpu_vertices.push_back({ { 0.0f, half_h, 0.0f }, n, { u, 1.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ { radius * cos_t, -half_h, radius * sin_t }, n, { u, 0.0f }, glm::vec4(1.0f), tan });
    }

    for (int s = 0; s < radial_segments; ++s) {
        uint16_t top_curr = static_cast<uint16_t>(s * 2);
        uint16_t bot_curr = static_cast<uint16_t>(top_curr + 1);
        uint16_t bot_next = static_cast<uint16_t>((s + 1) * 2 + 1);

        mesh->cpu_indices.push_back(top_curr);
        mesh->cpu_indices.push_back(bot_curr);
        mesh->cpu_indices.push_back(bot_next);
    }

    if (!open_ended) {
        uint16_t center_idx = static_cast<uint16_t>(mesh->cpu_vertices.size());
        mesh->cpu_vertices.push_back({ { 0.0f, -half_h, 0.0f }, { 0.0f, -1.0f, 0.0f }, { 0.5f, 0.5f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } });

        uint16_t ring_start = static_cast<uint16_t>(mesh->cpu_vertices.size());
        for (int s = 0; s <= radial_segments; ++s) {
            float u = static_cast<float>(s) / static_cast<float>(radial_segments);
            float theta = u * 2.0f * pi;
            float cos_t = std::cos(theta);
            float sin_t = std::sin(theta);
            glm::vec3 pos(radius * cos_t, -half_h, radius * sin_t);
            glm::vec2 uv(0.5f + 0.5f * cos_t, 0.5f - 0.5f * sin_t);
            mesh->cpu_vertices.push_back({ pos, { 0.0f, -1.0f, 0.0f }, uv, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } });
        }

        for (int s = 0; s < radial_segments; ++s) {
            uint16_t v0 = static_cast<uint16_t>(ring_start + s);
            uint16_t v1 = static_cast<uint16_t>(ring_start + s + 1);
            mesh->cpu_indices.push_back(center_idx);
            mesh->cpu_indices.push_back(v0);
            mesh->cpu_indices.push_back(v1);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_torus(float radius, float tube, int radial_segments, int tubular_segments) {
    auto mesh = std::make_shared<Mesh>();
    if (radial_segments < 3) radial_segments = 3;
    if (tubular_segments < 3) tubular_segments = 3;

    const float pi = 3.14159265358979323846f;
    mesh->cpu_vertices.reserve((tubular_segments + 1) * (radial_segments + 1));

    for (int j = 0; j <= radial_segments; ++j) {
        float v = static_cast<float>(j) / static_cast<float>(radial_segments);
        float phi = v * 2.0f * pi;
        float cos_phi = std::cos(phi);
        float sin_phi = std::sin(phi);

        for (int i = 0; i <= tubular_segments; ++i) {
            float u = static_cast<float>(i) / static_cast<float>(tubular_segments);
            float theta = u * 2.0f * pi;
            float cos_theta = std::cos(theta);
            float sin_theta = std::sin(theta);

            glm::vec3 pos(
                (radius + tube * cos_phi) * cos_theta,
                tube * sin_phi,
                (radius + tube * cos_phi) * sin_theta
            );

            glm::vec3 center(radius * cos_theta, 0.0f, radius * sin_theta);
            glm::vec3 normal = glm::normalize(pos - center);
            glm::vec4 tangent(-sin_theta, 0.0f, cos_theta, 1.0f);
            glm::vec2 uv(u, v);

            mesh->cpu_vertices.push_back({ pos, normal, uv, glm::vec4(1.0f), tangent });
        }
    }

    for (int j = 0; j < radial_segments; ++j) {
        for (int i = 0; i < tubular_segments; ++i) {
            uint16_t a = static_cast<uint16_t>((tubular_segments + 1) * j + i);
            uint16_t b = static_cast<uint16_t>((tubular_segments + 1) * (j + 1) + i);
            uint16_t c = static_cast<uint16_t>((tubular_segments + 1) * (j + 1) + i + 1);
            uint16_t d = static_cast<uint16_t>((tubular_segments + 1) * j + i + 1);

            mesh->cpu_indices.push_back(a);
            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(d);

            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(c);
            mesh->cpu_indices.push_back(d);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_torus_knot(float radius, float tube, int tubular_segments, int radial_segments, int p, int q) {
    auto mesh = std::make_shared<Mesh>();
    if (tubular_segments < 3) tubular_segments = 3;
    if (radial_segments < 3) radial_segments = 3;

    const float pi = 3.14159265358979323846f;

    auto calculate_pos_on_curve = [&](float u, glm::vec3& pos) {
        float cu = std::cos(u);
        float su = std::sin(u);
        float quOverP = u * static_cast<float>(q) / static_cast<float>(p);
        float cs = std::cos(quOverP);
        pos.x = radius * (2.0f + cs) * 0.5f * cu;
        pos.y = radius * (2.0f + cs) * 0.5f * su;
        pos.z = radius * std::sin(quOverP) * 0.5f;
    };

    mesh->cpu_vertices.reserve((tubular_segments + 1) * (radial_segments + 1));

    for (int i = 0; i <= tubular_segments; ++i) {
        float u = static_cast<float>(i) / static_cast<float>(tubular_segments) * static_cast<float>(p) * 2.0f * pi;
        glm::vec3 p1, p2;
        calculate_pos_on_curve(u, p1);
        calculate_pos_on_curve(u + 0.01f, p2);

        glm::vec3 T = glm::normalize(p2 - p1);
        glm::vec3 N = glm::normalize(p1 + p2);
        if (glm::length(N) < 0.001f || std::abs(glm::dot(T, N)) > 0.99f) {
            N = glm::normalize(glm::cross(T, glm::vec3(0.0f, 0.0f, 1.0f)));
        }
        glm::vec3 B = glm::normalize(glm::cross(T, N));
        N = glm::normalize(glm::cross(B, T));

        for (int j = 0; j <= radial_segments; ++j) {
            float v = static_cast<float>(j) / static_cast<float>(radial_segments) * 2.0f * pi;
            float cx = -tube * std::cos(v);
            float cy = tube * std::sin(v);

            glm::vec3 pos = p1 + cx * N + cy * B;
            glm::vec3 normal = glm::normalize(pos - p1);
            glm::vec4 tangent(T, 1.0f);
            glm::vec2 uv(static_cast<float>(i) / tubular_segments, static_cast<float>(j) / radial_segments);

            mesh->cpu_vertices.push_back({ pos, normal, uv, glm::vec4(1.0f), tangent });
        }
    }

    for (int i = 0; i < tubular_segments; ++i) {
        for (int j = 0; j < radial_segments; ++j) {
            uint16_t a = static_cast<uint16_t>((radial_segments + 1) * i + j);
            uint16_t b = static_cast<uint16_t>((radial_segments + 1) * (i + 1) + j);
            uint16_t c = static_cast<uint16_t>((radial_segments + 1) * (i + 1) + j + 1);
            uint16_t d = static_cast<uint16_t>((radial_segments + 1) * i + j + 1);

            mesh->cpu_indices.push_back(a);
            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(d);

            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(c);
            mesh->cpu_indices.push_back(d);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_circle(float radius, int segments) {
    auto mesh = std::make_shared<Mesh>();
    if (segments < 3) segments = 3;
    const float pi = 3.14159265358979323846f;

    mesh->cpu_vertices.push_back({ { 0.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f }, { 0.5f, 0.5f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } });

    for (int s = 0; s <= segments; ++s) {
        float u = static_cast<float>(s) / static_cast<float>(segments);
        float theta = u * 2.0f * pi;
        float cos_t = std::cos(theta);
        float sin_t = std::sin(theta);
        glm::vec3 pos(radius * cos_t, 0.0f, radius * sin_t);
        glm::vec2 uv(0.5f + 0.5f * cos_t, 0.5f - 0.5f * sin_t);
        glm::vec4 tan(-sin_t, 0.0f, cos_t, 1.0f);
        mesh->cpu_vertices.push_back({ pos, { 0.0f, 1.0f, 0.0f }, uv, glm::vec4(1.0f), tan });
    }

    for (int s = 1; s <= segments; ++s) {
        mesh->cpu_indices.push_back(0);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(s));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(s + 1));
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_ring(float inner_radius, float outer_radius, int segments) {
    auto mesh = std::make_shared<Mesh>();
    if (segments < 3) segments = 3;
    const float pi = 3.14159265358979323846f;

    for (int s = 0; s <= segments; ++s) {
        float u = static_cast<float>(s) / static_cast<float>(segments);
        float theta = u * 2.0f * pi;
        float cos_t = std::cos(theta);
        float sin_t = std::sin(theta);
        glm::vec4 tan(-sin_t, 0.0f, cos_t, 1.0f);

        glm::vec3 pos_in(inner_radius * cos_t, 0.0f, inner_radius * sin_t);
        glm::vec2 uv_in(0.5f + 0.5f * (inner_radius / outer_radius) * cos_t, 0.5f + 0.5f * (inner_radius / outer_radius) * sin_t);
        mesh->cpu_vertices.push_back({ pos_in, { 0.0f, 1.0f, 0.0f }, uv_in, glm::vec4(1.0f), tan });

        glm::vec3 pos_out(outer_radius * cos_t, 0.0f, outer_radius * sin_t);
        glm::vec2 uv_out(0.5f + 0.5f * cos_t, 0.5f + 0.5f * sin_t);
        mesh->cpu_vertices.push_back({ pos_out, { 0.0f, 1.0f, 0.0f }, uv_out, glm::vec4(1.0f), tan });
    }

    for (int s = 0; s < segments; ++s) {
        uint16_t in0 = static_cast<uint16_t>(s * 2);
        uint16_t out0 = static_cast<uint16_t>(in0 + 1);
        uint16_t in1 = static_cast<uint16_t>((s + 1) * 2);
        uint16_t out1 = static_cast<uint16_t>(in1 + 1);

        mesh->cpu_indices.push_back(in0);
        mesh->cpu_indices.push_back(in1);
        mesh->cpu_indices.push_back(out0);

        mesh->cpu_indices.push_back(out0);
        mesh->cpu_indices.push_back(in1);
        mesh->cpu_indices.push_back(out1);
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_tetrahedron(float radius) {
    auto mesh = std::make_shared<Mesh>();
    std::vector<glm::vec3> verts = {
        glm::normalize(glm::vec3( 1.0f,  1.0f,  1.0f)) * radius,
        glm::normalize(glm::vec3(-1.0f, -1.0f,  1.0f)) * radius,
        glm::normalize(glm::vec3(-1.0f,  1.0f, -1.0f)) * radius,
        glm::normalize(glm::vec3( 1.0f, -1.0f, -1.0f)) * radius
    };

    uint16_t faces[4][3] = {
        { 0, 2, 1 },
        { 0, 1, 3 },
        { 0, 3, 2 },
        { 1, 2, 3 }
    };

    for (int f = 0; f < 4; ++f) {
        glm::vec3 p0 = verts[faces[f][0]];
        glm::vec3 p1 = verts[faces[f][1]];
        glm::vec3 p2 = verts[faces[f][2]];
        glm::vec3 normal = glm::normalize(glm::cross(p1 - p0, p2 - p0));
        glm::vec3 up = (std::abs(normal.y) > 0.9f) ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
        glm::vec4 tan(glm::normalize(glm::cross(up, normal)), 1.0f);

        uint16_t base = static_cast<uint16_t>(mesh->cpu_vertices.size());
        mesh->cpu_vertices.push_back({ p0, normal, { 0.5f, 1.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ p1, normal, { 0.0f, 0.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ p2, normal, { 1.0f, 0.0f }, glm::vec4(1.0f), tan });

        mesh->cpu_indices.push_back(base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 1));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 2));
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_octahedron(float radius) {
    auto mesh = std::make_shared<Mesh>();
    std::vector<glm::vec3> verts = {
        {  radius, 0.0f, 0.0f },
        { -radius, 0.0f, 0.0f },
        { 0.0f,  radius, 0.0f },
        { 0.0f, -radius, 0.0f },
        { 0.0f, 0.0f,  radius },
        { 0.0f, 0.0f, -radius }
    };

    uint16_t faces[8][3] = {
        { 0, 2, 4 }, { 2, 1, 4 }, { 1, 3, 4 }, { 3, 0, 4 },
        { 2, 0, 5 }, { 1, 2, 5 }, { 3, 1, 5 }, { 0, 3, 5 }
    };

    for (int f = 0; f < 8; ++f) {
        glm::vec3 p0 = verts[faces[f][0]];
        glm::vec3 p1 = verts[faces[f][1]];
        glm::vec3 p2 = verts[faces[f][2]];
        glm::vec3 normal = glm::normalize(glm::cross(p1 - p0, p2 - p0));
        glm::vec3 up = (std::abs(normal.y) > 0.9f) ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
        glm::vec4 tan(glm::normalize(glm::cross(up, normal)), 1.0f);

        uint16_t base = static_cast<uint16_t>(mesh->cpu_vertices.size());
        mesh->cpu_vertices.push_back({ p0, normal, { 0.5f, 1.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ p1, normal, { 0.0f, 0.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ p2, normal, { 1.0f, 0.0f }, glm::vec4(1.0f), tan });

        mesh->cpu_indices.push_back(base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 1));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 2));
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_icosahedron(float radius, int subdivisions) {
    auto mesh = std::make_shared<Mesh>();
    float t = (1.0f + std::sqrt(5.0f)) * 0.5f;

    std::vector<glm::vec3> initial_verts = {
        glm::normalize(glm::vec3(-1.0f,  t, 0.0f)),
        glm::normalize(glm::vec3( 1.0f,  t, 0.0f)),
        glm::normalize(glm::vec3(-1.0f, -t, 0.0f)),
        glm::normalize(glm::vec3( 1.0f, -t, 0.0f)),
        glm::normalize(glm::vec3(0.0f, -1.0f,  t)),
        glm::normalize(glm::vec3(0.0f,  1.0f,  t)),
        glm::normalize(glm::vec3(0.0f, -1.0f, -t)),
        glm::normalize(glm::vec3(0.0f,  1.0f, -t)),
        glm::normalize(glm::vec3( t, 0.0f, -1.0f)),
        glm::normalize(glm::vec3( t, 0.0f,  1.0f)),
        glm::normalize(glm::vec3(-t, 0.0f, -1.0f)),
        glm::normalize(glm::vec3(-t, 0.0f,  1.0f))
    };

    struct Tri { glm::vec3 a, b, c; };
    std::vector<Tri> tris;
    uint16_t initial_faces[20][3] = {
        { 0, 11, 5 }, { 0, 5, 1 }, { 0, 1, 7 }, { 0, 7, 10 }, { 0, 10, 11 },
        { 1, 5, 9 }, { 5, 11, 4 }, { 11, 10, 2 }, { 10, 7, 6 }, { 7, 1, 8 },
        { 3, 9, 4 }, { 3, 4, 2 }, { 3, 2, 6 }, { 3, 6, 8 }, { 3, 8, 9 },
        { 4, 9, 5 }, { 2, 4, 11 }, { 6, 2, 10 }, { 8, 6, 7 }, { 9, 8, 1 }
    };
    for (int i = 0; i < 20; ++i) {
        tris.push_back({ initial_verts[initial_faces[i][0]], initial_verts[initial_faces[i][1]], initial_verts[initial_faces[i][2]] });
    }

    for (int s = 0; s < subdivisions; ++s) {
        std::vector<Tri> next_tris;
        next_tris.reserve(tris.size() * 4);
        for (const auto& tri : tris) {
            glm::vec3 m01 = glm::normalize(tri.a + tri.b);
            glm::vec3 m12 = glm::normalize(tri.b + tri.c);
            glm::vec3 m20 = glm::normalize(tri.c + tri.a);

            next_tris.push_back({ tri.a, m01, m20 });
            next_tris.push_back({ tri.b, m12, m01 });
            next_tris.push_back({ tri.c, m20, m12 });
            next_tris.push_back({ m01, m12, m20 });
        }
        tris = std::move(next_tris);
    }

    const float pi = 3.14159265358979323846f;
    for (const auto& tri : tris) {
        glm::vec3 pts[3] = { tri.a, tri.b, tri.c };
        uint16_t base = static_cast<uint16_t>(mesh->cpu_vertices.size());
        for (int i = 0; i < 3; ++i) {
            glm::vec3 n = pts[i];
            glm::vec3 pos = n * radius;
            float u = std::atan2(n.z, n.x) / (2.0f * pi) + 0.5f;
            float v = std::asin(std::clamp(n.y, -1.0f, 1.0f)) / pi + 0.5f;
            glm::vec4 tan(-n.z, 0.0f, n.x, 1.0f);
            if (glm::length(glm::vec2(n.x, n.z)) > 1e-4f) {
                tan = glm::vec4(glm::normalize(glm::vec3(-n.z, 0.0f, n.x)), 1.0f);
            } else {
                tan = glm::vec4(1.0f, 0.0f, 0.0f, 1.0f);
            }
            mesh->cpu_vertices.push_back({ pos, n, { u, v }, glm::vec4(1.0f), tan });
        }
        mesh->cpu_indices.push_back(base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 1));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 2));
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_dodecahedron(float radius) {
    auto mesh = std::make_shared<Mesh>();
    float phi = (1.0f + std::sqrt(5.0f)) * 0.5f;
    float inv_phi = 1.0f / phi;

    std::vector<glm::vec3> verts = {
        {-1,-1,-1}, {-1,-1, 1}, {-1, 1,-1}, {-1, 1, 1},
        { 1,-1,-1}, { 1,-1, 1}, { 1, 1,-1}, { 1, 1, 1},
        {0, -inv_phi, -phi}, {0, -inv_phi, phi}, {0, inv_phi, -phi}, {0, inv_phi, phi},
        {-inv_phi, -phi, 0}, {-inv_phi, phi, 0}, {inv_phi, -phi, 0}, {inv_phi, phi, 0},
        {-phi, 0, -inv_phi}, {-phi, 0, inv_phi}, {phi, 0, -inv_phi}, {phi, 0, inv_phi}
    };
    for (auto& v : verts) {
        v = glm::normalize(v) * radius;
    }

    uint16_t pentagons[12][5] = {
        { 3, 11,  7, 15, 13 },
        { 7, 19, 18,  6, 15 },
        { 7, 11,  9,  5, 19 },
        { 8, 10,  6, 18,  4 },
        { 10, 2, 13, 15,  6 },
        { 2, 16, 17,  3, 13 },
        { 3, 17,  1,  9, 11 },
        { 4, 18, 19,  5, 14 },
        { 2, 10,  8,  0, 16 },
        { 1, 12, 14,  5,  9 },
        { 0,  8,  4, 14, 12 },
        { 0, 12,  1, 17, 16 }
    };

    for (int p = 0; p < 12; ++p) {
        glm::vec3 p0 = verts[pentagons[p][0]];
        glm::vec3 p1 = verts[pentagons[p][1]];
        glm::vec3 p2 = verts[pentagons[p][2]];
        glm::vec3 normal = glm::normalize(glm::cross(p1 - p0, p2 - p0));
        glm::vec3 up = (std::abs(normal.y) > 0.9f) ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
        glm::vec4 tan(glm::normalize(glm::cross(up, normal)), 1.0f);

        uint16_t base = static_cast<uint16_t>(mesh->cpu_vertices.size());
        for (int k = 0; k < 5; ++k) {
            mesh->cpu_vertices.push_back({ verts[pentagons[p][k]], normal, { 0.5f, 0.5f }, glm::vec4(1.0f), tan });
        }
        mesh->cpu_indices.push_back(base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 1));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 2));

        mesh->cpu_indices.push_back(base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 2));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 3));

        mesh->cpu_indices.push_back(base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 3));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(base + 4));
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> Mesh::create_tube(const Curve3& curve, int tubular_segments, float radius, int radial_segments, bool closed) {
    return engine::create_tube(curve, tubular_segments, radius, radial_segments, closed);
}

std::shared_ptr<Mesh> Mesh::create_lathe(const std::vector<glm::vec2>& points, int segments, float phi_start, float phi_length) {
    return engine::create_lathe(points, segments, phi_start, phi_length);
}

std::shared_ptr<Mesh> Mesh::create_extrude(const std::vector<glm::vec2>& polygon, float depth, float bevel_thickness) {
    return engine::create_extrude(polygon, depth, bevel_thickness);
}

// ---------------------------------------------------------------------------
// InstancedMesh Implementation
// ---------------------------------------------------------------------------
InstancedMesh::InstancedMesh(std::shared_ptr<Mesh> base_mesh, size_t initial_count)
    : Node3D("InstancedMesh"), mesh(std::move(base_mesh)) {
    if (initial_count > 0) {
        instances.resize(initial_count);
    }
}

InstancedMesh::~InstancedMesh() {
    destroy();
}

void InstancedMesh::destroy() {
    if (inst_vbuf_id != 0) {
        if (sg_isvalid()) {
            sg_destroy_buffer(sg_buffer{ inst_vbuf_id });
        }
        inst_vbuf_id = 0;
    }
}

void InstancedMesh::set_instance_count(size_t count) {
    instances.resize(count);
}

void InstancedMesh::update_instances(const InstanceData* data, size_t count) {
    if (!data || count == 0) return;
    instances.assign(data, data + count);
    if (inst_vbuf_id != 0 && sg_isvalid()) {
        sg_range range{ instances.data(), instances.size() * sizeof(InstanceData) };
        sg_update_buffer(sg_buffer{ inst_vbuf_id }, &range);
    }
}

void InstancedMesh::set_instance(size_t index, const glm::mat4& matrix, const glm::vec4& color) {
    if (index >= instances.size()) {
        instances.resize(index + 1);
    }
    instances[index].model_matrix = matrix;
    instances[index].color = color;
    if (inst_vbuf_id != 0 && sg_isvalid()) {
        sg_range range{ instances.data(), instances.size() * sizeof(InstanceData) };
        sg_update_buffer(sg_buffer{ inst_vbuf_id }, &range);
    }
}

bool InstancedMesh::ensure_gpu_buffers() {
    if (!mesh || !mesh->ensure_gpu_buffers()) {
        return false;
    }
    if (instances.empty()) {
        return true;
    }
    if (!sg_isvalid()) {
        return false;
    }

    if (inst_vbuf_id == 0) {
        sg_buffer_desc desc{};
        desc.size = instances.size() * sizeof(InstanceData);
        desc.usage.vertex_buffer = true;
        desc.usage.dynamic_update = true;
        desc.data = { instances.data(), instances.size() * sizeof(InstanceData) };
        desc.label = "instanced-mesh-vbuf";
        sg_buffer buf = sg_make_buffer(&desc);
        inst_vbuf_id = buf.id;
    } else {
        sg_range range{ instances.data(), instances.size() * sizeof(InstanceData) };
        sg_update_buffer(sg_buffer{ inst_vbuf_id }, &range);
    }
    return inst_vbuf_id != 0;
}

} // namespace engine
