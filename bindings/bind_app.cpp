#include "bind_common.hpp"
#include "engine/app.hpp"
#include "engine/asset_io.hpp"
#include "engine/input.hpp"
#include "engine/audio.hpp"
#include "engine/editor.hpp"
#include "engine/scene.hpp"
#include "engine/camera.hpp"
#include "engine/render_target.hpp"
#include "engine/post_process.hpp"
#include "engine/cube_camera.hpp"
#include "contracts/phase4_environment_contracts.h"

void bind_app(nb::module_& m) {
    // -----------------------------------------------------------------------
    // Mode Enum
    // -----------------------------------------------------------------------
    nb::enum_<engine::EngineMode>(m, "Mode")
        .value("GAME", engine::EngineMode::GAME)
        .value("EDITOR", engine::EngineMode::EDITOR)
        .export_values();

    // -----------------------------------------------------------------------
    // Key Enum
    // -----------------------------------------------------------------------
    nb::enum_<engine::Key>(m, "Key")
        .value("INVALID", engine::Key::Invalid)
        .value("SPACE", engine::Key::Space)
        .value("APOSTROPHE", engine::Key::Apostrophe)
        .value("COMMA", engine::Key::Comma)
        .value("MINUS", engine::Key::Minus)
        .value("PERIOD", engine::Key::Period)
        .value("SLASH", engine::Key::Slash)
        .value("NUM_0", engine::Key::Num0)
        .value("NUM_1", engine::Key::Num1)
        .value("NUM_2", engine::Key::Num2)
        .value("NUM_3", engine::Key::Num3)
        .value("NUM_4", engine::Key::Num4)
        .value("NUM_5", engine::Key::Num5)
        .value("NUM_6", engine::Key::Num6)
        .value("NUM_7", engine::Key::Num7)
        .value("NUM_8", engine::Key::Num8)
        .value("NUM_9", engine::Key::Num9)
        .value("A", engine::Key::A)
        .value("B", engine::Key::B)
        .value("C", engine::Key::C)
        .value("D", engine::Key::D)
        .value("E", engine::Key::E)
        .value("F", engine::Key::F)
        .value("G", engine::Key::G)
        .value("H", engine::Key::H)
        .value("I", engine::Key::I)
        .value("J", engine::Key::J)
        .value("K", engine::Key::K)
        .value("L", engine::Key::L)
        .value("M", engine::Key::M)
        .value("N", engine::Key::N)
        .value("O", engine::Key::O)
        .value("P", engine::Key::P)
        .value("Q", engine::Key::Q)
        .value("R", engine::Key::R)
        .value("S", engine::Key::S)
        .value("T", engine::Key::T)
        .value("U", engine::Key::U)
        .value("V", engine::Key::V)
        .value("W", engine::Key::W)
        .value("X", engine::Key::X)
        .value("Y", engine::Key::Y)
        .value("Z", engine::Key::Z)
        .value("ESCAPE", engine::Key::Escape)
        .value("ENTER", engine::Key::Enter)
        .value("TAB", engine::Key::Tab)
        .value("BACKSPACE", engine::Key::Backspace)
        .value("RIGHT", engine::Key::Right)
        .value("LEFT", engine::Key::Left)
        .value("DOWN", engine::Key::Down)
        .value("UP", engine::Key::Up)
        .value("PAGE_UP", engine::Key::PageUp)
        .value("PAGE_DOWN", engine::Key::PageDown)
        .value("HOME", engine::Key::Home)
        .value("END", engine::Key::End)
        .value("LEFT_SHIFT", engine::Key::LeftShift)
        .value("LEFT_CONTROL", engine::Key::LeftControl)
        .value("LEFT_ALT", engine::Key::LeftAlt)
        .value("F1", engine::Key::F1)
        .value("F2", engine::Key::F2)
        .value("F3", engine::Key::F3)
        .value("F4", engine::Key::F4)
        .value("F5", engine::Key::F5)
        .export_values();

    // -----------------------------------------------------------------------
    // UI Command Contract (Phase 0.1)
    // -----------------------------------------------------------------------
    nb::enum_<engine::UICommandType>(m, "UICommandType")
        .value("Text", engine::UICommandType::Text)
        .value("Rect", engine::UICommandType::Rect)
        .value("Line", engine::UICommandType::Line)
        .value("Crosshair", engine::UICommandType::Crosshair)
        .export_values();

    nb::class_<engine::UICommand>(m, "UICommand")
        .def(nb::init<>())
        .def_rw("type", &engine::UICommand::type)
        .def_rw("text", &engine::UICommand::text)
        .def_prop_rw("pos",
            [](const engine::UICommand& c) { return c.pos; },
            [](engine::UICommand& c, const nb::object& o) {
                if (nb::isinstance<glm::vec2>(o)) c.pos = nb::cast<glm::vec2>(o);
                else if (nb::isinstance<nb::tuple>(o) || nb::isinstance<nb::list>(o)) {
                    auto s = nb::cast<std::vector<float>>(o);
                    if (s.size() >= 2) c.pos = { s[0], s[1] };
                }
            })
        .def_prop_rw("size",
            [](const engine::UICommand& c) { return c.size; },
            [](engine::UICommand& c, const nb::object& o) {
                if (nb::isinstance<glm::vec2>(o)) c.size = nb::cast<glm::vec2>(o);
                else if (nb::isinstance<nb::tuple>(o) || nb::isinstance<nb::list>(o)) {
                    auto s = nb::cast<std::vector<float>>(o);
                    if (s.size() >= 2) c.size = { s[0], s[1] };
                }
            })
        .def_prop_rw("color",
            [](const engine::UICommand& c) { return c.color; },
            [](engine::UICommand& c, const nb::object& o) {
                if (nb::isinstance<glm::vec4>(o)) c.color = nb::cast<glm::vec4>(o);
                else if (nb::isinstance<nb::tuple>(o) || nb::isinstance<nb::list>(o)) {
                    auto s = nb::cast<std::vector<float>>(o);
                    if (s.size() >= 4) c.color = { s[0], s[1], s[2], s[3] };
                    else if (s.size() == 3) c.color = { s[0], s[1], s[2], 1.0f };
                }
            })
        .def_rw("thickness", &engine::UICommand::thickness);

    // -----------------------------------------------------------------------
    // InputManager
    // -----------------------------------------------------------------------
    nb::class_<engine::InputManager>(m, "InputManager")
        .def("is_key_down", &engine::InputManager::is_key_down, "key"_a)
        .def("is_key_pressed", &engine::InputManager::is_key_pressed, "key"_a)
        .def("is_key_released", &engine::InputManager::is_key_released, "key"_a)
        .def("is_mouse_down", &engine::InputManager::is_mouse_down, "button"_a)
        .def_prop_ro("mouse_x", &engine::InputManager::mouse_x)
        .def_prop_ro("mouse_y", &engine::InputManager::mouse_y)
        .def_prop_ro("mouse_dx", &engine::InputManager::mouse_dx)
        .def_prop_ro("mouse_dy", &engine::InputManager::mouse_dy)
        .def("is_mouse_locked", &engine::InputManager::is_mouse_locked)
        .def("set_mouse_locked", &engine::InputManager::set_mouse_locked, "locked"_a);

    // -----------------------------------------------------------------------
    // AudioManager
    // -----------------------------------------------------------------------
    nb::class_<engine::AudioManager>(m, "AudioManager")
        .def("play_footstep", &engine::AudioManager::play_footstep)
        .def("play_jump", &engine::AudioManager::play_jump)
        .def("play_hit_3d", [](engine::AudioManager& a, const nb::object& pos) {
            if (nb::isinstance<glm::vec3>(pos)) {
                a.play_hit_3d(nb::cast<glm::vec3>(pos));
            } else if (nb::isinstance<nb::tuple>(pos) || nb::isinstance<nb::list>(pos)) {
                auto seq = nb::cast<std::vector<float>>(pos);
                if (seq.size() >= 3) a.play_hit_3d({ seq[0], seq[1], seq[2] });
            }
        }, "world_pos"_a)
        .def("play_sound_file", &engine::AudioManager::play_sound_file, "filepath"_a, "volume"_a = 1.0f);

    // -----------------------------------------------------------------------
    // EditorManager
    // -----------------------------------------------------------------------
    nb::class_<engine::EditorManager>(m, "EditorManager")
        .def_rw("show_hierarchy", &engine::EditorManager::show_hierarchy)
        .def_rw("show_inspector", &engine::EditorManager::show_inspector)
        .def_rw("show_postprocess", &engine::EditorManager::show_postprocess)
        .def_rw("show_perf_overlay", &engine::EditorManager::show_perf_overlay)
        .def_prop_rw("gizmo_operation", &engine::EditorManager::gizmo_operation, &engine::EditorManager::set_gizmo_operation)
        .def("select_entity", &engine::EditorManager::select_entity, "entity"_a.none() = nb::none())
        .def("set_selected_entity", &engine::EditorManager::select_entity, "entity"_a.none() = nb::none())
        .def("select_node", &engine::EditorManager::select_node, "node"_a.none() = nb::none())
        .def_prop_rw("selected_node", &engine::EditorManager::selected_node, &engine::EditorManager::select_node)
        .def_prop_rw("selected_entity",
            &engine::EditorManager::selected_entity,
            &engine::EditorManager::select_entity)
        .def("save_scene_to_script", &engine::EditorManager::save_scene_to_script, "filepath"_a = "exported_scene.py")
        .def("enable_toggle_hotkey", &engine::EditorManager::enable_toggle_hotkey, "enable"_a, "key"_a = engine::Key::F2)
        .def("is_toggle_hotkey_enabled", &engine::EditorManager::is_toggle_hotkey_enabled)
        .def("toggle_hotkey", &engine::EditorManager::toggle_hotkey);

    // -----------------------------------------------------------------------
    // EngineApp
    // -----------------------------------------------------------------------
    nb::class_<engine::EngineApp>(m, "EngineApp")
        .def(nb::init<>())
        .def(nb::init<const std::string&, int, int>(),
             "title"_a, "width"_a, "height"_a)
        .def("init", &engine::EngineApp::init,
             "title"_a = "VelocityEngine v0.2-beta",
             "width"_a = 800,
             "height"_a = 600)
        .def("run", &engine::EngineApp::run,
             nb::call_guard<nb::gil_scoped_release>())
        .def("close", &engine::EngineApp::close)
        .def("is_running", &engine::EngineApp::is_running)

        // Subsystems
        .def_prop_ro("scene", &engine::EngineApp::scene, nb::rv_policy::reference_internal)
        .def_prop_ro("camera", &engine::EngineApp::camera, nb::rv_policy::reference_internal)
        .def_prop_ro("input", &engine::EngineApp::input, nb::rv_policy::reference_internal)
        .def_prop_ro("audio", &engine::EngineApp::audio, nb::rv_policy::reference_internal)
        .def_prop_ro("editor", &engine::EngineApp::editor, nb::rv_policy::reference_internal)

        // Mode
        .def_prop_rw("mode", &engine::EngineApp::get_mode, &engine::EngineApp::set_mode)
        .def("get_mode", &engine::EngineApp::get_mode)
        .def("set_mode", &engine::EngineApp::set_mode, "mode"_a)
        .def("toggle_mode", &engine::EngineApp::toggle_mode)

        // Texture convenience loaders
        .def("load_texture", [](engine::EngineApp&, const std::string& path) {
            return engine::Texture::load_from_file(path);
        }, "filepath"_a)
        .def("create_checkerboard_texture", [](engine::EngineApp&, int w, int h, int tile) {
            return engine::Texture::create_checkerboard(w, h, tile);
        }, "width"_a = 64, "height"_a = 64, "tile_size"_a = 8)

        // Callbacks
        .def("set_update_callback", [](engine::EngineApp& self, std::optional<engine::EngineApp::UpdateCallback> cb) {
            if (cb.has_value()) {
                self.set_update_callback(std::move(*cb));
            } else {
                self.set_update_callback(nullptr);
            }
        }, "callback"_a.none() = nb::none())

        // Color & Window
        .def("set_clear_color", &engine::EngineApp::set_clear_color, "r"_a, "g"_a, "b"_a, "a"_a = 1.0f)
        .def("get_clear_color", &engine::EngineApp::get_clear_color)
        .def("set_mouse_locked", &engine::EngineApp::set_mouse_locked, "locked"_a)
        .def("is_mouse_locked", &engine::EngineApp::is_mouse_locked)
        .def_prop_ro("width", &engine::EngineApp::width)
        .def_prop_ro("height", &engine::EngineApp::height)
        .def_prop_ro("title", &engine::EngineApp::title)
        .def("set_title", &engine::EngineApp::set_title, "title"_a)

        // HUD and Debug options
        .def("set_show_hud", &engine::EngineApp::set_show_hud, "enable"_a)
        .def_prop_rw("show_hud", &engine::EngineApp::show_hud, &engine::EngineApp::set_show_hud)
        .def("set_show_crosshair", &engine::EngineApp::set_show_crosshair, "show"_a)
        .def_prop_rw("show_crosshair", &engine::EngineApp::show_crosshair, &engine::EngineApp::set_show_crosshair)
        .def("set_hud_score", &engine::EngineApp::set_hud_score, "score"_a)
        .def_prop_rw("hud_score", &engine::EngineApp::hud_score, &engine::EngineApp::set_hud_score)
        .def("set_hud_title", &engine::EngineApp::set_hud_title, "title"_a)
        .def_prop_rw("hud_title", &engine::EngineApp::hud_title, &engine::EngineApp::set_hud_title)
        .def("set_hud_hint", &engine::EngineApp::set_hud_hint, "hint"_a)
        .def_prop_rw("hud_hint", &engine::EngineApp::hud_hint, &engine::EngineApp::set_hud_hint)
        .def("set_debug_hitboxes", &engine::EngineApp::set_debug_hitboxes, "enable"_a)
        .def("toggle_debug_hitboxes", &engine::EngineApp::toggle_debug_hitboxes)
        .def_prop_rw("debug_hitboxes", &engine::EngineApp::is_debug_hitboxes, &engine::EngineApp::set_debug_hitboxes)
        .def("set_target_fps", &engine::EngineApp::set_target_fps, "fps"_a)
        .def_prop_rw("target_fps", &engine::EngineApp::target_fps, &engine::EngineApp::set_target_fps)
        .def("set_vsync", &engine::EngineApp::set_vsync, "enabled"_a)
        .def_prop_rw("vsync", &engine::EngineApp::vsync, &engine::EngineApp::set_vsync)
        .def_prop_ro("fps", &engine::EngineApp::fps)
        .def_prop_ro("frame_time_ms", &engine::EngineApp::frame_time_ms)

        // Fog & Tone Mapping
        .def("set_linear_fog", [](engine::EngineApp& app, const nb::object& color, float near_dist, float far_dist) {
            glm::vec3 c{0.8f, 0.8f, 0.85f};
            if (nb::isinstance<glm::vec3>(color)) c = nb::cast<glm::vec3>(color);
            else if (nb::isinstance<nb::tuple>(color) || nb::isinstance<nb::list>(color)) {
                auto s = nb::cast<std::vector<float>>(color);
                if (s.size() >= 3) c = { s[0], s[1], s[2] };
            }
            app.set_linear_fog(c, near_dist, far_dist);
        }, "color"_a, "near"_a = 1.0f, "far"_a = 100.0f)
        .def("set_exp2_fog", [](engine::EngineApp& app, const nb::object& color, float density) {
            glm::vec3 c{0.8f, 0.8f, 0.85f};
            if (nb::isinstance<glm::vec3>(color)) c = nb::cast<glm::vec3>(color);
            else if (nb::isinstance<nb::tuple>(color) || nb::isinstance<nb::list>(color)) {
                auto s = nb::cast<std::vector<float>>(color);
                if (s.size() >= 3) c = { s[0], s[1], s[2] };
            }
            app.set_exp2_fog(c, density);
        }, "color"_a, "density"_a = 0.02f)
        .def("clear_fog", &engine::EngineApp::clear_fog)
        .def_prop_ro("fog_enabled", &engine::EngineApp::fog_enabled)
        .def_prop_ro("fog_type", &engine::EngineApp::fog_type)
        .def_prop_ro("fog_color", &engine::EngineApp::fog_color)
        .def_prop_ro("fog_near", &engine::EngineApp::fog_near)
        .def_prop_ro("fog_far", &engine::EngineApp::fog_far)
        .def_prop_ro("fog_density", &engine::EngineApp::fog_density)
        .def("set_tone_mapping", &engine::EngineApp::set_tone_mapping, "enable"_a)
        .def_prop_rw("tone_mapping", &engine::EngineApp::tone_mapping_enabled, &engine::EngineApp::set_tone_mapping)
        .def("submit_ui_commands", [](engine::EngineApp& app, const nb::object& cmds_obj) {
            std::vector<engine::UICommand> cmds;
            if (nb::isinstance<nb::list>(cmds_obj) || nb::isinstance<nb::tuple>(cmds_obj)) {
                for (auto handle : cmds_obj) {
                    if (nb::isinstance<engine::UICommand>(handle)) {
                        cmds.push_back(nb::cast<engine::UICommand>(handle));
                    }
                }
            }
            app.submit_ui_commands(cmds);
        }, "cmds"_a)
        .def("clear_ui_commands", &engine::EngineApp::clear_ui_commands)
        .def_prop_ro("custom_ui_commands", &engine::EngineApp::custom_ui_commands)
        .def("evaluate_frustum_culling", &engine::EngineApp::evaluate_frustum_culling)
        .def("render_target", &engine::EngineApp::render_target, "scene"_a, "camera"_a, "target"_a)
        .def("read_pixels", [](engine::EngineApp& app, engine::RenderTarget& target) {
            auto pixels = app.read_pixels(target);
            return nb::bytes(pixels.data(), pixels.size());
        }, "target"_a)
        .def("read_depth_pixels", [](engine::EngineApp& app, engine::RenderTarget& target) {
            return app.read_depth_pixels(target);
        }, "target"_a)
        .def("set_composer", &engine::EngineApp::set_composer, "composer"_a)
        .def_prop_rw("composer", &engine::EngineApp::composer, &engine::EngineApp::set_composer)
        .def_prop_ro("stats", [](engine::EngineApp& app) -> const engine::RenderStats& {
            return app.stats();
        }, nb::rv_policy::reference_internal)
        .def_prop_rw("shadow_settings",
            [](engine::EngineApp& app) -> const engine::ShadowSettings& { return app.shadow_settings(); },
            [](engine::EngineApp& app, const engine::ShadowSettings& s) { app.set_shadow_settings(s); },
            nb::rv_policy::reference_internal)
        .def("set_shadow_settings", &engine::EngineApp::set_shadow_settings, "settings"_a)
        .def("set_shadow_resolution", &engine::EngineApp::set_shadow_resolution, "res"_a)
        .def("set_shadow_bias", &engine::EngineApp::set_shadow_bias, "bias"_a)
        .def("set_shadow_normal_bias", &engine::EngineApp::set_shadow_normal_bias, "normal_bias"_a)
        .def("set_shadow_ortho_size", &engine::EngineApp::set_shadow_ortho_size, "size"_a)
        .def("set_shadow_pcf_16_tap", &engine::EngineApp::set_shadow_pcf_16_tap, "enable"_a)
        .def("set_shadow_texel_snapping", &engine::EngineApp::set_shadow_texel_snapping, "enable"_a)
        .def("render_cube_camera", &engine::EngineApp::render_cube_camera, "scene"_a, "camera"_a)
        .def("save_screenshot", &engine::EngineApp::save_screenshot, "filepath"_a)
        .def("dispatch_mouse_click", &engine::EngineApp::dispatch_mouse_click, "mouse_x"_a, "mouse_y"_a)
        .def("dispatch_mouse_move", &engine::EngineApp::dispatch_mouse_move, "mouse_x"_a, "mouse_y"_a)
        .def("on", [](engine::EngineApp& app, const std::string& event_name, nb::callable cb) {
            app.on(event_name, [cb](const std::string& ev, void* data) {
                nb::gil_scoped_acquire gil;
                try {
                    cb(ev, data);
                } catch (...) {
                    try {
                        cb(ev);
                    } catch (...) {
                        try {
                            cb();
                        } catch (...) {}
                    }
                }
            });
        }, "event_name"_a, "callback"_a)
        .def("emit", [](engine::EngineApp& app, const std::string& event_name) {
            app.emit(event_name, nullptr);
        }, "event_name"_a);

    m.def("save_screenshot", &engine::save_screenshot, "app"_a, "filepath"_a);
}
