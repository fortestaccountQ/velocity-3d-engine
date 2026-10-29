#pragma once

#include "engine/node3d.hpp"
#include "engine/physics.hpp"
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <algorithm>
#include <cmath>

namespace engine {

class ICameraRaycast {
public:
    virtual ~ICameraRaycast() = default;

    // Convert 2D viewport coordinates (pixel space) to a 3D ray in world space
    virtual Ray screen_to_ray(float mouse_x, float mouse_y, float screen_w, float screen_h) const = 0;
};

class Camera : public Node3D, public ICameraRaycast {
public:
    glm::vec3 position{0.0f, 2.0f, 6.0f};
    glm::vec3 target{0.0f, 0.0f, 0.0f};
    glm::vec3 up{0.0f, 1.0f, 0.0f};
    float fov{55.0f};
    float aspect{1.333333f};
    float near_plane{0.20f};
    float far_plane{100.0f};
    float yaw{-90.0f};
    float pitch{0.0f};

    Camera() : Node3D("Camera") {
        transform.position = position;
        update_vectors_from_angles();
    }

    void set_perspective(float fov_deg, float aspect_ratio, float near_z, float far_z) {
        fov = fov_deg;
        aspect = aspect_ratio;
        near_plane = near_z;
        far_plane = far_z;
    }

    void update_vectors_from_angles() {
        glm::vec3 front;
        front.x = std::cos(glm::radians(yaw)) * std::cos(glm::radians(pitch));
        front.y = std::sin(glm::radians(pitch));
        front.z = std::sin(glm::radians(yaw)) * std::cos(glm::radians(pitch));
        target = position + glm::normalize(front);
        transform.position = position;
        transform.set_orientation(quat_look_rotation(forward(), up));
        invalidate_world_matrix();
    }

    void rotate(float delta_yaw, float delta_pitch) {
        yaw += delta_yaw;
        pitch += delta_pitch;
        if (pitch > 89.0f) pitch = 89.0f;
        if (pitch < -89.0f) pitch = -89.0f;
        update_vectors_from_angles();
    }

    void set_yaw_pitch(float new_yaw, float new_pitch) {
        yaw = new_yaw;
        pitch = std::clamp(new_pitch, -89.0f, 89.0f);
        update_vectors_from_angles();
    }

    void set_position(float x, float y, float z) {
        glm::vec3 fwd = forward();
        position = { x, y, z };
        transform.position = position;
        target = position + fwd;
        invalidate_world_matrix();
    }

    void set_target(float x, float y, float z) {
        target = { x, y, z };
        glm::vec3 dir = forward();
        pitch = glm::degrees(std::asin(std::clamp(dir.y, -1.0f, 1.0f)));
        yaw = glm::degrees(std::atan2(dir.z, dir.x));
        transform.set_orientation(quat_look_rotation(dir, up));
        invalidate_world_matrix();
    }

    void set_up(float x, float y, float z) {
        up = { x, y, z };
        transform.set_orientation(quat_look_rotation(forward(), up));
        invalidate_world_matrix();
    }

    glm::mat4 view_matrix() const {
        if (parent()) {
            glm::vec3 w_pos = world_position();
            glm::quat w_rot = world_orientation();
            glm::vec3 w_fwd = w_rot * glm::vec3(0.0f, 0.0f, -1.0f);
            glm::vec3 w_up = w_rot * glm::vec3(0.0f, 1.0f, 0.0f);
            return glm::lookAt(w_pos, w_pos + w_fwd, w_up);
        }
        return glm::lookAt(position, target, up);
    }

    glm::mat4 projection_matrix() const {
        return glm::perspective(glm::radians(fov), aspect, near_plane, far_plane);
    }

    glm::mat4 view_projection_matrix() const {
        return projection_matrix() * view_matrix();
    }

    glm::vec3 forward() const {
        glm::vec3 dir = target - position;
        float len = glm::length(dir);
        return (len > 0.0001f) ? (dir / len) : glm::vec3(0.0f, 0.0f, -1.0f);
    }

    glm::vec3 right() const {
        return glm::normalize(glm::cross(forward(), up));
    }

    void move_forward(float distance) {
        glm::vec3 fwd = forward();
        position += fwd * distance;
        target += fwd * distance;
        transform.position = position;
        invalidate_world_matrix();
    }

    void move_right(float distance) {
        glm::vec3 r = right();
        position += r * distance;
        target += r * distance;
        transform.position = position;
        invalidate_world_matrix();
    }

    void move_up(float distance) {
        position += up * distance;
        target += up * distance;
        transform.position = position;
        invalidate_world_matrix();
    }

    Ray screen_to_ray(float mouse_x, float mouse_y, float screen_w, float screen_h) const override;
};

} // namespace engine
