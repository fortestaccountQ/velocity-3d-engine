#pragma once

#include <string>
#include <array>
#include <functional>
#include <chrono>
#include <memory>

#include <glm/glm.hpp>
#include "engine/math_types.hpp"
#include "engine/transform.hpp"
#include "engine/camera.hpp"
#include "engine/scene.hpp"
#include "engine/input.hpp"
#include "engine/audio.hpp"
#include "engine/editor.hpp"
#include "engine/cube_texture.hpp"
#include "engine/sky.hpp"
#include "contracts/phase4_environment_contracts.h"

namespace engine {

class RenderTarget;
class EffectComposer;
class CubeRenderTarget;
class CubeCamera;

// ---------------------------------------------------------------------------
// UI Command Contract for Phase 0.1
// ---------------------------------------------------------------------------
enum class UICommandType : uint8_t {
    Text = 0,
    Rect = 1,
    Line = 2,
    Crosshair = 3
};

struct UICommand {
    UICommandType type{UICommandType::Rect};
    std::string text{};
    glm::vec2 pos{0.0f, 0.0f};      // (x, y) position
    glm::vec2 size{0.0f, 0.0f};     // (w, h) or (size, scale)
    glm::vec4 color{1.0f, 1.0f, 1.0f, 1.0f};
    float thickness{1.0f};
};

struct WindowConfig {
    std::string title = "VelocityEngine v0.2-beta";
    int width = 800;
    int height = 600;
    // Daylight sky-blue #6ea0d0 (RGB [0.431, 0.627, 0.823])
    std::array<float, 4> clear_color = { 0.43137f, 0.62745f, 0.82353f, 1.0f };
    bool vsync = true;
};

class EngineApp {
public:
    using UpdateCallback = std::function<void(double)>;

    EngineApp();
    EngineApp(const std::string& title, int width, int height);
    virtual ~EngineApp();

    void init(const std::string& title, int width, int height);
    void run();
    void close();

    bool is_running() const { return running_; }

    // Clear color
    void set_clear_color(float r, float g, float b, float a = 1.0f);
    std::array<float, 4> get_clear_color() const { return config_.clear_color; }

    // Window dimensions & title
    int width() const { return config_.width; }
    int height() const { return config_.height; }
    const std::string& title() const { return config_.title; }
    void set_title(const std::string& title);

    // Subsystems
    Scene& scene() { return scene_; }
    Camera& camera() { return camera_; }
    InputManager& input() { return input_; }
    AudioManager& audio() { return audio_; }

    // Mouse lock & visibility
    void set_mouse_locked(bool locked);
    bool is_mouse_locked() const;

    // Editor and Engine Mode
    void set_mode(EngineMode mode);
    EngineMode get_mode() const { return mode_; }
    void toggle_mode() { set_mode(mode_ == EngineMode::GAME ? EngineMode::EDITOR : EngineMode::GAME); }
    EditorManager& editor() { return editor_; }

    // HUD and Debug options
    void set_show_hud(bool enable) { show_hud_ = enable; }
    bool show_hud() const { return show_hud_; }
    void set_show_crosshair(bool show) { show_crosshair_ = show; }
    bool show_crosshair() const { return show_crosshair_; }
    void set_hud_score(int score) { hud_score_ = score; }
    int hud_score() const { return hud_score_; }
    void set_hud_title(const std::string& title) { hud_title_ = title; }
    std::string hud_title() const { return hud_title_; }
    void set_hud_hint(const std::string& hint) { hud_hint_ = hint; }
    std::string hud_hint() const { return hud_hint_; }

    // Frame pacing / Target FPS limiter & VSync
    void set_target_fps(int fps) { target_fps_ = fps; }
    int target_fps() const { return target_fps_; }
    void set_vsync(bool enabled);
    bool vsync() const { return config_.vsync; }
    float fps() const { return current_fps_; }
    float frame_time_ms() const { return current_fps_ > 0.0f ? (1000.0f / current_fps_) : 0.0f; }

    void set_debug_hitboxes(bool enable) { show_debug_hitboxes_ = enable; }
    void toggle_debug_hitboxes() { show_debug_hitboxes_ = !show_debug_hitboxes_; }
    bool is_debug_hitboxes() const { return show_debug_hitboxes_; }

    // Render statistics
    const RenderStats& stats() const { return stats_; }
    RenderStats& stats() { return stats_; }
    void evaluate_frustum_culling();

    // Fog and Tone Mapping
    void set_linear_fog(const glm::vec3& color, float near_dist, float far_dist) {
        fog_enabled_ = true;
        fog_type_ = 1;
        fog_color_ = color;
        fog_near_ = near_dist;
        fog_far_ = far_dist;
    }

    void set_exp2_fog(const glm::vec3& color, float density) {
        fog_enabled_ = true;
        fog_type_ = 2;
        fog_color_ = color;
        fog_density_ = density;
    }

    void clear_fog() {
        fog_enabled_ = false;
        fog_type_ = 0;
    }

    bool fog_enabled() const { return fog_enabled_; }
    int fog_type() const { return fog_type_; }
    glm::vec3 fog_color() const { return fog_color_; }
    float fog_near() const { return fog_near_; }
    float fog_far() const { return fog_far_; }
    float fog_density() const { return fog_density_; }

    void set_tone_mapping(bool enable) { tone_mapping_enabled_ = enable; }
    bool tone_mapping_enabled() const { return tone_mapping_enabled_; }

    // RenderTarget and Post-Processing (EffectComposer)
    void render_target(Scene& scene, Camera& camera, RenderTarget& target);
    std::vector<uint8_t> read_pixels(RenderTarget& target);
    void set_composer(std::shared_ptr<EffectComposer> composer);
    std::shared_ptr<EffectComposer> composer() const { return composer_; }

    // Shadows v2 Configuration
    const ShadowSettings& shadow_settings() const { return shadow_settings_; }
    ShadowSettings& shadow_settings() { return shadow_settings_; }
    void set_shadow_settings(const ShadowSettings& settings);
    void set_shadow_resolution(int res);
    void set_shadow_bias(float b) { shadow_settings_.bias = b; }
    void set_shadow_normal_bias(float nb) { shadow_settings_.normal_bias = nb; }
    void set_shadow_ortho_size(float size) { shadow_settings_.ortho_size = size; }
    void set_shadow_pcf_16_tap(bool enable) { shadow_settings_.pcf_16_tap = enable; }
    void set_shadow_texel_snapping(bool enable) { shadow_settings_.texel_snapping = enable; }

    // CubeCamera rendering
    void render_cube_camera(Scene& scene, CubeCamera& cam);

    // Python frame update callback
    void set_update_callback(UpdateCallback callback);

    // Custom UI Commands
    void submit_ui_commands(const std::vector<UICommand>& cmds) {
        custom_ui_commands_.insert(custom_ui_commands_.end(), cmds.begin(), cmds.end());
    }
    void clear_ui_commands() {
        custom_ui_commands_.clear();
    }
    const std::vector<UICommand>& custom_ui_commands() const { return custom_ui_commands_; }

    // Internal Sokol callbacks
    void on_init();
    void on_frame();
    void on_cleanup();
    void on_event(const void* raw_event);

private:
    void init_pipeline_and_shaders();
    void init_shadow_pipeline();
    void init_sky_pipelines();
    void init_hud_and_line_pipelines();
    void render_shadow_pass();
    void render_background_pass(Scene& scene, Camera& camera, bool is_offscreen = false, uint32_t color_format = 0);
    void render_scene_pass(Scene& scene, Camera& camera, int target_w, int target_h, bool is_offscreen, uint32_t color_format = 0);
    void render_debug_hitboxes(const glm::mat4& vp);
    void render_hud(float screen_w, float screen_h, float fps);

    WindowConfig config_;
    bool running_{false};
    bool initialized_{false};

    Scene scene_;
    Camera camera_;
    InputManager input_;
    AudioManager audio_;
    EditorManager editor_{*this};
    EngineMode mode_{EngineMode::GAME};

    UpdateCallback update_callback_{nullptr};
    std::chrono::steady_clock::time_point last_frame_time_;
    bool has_last_frame_{false};
    float current_fps_{60.0f};

    // Sokol graphics pipeline & shader handles
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};

    // Instanced pipeline & shader handles
    uint32_t instanced_pip_id_{0};
    uint32_t instanced_shd_id_{0};
    uint32_t instanced_shadow_pip_id_{0};
    uint32_t instanced_shadow_shd_id_{0};

    // Custom UI commands queue
    std::vector<UICommand> custom_ui_commands_;

    // Shadow Mapping resources
    ShadowSettings shadow_settings_{};
    uint32_t shadow_color_img_id_{0};
    uint32_t shadow_depth_img_id_{0};
    uint32_t shadow_color_view_id_{0};
    uint32_t shadow_depth_view_id_{0};
    uint32_t shadow_tex_view_id_{0};
    uint32_t shadow_sampler_id_{0};
    uint32_t shadow_pip_id_{0};
    uint32_t shadow_shd_id_{0};
    glm::mat4 light_vp_{1.0f};

    // Skybox and Procedural Sky resources
    uint32_t skybox_pip_id_{0};
    uint32_t skybox_offscreen_pip_id_{0};
    uint32_t skybox_rgba8_pip_id_{0};
    uint32_t skybox_shd_id_{0};
    uint32_t proc_sky_pip_id_{0};
    uint32_t proc_sky_offscreen_pip_id_{0};
    uint32_t proc_sky_rgba8_pip_id_{0};
    uint32_t proc_sky_shd_id_{0};
    std::shared_ptr<Mesh> sky_cube_mesh_{nullptr};
    std::shared_ptr<CubeTexture> default_env_cube_{nullptr};

    // Line & HUD rendering
    uint32_t line_pip_id_{0};
    uint32_t line_shd_id_{0};
    uint32_t line_vbuf_id_{0};

    uint32_t hud_pip_id_{0};
    uint32_t hud_shd_id_{0};
    uint32_t hud_vbuf_id_{0};

    bool show_hud_{true};
    bool show_crosshair_{true};
    bool show_debug_hitboxes_{false};
    int hud_score_{0};
    std::string hud_title_{""};
    std::string hud_hint_{""};
    int target_fps_{0};

    // Fog and Tone Mapping settings
    bool fog_enabled_{false};
    int fog_type_{0}; // 0 = off, 1 = linear, 2 = exp2
    glm::vec3 fog_color_{0.8f, 0.8f, 0.85f};
    float fog_near_{1.0f};
    float fog_far_{100.0f};
    float fog_density_{0.01f};
    bool tone_mapping_enabled_{true};

    // Render statistics
    RenderStats stats_{};

    // Default textures for PBR bindings
    std::shared_ptr<Texture> default_flat_normal_tex_{nullptr};
    std::shared_ptr<Texture> default_white_tex_{nullptr};
    std::shared_ptr<Texture> default_black_tex_{nullptr};

    // EffectComposer post-processing
    std::shared_ptr<EffectComposer> composer_{nullptr};
};

} // namespace engine
