#pragma once

#include "engine/texture.hpp"
#include <glm/glm.hpp>
#include <memory>

namespace engine {

class Material {
public:
    std::shared_ptr<Texture> albedo_map{nullptr};
    glm::vec4 base_color{1.0f, 1.0f, 1.0f, 1.0f};
    float roughness{0.5f};
    float metallic{0.0f};
    glm::vec2 uv_scale{1.0f, 1.0f};
    glm::vec2 uv_offset{0.0f, 0.0f};

    Material() = default;
    Material(std::shared_ptr<Texture> texture, float roughness = 0.5f, float metallic = 0.0f)
        : albedo_map(std::move(texture)), roughness(roughness), metallic(metallic) {}

    void set_color(float r, float g, float b, float a = 1.0f) {
        base_color = { r, g, b, a };
    }

    void set_uv_scale(float u, float v) {
        uv_scale = { u, v };
    }

    void set_uv_offset(float u, float v) {
        uv_offset = { u, v };
    }
};

} // namespace engine
