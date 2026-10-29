#include "engine/editor.hpp"
#include "engine/app.hpp"
#include "sokol_app.h"
#include "sokol_gfx.h"
#include "imgui.h"
#include "util/sokol_imgui.h"
#include "ImGuizmo.h"

#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <cstdlib>
#include <iostream>
#include <algorithm>
#include <filesystem>

#ifdef _WIN32
#include <windows.h>
#include <shellapi.h>
#endif

namespace engine {

EditorManager::EditorManager(EngineApp& app)
    : app_(app) {
}

EditorManager::~EditorManager() {
    shutdown();
}

void EditorManager::init() {
    if (initialized_) return;

    simgui_desc_t desc{};
    desc.sample_count = sapp_sample_count();
    simgui_setup(&desc);

    ImGuiIO& io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;
    io.IniFilename = nullptr; // Stateless / clean UI

    // Unity-style Dark Theme
    ImGuiStyle& style = ImGui::GetStyle();
    style.WindowRounding = 6.0f;
    style.FrameRounding = 4.0f;
    style.PopupRounding = 4.0f;
    style.ScrollbarRounding = 4.0f;
    style.GrabRounding = 3.0f;
    style.TabRounding = 4.0f;
    style.WindowBorderSize = 1.0f;
    style.FrameBorderSize = 0.0f;

    ImVec4* colors = style.Colors;
    colors[ImGuiCol_WindowBg]             = ImVec4(0.12f, 0.13f, 0.15f, 0.94f);
    colors[ImGuiCol_Header]               = ImVec4(0.20f, 0.23f, 0.28f, 0.85f);
    colors[ImGuiCol_HeaderHovered]        = ImVec4(0.28f, 0.33f, 0.40f, 0.90f);
    colors[ImGuiCol_HeaderActive]         = ImVec4(0.24f, 0.44f, 0.68f, 1.00f);
    colors[ImGuiCol_Button]               = ImVec4(0.20f, 0.24f, 0.30f, 0.85f);
    colors[ImGuiCol_ButtonHovered]        = ImVec4(0.28f, 0.36f, 0.46f, 1.00f);
    colors[ImGuiCol_ButtonActive]         = ImVec4(0.18f, 0.42f, 0.70f, 1.00f);
    colors[ImGuiCol_FrameBg]              = ImVec4(0.18f, 0.20f, 0.24f, 0.85f);
    colors[ImGuiCol_FrameBgHovered]       = ImVec4(0.24f, 0.28f, 0.34f, 0.90f);
    colors[ImGuiCol_FrameBgActive]        = ImVec4(0.28f, 0.34f, 0.42f, 1.00f);
    colors[ImGuiCol_TitleBg]              = ImVec4(0.09f, 0.10f, 0.12f, 1.00f);
    colors[ImGuiCol_TitleBgActive]        = ImVec4(0.14f, 0.16f, 0.20f, 1.00f);
    colors[ImGuiCol_CheckMark]            = ImVec4(0.35f, 0.75f, 1.00f, 1.00f);
    colors[ImGuiCol_SliderGrab]           = ImVec4(0.30f, 0.60f, 0.90f, 1.00f);
    colors[ImGuiCol_SliderGrabActive]     = ImVec4(0.40f, 0.75f, 1.00f, 1.00f);

    ImGuizmo::Enable(true);
    initialized_ = true;
}

void EditorManager::shutdown() {
    if (!initialized_) return;
    simgui_shutdown();
    initialized_ = false;
}

bool EditorManager::handle_event(const void* raw_event) {
    if (!initialized_ || !raw_event) return false;
    const auto* ev = static_cast<const sapp_event*>(raw_event);

    // Forward to Dear ImGui
    simgui_handle_event(ev);

    ImGuiIO& io = ImGui::GetIO();
    bool imgui_busy = io.WantCaptureMouse || io.WantCaptureKeyboard;
    bool gizmo_busy = ImGuizmo::IsUsing() || ImGuizmo::IsOver();

    // In-viewport raycast entity selection when clicking in 3D scene
    if (ev->type == SAPP_EVENTTYPE_MOUSE_DOWN && ev->mouse_button == SAPP_MOUSEBUTTON_LEFT) {
        if (!imgui_busy && !gizmo_busy) {
            float sw = sapp_widthf();
            float sh = sapp_heightf();
            if (sw > 0.0f && sh > 0.0f) {
                Ray ray = app_.camera().screen_to_ray(ev->mouse_x, ev->mouse_y, sw, sh);
                RaycastHit hit = app_.scene().raycast(ray, 100.0f);
                if (hit.hit && hit.entity) {
                    selected_entity_ = hit.entity;
                    while (selected_entity_->parent && selected_entity_->parent->parent) {
                        selected_entity_ = selected_entity_->parent;
                    }
                }
            }
        }
    }

    // Hotkey switching for gizmo operations: W=Translate, E=Rotate, R=Scale
    if (ev->type == SAPP_EVENTTYPE_KEY_DOWN && !io.WantCaptureKeyboard) {
        if (ev->key_code == SAPP_KEYCODE_W) gizmo_op_ = 0;
        else if (ev->key_code == SAPP_KEYCODE_E) gizmo_op_ = 1;
        else if (ev->key_code == SAPP_KEYCODE_R) gizmo_op_ = 2;
    }

    return (imgui_busy || gizmo_busy);
}

void EditorManager::render(float dt, float screen_w, float screen_h) {
    if (!initialized_) return;

    simgui_frame_desc_t fdesc{};
    fdesc.width = sapp_width();
    fdesc.height = sapp_height();
    fdesc.delta_time = dt;
    fdesc.dpi_scale = sapp_dpi_scale();
    simgui_new_frame(&fdesc);
    ImGuizmo::BeginFrame();

    render_top_menubar();

    if (show_hierarchy) {
        render_hierarchy_panel();
    }
    if (show_inspector) {
        render_inspector_panel();
    }
    if (show_perf_overlay) {
        render_perf_overlay(dt);
    }

    // 3D Gizmo for selected entity
    render_gizmo(screen_w, screen_h);

    simgui_render();
}

void EditorManager::render_top_menubar() {
    if (ImGui::BeginMainMenuBar()) {
        if (ImGui::BeginMenu("VelocityEngine")) {
            if (ImGui::MenuItem("Game Mode [F2]")) {
                app_.set_mode(EngineMode::GAME);
            }
            ImGui::Separator();
            if (ImGui::MenuItem("Exit", "ESC")) {
                sapp_request_quit();
            }
            ImGui::EndMenu();
        }

        if (ImGui::BeginMenu("Panels")) {
            ImGui::MenuItem("Scene Hierarchy", nullptr, &show_hierarchy);
            ImGui::MenuItem("Inspector", nullptr, &show_inspector);
            ImGui::MenuItem("Performance Overlay", nullptr, &show_perf_overlay);
            ImGui::EndMenu();
        }

        if (ImGui::BeginMenu("Gizmo Tool")) {
            if (ImGui::MenuItem("Translate [W]", nullptr, gizmo_op_ == 0)) gizmo_op_ = 0;
            if (ImGui::MenuItem("Rotate [E]", nullptr, gizmo_op_ == 1)) gizmo_op_ = 1;
            if (ImGui::MenuItem("Scale [R]", nullptr, gizmo_op_ == 2)) gizmo_op_ = 2;
            ImGui::EndMenu();
        }

        // Status right aligned in menubar
        float status_x = ImGui::GetWindowWidth() - 320.0f;
        if (status_x > ImGui::GetCursorPosX()) {
            ImGui::SetCursorPosX(status_x);
        }
        ImGui::TextColored(ImVec4(0.35f, 0.75f, 1.0f, 1.0f), "[EDITOR MODE]");
        ImGui::SameLine();
        ImGui::Text("| Press F2 to Play");

        ImGui::EndMainMenuBar();
    }
}

void EditorManager::render_hierarchy_panel() {
    ImGui::SetNextWindowPos(ImVec2(10.0f, 32.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(290.0f, 440.0f), ImGuiCond_FirstUseEver);

    if (ImGui::Begin("Scene Hierarchy", &show_hierarchy)) {
        // Quick Action Buttons
        if (ImGui::Button("+ Add Cube")) {
            static int cube_count = 1;
            auto entity = app_.scene().create_cube(glm::vec4(1.0f, 1.0f, 1.0f, 1.0f));
            entity->name = "Editor_Cube_" + std::to_string(cube_count++);
            entity->transform.position = app_.camera().position + app_.camera().forward() * 3.5f;
            selected_entity_ = entity;
        }
        ImGui::SameLine();
        if (ImGui::Button("+ Add Light")) {
            app_.scene().light.intensity += 0.2f;
        }

        ImGui::Separator();

        // Entity Tree
        ImGui::TextDisabled("SCENE OBJECTS (%zu)", app_.scene().entities().size());
        ImGui::Separator();

        for (const auto& entity : app_.scene().entities()) {
            if (!entity) continue;

            // Only display top-level or primary mesh nodes
            bool is_selected = (selected_entity_ == entity);
            ImGuiTreeNodeFlags flags = ImGuiTreeNodeFlags_Leaf | ImGuiTreeNodeFlags_NoTreePushOnOpen | ImGuiTreeNodeFlags_SpanAvailWidth;
            if (is_selected) flags |= ImGuiTreeNodeFlags_Selected;

            std::string icon = entity->mesh ? "[M] " : "[G] ";
            std::string label = icon + entity->name;

            if (ImGui::TreeNodeEx((void*)(intptr_t)entity->id, flags, "%s", label.c_str())) {
                if (ImGui::IsItemClicked()) {
                    selected_entity_ = entity;
                }
            }
        }
    }
    ImGui::End();
}

void EditorManager::render_inspector_panel() {
    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x - 330.0f, 32.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(320.0f, 520.0f), ImGuiCond_FirstUseEver);

    if (ImGui::Begin("Inspector", &show_inspector)) {
        if (!selected_entity_) {
            ImGui::TextDisabled("Select an entity from Hierarchy or Viewport");
            ImGui::Separator();
            // Show global Sun light properties by default if no entity selected
            ImGui::TextColored(ImVec4(1.0f, 0.85f, 0.3f, 1.0f), "Global Sun Light");
            auto& light = app_.scene().light;
            ImGui::DragFloat3("Direction", &light.direction.x, 0.02f, -1.0f, 1.0f);
            ImGui::ColorEdit3("Sun Color", &light.color.x);
            ImGui::DragFloat("Intensity", &light.intensity, 0.05f, 0.0f, 10.0f);
            ImGui::ColorEdit3("Ambient Sky", &light.ambient_sky.x);
            ImGui::ColorEdit3("Ambient Ground", &light.ambient_ground.x);
            ImGui::End();
            return;
        }

        // Entity Header
        char name_buf[128];
        std::snprintf(name_buf, sizeof(name_buf), "%s", selected_entity_->name.c_str());
        if (ImGui::InputText("Name", name_buf, sizeof(name_buf))) {
            selected_entity_->name = name_buf;
        }
        ImGui::Checkbox("Visible", &selected_entity_->visible);
        ImGui::SameLine();
        ImGui::Checkbox("Collision", &selected_entity_->has_collision);
        ImGui::SameLine();
        ImGui::Checkbox("Shadows", &selected_entity_->cast_shadows);

        ImGui::Separator();

        // 1. Transform Section
        if (ImGui::CollapsingHeader("Transform", ImGuiTreeNodeFlags_DefaultOpen)) {
            auto& t = selected_entity_->transform;
            glm::vec3 pos = t.position;
            if (ImGui::DragFloat3("Position", &pos.x, 0.05f)) {
                t.position = pos;
            }

            glm::vec3 rot = t.rotation();
            if (ImGui::DragFloat3("Rotation (deg)", &rot.x, 0.5f)) {
                t.set_rotation(rot);
            }

            glm::vec3 scale = t.scale;
            if (ImGui::DragFloat3("Scale", &scale.x, 0.02f, 0.001f, 100.0f)) {
                t.scale = scale;
            }

            if (selected_entity_->has_collision) {
                ImGui::SliderFloat("Collision Scale", &selected_entity_->collision_scale, 0.1f, 2.0f, "%.2f");
            }
        }

        // 2. Material & Color Section
        if (ImGui::CollapsingHeader("Material & Shading", ImGuiTreeNodeFlags_DefaultOpen)) {
            if (selected_entity_->material) {
                auto mat = selected_entity_->material;
                ImGui::ColorEdit4("Base Color", &mat->base_color.x);
                ImGui::SliderFloat("Metallic", &mat->metallic, 0.0f, 1.0f);
                ImGui::SliderFloat("Roughness", &mat->roughness, 0.04f, 1.0f);
                ImGui::DragFloat2("UV Scale", &mat->uv_scale.x, 0.1f, 0.1f, 50.0f);
            } else {
                ImGui::ColorEdit4("Tint Color", &selected_entity_->color.x);
            }
        }

        // 3. Script & VS Code Integration
        if (ImGui::CollapsingHeader("Scripting & Code", ImGuiTreeNodeFlags_DefaultOpen)) {
            char script_buf[256];
            std::snprintf(script_buf, sizeof(script_buf), "%s", selected_entity_->script_path.c_str());
            if (ImGui::InputText("Script Path", script_buf, sizeof(script_buf))) {
                selected_entity_->script_path = script_buf;
            }

            if (!selected_entity_->script_path.empty()) {
                if (ImGui::Button("[ Open in VS Code ]")) {
#ifdef _WIN32
                    std::string cmd = "/c code -g \"" + selected_entity_->script_path + "\":1";
                    ShellExecuteA(NULL, "open", "cmd.exe", cmd.c_str(), NULL, SW_HIDE);
#else
                    std::string cmd = "code -g \"" + selected_entity_->script_path + "\":1 &";
                    std::system(cmd.c_str());
#endif
                }
            } else {
                ImGui::TextDisabled("No script bound. Set path above to open in VS Code.");
            }
        }

        // 4. Quick Actions
        ImGui::Separator();
        if (ImGui::Button("Focus Camera")) {
            app_.camera().set_target(selected_entity_->transform.position.x,
                                     selected_entity_->transform.position.y,
                                     selected_entity_->transform.position.z);
        }
        ImGui::SameLine();
        if (ImGui::Button("Deselect")) {
            selected_entity_ = nullptr;
        }
    }
    ImGui::End();
}

void EditorManager::render_perf_overlay(float dt) {
    ImGuiIO& io = ImGui::GetIO();
    ImGuiWindowFlags flags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize |
                            ImGuiWindowFlags_NoSavedSettings | ImGuiWindowFlags_NoFocusOnAppearing |
                            ImGuiWindowFlags_NoNav;
    ImGui::SetNextWindowPos(ImVec2(10.0f, io.DisplaySize.y - 70.0f), ImGuiCond_Always);
    ImGui::SetNextWindowBgAlpha(0.65f);
    if (ImGui::Begin("PerfOverlay", nullptr, flags)) {
        float fps = (dt > 0.0f) ? (1.0f / dt) : 60.0f;
        ImGui::Text("FPS: %.1f (%.2f ms)", fps, dt * 1000.0f);
        ImGui::Text("Entities: %zu | Draws: %u | Culled: %u", app_.scene().entities().size(), app_.stats().draw_calls, app_.stats().culled_objects);
    }
    ImGui::End();
}

void EditorManager::render_gizmo(float screen_w, float screen_h) {
    if (!selected_entity_ || screen_w <= 0.0f || screen_h <= 0.0f) return;

    ImGuizmo::SetOrthographic(false);
    ImGuizmo::SetDrawlist(ImGui::GetForegroundDrawList());
    ImGuizmo::SetRect(0.0f, 0.0f, screen_w, screen_h);

    glm::mat4 view = app_.camera().view_matrix();
    glm::mat4 proj = app_.camera().projection_matrix();
    glm::mat4 model = selected_entity_->transform.model_matrix();

    ImGuizmo::OPERATION op = ImGuizmo::TRANSLATE;
    if (gizmo_op_ == 1) op = ImGuizmo::ROTATE;
    else if (gizmo_op_ == 2) op = ImGuizmo::SCALE;

    if (ImGuizmo::Manipulate(glm::value_ptr(view), glm::value_ptr(proj),
                             op, ImGuizmo::WORLD, glm::value_ptr(model))) {
        float translation[3], rotation[3], scale[3];
        ImGuizmo::DecomposeMatrixToComponents(glm::value_ptr(model), translation, rotation, scale);
        selected_entity_->transform.set_position(translation[0], translation[1], translation[2]);
        selected_entity_->transform.set_rotation(rotation[0], rotation[1], rotation[2]);
        selected_entity_->transform.set_scale(scale[0], scale[1], scale[2]);
    }
}

} // namespace engine
