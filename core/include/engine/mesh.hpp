#pragma once

#include <glm/glm.hpp>
#include <memory>
#include <cstdint>
#include <vector>
#include <cstring>

#include "engine/physics.hpp"

namespace engine {

struct Vertex {
    glm::vec3 position{0.0f};
    glm::vec3 normal{0.0f, 1.0f, 0.0f};
    glm::vec2 uv{0.0f};
    glm::vec4 color{1.0f};
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

    // Backward compatibility helper
    static std::shared_ptr<Mesh> create_cube();
};

class InstancedMesh : public IInstancedMesh {
public:
    InstancedMesh() = default;
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
