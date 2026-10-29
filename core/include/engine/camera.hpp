#pragma once

#include "engine/node3d.hpp"
#include "engine/physics.hpp"
#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <algorithm>
#include <cmath>
#include <string>

namespace engine {

enum class CameraType {
    Perspective = 0,
    Orthographic = 1
};

class ICameraRaycast {
public:
    virtual ~ICameraRaycast() = default;

    // Convert 2D viewport coordinates (pixel space) to a 3D ray in world space
    virtual Ray screen_to_ray(float mouse_x, float mouse_y, float screen_w, float screen_h) const = 0;
};

class Camera : public Node3D, public ICameraRaycast {
public:
    CameraType type{CameraType::Perspective};

    glm::vec3 position{0.0f, 2.0f, 6.0f};
    glm::vec3 target{0.0f, 0.0f, 0.0f};
    glm::vec3 up{0.0f, 1.0f, 0.0f};
    float fov{55.0f};
    float aspect{1.333333f};
    float near_plane{0.20f};
    float far_plane{100.0f};
    float yaw{-90.0f};
    float pitch{0.0f};

    // Viewport & Scissor support (normalized [0..1] or pixel coordinates)
    glm::vec4 viewport{0.0f, 0.0f, 1.0f, 1.0f};
    glm::vec4 scissor{0.0f, 0.0f, 1.0f, 1.0f};
    bool has_scissor{false};
    glm::vec4 clear_color{0.43137f, 0.62745f, 0.82353f, 1.0f};

    // Orthographic parameters
    float ortho_left{-1.0f};
    float ortho_right{1.0f};
    float ortho_bottom{-1.0f};
    float ortho_top{1.0f};
    float zoom{1.0f};

    Camera() : Node3D("Camera") {
        transform.position = position;
        update_vectors_from_angles();
    }

    explicit Camera(const std::string& name) : Node3D(name) {
        transform.position = position;
        update_vectors_from_angles();
    }

    virtual ~Camera() = default;

    void set_perspective(float fov_deg, float aspect_ratio, float near_z, float far_z) {
        type = CameraType::Perspective;
        fov = fov_deg;
        aspect = aspect_ratio;
        near_plane = near_z;
        far_plane = far_z;
    }

    void set_orthographic(float left, float right, float bottom, float top, float near_z = 0.1f, float far_z = 100.0f, float zoom_val = 1.0f) {
        type = CameraType::Orthographic;
        ortho_left = left;
        ortho_right = right;
        ortho_bottom = bottom;
        ortho_top = top;
        near_plane = near_z;
        far_plane = far_z;
        zoom = zoom_val;
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

    virtual glm::mat4 view_matrix() const {
        if (parent()) {
            glm::vec3 w_pos = world_position();
            glm::quat w_rot = world_orientation();
            glm::vec3 w_fwd = w_rot * glm::vec3(0.0f, 0.0f, -1.0f);
            glm::vec3 w_up = w_rot * glm::vec3(0.0f, 1.0f, 0.0f);
            return glm::lookAt(w_pos, w_pos + w_fwd, w_up);
        }
        return glm::lookAt(position, target, up);
    }

    virtual glm::mat4 projection_matrix() const {
        if (type == CameraType::Orthographic) {
            float z = (zoom > 0.0001f) ? zoom : 1.0f;
            return glm::ortho(ortho_left / z, ortho_right / z, ortho_bottom / z, ortho_top / z, near_plane, far_plane);
        }
        return glm::perspective(glm::radians(fov), aspect, near_plane, far_plane);
    }

    virtual glm::mat4 view_projection_matrix() const {
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

class PerspectiveCamera : public Camera {
public:
    PerspectiveCamera(float fov_deg = 55.0f, float aspect_ratio = 1.333333f, float near_z = 0.20f, float far_z = 100.0f)
        : Camera("PerspectiveCamera") {
        type = CameraType::Perspective;
        fov = fov_deg;
        aspect = aspect_ratio;
        near_plane = near_z;
        far_plane = far_z;
    }
};

class OrthographicCamera : public Camera {
public:
    OrthographicCamera(float left = -1.0f, float right = 1.0f, float bottom = -1.0f, float top = 1.0f, float near_z = 0.1f, float far_z = 100.0f, float zoom_val = 1.0f)
        : Camera("OrthographicCamera") {
        type = CameraType::Orthographic;
        ortho_left = left;
        ortho_right = right;
        ortho_bottom = bottom;
        ortho_top = top;
        near_plane = near_z;
        far_plane = far_z;
        zoom = zoom_val;
    }

    float left() const { return ortho_left; }
    void set_left(float val) { ortho_left = val; }
    float right() const { return ortho_right; }
    void set_right(float val) { ortho_right = val; }
    float bottom() const { return ortho_bottom; }
    void set_bottom(float val) { ortho_bottom = val; }
    float top() const { return ortho_top; }
    void set_top(float val) { ortho_top = val; }
};

} // namespace engine
