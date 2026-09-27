#pragma once

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <algorithm>
#include <cmath>

namespace engine {

class Camera {
public:
    glm::vec3 position{0.0f, 2.0f, 6.0f};
    glm::vec3 target{0.0f, 0.0f, 0.0f};
    glm::vec3 up{0.0f, 1.0f, 0.0f};
    float fov{55.0f};
    float aspect{1.333333f};
    float near_plane{0.1f};
    float far_plane{100.0f};
    float yaw{-90.0f};
    float pitch{0.0f};

    Camera() = default;

    void update_vectors_from_angles() {
        glm::vec3 front;
        front.x = std::cos(glm::radians(yaw)) * std::cos(glm::radians(pitch));
        front.y = std::sin(glm::radians(pitch));
        front.z = std::sin(glm::radians(yaw)) * std::cos(glm::radians(pitch));
        target = position + glm::normalize(front);
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
        target = position + fwd;
    }
    void set_target(float x, float y, float z) {
        target = { x, y, z };
        glm::vec3 dir = forward();
        pitch = glm::degrees(std::asin(std::clamp(dir.y, -1.0f, 1.0f)));
        yaw = glm::degrees(std::atan2(dir.z, dir.x));
    }
    void set_up(float x, float y, float z) { up = { x, y, z }; }

    glm::mat4 view_matrix() const {
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
    }

    void move_right(float distance) {
        glm::vec3 r = right();
        position += r * distance;
        target += r * distance;
    }

    void move_up(float distance) {
        position += up * distance;
        target += up * distance;
    }
};

} // namespace engine
