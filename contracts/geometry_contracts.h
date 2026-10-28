#pragma once

#include <glm/glm.hpp>
#include <vector>
#include <memory>
#include <cstdint>
#include "engine/physics.hpp"

namespace engine {

struct Vertex {
    glm::vec3 position;
    glm::vec3 normal;
    glm::vec2 uv;
    glm::vec4 color;
};

struct InstanceData {
    glm::mat4 model_matrix;
    glm::vec4 color;
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

} // namespace engine
