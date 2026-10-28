#pragma once

#include <glm/glm.hpp>
#include <string>
#include <memory>
#include <unordered_map>
#include <cstdint>

namespace engine {

enum class MaterialType : uint8_t {
    PBR = 0,
    UNLIT = 1,
    WIREFRAME = 2,
    CUSTOM_SHADER = 3
};

struct MaterialDescriptor {
    MaterialType type{MaterialType::PBR};
    glm::vec4 base_color{1.0f, 1.0f, 1.0f, 1.0f};
    float roughness{0.5f};
    float metallic{0.0f};
    glm::vec2 uv_scale{1.0f, 1.0f};
    bool double_sided{false};
    bool depth_write{true};
    bool wireframe{false};
    uint32_t albedo_texture_id{0};
    uint32_t normal_texture_id{0};
    uint32_t roughness_metallic_texture_id{0};
    uint32_t emissive_texture_id{0};
    glm::vec3 emissive_color{0.0f, 0.0f, 0.0f};
    float emissive_intensity{0.0f};
};

struct PipelineKey {
    uint32_t shader_id{0};
    bool wireframe{false};
    bool cull_back{true};
    bool depth_write{true};
    bool alpha_blend{false};

    bool operator==(const PipelineKey& other) const {
        return shader_id == other.shader_id &&
               wireframe == other.wireframe &&
               cull_back == other.cull_back &&
               depth_write == other.depth_write &&
               alpha_blend == other.alpha_blend;
    }
};

class IPipelineManager {
public:
    virtual ~IPipelineManager() = default;
    virtual uint32_t get_or_create_pipeline(const PipelineKey& key) = 0;
    virtual void release_all() = 0;
};

} // namespace engine
