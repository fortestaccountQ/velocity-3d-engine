#pragma once

#include "engine/math_types.hpp"
#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include <glm/gtc/matrix_transform.hpp>

namespace engine {

class Transform {
public:
    glm::vec3 position{0.0f, 0.0f, 0.0f};
    mutable glm::quat orientation{1.0f, 0.0f, 0.0f, 0.0f}; // Identity (w=1, x=0, y=0, z=0)
    glm::vec3 scale{1.0f, 1.0f, 1.0f};

    // Synchronized Euler angle cache (degrees, YXZ order)
    mutable glm::vec3 rotation_euler{0.0f, 0.0f, 0.0f};
    mutable glm::vec3 last_synced_euler_{0.0f, 0.0f, 0.0f};

    Transform() = default;

    Transform(const glm::vec3& pos, const glm::vec3& rot_deg = glm::vec3(0.0f), const glm::vec3& sc = glm::vec3(1.0f))
        : position(pos), scale(sc) {
        set_rotation(rot_deg);
    }

    Transform(const glm::vec3& pos, const glm::quat& orient, const glm::vec3& sc = glm::vec3(1.0f))
        : position(pos), scale(sc) {
        set_orientation(orient);
    }

    void set_position(float x, float y, float z) { position = { x, y, z }; }
    void set_position(const glm::vec3& p) { position = p; }

    void set_scale(float sx, float sy, float sz) { scale = { sx, sy, sz }; }
    void set_scale(const glm::vec3& s) { scale = s; }

    void sync_euler_from_orientation() const {
        rotation_euler = quat_to_euler(orientation, "YXZ");
        last_synced_euler_ = rotation_euler;
    }

    void sync_orientation_from_euler() const {
        orientation = quat_from_euler(rotation_euler.x, rotation_euler.y, rotation_euler.z, "YXZ");
        last_synced_euler_ = rotation_euler;
    }

    glm::vec3 rotation() const {
        sync_euler_from_orientation();
        return rotation_euler;
    }

    void set_rotation(float rx, float ry, float rz) {
        set_rotation(glm::vec3(rx, ry, rz));
    }

    void set_rotation(const glm::vec3& euler_deg) {
        rotation_euler = euler_deg;
        last_synced_euler_ = euler_deg;
        orientation = quat_from_euler(euler_deg.x, euler_deg.y, euler_deg.z, "YXZ");
    }

    void set_orientation(const glm::quat& q) {
        orientation = glm::normalize(q);
        sync_euler_from_orientation();
    }

    const glm::quat& get_orientation() const {
        return orientation;
    }

    void set_matrix(const glm::mat4& m) {
        position = glm::vec3(m[3]);
        float sx = glm::length(glm::vec3(m[0]));
        float sy = glm::length(glm::vec3(m[1]));
        float sz = glm::length(glm::vec3(m[2]));
        scale = glm::vec3(sx, sy, sz);
        if (sx > 1e-6f && sy > 1e-6f && sz > 1e-6f) {
            glm::mat3 rot_mat(
                glm::vec3(m[0]) / sx,
                glm::vec3(m[1]) / sy,
                glm::vec3(m[2]) / sz
            );
            set_orientation(glm::quat_cast(rot_mat));
        }
    }

    void translate(const glm::vec3& v) {
        position += v;
    }

    void rotate_x(float deg) {
        glm::quat q = quat_from_axis_angle(glm::vec3(1.0f, 0.0f, 0.0f), deg);
        set_orientation(orientation * q);
    }

    void rotate_y(float deg) {
        glm::quat q = quat_from_axis_angle(glm::vec3(0.0f, 1.0f, 0.0f), deg);
        set_orientation(orientation * q);
    }

    void rotate_z(float deg) {
        glm::quat q = quat_from_axis_angle(glm::vec3(0.0f, 0.0f, 1.0f), deg);
        set_orientation(orientation * q);
    }

    void rotate_on_axis(const glm::vec3& axis, float deg) {
        glm::quat q = quat_from_axis_angle(axis, deg);
        set_orientation(orientation * q);
    }

    void look_at(const glm::vec3& target, const glm::vec3& up = glm::vec3(0.0f, 1.0f, 0.0f)) {
        glm::vec3 dir = target - position;
        set_orientation(quat_look_rotation(dir, up));
    }

    glm::mat4 model_matrix() const {
        if (rotation_euler != last_synced_euler_) {
            sync_orientation_from_euler();
        }
        glm::mat4 m = glm::translate(glm::mat4(1.0f), position);
        m = m * glm::mat4_cast(orientation);
        m = glm::scale(m, scale);
        return m;
    }

    glm::mat4 normal_matrix() const {
        glm::mat3 m3 = glm::mat3(model_matrix());
        return glm::mat4(glm::transpose(glm::inverse(m3)));
    }
};

} // namespace engine
