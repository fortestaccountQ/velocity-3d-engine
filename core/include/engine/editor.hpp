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
    bool show_perf_overlay{false};

    void enable_toggle_hotkey(bool enable, Key hotkey = Key::F2) {
        toggle_hotkey_enabled_ = enable;
        toggle_hotkey_ = hotkey;
    }
    bool is_toggle_hotkey_enabled() const { return toggle_hotkey_enabled_; }
    Key toggle_hotkey() const { return toggle_hotkey_; }

    std::shared_ptr<Entity> selected_entity() const { return selected_entity_; }
    void select_entity(std::shared_ptr<Entity> entity) { selected_entity_ = entity; }

    int gizmo_operation() const { return gizmo_op_; }
    void set_gizmo_operation(int op) { gizmo_op_ = op; }

private:
    void render_top_menubar();
    void render_hierarchy_panel();
    void render_inspector_panel();
    void render_perf_overlay(float dt);
    void render_gizmo(float screen_w, float screen_h);

    EngineApp& app_;
    std::shared_ptr<Entity> selected_entity_{nullptr};
    bool toggle_hotkey_enabled_{true};
    Key toggle_hotkey_{Key::F2};
    int gizmo_op_{0}; // 0 = Translate, 1 = Rotate, 2 = Scale
    bool initialized_{false};
};

} // namespace engine
