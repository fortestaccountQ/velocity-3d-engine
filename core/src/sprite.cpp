#include "engine/sprite.hpp"
#include <cmath>
#include <algorithm>

namespace engine {

SpriteMaterial::SpriteMaterial(std::shared_ptr<Texture> tex, const glm::vec4& col)
    : Material(tex, 1.0f, 0.0f) {
    base_color = col;
    transparent = true;
    blend_mode = BlendMode::Alpha;
    depth_write = false;
}

Sprite::Sprite(std::shared_ptr<SpriteMaterial> mat)
    : Node3D("Sprite"), material(mat) {
    cast_shadows = false;
}

std::shared_ptr<Mesh> Sprite::quad_mesh() {
    static std::shared_ptr<Mesh> s_quad = nullptr;
    if (!s_quad) {
        s_quad = std::make_shared<Mesh>();
        s_quad->cpu_vertices = {
            { { -0.5f, -0.5f, 0.0f }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 1.0f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } },
            { {  0.5f, -0.5f, 0.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 1.0f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } },
            { {  0.5f,  0.5f, 0.0f }, { 0.0f, 0.0f, 1.0f }, { 1.0f, 0.0f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } },
            { { -0.5f,  0.5f, 0.0f }, { 0.0f, 0.0f, 1.0f }, { 0.0f, 0.0f }, glm::vec4(1.0f), { 1.0f, 0.0f, 0.0f, 1.0f } }
        };
        s_quad->cpu_indices = { 0, 1, 2, 0, 2, 3 };
        s_quad->num_indices = 6;
        s_quad->calculate_aabb();
        s_quad->ensure_gpu_buffers();
    }
    return s_quad;
}

glm::mat4 Sprite::compute_billboard_matrix(const Camera& camera) const {
    glm::mat4 w = world_matrix();
    glm::vec3 world_pos = glm::vec3(w[3]);
    glm::vec3 scale(
        glm::length(glm::vec3(w[0])),
        glm::length(glm::vec3(w[1])),
        glm::length(glm::vec3(w[2]))
    );

    glm::mat4 view = camera.view_matrix();
    glm::vec3 cam_right(view[0][0], view[1][0], view[2][0]);
    glm::vec3 cam_up(view[0][1], view[1][1], view[2][1]);

    float rot = material ? material->rotation : 0.0f;
    float cos_r = std::cos(rot);
    float sin_r = std::sin(rot);

    glm::vec3 right = (cam_right * cos_r + cam_up * sin_r) * scale.x;
    glm::vec3 up = (-cam_right * sin_r + cam_up * cos_r) * scale.y;
    glm::vec3 forward = glm::cross(cam_right, cam_up) * scale.z;

    if (material && !material->size_attenuation) {
        float dist = glm::length(world_pos - camera.position);
        right *= dist * 0.1f;
        up *= dist * 0.1f;
    }

    glm::mat4 m(1.0f);
    m[0] = glm::vec4(right, 0.0f);
    m[1] = glm::vec4(up, 0.0f);
    m[2] = glm::vec4(forward, 0.0f);

    glm::vec3 anchor_offset = right * (0.5f - center.x) + up * (0.5f - center.y);
    m[3] = glm::vec4(world_pos + anchor_offset, 1.0f);
    return m;
}

AABB Sprite::world_aabb() const {
    glm::vec3 p = world_position();
    glm::vec3 s = transform.scale;
    float r = std::max(s.x, s.y) * 0.707f;
    return AABB{ p - glm::vec3(r), p + glm::vec3(r) };
}

} // namespace engine
