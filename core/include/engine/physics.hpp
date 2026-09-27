#pragma once

#include <glm/glm.hpp>
#include <algorithm>
#include <limits>
#include <memory>
#include <cmath>

namespace engine {

class Entity;

struct AABB {
    glm::vec3 min_point{std::numeric_limits<float>::max()};
    glm::vec3 max_point{std::numeric_limits<float>::lowest()};

    AABB() = default;
    AABB(const glm::vec3& min_p, const glm::vec3& max_p)
        : min_point(min_p), max_point(max_p) {}

    bool is_valid() const {
        return min_point.x <= max_point.x &&
               min_point.y <= max_point.y &&
               min_point.z <= max_point.z;
    }

    glm::vec3 center() const {
        return (min_point + max_point) * 0.5f;
    }

    glm::vec3 size() const {
        return is_valid() ? (max_point - min_point) : glm::vec3(0.0f);
    }

    glm::vec3 extents() const {
        return size() * 0.5f;
    }

    void expand(const glm::vec3& point) {
        min_point = glm::min(min_point, point);
        max_point = glm::max(max_point, point);
    }

    void expand(const AABB& other) {
        if (!other.is_valid()) return;
        min_point = glm::min(min_point, other.min_point);
        max_point = glm::max(max_point, other.max_point);
    }

    bool contains(const glm::vec3& p) const {
        if (!is_valid()) return false;
        return (p.x >= min_point.x && p.x <= max_point.x &&
                p.y >= min_point.y && p.y <= max_point.y &&
                p.z >= min_point.z && p.z <= max_point.z);
    }

    bool intersects(const AABB& other) const {
        if (!is_valid() || !other.is_valid()) return false;
        if (max_point.x < other.min_point.x || min_point.x > other.max_point.x) return false;
        if (max_point.y < other.min_point.y || min_point.y > other.max_point.y) return false;
        if (max_point.z < other.min_point.z || min_point.z > other.max_point.z) return false;
        return true;
    }

    AABB scaled(float scale) const {
        if (!is_valid()) return *this;
        glm::vec3 c = center();
        glm::vec3 e = extents() * scale;
        return AABB(c - e, c + e);
    }

    bool get_penetration(const AABB& other, glm::vec3& mtv_out) const {
        if (!intersects(other)) return false;

        float dx1 = max_point.x - other.min_point.x;
        float dx2 = other.max_point.x - min_point.x;
        float push_x = (dx1 < dx2) ? -dx1 : dx2;

        float dy1 = max_point.y - other.min_point.y;
        float dy2 = other.max_point.y - min_point.y;
        float push_y = (dy1 < dy2) ? -dy1 : dy2;

        float dz1 = max_point.z - other.min_point.z;
        float dz2 = other.max_point.z - min_point.z;
        float push_z = (dz1 < dz2) ? -dz1 : dz2;

        float ax = std::abs(push_x);
        float ay = std::abs(push_y);
        float az = std::abs(push_z);

        if (ax <= ay && ax <= az) {
            mtv_out = glm::vec3(push_x, 0.0f, 0.0f);
        } else if (ay <= ax && ay <= az) {
            mtv_out = glm::vec3(0.0f, push_y, 0.0f);
        } else {
            mtv_out = glm::vec3(0.0f, 0.0f, push_z);
        }
        return true;
    }

    AABB transformed(const glm::mat4& matrix) const {
        if (!is_valid()) return *this;

        glm::vec3 corners[8] = {
            { min_point.x, min_point.y, min_point.z },
            { max_point.x, min_point.y, min_point.z },
            { min_point.x, max_point.y, min_point.z },
            { max_point.x, max_point.y, min_point.z },
            { min_point.x, min_point.y, max_point.z },
            { max_point.x, min_point.y, max_point.z },
            { min_point.x, max_point.y, max_point.z },
            { max_point.x, max_point.y, max_point.z },
        };

        AABB result;
        for (int i = 0; i < 8; ++i) {
            glm::vec4 t = matrix * glm::vec4(corners[i], 1.0f);
            float w = t.w != 0.0f ? t.w : 1.0f;
            result.expand(glm::vec3(t) / w);
        }
        return result;
    }
};

struct Ray {
    glm::vec3 origin{0.0f};
    glm::vec3 direction{0.0f, 0.0f, -1.0f};

    Ray() = default;
    Ray(const glm::vec3& orig, const glm::vec3& dir)
        : origin(orig) {
        float len = glm::length(dir);
        direction = (len > 1e-6f) ? (dir / len) : glm::vec3(0.0f, 0.0f, -1.0f);
    }

    glm::vec3 point_at(float t) const {
        return origin + direction * t;
    }

    bool intersect_aabb(const AABB& aabb, float& t_out) const {
        if (!aabb.is_valid()) return false;

        float tmin = 0.0f;
        float tmax = std::numeric_limits<float>::max();

        for (int i = 0; i < 3; ++i) {
            float o = origin[i];
            float d = direction[i];
            float min_val = aabb.min_point[i];
            float max_val = aabb.max_point[i];

            if (std::abs(d) < 1e-7f) {
                if (o < min_val || o > max_val) return false;
            } else {
                float inv_d = 1.0f / d;
                float t1 = (min_val - o) * inv_d;
                float t2 = (max_val - o) * inv_d;
                if (t1 > t2) std::swap(t1, t2);
                tmin = std::max(tmin, t1);
                tmax = std::min(tmax, t2);
                if (tmin > tmax) return false;
            }
        }

        t_out = tmin;
        return true;
    }
};

struct RaycastHit {
    bool hit{false};
    float distance{0.0f};
    glm::vec3 point{0.0f};
    std::shared_ptr<Entity> entity{nullptr};
};

} // namespace engine
