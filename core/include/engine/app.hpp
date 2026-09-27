#pragma once

#include <string>
#include <array>
#include <functional>
#include <chrono>

#include <glm/glm.hpp>

namespace engine {

struct WindowConfig {
    std::string title = "Engine 3D Core";
    int width = 800;
    int height = 600;
    // Dark-blue #1a1a24
    std::array<float, 4> clear_color = { 0.10196f, 0.10196f, 0.14118f, 1.0f };
};

struct Vertex {
    float x, y, z;
    float r, g, b, a;
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

    // Python frame update callback
    void set_update_callback(UpdateCallback callback);

    // 3D Scene / Cube Transform
    void set_rotation(float rx, float ry, float rz);
    void set_rotation_x(float rx) { rotation_.x = rx; }
    void set_rotation_y(float ry) { rotation_.y = ry; }
    void set_rotation_z(float rz) { rotation_.z = rz; }
    float rotation_x() const { return rotation_.x; }
    float rotation_y() const { return rotation_.y; }
    float rotation_z() const { return rotation_.z; }

    void set_position(float x, float y, float z);
    void set_position_x(float x) { position_.x = x; }
    void set_position_y(float y) { position_.y = y; }
    void set_position_z(float z) { position_.z = z; }
    float position_x() const { return position_.x; }
    float position_y() const { return position_.y; }
    float position_z() const { return position_.z; }

    void set_scale(float sx, float sy, float sz);
    float scale_x() const { return scale_.x; }
    float scale_y() const { return scale_.y; }
    float scale_z() const { return scale_.z; }

    // Internal Sokol callbacks
    void on_init();
    void on_frame();
    void on_cleanup();
    void on_event(const void* raw_event);

private:
    void init_mesh_and_pipeline();

    WindowConfig config_;
    bool running_{false};
    bool initialized_{false};

    UpdateCallback update_callback_{nullptr};
    std::chrono::steady_clock::time_point last_frame_time_;
    bool has_last_frame_{false};

    // 3D Transform
    glm::vec3 position_{0.0f, 0.0f, 0.0f};
    glm::vec3 rotation_{0.0f, 0.0f, 0.0f}; // in degrees
    glm::vec3 scale_{1.0f, 1.0f, 1.0f};

    // Camera parameters
    glm::vec3 camera_pos_{0.0f, 1.5f, 4.0f};
    glm::vec3 camera_target_{0.0f, 0.0f, 0.0f};
    glm::vec3 camera_up_{0.0f, 1.0f, 0.0f};

    // Sokol graphics resources (opaque handles stored as uint32_t)
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
    uint32_t vbuf_id_{0};
    uint32_t ibuf_id_{0};
};

} // namespace engine
