#include "engine/app.hpp"

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

struct FSParams {
    glm::vec4 light_dir;        // xyz = dir, w = intensity
    glm::vec4 light_color;      // rgb = color, w = unused
    glm::vec4 ambient_color;    // rgb = ambient, w = unused
    glm::vec4 eye_pos;          // xyz = camera position, w = unused
    glm::vec4 material_color;   // rgba base_color
    glm::vec4 material_params;  // x = roughness, y = metallic, zw = uv_scale
    glm::vec4 material_uv_offset; // xy = uv_offset, zw = unused
    glm::vec4 hemi_sky;         // rgb = sky ambient, w = 1.0
    glm::vec4 hemi_ground;      // rgb = ground ambient, w = 1.0
    glm::vec4 fog_color;        // rgb = fog color, w = tone_mapping_enabled (1.0 or 0.0)
    glm::vec4 fog_params;       // x = fog_type (0=off, 1=linear, 2=exp2), y = near, z = far, w = density
};

struct ShadowVSParams {
    glm::mat4 light_mvp;
};

struct LineVertex {
    glm::vec3 pos;
    glm::vec4 color;
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
    "};\n"
    "struct vs_out {\n"
    "    float4 color : COLOR0;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float3 world_pos : TEXCOORD1;\n"
    "    float4 light_pos : TEXCOORD2;\n"
    "    float4 pos : SV_Position;\n"
    "};\n"
    "vs_out main(vs_in inp) {\n"
    "    vs_out outp;\n"
    "    outp.pos = mul(mvp, float4(inp.pos, 1.0));\n"
    "    outp.world_pos = mul(model, float4(inp.pos, 1.0)).xyz;\n"
    "    outp.normal = mul((float3x3)normal_mat, inp.normal);\n"
    "    outp.uv = inp.uv;\n"
    "    outp.color = inp.color;\n"
    "    float3 normal_bias_offset = inp.normal * 0.04;\n"
    "    outp.light_pos = mul(light_mvp, float4(inp.pos + normal_bias_offset, 1.0));\n"
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
    "    float4 material_uv_offset;\n" // xy=uv_offset, zw=unused
    "    float4 hemi_sky;\n"
    "    float4 hemi_ground;\n"
    "    float4 fog_color;\n"       // rgb=fog color, w=tone_mapping_enabled (1.0 or 0.0)
    "    float4 fog_params;\n"      // x=fog_type (0=off, 1=linear, 2=exp2), y=near, z=far, w=density
    "};\n"
    "Texture2D tex_albedo : register(t0);\n"
    "SamplerState smp_albedo : register(s0);\n"
    "Texture2D tex_shadow : register(t1);\n"
    "SamplerState smp_shadow : register(s1);\n"
    "struct ps_in {\n"
    "    float4 color : COLOR0;\n"
    "    float3 normal : NORMAL;\n"
    "    float2 uv : TEXCOORD0;\n"
    "    float3 world_pos : TEXCOORD1;\n"
    "    float4 light_pos : TEXCOORD2;\n"
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
    "    float texel = 1.0 / 1024.0;\n"
    "    // 4-tap optimized PCF\n"
    "    float s0 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2(-0.5, -0.5) * texel).r) ? 1.0 : 0.0;\n"
    "    float s1 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2( 0.5, -0.5) * texel).r) ? 1.0 : 0.0;\n"
    "    float s2 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2(-0.5,  0.5) * texel).r) ? 1.0 : 0.0;\n"
    "    float s3 = (current_depth <= tex_shadow.Sample(smp_shadow, uv + float2( 0.5,  0.5) * texel).r) ? 1.0 : 0.0;\n"
    "    float shadow = (s0 + s1 + s2 + s3) * 0.25;\n"
    "    float2 border = min(uv, 1.0 - uv);\n"
    "    float edge_fade = saturate(min(border.x, border.y) * 15.0);\n"
    "    return lerp(1.0, shadow, edge_fade);\n"
    "}\n"
    "float4 main(ps_in inp) : SV_Target0 {\n"
    "    float2 uv = inp.uv * material_params.zw + material_uv_offset.xy;\n"
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
    "    float hemi = clamp(N.y * 0.5 + 0.5, 0.0, 1.0);\n"
    "    float3 ambient_light = lerp(hemi_ground.rgb, hemi_sky.rgb, hemi);\n"
    "    float3 ambient = ambient_light * albedo * (1.0 - 0.5 * metallic);\n"
    "    float shadow = sample_shadow(inp.light_pos, N, L);\n"
    "    float3 final_color = ambient + (diffuse + specular) * shadow;\n"
    "    // Atmospheric Depth Fog\n"
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
    "    // ACES Filmic Tone Mapping\n"
    "    if (fog_color.w > 0.5) {\n"
    "        final_color = apply_aces_filmic(final_color);\n"
    "    }\n"
    "    return float4(final_color, tex_sample.a * inp.color.a * material_color.a);\n"
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

#else // Fallback GLSL
static const char* glsl_vs = "#version 330\nvoid main(){}\n";
static const char* glsl_fs = "#version 330\nout vec4 c;\nvoid main(){c=vec4(1.0);}\n";
static const char* glsl_shadow_vs = "#version 330\nvoid main(){}\n";
static const char* glsl_shadow_fs = "#version 330\nout vec4 c;\nvoid main(){c=vec4(1.0);}\n";
static const char* glsl_line_vs = "#version 330\nvoid main(){}\n";
static const char* glsl_line_fs = "#version 330\nout vec4 c;\nvoid main(){c=vec4(1.0);}\n";
static const char* glsl_hud_vs = "#version 330\nvoid main(){}\n";
static const char* glsl_hud_fs = "#version 330\nout vec4 c;\nvoid main(){c=vec4(1.0);}\n";
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

void EngineApp::init_shadow_pipeline() {
    // 1. Color attachment image to store depth map
    sg_image_desc col_desc{};
    col_desc.usage.color_attachment = true;
    col_desc.width = SHADOW_MAP_SIZE;
    col_desc.height = SHADOW_MAP_SIZE;
    col_desc.pixel_format = SG_PIXELFORMAT_R32F;
    col_desc.sample_count = 1;
    col_desc.label = "shadow-color-map";
    sg_image col_img = sg_make_image(&col_desc);
    shadow_color_img_id_ = col_img.id;

    // 2. Depth stencil attachment image for shadow pass
    sg_image_desc depth_desc{};
    depth_desc.usage.depth_stencil_attachment = true;
    depth_desc.width = SHADOW_MAP_SIZE;
    depth_desc.height = SHADOW_MAP_SIZE;
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
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
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

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(VSParams);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.uniform_blocks[1].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[1].size = sizeof(FSParams);
    shd_desc.uniform_blocks[1].hlsl_register_b_n = 1;

    // Slot 0: Albedo Texture & Sampler
    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;

    // Slot 1: Shadow Map Texture & Sampler
    shd_desc.views[1].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[1].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[1].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[1].texture.hlsl_register_t_n = 1;

    shd_desc.samplers[1].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[1].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[1].hlsl_register_s_n = 1;
#endif
    shd_desc.label = "pbr-daylight-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    // Pipeline with Depth Test
    sg_pipeline_desc pip_desc{};
    pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[2].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[3].format = SG_VERTEXFORMAT_FLOAT4;
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

    init_shadow_pipeline();
    init_hud_and_line_pipelines();
}

void EngineApp::on_init() {
    sg_desc desc{};
    desc.environment = sglue_environment();
    desc.logger.func = slog_func;
    desc.buffer_pool_size = 8192;
    desc.image_pool_size = 512;
    desc.pipeline_pool_size = 256;
    sg_setup(&desc);

    init_pipeline_and_shaders();
    audio_.init();
    editor_.init();
}

void EngineApp::render_shadow_pass() {
    if (shadow_pip_id_ == 0 || shadow_color_view_id_ == 0 || shadow_depth_view_id_ == 0) {
        return;
    }

    // 1. Calculate Light Projection and View
    glm::vec3 sun_dir = glm::normalize(scene_.light.direction);
    glm::vec3 center = glm::vec3(camera_.target.x, 0.0f, camera_.target.z);
    glm::vec3 light_pos = center - sun_dir * 35.0f;
    glm::mat4 light_view = glm::lookAt(light_pos, center, glm::vec3(0.0f, 1.0f, 0.0f));
    glm::mat4 light_proj = glm::ortho(-32.0f, 32.0f, -32.0f, 32.0f, 2.0f, 85.0f);
    light_vp_ = light_proj * light_view;

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

    for (const auto& entity : scene_.entities()) {
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

void EngineApp::on_frame() {
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
    camera_.aspect = (h > 0.0f) ? (w / h) : 1.333333f;
    glm::mat4 vp = camera_.view_projection_matrix();

    // 5. Render Pass 1: Offscreen Shadow Map Pass
    render_shadow_pass();

    // 6. Render Pass 2: Main Swapchain Pass with Daylight Clear Color
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
        fs_params.hemi_sky = glm::vec4(scene_.light.ambient_sky, 1.0f);
        fs_params.hemi_ground = glm::vec4(scene_.light.ambient_ground, 1.0f);
        fs_params.fog_color = glm::vec4(fog_color_, tone_mapping_enabled_ ? 1.0f : 0.0f);
        fs_params.fog_params = glm::vec4(
            fog_enabled_ ? static_cast<float>(fog_type_) : 0.0f,
            fog_near_,
            fog_far_,
            fog_density_
        );

        auto default_white = scene_.default_white_texture();
        if (default_white) {
            default_white->ensure_gpu_resources();
        }
        auto default_mat = scene_.default_material();

        glm::vec4 last_mat_color{-999.0f};
        glm::vec4 last_mat_params{-999.0f};
        glm::vec4 last_mat_uv_offset{-999.0f};
        bool fs_applied = false;

        // Draw all visible entities in Scene
        for (const auto& entity : scene_.entities()) {
            if (!entity || !entity->visible || !entity->mesh) {
                continue;
            }

            if (!entity->mesh->ensure_gpu_buffers()) {
                continue;
            }

            // Material resolution
            auto mat = entity->material ? entity->material : default_mat;
            auto tex = (mat && mat->albedo_map) ? mat->albedo_map : default_white;
            if (tex) {
                tex->ensure_gpu_resources();
            }
            if (!tex || !tex->is_valid()) {
                tex = default_white;
            }
            if (!tex || !tex->is_valid()) {
                continue;
            }

            // Compute MVP, Normal, and Light MVP matrices
            glm::mat4 model = entity->world_model_matrix();
            glm::mat4 normal_mat = entity->world_normal_matrix();
            glm::mat4 mvp = vp * model;
            glm::mat4 l_mvp = light_vp_ * model;

            VSParams vs_params{ mvp, model, normal_mat, l_mvp };

            sg_bindings bind{};
            bind.vertex_buffers[0] = sg_buffer{ entity->mesh->vbuf_id };
            bind.index_buffer = sg_buffer{ entity->mesh->ibuf_id };
            // Slot 0: Albedo Texture
            bind.views[0] = sg_view{ tex->view_id };
            bind.samplers[0] = sg_sampler{ tex->sampler_id };
            // Slot 1: Shadow Texture
            bind.views[1] = sg_view{ shadow_tex_view_id_ };
            bind.samplers[1] = sg_sampler{ shadow_sampler_id_ };
            sg_apply_bindings(&bind);

            sg_apply_uniforms(0, SG_RANGE_REF(vs_params));

            glm::vec4 cur_mat_color = mat->base_color * entity->color;
            glm::vec4 cur_mat_params = glm::vec4(mat->roughness, mat->metallic, mat->uv_scale.x, mat->uv_scale.y);
            glm::vec4 cur_mat_uv_offset = glm::vec4(mat ? mat->uv_offset.x : 0.0f, mat ? mat->uv_offset.y : 0.0f, 0.0f, 0.0f);
            if (!fs_applied || cur_mat_color != last_mat_color || cur_mat_params != last_mat_params || cur_mat_uv_offset != last_mat_uv_offset) {
                fs_params.material_color = cur_mat_color;
                fs_params.material_params = cur_mat_params;
                fs_params.material_uv_offset = cur_mat_uv_offset;
                sg_apply_uniforms(1, SG_RANGE_REF(fs_params));
                last_mat_color = cur_mat_color;
                last_mat_params = cur_mat_params;
                last_mat_uv_offset = cur_mat_uv_offset;
                fs_applied = true;
            }

            sg_draw(0, entity->mesh->num_indices, 1);
        }
    }

    // 7. Optional Debug Hitbox Rendering (F1 toggle or Editor Mode)
    if (show_debug_hitboxes_ || mode_ == EngineMode::EDITOR) {
        render_debug_hitboxes(vp);
    }

    // 8. 2D HUD Rendering (only in Game Mode)
    if (show_hud_ && mode_ == EngineMode::GAME) {
        render_hud(w, h, current_fps_);
    }

    // 9. Visual Editor UI (Dear ImGui & ImGuizmo) - only in Editor Mode
    if (mode_ == EngineMode::EDITOR) {
        editor_.render(static_cast<float>(dt), w, h);
    }

    sg_end_pass();
    sg_commit();

    // 9. Reset per-frame input transients
    input_.post_frame();
}

void EngineApp::on_cleanup() {
    update_callback_ = nullptr;
    scene_.clear();
    audio_.shutdown();

    if (pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{pip_id_});
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        sg_destroy_shader(sg_shader{shd_id_});
        shd_id_ = 0;
    }
    if (shadow_pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{shadow_pip_id_});
        shadow_pip_id_ = 0;
    }
    if (shadow_shd_id_ != 0) {
        sg_destroy_shader(sg_shader{shadow_shd_id_});
        shadow_shd_id_ = 0;
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

    editor_.shutdown();
    sg_shutdown();
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

} // namespace engine
