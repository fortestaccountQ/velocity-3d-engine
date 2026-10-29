#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include <glm/gtc/matrix_transform.hpp>

namespace engine {

class Node3D;

// ---------------------------------------------------------------------------
// Plane & Frustum Geometric Math
// ---------------------------------------------------------------------------
struct Plane {
    glm::vec3 normal{0.0f, 1.0f, 0.0f};
    float constant{0.0f};

    Plane() = default;
    Plane(const glm::vec3& n, float c) : normal(n), constant(c) {}
    Plane(const glm::vec3& a, const glm::vec3& b, const glm::vec3& c) {
        normal = glm::normalize(glm::cross(b - a, c - a));
        constant = -glm::dot(normal, a);
    }

    float distance_to_point(const glm::vec3& point) const {
        return glm::dot(normal, point) + constant;
    }
};

struct Frustum {
    std::array<Plane, 6> planes; // Left, Right, Bottom, Top, Near, Far

    void set_from_projection_matrix(const glm::mat4& m) {
        // Left
        planes[0].normal = glm::vec3(m[0][3] + m[0][0], m[1][3] + m[1][0], m[2][3] + m[2][0]);
        planes[0].constant = m[3][3] + m[3][0];
        // Right
        planes[1].normal = glm::vec3(m[0][3] - m[0][0], m[1][3] - m[1][0], m[2][3] - m[2][0]);
        planes[1].constant = m[3][3] - m[3][0];
        // Bottom
        planes[2].normal = glm::vec3(m[0][3] + m[0][1], m[1][3] + m[1][1], m[2][3] + m[2][1]);
        planes[2].constant = m[3][3] + m[3][1];
        // Top
        planes[3].normal = glm::vec3(m[0][3] - m[0][1], m[1][3] - m[1][1], m[2][3] - m[2][1]);
        planes[3].constant = m[3][3] - m[3][1];
        // Near
        planes[4].normal = glm::vec3(m[0][3] + m[0][2], m[1][3] + m[1][2], m[2][3] + m[2][2]);
        planes[4].constant = m[3][3] + m[3][2];
        // Far
        planes[5].normal = glm::vec3(m[0][3] - m[0][2], m[1][3] - m[1][2], m[2][3] - m[2][2]);
        planes[5].constant = m[3][3] - m[3][2];

        for (auto& p : planes) {
            float len = glm::length(p.normal);
            if (len > 0.00001f) {
                p.normal /= len;
                p.constant /= len;
            }
        }
    }

    bool intersects_sphere(const glm::vec3& center, float radius) const {
        for (const auto& plane : planes) {
            if (plane.distance_to_point(center) < -radius) return false;
        }
        return true;
    }

    bool intersects_aabb(const glm::vec3& min_p, const glm::vec3& max_p) const {
        for (const auto& plane : planes) {
            glm::vec3 positive = min_p;
            if (plane.normal.x >= 0) positive.x = max_p.x;
            if (plane.normal.y >= 0) positive.y = max_p.y;
            if (plane.normal.z >= 0) positive.z = max_p.z;
            if (plane.distance_to_point(positive) < 0.0f) return false;
        }
        return true;
    }
};

// ---------------------------------------------------------------------------
// Render Statistics Contract
// ---------------------------------------------------------------------------
struct RenderStats {
    uint32_t draw_calls{0};
    uint32_t culled_objects{0};
    uint32_t total_triangles{0};
    uint32_t total_instances{0};
};

} // namespace engine
