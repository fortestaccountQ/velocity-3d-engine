#pragma once

#include "engine/texture.hpp"
#include "contracts/phase2_materials_contracts.h"
#include "sokol_gfx.h"
#include <glm/glm.hpp>
#include <memory>
#include <string>
#include <unordered_map>
#include <cstdint>

namespace engine {

enum class MaterialType : uint8_t {
    Standard = 0,
    Unlit = 1,
    Lambert = 2,
    Phong = 3,
    Physical = 4,
    Toon = 5,
    CustomShader = 6,
    PBR = 0
};

// ---------------------------------------------------------------------------
// Base Material
// ---------------------------------------------------------------------------
class Material {
public:
    virtual ~Material() = default;

    virtual MaterialType type() const { return MaterialType::Standard; }

    bool transparent{false};
    float opacity{1.0f};
    bool depth_write{true};
    bool depth_test{true};
    bool wireframe{false};
    SideMode side{SideMode::Front};
    BlendMode blend_mode{BlendMode::Opaque};

    // Textures & Basic properties (backwards-compatible)
    std::shared_ptr<Texture> albedo_map{nullptr};
    glm::vec4 base_color{1.0f, 1.0f, 1.0f, 1.0f};
    float roughness{0.5f};
    float metallic{0.0f};
    glm::vec2 uv_scale{1.0f, 1.0f};
    glm::vec2 uv_offset{0.0f, 0.0f};

    // PBR Texture maps
    std::shared_ptr<Texture> normal_map{nullptr};
    std::shared_ptr<Texture> metallic_roughness_map{nullptr};
    std::shared_ptr<Texture> occlusion_map{nullptr};
    std::shared_ptr<Texture> ao_map{nullptr};
    std::shared_ptr<Texture> emissive_map{nullptr};

    // PBR and Blending parameters
    glm::vec3 emissive_color{0.0f, 0.0f, 0.0f};
    float emissive_intensity{1.0f};
    float normal_scale{1.0f};
    float ao_intensity{1.0f};
    bool alpha_test{false};
    float alpha_cutoff{0.5f};

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

// ---------------------------------------------------------------------------
// Unlit Material
// ---------------------------------------------------------------------------
class UnlitMaterial : public Material {
public:
    UnlitMaterial() {
        roughness = 1.0f;
        metallic = 0.0f;
    }
    UnlitMaterial(const glm::vec4& color, std::shared_ptr<Texture> map = nullptr, bool wf = false) {
        base_color = color;
        albedo_map = std::move(map);
        wireframe = wf;
        roughness = 1.0f;
        metallic = 0.0f;
    }

    MaterialType type() const override { return MaterialType::Unlit; }
};

// ---------------------------------------------------------------------------
// Lambert Material
// ---------------------------------------------------------------------------
class LambertMaterial : public Material {
public:
    LambertMaterial() {
        roughness = 1.0f;
        metallic = 0.0f;
    }
    LambertMaterial(const glm::vec4& color, std::shared_ptr<Texture> map = nullptr) {
        base_color = color;
        albedo_map = std::move(map);
        roughness = 1.0f;
        metallic = 0.0f;
    }

    MaterialType type() const override { return MaterialType::Lambert; }
};

// ---------------------------------------------------------------------------
// Phong Material
// ---------------------------------------------------------------------------
class PhongMaterial : public Material {
public:
    float shininess{30.0f};
    glm::vec3 specular_color{1.0f, 1.0f, 1.0f};

    PhongMaterial() {
        roughness = 0.35f;
        metallic = 0.0f;
    }
    PhongMaterial(const glm::vec4& color, std::shared_ptr<Texture> map = nullptr, float shininess_val = 30.0f)
        : shininess(shininess_val) {
        base_color = color;
        albedo_map = std::move(map);
        roughness = 0.35f;
        metallic = 0.0f;
    }

    MaterialType type() const override { return MaterialType::Phong; }
};

// ---------------------------------------------------------------------------
// Standard Material (PBR Cook-Torrance)
// ---------------------------------------------------------------------------
class StandardMaterial : public Material {
public:
    StandardMaterial() = default;
    StandardMaterial(std::shared_ptr<Texture> texture, float roughness_val = 0.5f, float metallic_val = 0.0f)
        : Material(std::move(texture), roughness_val, metallic_val) {}

    MaterialType type() const override { return MaterialType::Standard; }
};

// ---------------------------------------------------------------------------
// Physical Material (Extended PBR: clearcoat, transmission, ior, sheen)
// ---------------------------------------------------------------------------
class PhysicalMaterial : public StandardMaterial {
public:
    float clearcoat{0.0f};
    float clearcoat_roughness{0.0f};
    float transmission{0.0f};
    float ior{1.5f};
    glm::vec3 sheen{0.0f, 0.0f, 0.0f};
    float sheen_roughness{0.0f};

    PhysicalMaterial() = default;

    MaterialType type() const override { return MaterialType::Physical; }
};

// ---------------------------------------------------------------------------
// Toon Material (Cel Shading)
// ---------------------------------------------------------------------------
class ToonMaterial : public Material {
public:
    int steps{3};
    int num_steps{3};

    ToonMaterial() = default;
    ToonMaterial(const glm::vec4& color, std::shared_ptr<Texture> map = nullptr, int step_count = 3)
        : steps(step_count), num_steps(step_count) {
        base_color = color;
        albedo_map = std::move(map);
    }

    MaterialType type() const override { return MaterialType::Toon; }
};

// ---------------------------------------------------------------------------
// Shader Material (Custom GLSL/HLSL strings + uniforms)
// ---------------------------------------------------------------------------
class ShaderMaterial : public Material {
public:
    std::string vertex_shader;
    std::string fragment_shader;
    std::unordered_map<std::string, glm::vec4> uniforms;

    ShaderMaterial() = default;
    ShaderMaterial(std::string vs, std::string fs)
        : vertex_shader(std::move(vs)), fragment_shader(std::move(fs)) {}

    MaterialType type() const override { return MaterialType::CustomShader; }
};

// ---------------------------------------------------------------------------
// Pipeline Manager
// ---------------------------------------------------------------------------
class PipelineManager {
public:
    static PipelineManager& instance();

    sg_pipeline get_or_create(uint64_t key, const sg_pipeline_desc& desc_template);
    void release_all();
    ~PipelineManager();

    static uint64_t make_key(
        uint32_t shader_id,
        SideMode side,
        bool depth_write,
        bool depth_test,
        BlendMode blend_mode,
        bool wireframe = false,
        bool is_instanced = false,
        int sample_count = 1
    );

private:
    std::unordered_map<uint64_t, sg_pipeline> cache_;
};

} // namespace engine
