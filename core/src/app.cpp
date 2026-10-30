#include "engine/app.hpp"
#include "engine/asset_io.hpp"
#include "engine/render_target.hpp"
#include "engine/post_process.hpp"
#include "engine/cube_texture.hpp"
#include "engine/sky.hpp"
#include "engine/cube_camera.hpp"
#include "engine/helpers.hpp"
#include "engine/lod.hpp"
#include "engine/animation.hpp"
#include "engine/skinned_mesh.hpp"
#include "engine/sprite.hpp"
#include "engine/points.hpp"
#include "engine/particle.hpp"

#include "sokol_app.h"
#include "sokol_gfx.h"
#include "sokol_glue.h"
#include "sokol_log.h"

#include <iostream>
#include <vector>
#include <cstdio>
#include <cstring>
#include <algorithm>
#include <thread>
#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#if defined(SOKOL_D3D11)
#include <d3d11.h>
#endif
#endif

namespace engine {

// ---------------------------------------------------------------------------
// Uniform Buffer Structs matching shader layouts
// ---------------------------------------------------------------------------
struct VSParams {
    glm::mat4 mvp;
    glm::mat4 model;
    glm::mat4 normal_mat;
    glm::mat4 light_mvp;
};

struct alignas(16) FSParams {
    glm::vec4 eye_pos;            // xyz = camera position, w = unused
    glm::vec4 material_color;     // rgba base_color
    glm::vec4 material_params;    // x = roughness, y = metallic, zw = uv_scale
    glm::vec4 material_uv_offset; // xy = uv_offset, z = normal_scale, w = ao_intensity
    glm::vec4 emissive_params;    // xyz = emissive_color * emissive_intensity, w = alpha_cutoff
    glm::vec4 texture_flags;      // x = has_normal_map, y = has_mr_map, z = has_emissive_map, w = has_ao_map
    glm::vec4 fog_color;          // rgb = fog color, w = tone_mapping_enabled (1.0 or 0.0)
    glm::vec4 fog_params;         // x = fog_type (0=off, 1=linear, 2=exp2), y = near, z = far, w = density
    glm::vec4 extra_params;       // x = material_type, y = toon_steps/shininess, z = opacity, w = transparent
};

struct ShadowVSParams {
    glm::mat4 light_mvp;
};

struct InstancedVSParams {
    glm::mat4 view_proj;
    glm::mat4 light_vp;
};

struct LineVSParams {
    glm::mat4 mvp;
};

struct HUDVertex {
    glm::vec2 pos;
    glm::vec4 color;
};

struct HUDVSParams {
    glm::mat4 ortho_proj;
};

struct SkyboxVSParams {
    glm::mat4 view_proj;
};

struct alignas(16) ProcSkyFSParams {
    glm::vec4 sun_dir_turbidity; // xyz = sun_dir, w = turbidity
    glm::vec4 rayleigh_params;   // rgb = rayleigh_color, w = rayleigh
    glm::vec4 mie_params;        // rgb = mie_color, w = mie_coefficient
    glm::vec4 sky_misc;          // x = mie_directional_g, y = time_of_day, zw = unused
};

// ---------------------------------------------------------------------------
// Standard 8x8 ASCII Bitmap Font (ASCII 32 ' ' to 126 '~')
// ---------------------------------------------------------------------------
static const uint8_t FONT_8X8[95][8] = {
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00}, // ' '
    {0x18,0x3C,0x3C,0x18,0x18,0x00,0x18,0x00}, // !
    {0x66,0x66,0x24,0x00,0x00,0x00,0x00,0x00}, // "
    {0x6C,0x6C,0xFE,0x6C,0xFE,0x6C,0x6C,0x00}, // #
    {0x18,0x3E,0x60,0x3C,0x06,0x7C,0x18,0x00}, // $
    {0x00,0x63,0x66,0x0C,0x18,0x33,0x63,0x00}, // %
    {0x38,0x6C,0x38,0x76,0xDC,0xCC,0x76,0x00}, // &
    {0x18,0x18,0x30,0x00,0x00,0x00,0x00,0x00}, // '
    {0x0C,0x18,0x30,0x30,0x30,0x18,0x0C,0x00}, // (
    {0x30,0x18,0x0C,0x0C,0x0C,0x18,0x30,0x00}, // )
    {0x00,0x66,0x3C,0xFF,0x3C,0x66,0x00,0x00}, // *
    {0x00,0x18,0x18,0x7E,0x18,0x18,0x00,0x00}, // +
    {0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x30}, // ,
    {0x00,0x00,0x00,0x7E,0x00,0x00,0x00,0x00}, // -
    {0x00,0x00,0x00,0x00,0x00,0x18,0x18,0x00}, // .
    {0x06,0x0C,0x18,0x30,0x60,0xC0,0x80,0x00}, // /
    {0x3C,0x66,0x6E,0x76,0x66,0x66,0x3C,0x00}, // 0
    {0x18,0x38,0x18,0x18,0x18,0x18,0x7E,0x00}, // 1
    {0x3C,0x66,0x06,0x0C,0x18,0x30,0x7E,0x00}, // 2
    {0x3C,0x66,0x06,0x1C,0x06,0x66,0x3C,0x00}, // 3
    {0x0C,0x1C,0x3C,0x6C,0xFE,0x0C,0x0C,0x00}, // 4
    {0x7E,0x60,0x7C,0x06,0x06,0x66,0x3C,0x00}, // 5
    {0x1C,0x30,0x60,0x7C,0x66,0x66,0x3C,0x00}, // 6
    {0x7E,0x06,0x0C,0x18,0x30,0x30,0x30,0x00}, // 7
    {0x3C,0x66,0x66,0x3C,0x66,0x66,0x3C,0x00}, // 8
    {0x3C,0x66,0x66,0x3E,0x06,0x0C,0x38,0x00}, // 9
    {0x00,0x18,0x18,0x00,0x00,0x18,0x18,0x00}, // :
    {0x00,0x18,0x18,0x00,0x00,0x18,0x18,0x30}, // ;
    {0x0E,0x1C,0x38,0x70,0x38,0x1C,0x0E,0x00}, // <
    {0x00,0x7E,0x00,0x7E,0x00,0x00,0x00,0x00}, // =
    {0x70,0x38,0x1C,0x0E,0x1C,0x38,0x70,0x00}, // >
    {0x3C,0x66,0x06,0x0C,0x18,0x00,0x18,0x00}, // ?
    {0x3C,0x66,0x6E,0x6A,0x6E,0x60,0x3C,0x00}, // @
    {0x18,0x3C,0x66,0x7E,0x66,0x66,0x66,0x00}, // A
    {0x7C,0x66,0x66,0x7C,0x66,0x66,0x7C,0x00}, // B
    {0x3C,0x66,0x60,0x60,0x60,0x66,0x3C,0x00}, // C
    {0x78,0x6C,0x66,0x66,0x66,0x6C,0x78,0x00}, // D
    {0x7E,0x60,0x60,0x7C,0x60,0x60,0x7E,0x00}, // E
    {0x7E,0x60,0x60,0x7C,0x60,0x60,0x60,0x00}, // F
    {0x3C,0x66,0x60,0x6E,0x66,0x66,0x3A,0x00}, // G
    {0x66,0x66,0x66,0x7E,0x66,0x66,0x66,0x00}, // H
    {0x3C,0x18,0x18,0x18,0x18,0x18,0x3C,0x00}, // I
    {0x0E,0x06,0x06,0x06,0x06,0x66,0x3C,0x00}, // J
    {0x66,0x6C,0x78,0x70,0x78,0x6C,0x66,0x00}, // K
    {0x60,0x60,0x60,0x60,0x60,0x60,0x7E,0x00}, // L
    {0x63,0x77,0x7F,0x6B,0x63,0x63,0x63,0x00}, // M
    {0x66,0x76,0x7E,0x7E,0x6E,0x66,0x66,0x00}, // N
    {0x3C,0x66,0x66,0x66,0x66,0x66,0x3C,0x00}, // O
    {0x7C,0x66,0x66,0x7C,0x60,0x60,0x60,0x00}, // P
    {0x3C,0x66,0x66,0x66,0x6A,0x6C,0x36,0x00}, // Q
    {0x7C,0x66,0x66,0x7C,0x6C,0x66,0x63,0x00}, // R
    {0x3C,0x66,0x60,0x3C,0x06,0x66,0x3C,0x00}, // S
    {0x7E,0x18,0x18,0x18,0x18,0x18,0x18,0x00}, // T
    {0x66,0x66,0x66,0x66,0x66,0x66,0x3C,0x00}, // U
    {0x66,0x66,0x66,0x66,0x66,0x3C,0x18,0x00}, // V
    {0x63,0x63,0x63,0x6B,0x7F,0x77,0x63,0x00}, // W
    {0x66,0x66,0x3C,0x18,0x3C,0x66,0x66,0x00}, // X
    {0x66,0x66,0x66,0x3C,0x18,0x18,0x18,0x00}, // Y
    {0x7E,0x06,0x0C,0x18,0x30,0x60,0x7E,0x00}, // Z
    {0x3C,0x30,0x30,0x30,0x30,0x30,0x3C,0x00}, // [
    {0xC0,0x60,0x30,0x18,0x0C,0x06,0x02,0x00}, // "\"
    {0x3C,0x0C,0x0C,0x0C,0x0C,0x0C,0x3C,0x00}, // ]
    {0x10,0x38,0x6C,0xC6,0x00,0x00,0x00,0x00}, // ^
    {0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF}, // _
    {0x30,0x18,0x0C,0x00,0x00,0x00,0x00,0x00}, // `
    {0x00,0x00,0x3C,0x06,0x3E,0x66,0x3B,0x00}, // a
    {0x60,0x60,0x7C,0x66,0x66,0x66,0x7C,0x00}, // b
    {0x00,0x00,0x3C,0x66,0x60,0x66,0x3C,0x00}, // c
    {0x06,0x06,0x3E,0x66,0x66,0x66,0x3E,0x00}, // d
    {0x00,0x00,0x3C,0x66,0x7E,0x60,0x3C,0x00}, // e
    {0x1C,0x30,0x78,0x30,0x30,0x30,0x30,0x00}, // f
    {0x00,0x00,0x3B,0x66,0x66,0x3E,0x06,0x3C}, // g
    {0x60,0x60,0x7C,0x66,0x66,0x66,0x66,0x00}, // h
    {0x18,0x00,0x38,0x18,0x18,0x18,0x3C,0x00}, // i
    {0x06,0x00,0x06,0x06,0x06,0x66,0x3C,0x00}, // j
    {0x60,0x60,0x66,0x6C,0x78,0x6C,0x66,0x00}, // k
    {0x38,0x18,0x18,0x18,0x18,0x18,0x3C,0x00}, // l
    {0x00,0x00,0x66,0x7F,0x7F,0x6B,0x63,0x00}, // m
    {0x00,0x00,0x7C,0x66,0x66,0x66,0x66,0x00}, // n
    {0x00,0x00,0x3C,0x66,0x66,0x66,0x3C,0x00}, // o
    {0x00,0x00,0x7C,0x66,0x66,0x7C,0x60,0x60}, // p
    {0x00,0x00,0x3E,0x66,0x66,0x3E,0x06,0x06}, // q
    {0x00,0x00,0x7C,0x66,0x60,0x60,0x60,0x00}, // r
    {0x00,0x00,0x3E,0x60,0x3C,0x06,0x7C,0x00}, // s
    {0x18,0x18,0x7E,0x18,0x18,0x18,0x0E,0x00}, // t
    {0x00,0x00,0x66,0x66,0x66,0x66,0x3B,0x00}, // u
    {0x00,0x00,0x66,0x66,0x66,0x3C,0x18,0x00}, // v
    {0x00,0x00,0x63,0x6B,0x7F,0x36,0x36,0x00}, // w
    {0x00,0x00,0x66,0x3C,0x18,0x3C,0x66,0x00}, // x
    {0x00,0x00,0x66,0x66,0x66,0x3E,0x06,0x3C}, // y
    {0x00,0x00,0x7E,0x0C,0x18,0x30,0x7E,0x00}, // z
    {0x0E,0x18,0x18,0x70,0x18,0x18,0x0E,0x00}, // {
    {0x18,0x18,0x18,0x00,0x18,0x18,0x18,0x00}, // |
    {0x70,0x18,0x18,0x0E,0x18,0x18,0x70,0x00}, // }
    {0x76,0xDC,0x00,0x00,0x00,0x00,0x00,0x00}, // ~
};

// ---------------------------------------------------------------------------
// Shaders with PBR-lite Texturing, Hemispheric Ambient & Dynamic Soft Shadows
// ---------------------------------------------------------------------------
#if defined(SOKOL_D3D11)
static const char* hlsl_vs =
    "cbuffer vs_params : register(b0) {\n"
    "    float4x4 mvp;\n"
    "    float4x4 model;\n"
    "    float4x4 normal_mat;\n"
    "    float4x4 light_mvp;\n"
    "};\n"
    "struct vs_in {\n"
    "    float3 pos : POSITION;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float4 color : COLOR0;\n"
    "    float4 tangent : TANGENT;\n"
    "};\n"
    "struct vs_out {\n"
    "    float4 color : COLOR0;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float3 world_pos : TEXCOORD1;\n"
    "    float4 light_pos : TEXCOORD2;\n"
    "    float3 tangent : TEXCOORD3;\n"
    "    float3 bitangent : TEXCOORD4;\n"
    "    float4 pos : SV_Position;\n"
    "};\n"
    "vs_out main(vs_in inp) {\n"
    "    vs_out outp;\n"
    "    outp.pos = mul(mvp, float4(inp.pos, 1.0));\n"
    "    float4 wpos = mul(model, float4(inp.pos, 1.0));\n"
    "    outp.world_pos = wpos.xyz;\n"
    "    float3 N = normalize(mul((float3x3)normal_mat, inp.normal));\n"
    "    float3 T = mul((float3x3)normal_mat, inp.tangent.xyz);\n"
    "    float3 ortho_T = T - dot(T, N) * N;\n"
    "    if (dot(ortho_T, ortho_T) < 0.0001) {\n"
    "        ortho_T = abs(N.y) > 0.99 ? cross(N, float3(0.0, 0.0, 1.0)) : cross(N, float3(0.0, 1.0, 0.0));\n"
    "    }\n"
    "    T = normalize(ortho_T);\n"
    "    float3 B = cross(N, T) * (inp.tangent.w < 0.0 ? -1.0 : 1.0);\n"
    "    outp.normal = N;\n"
    "    outp.tangent = T;\n"
    "    outp.bitangent = B;\n"
    "    outp.uv = inp.uv;\n"
    "    outp.color = inp.color;\n"
    "    float3 normal_bias_offset = N * 0.04;\n"
    "    outp.light_pos = mul(light_mvp, float4(inp.pos + normal_bias_offset, 1.0));\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_fs =
    "cbuffer fs_params : register(b1) {\n"
    "    float4 eye_pos;\n"
    "    float4 material_color;\n"
    "    float4 material_params;\n"
    "    float4 material_uv_offset;\n"
    "    float4 emissive_params;\n"
    "    float4 texture_flags;\n"
    "    float4 fog_color;\n"
    "    float4 fog_params;\n"
    "    float4 extra_params;\n"
    "};\n"
    "struct GPUDirectionalLight {\n"
    "    float4 direction_and_cast_shadow;\n"
    "    float4 color_and_intensity;\n"
    "};\n"
    "struct GPUPointLight {\n"
    "    float4 position_and_range;\n"
    "    float4 color_and_intensity;\n"
    "    float4 params;\n"
    "};\n"
    "struct GPUSpotLight {\n"
    "    float4 position_and_range;\n"
    "    float4 direction_and_cast_shadow;\n"
    "    float4 color_and_intensity;\n"
    "    float4 cone_params;\n"
    "};\n"
    "cbuffer light_params : register(b2) {\n"
    "    float4 ambient_and_count;\n"
    "    float4 light_counts;\n"
    "    float4 hemi_sky;\n"
    "    float4 hemi_ground;\n"
    "    GPUDirectionalLight dir_lights[4];\n"
    "    GPUPointLight point_lights[16];\n"
    "    GPUSpotLight spot_lights[8];\n"
    "};\n"
    "Texture2D tex_albedo : register(t0);\n"
    "SamplerState smp_albedo : register(s0);\n"
    "Texture2D tex_shadow : register(t1);\n"
    "SamplerState smp_shadow : register(s1);\n"
    "Texture2D tex_normal : register(t2);\n"
    "SamplerState smp_normal : register(s2);\n"
    "Texture2D tex_metallic_roughness : register(t3);\n"
    "SamplerState smp_metallic_roughness : register(s3);\n"
    "Texture2D tex_emissive : register(t4);\n"
    "SamplerState smp_emissive : register(s4);\n"
    "Texture2D tex_ao : register(t5);\n"
    "SamplerState smp_ao : register(s5);\n"
    "TextureCube tex_env : register(t6);\n"
    "SamplerState smp_env : register(s6);\n"
    "struct ps_in {\n"
    "    float4 color : COLOR0;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float3 world_pos : TEXCOORD1;\n"
    "    float4 light_pos : TEXCOORD2;\n"
    "    float3 tangent : TEXCOORD3;\n"
    "    float3 bitangent : TEXCOORD4;\n"
    "};\n"
    "static const float PI = 3.14159265359;\n"
    "static const float2 POISSON_DISK_16[16] = {\n"
    "    float2(-0.94201624, -0.39906216),\n"
    "    float2( 0.94558609, -0.76890725),\n"
    "    float2(-0.09418410, -0.92938870),\n"
    "    float2( 0.34495938,  0.29387760),\n"
    "    float2(-0.91588581,  0.45771432),\n"
    "    float2(-0.81544232, -0.87912464),\n"
    "    float2(-0.38277543,  0.27676845),\n"
    "    float2( 0.97484398,  0.75648379),\n"
    "    float2( 0.44323325, -0.97511554),\n"
    "    float2( 0.53742981, -0.47373420),\n"
    "    float2(-0.26496911, -0.41893023),\n"
    "    float2( 0.79197514,  0.19090188),\n"
    "    float2(-0.24188840,  0.99706507),\n"
    "    float2(-0.81409955,  0.91437590),\n"
    "    float2( 0.19984126,  0.78641367),\n"
    "    float2( 0.14383161, -0.14100790)\n"
    "};\n"
    "float3 apply_aces_filmic(float3 x) {\n"
    "    float a = 2.51;\n"
    "    float b = 0.03;\n"
    "    float c = 2.43;\n"
    "    float d = 0.59;\n"
    "    float e = 0.14;\n"
    "    return saturate((x * (a * x + b)) / (x * (c * x + d) + e));\n"
    "}\n"
    "float sample_shadow(float4 lpos, float3 N, float3 L) {\n"
    "    float NdotL = dot(N, L);\n"
    "    if (NdotL <= 0.0) return 0.0;\n"
    "    float3 proj = lpos.xyz / lpos.w;\n"
    "    float2 uv = float2(proj.x * 0.5 + 0.5, -proj.y * 0.5 + 0.5);\n"
    "    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0 || proj.z < 0.0 || proj.z > 1.0) {\n"
    "        return 1.0;\n"
    "    }\n"
    "    float depth_bias = max(0.0015 * (1.0 - NdotL), 0.0004);\n"
    "    float current_depth = proj.z - depth_bias;\n"
    "    float shadow_res = max(light_counts.z, 512.0);\n"
    "    float texel = 1.0 / shadow_res;\n"
    "    float shadow = 0.0;\n"
    "    if (light_counts.w > 0.5) {\n"
    "        float filter_radius = 2.5 * texel;\n"
    "        [unroll]\n"
    "        for (int tap = 0; tap < 16; ++tap) {\n"
    "            float2 offset = POISSON_DISK_16[tap] * filter_radius;\n"
    "            float d = tex_shadow.Sample(smp_shadow, uv + offset).r;\n"
    "            shadow += (current_depth <= d) ? 1.0 : 0.0;\n"
    "        }\n"
    "        shadow *= 0.0625;\n"
    "    } else {\n"
    "        float s0 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2(-0.5, -0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        float s1 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2( 0.5, -0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        float s2 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2(-0.5,  0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        float s3 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2( 0.5,  0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        shadow = (s0 + s1 + s2 + s3) * 0.25;\n"
    "    }\n"
    "    float2 border = min(uv, 1.0 - uv);\n"
    "    float edge_fade = saturate(min(border.x, border.y) * 15.0);\n"
    "    return lerp(1.0, shadow, edge_fade);\n"
    "}\n"
    "float distribution_ggx(float3 N, float3 H, float roughness) {\n"
    "    float a = roughness * roughness;\n"
    "    float a2 = a * a;\n"
    "    float NdotH = max(dot(N, H), 0.0);\n"
    "    float NdotH2 = NdotH * NdotH;\n"
    "    float denom = (NdotH2 * (a2 - 1.0) + 1.0);\n"
    "    return a2 / (PI * denom * denom + 0.00001);\n"
    "}\n"
    "float geometry_schlick_ggx(float NdotV, float roughness) {\n"
    "    float r = (roughness + 1.0);\n"
    "    float k = (r * r) / 8.0;\n"
    "    return NdotV / (NdotV * (1.0 - k) + k + 0.00001);\n"
    "}\n"
    "float geometry_smith(float3 N, float3 V, float3 L, float roughness) {\n"
    "    float NdotV = max(dot(N, V), 0.0001);\n"
    "    float NdotL = max(dot(N, L), 0.0);\n"
    "    float ggx2 = geometry_schlick_ggx(NdotV, roughness);\n"
    "    float ggx1 = geometry_schlick_ggx(NdotL, roughness);\n"
    "    return ggx1 * ggx2;\n"
    "}\n"
    "float3 fresnel_schlick(float cos_theta, float3 F0) {\n"
    "    return F0 + (1.0 - F0) * pow(clamp(1.0 - cos_theta, 0.0, 1.0), 5.0);\n"
    "}\n"
    "float4 main(ps_in inp) : SV_Target0 {\n"
    "    float2 uv = inp.uv * material_params.zw + material_uv_offset.xy;\n"
    "    float4 tex_sample = tex_albedo.Sample(smp_albedo, uv);\n"
    "    float3 albedo = tex_sample.rgb * inp.color.rgb * material_color.rgb;\n"
    "    float alpha = tex_sample.a * inp.color.a * material_color.a * extra_params.z;\n"
    "    if (emissive_params.w >= 0.0 && alpha < emissive_params.w) discard;\n"
    "    float mat_type = extra_params.x;\n"
    "    if (mat_type > 0.5 && mat_type < 1.5) {\n"
    "        float3 unlit_color = albedo;\n"
    "        if (texture_flags.z > 0.5) unlit_color += tex_emissive.Sample(smp_emissive, uv).rgb * emissive_params.xyz;\n"
    "        else unlit_color += emissive_params.xyz;\n"
    "        return float4(unlit_color, alpha);\n"
    "    }\n"
    "    float3 N = normalize(inp.normal);\n"
    "    if (texture_flags.x > 0.5) {\n"
    "        float3 norm_map = tex_normal.Sample(smp_normal, uv).rgb * 2.0 - 1.0;\n"
    "        norm_map.xy *= material_uv_offset.z;\n"
    "        norm_map = normalize(norm_map);\n"
    "        float3 T = inp.tangent;\n"
    "        if (dot(T, T) > 0.0001) {\n"
    "            T = normalize(T);\n"
    "        } else {\n"
    "            T = abs(N.y) > 0.99 ? cross(N, float3(0.0, 0.0, 1.0)) : cross(N, float3(0.0, 1.0, 0.0));\n"
    "            T = normalize(T);\n"
    "        }\n"
    "        float3 B = inp.bitangent;\n"
    "        if (dot(B, B) > 0.0001) {\n"
    "            B = normalize(B);\n"
    "        } else {\n"
    "            B = cross(N, T);\n"
    "        }\n"
    "        N = normalize(norm_map.x * T + norm_map.y * B + norm_map.z * N);\n"
    "    }\n"
    "    float roughness = clamp(material_params.x, 0.04, 1.0);\n"
    "    float metallic = clamp(material_params.y, 0.0, 1.0);\n"
    "    if (texture_flags.y > 0.5) {\n"
    "        float4 mr_sample = tex_metallic_roughness.Sample(smp_metallic_roughness, uv);\n"
    "        roughness = clamp(roughness * mr_sample.g, 0.04, 1.0);\n"
    "        metallic = clamp(metallic * mr_sample.b, 0.0, 1.0);\n"
    "    }\n"
    "    float3 emissive = emissive_params.xyz;\n"
    "    if (texture_flags.z > 0.5) emissive *= tex_emissive.Sample(smp_emissive, uv).rgb;\n"
    "    float ao = 1.0;\n"
    "    if (texture_flags.w > 0.5) {\n"
    "        float ao_sample = tex_ao.Sample(smp_ao, uv).r;\n"
    "        ao = lerp(1.0, ao_sample, material_uv_offset.w);\n"
    "    }\n"
    "    float3 V = normalize(eye_pos.xyz - inp.world_pos);\n"
    "    float hemi = clamp(N.y * 0.5 + 0.5, 0.0, 1.0);\n"
    "    float3 hemi_light = lerp(hemi_ground.rgb, hemi_sky.rgb * hemi_sky.w, hemi);\n"
    "    float3 F0 = lerp(float3(0.04, 0.04, 0.04), albedo, metallic);\n"
    "    float3 R = reflect(-V, N);\n"
    "    float env_lod = roughness * 7.0;\n"
    "    float3 env_spec = tex_env.SampleLevel(smp_env, R, env_lod).rgb;\n"
    "    float3 F_env = fresnel_schlick(max(dot(N, V), 0.0), F0);\n"
    "    float env_intensity = eye_pos.w;\n"
    "    float3 ibl_specular = env_spec * F_env * env_intensity;\n"
    "    float3 kS = F_env;\n"
    "    float3 kD = (float3(1.0, 1.0, 1.0) - kS) * (1.0 - metallic);\n"
    "    float3 env_diff = tex_env.SampleLevel(smp_env, N, 7.0).rgb;\n"
    "    float3 ibl_diffuse = kD * env_diff * albedo * ao * env_intensity;\n"
    "    float3 ambient = (ambient_and_count.rgb + hemi_light) * albedo * ao * (1.0 - 0.5 * metallic) + ibl_diffuse + ibl_specular;\n"
    "    float3 direct_lighting = float3(0.0, 0.0, 0.0);\n"
    "    int num_dirs = (int)ambient_and_count.w;\n"
    "    int num_points = (int)light_counts.x;\n"
    "    int num_spots = (int)light_counts.y;\n"
    "    [loop]\n"
    "    for (int i = 0; i < num_dirs && i < 4; ++i) {\n"
    "        float3 L = normalize(-dir_lights[i].direction_and_cast_shadow.xyz);\n"
    "        float3 H = normalize(V + L);\n"
    "        float NdotL = max(dot(N, L), 0.0);\n"
    "        if (NdotL > 0.0) {\n"
    "            float shadow = 1.0;\n"
    "            if (i == 0 && dir_lights[i].direction_and_cast_shadow.w > 0.5) {\n"
    "                shadow = sample_shadow(inp.light_pos, N, L);\n"
    "            }\n"
    "            float3 light_rad = dir_lights[i].color_and_intensity.rgb * dir_lights[i].color_and_intensity.w;\n"
    "            if (mat_type > 1.5 && mat_type < 2.5) {\n"
    "                direct_lighting += albedo * NdotL * light_rad * shadow;\n"
    "            } else if (mat_type > 2.5 && mat_type < 3.5) {\n"
    "                float shininess = max(extra_params.y, 1.0);\n"
    "                float NdotH = max(dot(N, H), 0.0);\n"
    "                float spec = pow(NdotH, shininess);\n"
    "                direct_lighting += (albedo * NdotL + spec * 0.5) * light_rad * shadow;\n"
    "            } else if (mat_type > 3.5 && mat_type < 4.5) {\n"
    "                float steps = max(extra_params.y, 2.0);\n"
    "                float toon_diff = floor(NdotL * steps) / steps;\n"
    "                float NdotH = max(dot(N, H), 0.0);\n"
    "                float toon_spec = (pow(NdotH, 32.0) > 0.5) ? 0.6 : 0.0;\n"
    "                direct_lighting += (albedo * toon_diff + toon_spec) * light_rad * shadow;\n"
    "            } else {\n"
    "                float NDF = distribution_ggx(N, H, roughness);\n"
    "                float G = geometry_smith(N, V, L, roughness);\n"
    "                float3 F = fresnel_schlick(max(dot(H, V), 0.0), F0);\n"
    "                float3 numerator = NDF * G * F;\n"
    "                float denominator = 4.0 * max(dot(N, V), 0.0001) * NdotL + 0.0001;\n"
    "                float3 specular = numerator / denominator;\n"
    "                float3 kD = (float3(1.0, 1.0, 1.0) - F) * (1.0 - metallic);\n"
    "                direct_lighting += (kD * albedo / PI + specular) * light_rad * NdotL * shadow;\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    [loop]\n"
    "    for (int p = 0; p < num_points && p < 16; ++p) {\n"
    "        float3 to_light = point_lights[p].position_and_range.xyz - inp.world_pos;\n"
    "        float dist = length(to_light);\n"
    "        float range = point_lights[p].position_and_range.w;\n"
    "        if (range <= 0.0 || dist < range) {\n"
    "            float3 L = to_light / max(dist, 0.0001);\n"
    "            float3 H = normalize(V + L);\n"
    "            float NdotL = max(dot(N, L), 0.0);\n"
    "            if (NdotL > 0.0) {\n"
    "                float att = 1.0 / max(dist * dist, 0.01);\n"
    "                if (range > 0.0) {\n"
    "                    float win = saturate(1.0 - pow(dist / range, 4.0));\n"
    "                    att *= win * win;\n"
    "                }\n"
    "                float3 light_rad = point_lights[p].color_and_intensity.rgb * point_lights[p].color_and_intensity.w * att;\n"
    "                if (mat_type > 1.5 && mat_type < 2.5) {\n"
    "                    direct_lighting += albedo * NdotL * light_rad;\n"
    "                } else if (mat_type > 2.5 && mat_type < 3.5) {\n"
    "                    float shininess = max(extra_params.y, 1.0);\n"
    "                    float NdotH = max(dot(N, H), 0.0);\n"
    "                    float spec = pow(NdotH, shininess);\n"
    "                    direct_lighting += (albedo * NdotL + spec * 0.5) * light_rad;\n"
    "                } else if (mat_type > 3.5 && mat_type < 4.5) {\n"
    "                    float steps = max(extra_params.y, 2.0);\n"
    "                    float toon_diff = floor(NdotL * steps) / steps;\n"
    "                    direct_lighting += albedo * toon_diff * light_rad;\n"
    "                } else {\n"
    "                    float NDF = distribution_ggx(N, H, roughness);\n"
    "                    float G = geometry_smith(N, V, L, roughness);\n"
    "                    float3 F = fresnel_schlick(max(dot(H, V), 0.0), F0);\n"
    "                    float3 numerator = NDF * G * F;\n"
    "                    float denominator = 4.0 * max(dot(N, V), 0.0001) * NdotL + 0.0001;\n"
    "                    float3 specular = numerator / denominator;\n"
    "                    float3 kD = (float3(1.0, 1.0, 1.0) - F) * (1.0 - metallic);\n"
    "                    direct_lighting += (kD * albedo / PI + specular) * light_rad * NdotL;\n"
    "                }\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    [loop]\n"
    "    for (int s = 0; s < num_spots && s < 8; ++s) {\n"
    "        float3 to_light = spot_lights[s].position_and_range.xyz - inp.world_pos;\n"
    "        float dist = length(to_light);\n"
    "        float range = spot_lights[s].position_and_range.w;\n"
    "        if (range <= 0.0 || dist < range) {\n"
    "            float3 L = to_light / max(dist, 0.0001);\n"
    "            float3 spot_dir = normalize(spot_lights[s].direction_and_cast_shadow.xyz);\n"
    "            float cos_theta = dot(-L, spot_dir);\n"
    "            float cos_inner = spot_lights[s].cone_params.x;\n"
    "            float cos_outer = spot_lights[s].cone_params.y;\n"
    "            float spot_factor = saturate((cos_theta - cos_outer) / max(cos_inner - cos_outer, 0.0001));\n"
    "            if (spot_factor > 0.0) {\n"
    "                float3 H = normalize(V + L);\n"
    "                float NdotL = max(dot(N, L), 0.0);\n"
    "                if (NdotL > 0.0) {\n"
    "                    float att = 1.0 / max(dist * dist, 0.01);\n"
    "                    if (range > 0.0) {\n"
    "                        float win = saturate(1.0 - pow(dist / range, 4.0));\n"
    "                        att *= win * win;\n"
    "                    }\n"
    "                    float3 light_rad = spot_lights[s].color_and_intensity.rgb * spot_lights[s].color_and_intensity.w * att * spot_factor;\n"
    "                    if (mat_type > 1.5 && mat_type < 2.5) {\n"
    "                        direct_lighting += albedo * NdotL * light_rad;\n"
    "                    } else if (mat_type > 2.5 && mat_type < 3.5) {\n"
    "                        float shininess = max(extra_params.y, 1.0);\n"
    "                        float NdotH = max(dot(N, H), 0.0);\n"
    "                        float spec = pow(NdotH, shininess);\n"
    "                        direct_lighting += (albedo * NdotL + spec * 0.5) * light_rad;\n"
    "                    } else if (mat_type > 3.5 && mat_type < 4.5) {\n"
    "                        float steps = max(extra_params.y, 2.0);\n"
    "                        float toon_diff = floor(NdotL * steps) / steps;\n"
    "                        direct_lighting += albedo * toon_diff * light_rad;\n"
    "                    } else {\n"
    "                        float NDF = distribution_ggx(N, H, roughness);\n"
    "                        float G = geometry_smith(N, V, L, roughness);\n"
    "                        float3 F = fresnel_schlick(max(dot(H, V), 0.0), F0);\n"
    "                        float3 numerator = NDF * G * F;\n"
    "                        float denominator = 4.0 * max(dot(N, V), 0.0001) * NdotL + 0.0001;\n"
    "                        float3 specular = numerator / denominator;\n"
    "                        float3 kD = (float3(1.0, 1.0, 1.0) - F) * (1.0 - metallic);\n"
    "                        direct_lighting += (kD * albedo / PI + specular) * light_rad * NdotL;\n"
    "                    }\n"
    "                }\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    float3 final_color = ambient + direct_lighting + emissive;\n"
    "    float fog_type = fog_params.x;\n"
    "    if (fog_type > 0.5) {\n"
    "        float dist = length(inp.world_pos - eye_pos.xyz);\n"
    "        float fog_factor = 1.0;\n"
    "        if (fog_type < 1.5) {\n"
    "            float near = fog_params.y;\n"
    "            float far = fog_params.z;\n"
    "            fog_factor = saturate((far - dist) / max(far - near, 0.0001));\n"
    "        } else {\n"
    "            float density = fog_params.w;\n"
    "            float d = dist * density;\n"
    "            fog_factor = saturate(exp(- d * d));\n"
    "        }\n"
    "        final_color = lerp(fog_color.rgb, final_color, fog_factor);\n"
    "    }\n"
    "    if (fog_color.w > 0.5) {\n"
    "        final_color = apply_aces_filmic(final_color);\n"
    "    }\n"
    "    return float4(final_color, alpha);\n"
    "}\n";

// Shadow Pass Shaders
static const char* hlsl_shadow_vs =
    "cbuffer shadow_vs_params : register(b0) {\n"
    "    float4x4 light_mvp;\n"
    "};\n"
    "struct vs_shadow_in {\n"
    "    float3 pos : POSITION;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float4 color : COLOR0;\n"
    "    float4 tangent : TANGENT;\n"
    "};\n"
    "struct vs_shadow_out {\n"
    "    float4 pos : SV_Position;\n"
    "    float depth : TEXCOORD0;\n"
    "};\n"
    "vs_shadow_out main(vs_shadow_in inp) {\n"
    "    vs_shadow_out outp;\n"
    "    outp.pos = mul(light_mvp, float4(inp.pos, 1.0));\n"
    "    outp.depth = outp.pos.z / outp.pos.w;\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_shadow_fs =
    "struct ps_shadow_in {\n"
    "    float4 pos : SV_Position;\n"
    "    float depth : TEXCOORD0;\n"
    "};\n"
    "float4 main(ps_shadow_in inp) : SV_Target0 {\n"
    "    return float4(inp.depth, 0.0, 0.0, 1.0);\n"
    "}\n";

// Line Shaders for Debug AABB wireframes
static const char* hlsl_line_vs =
    "cbuffer line_vs_params : register(b0) {\n"
    "    float4x4 mvp;\n"
    "};\n"
    "struct vs_line_in {\n"
    "    float3 pos : POSITION;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "struct vs_line_out {\n"
    "    float4 pos : SV_Position;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "vs_line_out main(vs_line_in inp) {\n"
    "    vs_line_out outp;\n"
    "    outp.pos = mul(mvp, float4(inp.pos, 1.0));\n"
    "    outp.color = inp.color;\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_line_fs =
    "struct ps_line_in {\n"
    "    float4 pos : SV_Position;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "float4 main(ps_line_in inp) : SV_Target0 {\n"
    "    return inp.color;\n"
    "}\n";

// HUD Shaders for 2D Screen space elements (crosshair, text)
static const char* hlsl_hud_vs =
    "cbuffer hud_vs_params : register(b0) {\n"
    "    float4x4 ortho_proj;\n"
    "};\n"
    "struct vs_hud_in {\n"
    "    float2 pos : POSITION;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "struct vs_hud_out {\n"
    "    float4 pos : SV_Position;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "vs_hud_out main(vs_hud_in inp) {\n"
    "    vs_hud_out outp;\n"
    "    outp.pos = mul(ortho_proj, float4(inp.pos, 0.0, 1.0));\n"
    "    outp.color = inp.color;\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_hud_fs =
    "struct ps_hud_in {\n"
    "    float4 pos : SV_Position;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "float4 main(ps_hud_in inp) : SV_Target0 {\n"
    "    return inp.color;\n"
    "}\n";

// Instanced Mesh Shaders
static const char* hlsl_inst_vs =
    "cbuffer inst_vs_params : register(b0) {\n"
    "    float4x4 view_proj;\n"
    "    float4x4 light_vp;\n"
    "};\n"
    "struct vs_inst_in {\n"
    "    float3 pos : POSITION;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float4 color : COLOR0;\n"
    "    float4 tangent : TANGENT;\n"
    "    float4 i_model0 : TEXCOORD3;\n"
    "    float4 i_model1 : TEXCOORD4;\n"
    "    float4 i_model2 : TEXCOORD5;\n"
    "    float4 i_model3 : TEXCOORD6;\n"
    "    float4 i_color : COLOR1;\n"
    "};\n"
    "struct vs_out {\n"
    "    float4 color : COLOR0;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float3 world_pos : TEXCOORD1;\n"
    "    float4 light_pos : TEXCOORD2;\n"
    "    float3 tangent : TEXCOORD3;\n"
    "    float3 bitangent : TEXCOORD4;\n"
    "    float4 pos : SV_Position;\n"
    "};\n"
    "vs_out main(vs_inst_in inp) {\n"
    "    vs_out outp;\n"
    "    float4x4 model = transpose(float4x4(inp.i_model0, inp.i_model1, inp.i_model2, inp.i_model3));\n"
    "    float4 world_pos = mul(model, float4(inp.pos, 1.0));\n"
    "    outp.pos = mul(view_proj, world_pos);\n"
    "    outp.world_pos = world_pos.xyz;\n"
    "    float3x3 nmat = (float3x3)model;\n"
    "    float3 N = normalize(mul(nmat, inp.normal));\n"
    "    float3 T = mul(nmat, inp.tangent.xyz);\n"
    "    float3 ortho_T = T - dot(T, N) * N;\n"
    "    if (dot(ortho_T, ortho_T) < 0.0001) {\n"
    "        ortho_T = abs(N.y) > 0.99 ? cross(N, float3(0.0, 0.0, 1.0)) : cross(N, float3(0.0, 1.0, 0.0));\n"
    "    }\n"
    "    T = normalize(ortho_T);\n"
    "    float3 B = cross(N, T) * (inp.tangent.w < 0.0 ? -1.0 : 1.0);\n"
    "    outp.normal = N;\n"
    "    outp.tangent = T;\n"
    "    outp.bitangent = B;\n"
    "    outp.uv = inp.uv;\n"
    "    outp.color = inp.color * inp.i_color;\n"
    "    float3 normal_bias_offset = N * 0.04;\n"
    "    outp.light_pos = mul(light_vp, float4(world_pos.xyz + normal_bias_offset, 1.0));\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_inst_shadow_vs =
    "cbuffer shadow_vs_params : register(b0) {\n"
    "    float4x4 light_vp;\n"
    "};\n"
    "struct vs_inst_shadow_in {\n"
    "    float3 pos : POSITION;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float4 color : COLOR0;\n"
    "    float4 tangent : TANGENT;\n"
    "    float4 i_model0 : TEXCOORD3;\n"
    "    float4 i_model1 : TEXCOORD4;\n"
    "    float4 i_model2 : TEXCOORD5;\n"
    "    float4 i_model3 : TEXCOORD6;\n"
    "    float4 i_color : COLOR1;\n"
    "};\n"
    "struct vs_shadow_out {\n"
    "    float4 pos : SV_Position;\n"
    "    float depth : TEXCOORD0;\n"
    "};\n"
    "vs_shadow_out main(vs_inst_shadow_in inp) {\n"
    "    vs_shadow_out outp;\n"
    "    float4x4 model = transpose(float4x4(inp.i_model0, inp.i_model1, inp.i_model2, inp.i_model3));\n"
    "    float4 world_pos = mul(model, float4(inp.pos, 1.0));\n"
    "    outp.pos = mul(light_vp, world_pos);\n"
    "    outp.depth = outp.pos.z / outp.pos.w;\n"
    "    return outp;\n"
    "}\n";

// Skybox & Procedural Sky Shaders (HLSL)
static const char* hlsl_skybox_vs =
    "cbuffer skybox_vs_params : register(b0) {\n"
    "    float4x4 view_proj;\n"
    "};\n"
    "struct vs_sky_in {\n"
    "    float3 pos : POSITION;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float4 color : COLOR0;\n"
    "    float4 tangent : TANGENT;\n"
    "};\n"
    "struct vs_sky_out {\n"
    "    float4 pos : SV_Position;\n"
    "    float3 dir : TEXCOORD0;\n"
    "};\n"
    "vs_sky_out main(vs_sky_in inp) {\n"
    "    vs_sky_out outp;\n"
    "    float4 p = mul(view_proj, float4(inp.pos, 1.0));\n"
    "    outp.pos = p.xyww;\n"
    "    outp.dir = inp.pos;\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_skybox_fs =
    "TextureCube tex_sky : register(t0);\n"
    "SamplerState smp_sky : register(s0);\n"
    "struct ps_sky_in {\n"
    "    float4 pos : SV_Position;\n"
    "    float3 dir : TEXCOORD0;\n"
    "};\n"
    "float4 main(ps_sky_in inp) : SV_Target0 {\n"
    "    float3 dir = normalize(inp.dir);\n"
    "    float3 col = tex_sky.Sample(smp_sky, dir).rgb;\n"
    "    return float4(col, 1.0);\n"
    "}\n";

static const char* hlsl_proc_sky_vs = hlsl_skybox_vs;

static const char* hlsl_proc_sky_fs =
    "cbuffer proc_sky_fs_params : register(b1) {\n"
    "    float4 sun_dir_turbidity;\n"
    "    float4 rayleigh_params;\n"
    "    float4 mie_params;\n"
    "    float4 sky_misc;\n"
    "};\n"
    "struct ps_proc_sky_in {\n"
    "    float4 pos : SV_Position;\n"
    "    float3 dir : TEXCOORD0;\n"
    "};\n"
    "static const float PI = 3.14159265359;\n"
    "float3 apply_aces_filmic_sky(float3 x) {\n"
    "    float a = 2.51;\n"
    "    float b = 0.03;\n"
    "    float c = 2.43;\n"
    "    float d = 0.59;\n"
    "    float e = 0.14;\n"
    "    return saturate((x * (a * x + b)) / (x * (c * x + d) + e));\n"
    "}\n"
    "float4 main(ps_proc_sky_in inp) : SV_Target0 {\n"
    "    float3 V = normalize(inp.dir);\n"
    "    float3 S = normalize(sun_dir_turbidity.xyz);\n"
    "    float cos_gamma = clamp(dot(V, S), -1.0, 1.0);\n"
    "    float phase_r = (3.0 / (16.0 * PI)) * (1.0 + cos_gamma * cos_gamma);\n"
    "    float g = sky_misc.x;\n"
    "    float g2 = g * g;\n"
    "    float denom = pow(max(1.0 + g2 - 2.0 * g * cos_gamma, 0.0001), 1.5);\n"
    "    float phase_m = (1.0 / (4.0 * PI)) * (1.0 - g2) / denom;\n"
    "    float3 beta_r = rayleigh_params.rgb * rayleigh_params.w * 0.08;\n"
    "    float3 beta_m = mie_params.rgb * mie_params.w * sun_dir_turbidity.w * 0.04;\n"
    "    float zenith_V = max(V.y, 0.03);\n"
    "    float zenith_S = max(S.y, 0.03);\n"
    "    float3 T = exp(-(beta_r + beta_m) * (1.0 / zenith_V + 1.0 / zenith_S) * 0.8);\n"
    "    float3 inscatter = (beta_r * phase_r + beta_m * phase_m) * (float3(1.0, 1.0, 1.0) - T) * 12.0;\n"
    "    float sun_disk = smoothstep(0.9992, 0.9998, cos_gamma) * 25.0;\n"
    "    float3 sun_color = sun_disk * T * mie_params.rgb;\n"
    "    float3 sky = inscatter + sun_color;\n"
    "    if (V.y < 0.0) {\n"
    "        float3 ground = mie_params.rgb * 0.15 * max(S.y, 0.1);\n"
    "        sky = lerp(sky, ground, saturate(-V.y * 6.0));\n"
    "    }\n"
    "    sky = max(sky, float3(0.015, 0.02, 0.035));\n"
    "    sky = apply_aces_filmic_sky(sky);\n"
    "    return float4(sky, 1.0);\n"
    "}\n";

#else // Full GLSL #version 330
static const char* glsl_vs =
    "#version 330\n"
    "layout(location = 0) in vec3 pos;\n"
    "layout(location = 1) in vec3 normal;\n"
    "layout(location = 2) in vec2 uv;\n"
    "layout(location = 3) in vec4 color;\n"
    "layout(location = 4) in vec4 tangent;\n"
    "uniform mat4 mvp;\n"
    "uniform mat4 model;\n"
    "uniform mat4 normal_mat;\n"
    "uniform mat4 light_mvp;\n"
    "out vec4 v_color;\n"
    "out vec3 v_normal;\n"
    "out vec2 v_uv;\n"
    "out vec3 v_world_pos;\n"
    "out vec4 v_light_pos;\n"
    "out vec3 v_tangent;\n"
    "out vec3 v_bitangent;\n"
    "void main() {\n"
    "    gl_Position = mvp * vec4(pos, 1.0);\n"
    "    vec4 wpos = model * vec4(pos, 1.0);\n"
    "    v_world_pos = wpos.xyz;\n"
    "    vec3 N = normalize(mat3(normal_mat) * normal);\n"
    "    vec3 T = mat3(normal_mat) * tangent.xyz;\n"
    "    vec3 ortho_T = T - dot(T, N) * N;\n"
    "    if (dot(ortho_T, ortho_T) < 0.0001) {\n"
    "        ortho_T = abs(N.y) > 0.99 ? cross(N, vec3(0.0, 0.0, 1.0)) : cross(N, vec3(0.0, 1.0, 0.0));\n"
    "    }\n"
    "    T = normalize(ortho_T);\n"
    "    vec3 B = cross(N, T) * (tangent.w < 0.0 ? -1.0 : 1.0);\n"
    "    v_normal = N;\n"
    "    v_tangent = T;\n"
    "    v_bitangent = B;\n"
    "    v_uv = uv;\n"
    "    v_color = color;\n"
    "    vec3 normal_bias_offset = N * 0.04;\n"
    "    v_light_pos = light_mvp * vec4(pos + normal_bias_offset, 1.0);\n"
    "}\n";

static const char* glsl_fs =
    "#version 330\n"
    "struct GPUDirectionalLight {\n"
    "    vec4 direction_and_cast_shadow;\n"
    "    vec4 color_and_intensity;\n"
    "};\n"
    "struct GPUPointLight {\n"
    "    vec4 position_and_range;\n"
    "    vec4 color_and_intensity;\n"
    "    vec4 params;\n"
    "};\n"
    "struct GPUSpotLight {\n"
    "    vec4 position_and_range;\n"
    "    vec4 direction_and_cast_shadow;\n"
    "    vec4 color_and_intensity;\n"
    "    vec4 cone_params;\n"
    "};\n"
    "layout(std140) uniform fs_params {\n"
    "    vec4 eye_pos;\n"
    "    vec4 material_color;\n"
    "    vec4 material_params;\n"
    "    vec4 material_uv_offset;\n"
    "    vec4 emissive_params;\n"
    "    vec4 texture_flags;\n"
    "    vec4 fog_color;\n"
    "    vec4 fog_params;\n"
    "    vec4 extra_params;\n"
    "};\n"
    "layout(std140) uniform light_params {\n"
    "    vec4 ambient_and_count;\n"
    "    vec4 light_counts;\n"
    "    vec4 hemi_sky;\n"
    "    vec4 hemi_ground;\n"
    "    GPUDirectionalLight dir_lights[4];\n"
    "    GPUPointLight point_lights[16];\n"
    "    GPUSpotLight spot_lights[8];\n"
    "};\n"
    "uniform sampler2D tex_albedo;\n"
    "uniform sampler2D tex_shadow;\n"
    "uniform sampler2D tex_normal;\n"
    "uniform sampler2D tex_metallic_roughness;\n"
    "uniform sampler2D tex_emissive;\n"
    "uniform sampler2D tex_ao;\n"
    "uniform samplerCube tex_env;\n"
    "in vec4 v_color;\n"
    "in vec3 v_normal;\n"
    "in vec2 v_uv;\n"
    "in vec3 v_world_pos;\n"
    "in vec4 v_light_pos;\n"
    "in vec3 v_tangent;\n"
    "in vec3 v_bitangent;\n"
    "out vec4 frag_color;\n"
    "const float PI = 3.14159265359;\n"
    "const vec2 POISSON_DISK_16[16] = vec2[](\n"
    "    vec2(-0.94201624, -0.39906216),\n"
    "    vec2( 0.94558609, -0.76890725),\n"
    "    vec2(-0.09418410, -0.92938870),\n"
    "    vec2( 0.34495938,  0.29387760),\n"
    "    vec2(-0.91588581,  0.45771432),\n"
    "    vec2(-0.81544232, -0.87912464),\n"
    "    vec2(-0.38277543,  0.27676845),\n"
    "    vec2( 0.97484398,  0.75648379),\n"
    "    vec2( 0.44323325, -0.97511554),\n"
    "    vec2( 0.53742981, -0.47373420),\n"
    "    vec2(-0.26496911, -0.41893023),\n"
    "    vec2( 0.79197514,  0.19090188),\n"
    "    vec2(-0.24188840,  0.99706507),\n"
    "    vec2(-0.81409955,  0.91437590),\n"
    "    vec2( 0.19984126,  0.78641367),\n"
    "    vec2( 0.14383161, -0.14100790)\n"
    ");\n"
    "vec3 apply_aces_filmic(vec3 x) {\n"
    "    float a = 2.51;\n"
    "    float b = 0.03;\n"
    "    float c = 2.43;\n"
    "    float d = 0.59;\n"
    "    float e = 0.14;\n"
    "    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);\n"
    "}\n"
    "float sample_shadow(vec4 lpos, vec3 N, vec3 L) {\n"
    "    float NdotL = dot(N, L);\n"
    "    if (NdotL <= 0.0) return 0.0;\n"
    "    vec3 proj = lpos.xyz / lpos.w;\n"
    "    vec2 uv = vec2(proj.x * 0.5 + 0.5, proj.y * 0.5 + 0.5);\n"
    "    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0 || proj.z < 0.0 || proj.z > 1.0) {\n"
    "        return 1.0;\n"
    "    }\n"
    "    float depth_bias = max(0.0015 * (1.0 - NdotL), 0.0004);\n"
    "    float current_depth = proj.z - depth_bias;\n"
    "    float shadow_res = max(light_counts.z, 512.0);\n"
    "    float texel = 1.0 / shadow_res;\n"
    "    float shadow = 0.0;\n"
    "    if (light_counts.w > 0.5) {\n"
    "        float filter_radius = 2.5 * texel;\n"
    "        for (int tap = 0; tap < 16; ++tap) {\n"
    "            vec2 offset = POISSON_DISK_16[tap] * filter_radius;\n"
    "            float d = texture(tex_shadow, uv + offset).r;\n"
    "            shadow += (current_depth <= d) ? 1.0 : 0.0;\n"
    "        }\n"
    "        shadow *= 0.0625;\n"
    "    } else {\n"
    "        float s0 = (current_depth <= texture(tex_shadow, uv + vec2(-0.5, -0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        float s1 = (current_depth <= texture(tex_shadow, uv + vec2( 0.5, -0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        float s2 = (current_depth <= texture(tex_shadow, uv + vec2(-0.5,  0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        float s3 = (current_depth <= texture(tex_shadow, uv + vec2( 0.5,  0.5) * texel).r) ? 1.0 : 0.0;\n"
    "        shadow = (s0 + s1 + s2 + s3) * 0.25;\n"
    "    }\n"
    "    vec2 border = min(uv, 1.0 - uv);\n"
    "    float edge_fade = clamp(min(border.x, border.y) * 15.0, 0.0, 1.0);\n"
    "    return mix(1.0, shadow, edge_fade);\n"
    "}\n"
    "float distribution_ggx(vec3 N, vec3 H, float roughness) {\n"
    "    float a = roughness * roughness;\n"
    "    float a2 = a * a;\n"
    "    float NdotH = max(dot(N, H), 0.0);\n"
    "    float NdotH2 = NdotH * NdotH;\n"
    "    float denom = (NdotH2 * (a2 - 1.0) + 1.0);\n"
    "    return a2 / (PI * denom * denom + 0.00001);\n"
    "}\n"
    "float geometry_schlick_ggx(float NdotV, float roughness) {\n"
    "    float r = (roughness + 1.0);\n"
    "    float k = (r * r) / 8.0;\n"
    "    return NdotV / (NdotV * (1.0 - k) + k + 0.00001);\n"
    "}\n"
    "float geometry_smith(vec3 N, vec3 V, vec3 L, float roughness) {\n"
    "    float NdotV = max(dot(N, V), 0.0001);\n"
    "    float NdotL = max(dot(N, L), 0.0);\n"
    "    float ggx2 = geometry_schlick_ggx(NdotV, roughness);\n"
    "    float ggx1 = geometry_schlick_ggx(NdotL, roughness);\n"
    "    return ggx1 * ggx2;\n"
    "}\n"
    "vec3 fresnel_schlick(float cos_theta, vec3 F0) {\n"
    "    return F0 + (1.0 - F0) * pow(clamp(1.0 - cos_theta, 0.0, 1.0), 5.0);\n"
    "}\n"
    "void main() {\n"
    "    vec2 uv = v_uv * material_params.zw + material_uv_offset.xy;\n"
    "    vec4 tex_sample = texture(tex_albedo, uv);\n"
    "    vec3 albedo = tex_sample.rgb * v_color.rgb * material_color.rgb;\n"
    "    float alpha = tex_sample.a * v_color.a * material_color.a * extra_params.z;\n"
    "    if (emissive_params.w >= 0.0 && alpha < emissive_params.w) discard;\n"
    "    float mat_type = extra_params.x;\n"
    "    if (mat_type > 0.5 && mat_type < 1.5) {\n"
    "        vec3 unlit_color = albedo;\n"
    "        if (texture_flags.z > 0.5) unlit_color += texture(tex_emissive, uv).rgb * emissive_params.xyz;\n"
    "        else unlit_color += emissive_params.xyz;\n"
    "        frag_color = vec4(unlit_color, alpha);\n"
    "        return;\n"
    "    }\n"
    "    vec3 N = normalize(v_normal);\n"
    "    if (texture_flags.x > 0.5) {\n"
    "        vec3 norm_map = texture(tex_normal, uv).rgb * 2.0 - 1.0;\n"
    "        norm_map.xy *= material_uv_offset.z;\n"
    "        norm_map = normalize(norm_map);\n"
    "        vec3 T = v_tangent;\n"
    "        if (dot(T, T) > 0.0001) {\n"
    "            T = normalize(T);\n"
    "        } else {\n"
    "            T = abs(N.y) > 0.99 ? cross(N, vec3(0.0, 0.0, 1.0)) : cross(N, vec3(0.0, 1.0, 0.0));\n"
    "            T = normalize(T);\n"
    "        }\n"
    "        vec3 B = v_bitangent;\n"
    "        if (dot(B, B) > 0.0001) {\n"
    "            B = normalize(B);\n"
    "        } else {\n"
    "            B = cross(N, T);\n"
    "        }\n"
    "        N = normalize(norm_map.x * T + norm_map.y * B + norm_map.z * N);\n"
    "    }\n"
    "    float roughness = clamp(material_params.x, 0.04, 1.0);\n"
    "    float metallic = clamp(material_params.y, 0.0, 1.0);\n"
    "    if (texture_flags.y > 0.5) {\n"
    "        vec4 mr_sample = texture(tex_metallic_roughness, uv);\n"
    "        roughness = clamp(roughness * mr_sample.g, 0.04, 1.0);\n"
    "        metallic = clamp(metallic * mr_sample.b, 0.0, 1.0);\n"
    "    }\n"
    "    vec3 emissive = emissive_params.xyz;\n"
    "    if (texture_flags.z > 0.5) emissive *= texture(tex_emissive, uv).rgb;\n"
    "    float ao = 1.0;\n"
    "    if (texture_flags.w > 0.5) {\n"
    "        float ao_sample = texture(tex_ao, uv).r;\n"
    "        ao = mix(1.0, ao_sample, material_uv_offset.w);\n"
    "    }\n"
    "    vec3 V = normalize(eye_pos.xyz - v_world_pos);\n"
    "    float hemi = clamp(N.y * 0.5 + 0.5, 0.0, 1.0);\n"
    "    vec3 hemi_light = mix(hemi_ground.rgb, hemi_sky.rgb * hemi_sky.w, hemi);\n"
    "    vec3 F0 = mix(vec3(0.04), albedo, metallic);\n"
    "    vec3 R = reflect(-V, N);\n"
    "    float env_lod = roughness * 7.0;\n"
    "    vec3 env_spec = textureLod(tex_env, R, env_lod).rgb;\n"
    "    vec3 F_env = fresnel_schlick(max(dot(N, V), 0.0), F0);\n"
    "    float env_intensity = eye_pos.w;\n"
    "    vec3 ibl_specular = env_spec * F_env * env_intensity;\n"
    "    vec3 kS = F_env;\n"
    "    vec3 kD = (vec3(1.0) - kS) * (1.0 - metallic);\n"
    "    vec3 env_diff = textureLod(tex_env, N, 7.0).rgb;\n"
    "    vec3 ibl_diffuse = kD * env_diff * albedo * ao * env_intensity;\n"
    "    vec3 ambient = (ambient_and_count.rgb + hemi_light) * albedo * ao * (1.0 - 0.5 * metallic) + ibl_diffuse + ibl_specular;\n"
    "    vec3 direct_lighting = vec3(0.0);\n"
    "    int num_dirs = int(ambient_and_count.w);\n"
    "    int num_points = int(light_counts.x);\n"
    "    int num_spots = int(light_counts.y);\n"
    "    for (int i = 0; i < num_dirs && i < 4; ++i) {\n"
    "        vec3 L = normalize(-dir_lights[i].direction_and_cast_shadow.xyz);\n"
    "        vec3 H = normalize(V + L);\n"
    "        float NdotL = max(dot(N, L), 0.0);\n"
    "        if (NdotL > 0.0) {\n"
    "            float shadow = 1.0;\n"
    "            if (i == 0 && dir_lights[i].direction_and_cast_shadow.w > 0.5) shadow = sample_shadow(v_light_pos, N, L);\n"
    "            vec3 light_rad = dir_lights[i].color_and_intensity.rgb * dir_lights[i].color_and_intensity.w;\n"
    "            if (mat_type > 1.5 && mat_type < 2.5) {\n"
    "                direct_lighting += albedo * NdotL * light_rad * shadow;\n"
    "            } else if (mat_type > 2.5 && mat_type < 3.5) {\n"
    "                float shininess = max(extra_params.y, 1.0);\n"
    "                float NdotH = max(dot(N, H), 0.0);\n"
    "                float spec = pow(NdotH, shininess);\n"
    "                direct_lighting += (albedo * NdotL + spec * 0.5) * light_rad * shadow;\n"
    "            } else if (mat_type > 3.5 && mat_type < 4.5) {\n"
    "                float steps = max(extra_params.y, 2.0);\n"
    "                float toon_diff = floor(NdotL * steps) / steps;\n"
    "                float NdotH = max(dot(N, H), 0.0);\n"
    "                float toon_spec = (pow(NdotH, 32.0) > 0.5) ? 0.6 : 0.0;\n"
    "                direct_lighting += (albedo * toon_diff + toon_spec) * light_rad * shadow;\n"
    "            } else {\n"
    "                float NDF = distribution_ggx(N, H, roughness);\n"
    "                float G = geometry_smith(N, V, L, roughness);\n"
    "                vec3 F = fresnel_schlick(max(dot(H, V), 0.0), F0);\n"
    "                vec3 numerator = NDF * G * F;\n"
    "                float denominator = 4.0 * max(dot(N, V), 0.0001) * NdotL + 0.0001;\n"
    "                vec3 specular = numerator / denominator;\n"
    "                vec3 kD = (vec3(1.0) - F) * (1.0 - metallic);\n"
    "                direct_lighting += (kD * albedo / PI + specular) * light_rad * NdotL * shadow;\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    for (int p = 0; p < num_points && p < 16; ++p) {\n"
    "        vec3 to_light = point_lights[p].position_and_range.xyz - v_world_pos;\n"
    "        float dist = length(to_light);\n"
    "        float range = point_lights[p].position_and_range.w;\n"
    "        if (range <= 0.0 || dist < range) {\n"
    "            vec3 L = to_light / max(dist, 0.0001);\n"
    "            vec3 H = normalize(V + L);\n"
    "            float NdotL = max(dot(N, L), 0.0);\n"
    "            if (NdotL > 0.0) {\n"
    "                float att = 1.0 / max(dist * dist, 0.01);\n"
    "                if (range > 0.0) {\n"
    "                    float win = clamp(1.0 - pow(dist / range, 4.0), 0.0, 1.0);\n"
    "                    att *= win * win;\n"
    "                }\n"
    "                vec3 light_rad = point_lights[p].color_and_intensity.rgb * point_lights[p].color_and_intensity.w * att;\n"
    "                if (mat_type > 1.5 && mat_type < 2.5) {\n"
    "                    direct_lighting += albedo * NdotL * light_rad;\n"
    "                } else if (mat_type > 2.5 && mat_type < 3.5) {\n"
    "                    float shininess = max(extra_params.y, 1.0);\n"
    "                    float NdotH = max(dot(N, H), 0.0);\n"
    "                    float spec = pow(NdotH, shininess);\n"
    "                    direct_lighting += (albedo * NdotL + spec * 0.5) * light_rad;\n"
    "                } else if (mat_type > 3.5 && mat_type < 4.5) {\n"
    "                    float steps = max(extra_params.y, 2.0);\n"
    "                    float toon_diff = floor(NdotL * steps) / steps;\n"
    "                    direct_lighting += albedo * toon_diff * light_rad;\n"
    "                } else {\n"
    "                    float NDF = distribution_ggx(N, H, roughness);\n"
    "                    float G = geometry_smith(N, V, L, roughness);\n"
    "                    vec3 F = fresnel_schlick(max(dot(H, V), 0.0), F0);\n"
    "                    vec3 numerator = NDF * G * F;\n"
    "                    float denominator = 4.0 * max(dot(N, V), 0.0001) * NdotL + 0.0001;\n"
    "                    vec3 specular = numerator / denominator;\n"
    "                    vec3 kD = (vec3(1.0) - F) * (1.0 - metallic);\n"
    "                    direct_lighting += (kD * albedo / PI + specular) * light_rad * NdotL;\n"
    "                }\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    for (int s = 0; s < num_spots && s < 8; ++s) {\n"
    "        vec3 to_light = spot_lights[s].position_and_range.xyz - v_world_pos;\n"
    "        float dist = length(to_light);\n"
    "        float range = spot_lights[s].position_and_range.w;\n"
    "        if (range <= 0.0 || dist < range) {\n"
    "            vec3 L = to_light / max(dist, 0.0001);\n"
    "            vec3 spot_dir = normalize(spot_lights[s].direction_and_cast_shadow.xyz);\n"
    "            float cos_theta = dot(-L, spot_dir);\n"
    "            float cos_inner = spot_lights[s].cone_params.x;\n"
    "            float cos_outer = spot_lights[s].cone_params.y;\n"
    "            float spot_factor = clamp((cos_theta - cos_outer) / max(cos_inner - cos_outer, 0.0001), 0.0, 1.0);\n"
    "            if (spot_factor > 0.0) {\n"
    "                vec3 H = normalize(V + L);\n"
    "                float NdotL = max(dot(N, L), 0.0);\n"
    "                if (NdotL > 0.0) {\n"
    "                    float att = 1.0 / max(dist * dist, 0.01);\n"
    "                    if (range > 0.0) {\n"
    "                        float win = clamp(1.0 - pow(dist / range, 4.0), 0.0, 1.0);\n"
    "                        att *= win * win;\n"
    "                    }\n"
    "                    vec3 light_rad = spot_lights[s].color_and_intensity.rgb * spot_lights[s].color_and_intensity.w * att * spot_factor;\n"
    "                    if (mat_type > 1.5 && mat_type < 2.5) {\n"
    "                        direct_lighting += albedo * NdotL * light_rad;\n"
    "                    } else if (mat_type > 2.5 && mat_type < 3.5) {\n"
    "                        float shininess = max(extra_params.y, 1.0);\n"
    "                        float NdotH = max(dot(N, H), 0.0);\n"
    "                        float spec = pow(NdotH, shininess);\n"
    "                        direct_lighting += (albedo * NdotL + spec * 0.5) * light_rad;\n"
    "                    } else if (mat_type > 3.5 && mat_type < 4.5) {\n"
    "                        float steps = max(extra_params.y, 2.0);\n"
    "                        float toon_diff = floor(NdotL * steps) / steps;\n"
    "                        direct_lighting += albedo * toon_diff * light_rad;\n"
    "                    } else {\n"
    "                        float NDF = distribution_ggx(N, H, roughness);\n"
    "                        float G = geometry_smith(N, V, L, roughness);\n"
    "                        vec3 F = fresnel_schlick(max(dot(H, V), 0.0), F0);\n"
    "                        vec3 numerator = NDF * G * F;\n"
    "                        float denominator = 4.0 * max(dot(N, V), 0.0001) * NdotL + 0.0001;\n"
    "                        vec3 specular = numerator / denominator;\n"
    "                        vec3 kD = (vec3(1.0) - F) * (1.0 - metallic);\n"
    "                        direct_lighting += (kD * albedo / PI + specular) * light_rad * NdotL;\n"
    "                    }\n"
    "                }\n"
    "            }\n"
    "        }\n"
    "    }\n"
    "    vec3 final_color = ambient + direct_lighting + emissive;\n"
    "    float fog_type = fog_params.x;\n"
    "    if (fog_type > 0.5) {\n"
    "        float dist = length(v_world_pos - eye_pos.xyz);\n"
    "        float fog_factor = 1.0;\n"
    "        if (fog_type < 1.5) {\n"
    "            float near = fog_params.y;\n"
    "            float far = fog_params.z;\n"
    "            fog_factor = clamp((far - dist) / max(far - near, 0.0001), 0.0, 1.0);\n"
    "        } else {\n"
    "            float density = fog_params.w;\n"
    "            float d = dist * density;\n"
    "            fog_factor = clamp(exp(- d * d), 0.0, 1.0);\n"
    "        }\n"
    "        final_color = mix(fog_color.rgb, final_color, fog_factor);\n"
    "    }\n"
    "    if (fog_color.w > 0.5) final_color = apply_aces_filmic(final_color);\n"
    "    frag_color = vec4(final_color, alpha);\n"
    "}\n";

static const char* glsl_shadow_vs =
    "#version 330\n"
    "layout(location = 0) in vec3 pos;\n"
    "layout(location = 1) in vec3 normal;\n"
    "layout(location = 2) in vec2 uv;\n"
    "layout(location = 3) in vec4 color;\n"
    "layout(location = 4) in vec4 tangent;\n"
    "uniform mat4 light_mvp;\n"
    "out float v_depth;\n"
    "void main() {\n"
    "    vec4 p = light_mvp * vec4(pos, 1.0);\n"
    "    gl_Position = p;\n"
    "    v_depth = p.z / p.w;\n"
    "}\n";

static const char* glsl_shadow_fs =
    "#version 330\n"
    "in float v_depth;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    frag_color = vec4(v_depth, 0.0, 0.0, 1.0);\n"
    "}\n";

static const char* glsl_line_vs =
    "#version 330\n"
    "layout(location = 0) in vec3 pos;\n"
    "layout(location = 1) in vec4 color;\n"
    "uniform mat4 mvp;\n"
    "out vec4 v_color;\n"
    "void main() {\n"
    "    gl_Position = mvp * vec4(pos, 1.0);\n"
    "    v_color = color;\n"
    "}\n";

static const char* glsl_line_fs =
    "#version 330\n"
    "in vec4 v_color;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    frag_color = v_color;\n"
    "}\n";

static const char* glsl_hud_vs =
    "#version 330\n"
    "layout(location = 0) in vec2 pos;\n"
    "layout(location = 1) in vec4 color;\n"
    "uniform mat4 ortho_proj;\n"
    "out vec4 v_color;\n"
    "void main() {\n"
    "    gl_Position = ortho_proj * vec4(pos, 0.0, 1.0);\n"
    "    v_color = color;\n"
    "}\n";

static const char* glsl_hud_fs =
    "#version 330\n"
    "in vec4 v_color;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    frag_color = v_color;\n"
    "}\n";

static const char* glsl_inst_vs =
    "#version 330\n"
    "layout(location = 0) in vec3 pos;\n"
    "layout(location = 1) in vec3 normal;\n"
    "layout(location = 2) in vec2 uv;\n"
    "layout(location = 3) in vec4 color;\n"
    "layout(location = 4) in vec4 tangent;\n"
    "layout(location = 5) in vec4 i_model0;\n"
    "layout(location = 6) in vec4 i_model1;\n"
    "layout(location = 7) in vec4 i_model2;\n"
    "layout(location = 8) in vec4 i_model3;\n"
    "layout(location = 9) in vec4 i_color;\n"
    "uniform mat4 view_proj;\n"
    "uniform mat4 light_vp;\n"
    "out vec4 v_color;\n"
    "out vec3 v_normal;\n"
    "out vec2 v_uv;\n"
    "out vec3 v_world_pos;\n"
    "out vec4 v_light_pos;\n"
    "out vec3 v_tangent;\n"
    "out vec3 v_bitangent;\n"
    "void main() {\n"
    "    mat4 model = mat4(i_model0, i_model1, i_model2, i_model3);\n"
    "    vec4 world_pos = model * vec4(pos, 1.0);\n"
    "    gl_Position = view_proj * world_pos;\n"
    "    v_world_pos = world_pos.xyz;\n"
    "    mat3 nmat = mat3(model);\n"
    "    vec3 N = normalize(nmat * normal);\n"
    "    vec3 T = nmat * tangent.xyz;\n"
    "    vec3 ortho_T = T - dot(T, N) * N;\n"
    "    if (dot(ortho_T, ortho_T) < 0.0001) {\n"
    "        ortho_T = abs(N.y) > 0.99 ? cross(N, vec3(0.0, 0.0, 1.0)) : cross(N, vec3(0.0, 1.0, 0.0));\n"
    "    }\n"
    "    T = normalize(ortho_T);\n"
    "    vec3 B = cross(N, T) * (tangent.w < 0.0 ? -1.0 : 1.0);\n"
    "    v_normal = N;\n"
    "    v_tangent = T;\n"
    "    v_bitangent = B;\n"
    "    v_uv = uv;\n"
    "    v_color = color * i_color;\n"
    "    vec3 normal_bias_offset = N * 0.04;\n"
    "    v_light_pos = light_vp * vec4(world_pos.xyz + normal_bias_offset, 1.0);\n"
    "}\n";

static const char* glsl_inst_shadow_vs =
    "#version 330\n"
    "layout(location = 0) in vec3 pos;\n"
    "layout(location = 1) in vec3 normal;\n"
    "layout(location = 2) in vec2 uv;\n"
    "layout(location = 3) in vec4 color;\n"
    "layout(location = 4) in vec4 tangent;\n"
    "layout(location = 5) in vec4 i_model0;\n"
    "layout(location = 6) in vec4 i_model1;\n"
    "layout(location = 7) in vec4 i_model2;\n"
    "layout(location = 8) in vec4 i_model3;\n"
    "layout(location = 9) in vec4 i_color;\n"
    "uniform mat4 light_vp;\n"
    "out float v_depth;\n"
    "void main() {\n"
    "    mat4 model = mat4(i_model0, i_model1, i_model2, i_model3);\n"
    "    vec4 world_pos = model * vec4(pos, 1.0);\n"
    "    vec4 p = light_vp * world_pos;\n"
    "    gl_Position = p;\n"
    "    v_depth = p.z / p.w;\n"
    "}\n";

// Skybox & Procedural Sky Shaders (GLSL)
static const char* glsl_skybox_vs =
    "#version 330\n"
    "layout(location = 0) in vec3 pos;\n"
    "layout(std140) uniform skybox_vs_params {\n"
    "    mat4 view_proj;\n"
    "};\n"
    "out vec3 v_dir;\n"
    "void main() {\n"
    "    vec4 p = view_proj * vec4(pos, 1.0);\n"
    "    gl_Position = p.xyww;\n"
    "    v_dir = pos;\n"
    "}\n";

static const char* glsl_skybox_fs =
    "#version 330\n"
    "uniform samplerCube tex_sky;\n"
    "in vec3 v_dir;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    vec3 dir = normalize(v_dir);\n"
    "    vec3 col = texture(tex_sky, dir).rgb;\n"
    "    frag_color = vec4(col, 1.0);\n"
    "}\n";

static const char* glsl_proc_sky_vs = glsl_skybox_vs;

static const char* glsl_proc_sky_fs =
    "#version 330\n"
    "layout(std140) uniform proc_sky_fs_params {\n"
    "    vec4 sun_dir_turbidity;\n"
    "    vec4 rayleigh_params;\n"
    "    vec4 mie_params;\n"
    "    vec4 sky_misc;\n"
    "};\n"
    "in vec3 v_dir;\n"
    "out vec4 frag_color;\n"
    "const float PI = 3.14159265359;\n"
    "vec3 apply_aces_filmic_sky(vec3 x) {\n"
    "    float a = 2.51;\n"
    "    float b = 0.03;\n"
    "    float c = 2.43;\n"
    "    float d = 0.59;\n"
    "    float e = 0.14;\n"
    "    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);\n"
    "}\n"
    "void main() {\n"
    "    vec3 V = normalize(v_dir);\n"
    "    vec3 S = normalize(sun_dir_turbidity.xyz);\n"
    "    float cos_gamma = clamp(dot(V, S), -1.0, 1.0);\n"
    "    float phase_r = (3.0 / (16.0 * PI)) * (1.0 + cos_gamma * cos_gamma);\n"
    "    float g = sky_misc.x;\n"
    "    float g2 = g * g;\n"
    "    float denom = pow(max(1.0 + g2 - 2.0 * g * cos_gamma, 0.0001), 1.5);\n"
    "    float phase_m = (1.0 / (4.0 * PI)) * (1.0 - g2) / denom;\n"
    "    vec3 beta_r = rayleigh_params.rgb * rayleigh_params.w * 0.08;\n"
    "    vec3 beta_m = mie_params.rgb * mie_params.w * sun_dir_turbidity.w * 0.04;\n"
    "    float zenith_V = max(V.y, 0.03);\n"
    "    float zenith_S = max(S.y, 0.03);\n"
    "    vec3 T = exp(-(beta_r + beta_m) * (1.0 / zenith_V + 1.0 / zenith_S) * 0.8);\n"
    "    vec3 inscatter = (beta_r * phase_r + beta_m * phase_m) * (vec3(1.0) - T) * 12.0;\n"
    "    float sun_disk = smoothstep(0.9992, 0.9998, cos_gamma) * 25.0;\n"
    "    vec3 sun_color = sun_disk * T * mie_params.rgb;\n"
    "    vec3 sky = inscatter + sun_color;\n"
    "    if (V.y < 0.0) {\n"
    "        vec3 ground = mie_params.rgb * 0.15 * max(S.y, 0.1);\n"
    "        sky = mix(sky, ground, clamp(-V.y * 6.0, 0.0, 1.0));\n"
    "    }\n"
    "    sky = max(sky, vec3(0.015, 0.02, 0.035));\n"
    "    sky = apply_aces_filmic_sky(sky);\n"
    "    frag_color = vec4(sky, 1.0);\n"
    "}\n";
#endif

// ---------------------------------------------------------------------------
// EngineApp Implementation
// ---------------------------------------------------------------------------
static EngineApp* s_active_engine_app = nullptr;

EngineApp::EngineApp() {
    s_active_engine_app = this;
}

EngineApp::EngineApp(const std::string& title, int width, int height) {
    s_active_engine_app = this;
    init(title, width, height);
}

EngineApp::~EngineApp() {
    if (s_active_engine_app == this) {
        s_active_engine_app = nullptr;
    }
    close();
}

void EngineApp::ensure_device() {
    if (sg_isvalid()) {
        if (pip_id_ == 0) {
            init_pipeline_and_shaders();
        }
        return;
    }
#if defined(SOKOL_D3D11)
    D3D_FEATURE_LEVEL feature_levels[] = {
        D3D_FEATURE_LEVEL_11_1,
        D3D_FEATURE_LEVEL_11_0,
        D3D_FEATURE_LEVEL_10_1,
        D3D_FEATURE_LEVEL_10_0
    };
    D3D_FEATURE_LEVEL feature_level;
    ID3D11Device* dev = nullptr;
    ID3D11DeviceContext* ctx = nullptr;

    HRESULT hr = D3D11CreateDevice(
        nullptr,
        D3D_DRIVER_TYPE_HARDWARE,
        nullptr,
        D3D11_CREATE_DEVICE_BGRA_SUPPORT,
        feature_levels,
        sizeof(feature_levels) / sizeof(feature_levels[0]),
        D3D11_SDK_VERSION,
        &dev,
        &feature_level,
        &ctx
    );

    if (FAILED(hr)) {
        hr = D3D11CreateDevice(
            nullptr,
            D3D_DRIVER_TYPE_WARP,
            nullptr,
            D3D11_CREATE_DEVICE_BGRA_SUPPORT,
            feature_levels,
            sizeof(feature_levels) / sizeof(feature_levels[0]),
            D3D11_SDK_VERSION,
            &dev,
            &feature_level,
            &ctx
        );
    }

    if (SUCCEEDED(hr) && dev && ctx) {
        headless_dev_ = dev;
        headless_ctx_ = ctx;

        sg_desc desc{};
        desc.environment.defaults.color_format = SG_PIXELFORMAT_RGBA8;
        desc.environment.defaults.depth_format = SG_PIXELFORMAT_DEPTH;
        desc.environment.defaults.sample_count = 1;
        desc.environment.d3d11.device = dev;
        desc.environment.d3d11.device_context = ctx;
        desc.logger.func = slog_func;
        desc.buffer_pool_size = 16384;
        desc.image_pool_size = 4096;
        desc.sampler_pool_size = 1024;
        desc.shader_pool_size = 2048;
        desc.pipeline_pool_size = 4096;
        desc.view_pool_size = 8192;
        desc.uniform_buffer_size = 8 * 1024 * 1024;
        sg_setup(&desc);

        init_pipeline_and_shaders();
        is_headless_ = true;
    }
#endif
}

EngineApp* EngineApp::active_instance() {
    return s_active_engine_app;
}

void EngineApp::ensure_headless_device() {
    if (sg_isvalid()) return;
    if (s_active_engine_app) {
        s_active_engine_app->ensure_device();
    } else {
#if defined(SOKOL_D3D11)
        D3D_FEATURE_LEVEL feature_levels[] = {
            D3D_FEATURE_LEVEL_11_1,
            D3D_FEATURE_LEVEL_11_0,
            D3D_FEATURE_LEVEL_10_1,
            D3D_FEATURE_LEVEL_10_0
        };
        D3D_FEATURE_LEVEL feature_level;
        ID3D11Device* dev = nullptr;
        ID3D11DeviceContext* ctx = nullptr;

        HRESULT hr = D3D11CreateDevice(
            nullptr,
            D3D_DRIVER_TYPE_HARDWARE,
            nullptr,
            D3D11_CREATE_DEVICE_BGRA_SUPPORT,
            feature_levels,
            sizeof(feature_levels) / sizeof(feature_levels[0]),
            D3D11_SDK_VERSION,
            &dev,
            &feature_level,
            &ctx
        );

        if (FAILED(hr)) {
            hr = D3D11CreateDevice(
                nullptr,
                D3D_DRIVER_TYPE_WARP,
                nullptr,
                D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                feature_levels,
                sizeof(feature_levels) / sizeof(feature_levels[0]),
                D3D11_SDK_VERSION,
                &dev,
                &feature_level,
                &ctx
            );
        }

        if (SUCCEEDED(hr) && dev && ctx) {
            sg_desc desc{};
            desc.environment.defaults.color_format = SG_PIXELFORMAT_RGBA8;
            desc.environment.defaults.depth_format = SG_PIXELFORMAT_DEPTH;
            desc.environment.defaults.sample_count = 1;
            desc.environment.d3d11.device = dev;
            desc.environment.d3d11.device_context = ctx;
            desc.logger.func = slog_func;
            desc.buffer_pool_size = 16384;
            desc.image_pool_size = 4096;
            desc.sampler_pool_size = 1024;
            desc.shader_pool_size = 2048;
            desc.pipeline_pool_size = 4096;
            desc.view_pool_size = 8192;
            desc.uniform_buffer_size = 8 * 1024 * 1024;
            sg_setup(&desc);
        }
#endif
    }
}

void EngineApp::init(const std::string& title, int width, int height) {
    s_active_engine_app = this;
    config_.title = title;
    config_.width = width;
    config_.height = height;
    initialized_ = true;
}

void EngineApp::set_title(const std::string& title) {
    config_.title = title;
    sapp_set_window_title(title.c_str());
}

void EngineApp::set_clear_color(float r, float g, float b, float a) {
    config_.clear_color = { r, g, b, a };
}

void EngineApp::set_update_callback(UpdateCallback callback) {
    update_callback_ = std::move(callback);
}

void EngineApp::set_mouse_locked(bool locked) {
    sapp_lock_mouse(locked);
    sapp_show_mouse(!locked);
#if defined(_WIN32)
    ShowCursor(!locked ? TRUE : FALSE);
#endif
}

bool EngineApp::is_mouse_locked() const {
    return sapp_mouse_locked();
}

void EngineApp::set_shadow_settings(const ShadowSettings& settings) {
    bool res_changed = (settings.resolution != shadow_settings_.resolution);
    shadow_settings_ = settings;
    if (res_changed && shadow_pip_id_ != 0) {
        init_shadow_pipeline();
    }
}

void EngineApp::set_shadow_resolution(int res) {
    if (res == shadow_settings_.resolution) return;
    shadow_settings_.resolution = res;
    if (shadow_pip_id_ != 0) {
        init_shadow_pipeline();
    }
}

void EngineApp::init_shadow_pipeline() {
    int res = shadow_settings_.resolution > 0 ? shadow_settings_.resolution : 2048;

    if (shadow_color_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ shadow_color_view_id_ });
        shadow_color_view_id_ = 0;
    }
    if (shadow_depth_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ shadow_depth_view_id_ });
        shadow_depth_view_id_ = 0;
    }
    if (shadow_tex_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ shadow_tex_view_id_ });
        shadow_tex_view_id_ = 0;
    }
    if (shadow_sampler_id_ != 0) {
        if (sg_isvalid()) sg_destroy_sampler(sg_sampler{ shadow_sampler_id_ });
        shadow_sampler_id_ = 0;
    }
    if (shadow_color_img_id_ != 0) {
        if (sg_isvalid()) sg_destroy_image(sg_image{ shadow_color_img_id_ });
        shadow_color_img_id_ = 0;
    }
    if (shadow_depth_img_id_ != 0) {
        if (sg_isvalid()) sg_destroy_image(sg_image{ shadow_depth_img_id_ });
        shadow_depth_img_id_ = 0;
    }

    // 1. Color attachment image to store depth map
    sg_image_desc col_desc{};
    col_desc.usage.color_attachment = true;
    col_desc.width = res;
    col_desc.height = res;
    col_desc.pixel_format = SG_PIXELFORMAT_R32F;
    col_desc.sample_count = 1;
    col_desc.label = "shadow-color-map";
    sg_image col_img = sg_make_image(&col_desc);
    shadow_color_img_id_ = col_img.id;

    // 2. Depth stencil attachment image for shadow pass
    sg_image_desc depth_desc{};
    depth_desc.usage.depth_stencil_attachment = true;
    depth_desc.width = res;
    depth_desc.height = res;
    depth_desc.pixel_format = SG_PIXELFORMAT_DEPTH;
    depth_desc.sample_count = 1;
    depth_desc.label = "shadow-depth-map";
    sg_image depth_img = sg_make_image(&depth_desc);
    shadow_depth_img_id_ = depth_img.id;

    // 3. Views
    sg_view_desc col_view_desc{};
    col_view_desc.color_attachment.image = col_img;
    col_view_desc.label = "shadow-color-rt-view";
    sg_view col_view = sg_make_view(&col_view_desc);
    shadow_color_view_id_ = col_view.id;

    sg_view_desc depth_view_desc{};
    depth_view_desc.depth_stencil_attachment.image = depth_img;
    depth_view_desc.label = "shadow-depth-rt-view";
    sg_view depth_view = sg_make_view(&depth_view_desc);
    shadow_depth_view_id_ = depth_view.id;

    sg_view_desc tex_view_desc{};
    tex_view_desc.texture.image = col_img;
    tex_view_desc.label = "shadow-tex-sample-view";
    sg_view tex_view = sg_make_view(&tex_view_desc);
    shadow_tex_view_id_ = tex_view.id;

    // 4. Sampler
    sg_sampler_desc smp_desc{};
    smp_desc.min_filter = SG_FILTER_LINEAR;
    smp_desc.mag_filter = SG_FILTER_LINEAR;
    smp_desc.wrap_u = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.wrap_v = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.label = "shadow-sampler";
    sg_sampler smp = sg_make_sampler(&smp_desc);
    shadow_sampler_id_ = smp.id;

    if (shadow_pip_id_ != 0) {
        return;
    }

    // 5. Shader & Pipeline
    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_shadow_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_shadow_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "NORMAL";
    shd_desc.attrs[2].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[2].hlsl_sem_index = 0;
    shd_desc.attrs[3].hlsl_sem_name = "COLOR";
    shd_desc.attrs[3].hlsl_sem_index = 0;
    shd_desc.attrs[4].hlsl_sem_name = "TANGENT";
    shd_desc.attrs[4].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(ShadowVSParams);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;
#endif
    shd_desc.label = "shadow-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shadow_shd_id_ = shd.id;

    sg_pipeline_desc pip_desc{};
    pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[0].offset = offsetof(Vertex, position);
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[1].offset = offsetof(Vertex, normal);
    pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[2].offset = offsetof(Vertex, uv);
    pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
    pip_desc.layout.attrs[3].offset = offsetof(Vertex, color);
    pip_desc.layout.attrs[4].format = SG_VERTEXFORMAT_FLOAT4;
    pip_desc.layout.attrs[4].offset = offsetof(Vertex, tangent);
    pip_desc.shader = shd;
    pip_desc.index_type = SG_INDEXTYPE_UINT16;
    pip_desc.depth.compare = SG_COMPAREFUNC_LESS_EQUAL;
    pip_desc.depth.write_enabled = true;
    pip_desc.face_winding = SG_FACEWINDING_CCW;
    pip_desc.cull_mode = SG_CULLMODE_FRONT;
    pip_desc.colors[0].pixel_format = SG_PIXELFORMAT_R32F;
    pip_desc.depth.pixel_format = SG_PIXELFORMAT_DEPTH;
    pip_desc.label = "shadow-pipeline";
    sg_pipeline pip = sg_make_pipeline(&pip_desc);
    shadow_pip_id_ = pip.id;

    // 6. Instanced Shadow Shader & Pipeline
    sg_shader_desc inst_shd_desc{};
#if defined(SOKOL_D3D11)
    inst_shd_desc.vertex_func.source = hlsl_inst_shadow_vs;
    inst_shd_desc.vertex_func.entry = "main";
    inst_shd_desc.vertex_func.d3d11_target = "vs_4_0";
    inst_shd_desc.fragment_func.source = hlsl_shadow_fs;
    inst_shd_desc.fragment_func.entry = "main";
    inst_shd_desc.fragment_func.d3d11_target = "ps_4_0";

    inst_shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    inst_shd_desc.attrs[1].hlsl_sem_name = "NORMAL";
    inst_shd_desc.attrs[2].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[2].hlsl_sem_index = 0;
    inst_shd_desc.attrs[3].hlsl_sem_name = "COLOR";
    inst_shd_desc.attrs[3].hlsl_sem_index = 0;
    inst_shd_desc.attrs[4].hlsl_sem_name = "TANGENT";
    inst_shd_desc.attrs[4].hlsl_sem_index = 0;
    inst_shd_desc.attrs[5].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[5].hlsl_sem_index = 3;
    inst_shd_desc.attrs[6].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[6].hlsl_sem_index = 4;
    inst_shd_desc.attrs[7].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[7].hlsl_sem_index = 5;
    inst_shd_desc.attrs[8].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[8].hlsl_sem_index = 6;
    inst_shd_desc.attrs[9].hlsl_sem_name = "COLOR";
    inst_shd_desc.attrs[9].hlsl_sem_index = 1;

    inst_shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    inst_shd_desc.uniform_blocks[0].size = sizeof(ShadowVSParams);
    inst_shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;
#else
    inst_shd_desc.vertex_func.source = glsl_inst_shadow_vs;
    inst_shd_desc.fragment_func.source = glsl_shadow_fs;
#endif
    inst_shd_desc.label = "instanced-shadow-shader";
    sg_shader inst_shd = sg_make_shader(&inst_shd_desc);
    instanced_shadow_shd_id_ = inst_shd.id;

    sg_pipeline_desc inst_pip_desc{};
    inst_pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    inst_pip_desc.layout.buffers[0].step_func = SG_VERTEXSTEP_PER_VERTEX;
    inst_pip_desc.layout.buffers[1].stride = sizeof(InstanceData);
    inst_pip_desc.layout.buffers[1].step_func = SG_VERTEXSTEP_PER_INSTANCE;
    inst_pip_desc.layout.buffers[1].step_rate = 1;

    inst_pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    inst_pip_desc.layout.attrs[0].buffer_index = 0;
    inst_pip_desc.layout.attrs[0].offset = offsetof(Vertex, position);
    inst_pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
    inst_pip_desc.layout.attrs[1].buffer_index = 0;
    inst_pip_desc.layout.attrs[1].offset = offsetof(Vertex, normal);
    inst_pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
    inst_pip_desc.layout.attrs[2].buffer_index = 0;
    inst_pip_desc.layout.attrs[2].offset = offsetof(Vertex, uv);
    inst_pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[3].buffer_index = 0;
    inst_pip_desc.layout.attrs[3].offset = offsetof(Vertex, color);
    inst_pip_desc.layout.attrs[4].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[4].buffer_index = 0;
    inst_pip_desc.layout.attrs[4].offset = offsetof(Vertex, tangent);

    inst_pip_desc.layout.attrs[5].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[5].buffer_index = 1;
    inst_pip_desc.layout.attrs[5].offset = 0;
    inst_pip_desc.layout.attrs[6].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[6].buffer_index = 1;
    inst_pip_desc.layout.attrs[6].offset = 16;
    inst_pip_desc.layout.attrs[7].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[7].buffer_index = 1;
    inst_pip_desc.layout.attrs[7].offset = 32;
    inst_pip_desc.layout.attrs[8].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[8].buffer_index = 1;
    inst_pip_desc.layout.attrs[8].offset = 48;
    inst_pip_desc.layout.attrs[9].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[9].buffer_index = 1;
    inst_pip_desc.layout.attrs[9].offset = 64;

    inst_pip_desc.shader = inst_shd;
    inst_pip_desc.index_type = SG_INDEXTYPE_UINT16;
    inst_pip_desc.depth.compare = SG_COMPAREFUNC_LESS_EQUAL;
    inst_pip_desc.depth.write_enabled = true;
    inst_pip_desc.face_winding = SG_FACEWINDING_CCW;
    inst_pip_desc.cull_mode = SG_CULLMODE_FRONT;
    inst_pip_desc.colors[0].pixel_format = SG_PIXELFORMAT_R32F;
    inst_pip_desc.depth.pixel_format = SG_PIXELFORMAT_DEPTH;
    inst_pip_desc.label = "instanced-shadow-pipeline";
    sg_pipeline inst_pip = sg_make_pipeline(&inst_pip_desc);
    instanced_shadow_pip_id_ = inst_pip.id;
}

void EngineApp::init_hud_and_line_pipelines() {
    // Line Pipeline (Debug AABB)
    sg_shader_desc lshd_desc{};
#if defined(SOKOL_D3D11)
    lshd_desc.vertex_func.source = hlsl_line_vs;
    lshd_desc.vertex_func.entry = "main";
    lshd_desc.vertex_func.d3d11_target = "vs_4_0";
    lshd_desc.fragment_func.source = hlsl_line_fs;
    lshd_desc.fragment_func.entry = "main";
    lshd_desc.fragment_func.d3d11_target = "ps_4_0";

    lshd_desc.attrs[0].hlsl_sem_name = "POSITION";
    lshd_desc.attrs[1].hlsl_sem_name = "COLOR";
    lshd_desc.attrs[1].hlsl_sem_index = 0;

    lshd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    lshd_desc.uniform_blocks[0].size = sizeof(LineVSParams);
    lshd_desc.uniform_blocks[0].hlsl_register_b_n = 0;
#endif
    lshd_desc.label = "line-shader";
    sg_shader lshd = sg_make_shader(&lshd_desc);
    line_shd_id_ = lshd.id;

    sg_pipeline_desc lpip_desc{};
    lpip_desc.primitive_type = SG_PRIMITIVETYPE_LINES;
    lpip_desc.layout.buffers[0].stride = sizeof(LineVertex);
    lpip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    lpip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT4;
    lpip_desc.shader = lshd;
    lpip_desc.depth.compare = SG_COMPAREFUNC_ALWAYS;
    lpip_desc.depth.write_enabled = false;
    lpip_desc.cull_mode = SG_CULLMODE_NONE;
    lpip_desc.sample_count = sapp_sample_count();
    lpip_desc.label = "line-pipeline";
    sg_pipeline lpip = sg_make_pipeline(&lpip_desc);
    line_pip_id_ = lpip.id;

    sg_buffer_desc lbuf_desc{};
    lbuf_desc.size = 8192 * sizeof(LineVertex);
    lbuf_desc.usage.vertex_buffer = true;
    lbuf_desc.usage.dynamic_update = true;
    lbuf_desc.label = "line-dynamic-vbuf";
    sg_buffer lbuf = sg_make_buffer(&lbuf_desc);
    line_vbuf_id_ = lbuf.id;

    // HUD Pipeline (2D Screen overlay)
    sg_shader_desc hshd_desc{};
#if defined(SOKOL_D3D11)
    hshd_desc.vertex_func.source = hlsl_hud_vs;
    hshd_desc.vertex_func.entry = "main";
    hshd_desc.vertex_func.d3d11_target = "vs_4_0";
    hshd_desc.fragment_func.source = hlsl_hud_fs;
    hshd_desc.fragment_func.entry = "main";
    hshd_desc.fragment_func.d3d11_target = "ps_4_0";

    hshd_desc.attrs[0].hlsl_sem_name = "POSITION";
    hshd_desc.attrs[1].hlsl_sem_name = "COLOR";
    hshd_desc.attrs[1].hlsl_sem_index = 0;

    hshd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    hshd_desc.uniform_blocks[0].size = sizeof(HUDVSParams);
    hshd_desc.uniform_blocks[0].hlsl_register_b_n = 0;
#endif
    hshd_desc.label = "hud-shader";
    sg_shader hshd = sg_make_shader(&hshd_desc);
    hud_shd_id_ = hshd.id;

    sg_pipeline_desc hpip_desc{};
    hpip_desc.primitive_type = SG_PRIMITIVETYPE_TRIANGLES;
    hpip_desc.layout.buffers[0].stride = sizeof(HUDVertex);
    hpip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT2;
    hpip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT4;
    hpip_desc.shader = hshd;
    hpip_desc.depth.compare = SG_COMPAREFUNC_ALWAYS;
    hpip_desc.depth.write_enabled = false;
    hpip_desc.cull_mode = SG_CULLMODE_NONE;
    hpip_desc.sample_count = sapp_sample_count();
    hpip_desc.colors[0].blend.enabled = true;
    hpip_desc.colors[0].blend.src_factor_rgb = SG_BLENDFACTOR_SRC_ALPHA;
    hpip_desc.colors[0].blend.dst_factor_rgb = SG_BLENDFACTOR_ONE_MINUS_SRC_ALPHA;
    hpip_desc.label = "hud-pipeline";
    sg_pipeline hpip = sg_make_pipeline(&hpip_desc);
    hud_pip_id_ = hpip.id;

    sg_buffer_desc hbuf_desc{};
    hbuf_desc.size = 16384 * sizeof(HUDVertex);
    hbuf_desc.usage.vertex_buffer = true;
    hbuf_desc.usage.dynamic_update = true;
    hbuf_desc.label = "hud-dynamic-vbuf";
    sg_buffer hbuf = sg_make_buffer(&hbuf_desc);
    hud_vbuf_id_ = hbuf.id;
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
    shd_desc.attrs[4].hlsl_sem_name = "TANGENT";
    shd_desc.attrs[4].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(VSParams);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.uniform_blocks[1].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[1].size = sizeof(FSParams);
    shd_desc.uniform_blocks[1].hlsl_register_b_n = 1;

    shd_desc.uniform_blocks[2].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[2].size = sizeof(LightParamsUBO);
    shd_desc.uniform_blocks[2].hlsl_register_b_n = 2;

    for (int i = 0; i < 6; ++i) {
        shd_desc.views[i].texture.stage = SG_SHADERSTAGE_FRAGMENT;
        shd_desc.views[i].texture.image_type = SG_IMAGETYPE_2D;
        shd_desc.views[i].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
        shd_desc.views[i].texture.hlsl_register_t_n = i;

        shd_desc.samplers[i].stage = SG_SHADERSTAGE_FRAGMENT;
        shd_desc.samplers[i].sampler_type = SG_SAMPLERTYPE_FILTERING;
        shd_desc.samplers[i].hlsl_register_s_n = i;
    }
    shd_desc.views[6].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[6].texture.image_type = SG_IMAGETYPE_CUBE;
    shd_desc.views[6].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[6].texture.hlsl_register_t_n = 6;

    shd_desc.samplers[6].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[6].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[6].hlsl_register_s_n = 6;
#else
    shd_desc.vertex_func.source = glsl_vs;
    shd_desc.fragment_func.source = glsl_fs;
#endif
    shd_desc.label = "pbr-daylight-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    // Pipeline with Depth Test
    sg_pipeline_desc pip_desc{};
    pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[0].offset = offsetof(Vertex, position);
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[1].offset = offsetof(Vertex, normal);
    pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[2].offset = offsetof(Vertex, uv);
    pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
    pip_desc.layout.attrs[3].offset = offsetof(Vertex, color);
    pip_desc.layout.attrs[4].format = SG_VERTEXFORMAT_FLOAT4;
    pip_desc.layout.attrs[4].offset = offsetof(Vertex, tangent);
    pip_desc.shader = shd;
    pip_desc.index_type = SG_INDEXTYPE_UINT16;
    pip_desc.depth.compare = SG_COMPAREFUNC_LESS_EQUAL;
    pip_desc.depth.write_enabled = true;
    pip_desc.face_winding = SG_FACEWINDING_CCW;
    pip_desc.cull_mode = SG_CULLMODE_BACK;
    pip_desc.sample_count = sapp_sample_count();
    pip_desc.label = "pbr-daylight-pipeline";
    sg_pipeline pip = sg_make_pipeline(&pip_desc);
    pip_id_ = pip.id;

    // Instanced Scene Shader & Pipeline
    sg_shader_desc inst_shd_desc{};
#if defined(SOKOL_D3D11)
    inst_shd_desc.vertex_func.source = hlsl_inst_vs;
    inst_shd_desc.vertex_func.entry = "main";
    inst_shd_desc.vertex_func.d3d11_target = "vs_4_0";
    inst_shd_desc.fragment_func.source = hlsl_fs;
    inst_shd_desc.fragment_func.entry = "main";
    inst_shd_desc.fragment_func.d3d11_target = "ps_4_0";

    inst_shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    inst_shd_desc.attrs[1].hlsl_sem_name = "NORMAL";
    inst_shd_desc.attrs[2].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[2].hlsl_sem_index = 0;
    inst_shd_desc.attrs[3].hlsl_sem_name = "COLOR";
    inst_shd_desc.attrs[3].hlsl_sem_index = 0;
    inst_shd_desc.attrs[4].hlsl_sem_name = "TANGENT";
    inst_shd_desc.attrs[4].hlsl_sem_index = 0;
    inst_shd_desc.attrs[5].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[5].hlsl_sem_index = 3;
    inst_shd_desc.attrs[6].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[6].hlsl_sem_index = 4;
    inst_shd_desc.attrs[7].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[7].hlsl_sem_index = 5;
    inst_shd_desc.attrs[8].hlsl_sem_name = "TEXCOORD";
    inst_shd_desc.attrs[8].hlsl_sem_index = 6;
    inst_shd_desc.attrs[9].hlsl_sem_name = "COLOR";
    inst_shd_desc.attrs[9].hlsl_sem_index = 1;

    inst_shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    inst_shd_desc.uniform_blocks[0].size = sizeof(InstancedVSParams);
    inst_shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    inst_shd_desc.uniform_blocks[1].stage = SG_SHADERSTAGE_FRAGMENT;
    inst_shd_desc.uniform_blocks[1].size = sizeof(FSParams);
    inst_shd_desc.uniform_blocks[1].hlsl_register_b_n = 1;

    inst_shd_desc.uniform_blocks[2].stage = SG_SHADERSTAGE_FRAGMENT;
    inst_shd_desc.uniform_blocks[2].size = sizeof(LightParamsUBO);
    inst_shd_desc.uniform_blocks[2].hlsl_register_b_n = 2;

    for (int i = 0; i < 6; ++i) {
        inst_shd_desc.views[i].texture.stage = SG_SHADERSTAGE_FRAGMENT;
        inst_shd_desc.views[i].texture.image_type = SG_IMAGETYPE_2D;
        inst_shd_desc.views[i].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
        inst_shd_desc.views[i].texture.hlsl_register_t_n = i;

        inst_shd_desc.samplers[i].stage = SG_SHADERSTAGE_FRAGMENT;
        inst_shd_desc.samplers[i].sampler_type = SG_SAMPLERTYPE_FILTERING;
        inst_shd_desc.samplers[i].hlsl_register_s_n = i;
    }
    inst_shd_desc.views[6].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    inst_shd_desc.views[6].texture.image_type = SG_IMAGETYPE_CUBE;
    inst_shd_desc.views[6].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    inst_shd_desc.views[6].texture.hlsl_register_t_n = 6;

    inst_shd_desc.samplers[6].stage = SG_SHADERSTAGE_FRAGMENT;
    inst_shd_desc.samplers[6].sampler_type = SG_SAMPLERTYPE_FILTERING;
    inst_shd_desc.samplers[6].hlsl_register_s_n = 6;
#else
    inst_shd_desc.vertex_func.source = glsl_inst_vs;
    inst_shd_desc.fragment_func.source = glsl_fs;
#endif
    inst_shd_desc.label = "instanced-scene-shader";
    sg_shader inst_shd = sg_make_shader(&inst_shd_desc);
    instanced_shd_id_ = inst_shd.id;

    sg_pipeline_desc inst_pip_desc{};
    inst_pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    inst_pip_desc.layout.buffers[0].step_func = SG_VERTEXSTEP_PER_VERTEX;
    inst_pip_desc.layout.buffers[1].stride = sizeof(InstanceData);
    inst_pip_desc.layout.buffers[1].step_func = SG_VERTEXSTEP_PER_INSTANCE;
    inst_pip_desc.layout.buffers[1].step_rate = 1;

    inst_pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    inst_pip_desc.layout.attrs[0].buffer_index = 0;
    inst_pip_desc.layout.attrs[0].offset = offsetof(Vertex, position);
    inst_pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
    inst_pip_desc.layout.attrs[1].buffer_index = 0;
    inst_pip_desc.layout.attrs[1].offset = offsetof(Vertex, normal);
    inst_pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
    inst_pip_desc.layout.attrs[2].buffer_index = 0;
    inst_pip_desc.layout.attrs[2].offset = offsetof(Vertex, uv);
    inst_pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[3].buffer_index = 0;
    inst_pip_desc.layout.attrs[3].offset = offsetof(Vertex, color);
    inst_pip_desc.layout.attrs[4].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[4].buffer_index = 0;
    inst_pip_desc.layout.attrs[4].offset = offsetof(Vertex, tangent);

    inst_pip_desc.layout.attrs[5].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[5].buffer_index = 1;
    inst_pip_desc.layout.attrs[5].offset = 0;
    inst_pip_desc.layout.attrs[6].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[6].buffer_index = 1;
    inst_pip_desc.layout.attrs[6].offset = 16;
    inst_pip_desc.layout.attrs[7].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[7].buffer_index = 1;
    inst_pip_desc.layout.attrs[7].offset = 32;
    inst_pip_desc.layout.attrs[8].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[8].buffer_index = 1;
    inst_pip_desc.layout.attrs[8].offset = 48;
    inst_pip_desc.layout.attrs[9].format = SG_VERTEXFORMAT_FLOAT4;
    inst_pip_desc.layout.attrs[9].buffer_index = 1;
    inst_pip_desc.layout.attrs[9].offset = 64;

    inst_pip_desc.shader = inst_shd;
    inst_pip_desc.index_type = SG_INDEXTYPE_UINT16;
    inst_pip_desc.depth.compare = SG_COMPAREFUNC_LESS_EQUAL;
    inst_pip_desc.depth.write_enabled = true;
    inst_pip_desc.face_winding = SG_FACEWINDING_CCW;
    inst_pip_desc.cull_mode = SG_CULLMODE_BACK;
    inst_pip_desc.sample_count = sapp_sample_count();
    inst_pip_desc.label = "instanced-scene-pipeline";
    sg_pipeline inst_pip = sg_make_pipeline(&inst_pip_desc);
    instanced_pip_id_ = inst_pip.id;

    // Initialize Default PBR Textures
    default_white_tex_ = Texture::create_solid_color(255, 255, 255, 255);
    default_white_tex_->ensure_gpu_resources();

    default_black_tex_ = Texture::create_solid_color(0, 0, 0, 255);
    default_black_tex_->ensure_gpu_resources();

    default_flat_normal_tex_ = Texture::create_solid_color(128, 128, 255, 255);
    default_flat_normal_tex_->ensure_gpu_resources();

    init_shadow_pipeline();
    init_hud_and_line_pipelines();
    init_sky_pipelines();
}

void EngineApp::on_init() {
    sg_desc desc{};
    desc.environment = sglue_environment();
    desc.logger.func = slog_func;
    desc.buffer_pool_size = 16384;
    desc.image_pool_size = 4096;
    desc.sampler_pool_size = 1024;
    desc.shader_pool_size = 2048;
    desc.pipeline_pool_size = 4096;
    desc.view_pool_size = 8192;
    desc.uniform_buffer_size = 8 * 1024 * 1024;
    sg_setup(&desc);

    init_pipeline_and_shaders();
    audio_.init();
    editor_.init();
}

void EngineApp::init_sky_pipelines() {
    if (!sg_isvalid()) return;

    // 1. Sky cube mesh and default environment cubemap
    if (!sky_cube_mesh_) {
        sky_cube_mesh_ = Mesh::create_box(2.0f, 2.0f, 2.0f);
    }
    sky_cube_mesh_->ensure_gpu_buffers();

    if (!default_env_cube_) {
        default_env_cube_ = CubeTexture::create_default();
    }
    default_env_cube_->ensure_gpu_resources();

    // 2. Skybox Shader & Pipelines
    sg_shader_desc sky_shd_desc{};
#if defined(SOKOL_D3D11)
    sky_shd_desc.vertex_func.source = hlsl_skybox_vs;
    sky_shd_desc.vertex_func.entry = "main";
    sky_shd_desc.vertex_func.d3d11_target = "vs_4_0";
    sky_shd_desc.fragment_func.source = hlsl_skybox_fs;
    sky_shd_desc.fragment_func.entry = "main";
    sky_shd_desc.fragment_func.d3d11_target = "ps_4_0";

    sky_shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    sky_shd_desc.attrs[1].hlsl_sem_name = "NORMAL";
    sky_shd_desc.attrs[2].hlsl_sem_name = "TEXCOORD";
    sky_shd_desc.attrs[2].hlsl_sem_index = 0;
    sky_shd_desc.attrs[3].hlsl_sem_name = "COLOR";
    sky_shd_desc.attrs[3].hlsl_sem_index = 0;
    sky_shd_desc.attrs[4].hlsl_sem_name = "TANGENT";
    sky_shd_desc.attrs[4].hlsl_sem_index = 0;

    sky_shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    sky_shd_desc.uniform_blocks[0].size = sizeof(SkyboxVSParams);
    sky_shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    sky_shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    sky_shd_desc.views[0].texture.image_type = SG_IMAGETYPE_CUBE;
    sky_shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    sky_shd_desc.views[0].texture.hlsl_register_t_n = 0;

    sky_shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    sky_shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    sky_shd_desc.samplers[0].hlsl_register_s_n = 0;
#else
    sky_shd_desc.vertex_func.source = glsl_skybox_vs;
    sky_shd_desc.fragment_func.source = glsl_skybox_fs;
#endif
    sky_shd_desc.label = "skybox-shader";
    sg_shader sky_shd = sg_make_shader(&sky_shd_desc);
    skybox_shd_id_ = sky_shd.id;

    // Window swapchain pipeline
    sg_pipeline_desc sky_pip_desc{};
    sky_pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    sky_pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    sky_pip_desc.layout.attrs[0].offset = offsetof(Vertex, position);
    sky_pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
    sky_pip_desc.layout.attrs[1].offset = offsetof(Vertex, normal);
    sky_pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
    sky_pip_desc.layout.attrs[2].offset = offsetof(Vertex, uv);
    sky_pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
    sky_pip_desc.layout.attrs[3].offset = offsetof(Vertex, color);
    sky_pip_desc.layout.attrs[4].format = SG_VERTEXFORMAT_FLOAT4;
    sky_pip_desc.layout.attrs[4].offset = offsetof(Vertex, tangent);
    sky_pip_desc.shader = sky_shd;
    sky_pip_desc.index_type = SG_INDEXTYPE_UINT16;
    sky_pip_desc.depth.compare = SG_COMPAREFUNC_LESS_EQUAL;
    sky_pip_desc.depth.write_enabled = false;
    sky_pip_desc.face_winding = SG_FACEWINDING_CCW;
    sky_pip_desc.cull_mode = SG_CULLMODE_FRONT;
    sky_pip_desc.sample_count = sapp_sample_count();
    sky_pip_desc.label = "skybox-pipeline";
    sg_pipeline sky_pip = sg_make_pipeline(&sky_pip_desc);
    skybox_pip_id_ = sky_pip.id;

    // Offscreen RGBA16F pipeline
    sg_pipeline_desc sky_off_desc = sky_pip_desc;
    sky_off_desc.sample_count = 1;
    sky_off_desc.colors[0].pixel_format = SG_PIXELFORMAT_RGBA16F;
    sky_off_desc.label = "skybox-offscreen-pipeline";
    skybox_offscreen_pip_id_ = sg_make_pipeline(&sky_off_desc).id;

    // Cubemap RGBA8 pipeline
    sg_pipeline_desc sky_cube_desc = sky_pip_desc;
    sky_cube_desc.sample_count = 1;
    sky_cube_desc.colors[0].pixel_format = SG_PIXELFORMAT_RGBA8;
    sky_cube_desc.label = "skybox-rgba8-pipeline";
    skybox_rgba8_pip_id_ = sg_make_pipeline(&sky_cube_desc).id;

    // 3. Procedural Sky Shader & Pipelines
    sg_shader_desc psky_shd_desc{};
#if defined(SOKOL_D3D11)
    psky_shd_desc.vertex_func.source = hlsl_proc_sky_vs;
    psky_shd_desc.vertex_func.entry = "main";
    psky_shd_desc.vertex_func.d3d11_target = "vs_4_0";
    psky_shd_desc.fragment_func.source = hlsl_proc_sky_fs;
    psky_shd_desc.fragment_func.entry = "main";
    psky_shd_desc.fragment_func.d3d11_target = "ps_4_0";

    psky_shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    psky_shd_desc.attrs[1].hlsl_sem_name = "NORMAL";
    psky_shd_desc.attrs[2].hlsl_sem_name = "TEXCOORD";
    psky_shd_desc.attrs[2].hlsl_sem_index = 0;
    psky_shd_desc.attrs[3].hlsl_sem_name = "COLOR";
    psky_shd_desc.attrs[3].hlsl_sem_index = 0;
    psky_shd_desc.attrs[4].hlsl_sem_name = "TANGENT";
    psky_shd_desc.attrs[4].hlsl_sem_index = 0;

    psky_shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    psky_shd_desc.uniform_blocks[0].size = sizeof(SkyboxVSParams);
    psky_shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    psky_shd_desc.uniform_blocks[1].stage = SG_SHADERSTAGE_FRAGMENT;
    psky_shd_desc.uniform_blocks[1].size = sizeof(ProcSkyFSParams);
    psky_shd_desc.uniform_blocks[1].hlsl_register_b_n = 1;
#else
    psky_shd_desc.vertex_func.source = glsl_proc_sky_vs;
    psky_shd_desc.fragment_func.source = glsl_proc_sky_fs;
#endif
    psky_shd_desc.label = "proc-sky-shader";
    sg_shader psky_shd = sg_make_shader(&psky_shd_desc);
    proc_sky_shd_id_ = psky_shd.id;

    sg_pipeline_desc psky_pip_desc = sky_pip_desc;
    psky_pip_desc.shader = psky_shd;
    psky_pip_desc.label = "proc-sky-pipeline";
    proc_sky_pip_id_ = sg_make_pipeline(&psky_pip_desc).id;

    sg_pipeline_desc psky_off_desc = sky_off_desc;
    psky_off_desc.shader = psky_shd;
    psky_off_desc.label = "proc-sky-offscreen-pipeline";
    proc_sky_offscreen_pip_id_ = sg_make_pipeline(&psky_off_desc).id;

    sg_pipeline_desc psky_cube_desc = sky_cube_desc;
    psky_cube_desc.shader = psky_shd;
    psky_cube_desc.label = "proc-sky-rgba8-pipeline";
    proc_sky_rgba8_pip_id_ = sg_make_pipeline(&psky_cube_desc).id;
}

void EngineApp::render_background_pass(Scene& scene, Camera& camera, bool is_offscreen, uint32_t color_format) {
    uint32_t sky_pip = skybox_pip_id_;
    uint32_t psky_pip = proc_sky_pip_id_;

    if (is_offscreen) {
        if (color_format == static_cast<uint32_t>(SG_PIXELFORMAT_RGBA8)) {
            sky_pip = skybox_rgba8_pip_id_;
            psky_pip = proc_sky_rgba8_pip_id_;
        } else {
            sky_pip = skybox_offscreen_pip_id_;
            psky_pip = proc_sky_offscreen_pip_id_;
        }
    }

    if (scene.background_type() == BackgroundType::CubeMap && scene.background_cube()) {
        if (sky_pip == 0 || !sky_cube_mesh_ || !sky_cube_mesh_->ensure_gpu_buffers()) return;
        auto cube = scene.background_cube();
        if (!cube->ensure_gpu_resources() || !cube->is_valid()) return;

        sg_pipeline pip{ sky_pip };
        sg_apply_pipeline(pip);

        glm::mat4 view_no_trans = glm::mat4(glm::mat3(camera.view_matrix()));
        glm::mat4 vp = camera.projection_matrix() * view_no_trans;
        SkyboxVSParams vs{ vp };
        sg_apply_uniforms(0, SG_RANGE_REF(vs));

        sg_bindings bind{};
        bind.vertex_buffers[0] = sg_buffer{ sky_cube_mesh_->vbuf_id };
        bind.index_buffer = sg_buffer{ sky_cube_mesh_->ibuf_id };
        bind.views[0] = sg_view{ cube->view_id };
        bind.samplers[0] = sg_sampler{ cube->sampler_id };
        sg_apply_bindings(&bind);

        sg_draw(0, sky_cube_mesh_->num_indices, 1);
        stats_.draw_calls++;
        stats_.total_triangles += sky_cube_mesh_->num_indices / 3;
    } else if (scene.background_type() == BackgroundType::ProceduralSky && scene.procedural_sky()) {
        if (psky_pip == 0 || !sky_cube_mesh_ || !sky_cube_mesh_->ensure_gpu_buffers()) return;
        auto sky = scene.procedural_sky();

        sg_pipeline pip{ psky_pip };
        sg_apply_pipeline(pip);

        glm::mat4 view_no_trans = glm::mat4(glm::mat3(camera.view_matrix()));
        glm::mat4 vp = camera.projection_matrix() * view_no_trans;
        SkyboxVSParams vs{ vp };
        sg_apply_uniforms(0, SG_RANGE_REF(vs));

        ProcSkyFSParams fs{};
        fs.sun_dir_turbidity = glm::vec4(sky->sun_direction(), sky->turbidity());
        fs.rayleigh_params = glm::vec4(sky->rayleigh_color(), sky->rayleigh());
        fs.mie_params = glm::vec4(sky->mie_color(), sky->mie_coefficient());
        fs.sky_misc = glm::vec4(sky->mie_directional_g(), sky->time_of_day(), 0.0f, 0.0f);
        sg_apply_uniforms(1, SG_RANGE_REF(fs));

        sg_bindings bind{};
        bind.vertex_buffers[0] = sg_buffer{ sky_cube_mesh_->vbuf_id };
        bind.index_buffer = sg_buffer{ sky_cube_mesh_->ibuf_id };
        sg_apply_bindings(&bind);

        sg_draw(0, sky_cube_mesh_->num_indices, 1);
        stats_.draw_calls++;
        stats_.total_triangles += sky_cube_mesh_->num_indices / 3;
    }
}

void EngineApp::render_cube_camera(Scene& scene, CubeCamera& cam) {
    auto rt = cam.render_target();
    if (!rt) return;

    glm::vec3 pos = cam.world_position();

    static const glm::vec3 targets[6] = {
        glm::vec3( 1.0f,  0.0f,  0.0f), // +X
        glm::vec3(-1.0f,  0.0f,  0.0f), // -X
        glm::vec3( 0.0f,  1.0f,  0.0f), // +Y
        glm::vec3( 0.0f, -1.0f,  0.0f), // -Y
        glm::vec3( 0.0f,  0.0f,  1.0f), // +Z
        glm::vec3( 0.0f,  0.0f, -1.0f)  // -Z
    };
    static const glm::vec3 ups[6] = {
        glm::vec3( 0.0f, -1.0f,  0.0f), // +X
        glm::vec3( 0.0f, -1.0f,  0.0f), // -X
        glm::vec3( 0.0f,  0.0f,  1.0f), // +Y
        glm::vec3( 0.0f,  0.0f, -1.0f), // -Y
        glm::vec3( 0.0f, -1.0f,  0.0f), // +Z
        glm::vec3( 0.0f, -1.0f,  0.0f)  // -Z
    };

    int res = rt->resolution();
    Camera face_cam;
    face_cam.type = CameraType::Perspective;
    face_cam.fov = 90.0f;
    face_cam.aspect = 1.0f;
    face_cam.near_plane = cam.near_plane();
    face_cam.far_plane = cam.far_plane();
    face_cam.position = pos;

    for (int f = 0; f < 6; ++f) {
        face_cam.target = pos + targets[f];
        face_cam.up = ups[f];

        sg_pass pass{};
        pass.action.colors[0].load_action = SG_LOADACTION_CLEAR;
        pass.action.colors[0].clear_value = { 0.1f, 0.1f, 0.1f, 1.0f };
        pass.action.depth.load_action = SG_LOADACTION_CLEAR;
        pass.action.depth.clear_value = 1.0f;
        pass.attachments.colors[0] = sg_view{ rt->face_view_id(f) };
        pass.attachments.depth_stencil = sg_view{ rt->depth_view_id() };
        pass.label = "cubecamera-face-pass";

        sg_begin_pass(&pass);
        render_scene_pass(scene, face_cam, res, res, true, static_cast<uint32_t>(SG_PIXELFORMAT_RGBA8));
        sg_end_pass();
    }
}

void EngineApp::render_shadow_pass(Scene* scene_override, Camera* camera_override) {
    if (shadow_pip_id_ == 0 || shadow_color_view_id_ == 0 || shadow_depth_view_id_ == 0) {
        return;
    }

    Scene& sc = scene_override ? *scene_override : scene_;
    Camera& cam = camera_override ? *camera_override : camera_;

    // 1. Check for SpotLight casting shadows
    std::shared_ptr<SpotLight> casting_spot = nullptr;
    for (const auto& l : sc.lights()) {
        if (!l) continue;
        if (l->type == LightType::Spot) {
            auto sl = std::dynamic_pointer_cast<SpotLight>(l);
            if (sl && sl->cast_shadow) {
                casting_spot = sl;
                break;
            }
        }
    }

    if (casting_spot) {
        glm::vec3 light_pos = casting_spot->get_world_position();
        glm::vec3 light_dir = glm::normalize(casting_spot->get_world_direction());
        glm::vec3 up = std::abs(light_dir.y) > 0.99f ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
        glm::mat4 light_view = glm::lookAt(light_pos, light_pos + light_dir, up);
        float fov_rad = casting_spot->outer_cone_angle * 2.0f;
        float near_z = 0.5f;
        float far_z = std::max(casting_spot->range, 25.0f);
        glm::mat4 light_proj = glm::perspective(fov_rad, 1.0f, near_z, far_z);
        light_vp_ = light_proj * light_view;
    } else {
        // Directional Light with camera-following shadow box and texel snapping
        std::shared_ptr<DirectionalLight> casting_dir = nullptr;
        for (const auto& l : sc.lights()) {
            if (!l) continue;
            if (l->type == LightType::Directional) {
                auto dl = std::dynamic_pointer_cast<DirectionalLight>(l);
                if (dl && dl->cast_shadow) {
                    casting_dir = dl;
                    break;
                }
            }
        }
        glm::vec3 sun_dir = casting_dir ? glm::normalize(casting_dir->get_world_direction()) : glm::normalize(sc.light.direction);
        if (glm::length(sun_dir) < 0.001f) {
            sun_dir = glm::vec3(0.4f, -0.8f, 0.4f);
        }

        glm::vec3 center = cam.parent() ? cam.world_position() : cam.position;
        glm::vec3 light_up = std::abs(sun_dir.y) > 0.99f ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
        float dist = shadow_settings_.far_z * 0.5f;
        glm::vec3 light_pos = center - sun_dir * dist;
        glm::mat4 light_view = glm::lookAt(light_pos, center, light_up);

        if (shadow_settings_.texel_snapping && shadow_settings_.resolution > 0) {
            glm::vec4 center_ls = light_view * glm::vec4(center, 1.0f);
            float texel_size = (2.0f * shadow_settings_.ortho_size) / static_cast<float>(shadow_settings_.resolution);
            center_ls.x = std::floor(center_ls.x / texel_size) * texel_size;
            center_ls.y = std::floor(center_ls.y / texel_size) * texel_size;
            glm::vec4 snapped_center_ws = glm::inverse(light_view) * center_ls;
            glm::vec3 snapped_center = glm::vec3(snapped_center_ws);
            light_pos = snapped_center - sun_dir * dist;
            light_view = glm::lookAt(light_pos, snapped_center, light_up);
        }

        float o = shadow_settings_.ortho_size;
        glm::mat4 light_proj = glm::ortho(-o, o, -o, o, shadow_settings_.near_z, shadow_settings_.far_z);
        light_vp_ = light_proj * light_view;
    }

    // 2. Begin Shadow Render Pass
    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_CLEAR;
    pass.action.colors[0].clear_value = { 1.0f, 1.0f, 1.0f, 1.0f };
    pass.action.depth.load_action = SG_LOADACTION_CLEAR;
    pass.action.depth.clear_value = 1.0f;
    pass.attachments.colors[0] = sg_view{ shadow_color_view_id_ };
    pass.attachments.depth_stencil = sg_view{ shadow_depth_view_id_ };
    pass.label = "shadow-pass";

    sg_begin_pass(&pass);
    sg_pipeline pip{ shadow_pip_id_ };
    sg_apply_pipeline(pip);

    for (const auto& entity : sc.entities()) {
        if (!entity || !entity->visible || !entity->mesh || !entity->cast_shadows) continue;
        if (!entity->mesh->ensure_gpu_buffers()) continue;

        glm::mat4 model = entity->world_model_matrix();
        ShadowVSParams vs_params{ light_vp_ * model };

        sg_bindings bind{};
        bind.vertex_buffers[0] = sg_buffer{ entity->mesh->vbuf_id };
        bind.index_buffer = sg_buffer{ entity->mesh->ibuf_id };
        sg_apply_bindings(&bind);

        sg_apply_uniforms(0, SG_RANGE_REF(vs_params));
        sg_draw(0, entity->mesh->num_indices, 1);
    }

    if (instanced_shadow_pip_id_ != 0 && !sc.instanced_meshes().empty()) {
        sg_pipeline inst_pip{ instanced_shadow_pip_id_ };
        sg_apply_pipeline(inst_pip);

        ShadowVSParams vs_params{ light_vp_ };
        sg_apply_uniforms(0, SG_RANGE_REF(vs_params));

        for (const auto& inst_mesh : sc.instanced_meshes()) {
            if (!inst_mesh || !inst_mesh->mesh || inst_mesh->instance_count() == 0) continue;
            if (!inst_mesh->ensure_gpu_buffers()) continue;

            sg_bindings bind{};
            bind.vertex_buffers[0] = sg_buffer{ inst_mesh->mesh->vbuf_id };
            bind.vertex_buffers[1] = sg_buffer{ inst_mesh->inst_vbuf_id };
            bind.index_buffer = sg_buffer{ inst_mesh->mesh->ibuf_id };
            sg_apply_bindings(&bind);

            sg_draw(0, inst_mesh->mesh->num_indices, static_cast<int>(inst_mesh->instance_count()));
        }
    }

    sg_end_pass();
}

void EngineApp::render_debug_hitboxes(const glm::mat4& vp) {
    if (line_pip_id_ == 0 || line_vbuf_id_ == 0) return;

    std::vector<LineVertex> verts;
    verts.reserve(2048);

    glm::vec4 green{ 0.15f, 0.95f, 0.25f, 1.0f };

    for (const auto& entity : scene_.entities()) {
        if (!entity || !entity->visible || !entity->has_collision || !entity->mesh) continue;
        if (!entity->local_collision_box().is_valid()) continue;

        auto c = entity->world_obb_corners();

        static const int edges[12][2] = {
            {0,1}, {1,2}, {2,3}, {3,0},
            {4,5}, {5,6}, {6,7}, {7,4},
            {0,4}, {1,5}, {2,6}, {3,7}
        };

        for (int i = 0; i < 12; ++i) {
            verts.push_back({ c[edges[i][0]], green });
            verts.push_back({ c[edges[i][1]], green });
        }
    }

    if (verts.empty()) return;

    size_t count = std::min(verts.size(), static_cast<size_t>(8192));
    sg_range range{ verts.data(), count * sizeof(LineVertex) };
    sg_update_buffer(sg_buffer{ line_vbuf_id_ }, &range);

    sg_pipeline pip{ line_pip_id_ };
    sg_apply_pipeline(pip);

    LineVSParams vs{ vp };
    sg_apply_uniforms(0, SG_RANGE_REF(vs));

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ line_vbuf_id_ };
    sg_apply_bindings(&bind);

    sg_draw(0, static_cast<int>(count), 1);
}

namespace {

void add_rect(std::vector<HUDVertex>& verts, float x0, float y0, float x1, float y1, const glm::vec4& color) {
    verts.push_back({ { x0, y0 }, color });
    verts.push_back({ { x1, y0 }, color });
    verts.push_back({ { x1, y1 }, color });

    verts.push_back({ { x0, y0 }, color });
    verts.push_back({ { x1, y1 }, color });
    verts.push_back({ { x0, y1 }, color });
}

void add_char(std::vector<HUDVertex>& verts, char ch, float start_x, float start_y, float scale, const glm::vec4& color) {
    if (ch < 32 || ch > 126) return;
    int idx = ch - 32;
    for (int row = 0; row < 8; ++row) {
        uint8_t bits = FONT_8X8[idx][row];
        for (int col = 0; col < 8; ++col) {
            if ((bits >> (7 - col)) & 1) {
                float px0 = start_x + col * scale;
                float py0 = start_y + row * scale;
                add_rect(verts, px0, py0, px0 + scale, py0 + scale, color);
            }
        }
    }
}

void add_string(std::vector<HUDVertex>& verts, const char* str, float start_x, float start_y, float scale, const glm::vec4& color) {
    float cur_x = start_x;
    while (*str) {
        if (*str == '\n') {
            start_y += 10.0f * scale;
            cur_x = start_x;
        } else {
            add_char(verts, *str, cur_x, start_y, scale, color);
            cur_x += 8.0f * scale;
        }
        str++;
    }
}

} // namespace

void EngineApp::render_hud(float screen_w, float screen_h, float fps) {
    if (hud_pip_id_ == 0 || hud_vbuf_id_ == 0) return;

    std::vector<HUDVertex> verts;
    verts.reserve(4096);

    // 1. Center Crosshair
    if (show_crosshair_) {
        float cx = screen_w * 0.5f;
        float cy = screen_h * 0.5f;
        glm::vec4 cross_color{ 1.0f, 1.0f, 1.0f, 0.92f };
        glm::vec4 cross_shadow{ 0.0f, 0.0f, 0.0f, 0.55f };

        // Crosshair shadow / outline for high contrast
        add_rect(verts, cx - 11.0f, cy - 2.0f, cx - 2.0f, cy + 2.0f, cross_shadow);
        add_rect(verts, cx + 2.0f, cy - 2.0f, cx + 11.0f, cy + 2.0f, cross_shadow);
        add_rect(verts, cx - 2.0f, cy - 11.0f, cx + 2.0f, cy - 2.0f, cross_shadow);
        add_rect(verts, cx - 2.0f, cy + 2.0f, cx + 2.0f, cy + 11.0f, cross_shadow);

        // Crosshair lines
        add_rect(verts, cx - 10.0f, cy - 1.0f, cx - 3.0f, cy + 1.0f, cross_color);
        add_rect(verts, cx + 3.0f, cy - 1.0f, cx + 10.0f, cy + 1.0f, cross_color);
        add_rect(verts, cx - 1.0f, cy - 10.0f, cx + 1.0f, cy - 3.0f, cross_color);
        add_rect(verts, cx - 1.0f, cy + 3.0f, cx + 1.0f, cy + 10.0f, cross_color);

        // Center dot
        add_rect(verts, cx - 1.0f, cy - 1.0f, cx + 1.0f, cy + 1.0f, cross_color);
    }

    // 2. Top-Left HUD Info Card (FPS & Score)
    if (show_hud_) {
        char fps_score_buf[256];
        int top_len = 0;
        if (!hud_title_.empty()) {
            top_len = std::snprintf(fps_score_buf, sizeof(fps_score_buf), "%s | FPS: %3.0f   SCORE: %d", hud_title_.c_str(), fps, hud_score_);
        } else {
            top_len = std::snprintf(fps_score_buf, sizeof(fps_score_buf), "FPS: %3.0f   SCORE: %d", fps, hud_score_);
        }
        float t_scale = 1.8f;
        float t_char_w = 8.0f * t_scale;
        float t_width = top_len * t_char_w;
        float t_pad_x = 16.0f;
        float t_pad_y = 9.0f;
        float top_x0 = 16.0f;
        float top_y0 = 16.0f;
        float top_x1 = top_x0 + t_width + t_pad_x * 2.0f;
        float top_y1 = top_y0 + 8.0f * t_scale + t_pad_y * 2.0f;

        // Dark semi-transparent slate card
        add_rect(verts, top_x0, top_y0, top_x1, top_y1, { 0.05f, 0.08f, 0.14f, 0.82f });
        // Neon cyan top accent line spanning exact card width
        add_rect(verts, top_x0, top_y0, top_x1, top_y0 + 3.0f, { 0.25f, 0.65f, 0.95f, 0.95f });
        // Text inside card
        add_string(verts, fps_score_buf, top_x0 + t_pad_x, top_y0 + t_pad_y + 2.0f, t_scale, { 1.0f, 0.92f, 0.45f, 1.0f });

        // 3. Bottom Controls Hint Card
        const char* hint = !hud_hint_.empty() ? hud_hint_.c_str() : "[TAB] Lock Mouse   [F1] Hitboxes   [LMB] Shoot";
        float b_scale = 1.35f;
        float b_char_w = 8.0f * b_scale;
        float b_width = std::strlen(hint) * b_char_w;
        float b_pad_x = 16.0f;
        float b_pad_y = 8.0f;
        float b_h = 8.0f * b_scale + b_pad_y * 2.0f;
        float b_x0 = 16.0f;
        float b_y0 = screen_h - b_h - 16.0f;
        float b_x1 = b_x0 + b_width + b_pad_x * 2.0f;
        float b_y1 = b_y0 + b_h;

        // Background plate
        add_rect(verts, b_x0, b_y0, b_x1, b_y1, { 0.05f, 0.08f, 0.14f, 0.82f });
        // Subtle border/accent
        add_rect(verts, b_x0, b_y0, b_x1, b_y0 + 2.0f, { 0.35f, 0.50f, 0.70f, 0.85f });
        // Text inside card
        add_string(verts, hint, b_x0 + b_pad_x, b_y0 + b_pad_y + 1.0f, b_scale, { 0.90f, 0.93f, 0.98f, 0.95f });
    }

    // 4. Custom UI Commands Queue
    for (const auto& cmd : custom_ui_commands_) {
        switch (cmd.type) {
            case UICommandType::Rect:
                add_rect(verts, cmd.pos.x, cmd.pos.y, cmd.pos.x + cmd.size.x, cmd.pos.y + cmd.size.y, cmd.color);
                break;
            case UICommandType::Text:
                add_string(verts, cmd.text.c_str(), cmd.pos.x, cmd.pos.y, cmd.size.y > 0.0f ? cmd.size.y / 8.0f : 1.5f, cmd.color);
                break;
            case UICommandType::Crosshair: {
                float cx = (cmd.pos.x != 0.0f || cmd.pos.y != 0.0f) ? cmd.pos.x : (screen_w * 0.5f);
                float cy = (cmd.pos.x != 0.0f || cmd.pos.y != 0.0f) ? cmd.pos.y : (screen_h * 0.5f);
                float s = cmd.size.x > 0.0f ? cmd.size.x : 10.0f;
                float th = cmd.thickness > 0.0f ? cmd.thickness : 1.0f;
                float hth = th * 0.5f;
                add_rect(verts, cx - s, cy - hth, cx + s, cy + hth, cmd.color);
                add_rect(verts, cx - hth, cy - s, cx + hth, cy + s, cmd.color);
                break;
            }
            case UICommandType::Line: {
                float th = cmd.thickness > 0.0f ? cmd.thickness : 1.0f;
                glm::vec2 d = cmd.size;
                float len = glm::length(d);
                if (len > 0.0001f) {
                    glm::vec2 n = glm::vec2(-d.y, d.x) / len * (th * 0.5f);
                    glm::vec2 p0 = cmd.pos;
                    glm::vec2 p1 = cmd.pos + cmd.size;
                    verts.push_back({ p0 + n, cmd.color });
                    verts.push_back({ p1 + n, cmd.color });
                    verts.push_back({ p1 - n, cmd.color });
                    verts.push_back({ p0 + n, cmd.color });
                    verts.push_back({ p1 - n, cmd.color });
                    verts.push_back({ p0 - n, cmd.color });
                }
                break;
            }
        }
    }
    custom_ui_commands_.clear();

    if (verts.empty()) return;

    size_t count = std::min(verts.size(), static_cast<size_t>(16384));
    sg_range range{ verts.data(), count * sizeof(HUDVertex) };
    sg_update_buffer(sg_buffer{ hud_vbuf_id_ }, &range);

    sg_pipeline pip{ hud_pip_id_ };
    sg_apply_pipeline(pip);

    glm::mat4 ortho = glm::ortho(0.0f, screen_w, screen_h, 0.0f, -1.0f, 1.0f);
    HUDVSParams vs{ ortho };
    sg_apply_uniforms(0, SG_RANGE_REF(vs));

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ hud_vbuf_id_ };
    sg_apply_bindings(&bind);

    sg_draw(0, static_cast<int>(count), 1);
}

void EngineApp::evaluate_frustum_culling() {
    stats_ = RenderStats{};
    Frustum camera_frustum;
    camera_frustum.set_from_projection_matrix(camera_.view_projection_matrix());

    for (const auto& entity : scene_.entities()) {
        if (!entity || !entity->visible || !entity->mesh) {
            continue;
        }

        if ((camera_.layers & entity->layers) == 0) {
            continue;
        }

        AABB aabb = entity->world_aabb();
        if (aabb.is_valid()) {
            if (!camera_frustum.intersects_aabb(aabb.min_point, aabb.max_point)) {
                stats_.culled_objects++;
                continue;
            }
        }

        stats_.draw_calls++;
        stats_.total_triangles += entity->mesh->num_indices / 3;
    }

    for (const auto& inst_mesh : scene_.instanced_meshes()) {
        if (!inst_mesh || !inst_mesh->mesh || inst_mesh->instance_count() == 0) continue;
        if ((camera_.layers & inst_mesh->layers) == 0) continue;
        stats_.draw_calls++;
        stats_.total_instances += static_cast<uint32_t>(inst_mesh->instance_count());
        stats_.total_triangles += (inst_mesh->mesh->num_indices / 3) * static_cast<uint32_t>(inst_mesh->instance_count());
    }
}

static void apply_camera_viewport_and_scissor(const Camera& cam, int target_w, int target_h) {
    if (target_w <= 0 || target_h <= 0) return;

    // Viewport
    int vp_x = 0;
    int vp_y = 0;
    int vp_w = target_w;
    int vp_h = target_h;

    if (cam.viewport.z <= 1.0f && cam.viewport.w <= 1.0f && cam.viewport.z > 0.0f && cam.viewport.w > 0.0f) {
        vp_x = static_cast<int>(cam.viewport.x * static_cast<float>(target_w));
        vp_y = static_cast<int>(cam.viewport.y * static_cast<float>(target_h));
        vp_w = static_cast<int>(cam.viewport.z * static_cast<float>(target_w));
        vp_h = static_cast<int>(cam.viewport.w * static_cast<float>(target_h));
    } else if (cam.viewport.z > 1.0f || cam.viewport.w > 1.0f) {
        vp_x = static_cast<int>(cam.viewport.x);
        vp_y = static_cast<int>(cam.viewport.y);
        vp_w = static_cast<int>(cam.viewport.z);
        vp_h = static_cast<int>(cam.viewport.w);
    }

    sg_apply_viewport(vp_x, vp_y, vp_w, vp_h, true);

    // Scissor
    if (cam.has_scissor) {
        int sc_x = 0;
        int sc_y = 0;
        int sc_w = target_w;
        int sc_h = target_h;

        if (cam.scissor.z <= 1.0f && cam.scissor.w <= 1.0f && cam.scissor.z > 0.0f && cam.scissor.w > 0.0f) {
            sc_x = static_cast<int>(cam.scissor.x * static_cast<float>(target_w));
            sc_y = static_cast<int>(cam.scissor.y * static_cast<float>(target_h));
            sc_w = static_cast<int>(cam.scissor.z * static_cast<float>(target_w));
            sc_h = static_cast<int>(cam.scissor.w * static_cast<float>(target_h));
        } else {
            sc_x = static_cast<int>(cam.scissor.x);
            sc_y = static_cast<int>(cam.scissor.y);
            sc_w = static_cast<int>(cam.scissor.z);
            sc_h = static_cast<int>(cam.scissor.w);
        }

        sg_apply_scissor_rect(sc_x, sc_y, sc_w, sc_h, true);
    }
}

void EngineApp::render_scene_pass(Scene& scene, Camera& camera, int target_w, int target_h, bool is_offscreen, uint32_t color_format) {
    if (pip_id_ == 0) return;

    // 0. Update LOD levels according to camera position
    for (const auto& lod : scene.lods()) {
        if (lod && lod->visible) {
            lod->update_lod(camera.position);
        }
    }

    apply_camera_viewport_and_scissor(camera, target_w, target_h);

    if (target_h > 0 && camera.type == CameraType::Perspective) {
        float vp_w_f = (camera.viewport.z <= 1.0f && camera.viewport.z > 0.0f) ? (camera.viewport.z * static_cast<float>(target_w)) : camera.viewport.z;
        float vp_h_f = (camera.viewport.w <= 1.0f && camera.viewport.w > 0.0f) ? (camera.viewport.w * static_cast<float>(target_h)) : camera.viewport.w;
        camera.aspect = (vp_h_f > 0.0f) ? (vp_w_f / vp_h_f) : (static_cast<float>(target_w) / static_cast<float>(target_h));
    }
    glm::mat4 vp = camera.view_projection_matrix();

    // 1. Gather lights from scene into LightParamsUBO
    LightParamsUBO light_ubo{};
    light_ubo.hemi_sky = glm::vec4(scene.light.ambient_sky, 1.0f);
    light_ubo.hemi_ground = glm::vec4(scene.light.ambient_ground, 1.0f);
    light_ubo.ambient_and_count = glm::vec4(scene.light.ambient, 0.0f);

    int num_dirs = 0;
    int num_points = 0;
    int num_spots = 0;

    for (const auto& l : scene.lights()) {
        if (!l) continue;
        switch (l->type) {
            case LightType::Ambient:
                light_ubo.ambient_and_count.r += l->color.r * l->intensity;
                light_ubo.ambient_and_count.g += l->color.g * l->intensity;
                light_ubo.ambient_and_count.b += l->color.b * l->intensity;
                break;
            case LightType::Hemisphere: {
                auto hl = std::dynamic_pointer_cast<HemisphereLight>(l);
                if (hl) {
                    light_ubo.hemi_sky = glm::vec4(hl->sky_color, hl->intensity);
                    light_ubo.hemi_ground = glm::vec4(hl->ground_color, 1.0f);
                }
                break;
            }
            case LightType::Directional: {
                if (num_dirs < 4) {
                    auto dl = std::dynamic_pointer_cast<DirectionalLight>(l);
                    bool cast_shd = dl ? dl->cast_shadow : true;
                    light_ubo.dir_lights[num_dirs].direction_and_cast_shadow = glm::vec4(l->get_world_direction(), cast_shd ? 1.0f : 0.0f);
                    light_ubo.dir_lights[num_dirs].color_and_intensity = glm::vec4(l->color, l->intensity);
                    num_dirs++;
                }
                break;
            }
            case LightType::Point: {
                if (num_points < 16) {
                    auto pl = std::dynamic_pointer_cast<PointLight>(l);
                    light_ubo.point_lights[num_points].position_and_range = glm::vec4(l->get_world_position(), l->range);
                    light_ubo.point_lights[num_points].color_and_intensity = glm::vec4(l->color, l->intensity);
                    light_ubo.point_lights[num_points].params = glm::vec4(pl ? pl->decay : 2.0f, 0.0f, 0.0f, 0.0f);
                    num_points++;
                }
                break;
            }
            case LightType::Spot: {
                if (num_spots < 8) {
                    auto sl = std::dynamic_pointer_cast<SpotLight>(l);
                    light_ubo.spot_lights[num_spots].position_and_range = glm::vec4(l->get_world_position(), l->range);
                    light_ubo.spot_lights[num_spots].direction_and_cast_shadow = glm::vec4(l->get_world_direction(), (sl && sl->cast_shadow) ? 1.0f : 0.0f);
                    light_ubo.spot_lights[num_spots].color_and_intensity = glm::vec4(l->color, l->intensity);
                    float inner = sl ? sl->inner_cone_angle : 0.349f;
                    float outer = sl ? sl->outer_cone_angle : 0.523f;
                    float penumbra = sl ? sl->penumbra : 0.0f;
                    light_ubo.spot_lights[num_spots].cone_params = glm::vec4(std::cos(inner), std::cos(outer), penumbra, 0.0f);
                    num_spots++;
                }
                break;
            }
            default:
                break;
        }
    }

    if (num_dirs == 0) {
        light_ubo.dir_lights[0].direction_and_cast_shadow = glm::vec4(scene.light.direction, 1.0f);
        light_ubo.dir_lights[0].color_and_intensity = glm::vec4(scene.light.color, scene.light.intensity);
        num_dirs = 1;
    }

    light_ubo.ambient_and_count.w = static_cast<float>(num_dirs);
    light_ubo.light_counts.x = static_cast<float>(num_points);
    light_ubo.light_counts.y = static_cast<float>(num_spots);
    light_ubo.light_counts.z = static_cast<float>(shadow_settings_.resolution);
    light_ubo.light_counts.w = shadow_settings_.pcf_16_tap ? 1.0f : 0.0f;

    // Prepare base lighting uniform
    glm::vec3 cam_pos = camera.parent() ? camera.world_position() : camera.position;
    FSParams fs_params{};
    fs_params.eye_pos = glm::vec4(cam_pos, scene.environment_intensity());
    fs_params.fog_color = glm::vec4(fog_color_, (tone_mapping_enabled_ && !composer_) ? 1.0f : 0.0f);
    fs_params.fog_params = glm::vec4(
        fog_enabled_ ? static_cast<float>(fog_type_) : 0.0f,
        fog_near_,
        fog_far_,
        fog_density_
    );

    auto default_mat = scene.default_material();

    // Compute camera frustum for culling
    Frustum camera_frustum;
    camera_frustum.set_from_projection_matrix(camera.view_projection_matrix());

    // Split visible entities into opaque and transparent queues
    struct RenderItem {
        std::shared_ptr<Mesh> mesh;
        std::shared_ptr<Material> material;
        glm::mat4 model;
        glm::mat4 normal_mat;
        glm::vec4 color{1.0f};
        float dist_sq{0.0f};
    };

    std::vector<RenderItem> opaque_queue;
    std::vector<RenderItem> transparent_queue;

    auto push_item = [&](std::shared_ptr<Mesh> mesh, std::shared_ptr<Material> mat, const glm::mat4& model, const glm::mat4& normal_mat, const glm::vec4& color, const glm::vec3& wpos, const AABB& aabb) {
        if (!mesh) return;
        if (aabb.is_valid()) {
            if (!camera_frustum.intersects_aabb(aabb.min_point, aabb.max_point)) {
                stats_.culled_objects++;
                return;
            }
        }
        if (!mesh->ensure_gpu_buffers()) return;

        glm::vec3 diff = cam_pos - wpos;
        float d2 = glm::dot(diff, diff);
        auto m = mat ? mat : default_mat;
        bool is_trans = m && (m->transparent || m->opacity < 0.999f || m->blend_mode != BlendMode::Opaque);
        if (is_trans) {
            transparent_queue.push_back({ mesh, m, model, normal_mat, color, d2 });
        } else {
            opaque_queue.push_back({ mesh, m, model, normal_mat, color, d2 });
        }
    };

    // 1. Entities
    for (const auto& entity : scene.entities()) {
        if (!entity || !entity->visible || !entity->mesh) continue;
        if ((camera.layers & entity->layers) == 0) continue;
        push_item(entity->mesh, entity->material, entity->world_model_matrix(), entity->world_normal_matrix(), entity->color, entity->world_position(), entity->world_aabb());
    }

    // 2. Skinned Meshes
    for (const auto& skm : scene.skinned_meshes()) {
        if (!skm || !skm->visible || !skm->mesh) continue;
        if ((camera.layers & skm->layers) == 0) continue;
        skm->compute_cpu_skinning();
        push_item(skm->mesh, skm->material, skm->world_model_matrix(), skm->world_normal_matrix(), skm->color, skm->world_position(), skm->world_aabb());
    }

    // 3. Points
    for (const auto& pts : scene.points()) {
        if (!pts || !pts->visible || !pts->mesh || pts->mesh->num_indices == 0) continue;
        if ((camera.layers & pts->layers) == 0) continue;
        push_item(pts->mesh, pts->material, pts->world_matrix(), glm::mat4(1.0f), glm::vec4(1.0f), pts->world_position(), pts->world_aabb());
    }

    // 4. Sprites
    for (const auto& spr : scene.sprites()) {
        if (!spr || !spr->visible || !spr->material) continue;
        if ((camera.layers & spr->layers) == 0) continue;
        auto q = Sprite::quad_mesh();
        glm::mat4 bm = spr->compute_billboard_matrix(camera);
        push_item(q, spr->material, bm, glm::mat4(1.0f), glm::vec4(1.0f), spr->world_position(), spr->world_aabb());
    }

    // 5. Particle Emitters
    for (const auto& pe : scene.particle_emitters()) {
        if (!pe || !pe->visible || pe->active_count() == 0) continue;
        if ((camera.layers & pe->layers) == 0) continue;
        pe->update_mesh(camera);
        auto pmesh = pe->get_particle_mesh();
        if (pmesh && pmesh->num_indices > 0) {
            auto pmat = std::make_shared<Material>(pe->texture, 1.0f, 0.0f);
            pmat->transparent = true;
            pmat->blend_mode = pe->blend_mode;
            pmat->depth_write = false;
            push_item(pmesh, pmat, glm::mat4(1.0f), glm::mat4(1.0f), glm::vec4(1.0f), pe->world_position(), pe->world_aabb());
        }
    }

    // Sort opaque front-to-back (ascending distance)
    std::sort(opaque_queue.begin(), opaque_queue.end(), [](const RenderItem& a, const RenderItem& b) {
        return a.dist_sq < b.dist_sq;
    });

    // Sort transparent back-to-front (descending distance)
    std::sort(transparent_queue.begin(), transparent_queue.end(), [](const RenderItem& a, const RenderItem& b) {
        return a.dist_sq > b.dist_sq;
    });

    uint64_t current_pip_key = 0;

    auto render_entities = [&](const std::vector<RenderItem>& queue, bool is_transparent_pass) {
        for (const auto& item : queue) {
            const auto& mesh = item.mesh;
            if (!mesh || !mesh->ensure_gpu_buffers()) continue;
            auto mat = item.material ? item.material : default_mat;

            SideMode side = mat ? mat->side : SideMode::Front;
            bool depth_write = is_transparent_pass ? false : (mat ? mat->depth_write : true);
            bool depth_test = mat ? mat->depth_test : true;
            BlendMode blend = is_transparent_pass ? ((mat && mat->blend_mode != BlendMode::Opaque) ? mat->blend_mode : BlendMode::Alpha) : BlendMode::Opaque;
            bool wireframe = mat ? mat->wireframe : false;
            int samples = is_offscreen ? 1 : sapp_sample_count();
            uint32_t target_fmt = is_offscreen ? ((color_format != 0) ? color_format : static_cast<uint32_t>(SG_PIXELFORMAT_RGBA16F)) : 0;

            uint64_t pip_key = PipelineManager::make_key(shd_id_, side, depth_write, depth_test, blend, wireframe, false, samples, target_fmt);
            if (pip_key != current_pip_key) {
                sg_pipeline_desc pdesc{};
                pdesc.layout.buffers[0].stride = sizeof(Vertex);
                pdesc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
                pdesc.layout.attrs[0].offset = offsetof(Vertex, position);
                pdesc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
                pdesc.layout.attrs[1].offset = offsetof(Vertex, normal);
                pdesc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
                pdesc.layout.attrs[2].offset = offsetof(Vertex, uv);
                pdesc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
                pdesc.layout.attrs[3].offset = offsetof(Vertex, color);
                pdesc.layout.attrs[4].format = SG_VERTEXFORMAT_FLOAT4;
                pdesc.layout.attrs[4].offset = offsetof(Vertex, tangent);
                pdesc.shader = sg_shader{ shd_id_ };
                pdesc.index_type = SG_INDEXTYPE_UINT16;
                pdesc.depth.compare = depth_test ? SG_COMPAREFUNC_LESS_EQUAL : SG_COMPAREFUNC_ALWAYS;
                pdesc.depth.write_enabled = depth_write;
                pdesc.face_winding = SG_FACEWINDING_CCW;
                pdesc.cull_mode = (side == SideMode::Double) ? SG_CULLMODE_NONE : ((side == SideMode::Back) ? SG_CULLMODE_FRONT : SG_CULLMODE_BACK);
                pdesc.sample_count = samples;
                pdesc.primitive_type = wireframe ? SG_PRIMITIVETYPE_LINES : SG_PRIMITIVETYPE_TRIANGLES;
                pdesc.colors[0].pixel_format = is_offscreen ? static_cast<sg_pixel_format>(target_fmt) : _SG_PIXELFORMAT_DEFAULT;

                if (blend == BlendMode::Alpha) {
                    pdesc.colors[0].blend.enabled = true;
                    pdesc.colors[0].blend.src_factor_rgb = SG_BLENDFACTOR_SRC_ALPHA;
                    pdesc.colors[0].blend.dst_factor_rgb = SG_BLENDFACTOR_ONE_MINUS_SRC_ALPHA;
                    pdesc.colors[0].blend.src_factor_alpha = SG_BLENDFACTOR_ONE;
                    pdesc.colors[0].blend.dst_factor_alpha = SG_BLENDFACTOR_ONE_MINUS_SRC_ALPHA;
                } else if (blend == BlendMode::Additive) {
                    pdesc.colors[0].blend.enabled = true;
                    pdesc.colors[0].blend.src_factor_rgb = SG_BLENDFACTOR_SRC_ALPHA;
                    pdesc.colors[0].blend.dst_factor_rgb = SG_BLENDFACTOR_ONE;
                    pdesc.colors[0].blend.src_factor_alpha = SG_BLENDFACTOR_ONE;
                    pdesc.colors[0].blend.dst_factor_alpha = SG_BLENDFACTOR_ONE;
                } else if (blend == BlendMode::Multiply) {
                    pdesc.colors[0].blend.enabled = true;
                    pdesc.colors[0].blend.src_factor_rgb = SG_BLENDFACTOR_DST_COLOR;
                    pdesc.colors[0].blend.dst_factor_rgb = SG_BLENDFACTOR_ZERO;
                    pdesc.colors[0].blend.src_factor_alpha = SG_BLENDFACTOR_DST_ALPHA;
                    pdesc.colors[0].blend.dst_factor_alpha = SG_BLENDFACTOR_ZERO;
                }

                sg_pipeline pip = PipelineManager::instance().get_or_create(pip_key, pdesc);
                if (pip.id != 0) {
                    sg_apply_pipeline(pip);
                    current_pip_key = pip_key;
                    sg_apply_uniforms(2, SG_RANGE_REF(light_ubo));
                }
            }

            auto tex_alb = (mat && mat->albedo_map) ? mat->albedo_map : default_white_tex_;
            if (tex_alb) tex_alb->ensure_gpu_resources();
            if (!tex_alb || !tex_alb->is_valid()) tex_alb = default_white_tex_;

            auto tex_norm = (mat && mat->normal_map) ? mat->normal_map : default_flat_normal_tex_;
            if (tex_norm) tex_norm->ensure_gpu_resources();
            if (!tex_norm || !tex_norm->is_valid()) tex_norm = default_flat_normal_tex_;

            auto tex_mr = (mat && mat->metallic_roughness_map) ? mat->metallic_roughness_map : default_white_tex_;
            if (tex_mr) tex_mr->ensure_gpu_resources();
            if (!tex_mr || !tex_mr->is_valid()) tex_mr = default_white_tex_;

            auto tex_em = (mat && mat->emissive_map) ? mat->emissive_map : default_black_tex_;
            if (tex_em) tex_em->ensure_gpu_resources();
            if (!tex_em || !tex_em->is_valid()) tex_em = default_black_tex_;

            auto tex_ao_tex = (mat && mat->ao_map) ? mat->ao_map : ((mat && mat->occlusion_map) ? mat->occlusion_map : default_white_tex_);
            if (tex_ao_tex) tex_ao_tex->ensure_gpu_resources();
            if (!tex_ao_tex || !tex_ao_tex->is_valid()) tex_ao_tex = default_white_tex_;

            glm::mat4 model = item.model;
            glm::mat4 normal_mat = item.normal_mat;
            glm::mat4 mvp = vp * model;
            glm::mat4 l_mvp = light_vp_ * model;

            VSParams vs_params{ mvp, model, normal_mat, l_mvp };

            sg_bindings bind{};
            bind.vertex_buffers[0] = sg_buffer{ mesh->vbuf_id };
            bind.index_buffer = sg_buffer{ mesh->ibuf_id };
            bind.views[0] = sg_view{ tex_alb ? tex_alb->view_id : 0 };
            bind.samplers[0] = sg_sampler{ tex_alb ? tex_alb->sampler_id : 0 };
            bind.views[1] = sg_view{ shadow_tex_view_id_ };
            bind.samplers[1] = sg_sampler{ shadow_sampler_id_ };
            bind.views[2] = sg_view{ tex_norm ? tex_norm->view_id : 0 };
            bind.samplers[2] = sg_sampler{ tex_norm ? tex_norm->sampler_id : 0 };
            bind.views[3] = sg_view{ tex_mr ? tex_mr->view_id : 0 };
            bind.samplers[3] = sg_sampler{ tex_mr ? tex_mr->sampler_id : 0 };
            bind.views[4] = sg_view{ tex_em ? tex_em->view_id : 0 };
            bind.samplers[4] = sg_sampler{ tex_em ? tex_em->sampler_id : 0 };
            bind.views[5] = sg_view{ tex_ao_tex ? tex_ao_tex->view_id : 0 };
            bind.samplers[5] = sg_sampler{ tex_ao_tex ? tex_ao_tex->sampler_id : 0 };

            auto env_cube = scene.environment() ? scene.environment() : default_env_cube_;
            if (env_cube) env_cube->ensure_gpu_resources();
            uint32_t env_v = (env_cube && env_cube->is_valid()) ? env_cube->view_id : (default_env_cube_ ? default_env_cube_->view_id : 0);
            uint32_t env_s = (env_cube && env_cube->is_valid()) ? env_cube->sampler_id : (default_env_cube_ ? default_env_cube_->sampler_id : 0);
            bind.views[6] = sg_view{ env_v };
            bind.samplers[6] = sg_sampler{ env_s };

            sg_apply_bindings(&bind);
            sg_apply_uniforms(0, SG_RANGE_REF(vs_params));

            FSParams ent_fs = fs_params;
            ent_fs.material_color = (mat ? mat->base_color : glm::vec4(1.0f)) * item.color;
            ent_fs.material_params = glm::vec4(mat ? mat->roughness : 0.5f, mat ? mat->metallic : 0.0f, mat ? mat->uv_scale.x : 1.0f, mat ? mat->uv_scale.y : 1.0f);
            ent_fs.material_uv_offset = glm::vec4(mat ? mat->uv_offset.x : 0.0f, mat ? mat->uv_offset.y : 0.0f, mat ? mat->normal_scale : 1.0f, mat ? mat->ao_intensity : 1.0f);
            ent_fs.emissive_params = glm::vec4(mat ? (mat->emissive_color * mat->emissive_intensity) : glm::vec3(0.0f), (mat && mat->alpha_test) ? mat->alpha_cutoff : -1.0f);
            ent_fs.texture_flags = glm::vec4(
                (mat && mat->normal_map) ? 1.0f : 0.0f,
                (mat && mat->metallic_roughness_map) ? 1.0f : 0.0f,
                (mat && mat->emissive_map) ? 1.0f : 0.0f,
                (mat && (mat->ao_map || mat->occlusion_map)) ? 1.0f : 0.0f
            );
            float mtype = 0.0f;
            float extra_val = 0.0f;
            if (mat) {
                switch (mat->type()) {
                    case MaterialType::Unlit: mtype = 1.0f; break;
                    case MaterialType::Lambert: mtype = 2.0f; break;
                    case MaterialType::Phong: {
                        mtype = 3.0f;
                        auto pm = std::dynamic_pointer_cast<PhongMaterial>(mat);
                        extra_val = pm ? pm->shininess : 32.0f;
                        break;
                    }
                    case MaterialType::Toon: {
                        mtype = 4.0f;
                        auto tm = std::dynamic_pointer_cast<ToonMaterial>(mat);
                        extra_val = tm ? tm->steps : 4.0f;
                        break;
                    }
                    case MaterialType::Physical:
                    case MaterialType::Standard:
                    default:
                        mtype = 0.0f;
                        break;
                }
            }
            ent_fs.extra_params = glm::vec4(mtype, extra_val, mat ? mat->opacity : 1.0f, is_transparent_pass ? 1.0f : 0.0f);

            sg_apply_uniforms(1, SG_RANGE_REF(ent_fs));

            sg_draw(0, mesh->num_indices, 1);
            stats_.draw_calls++;
            stats_.total_triangles += mesh->num_indices / 3;
        }
    };

    // Render background pass (Skybox or Procedural Sky) before opaque geometry
    render_background_pass(scene, camera, is_offscreen, is_offscreen ? ((color_format != 0) ? color_format : static_cast<uint32_t>(SG_PIXELFORMAT_RGBA16F)) : 0);

    // Render opaque entities first
    render_entities(opaque_queue, false);

    // Draw instanced meshes in Scene
    if (instanced_pip_id_ != 0 && !scene.instanced_meshes().empty()) {
        sg_pipeline inst_pip{ instanced_pip_id_ };
        sg_apply_pipeline(inst_pip);

        InstancedVSParams inst_vs{ vp, light_vp_ };
        sg_apply_uniforms(0, SG_RANGE_REF(inst_vs));

        for (const auto& inst_mesh : scene.instanced_meshes()) {
            if (!inst_mesh || !inst_mesh->mesh || inst_mesh->instance_count() == 0) continue;
            if (!inst_mesh->mesh->ensure_gpu_buffers() || !inst_mesh->ensure_gpu_buffers()) continue;

            sg_bindings bind{};
            bind.vertex_buffers[0] = sg_buffer{ inst_mesh->mesh->vbuf_id };
            bind.vertex_buffers[1] = sg_buffer{ inst_mesh->inst_vbuf_id };
            bind.index_buffer = sg_buffer{ inst_mesh->mesh->ibuf_id };
            bind.views[0] = sg_view{ default_white_tex_ ? default_white_tex_->view_id : 0 };
            bind.samplers[0] = sg_sampler{ default_white_tex_ ? default_white_tex_->sampler_id : 0 };
            bind.views[1] = sg_view{ shadow_tex_view_id_ };
            bind.samplers[1] = sg_sampler{ shadow_sampler_id_ };
            bind.views[2] = sg_view{ default_flat_normal_tex_ ? default_flat_normal_tex_->view_id : 0 };
            bind.samplers[2] = sg_sampler{ default_flat_normal_tex_ ? default_flat_normal_tex_->sampler_id : 0 };
            bind.views[3] = sg_view{ default_white_tex_ ? default_white_tex_->view_id : 0 };
            bind.samplers[3] = sg_sampler{ default_white_tex_ ? default_white_tex_->sampler_id : 0 };
            bind.views[4] = sg_view{ default_black_tex_ ? default_black_tex_->view_id : 0 };
            bind.samplers[4] = sg_sampler{ default_black_tex_ ? default_black_tex_->sampler_id : 0 };
            bind.views[5] = sg_view{ default_white_tex_ ? default_white_tex_->view_id : 0 };
            bind.samplers[5] = sg_sampler{ default_white_tex_ ? default_white_tex_->sampler_id : 0 };

            auto env_cube = scene.environment() ? scene.environment() : default_env_cube_;
            if (env_cube) env_cube->ensure_gpu_resources();
            uint32_t env_v = (env_cube && env_cube->is_valid()) ? env_cube->view_id : (default_env_cube_ ? default_env_cube_->view_id : 0);
            uint32_t env_s = (env_cube && env_cube->is_valid()) ? env_cube->sampler_id : (default_env_cube_ ? default_env_cube_->sampler_id : 0);
            bind.views[6] = sg_view{ env_v };
            bind.samplers[6] = sg_sampler{ env_s };

            sg_apply_bindings(&bind);

            sg_draw(0, inst_mesh->mesh->num_indices, static_cast<int>(inst_mesh->instance_count()));
            stats_.draw_calls++;
            stats_.total_instances += static_cast<uint32_t>(inst_mesh->instance_count());
            stats_.total_triangles += static_cast<uint32_t>((inst_mesh->mesh->num_indices / 3) * inst_mesh->instance_count());
        }
    }

    // Render transparent entities second
    render_entities(transparent_queue, true);

    // Render visual helpers via line pipeline
    if (line_pip_id_ != 0 && line_vbuf_id_ != 0 && !scene.helpers().empty()) {
        std::vector<LineVertex> helper_verts;
        helper_verts.reserve(2048);
        for (const auto& hlp : scene.helpers()) {
            if (!hlp || !hlp->visible) continue;
            hlp->update();
            std::vector<LineVertex> local_verts;
            hlp->get_line_vertices(local_verts);
            glm::mat4 model = hlp->world_matrix();
            for (auto& lv : local_verts) {
                glm::vec4 wpos = model * glm::vec4(lv.pos, 1.0f);
                helper_verts.push_back({ glm::vec3(wpos), lv.color });
            }
        }
        if (!helper_verts.empty()) {
            size_t count = std::min(helper_verts.size(), static_cast<size_t>(8192));
            sg_range range{ helper_verts.data(), count * sizeof(LineVertex) };
            sg_update_buffer(sg_buffer{ line_vbuf_id_ }, &range);

            sg_pipeline pip{ line_pip_id_ };
            sg_apply_pipeline(pip);

            LineVSParams vs{ vp };
            sg_apply_uniforms(0, SG_RANGE_REF(vs));

            sg_bindings bind{};
            bind.vertex_buffers[0] = sg_buffer{ line_vbuf_id_ };
            sg_apply_bindings(&bind);

            sg_draw(0, static_cast<int>(count), 1);
        }
    }
}

void EngineApp::render_target(Scene& scene, Camera& camera, RenderTarget& target) {
    ensure_device();
    if (pip_id_ == 0 || target.color_view_id() == 0) return;

    render_shadow_pass(&scene, &camera);

    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_CLEAR;
    glm::vec4 clr = (scene.background_type() == BackgroundType::Color) ? scene.background_color() : camera.clear_color;
    pass.action.colors[0].clear_value = {
        clr.r,
        clr.g,
        clr.b,
        clr.a
    };
    if (target.has_depth()) {
        pass.action.depth.load_action = SG_LOADACTION_CLEAR;
        pass.action.depth.clear_value = 1.0f;
        pass.attachments.depth_stencil = sg_view{ target.depth_view_id() };
    }
    pass.attachments.colors[0] = sg_view{ target.color_view_id() };
    pass.label = "rendertarget-scene-pass";

    uint32_t target_fmt = (target.format() == RenderTargetFormat::RGBA16F)
        ? static_cast<uint32_t>(SG_PIXELFORMAT_RGBA16F)
        : static_cast<uint32_t>(SG_PIXELFORMAT_RGBA8);

    sg_begin_pass(&pass);
    render_scene_pass(scene, camera, target.width(), target.height(), true, target_fmt);
    sg_end_pass();
}

std::vector<uint8_t> EngineApp::read_pixels(RenderTarget& target) {
    ensure_device();
    return target.read_pixels();
}

std::vector<float> EngineApp::read_depth_pixels(RenderTarget& target) {
    ensure_device();
    return target.read_depth_pixels();
}

void EngineApp::set_composer(std::shared_ptr<EffectComposer> composer) {
    composer_ = composer;
    if (composer_) {
        composer_->set_app(this);
    }
}

void EngineApp::on_frame() {
    // Reset render stats for current frame
    stats_ = RenderStats{};

    // 0. Frame pacing / Target FPS limiter
    if (target_fps_ > 0 && has_last_frame_) {
        double min_dt = 1.0 / static_cast<double>(target_fps_);
        auto target_time = last_frame_time_ + std::chrono::duration<double>(min_dt);
        auto now = std::chrono::steady_clock::now();
        if (now < target_time) {
            auto sleep_dur = target_time - now;
            if (sleep_dur > std::chrono::milliseconds(3)) {
                std::this_thread::sleep_for(sleep_dur - std::chrono::milliseconds(2));
            }
            while (std::chrono::steady_clock::now() < target_time) {
                std::this_thread::yield();
            }
        }
    }

    // 1. Calculate delta time (dt) & FPS
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
    if (dt > 0.0) {
        float instant_fps = static_cast<float>(1.0 / dt);
        current_fps_ = current_fps_ * 0.92f + instant_fps * 0.08f;
    }

    // 2. Update Audio Listener with Camera Pose
    audio_.update_listener(camera_.position, camera_.forward(), camera_.up);

    // 3. Invoke Python frame update callback with GIL
    if (update_callback_) {
        try {
            update_callback_(dt);
        } catch (const std::exception& e) {
            std::cerr << "[Engine] Exception in Python update callback: " << e.what() << "\n";
        }
    }

    // 4. Update Camera Aspect & Matrix
    float w = sapp_widthf();
    float h = sapp_heightf();
    if (camera_.type == CameraType::Perspective) {
        camera_.aspect = (h > 0.0f) ? (w / h) : 1.333333f;
    }
    glm::mat4 vp = camera_.view_projection_matrix();

    // 5. Render Pass 1: Offscreen Shadow Map Pass
    render_shadow_pass();

    // 6. Main Render Pass (Direct Swapchain or via EffectComposer)
    if (composer_ && composer_->enabled) {
        // Run passes through EffectComposer
        composer_->render_passes(*this, scene_, camera_);

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

        if (composer_->final_target() && composer_->final_target()->tex_view_id() != 0) {
            composer_->blit_to_swapchain(*composer_->final_target());
        } else {
            static bool s_warned_composer = false;
            if (!s_warned_composer) {
                std::cerr << "[EngineApp] Warning: EffectComposer final_target is null or invalid, skipping swapchain blit.\n";
                s_warned_composer = true;
            }
        }

        // 7. Optional Debug Hitbox Rendering (F1 toggle or Editor Mode)
        if (show_debug_hitboxes_ || mode_ == EngineMode::EDITOR) {
            render_debug_hitboxes(vp);
        }

        // 8. 2D HUD Rendering (only in Game Mode)
        if ((show_hud_ || !custom_ui_commands_.empty()) && mode_ == EngineMode::GAME) {
            render_hud(w, h, current_fps_);
        }

        // 9. Visual Editor UI (Dear ImGui & ImGuizmo) - only in Editor Mode
        if (mode_ == EngineMode::EDITOR) {
            editor_.render(static_cast<float>(dt), w, h);
        }

        sg_end_pass();
        sg_commit();
    } else {
        sg_pass pass{};
        pass.action.colors[0].load_action = SG_LOADACTION_CLEAR;
        glm::vec4 bg_clr = (scene_.background_type() == BackgroundType::Color)
            ? scene_.background_color()
            : glm::vec4(config_.clear_color[0], config_.clear_color[1], config_.clear_color[2], config_.clear_color[3]);
        pass.action.colors[0].clear_value = {
            bg_clr.r,
            bg_clr.g,
            bg_clr.b,
            bg_clr.a
        };
        pass.action.depth.load_action = SG_LOADACTION_CLEAR;
        pass.action.depth.clear_value = 1.0f;
        pass.swapchain = sglue_swapchain();

        sg_begin_pass(&pass);

        render_scene_pass(scene_, camera_, static_cast<int>(w), static_cast<int>(h), false, 0);

        // 7. Optional Debug Hitbox Rendering (F1 toggle or Editor Mode)
        if (show_debug_hitboxes_ || mode_ == EngineMode::EDITOR) {
            render_debug_hitboxes(vp);
        }

        // 8. 2D HUD Rendering (only in Game Mode)
        if ((show_hud_ || !custom_ui_commands_.empty()) && mode_ == EngineMode::GAME) {
            render_hud(w, h, current_fps_);
        }

        // 9. Visual Editor UI (Dear ImGui & ImGuizmo) - only in Editor Mode
        if (mode_ == EngineMode::EDITOR) {
            editor_.render(static_cast<float>(dt), w, h);
        }

        sg_end_pass();
        sg_commit();
    }

    // 9. Reset per-frame input transients
    input_.post_frame();
}

void EngineApp::on_cleanup() {
    update_callback_ = nullptr;
    scene_.clear();
    audio_.shutdown();

    PipelineManager::instance().release_all();

    if (default_white_tex_) {
        default_white_tex_->destroy();
        default_white_tex_ = nullptr;
    }
    if (default_black_tex_) {
        default_black_tex_->destroy();
        default_black_tex_ = nullptr;
    }
    if (default_flat_normal_tex_) {
        default_flat_normal_tex_->destroy();
        default_flat_normal_tex_ = nullptr;
    }

    if (pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{pip_id_});
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        sg_destroy_shader(sg_shader{shd_id_});
        shd_id_ = 0;
    }
    if (instanced_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{instanced_pip_id_});
        instanced_pip_id_ = 0;
    }
    if (instanced_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{instanced_shd_id_});
        instanced_shd_id_ = 0;
    }
    if (shadow_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{shadow_pip_id_});
        shadow_pip_id_ = 0;
    }
    if (shadow_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{shadow_shd_id_});
        shadow_shd_id_ = 0;
    }
    if (instanced_shadow_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{instanced_shadow_pip_id_});
        instanced_shadow_pip_id_ = 0;
    }
    if (instanced_shadow_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{instanced_shadow_shd_id_});
        instanced_shadow_shd_id_ = 0;
    }
    if (shadow_color_view_id_ != 0) {
        sg_destroy_view(sg_view{shadow_color_view_id_});
        shadow_color_view_id_ = 0;
    }
    if (shadow_depth_view_id_ != 0) {
        sg_destroy_view(sg_view{shadow_depth_view_id_});
        shadow_depth_view_id_ = 0;
    }
    if (shadow_tex_view_id_ != 0) {
        sg_destroy_view(sg_view{shadow_tex_view_id_});
        shadow_tex_view_id_ = 0;
    }
    if (shadow_sampler_id_ != 0) {
        sg_destroy_sampler(sg_sampler{shadow_sampler_id_});
        shadow_sampler_id_ = 0;
    }
    if (shadow_color_img_id_ != 0) {
        sg_destroy_image(sg_image{shadow_color_img_id_});
        shadow_color_img_id_ = 0;
    }
    if (shadow_depth_img_id_ != 0) {
        sg_destroy_image(sg_image{shadow_depth_img_id_});
        shadow_depth_img_id_ = 0;
    }

    if (line_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{line_pip_id_});
        line_pip_id_ = 0;
    }
    if (line_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{line_shd_id_});
        line_shd_id_ = 0;
    }
    if (line_vbuf_id_ != 0) {
        sg_destroy_buffer(sg_buffer{line_vbuf_id_});
        line_vbuf_id_ = 0;
    }

    if (hud_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{hud_pip_id_});
        hud_pip_id_ = 0;
    }
    if (hud_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{hud_shd_id_});
        hud_shd_id_ = 0;
    }
    if (hud_vbuf_id_ != 0) {
        sg_destroy_buffer(sg_buffer{hud_vbuf_id_});
        hud_vbuf_id_ = 0;
    }

    if (skybox_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{skybox_pip_id_});
        skybox_pip_id_ = 0;
    }
    if (skybox_offscreen_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{skybox_offscreen_pip_id_});
        skybox_offscreen_pip_id_ = 0;
    }
    if (skybox_rgba8_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{skybox_rgba8_pip_id_});
        skybox_rgba8_pip_id_ = 0;
    }
    if (skybox_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{skybox_shd_id_});
        skybox_shd_id_ = 0;
    }
    if (proc_sky_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{proc_sky_pip_id_});
        proc_sky_pip_id_ = 0;
    }
    if (proc_sky_offscreen_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{proc_sky_offscreen_pip_id_});
        proc_sky_offscreen_pip_id_ = 0;
    }
    if (proc_sky_rgba8_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{proc_sky_rgba8_pip_id_});
        proc_sky_rgba8_pip_id_ = 0;
    }
    if (proc_sky_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{proc_sky_shd_id_});
        proc_sky_shd_id_ = 0;
    }
    if (sky_cube_mesh_) {
        sky_cube_mesh_->destroy();
        sky_cube_mesh_ = nullptr;
    }
    if (default_env_cube_) {
        default_env_cube_->destroy();
        default_env_cube_ = nullptr;
    }

    editor_.shutdown();
    sg_shutdown();

#if defined(SOKOL_D3D11)
    if (headless_ctx_) {
        static_cast<ID3D11DeviceContext*>(headless_ctx_)->Release();
        headless_ctx_ = nullptr;
    }
    if (headless_dev_) {
        static_cast<ID3D11Device*>(headless_dev_)->Release();
        headless_dev_ = nullptr;
    }
#endif
    is_headless_ = false;
}

void EngineApp::set_mode(EngineMode mode) {
    mode_ = mode;
    if (mode_ == EngineMode::GAME) {
        set_mouse_locked(true);
    } else {
        set_mouse_locked(false);
    }
}

void EngineApp::on_event(const void* raw_event) {
    if (!raw_event) return;
    const auto* ev = static_cast<const sapp_event*>(raw_event);

    // 1. Hotkey toggle between Game and Editor mode (default F2)
    if (ev->type == SAPP_EVENTTYPE_KEY_DOWN && !ev->key_repeat) {
        if (editor_.is_toggle_hotkey_enabled() && ev->key_code == static_cast<int>(editor_.toggle_hotkey())) {
            toggle_mode();
            return;
        }
    }

    // 2. When in Editor mode, let Dear ImGui / ImGuizmo handle UI interaction
    if (mode_ == EngineMode::EDITOR) {
        if (editor_.handle_event(raw_event)) {
            return;
        }
    }

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

        case SAPP_EVENTTYPE_RESIZED:
            config_.width = ev->window_width;
            config_.height = ev->window_height;
            emit("resize", nullptr);
            break;

        case SAPP_EVENTTYPE_MOUSE_MOVE: {
            input_.on_mouse_move(ev->mouse_x, ev->mouse_y, ev->mouse_dx, ev->mouse_dy);
            float sw = static_cast<float>(config_.width);
            float sh = static_cast<float>(config_.height);
            if (sw > 0.0f && sh > 0.0f) {
                Ray ray = camera_.screen_to_ray(ev->mouse_x, ev->mouse_y, sw, sh);
                RaycastHit hit = scene_.raycast(ray, 1000.0f);
                std::shared_ptr<Node3D> hit_node = (hit.hit && hit.entity) ? hit.entity : nullptr;
                if (hit_node != hovered_node_) {
                    if (hovered_node_) {
                        hovered_node_->emit("hover_leave", nullptr);
                    }
                    hovered_node_ = hit_node;
                    if (hovered_node_) {
                        hovered_node_->emit("hover_enter", &hit);
                    }
                }
            }
            break;
        }

        case SAPP_EVENTTYPE_MOUSE_LEAVE:
            if (hovered_node_) {
                hovered_node_->emit("hover_leave", nullptr);
                hovered_node_ = nullptr;
            }
            break;

        case SAPP_EVENTTYPE_MOUSE_DOWN: {
            input_.on_mouse_down(ev->mouse_button);
            if (ev->mouse_button == SAPP_MOUSEBUTTON_LEFT) {
                float sw = static_cast<float>(config_.width);
                float sh = static_cast<float>(config_.height);
                if (sw > 0.0f && sh > 0.0f) {
                    Ray ray = camera_.screen_to_ray(ev->mouse_x, ev->mouse_y, sw, sh);
                    RaycastHit hit = scene_.raycast(ray, 1000.0f);
                    if (hit.hit && hit.entity) {
                        hit.entity->emit("click", &hit);
                        for (Node3D* p = static_cast<Node3D*>(hit.entity.get())->parent(); p != nullptr; p = p->parent()) {
                            p->emit("click", &hit);
                        }
                    }
                }
            }
            break;
        }

        case SAPP_EVENTTYPE_MOUSE_UP:
            input_.on_mouse_up(ev->mouse_button);
            break;

        default:
            break;
    }
}

RaycastHit EngineApp::dispatch_mouse_click(float mouse_x, float mouse_y) {
    float sw = static_cast<float>(config_.width > 0 ? config_.width : 800);
    float sh = static_cast<float>(config_.height > 0 ? config_.height : 600);
    Ray ray = camera_.screen_to_ray(mouse_x, mouse_y, sw, sh);
    RaycastHit hit = scene_.raycast(ray, 1000.0f);
    if (hit.hit && hit.entity) {
        hit.entity->emit("click", &hit);
        for (Node3D* p = static_cast<Node3D*>(hit.entity.get())->parent(); p != nullptr; p = p->parent()) {
            p->emit("click", &hit);
        }
    }
    return hit;
}

void EngineApp::dispatch_mouse_move(float mouse_x, float mouse_y) {
    float sw = static_cast<float>(config_.width > 0 ? config_.width : 800);
    float sh = static_cast<float>(config_.height > 0 ? config_.height : 600);
    Ray ray = camera_.screen_to_ray(mouse_x, mouse_y, sw, sh);
    RaycastHit hit = scene_.raycast(ray, 1000.0f);
    std::shared_ptr<Node3D> hit_node = (hit.hit && hit.entity) ? hit.entity : nullptr;
    if (hit_node != hovered_node_) {
        if (hovered_node_) {
            hovered_node_->emit("hover_leave", nullptr);
        }
        hovered_node_ = hit_node;
        if (hovered_node_) {
            hovered_node_->emit("hover_enter", &hit);
        }
    }
}

void EngineApp::run() {
    if (is_headless_) {
        // Gracefully shutdown headless Sokol context WITHOUT destroying scene entities or update callback!
        PipelineManager::instance().release_all();

        if (default_white_tex_) {
            default_white_tex_->destroy();
            default_white_tex_ = nullptr;
        }
        if (default_black_tex_) {
            default_black_tex_->destroy();
            default_black_tex_ = nullptr;
        }
        if (default_flat_normal_tex_) {
            default_flat_normal_tex_->destroy();
            default_flat_normal_tex_ = nullptr;
        }

        if (pip_id_ != 0) {
            sg_destroy_pipeline(sg_pipeline{pip_id_});
            pip_id_ = 0;
        }
        if (shd_id_ != 0) {
            sg_destroy_shader(sg_shader{shd_id_});
            shd_id_ = 0;
        }

        // Reset GPU handles for all scene meshes and textures so they cleanly re-upload on the window device
        for (auto& entity : scene_.entities()) {
            if (entity && entity->mesh) {
                entity->mesh->destroy();
            }
        }
        for (auto& inst : scene_.instanced_meshes()) {
            if (inst) {
                inst->destroy();
                if (inst->mesh) inst->mesh->destroy();
            }
        }
        for (auto& skinned : scene_.skinned_meshes()) {
            if (skinned && skinned->mesh) {
                skinned->mesh->destroy();
            }
        }
        for (auto& emitter : scene_.particle_emitters()) {
            if (emitter && emitter->get_particle_mesh()) {
                emitter->get_particle_mesh()->destroy();
            }
        }
        if (sky_cube_mesh_) {
            sky_cube_mesh_->destroy();
        }
        if (composer_) {
            composer_->destroy();
        }

        if (sg_isvalid()) {
            sg_shutdown();
        }

#if defined(SOKOL_D3D11)
        if (headless_ctx_) {
            static_cast<ID3D11DeviceContext*>(headless_ctx_)->Release();
            headless_ctx_ = nullptr;
        }
        if (headless_dev_) {
            static_cast<ID3D11Device*>(headless_dev_)->Release();
            headless_dev_ = nullptr;
        }
#endif
        is_headless_ = false;
    }
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
    desc.sample_count = 4;
    desc.window_title = config_.title.c_str();
    desc.logger.func = slog_func;
    desc.icon.sokol_default = true;
    desc.disable_vsync = !config_.vsync;
    desc.swap_interval = config_.vsync ? 1 : 0;

    running_ = true;
    sapp_run(&desc);
    running_ = false;
}

extern "C" void sapp_set_swap_interval(int interval);

void EngineApp::set_vsync(bool enabled) {
    config_.vsync = enabled;
    if (running_) {
        sapp_set_swap_interval(enabled ? 1 : 0);
    }
}

void EngineApp::close() {
    if (running_) {
        sapp_request_quit();
    }
}

bool EngineApp::save_screenshot(const std::string& filepath) {
    return engine::save_screenshot(*this, filepath);
}

void EngineApp::on(const std::string& event_name, AppEventCallback callback) {
    if (callback) {
        app_event_listeners_[event_name].push_back(std::move(callback));
    }
}

void EngineApp::emit(const std::string& event_name, void* data) {
    auto it = app_event_listeners_.find(event_name);
    if (it != app_event_listeners_.end()) {
        auto callbacks = it->second;
        for (const auto& cb : callbacks) {
            if (cb) {
                cb(event_name, data);
            }
        }
    }
}

} // namespace engine
