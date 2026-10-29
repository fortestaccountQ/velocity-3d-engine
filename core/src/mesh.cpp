#include "engine/mesh.hpp"

#include "sokol_gfx.h"
#include <cmath>

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

std::shared_ptr<Mesh> Mesh::create_box(float width, float height, float depth) {
    auto mesh = std::make_shared<Mesh>();
    float hw = width * 0.5f;
    float hh = height * 0.5f;
    float hd = depth * 0.5f;

    // 24 vertices for 6 faces with proper position, normal, UV coordinates and base tint
    mesh->cpu_vertices = {
        // Front face (Z = +hd, normal: 0, 0, +1)
        { { -hw, -hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw, -hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw,  hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw,  hh,  hd }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Back face (Z = -hd, normal: 0, 0, -1)
        { {  hw, -hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw, -hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw,  hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw,  hh, -hd }, { 0.0f, 0.0f, -1.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Left face (X = -hw, normal: -1, 0, 0)
        { { -hw, -hh, -hd }, { -1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw, -hh,  hd }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw,  hh,  hd }, { -1.0f, 0.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw,  hh, -hd }, { -1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Right face (X = +hw, normal: +1, 0, 0)
        { {  hw, -hh,  hd }, { 1.0f, 0.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw, -hh, -hd }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw,  hh, -hd }, { 1.0f, 0.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw,  hh,  hd }, { 1.0f, 0.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Top face (Y = +hh, normal: 0, +1, 0)
        { { -hw,  hh,  hd }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw,  hh,  hd }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw,  hh, -hd }, { 0.0f, 1.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw,  hh, -hd }, { 0.0f, 1.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },

        // Bottom face (Y = -hh, normal: 0, -1, 0)
        { { -hw, -hh, -hd }, { 0.0f, -1.0f, 0.0f }, { 0.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw, -hh, -hd }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 1.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { {  hw, -hh,  hd }, { 0.0f, -1.0f, 0.0f }, { 1.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
        { { -hw, -hh,  hd }, { 0.0f, -1.0f, 0.0f }, { 0.0f, 0.0f }, { 1.0f, 1.0f, 1.0f, 1.0f } },
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

            mesh->cpu_vertices.push_back({ position, normal, uv, glm::vec4(1.0f) });
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

        mesh->cpu_vertices.push_back({ pos_top, normal, { u, 1.0f }, glm::vec4(1.0f) });
        mesh->cpu_vertices.push_back({ pos_bot, normal, { u, 0.0f }, glm::vec4(1.0f) });
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
        mesh->cpu_vertices.push_back({ { 0.0f, half_h, 0.0f }, { 0.0f, 1.0f, 0.0f }, { 0.5f, 0.5f }, glm::vec4(1.0f) });

        uint16_t top_ring_start = static_cast<uint16_t>(mesh->cpu_vertices.size());
        for (int s = 0; s <= segments; ++s) {
            float u = static_cast<float>(s) / static_cast<float>(segments);
            float theta = u * 2.0f * pi;
            float cos_theta = std::cos(theta);
            float sin_theta = std::sin(theta);
            glm::vec3 pos(radius * cos_theta, half_h, radius * sin_theta);
            glm::vec2 uv(0.5f + 0.5f * cos_theta, 0.5f + 0.5f * sin_theta);
            mesh->cpu_vertices.push_back({ pos, { 0.0f, 1.0f, 0.0f }, uv, glm::vec4(1.0f) });
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
        mesh->cpu_vertices.push_back({ { 0.0f, -half_h, 0.0f }, { 0.0f, -1.0f, 0.0f }, { 0.5f, 0.5f }, glm::vec4(1.0f) });

        uint16_t bot_ring_start = static_cast<uint16_t>(mesh->cpu_vertices.size());
        for (int s = 0; s <= segments; ++s) {
            float u = static_cast<float>(s) / static_cast<float>(segments);
            float theta = u * 2.0f * pi;
            float cos_theta = std::cos(theta);
            float sin_theta = std::sin(theta);
            glm::vec3 pos(radius * cos_theta, -half_h, radius * sin_theta);
            glm::vec2 uv(0.5f + 0.5f * cos_theta, 0.5f - 0.5f * sin_theta);
            mesh->cpu_vertices.push_back({ pos, { 0.0f, -1.0f, 0.0f }, uv, glm::vec4(1.0f) });
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
                { 1.0f, 1.0f, 1.0f, 1.0f }
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
            mesh->cpu_vertices.push_back(v);
        }
    }

    mesh->cpu_indices.assign(index_data, index_data + index_count);
    mesh->num_indices = static_cast<int>(index_count);
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
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
