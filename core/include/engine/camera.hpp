#pragma once

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>

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

    Camera() = default;

    void set_position(float x, float y, float z) { position = { x, y, z }; }
    void set_target(float x, float y, float z) { target = { x, y, z }; }
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
