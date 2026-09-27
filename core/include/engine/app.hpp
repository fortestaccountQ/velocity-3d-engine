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

namespace engine {

struct WindowConfig {
    std::string title = "Engine 3D Core";
    int width = 800;
    int height = 600;
    // Dark-blue #1a1a24
    std::array<float, 4> clear_color = { 0.10196f, 0.10196f, 0.14118f, 1.0f };
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

    // Subsystems
    Scene& scene() { return scene_; }
    Camera& camera() { return camera_; }
    InputManager& input() { return input_; }

    // Mouse lock & visibility
    void set_mouse_locked(bool locked);
    bool is_mouse_locked() const;

    // Python frame update callback
    void set_update_callback(UpdateCallback callback);

    // Internal Sokol callbacks
    void on_init();
    void on_frame();
    void on_cleanup();
    void on_event(const void* raw_event);

private:
    void init_pipeline_and_shaders();

    WindowConfig config_;
    bool running_{false};
    bool initialized_{false};

    Scene scene_;
    Camera camera_;
    InputManager input_;

    UpdateCallback update_callback_{nullptr};
    std::chrono::steady_clock::time_point last_frame_time_;
    bool has_last_frame_{false};

    // Sokol graphics pipeline & shader handles
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
};

} // namespace engine
