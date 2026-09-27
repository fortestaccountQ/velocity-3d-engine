#include "engine/app.hpp"

#include "sokol_app.h"
#include "sokol_gfx.h"
#include "sokol_glue.h"
#include "sokol_log.h"

#include <glm/gtc/matrix_transform.hpp>
#include <iostream>

namespace engine {

// ---------------------------------------------------------------------------
// Shaders for various platforms
// ---------------------------------------------------------------------------
#if defined(SOKOL_D3D11)
static const char* hlsl_vs =
    "cbuffer vs_params : register(b0) {\n"
    "    float4x4 mvp;\n"
    "};\n"
    "struct vs_in {\n"
    "    float3 pos : POSITION;\n"
    "    float4 color : COLOR0;\n"
    "};\n"
    "struct vs_out {\n"
    "    float4 color : COLOR0;\n"
    "    float4 pos : SV_Position;\n"
    "};\n"
    "vs_out main(vs_in inp) {\n"
    "    vs_out outp;\n"
    "    outp.pos = mul(mvp, float4(inp.pos, 1.0));\n"
    "    outp.color = inp.color;\n"
    "    return outp;\n"
    "}\n";

static const char* hlsl_fs =
    "float4 main(float4 color : COLOR0) : SV_Target0 {\n"
    "    return color;\n"
    "}\n";

#elif defined(SOKOL_METAL)
static const char* metal_src =
    "#include <metal_stdlib>\n"
    "using namespace metal;\n"
    "struct params_t {\n"
    "    float4x4 mvp;\n"
    "};\n"
    "struct vs_in {\n"
    "    float3 position [[attribute(0)]];\n"
    "    float4 color0 [[attribute(1)]];\n"
    "};\n"
    "struct vs_out {\n"
    "    float4 pos [[position]];\n"
    "    float4 color;\n"
    "};\n"
    "vertex vs_out vs_main(vs_in in [[stage_in]], constant params_t& params [[buffer(0)]]) {\n"
    "    vs_out out;\n"
    "    out.pos = params.mvp * float4(in.position, 1.0);\n"
    "    out.color = in.color0;\n"
    "    return out;\n"
    "}\n"
    "fragment float4 fs_main(vs_out in [[stage_in]]) {\n"
    "    return in.color;\n"
    "}\n";

#elif defined(SOKOL_GLES3)
static const char* glsl_vs =
    "#version 300 es\n"
    "layout(location=0) in vec3 position;\n"
    "layout(location=1) in vec4 color0;\n"
    "uniform mat4 mvp;\n"
    "out vec4 color;\n"
    "void main() {\n"
    "    gl_Position = mvp * vec4(position, 1.0);\n"
    "    color = color0;\n"
    "}\n";

static const char* glsl_fs =
    "#version 300 es\n"
    "precision mediump float;\n"
    "in vec4 color;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    frag_color = color;\n"
    "}\n";

#else // Desktop GLCORE
static const char* glsl_vs =
    "#version 330\n"
    "layout(location=0) in vec3 position;\n"
    "layout(location=1) in vec4 color0;\n"
    "uniform mat4 mvp;\n"
    "out vec4 color;\n"
    "void main() {\n"
    "    gl_Position = mvp * vec4(position, 1.0);\n"
    "    color = color0;\n"
    "}\n";

static const char* glsl_fs =
    "#version 330\n"
    "in vec4 color;\n"
    "out vec4 frag_color;\n"
    "void main() {\n"
    "    frag_color = color;\n"
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

void EngineApp::set_rotation(float rx, float ry, float rz) {
    rotation_ = glm::vec3(rx, ry, rz);
}

void EngineApp::set_position(float x, float y, float z) {
    position_ = glm::vec3(x, y, z);
}

void EngineApp::set_scale(float sx, float sy, float sz) {
    scale_ = glm::vec3(sx, sy, sz);
}

void EngineApp::init_mesh_and_pipeline() {
    // 24 vertices for 6 faces with distinct colors
    const Vertex vertices[24] = {
        // Back face (Z = -1, red)
        { -1.0f, -1.0f, -1.0f,   1.0f, 0.25f, 0.25f, 1.0f },
        {  1.0f, -1.0f, -1.0f,   1.0f, 0.25f, 0.25f, 1.0f },
        {  1.0f,  1.0f, -1.0f,   1.0f, 0.25f, 0.25f, 1.0f },
        { -1.0f,  1.0f, -1.0f,   1.0f, 0.25f, 0.25f, 1.0f },

        // Front face (Z = +1, green)
        { -1.0f, -1.0f,  1.0f,   0.25f, 1.0f, 0.25f, 1.0f },
        {  1.0f, -1.0f,  1.0f,   0.25f, 1.0f, 0.25f, 1.0f },
        {  1.0f,  1.0f,  1.0f,   0.25f, 1.0f, 0.25f, 1.0f },
        { -1.0f,  1.0f,  1.0f,   0.25f, 1.0f, 0.25f, 1.0f },

        // Left face (X = -1, blue)
        { -1.0f, -1.0f, -1.0f,   0.25f, 0.45f, 1.0f, 1.0f },
        { -1.0f,  1.0f, -1.0f,   0.25f, 0.45f, 1.0f, 1.0f },
        { -1.0f,  1.0f,  1.0f,   0.25f, 0.45f, 1.0f, 1.0f },
        { -1.0f, -1.0f,  1.0f,   0.25f, 0.45f, 1.0f, 1.0f },

        // Right face (X = +1, yellow)
        {  1.0f, -1.0f, -1.0f,   1.0f, 0.9f, 0.2f, 1.0f },
        {  1.0f,  1.0f, -1.0f,   1.0f, 0.9f, 0.2f, 1.0f },
        {  1.0f,  1.0f,  1.0f,   1.0f, 0.9f, 0.2f, 1.0f },
        {  1.0f, -1.0f,  1.0f,   1.0f, 0.9f, 0.2f, 1.0f },

        // Bottom face (Y = -1, magenta)
        { -1.0f, -1.0f, -1.0f,   0.9f, 0.2f, 0.9f, 1.0f },
        { -1.0f, -1.0f,  1.0f,   0.9f, 0.2f, 0.9f, 1.0f },
        {  1.0f, -1.0f,  1.0f,   0.9f, 0.2f, 0.9f, 1.0f },
        {  1.0f, -1.0f, -1.0f,   0.9f, 0.2f, 0.9f, 1.0f },

        // Top face (Y = +1, cyan)
        { -1.0f,  1.0f, -1.0f,   0.2f, 0.9f, 0.9f, 1.0f },
        { -1.0f,  1.0f,  1.0f,   0.2f, 0.9f, 0.9f, 1.0f },
        {  1.0f,  1.0f,  1.0f,   0.2f, 0.9f, 0.9f, 1.0f },
        {  1.0f,  1.0f, -1.0f,   0.2f, 0.9f, 0.9f, 1.0f },
    };

    // 36 indices (6 indices per face)
    const uint16_t indices[36] = {
        0,  1,  2,    0,  2,  3,
        6,  5,  4,    7,  6,  4,
        8,  9, 10,    8, 10, 11,
       14, 13, 12,   15, 14, 12,
       16, 17, 18,   16, 18, 19,
       22, 21, 20,   23, 22, 20
    };

    // 1. Vertex buffer
    sg_buffer_desc vbuf_desc{};
    vbuf_desc.usage.vertex_buffer = true;
    vbuf_desc.data = SG_RANGE(vertices);
    vbuf_desc.label = "cube-vertices";
    sg_buffer vbuf = sg_make_buffer(&vbuf_desc);
    vbuf_id_ = vbuf.id;

    // 2. Index buffer
    sg_buffer_desc ibuf_desc{};
    ibuf_desc.usage.index_buffer = true;
    ibuf_desc.data = SG_RANGE(indices);
    ibuf_desc.label = "cube-indices";
    sg_buffer ibuf = sg_make_buffer(&ibuf_desc);
    ibuf_id_ = ibuf.id;

    // 3. Shader creation
    sg_shader_desc shd_desc{};
#if defined(SOKOL_D3D11)
    shd_desc.vertex_func.source = hlsl_vs;
    shd_desc.vertex_func.entry = "main";
    shd_desc.vertex_func.d3d11_target = "vs_4_0";
    shd_desc.fragment_func.source = hlsl_fs;
    shd_desc.fragment_func.entry = "main";
    shd_desc.fragment_func.d3d11_target = "ps_4_0";
    shd_desc.attrs[0].hlsl_sem_name = "POSITION";
    shd_desc.attrs[1].hlsl_sem_name = "COLOR";
    shd_desc.attrs[1].hlsl_sem_index = 0;
    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(glm::mat4);
    shd_desc.uniform_blocks[0].hlsl_register_b_n = 0;
#elif defined(SOKOL_METAL)
    shd_desc.vertex_func.source = metal_src;
    shd_desc.vertex_func.entry = "vs_main";
    shd_desc.fragment_func.source = metal_src;
    shd_desc.fragment_func.entry = "fs_main";
    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(glm::mat4);
    shd_desc.uniform_blocks[0].msl_buffer_n = 0;
#else
    shd_desc.vertex_func.source = glsl_vs;
    shd_desc.fragment_func.source = glsl_fs;
    shd_desc.attrs[0].glsl_name = "position";
    shd_desc.attrs[1].glsl_name = "color0";
    shd_desc.uniform_blocks[0].stage = SG_SHADERSTAGE_VERTEX;
    shd_desc.uniform_blocks[0].size = sizeof(glm::mat4);
    shd_desc.uniform_blocks[0].glsl_uniforms[0].type = SG_UNIFORMTYPE_MAT4;
    shd_desc.uniform_blocks[0].glsl_uniforms[0].array_count = 1;
    shd_desc.uniform_blocks[0].glsl_uniforms[0].glsl_name = "mvp";
#endif
    shd_desc.label = "cube-shader";
    sg_shader shd = sg_make_shader(&shd_desc);
    shd_id_ = shd.id;

    // 4. Pipeline with depth test
    sg_pipeline_desc pip_desc{};
    pip_desc.layout.buffers[0].stride = sizeof(Vertex);
    pip_desc.layout.attrs[0].format = SG_VERTEXFORMAT_FLOAT3;
    pip_desc.layout.attrs[1].format = SG_VERTEXFORMAT_FLOAT4;
    pip_desc.shader = shd;
    pip_desc.index_type = SG_INDEXTYPE_UINT16;
    pip_desc.depth.compare = SG_COMPAREFUNC_LESS_EQUAL;
    pip_desc.depth.write_enabled = true;
    pip_desc.cull_mode = SG_CULLMODE_NONE;
    pip_desc.label = "cube-pipeline";
    sg_pipeline pip = sg_make_pipeline(&pip_desc);
    pip_id_ = pip.id;
}

void EngineApp::on_init() {
    sg_desc desc{};
    desc.environment = sglue_environment();
    desc.logger.func = slog_func;
    sg_setup(&desc);

    init_mesh_and_pipeline();
}

void EngineApp::on_frame() {
    // 1. Calculate delta time (dt)
    auto now = std::chrono::steady_clock::now();
    double dt = 0.0;
    if (has_last_frame_) {
        dt = std::chrono::duration<double>(now - last_frame_time_).count();
        if (dt > 0.1) dt = 0.1; // clamp during stalls
    } else {
        has_last_frame_ = true;
        dt = 1.0 / 60.0;
    }
    last_frame_time_ = now;

    // 2. Safely invoke Python update callback with GIL
    if (update_callback_) {
        try {
            update_callback_(dt);
        } catch (const std::exception& e) {
            std::cerr << "[Engine] Exception in Python update callback: " << e.what() << "\n";
        }
    }

    // 3. Compute 3D MVP Matrix (GLM)
    float w = sapp_widthf();
    float h = sapp_heightf();
    float aspect = (h > 0.0f) ? (w / h) : 1.333333f;

    glm::mat4 proj = glm::perspective(glm::radians(55.0f), aspect, 0.1f, 100.0f);
    glm::mat4 view = glm::lookAt(
        camera_pos_,
        camera_target_,
        camera_up_
    );

    glm::mat4 model = glm::mat4(1.0f);
    model = glm::translate(model, position_);
    model = glm::rotate(model, glm::radians(rotation_.x), glm::vec3(1.0f, 0.0f, 0.0f));
    model = glm::rotate(model, glm::radians(rotation_.y), glm::vec3(0.0f, 1.0f, 0.0f));
    model = glm::rotate(model, glm::radians(rotation_.z), glm::vec3(0.0f, 0.0f, 1.0f));
    model = glm::scale(model, scale_);

    glm::mat4 mvp = proj * view * model;

    // 4. Begin render pass with color clear AND depth clear
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

    // 5. Apply pipeline, bindings, uniforms and draw cube
    sg_pipeline pip{pip_id_};
    sg_apply_pipeline(pip);

    sg_bindings bind{};
    bind.vertex_buffers[0] = sg_buffer{vbuf_id_};
    bind.index_buffer = sg_buffer{ibuf_id_};
    sg_apply_bindings(&bind);

    sg_apply_uniforms(0, SG_RANGE_REF(mvp));
    sg_draw(0, 36, 1);

    sg_end_pass();
    sg_commit();
}

void EngineApp::on_cleanup() {
    // Release Python callback to break cyclic references
    update_callback_ = nullptr;

    if (pip_id_ != 0) {
        sg_destroy_pipeline(sg_pipeline{pip_id_});
        pip_id_ = 0;
    }
    if (shd_id_ != 0) {
        sg_destroy_shader(sg_shader{shd_id_});
        shd_id_ = 0;
    }
    if (vbuf_id_ != 0) {
        sg_destroy_buffer(sg_buffer{vbuf_id_});
        vbuf_id_ = 0;
    }
    if (ibuf_id_ != 0) {
        sg_destroy_buffer(sg_buffer{ibuf_id_});
        ibuf_id_ = 0;
    }

    sg_shutdown();
}

void EngineApp::on_event(const void* raw_event) {
    if (!raw_event) return;
    const auto* ev = static_cast<const sapp_event*>(raw_event);

    if (ev->type == SAPP_EVENTTYPE_KEY_DOWN) {
        if (ev->key_code == SAPP_KEYCODE_ESCAPE) {
            sapp_request_quit();
        }
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
