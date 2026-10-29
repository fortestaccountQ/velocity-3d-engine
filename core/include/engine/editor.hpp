#pragma once

#include <string>
#include <memory>
#include <vector>
#include <array>
#include <glm/glm.hpp>
#include "engine/entity.hpp"
#include "engine/input.hpp"

namespace engine {

class EngineApp;

enum class EngineMode : int {
    GAME = 0,
    EDITOR = 1
};

class EditorManager {
public:
    explicit EditorManager(EngineApp& app);
    ~EditorManager();

    void init();
    void shutdown();
    void render(float dt, float screen_w, float screen_h);
    bool handle_event(const void* raw_event);

    bool show_hierarchy{true};
    bool show_inspector{true};
    bool show_postprocess{true};
    bool show_perf_overlay{false};

    void enable_toggle_hotkey(bool enable, Key hotkey = Key::F2) {
        toggle_hotkey_enabled_ = enable;
        toggle_hotkey_ = hotkey;
    }
    bool is_toggle_hotkey_enabled() const { return toggle_hotkey_enabled_; }
    Key toggle_hotkey() const { return toggle_hotkey_; }

    std::shared_ptr<Entity> selected_entity() const {
        return std::dynamic_pointer_cast<Entity>(selected_node_);
    }
    void select_entity(std::shared_ptr<Entity> entity) {
        selected_node_ = entity;
    }

    std::shared_ptr<Node3D> selected_node() const { return selected_node_; }
    void select_node(std::shared_ptr<Node3D> node) { selected_node_ = node; }

    int gizmo_operation() const { return gizmo_op_; }
    void set_gizmo_operation(int op) { gizmo_op_ = op; }

    bool save_scene_to_script(const std::string& filepath);

private:
    void render_top_menubar();
    void render_hierarchy_panel();
    void render_hierarchy_node_recursive(const std::shared_ptr<Node3D>& node, const std::string& filter);
    void render_inspector_panel();
    void render_postprocess_panel();
    void render_perf_overlay(float dt);
    void render_gizmo(float screen_w, float screen_h);

    EngineApp& app_;
    std::shared_ptr<Node3D> selected_node_{nullptr};
    bool toggle_hotkey_enabled_{true};
    Key toggle_hotkey_{Key::F2};
    int gizmo_op_{0}; // 0 = Translate, 1 = Rotate, 2 = Scale
    bool initialized_{false};

    char search_filter_[128]{};
    std::string last_saved_script_path_{""};
    float save_notification_timer_{0.0f};

    // Editor local post-process values (synced with composer passes when available)
    float bloom_threshold_{1.0f};
    float bloom_strength_{1.5f};
    float bloom_radius_{0.5f};
    float ssao_radius_{0.5f};
    float ssao_power_{1.0f};
    float tonemap_exposure_{1.0f};
    float tonemap_gamma_{2.2f};
    int tonemap_mode_{0}; // 0 = ACESFilmic, 1 = Reinhard, 2 = Cineon, 3 = Linear, 4 = Neutral
};

} // namespace engine
