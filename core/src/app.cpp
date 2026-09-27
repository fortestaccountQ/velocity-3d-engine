#include "engine/app.hpp"

#include "sokol_app.h"
#include "sokol_gfx.h"
#include "sokol_glue.h"
#include "sokol_log.h"

#include <iostream>

namespace engine {

// ---------------------------------------------------------------------------
// Uniform Buffer Structs matching shader layouts
// ---------------------------------------------------------------------------
struct VSParams {
    glm::mat4 mvp;
    glm::mat4 model;
    glm::mat4 normal_mat;
};

struct FSParams {
    glm::vec4 light_dir;        // xyz = dir, w = intensity
    glm::vec4 light_color;      // rgb = color, w = unused
    glm::vec4 ambient_color;    // rgb = ambient, w = unused
    glm::vec4 eye_pos;          // xyz = camera position, w = unused
    glm::vec4 material_color;   // rgba base_color
    glm::vec4 material_params;  // x = roughness, y = metallic, z = uv_scale.x, w = uv_scale.y
};

// ---------------------------------------------------------------------------
// Shaders for various platforms with PBR-lite Texturing & Metallic-Roughness
// ---------------------------------------------------------------------------
#if defined(SOKOL_D3D11)
static const char* hlsl_vs =
    "cbuffer vs_params : register(b0) {\n"
    "    float4x4 mvp;\n"
    "    float4x4 model;\n"
    "    float4x4 normal_mat;\n"
    "};\n"
    "struct vs_in {\n"
    "    float3 pos : POSITION;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "struct vs_out {\n"
    "    float4 color : COLOR0;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float3 world_pos : TEXCOORD1;\n"
    "    float4 pos : SV_Position;\n"
    "};\n"
    "vs_out main(vs_in inp) {\n"
    "    vs_out outp;\n"
    "    outp.pos = mul(mvp, float4(inp.pos, 1.0));\n"
    "    outp.world_pos = mul(model, float4(inp.pos, 1.0)).xyz;\n"
    "    outp.normal = mul((float3x3)normal_mat, inp.normal);\n"
    "    outp.uv = inp.uv;\n"
    "    outp.color = inp.color;\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_fs =
    "cbuffer fs_params : register(b1) {\n"
    "    float4 light_dir;\n"
    "    float4 light_color;\n"
    "    float4 ambient_color;\n"
    "    float4 eye_pos;\n"
    "    float4 material_color;\n"
    "    float4 material_params;\n" // x=roughness, y=metallic, zw=uv_scale
    "};\n"
    "Texture2D tex_albedo : register(t0);\n"
    "SamplerState smp_albedo : register(s0);\n"
    "struct ps_in {\n"
    "    float4 color : COLOR0;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float3 world_pos : TEXCOORD1;\n"
    "};\n"
    "float4 main(ps_in inp) : SV_Target0 {\n"
    "    float2 uv = inp.uv * material_params.zw;\n"
    "    float4 tex_sample = tex_albedo.Sample(smp_albedo, uv);\n"
    "    float3 albedo = tex_sample.rgb * inp.color.rgb * material_color.rgb;\n"
    "    float roughness = clamp(material_params.x, 0.04, 1.0);\n"
    "    float metallic = clamp(material_params.y, 0.0, 1.0);\n"
    "    float3 N = normalize(inp.normal);\n"
    "    float3 L = normalize(-light_dir.xyz);\n"
    "    float3 V = normalize(eye_pos.xyz - inp.world_pos);\n"
    "    float3 H = normalize(L + V);\n"
    "    float NdotL = max(dot(N, L), 0.0);\n"
    "    float NdotH = max(dot(N, H), 0.0);\n"
    "    float VdotH = max(dot(V, H), 0.0);\n"
    "    float3 F0 = lerp(float3(0.04, 0.04, 0.04), albedo, metallic);\n"
    "    float3 F = F0 + (1.0 - F0) * pow(1.0 - VdotH, 5.0);\n"
    "    float shininess = 2.0 / (pow(roughness, 4.0) + 0.0001) - 2.0;\n"
    "    shininess = clamp(shininess, 2.0, 512.0);\n"
    "    float3 specular = float3(0.0, 0.0, 0.0);\n"
    "    if (NdotL > 0.0) {\n"
    "        float spec_factor = pow(NdotH, shininess);\n"
    "        specular = F * spec_factor * light_color.rgb * light_dir.w;\n"
    "    }\n"
    "    float3 kD = (1.0 - metallic) * (float3(1.0, 1.0, 1.0) - F);\n"
    "    float3 diffuse = kD * albedo * NdotL * light_color.rgb * light_dir.w;\n"
    "    float3 ambient = ambient_color.rgb * albedo * (1.0 - 0.5 * metallic);\n"
    "    float3 final_color = ambient + diffuse + specular;\n"
    "    return float4(final_color, tex_sample.a * inp.color.a * material_color.a);\n"
    "}\n";

#elif defined(SOKOL_METAL)
static const char* metal_src =
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "struct vs_params_t {\n"
    "    float4x4 mvp;\n"
    "    float4x4 model;\n"
    "    float4x4 normal_mat;\n"
    "};\n"
    "struct fs_params_t {\n"
    "    float4 light_dir;\n"
    "    float4 light_color;\n"
    "    float4 ambient_color;\n"
    "    float4 eye_pos;\n"
    "    float4 material_color;\n"
    "    float4 material_params;\n"
    "};\n"
    "struct vs_in {\n"
    "    float3 position [[attribute(0)]];\n"
    "    float3 normal   [[attribute(1)]];\n"
    "    float2 uv       [[attribute(2)]];\n"
    "    float4 color0   [[attribute(3)]];\n"
    "};\n"
    "struct vs_out {\n"
    "    float4 pos [[position]];\n"
    "    float4 color;\n"
    "    float3 normal;\n"
    "    float2 uv;\n"
    "    float3 world_pos;\n"
    "};\n"
    "vertex vs_out vs_main(vs_in in [[stage_in]], constant vs_params_t& params [[buffer(0)]]) {\n"
    "    vs_out out;\n"
    "    out.pos = params.mvp * float4(in.position, 1.0);\n"
    "    out.world_pos = (params.model * float4(in.position, 1.0)).xyz;\n"
    "    out.normal = float3x3(params.normal_mat[0].xyz, params.normal_mat[1].xyz, params.normal_mat[2].xyz) * in.normal;\n"
    "    out.uv = in.uv;\n"
    "    out.color = in.color0;\n"
    "    return out;\n"
    "}\n"
    "fragment float4 fs_main(\n"
    "    vs_out in [[stage_in]],\n"
    "    constant fs_params_t& params [[buffer(0)]],\n"
    "    texture2d<float> tex_albedo [[texture(0)]],\n"
    "    sampler smp_albedo [[sampler(0)]]\n"
    ") {\n"
    "    float2 uv = in.uv * params.material_params.zw;\n"
    "    float4 tex_sample = tex_albedo.sample(smp_albedo, uv);\n"
    "    float3 albedo = tex_sample.rgb * in.color.rgb * params.material_color.rgb;\n"
    "    float roughness = clamp(params.material_params.x, 0.04f, 1.0f);\n"
    "    float metallic = clamp(params.material_params.y, 0.0f, 1.0f);\n"
    "    float3 N = normalize(in.normal);\n"
    "    float3 L = normalize(-params.light_dir.xyz);\n"
    "    float3 V = normalize(params.eye_pos.xyz - in.world_pos);\n"
    "    float3 H = normalize(L + V);\n"
    "    float NdotL = max(dot(N, L), 0.0f);\n"
    "    float NdotH = max(dot(N, H), 0.0f);\n"
    "    float VdotH = max(dot(V, H), 0.0f);\n"
    "    float3 F0 = mix(float3(0.04f), albedo, metallic);\n"
    "    float3 F = F0 + (1.0f - F0) * pow(1.0f - VdotH, 5.0f);\n"
    "    float shininess = 2.0f / (pow(roughness, 4.0f) + 0.0001f) - 2.0f;\n"
    "    shininess = clamp(shininess, 2.0f, 512.0f);\n"
    "    float3 specular = float3(0.0f);\n"
    "    if (NdotL > 0.0f) {\n"
    "        float spec_factor = pow(NdotH, shininess);\n"
    "        specular = F * spec_factor * params.light_color.rgb * params.light_dir.w;\n"
    "    }\n"
    "    float3 kD = (1.0f - metallic) * (float3(1.0f) - F);\n"
    "    float3 diffuse = kD * albedo * NdotL * params.light_color.rgb * params.light_dir.w;\n"
    "    float3 ambient = params.ambient_color.rgb * albedo * (1.0f - 0.5f * metallic);\n"
    "    return float4(ambient + diffuse + specular, tex_sample.a * in.color.a * params.material_color.a);\n"
    "}\n";

#elif defined(SOKOL_GLES3)
static const char* glsl_vs =
    "#version 300 es\n"
    "layout(location=0) in vec3 position;\n"
    "layout(location=1) in vec3 normal;\n"
    "layout(location=2) in vec2 uv;\n"
    "layout(location=3) in vec4 color0;\n"
    "uniform mat4 mvp;\n"
    "uniform mat4 model;\n"
    "uniform mat4 normal_mat;\n"
    "out vec4 color;\n"
    "out vec3 v_normal;\n"
    "out vec2 v_uv;\n"
    "out vec3 v_world_pos;\n"
    "void main() {\n"
    "    gl_Position = mvp * vec4(position, 1.0);\n"
    "    v_world_pos = (model * vec4(position, 1.0)).xyz;\n"
    "    v_normal = mat3(normal_mat) * normal;\n"
    "    v_uv = uv;\n"
    "    color = color0;\n"
    "}\n";

static const char* glsl_fs =
    "#version 300 es\n"
    "precision mediump float;\n"
    "in vec4 color;\n"
    "in vec3 v_normal;\n"
    "in vec2 v_uv;\n"
    "in vec3 v_world_pos;\n"
    "out vec4 frag_color;\n"
    "uniform vec4 light_dir;\n"
    "uniform vec4 light_color;\n"
    "uniform vec4 ambient_color;\n"
    "uniform vec4 eye_pos;\n"
    "uniform vec4 material_color;\n"
    "uniform vec4 material_params;\n"
    "uniform sampler2D tex_albedo;\n"
    "void main() {\n"
    "    vec2 uv = v_uv * material_params.zw;\n"
    "    vec4 tex_sample = texture(tex_albedo, uv);\n"
    "    vec3 albedo = tex_sample.rgb * color.rgb * material_color.rgb;\n"
    "    float roughness = clamp(material_params.x, 0.04, 1.0);\n"
    "    float metallic = clamp(material_params.y, 0.0, 1.0);\n"
    "    vec3 N = normalize(v_normal);\n"
    "    vec3 L = normalize(-light_dir.xyz);\n"
    "    vec3 V = normalize(eye_pos.xyz - v_world_pos);\n"
    "    vec3 H = normalize(L + V);\n"
    "    float NdotL = max(dot(N, L), 0.0);\n"
    "    float NdotH = max(dot(N, H), 0.0);\n"
    "    float VdotH = max(dot(V, H), 0.0);\n"
    "    vec3 F0 = mix(vec3(0.04), albedo, metallic);\n"
    "    vec3 F = F0 + (1.0 - F0) * pow(1.0 - VdotH, 5.0);\n"
    "    float shininess = 2.0 / (pow(roughness, 4.0) + 0.0001) - 2.0;\n"
    "    shininess = clamp(shininess, 2.0, 512.0);\n"
    "    vec3 specular = vec3(0.0);\n"
    "    if (NdotL > 0.0) {\n"
    "        float spec_factor = pow(NdotH, shininess);\n"
    "        specular = F * spec_factor * light_color.rgb * light_dir.w;\n"
    "    }\n"
    "    vec3 kD = (1.0 - metallic) * (vec3(1.0) - F);\n"
    "    vec3 diffuse = kD * albedo * NdotL * light_color.rgb * light_dir.w;\n"
    "    vec3 ambient = ambient_color.rgb * albedo * (1.0 - 0.5 * metallic);\n"
    "    frag_color = vec4(ambient + diffuse + specular, tex_sample.a * color.a * material_color.a);\n"
    "}\n";

#else // Desktop GLCORE
static const char* glsl_vs =
    "#version 330\n"
    "layout(location=0) in vec3 position;\n"
    "layout(location=1) in vec3 normal;\n"
    "layout(location=2) in vec2 uv;\n"
    "layout(location=3) in vec4 color0;\n"
    "uniform mat4 mvp;\n"
    "uniform mat4 model;\n"
    "uniform mat4 normal_mat;\n"
    "out vec4 color;\n"
    "out vec3 v_normal;\n"
    "out vec2 v_uv;\n"
    "out vec3 v_world_pos;\n"
    "void main() {\n"
    "    gl_Position = mvp * vec4(position, 1.0);\n"
    "    v_world_pos = (model * vec4(position, 1.0)).xyz;\n"
    "    v_normal = mat3(normal_mat) * normal;\n"
    "    v_uv = uv;\n"
    "    color = color0;\n"
    "}\n";

static const char* glsl_fs =
    "#version 330\n"
    "in vec4 color;\n"
    "in vec3 v_normal;\n"
    "in vec2 v_uv;\n"
    "in vec3 v_world_pos;\n"
    "out vec4 frag_color;\n"
    "uniform vec4 light_dir;\n"
    "uniform vec4 light_color;\n"
    "uniform vec4 ambient_color;\n"
    "uniform vec4 eye_pos;\n"
    "uniform vec4 material_color;\n"
    "uniform vec4 material_params;\n"
    "uniform sampler2D tex_albedo;\n"
    "void main() {\n"
    "    vec2 uv = v_uv * material_params.zw;\n"
    "    vec4 tex_sample = texture(tex_albedo, uv);\n"
    "    vec3 albedo = tex_sample.rgb * color.rgb * material_color.rgb;\n"
    "    float roughness = clamp(material_params.x, 0.04, 1.0);\n"
    "    float metallic = clamp(material_params.y, 0.0, 1.0);\n"
    "    vec3 N = normalize(v_normal);\n"
    "    vec3 L = normalize(-light_dir.xyz);\n"
    "    vec3 V = normalize(eye_pos.xyz - v_world_pos);\n"
    "    vec3 H = normalize(L + V);\n"
    "    float NdotL = max(dot(N, L), 0.0);\n"
    "    float NdotH = max(dot(N, H), 0.0);\n"
    "    float VdotH = max(dot(V, H), 0.0);\n"
    "    vec3 F0 = mix(vec3(0.04), albedo, metallic);\n"
    "    vec3 F = F0 + (1.0 - F0) * pow(1.0 - VdotH, 5.0);\n"
    "    float shininess = 2.0 / (pow(roughness, 4.0) + 0.0001) - 2.0;\n"
    "    shininess = clamp(shininess, 2.0, 512.0);\n"
    "    vec3 specular = vec3(0.0);\n"
    "    if (NdotL > 0.0) {\n"
    "        float spec_factor = pow(NdotH, shininess);\n"
    "        specular = F * spec_factor * light_color.rgb * light_dir.w;\n"
    "    }\n"
    "    vec3 kD = (1.0 - metallic) * (vec3(1.0) - F);\n"
    "    vec3 diffuse = kD * albedo * NdotL * light_color.rgb * light_dir.w;\n"
    "    vec3 ambient = ambient_color.rgb * albedo * (1.0 - 0.5 * metallic);\n"
    "    frag_color = vec4(ambient + diffuse + specular, tex_sample.a * color.a * material_color.a);\n"
    "}\n";
#endif

// ---------------------------------------------------------------------------
// EngineApp Implementation
// ---------------------------------------------------------------------------
EngineApp::EngineApp() = default;

EngineApp::EngineApp(const std::string& title, int width, int height) {
    init(title, width, height);
}

EngineApp::~EngineApp() {
    close();
}

void EngineApp::init(const std::string& title, int width, int height) {
    config_.title = title;
    config_.width = width;
    config_.height = height;
    initialized_ = true;
}

void EngineApp::set_clear_color(float r, float g, float b, float a) {
    config_.clear_color = { r, g, b, a };
}

void EngineApp::set_update_callback(UpdateCallback callback) {
    update_callback_ = std::move(callback);
}

void EngineApp::init_pipeline_and_shaders() {
    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "NORMAL";
    shd_desc.attrs[2].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[2].hlsl_sem_index = 0;
    shd_desc.attrs[3].hlsl_sem_name = "COLOR";
    shd_desc.attrs[3].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(VSParams);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.uniform_blocks[1].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[1].size = sizeof(FSParams);
    shd_desc.uniform_blocks[1].hlsl_register_b_n = 1;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;

#elif defined(SOKOL_METAL)
    shd_desc.vertex_func.source = metal_src;
    shd_desc.vertex_func.entry = "vs_main";
    shd_desc.fragment_func.source = metal_src;
    shd_desc.fragment_func.entry = "fs_main";

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(VSParams);
    shd_desc.uniform_blocks[0].msl_buffer_n = 0;

    shd_desc.uniform_blocks[1].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[1].size = sizeof(FSParams);
    shd_desc.uniform_blocks[1].msl_buffer_n = 1;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.msl_texture_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].msl_sampler_n = 0;

#else // GLCORE / GLES3
    shd_desc.vertex_func.source = glsl_vs;
    shd_desc.fragment_func.source = glsl_fs;

    shd_desc.attrs[0].glsl_name = "position";
    shd_desc.attrs[1].glsl_name = "normal";
    shd_desc.attrs[2].glsl_name = "uv";
    shd_desc.attrs[3].glsl_name = "color0";

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(VSParams);
    shd_desc.uniform_blocks[0].glsl_uniforms[0] = { SG_UNIFORMTYPE_MAT4, 1, "mvp" };
    shd_desc.uniform_blocks[0].glsl_uniforms[1] = { SG_UNIFORMTYPE_MAT4, 1, "model" };
    shd_desc.uniform_blocks[0].glsl_uniforms[2] = { SG_UNIFORMTYPE_MAT4, 1, "normal_mat" };

    shd_desc.uniform_blocks[1].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[1].size = sizeof(FSParams);
    shd_desc.uniform_blocks[1].glsl_uniforms[0] = { SG_UNIFORMTYPE_FLOAT4, 1, "light_dir" };
    shd_desc.uniform_blocks[1].glsl_uniforms[1] = { SG_UNIFORMTYPE_FLOAT4, 1, "light_color" };
    shd_desc.uniform_blocks[1].glsl_uniforms[2] = { SG_UNIFORMTYPE_FLOAT4, 1, "ambient_color" };
    shd_desc.uniform_blocks[1].glsl_uniforms[3] = { SG_UNIFORMTYPE_FLOAT4, 1, "eye_pos" };
    shd_desc.uniform_blocks[1].glsl_uniforms[4] = { SG_UNIFORMTYPE_FLOAT4, 1, "material_color" };
    shd_desc.uniform_blocks[1].glsl_uniforms[5] = { SG_UNIFORMTYPE_FLOAT4, 1, "material_params" };

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;

    shd_desc.texture_sampler_pairs[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.texture_sampler_pairs[0].view_slot = 0;
    shd_desc.texture_sampler_pairs[0].sampler_slot = 0;
    shd_desc.texture_sampler_pairs[0].glsl_name = "tex_albedo";
#endif
    shd_desc.label = "pbr-lite-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;
    sg_resource_state shd_state = sg_query_shader_state(shd);
    if (shd_state != SG_RESOURCESTATE_VALID) {
        std::cerr << "[Sokol GFX ERROR] Shader creation failed, state: " << static_cast<int>(shd_state) << std::endl;
    }

    // Pipeline with Depth Test
    sg_pipeline_desc pip_desc{};
    pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3; // pos
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3; // normal
    pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2; // uv
    pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4; // color
    pip_desc.shader = shd;
    pip_desc.index_type = SG_INDEXTYPE_UINT16;
    pip_desc.depth.compare = SG_COMPAREFUNC_LESS_EQUAL;
    pip_desc.depth.write_enabled = true;
    pip_desc.cull_mode = SG_CULLMODE_NONE;
    pip_desc.label = "pbr-lite-pipeline";
    sg_pipeline pip = sg_make_pipeline(&pip_desc);
    pip_id_ = pip.id;
    sg_resource_state pip_state = sg_query_pipeline_state(pip);
    if (pip_state != SG_RESOURCESTATE_VALID) {
        std::cerr << "[Sokol GFX ERROR] Pipeline creation failed, state: " << static_cast<int>(pip_state) << std::endl;
    }
}

void EngineApp::on_init() {
    sg_desc desc{};
    desc.environment = sglue_environment();
    desc.logger.func = slog_func;
    sg_setup(&desc);

    init_pipeline_and_shaders();
}

void EngineApp::on_frame() {
    // 1. Calculate delta time (dt)
    auto now = std::chrono::steady_clock::now();
    double dt = 0.0;
    if (has_last_frame_) {
        dt = std::chrono::duration<double>(now - last_frame_time_).count();
        if (dt > 0.1) dt = 0.1;
    } else {
        has_last_frame_ = true;
        dt = 1.0 / 60.0;
    }
    last_frame_time_ = now;

    // 2. Invoke Python frame update callback with GIL
    if (update_callback_) {
        try {
            update_callback_(dt);
        } catch (const std::exception& e) {
            std::cerr << "[Engine] Exception in Python update callback: " << e.what() << "\n";
        }
    }

    // 3. Update Camera Aspect & Matrix
    float w = sapp_widthf();
    float h = sapp_heightf();
    camera_.aspect = (h > 0.0f) ? (w / h) : 1.333333f;
    glm::mat4 vp = camera_.view_projection_matrix();

    // 4. Begin render pass with color clear and depth clear
    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_CLEAR;
    pass.action.colors[0].clear_value = {
        config_.clear_color[0],
        config_.clear_color[1],
        config_.clear_color[2],
        config_.clear_color[3]
    };
    pass.action.depth.load_action = SG_LOADACTION_CLEAR;
    pass.action.depth.clear_value = 1.0f;
    pass.swapchain = sglue_swapchain();

    sg_begin_pass(&pass);

    if (pip_id_ != 0) {
        sg_pipeline pip{pip_id_};
        sg_apply_pipeline(pip);

        // Prepare lighting uniform
        FSParams fs_params{};
        fs_params.light_dir = glm::vec4(scene_.light.direction, scene_.light.intensity);
        fs_params.light_color = glm::vec4(scene_.light.color, 1.0f);
        fs_params.ambient_color = glm::vec4(scene_.light.ambient, 1.0f);
        fs_params.eye_pos = glm::vec4(camera_.position, 1.0f);

        auto default_checker = scene_.default_checker_texture();
        if (default_checker) {
            default_checker->ensure_gpu_resources();
        }
        auto default_mat = scene_.default_material();

        // 5. Draw all visible entities in Scene
        for (const auto& entity : scene_.entities()) {
            if (!entity || !entity->visible) {
                continue;
            }

            if (!entity->mesh) {
                continue;
            }

            if (!entity->mesh || !entity->mesh->ensure_gpu_buffers()) {
                continue;
            }

            // Material resolution
            auto mat = entity->material ? entity->material : default_mat;
            auto tex = (mat && mat->albedo_map) ? mat->albedo_map : default_checker;
            if (tex) {
                tex->ensure_gpu_resources();
            }
            if (!tex || !tex->is_valid()) {
                tex = default_checker;
            }
            if (!tex || !tex->is_valid()) {
                continue;
            }

            // Compute MVP and Normal matrices
            glm::mat4 model = entity->world_model_matrix();
            glm::mat4 normal_mat = entity->world_normal_matrix();
            glm::mat4 mvp = vp * model;

            VSParams vs_params{ mvp, model, normal_mat };
            fs_params.material_color = mat->base_color;
            fs_params.material_params = glm::vec4(mat->roughness, mat->metallic, mat->uv_scale.x, mat->uv_scale.y);

            sg_bindings bind{};
            bind.vertex_buffers[0] = sg_buffer{ entity->mesh->vbuf_id };
            bind.index_buffer = sg_buffer{ entity->mesh->ibuf_id };
            bind.views[0] = sg_view{ tex->view_id };
            bind.samplers[0] = sg_sampler{ tex->sampler_id };
            sg_apply_bindings(&bind);

            sg_apply_uniforms(0, SG_RANGE_REF(vs_params));
            sg_apply_uniforms(1, SG_RANGE_REF(fs_params));
            sg_draw(0, entity->mesh->num_indices, 1);
        }
    }

    sg_end_pass();
    sg_commit();

    // 6. Reset per-frame input transients
    input_.post_frame();
}

void EngineApp::on_cleanup() {
    update_callback_ = nullptr;
    scene_.clear();

    if (pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{pip_id_});
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        sg_destroy_shader(sg_shader{shd_id_});
        shd_id_ = 0;
    }

    sg_shutdown();
}

void EngineApp::on_event(const void* raw_event) {
    if (!raw_event) return;
    const auto* ev = static_cast<const sapp_event*>(raw_event);

    switch (ev->type) {
        case SAPP_EVENTTYPE_KEY_DOWN:
            if (ev->key_code == SAPP_KEYCODE_ESCAPE) {
                sapp_request_quit();
            }
            input_.on_key_down(ev->key_code);
            break;

        case SAPP_EVENTTYPE_KEY_UP:
            input_.on_key_up(ev->key_code);
            break;

        case SAPP_EVENTTYPE_MOUSE_MOVE:
            input_.on_mouse_move(ev->mouse_x, ev->mouse_y, ev->mouse_dx, ev->mouse_dy);
            break;

        case SAPP_EVENTTYPE_MOUSE_DOWN:
            input_.on_mouse_down(ev->mouse_button);
            break;

        case SAPP_EVENTTYPE_MOUSE_UP:
            input_.on_mouse_up(ev->mouse_button);
            break;

        default:
            break;
    }
}

void EngineApp::run() {
    sapp_desc desc{};
    desc.user_data = this;
    desc.init_userdata_cb = [](void* ud) {
        if (ud) static_cast<EngineApp*>(ud)->on_init();
    };
    desc.frame_userdata_cb = [](void* ud) {
        if (ud) static_cast<EngineApp*>(ud)->on_frame();
    };
    desc.cleanup_userdata_cb = [](void* ud) {
        if (ud) static_cast<EngineApp*>(ud)->on_cleanup();
    };
    desc.event_userdata_cb = [](const sapp_event* ev, void* ud) {
        if (ud) static_cast<EngineApp*>(ud)->on_event(ev);
    };

    desc.width = config_.width;
    desc.height = config_.height;
    desc.window_title = config_.title.c_str();
    desc.logger.func = slog_func;
    desc.icon.sokol_default = true;

    running_ = true;
    sapp_run(&desc);
    running_ = false;
}

void EngineApp::close() {
    if (running_) {
        sapp_request_quit();
    }
}

} // namespace engine
