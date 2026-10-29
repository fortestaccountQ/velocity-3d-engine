#pragma once

#include <glm/glm.hpp>
#include <memory>
#include <cstdint>
#include <vector>
#include <cstring>

#include "engine/physics.hpp"
#include "engine/node3d.hpp"

namespace engine {

struct Vertex {
    glm::vec3 position{0.0f};
    glm::vec3 normal{0.0f, 1.0f, 0.0f};
    glm::vec2 uv{0.0f};
    glm::vec4 color{1.0f};
    glm::vec4 tangent{1.0f, 0.0f, 0.0f, 1.0f};
};

struct InstanceData {
    glm::mat4 model_matrix{1.0f};
    glm::vec4 color{1.0f};
};

class Mesh;

class IGeometryFactory {
public:
    virtual ~IGeometryFactory() = default;

    virtual std::shared_ptr<Mesh> create_box(float width, float height, float depth) = 0;
    virtual std::shared_ptr<Mesh> create_sphere(float radius, int rings = 32, int sectors = 32) = 0;
    virtual std::shared_ptr<Mesh> create_cylinder(float radius, float height, int segments = 32, bool capped = true) = 0;
    virtual std::shared_ptr<Mesh> create_plane(float width, float depth, int subdivisions_x = 1, int subdivisions_z = 1) = 0;
    virtual std::shared_ptr<Mesh> create_custom(
        const float* vertex_data, size_t vertex_count, size_t stride_bytes,
        const uint16_t* index_data, size_t index_count
    ) = 0;
};

class IInstancedMesh {
public:
    virtual ~IInstancedMesh() = default;
    virtual void set_instance_count(size_t count) = 0;
    virtual size_t instance_count() const = 0;
    virtual void update_instances(const InstanceData* data, size_t count) = 0;
    virtual void set_instance(size_t index, const glm::mat4& matrix, const glm::vec4& color) = 0;
};

class Mesh {
public:
    Mesh() = default;
    ~Mesh();

    uint32_t vbuf_id{0};
    uint32_t ibuf_id{0};
    int num_indices{0};
    bool is_dynamic{false};

    std::vector<Vertex> cpu_vertices;
    std::vector<uint16_t> cpu_indices;

    AABB local_aabb;

    void calculate_aabb() {
        if (cpu_vertices.empty()) {
            local_aabb = AABB{};
            return;
        }
        glm::vec3 min_p = cpu_vertices[0].position;
        glm::vec3 max_p = cpu_vertices[0].position;
        const size_t n = cpu_vertices.size();
        for (size_t i = 1; i < n; ++i) {
            const glm::vec3& p = cpu_vertices[i].position;
            min_p = glm::min(min_p, p);
            max_p = glm::max(max_p, p);
        }
        local_aabb = AABB{ min_p, max_p };
    }

    void mark_dynamic() { is_dynamic = true; }
    void update_vertices_raw(const float* raw_data, size_t num_floats);

    bool ensure_gpu_buffers();
    void destroy();

    // Procedural Primitives
    static std::shared_ptr<Mesh> create_box(float width, float height, float depth);
    static std::shared_ptr<Mesh> create_sphere(float radius, int rings = 32, int sectors = 32);
    static std::shared_ptr<Mesh> create_cylinder(float radius, float height, int segments = 32, bool capped = true);
    static std::shared_ptr<Mesh> create_plane(float width = 10.0f, float depth = 10.0f, int subdivisions_x = 1, int subdivisions_z = 1);
    static std::shared_ptr<Mesh> create_custom(
        const float* vertex_data, size_t vertex_count,
        const uint16_t* index_data, size_t index_count,
        size_t stride_bytes = 0
    );

    // Phase 5 Primitives
    static std::shared_ptr<Mesh> create_capsule(float radius = 0.5f, float length = 1.0f, int cap_segments = 8, int radial_segments = 16);
    static std::shared_ptr<Mesh> create_cone(float radius = 1.0f, float height = 2.0f, int radial_segments = 32, bool open_ended = false);
    static std::shared_ptr<Mesh> create_torus(float radius = 1.0f, float tube = 0.4f, int radial_segments = 16, int tubular_segments = 32);
    static std::shared_ptr<Mesh> create_torus_knot(float radius = 1.0f, float tube = 0.4f, int tubular_segments = 64, int radial_segments = 16, int p = 2, int q = 3);
    static std::shared_ptr<Mesh> create_circle(float radius = 1.0f, int segments = 32);
    static std::shared_ptr<Mesh> create_ring(float inner_radius = 0.5f, float outer_radius = 1.0f, int segments = 32);

    // Platonic solids
    static std::shared_ptr<Mesh> create_icosahedron(float radius = 1.0f, int subdivisions = 0);
    static std::shared_ptr<Mesh> create_octahedron(float radius = 1.0f);
    static std::shared_ptr<Mesh> create_tetrahedron(float radius = 1.0f);
    static std::shared_ptr<Mesh> create_dodecahedron(float radius = 1.0f);

    // Procedural Curves & Extrusions
    static std::shared_ptr<Mesh> create_tube(const class Curve3& curve, int tubular_segments = 64, float radius = 0.2f, int radial_segments = 8, bool closed = false);
    static std::shared_ptr<Mesh> create_lathe(const std::vector<glm::vec2>& points, int segments = 32, float phi_start = 0.0f, float phi_length = 6.283185307179586f);
    static std::shared_ptr<Mesh> create_extrude(const std::vector<glm::vec2>& polygon, float depth = 1.0f, float bevel_thickness = 0.0f);

    // Backward compatibility helper
    static std::shared_ptr<Mesh> create_cube();
};

class InstancedMesh : public Node3D, public IInstancedMesh {
public:
    InstancedMesh() : Node3D("InstancedMesh") {}
    explicit InstancedMesh(std::shared_ptr<Mesh> base_mesh, size_t initial_count = 0);
    ~InstancedMesh() override;

    std::shared_ptr<Mesh> mesh{nullptr};
    std::vector<InstanceData> instances;
    uint32_t inst_vbuf_id{0};

    void set_instance_count(size_t count) override;
    size_t instance_count() const override { return instances.size(); }
    void update_instances(const InstanceData* data, size_t count) override;
    void set_instance(size_t index, const glm::mat4& matrix, const glm::vec4& color) override;

    bool ensure_gpu_buffers();
    void destroy();
};

class GeometryFactory : public IGeometryFactory {
public:
    static GeometryFactory& instance() {
        static GeometryFactory s_inst;
        return s_inst;
    }

    std::shared_ptr<Mesh> create_box(float width, float height, float depth) override {
        return Mesh::create_box(width, height, depth);
    }
    std::shared_ptr<Mesh> create_sphere(float radius, int rings = 32, int sectors = 32) override {
        return Mesh::create_sphere(radius, rings, sectors);
    }
    std::shared_ptr<Mesh> create_cylinder(float radius, float height, int segments = 32, bool capped = true) override {
        return Mesh::create_cylinder(radius, height, segments, capped);
    }
    std::shared_ptr<Mesh> create_plane(float width, float depth, int subdivisions_x = 1, int subdivisions_z = 1) override {
        return Mesh::create_plane(width, depth, subdivisions_x, subdivisions_z);
    }
    std::shared_ptr<Mesh> create_custom(
        const float* vertex_data, size_t vertex_count, size_t stride_bytes,
        const uint16_t* index_data, size_t index_count
    ) override {
        return Mesh::create_custom(vertex_data, vertex_count, index_data, index_count, stride_bytes);
    }
};

} // namespace engine
