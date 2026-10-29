#include "engine/camera.hpp"

namespace engine {

Ray Camera::screen_to_ray(float mouse_x, float mouse_y, float screen_w, float screen_h) const {
    glm::vec3 origin = parent() ? world_position() : position;
    glm::vec3 fwd = parent() ? world_direction() : forward();

    if (screen_w <= 0.0f || screen_h <= 0.0f) {
        return Ray(origin, fwd);
    }

    // Normalized Device Coordinates:
    // mouse_x: [0, screen_w] -> [-1.0, 1.0]
    // mouse_y: [0, screen_h] (top to bottom) -> [1.0, -1.0] (top to bottom)
    float ndc_x = (2.0f * mouse_x) / screen_w - 1.0f;
    float ndc_y = 1.0f - (2.0f * mouse_y) / screen_h;

    glm::mat4 proj = projection_matrix();
    if (type == CameraType::Perspective) {
        float cur_aspect = screen_w / screen_h;
        proj = glm::perspective(glm::radians(fov), cur_aspect, near_plane, far_plane);
    }
    glm::mat4 inv_vp = glm::inverse(proj * view_matrix());

    // Unproject near point (z = 0.0f for DirectX/Metal [0, 1] clip space)
    // and far point (z = 1.0f)
    glm::vec4 near_clip(ndc_x, ndc_y, 0.0f, 1.0f);
    glm::vec4 far_clip(ndc_x, ndc_y, 1.0f, 1.0f);

    glm::vec4 near_world_h = inv_vp * near_clip;
    glm::vec4 far_world_h = inv_vp * far_clip;

    if (std::abs(near_world_h.w) > 1e-7f && std::abs(far_world_h.w) > 1e-7f) {
        glm::vec3 near_world = glm::vec3(near_world_h) / near_world_h.w;
        glm::vec3 far_world = glm::vec3(far_world_h) / far_world_h.w;
        glm::vec3 ray_dir = glm::normalize(far_world - near_world);
        return Ray(near_world, ray_dir);
    }

    return Ray(origin, fwd);
}

} // namespace engine
