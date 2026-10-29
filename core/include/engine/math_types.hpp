#pragma once

#ifndef GLM_ENABLE_EXPERIMENTAL
#define GLM_ENABLE_EXPERIMENTAL
#endif

#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <glm/gtx/matrix_decompose.hpp>

#include <array>
#include <vector>
#include <string>
#include <cmath>
#include <algorithm>
#include <cstdint>
#include <utility>

namespace engine {

// ---------------------------------------------------------------------------
// Math Constants & Utility Functions
// ---------------------------------------------------------------------------
struct MathUtils {
    static constexpr float PI = 3.14159265358979323846f;
    static constexpr float TWO_PI = 6.28318530717958647692f;
    static constexpr float HALF_PI = 1.57079632679489661923f;

    template <typename T>
    static constexpr T clamp(T val, T min_v, T max_v) {
        return (val < min_v) ? min_v : ((val > max_v) ? max_v : val);
    }

    template <typename T>
    static constexpr T lerp(T a, T b, float t) {
        return a + (b - a) * t;
    }

    static float smoothstep(float edge0, float edge1, float x) {
        if (std::abs(edge1 - edge0) < 1e-7f) return 0.0f;
        float t = clamp((x - edge0) / (edge1 - edge0), 0.0f, 1.0f);
        return t * t * (3.0f - 2.0f * t);
    }

    template <typename T>
    static T damp(T a, T b, float lambda, float dt) {
        return lerp(a, b, 1.0f - std::exp(-lambda * dt));
    }

    static float map_linear(float val, float in_min, float in_max, float out_min, float out_max) {
        if (std::abs(in_max - in_min) < 1e-7f) return out_min;
        return out_min + (val - in_min) * (out_max - out_min) / (in_max - in_min);
    }

    static constexpr float deg_to_rad(float deg) {
        return deg * (PI / 180.0f);
    }

    static constexpr float rad_to_deg(float rad) {
        return rad * (180.0f / PI);
    }
};

// ---------------------------------------------------------------------------
// Quaternion Helper Functions
// ---------------------------------------------------------------------------

inline glm::quat quat_from_axis_angle(const glm::vec3& axis, float deg) {
    float len = glm::length(axis);
    if (len < 1e-6f) return glm::quat(1.0f, 0.0f, 0.0f, 0.0f);
    return glm::angleAxis(glm::radians(deg), axis / len);
}

inline glm::quat quat_from_euler(float pitch_deg, float yaw_deg, float roll_deg, const std::string& order = "YXZ") {
    glm::quat qx = quat_from_axis_angle(glm::vec3(1.0f, 0.0f, 0.0f), pitch_deg);
    glm::quat qy = quat_from_axis_angle(glm::vec3(0.0f, 1.0f, 0.0f), yaw_deg);
    glm::quat qz = quat_from_axis_angle(glm::vec3(0.0f, 0.0f, 1.0f), roll_deg);

    glm::quat q;
    if (order == "XYZ") {
        q = qx * qy * qz;
    } else if (order == "XZY") {
        q = qx * qz * qy;
    } else if (order == "YZX") {
        q = qy * qz * qx;
    } else if (order == "ZXY") {
        q = qz * qx * qy;
    } else if (order == "ZYX") {
        q = qz * qy * qx;
    } else { // Default: "YXZ"
        q = qy * qx * qz;
    }
    return glm::normalize(q);
}

inline glm::quat quat_from_euler(const glm::vec3& euler_deg, const std::string& order = "YXZ") {
    return quat_from_euler(euler_deg.x, euler_deg.y, euler_deg.z, order);
}

inline glm::vec3 quat_to_euler(const glm::quat& q_in, const std::string& order = "YXZ") {
    glm::quat q = glm::normalize(q_in);
    glm::mat3 m = glm::mat3_cast(q);

    float pitch = 0.0f;
    float yaw = 0.0f;
    float roll = 0.0f;

    if (order == "XYZ") {
        if (std::abs(m[2][0]) < 0.99999f) {
            yaw = std::asin(MathUtils::clamp(m[2][0], -1.0f, 1.0f));
            pitch = std::atan2(-m[2][1], m[2][2]);
            roll = std::atan2(-m[1][0], m[0][0]);
        } else {
            yaw = (m[2][0] > 0.0f) ? MathUtils::HALF_PI : -MathUtils::HALF_PI;
            pitch = std::atan2(m[1][2], m[1][1]);
            roll = 0.0f;
        }
    } else if (order == "ZYX") {
        if (std::abs(m[0][2]) < 0.99999f) {
            yaw = std::asin(MathUtils::clamp(-m[0][2], -1.0f, 1.0f));
            pitch = std::atan2(m[1][2], m[2][2]);
            roll = std::atan2(m[0][1], m[0][0]);
        } else {
            yaw = (m[0][2] < 0.0f) ? MathUtils::HALF_PI : -MathUtils::HALF_PI;
            pitch = std::atan2(-m[1][0], m[1][1]);
            roll = 0.0f;
        }
    } else { // Default: "YXZ"
        if (std::abs(m[2][1]) < 0.99999f) {
            pitch = std::asin(MathUtils::clamp(-m[2][1], -1.0f, 1.0f));
            yaw = std::atan2(m[2][0], m[2][2]);
            roll = std::atan2(m[0][1], m[1][1]);
        } else {
            pitch = (m[2][1] < 0.0f) ? MathUtils::HALF_PI : -MathUtils::HALF_PI;
            yaw = std::atan2(-m[1][0], m[0][0]);
            roll = 0.0f;
        }
    }

    return glm::vec3(glm::degrees(pitch), glm::degrees(yaw), glm::degrees(roll));
}

inline glm::quat quat_look_rotation(const glm::vec3& forward, const glm::vec3& up = glm::vec3(0.0f, 1.0f, 0.0f)) {
    float len = glm::length(forward);
    if (len < 1e-6f) {
        return glm::quat(1.0f, 0.0f, 0.0f, 0.0f);
    }
    glm::vec3 f = forward / len;
    glm::vec3 r = glm::cross(f, up);
    float r_len = glm::length(r);
    if (r_len < 1e-6f) {
        glm::vec3 alt_up = (std::abs(f.y) < 0.999f) ? glm::vec3(0.0f, 1.0f, 0.0f) : glm::vec3(0.0f, 0.0f, 1.0f);
        r = glm::cross(f, alt_up);
        r_len = glm::length(r);
        if (r_len < 1e-6f) {
            return glm::quat(1.0f, 0.0f, 0.0f, 0.0f);
        }
    }
    r /= r_len;
    glm::vec3 u = glm::cross(r, f);
    glm::mat3 rot(r, u, -f);
    return glm::normalize(glm::quat_cast(rot));
}

inline glm::quat quat_slerp(const glm::quat& q1, const glm::quat& q2, float t) {
    return glm::slerp(glm::normalize(q1), glm::normalize(q2), t);
}

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

    bool intersects_aabb(const std::pair<glm::vec3, glm::vec3>& aabb) const {
        return intersects_aabb(aabb.first, aabb.second);
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
