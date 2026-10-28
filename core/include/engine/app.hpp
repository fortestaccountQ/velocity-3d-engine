#pragma once

#include <string>
#include <array>
#include <functional>
#include <chrono>
#include <memory>

#include <glm/glm.hpp>
#include "engine/transform.hpp"
#include "engine/camera.hpp"
#include "engine/scene.hpp"
#include "engine/input.hpp"
#include "engine/audio.hpp"
#include "engine/editor.hpp"

namespace engine {

struct WindowConfig {
    std::string title = "VelocityEngine v0.2-beta";
    int width = 800;
    int height = 600;
    // Daylight sky-blue #6ea0d0 (RGB [0.431, 0.627, 0.823])
    std::array<float, 4> clear_color = { 0.43137f, 0.62745f, 0.82353f, 1.0f };
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

    // Frame pacing / Target FPS limiter
    void set_target_fps(int fps) { target_fps_ = fps; }
    int target_fps() const { return target_fps_; }

    void set_debug_hitboxes(bool enable) { show_debug_hitboxes_ = enable; }
    void toggle_debug_hitboxes() { show_debug_hitboxes_ = !show_debug_hitboxes_; }
    bool is_debug_hitboxes() const { return show_debug_hitboxes_; }

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

    // Python frame update callback
    void set_update_callback(UpdateCallback callback);

    // Internal Sokol callbacks
    void on_init();
    void on_frame();
    void on_cleanup();
    void on_event(const void* raw_event);

private:
    void init_pipeline_and_shaders();
    void init_shadow_pipeline();
    void init_hud_and_line_pipelines();
    void render_shadow_pass();
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

    // Shadow Mapping resources
    static constexpr int SHADOW_MAP_SIZE = 2048;
    uint32_t shadow_color_img_id_{0};
    uint32_t shadow_depth_img_id_{0};
    uint32_t shadow_color_view_id_{0};
    uint32_t shadow_depth_view_id_{0};
    uint32_t shadow_tex_view_id_{0};
    uint32_t shadow_sampler_id_{0};
    uint32_t shadow_pip_id_{0};
    uint32_t shadow_shd_id_{0};
    glm::mat4 light_vp_{1.0f};

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
    int target_fps_{60};

    // Fog and Tone Mapping settings
    bool fog_enabled_{false};
    int fog_type_{0}; // 0 = off, 1 = linear, 2 = exp2
    glm::vec3 fog_color_{0.8f, 0.8f, 0.85f};
    float fog_near_{1.0f};
    float fog_far_{100.0f};
    float fog_density_{0.01f};
    bool tone_mapping_enabled_{true};
};

} // namespace engine
