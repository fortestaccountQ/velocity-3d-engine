#include "engine/post_process.hpp"
#include "engine/app.hpp"
#include "engine/scene.hpp"
#include "engine/camera.hpp"

#include "sokol_gfx.h"
#include "sokol_app.h"
#include "sokol_glue.h"

#include <iostream>
#include <algorithm>

namespace engine {

struct QuadVertex {
    float x, y;
    float u, v;
};

static const QuadVertex QUAD_VERTS[4] = {
    { -1.0f, -1.0f, 0.0f, 1.0f },
    {  1.0f, -1.0f, 1.0f, 1.0f },
    {  1.0f,  1.0f, 1.0f, 0.0f },
    { -1.0f,  1.0f, 0.0f, 0.0f }
};

static const uint16_t QUAD_INDICES[6] = {
    0, 1, 2,
    0, 2, 3
};

// ---------------------------------------------------------------------------
// Shaders for Post Processing
// ---------------------------------------------------------------------------
#if defined(SOKOL_D3D11)
static const char* hlsl_quad_vs =
    "struct VSIn {\n"
    "    float2 pos : POSITION;\n"
    "    float2 uv : TEXCOORD0;\n"
    "};\n"
    "struct VSOut {\n"
    "    float4 pos : SV_Position;\n"
    "    float2 uv : TEXCOORD0;\n"
    "};\n"
    "VSOut main(VSIn input) {\n"
    "    VSOut output;\n"
    "    output.pos = float4(input.pos, 0.0, 1.0);\n"
    "    output.uv = input.uv;\n"
    "    return output;\n"
    "}\n";

static const char* hlsl_bloom_fs =
    "cbuffer BloomParams : register(b0) {\n"
    "    float threshold;\n"
    "    float strength;\n"
    "    float radius;\n"
    "    float pad;\n"
    "};\n"
    "Texture2D scene_tex : register(t0);\n"
    "SamplerState smp : register(s0);\n"
    "float4 main(float4 pos : SV_Position, float2 uv : TEXCOORD0) : SV_Target {\n"
    "    float4 base_col = scene_tex.Sample(smp, uv);\n"
    "    float3 bloom = float3(0.0, 0.0, 0.0);\n"
    "    float2 offsets[9] = {\n"
    "        float2(-1.0, -1.0), float2(0.0, -1.0), float2(1.0, -1.0),\n"
    "        float2(-1.0,  0.0), float2(0.0,  0.0), float2(1.0,  0.0),\n"
    "        float2(-1.0,  1.0), float2(0.0,  1.0), float2(1.0,  1.0)\n"
    "    };\n"
    "    float weights[9] = {\n"
    "        0.0625, 0.125, 0.0625,\n"
    "        0.125,  0.25,  0.125,\n"
    "        0.0625, 0.125, 0.0625\n"
    "    };\n"
    "    float2 step_uv = (radius * 0.003) * float2(1.0, 1.0);\n"
    "    for (int i = 0; i < 9; ++i) {\n"
    "        float3 s = scene_tex.Sample(smp, uv + offsets[i] * step_uv).rgb;\n"
    "        float lum = dot(s, float3(0.2126, 0.7152, 0.0722));\n"
    "        float bright = max(lum - threshold, 0.0);\n"
    "        float3 bright_color = s * (bright / max(lum, 0.0001));\n"
    "        bloom += bright_color * weights[i];\n"
    "    }\n"
    "    return float4(base_col.rgb + bloom * strength, base_col.a);\n"
    "}\n";

static const char* hlsl_ssao_fs =
    "cbuffer SSAOParams : register(b0) {\n"
    "    float radius;\n"
    "    float bias;\n"
    "    float power;\n"
    "    float pad;\n"
    "};\n"
    "Texture2D scene_tex : register(t0);\n"
    "SamplerState smp : register(s0);\n"
    "Texture2D depth_tex : register(t1);\n"
    "SamplerState depth_smp : register(s1);\n"
    "float4 main(float4 pos : SV_Position, float2 uv : TEXCOORD0) : SV_Target {\n"
    "    float4 col = scene_tex.Sample(smp, uv);\n"
    "    float center_d = depth_tex.Sample(depth_smp, uv).r;\n"
    "    float occlusion = 0.0;\n"
    "    float2 samples[8] = {\n"
    "        float2( 1.0,  0.0), float2(-1.0,  0.0), float2(0.0,  1.0), float2(0.0, -1.0),\n"
    "        float2( 0.7,  0.7), float2(-0.7,  0.7), float2(0.7, -0.7), float2(-0.7, -0.7)\n"
    "    };\n"
    "    float2 step = radius * float2(0.004, 0.004);\n"
    "    for (int i = 0; i < 8; ++i) {\n"
    "        float d = depth_tex.Sample(depth_smp, uv + samples[i] * step).r;\n"
    "        float diff = center_d - d;\n"
    "        if (diff > bias && diff < radius * 0.1) {\n"
    "            occlusion += 1.0;\n"
    "        }\n"
    "    }\n"
    "    float ao = 1.0 - (occlusion / 8.0);\n"
    "    ao = clamp(pow(max(ao, 0.0), power), 0.0, 1.0);\n"
    "    return float4(col.rgb * ao, col.a);\n"
    "}\n";

static const char* hlsl_fxaa_fs =
    "cbuffer FXAAParams : register(b0) {\n"
    "    float2 texel_size;\n"
    "    float2 pad;\n"
    "};\n"
    "Texture2D scene_tex : register(t0);\n"
    "SamplerState smp : register(s0);\n"
    "float rgb2luma(float3 rgb) {\n"
    "    return sqrt(dot(rgb, float3(0.299, 0.587, 0.114)));\n"
    "}\n"
    "float4 main(float4 pos : SV_Position, float2 uv : TEXCOORD0) : SV_Target {\n"
    "    float3 rgbM = scene_tex.Sample(smp, uv).rgb;\n"
    "    float lumaM = rgb2luma(rgbM);\n"
    "    float lumaNW = rgb2luma(scene_tex.Sample(smp, uv + float2(-1.0, -1.0) * texel_size).rgb);\n"
    "    float lumaNE = rgb2luma(scene_tex.Sample(smp, uv + float2( 1.0, -1.0) * texel_size).rgb);\n"
    "    float lumaSW = rgb2luma(scene_tex.Sample(smp, uv + float2(-1.0,  1.0) * texel_size).rgb);\n"
    "    float lumaSE = rgb2luma(scene_tex.Sample(smp, uv + float2( 1.0,  1.0) * texel_size).rgb);\n"
    "    float lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));\n"
    "    float lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));\n"
    "    float range = lumaMax - lumaMin;\n"
    "    if (range < max(0.05, lumaMax * 0.125)) {\n"
    "        return float4(rgbM, 1.0);\n"
    "    }\n"
    "    float2 dir;\n"
    "    dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));\n"
    "    dir.y =  ((lumaNW + lumaSW) - (lumaNE + lumaSE));\n"
    "    float dirReduce = max((lumaNW + lumaNE + lumaSW + lumaSE) * 0.03125, 0.0078125);\n"
    "    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);\n"
    "    dir = min(float2(8.0, 8.0), max(float2(-8.0, -8.0), dir * rcpDirMin)) * texel_size;\n"
    "    float3 rgbA = 0.5 * (\n"
    "        scene_tex.Sample(smp, uv + dir * (1.0 / 3.0 - 0.5)).rgb +\n"
    "        scene_tex.Sample(smp, uv + dir * (2.0 / 3.0 - 0.5)).rgb);\n"
    "    float3 rgbB = rgbA * 0.5 + 0.25 * (\n"
    "        scene_tex.Sample(smp, uv + dir * -0.5).rgb +\n"
    "        scene_tex.Sample(smp, uv + dir * 0.5).rgb);\n"
    "    float lumaB = rgb2luma(rgbB);\n"
    "    if ((lumaB < lumaMin) || (lumaB > lumaMax)) {\n"
    "        return float4(rgbA, 1.0);\n"
    "    } else {\n"
    "        return float4(rgbB, 1.0);\n"
    "    }\n"
    "}\n";

static const char* hlsl_tonemap_fs =
    "cbuffer TonemapParams : register(b0) {\n"
    "    float exposure;\n"
    "    float gamma;\n"
    "    int mode;\n"
    "    float pad;\n"
    "};\n"
    "Texture2D scene_tex : register(t0);\n"
    "SamplerState smp : register(s0);\n"
    "float3 aces_filmic(float3 x) {\n"
    "    float a = 2.51f;\n"
    "    float b = 0.03f;\n"
    "    float c = 2.43f;\n"
    "    float d = 0.59f;\n"
    "    float e = 0.14f;\n"
    "    return saturate((x * (a * x + b)) / (x * (c * x + d) + e));\n"
    "}\n"
    "float3 reinhard(float3 x) {\n"
    "    return x / (1.0 + x);\n"
    "}\n"
    "float3 cineon(float3 x) {\n"
    "    x = max(float3(0.0, 0.0, 0.0), x - 0.004);\n"
    "    return (x * (6.2 * x + 0.5)) / (x * (6.2 * x + 1.7) + 0.06);\n"
    "}\n"
    "float3 neutral(float3 color) {\n"
    "    const float startCompression = 0.8 - 0.04;\n"
    "    const float desaturation = 0.15;\n"
    "    float x = min(color.r, min(color.g, color.b));\n"
    "    float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;\n"
    "    color -= offset;\n"
    "    float peak = max(color.r, max(color.g, color.b));\n"
    "    if (peak < startCompression) return color;\n"
    "    const float d = 1.0 - startCompression;\n"
    "    float newPeak = 1.0 - d * d / (peak + d - startCompression);\n"
    "    color *= newPeak / peak;\n"
    "    float g = 1.0 - 1.0 / (desaturation * (peak - newPeak) + 1.0);\n"
    "    return lerp(color, newPeak.xxx, g);\n"
    "}\n"
    "float4 main(float4 pos : SV_Position, float2 uv : TEXCOORD0) : SV_Target {\n"
    "    float4 col = scene_tex.Sample(smp, uv);\n"
    "    float3 c = col.rgb * exposure;\n"
    "    if (mode == 0) {\n"
    "        c = aces_filmic(c);\n"
    "    } else if (mode == 1) {\n"
    "        c = reinhard(c);\n"
    "    } else if (mode == 2) {\n"
    "        c = cineon(c);\n"
    "    } else if (mode == 3) {\n"
    "        c = saturate(c);\n"
    "    } else if (mode == 4) {\n"
    "        c = neutral(c);\n"
    "    }\n"
    "    float inv_gamma = 1.0 / max(gamma, 0.0001);\n"
    "    c = pow(max(c, 0.0), float3(inv_gamma, inv_gamma, inv_gamma));\n"
    "    return float4(c, col.a);\n"
    "}\n";

static const char* hlsl_vignette_fs =
    "cbuffer VignetteParams : register(b0) {\n"
    "    float vignette;\n"
    "    float chromatic;\n"
    "    float grain;\n"
    "    float time;\n"
    "};\n"
    "Texture2D scene_tex : register(t0);\n"
    "SamplerState smp : register(s0);\n"
    "float rand(float2 co) {\n"
    "    return frac(sin(dot(co, float2(12.9898, 78.233))) * 43758.5453);\n"
    "}\n"
    "float4 main(float4 pos : SV_Position, float2 uv : TEXCOORD0) : SV_Target {\n"
    "    float2 to_center = uv - float2(0.5, 0.5);\n"
    "    float dist = length(to_center);\n"
    "    float2 r_uv = uv - to_center * chromatic;\n"
    "    float2 b_uv = uv + to_center * chromatic;\n"
    "    float r = scene_tex.Sample(smp, r_uv).r;\n"
    "    float g = scene_tex.Sample(smp, uv).g;\n"
    "    float b = scene_tex.Sample(smp, b_uv).b;\n"
    "    float a = scene_tex.Sample(smp, uv).a;\n"
    "    float3 col = float3(r, g, b);\n"
    "    float vig = smoothstep(0.8, 0.8 - vignette, dist * 1.414);\n"
    "    col *= vig;\n"
    "    float noise = (rand(uv + float2(time, time * 0.5)) - 0.5) * grain;\n"
    "    col += noise;\n"
    "    return float4(saturate(col), a);\n"
    "}\n";

static const char* hlsl_colorgrade_fs =
    "cbuffer ColorGradingParams : register(b0) {\n"
    "    float contrast;\n"
    "    float saturation;\n"
    "    float brightness;\n"
    "    float pad;\n"
    "};\n"
    "Texture2D scene_tex : register(t0);\n"
    "SamplerState smp : register(s0);\n"
    "float4 main(float4 pos : SV_Position, float2 uv : TEXCOORD0) : SV_Target {\n"
    "    float4 col = scene_tex.Sample(smp, uv);\n"
    "    float3 c = col.rgb;\n"
    "    c *= brightness;\n"
    "    c = (c - 0.5) * contrast + 0.5;\n"
    "    float lum = dot(c, float3(0.2126, 0.7152, 0.0722));\n"
    "    c = lerp(float3(lum, lum, lum), c, saturation);\n"
    "    return float4(saturate(c), col.a);\n"
    "}\n";

static const char* hlsl_blit_fs =
    "Texture2D tex : register(t0);\n"
    "SamplerState smp : register(s0);\n"
    "float4 main(float4 pos : SV_Position, float2 uv : TEXCOORD0) : SV_Target {\n"
    "    return tex.Sample(smp, uv);\n"
    "}\n";

#else
// GLSL 330 fallbacks for non-D3D11 backends
static const char* glsl_quad_vs =
    "#version 330\n"
    "layout(location = 0) in vec2 pos;\n"
    "layout(location = 1) in vec2 uv;\n"
    "out vec2 v_uv;\n"
    "void main() {\n"
    "    gl_Position = vec4(pos, 0.0, 1.0);\n"
    "    v_uv = uv;\n"
    "}\n";

static const char* glsl_bloom_fs =
    "#version 330\n"
    "uniform BloomParams {\n"
    "    float threshold;\n"
    "    float strength;\n"
    "    float radius;\n"
    "    float pad;\n"
    "};\n"
    "uniform sampler2D scene_tex;\n"
    "in vec2 v_uv;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    vec4 base_col = texture(scene_tex, v_uv);\n"
    "    vec3 bloom = vec3(0.0);\n"
    "    vec2 offsets[9] = vec2[](\n"
    "        vec2(-1.0, -1.0), vec2(0.0, -1.0), vec2(1.0, -1.0),\n"
    "        vec2(-1.0,  0.0), vec2(0.0,  0.0), vec2(1.0,  0.0),\n"
    "        vec2(-1.0,  1.0), vec2(0.0,  1.0), vec2(1.0,  1.0)\n"
    "    );\n"
    "    float weights[9] = float[](\n"
    "        0.0625, 0.125, 0.0625,\n"
    "        0.125,  0.25,  0.125,\n"
    "        0.0625, 0.125, 0.0625\n"
    "    );\n"
    "    vec2 step_uv = (radius * 0.003) * vec2(1.0, 1.0);\n"
    "    for (int i = 0; i < 9; ++i) {\n"
    "        vec3 s = texture(scene_tex, v_uv + offsets[i] * step_uv).rgb;\n"
    "        float lum = dot(s, vec3(0.2126, 0.7152, 0.0722));\n"
    "        float bright = max(lum - threshold, 0.0);\n"
    "        vec3 bright_color = s * (bright / max(lum, 0.0001));\n"
    "        bloom += bright_color * weights[i];\n"
    "    }\n"
    "    frag_color = vec4(base_col.rgb + bloom * strength, base_col.a);\n"
    "}\n";

static const char* glsl_ssao_fs =
    "#version 330\n"
    "uniform SSAOParams {\n"
    "    float radius;\n"
    "    float bias;\n"
    "    float power;\n"
    "    float pad;\n"
    "};\n"
    "uniform sampler2D scene_tex;\n"
    "uniform sampler2D depth_tex;\n"
    "in vec2 v_uv;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    vec4 col = texture(scene_tex, v_uv);\n"
    "    float center_d = texture(depth_tex, v_uv).r;\n"
    "    float occlusion = 0.0;\n"
    "    vec2 samples[8] = vec2[](\n"
    "        vec2( 1.0,  0.0), vec2(-1.0,  0.0), vec2(0.0,  1.0), vec2(0.0, -1.0),\n"
    "        vec2( 0.7,  0.7), vec2(-0.7,  0.7), vec2(0.7, -0.7), vec2(-0.7, -0.7)\n"
    "    );\n"
    "    vec2 step = radius * vec2(0.004, 0.004);\n"
    "    for (int i = 0; i < 8; ++i) {\n"
    "        float d = texture(depth_tex, v_uv + samples[i] * step).r;\n"
    "        float diff = center_d - d;\n"
    "        if (diff > bias && diff < radius * 0.1) {\n"
    "            occlusion += 1.0;\n"
    "        }\n"
    "    }\n"
    "    float ao = 1.0 - (occlusion / 8.0);\n"
    "    ao = clamp(pow(max(ao, 0.0), power), 0.0, 1.0);\n"
    "    frag_color = vec4(col.rgb * ao, col.a);\n"
    "}\n";

static const char* glsl_fxaa_fs =
    "#version 330\n"
    "uniform FXAAParams {\n"
    "    vec2 texel_size;\n"
    "    vec2 pad;\n"
    "};\n"
    "uniform sampler2D scene_tex;\n"
    "in vec2 v_uv;\n"
    "out vec4 frag_color;\n"
    "float rgb2luma(vec3 rgb) {\n"
    "    return sqrt(dot(rgb, vec3(0.299, 0.587, 0.114)));\n"
    "}\n"
    "void main() {\n"
    "    vec3 rgbM = texture(scene_tex, v_uv).rgb;\n"
    "    float lumaM = rgb2luma(rgbM);\n"
    "    float lumaNW = rgb2luma(texture(scene_tex, v_uv + vec2(-1.0, -1.0) * texel_size).rgb);\n"
    "    float lumaNE = rgb2luma(texture(scene_tex, v_uv + vec2( 1.0, -1.0) * texel_size).rgb);\n"
    "    float lumaSW = rgb2luma(texture(scene_tex, v_uv + vec2(-1.0,  1.0) * texel_size).rgb);\n"
    "    float lumaSE = rgb2luma(texture(scene_tex, v_uv + vec2( 1.0,  1.0) * texel_size).rgb);\n"
    "    float lumaMin = min(lumaM, min(min(lumaNW, lumaNE), min(lumaSW, lumaSE)));\n"
    "    float lumaMax = max(lumaM, max(max(lumaNW, lumaNE), max(lumaSW, lumaSE)));\n"
    "    float range = lumaMax - lumaMin;\n"
    "    if (range < max(0.05, lumaMax * 0.125)) {\n"
    "        frag_color = vec4(rgbM, 1.0);\n"
    "        return;\n"
    "    }\n"
    "    vec2 dir;\n"
    "    dir.x = -((lumaNW + lumaNE) - (lumaSW + lumaSE));\n"
    "    dir.y =  ((lumaNW + lumaSW) - (lumaNE + lumaSE));\n"
    "    float dirReduce = max((lumaNW + lumaNE + lumaSW + lumaSE) * 0.03125, 0.0078125);\n"
    "    float rcpDirMin = 1.0 / (min(abs(dir.x), abs(dir.y)) + dirReduce);\n"
    "    dir = min(vec2(8.0, 8.0), max(vec2(-8.0, -8.0), dir * rcpDirMin)) * texel_size;\n"
    "    vec3 rgbA = 0.5 * (\n"
    "        texture(scene_tex, v_uv + dir * (1.0 / 3.0 - 0.5)).rgb +\n"
    "        texture(scene_tex, v_uv + dir * (2.0 / 3.0 - 0.5)).rgb);\n"
    "    vec3 rgbB = rgbA * 0.5 + 0.25 * (\n"
    "        texture(scene_tex, v_uv + dir * -0.5).rgb +\n"
    "        texture(scene_tex, v_uv + dir * 0.5).rgb);\n"
    "    float lumaB = rgb2luma(rgbB);\n"
    "    if ((lumaB < lumaMin) || (lumaB > lumaMax)) {\n"
    "        frag_color = vec4(rgbA, 1.0);\n"
    "    } else {\n"
    "        frag_color = vec4(rgbB, 1.0);\n"
    "    }\n"
    "}\n";

static const char* glsl_tonemap_fs =
    "#version 330\n"
    "uniform TonemapParams {\n"
    "    float exposure;\n"
    "    float gamma;\n"
    "    int mode;\n"
    "    float pad;\n"
    "};\n"
    "uniform sampler2D scene_tex;\n"
    "in vec2 v_uv;\n"
    "out vec4 frag_color;\n"
    "vec3 aces_filmic(vec3 x) {\n"
    "    float a = 2.51;\n"
    "    float b = 0.03;\n"
    "    float c = 2.43;\n"
    "    float d = 0.59;\n"
    "    float e = 0.14;\n"
    "    return clamp((x * (a * x + b)) / (x * (c * x + d) + e), 0.0, 1.0);\n"
    "}\n"
    "vec3 reinhard(vec3 x) {\n"
    "    return x / (1.0 + x);\n"
    "}\n"
    "vec3 cineon(vec3 x) {\n"
    "    x = max(vec3(0.0), x - 0.004);\n"
    "    return (x * (6.2 * x + 0.5)) / (x * (6.2 * x + 1.7) + 0.06);\n"
    "}\n"
    "vec3 neutral(vec3 color) {\n"
    "    const float startCompression = 0.8 - 0.04;\n"
    "    const float desaturation = 0.15;\n"
    "    float x = min(color.r, min(color.g, color.b));\n"
    "    float offset = x < 0.08 ? x - 6.25 * x * x : 0.04;\n"
    "    color -= offset;\n"
    "    float peak = max(color.r, max(color.g, color.b));\n"
    "    if (peak < startCompression) return color;\n"
    "    const float d = 1.0 - startCompression;\n"
    "    float newPeak = 1.0 - d * d / (peak + d - startCompression);\n"
    "    color *= newPeak / peak;\n"
    "    float g = 1.0 - 1.0 / (desaturation * (peak - newPeak) + 1.0);\n"
    "    return mix(color, vec3(newPeak), g);\n"
    "}\n"
    "void main() {\n"
    "    vec4 col = texture(scene_tex, v_uv);\n"
    "    vec3 c = col.rgb * exposure;\n"
    "    if (mode == 0) c = aces_filmic(c);\n"
    "    else if (mode == 1) c = reinhard(c);\n"
    "    else if (mode == 2) c = cineon(c);\n"
    "    else if (mode == 3) c = clamp(c, 0.0, 1.0);\n"
    "    else if (mode == 4) c = neutral(c);\n"
    "    float inv_gamma = 1.0 / max(gamma, 0.0001);\n"
    "    c = pow(max(c, 0.0), vec3(inv_gamma));\n"
    "    frag_color = vec4(c, col.a);\n"
    "}\n";

static const char* glsl_vignette_fs =
    "#version 330\n"
    "uniform VignetteParams {\n"
    "    float vignette;\n"
    "    float chromatic;\n"
    "    float grain;\n"
    "    float time;\n"
    "};\n"
    "uniform sampler2D scene_tex;\n"
    "in vec2 v_uv;\n"
    "out vec4 frag_color;\n"
    "float rand(vec2 co) {\n"
    "    return fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453);\n"
    "}\n"
    "void main() {\n"
    "    vec2 to_center = v_uv - vec2(0.5);\n"
    "    float dist = length(to_center);\n"
    "    vec2 r_uv = v_uv - to_center * chromatic;\n"
    "    vec2 b_uv = v_uv + to_center * chromatic;\n"
    "    float r = texture(scene_tex, r_uv).r;\n"
    "    float g = texture(scene_tex, v_uv).g;\n"
    "    float b = texture(scene_tex, b_uv).b;\n"
    "    float a = texture(scene_tex, v_uv).a;\n"
    "    vec3 col = vec3(r, g, b);\n"
    "    float vig = smoothstep(0.8, 0.8 - vignette, dist * 1.414);\n"
    "    col *= vig;\n"
    "    float noise = (rand(v_uv + vec2(time, time * 0.5)) - 0.5) * grain;\n"
    "    col += noise;\n"
    "    frag_color = vec4(clamp(col, 0.0, 1.0), a);\n"
    "}\n";

static const char* glsl_colorgrade_fs =
    "#version 330\n"
    "uniform ColorGradingParams {\n"
    "    float contrast;\n"
    "    float saturation;\n"
    "    float brightness;\n"
    "    float pad;\n"
    "};\n"
    "uniform sampler2D scene_tex;\n"
    "in vec2 v_uv;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    vec4 col = texture(scene_tex, v_uv);\n"
    "    vec3 c = col.rgb * brightness;\n"
    "    c = (c - 0.5) * contrast + 0.5;\n"
    "    float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));\n"
    "    c = mix(vec3(lum), c, saturation);\n"
    "    frag_color = vec4(clamp(c, 0.0, 1.0), col.a);\n"
    "}\n";

static const char* glsl_blit_fs =
    "#version 330\n"
    "uniform sampler2D tex;\n"
    "in vec2 v_uv;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    frag_color = texture(tex, v_uv);\n"
    "}\n";
#endif

// Helper to configure fullscreen pass pipeline
static sg_pipeline create_quad_pipeline(sg_shader shd, sg_pixel_format target_fmt, int sample_count = 1) {
    sg_pipeline_desc pip_desc{};
    pip_desc.layout.buffers[0].stride = sizeof(QuadVertex);
    pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[0].offset = offsetof(QuadVertex, x);
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[1].offset = offsetof(QuadVertex, u);
    pip_desc.shader = shd;
    pip_desc.index_type = SG_INDEXTYPE_UINT16;
    pip_desc.depth.compare = SG_COMPAREFUNC_ALWAYS;
    pip_desc.depth.write_enabled = false;
    pip_desc.cull_mode = SG_CULLMODE_NONE;
    pip_desc.colors[0].pixel_format = target_fmt;
    pip_desc.sample_count = sample_count;
    pip_desc.label = "post-process-quad-pipeline";
    return sg_make_pipeline(&pip_desc);
}

// ---------------------------------------------------------------------------
// BloomPass
// ---------------------------------------------------------------------------
struct alignas(16) BloomUniforms {
    float threshold;
    float strength;
    float radius;
    float pad;
};

BloomPass::BloomPass(float thresh, float str, float rad)
    : threshold(thresh), strength(str), radius(rad) {
    init_pipeline();
}

BloomPass::~BloomPass() {
    if (pip_id_ != 0) {
        if (sg_isvalid()) sg_destroy_pipeline(sg_pipeline{ pip_id_ });
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        if (sg_isvalid()) sg_destroy_shader(sg_shader{ shd_id_ });
        shd_id_ = 0;
    }
}

void BloomPass::init_pipeline() {
    if (!sg_isvalid()) return;

    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_quad_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_bloom_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[1].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[0].size = sizeof(BloomUniforms);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;
#else
    shd_desc.vertex_func.source = glsl_quad_vs;
    shd_desc.fragment_func.source = glsl_bloom_fs;
#endif
    shd_desc.label = "bloom-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    sg_pipeline pip = create_quad_pipeline(shd, SG_PIXELFORMAT_RGBA16F);
    pip_id_ = pip.id;
}

void BloomPass::render(RenderTarget& input, RenderTarget& /*depth_source*/, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) {
    if (pip_id_ == 0 || shd_id_ == 0) init_pipeline();
    if (pip_id_ == 0) return;

    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_DONTCARE;
    pass.action.depth.load_action = SG_LOADACTION_DONTCARE;
    pass.attachments.colors[0] = sg_view{ output.color_view_id() };
    pass.label = "bloom-pass";

    sg_begin_pass(&pass);
    sg_apply_pipeline(sg_pipeline{ pip_id_ });

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ quad_vbuf };
    bind.index_buffer = sg_buffer{ quad_ibuf };
    bind.views[0] = sg_view{ input.tex_view_id() };
    bind.samplers[0] = sg_sampler{ input.sampler_id() };
    sg_apply_bindings(&bind);

    BloomUniforms ubo{ threshold, strength, radius, 0.0f };
    sg_apply_uniforms(0, SG_RANGE_REF(ubo));

    sg_draw(0, 6, 1);
    sg_end_pass();
}

// ---------------------------------------------------------------------------
// SSAOPass
// ---------------------------------------------------------------------------
struct alignas(16) SSAOUniforms {
    float radius;
    float bias;
    float power;
    float pad;
};

SSAOPass::SSAOPass(float rad, float bi, float pow)
    : radius(rad), bias(bi), power(pow) {
    init_pipeline();
}

SSAOPass::~SSAOPass() {
    if (pip_id_ != 0) {
        if (sg_isvalid()) sg_destroy_pipeline(sg_pipeline{ pip_id_ });
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        if (sg_isvalid()) sg_destroy_shader(sg_shader{ shd_id_ });
        shd_id_ = 0;
    }
}

void SSAOPass::init_pipeline() {
    if (!sg_isvalid()) return;

    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_quad_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_ssao_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[1].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[0].size = sizeof(SSAOUniforms);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;

    shd_desc.views[1].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[1].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[1].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[1].texture.hlsl_register_t_n = 1;

    shd_desc.samplers[1].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[1].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[1].hlsl_register_s_n = 1;
#else
    shd_desc.vertex_func.source = glsl_quad_vs;
    shd_desc.fragment_func.source = glsl_ssao_fs;
#endif
    shd_desc.label = "ssao-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    sg_pipeline pip = create_quad_pipeline(shd, SG_PIXELFORMAT_RGBA16F);
    pip_id_ = pip.id;
}

void SSAOPass::render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) {
    if (pip_id_ == 0 || shd_id_ == 0) init_pipeline();
    if (pip_id_ == 0) return;

    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_DONTCARE;
    pass.action.depth.load_action = SG_LOADACTION_DONTCARE;
    pass.attachments.colors[0] = sg_view{ output.color_view_id() };
    pass.label = "ssao-pass";

    sg_begin_pass(&pass);
    sg_apply_pipeline(sg_pipeline{ pip_id_ });

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ quad_vbuf };
    bind.index_buffer = sg_buffer{ quad_ibuf };
    bind.views[0] = sg_view{ input.tex_view_id() };
    bind.samplers[0] = sg_sampler{ input.sampler_id() };

    uint32_t d_view = depth_source.depth_tex_view_id() ? depth_source.depth_tex_view_id() : input.tex_view_id();
    bind.views[1] = sg_view{ d_view };
    bind.samplers[1] = sg_sampler{ input.sampler_id() };
    sg_apply_bindings(&bind);

    SSAOUniforms ubo{ radius, bias, power, 0.0f };
    sg_apply_uniforms(0, SG_RANGE_REF(ubo));

    sg_draw(0, 6, 1);
    sg_end_pass();
}

// ---------------------------------------------------------------------------
// FXAAPass
// ---------------------------------------------------------------------------
struct alignas(16) FXAAUniforms {
    glm::vec2 texel_size;
    glm::vec2 pad;
};

FXAAPass::FXAAPass() {
    init_pipeline();
}

FXAAPass::~FXAAPass() {
    if (pip_id_ != 0) {
        if (sg_isvalid()) sg_destroy_pipeline(sg_pipeline{ pip_id_ });
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        if (sg_isvalid()) sg_destroy_shader(sg_shader{ shd_id_ });
        shd_id_ = 0;
    }
}

void FXAAPass::init_pipeline() {
    if (!sg_isvalid()) return;

    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_quad_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_fxaa_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[1].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[0].size = sizeof(FXAAUniforms);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;
#else
    shd_desc.vertex_func.source = glsl_quad_vs;
    shd_desc.fragment_func.source = glsl_fxaa_fs;
#endif
    shd_desc.label = "fxaa-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    sg_pipeline pip = create_quad_pipeline(shd, SG_PIXELFORMAT_RGBA16F);
    pip_id_ = pip.id;
}

void FXAAPass::render(RenderTarget& input, RenderTarget& /*depth_source*/, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) {
    if (pip_id_ == 0 || shd_id_ == 0) init_pipeline();
    if (pip_id_ == 0) return;

    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_DONTCARE;
    pass.action.depth.load_action = SG_LOADACTION_DONTCARE;
    pass.attachments.colors[0] = sg_view{ output.color_view_id() };
    pass.label = "fxaa-pass";

    sg_begin_pass(&pass);
    sg_apply_pipeline(sg_pipeline{ pip_id_ });

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ quad_vbuf };
    bind.index_buffer = sg_buffer{ quad_ibuf };
    bind.views[0] = sg_view{ input.tex_view_id() };
    bind.samplers[0] = sg_sampler{ input.sampler_id() };
    sg_apply_bindings(&bind);

    float w = static_cast<float>(input.width());
    float h = static_cast<float>(input.height());
    FXAAUniforms ubo{ glm::vec2(1.0f / (w > 0.0f ? w : 800.0f), 1.0f / (h > 0.0f ? h : 600.0f)), glm::vec2(0.0f) };
    sg_apply_uniforms(0, SG_RANGE_REF(ubo));

    sg_draw(0, 6, 1);
    sg_end_pass();
}

// ---------------------------------------------------------------------------
// TonemappingPass
// ---------------------------------------------------------------------------
struct alignas(16) TonemapUniforms {
    float exposure;
    float gamma;
    int mode;
    float pad;
};

TonemappingPass::TonemappingPass(TonemappingMode m, float exp, float gam)
    : mode(m), exposure(exp), gamma(gam) {
    init_pipeline();
}

TonemappingPass::~TonemappingPass() {
    if (pip_id_ != 0) {
        if (sg_isvalid()) sg_destroy_pipeline(sg_pipeline{ pip_id_ });
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        if (sg_isvalid()) sg_destroy_shader(sg_shader{ shd_id_ });
        shd_id_ = 0;
    }
}

void TonemappingPass::init_pipeline() {
    if (!sg_isvalid()) return;

    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_quad_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_tonemap_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[1].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[0].size = sizeof(TonemapUniforms);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;
#else
    shd_desc.vertex_func.source = glsl_quad_vs;
    shd_desc.fragment_func.source = glsl_tonemap_fs;
#endif
    shd_desc.label = "tonemap-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    sg_pipeline pip = create_quad_pipeline(shd, SG_PIXELFORMAT_RGBA16F);
    pip_id_ = pip.id;
}

void TonemappingPass::render(RenderTarget& input, RenderTarget& /*depth_source*/, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) {
    if (pip_id_ == 0 || shd_id_ == 0) init_pipeline();
    if (pip_id_ == 0) return;

    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_DONTCARE;
    pass.action.depth.load_action = SG_LOADACTION_DONTCARE;
    pass.attachments.colors[0] = sg_view{ output.color_view_id() };
    pass.label = "tonemap-pass";

    sg_begin_pass(&pass);
    sg_apply_pipeline(sg_pipeline{ pip_id_ });

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ quad_vbuf };
    bind.index_buffer = sg_buffer{ quad_ibuf };
    bind.views[0] = sg_view{ input.tex_view_id() };
    bind.samplers[0] = sg_sampler{ input.sampler_id() };
    sg_apply_bindings(&bind);

    TonemapUniforms ubo{ exposure, gamma, static_cast<int>(mode), 0.0f };
    sg_apply_uniforms(0, SG_RANGE_REF(ubo));

    sg_draw(0, 6, 1);
    sg_end_pass();
}

// ---------------------------------------------------------------------------
// VignetteChromaticPass
// ---------------------------------------------------------------------------
struct alignas(16) VignetteUniforms {
    float vignette;
    float chromatic;
    float grain;
    float time;
};

VignetteChromaticPass::VignetteChromaticPass(float vig, float chrom, float gr)
    : vignette(vig), chromatic(chrom), grain(gr) {
    init_pipeline();
}

VignetteChromaticPass::~VignetteChromaticPass() {
    if (pip_id_ != 0) {
        if (sg_isvalid()) sg_destroy_pipeline(sg_pipeline{ pip_id_ });
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        if (sg_isvalid()) sg_destroy_shader(sg_shader{ shd_id_ });
        shd_id_ = 0;
    }
}

void VignetteChromaticPass::init_pipeline() {
    if (!sg_isvalid()) return;

    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_quad_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_vignette_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[1].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[0].size = sizeof(VignetteUniforms);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;
#else
    shd_desc.vertex_func.source = glsl_quad_vs;
    shd_desc.fragment_func.source = glsl_vignette_fs;
#endif
    shd_desc.label = "vignette-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    sg_pipeline pip = create_quad_pipeline(shd, SG_PIXELFORMAT_RGBA16F);
    pip_id_ = pip.id;
}

void VignetteChromaticPass::render(RenderTarget& input, RenderTarget& /*depth_source*/, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) {
    if (pip_id_ == 0 || shd_id_ == 0) init_pipeline();
    if (pip_id_ == 0) return;

    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_DONTCARE;
    pass.action.depth.load_action = SG_LOADACTION_DONTCARE;
    pass.attachments.colors[0] = sg_view{ output.color_view_id() };
    pass.label = "vignette-pass";

    sg_begin_pass(&pass);
    sg_apply_pipeline(sg_pipeline{ pip_id_ });

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ quad_vbuf };
    bind.index_buffer = sg_buffer{ quad_ibuf };
    bind.views[0] = sg_view{ input.tex_view_id() };
    bind.samplers[0] = sg_sampler{ input.sampler_id() };
    sg_apply_bindings(&bind);

    time += 0.0166f;
    VignetteUniforms ubo{ vignette, chromatic, grain, time };
    sg_apply_uniforms(0, SG_RANGE_REF(ubo));

    sg_draw(0, 6, 1);
    sg_end_pass();
}

// ---------------------------------------------------------------------------
// ColorGradingPass
// ---------------------------------------------------------------------------
struct alignas(16) ColorGradingUniforms {
    float contrast;
    float saturation;
    float brightness;
    float pad;
};

ColorGradingPass::ColorGradingPass(float cont, float sat, float bright)
    : contrast(cont), saturation(sat), brightness(bright) {
    init_pipeline();
}

ColorGradingPass::~ColorGradingPass() {
    if (pip_id_ != 0) {
        if (sg_isvalid()) sg_destroy_pipeline(sg_pipeline{ pip_id_ });
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        if (sg_isvalid()) sg_destroy_shader(sg_shader{ shd_id_ });
        shd_id_ = 0;
    }
}

void ColorGradingPass::init_pipeline() {
    if (!sg_isvalid()) return;

    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_quad_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_colorgrade_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[1].hlsl_sem_index = 0;

    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.uniform_blocks[0].size = sizeof(ColorGradingUniforms);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;
#else
    shd_desc.vertex_func.source = glsl_quad_vs;
    shd_desc.fragment_func.source = glsl_colorgrade_fs;
#endif
    shd_desc.label = "colorgrade-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    sg_pipeline pip = create_quad_pipeline(shd, SG_PIXELFORMAT_RGBA16F);
    pip_id_ = pip.id;
}

void ColorGradingPass::render(RenderTarget& input, RenderTarget& /*depth_source*/, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) {
    if (pip_id_ == 0 || shd_id_ == 0) init_pipeline();
    if (pip_id_ == 0) return;

    sg_pass pass{};
    pass.action.colors[0].load_action = SG_LOADACTION_DONTCARE;
    pass.action.depth.load_action = SG_LOADACTION_DONTCARE;
    pass.attachments.colors[0] = sg_view{ output.color_view_id() };
    pass.label = "colorgrade-pass";

    sg_begin_pass(&pass);
    sg_apply_pipeline(sg_pipeline{ pip_id_ });

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ quad_vbuf };
    bind.index_buffer = sg_buffer{ quad_ibuf };
    bind.views[0] = sg_view{ input.tex_view_id() };
    bind.samplers[0] = sg_sampler{ input.sampler_id() };
    sg_apply_bindings(&bind);

    ColorGradingUniforms ubo{ contrast, saturation, brightness, 0.0f };
    sg_apply_uniforms(0, SG_RANGE_REF(ubo));

    sg_draw(0, 6, 1);
    sg_end_pass();
}

// ---------------------------------------------------------------------------
// EffectComposer
// ---------------------------------------------------------------------------
EffectComposer::EffectComposer(int width, int height)
    : width_(width), height_(height) {
    init_resources();
}

EffectComposer::EffectComposer(EngineApp& app)
    : width_(app.width()), height_(app.height()), app_(&app) {
    init_resources();
}

EffectComposer::~EffectComposer() {
    destroy();
}

void EffectComposer::init_resources() {
    if (!sg_isvalid()) return;

    // 1. Create Quad vertex and index buffers
    if (quad_vbuf_id_ == 0) {
        sg_buffer_desc vbuf_desc{};
        vbuf_desc.data = SG_RANGE(QUAD_VERTS);
        vbuf_desc.usage.vertex_buffer = true;
        vbuf_desc.label = "effectcomposer-quad-vbuf";
        sg_buffer vbuf = sg_make_buffer(&vbuf_desc);
        quad_vbuf_id_ = vbuf.id;
    }
    if (quad_ibuf_id_ == 0) {
        sg_buffer_desc ibuf_desc{};
        ibuf_desc.data = SG_RANGE(QUAD_INDICES);
        ibuf_desc.usage.index_buffer = true;
        ibuf_desc.label = "effectcomposer-quad-ibuf";
        sg_buffer ibuf = sg_make_buffer(&ibuf_desc);
        quad_ibuf_id_ = ibuf.id;
    }

    // 2. Create HDR RenderTarget (RGBA16F with depth)
    hdr_target_ = std::make_unique<RenderTarget>(width_, height_, RenderTargetFormat::RGBA16F, true);

    // 3. Create Ping-Pong RenderTargets (RGBA16F without depth)
    ping_pong_[0] = std::make_unique<RenderTarget>(width_, height_, RenderTargetFormat::RGBA16F, false);
    ping_pong_[1] = std::make_unique<RenderTarget>(width_, height_, RenderTargetFormat::RGBA16F, false);

    final_target_ = hdr_target_.get();

    // 4. Init Swapchain Blit Pipeline
    init_blit_pipeline();
}

void EffectComposer::init_blit_pipeline() {
    if (!sg_isvalid()) return;

    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_quad_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_blit_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";

    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "TEXCOORD";
    shd_desc.attrs[1].hlsl_sem_index = 0;

    shd_desc.views[0].texture.stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.views[0].texture.image_type = SG_IMAGETYPE_2D;
    shd_desc.views[0].texture.sample_type = SG_IMAGESAMPLETYPE_FLOAT;
    shd_desc.views[0].texture.hlsl_register_t_n = 0;

    shd_desc.samplers[0].stage = SG_SHADERSTAGE_FRAGMENT;
    shd_desc.samplers[0].sampler_type = SG_SAMPLERTYPE_FILTERING;
    shd_desc.samplers[0].hlsl_register_s_n = 0;
#else
    shd_desc.vertex_func.source = glsl_quad_vs;
    shd_desc.fragment_func.source = glsl_blit_fs;
#endif
    shd_desc.label = "blit-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    blit_shd_id_ = shd.id;

    sg_pipeline_desc pip_desc{};
    pip_desc.layout.buffers[0].stride = sizeof(QuadVertex);
    pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[0].offset = offsetof(QuadVertex, x);
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT2;
    pip_desc.layout.attrs[1].offset = offsetof(QuadVertex, u);
    pip_desc.shader = shd;
    pip_desc.index_type = SG_INDEXTYPE_UINT16;
    pip_desc.depth.compare = SG_COMPAREFUNC_ALWAYS;
    pip_desc.depth.write_enabled = false;
    pip_desc.cull_mode = SG_CULLMODE_NONE;
    pip_desc.colors[0].pixel_format = _SG_PIXELFORMAT_DEFAULT;
    pip_desc.sample_count = sapp_sample_count();
    pip_desc.label = "blit-swapchain-pipeline";
    sg_pipeline pip = sg_make_pipeline(&pip_desc);
    blit_pip_id_ = pip.id;
}

void EffectComposer::destroy() {
    if (blit_pip_id_ != 0) {
        if (sg_isvalid()) sg_destroy_pipeline(sg_pipeline{ blit_pip_id_ });
        blit_pip_id_ = 0;
    }
    if (blit_shd_id_ != 0) {
        if (sg_isvalid()) sg_destroy_shader(sg_shader{ blit_shd_id_ });
        blit_shd_id_ = 0;
    }
    if (quad_vbuf_id_ != 0) {
        if (sg_isvalid()) sg_destroy_buffer(sg_buffer{ quad_vbuf_id_ });
        quad_vbuf_id_ = 0;
    }
    if (quad_ibuf_id_ != 0) {
        if (sg_isvalid()) sg_destroy_buffer(sg_buffer{ quad_ibuf_id_ });
        quad_ibuf_id_ = 0;
    }

    hdr_target_.reset();
    ping_pong_[0].reset();
    ping_pong_[1].reset();
    final_target_ = nullptr;
}

void EffectComposer::resize(int width, int height) {
    if (width <= 0 || height <= 0) return;
    if (width == width_ && height == height_) return;

    width_ = width;
    height_ = height;

    if (hdr_target_) hdr_target_->resize(width_, height_);
    if (ping_pong_[0]) ping_pong_[0]->resize(width_, height_);
    if (ping_pong_[1]) ping_pong_[1]->resize(width_, height_);
}

void EffectComposer::add_pass(std::shared_ptr<PostProcessPass> pass) {
    if (pass) {
        passes_.push_back(pass);
    }
}

void EffectComposer::remove_pass(std::shared_ptr<PostProcessPass> pass) {
    auto it = std::remove(passes_.begin(), passes_.end(), pass);
    passes_.erase(it, passes_.end());
}

void EffectComposer::clear_passes() {
    passes_.clear();
}

void EffectComposer::render_passes(EngineApp& app, Scene& scene, Camera& camera) {
    if (!enabled) return;

    // 1. Ensure resources exist and match window size
    int w = app.width();
    int h = app.height();
    if (!hdr_target_ || width_ != w || height_ != h) {
        resize(w, h);
        if (!hdr_target_) init_resources();
    }
    if (!hdr_target_) return;

    // 2. Render Scene into HDR RenderTarget
    app.render_target(scene, camera, *hdr_target_);

    // 3. Collect active passes
    std::vector<std::shared_ptr<PostProcessPass>> active_passes;
    for (const auto& pass : passes_) {
        if (pass && pass->enabled) {
            active_passes.push_back(pass);
        }
    }

    if (active_passes.empty()) {
        final_target_ = hdr_target_.get();
        return;
    }

    // 4. Ping-Pong execution
    RenderTarget* current_read = hdr_target_.get();
    int write_idx = 0;

    for (size_t i = 0; i < active_passes.size(); ++i) {
        RenderTarget* current_write = ping_pong_[write_idx].get();
        active_passes[i]->render(*current_read, *hdr_target_, *current_write, quad_vbuf_id_, quad_ibuf_id_);
        current_read = current_write;
        write_idx = 1 - write_idx;
    }

    final_target_ = current_read;
}

void EffectComposer::blit_to_swapchain(RenderTarget& source) {
    if (blit_pip_id_ == 0 || blit_shd_id_ == 0) {
        init_blit_pipeline();
    }
    if (blit_pip_id_ == 0 || quad_vbuf_id_ == 0) return;

    sg_apply_pipeline(sg_pipeline{ blit_pip_id_ });

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{ quad_vbuf_id_ };
    bind.index_buffer = sg_buffer{ quad_ibuf_id_ };
    bind.views[0] = sg_view{ source.tex_view_id() };
    bind.samplers[0] = sg_sampler{ source.sampler_id() };
    sg_apply_bindings(&bind);

    sg_draw(0, 6, 1);
}

void EffectComposer::render(Scene& scene, Camera& camera) {
    if (!app_) return;

    render_passes(*app_, scene, camera);

    if (final_target_) {
        sg_pass pass{};
        pass.swapchain = sglue_swapchain();
        pass.action.colors[0].load_action = SG_LOADACTION_CLEAR;
        pass.action.colors[0].clear_value = { 0.0f, 0.0f, 0.0f, 1.0f };
        pass.action.depth.load_action = SG_LOADACTION_CLEAR;
        pass.action.depth.clear_value = 1.0f;
        sg_begin_pass(&pass);

        blit_to_swapchain(*final_target_);

        sg_end_pass();
    }
}

} // namespace engine
