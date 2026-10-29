#include "engine/editor.hpp"
#include "engine/app.hpp"
#include "engine/light.hpp"
#include "engine/camera.hpp"
#include "engine/post_process.hpp"
#include "engine/particle.hpp"
#include "engine/sprite.hpp"
#include "engine/points.hpp"
#include "engine/animation.hpp"
#include "engine/skinned_mesh.hpp"

#include "sokol_app.h"
#include "sokol_gfx.h"
#include "imgui.h"
#include "util/sokol_imgui.h"
#include "ImGuizmo.h"

#include <glm/gtc/type_ptr.hpp>
#include <glm/gtc/matrix_transform.hpp>
#include <cstdlib>
#include <iostream>
#include <fstream>
#include <algorithm>
#include <filesystem>
#include <iomanip>

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
                RaycastHit hit = app_.scene().raycast(ray, 1000.0f);
                if (hit.hit && hit.entity) {
                    selected_node_ = hit.entity;
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

    if (save_notification_timer_ > 0.0f) {
        save_notification_timer_ -= dt;
    }

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
    if (show_postprocess) {
        render_postprocess_panel();
    }
    if (show_perf_overlay) {
        render_perf_overlay(dt);
    }

    // 3D Gizmo for selected node
    render_gizmo(screen_w, screen_h);

    simgui_render();
}

void EditorManager::render_top_menubar() {
    if (ImGui::BeginMainMenuBar()) {
        if (ImGui::BeginMenu("Pielosyty")) {
            if (ImGui::MenuItem("Game Mode [F2]")) {
                app_.set_mode(EngineMode::GAME);
            }
            ImGui::Separator();
            if (ImGui::MenuItem("Save Scene to Python Script...")) {
                save_scene_to_script("exported_scene.py");
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
            ImGui::MenuItem("Post-Process & Render", nullptr, &show_postprocess);
            ImGui::MenuItem("Performance Overlay", nullptr, &show_perf_overlay);
            ImGui::EndMenu();
        }

        if (ImGui::BeginMenu("Gizmo Tool")) {
            if (ImGui::MenuItem("Translate [W]", nullptr, gizmo_op_ == 0)) gizmo_op_ = 0;
            if (ImGui::MenuItem("Rotate [E]", nullptr, gizmo_op_ == 1)) gizmo_op_ = 1;
            if (ImGui::MenuItem("Scale [R]", nullptr, gizmo_op_ == 2)) gizmo_op_ = 2;
            ImGui::EndMenu();
        }

        // Notification if saved
        if (save_notification_timer_ > 0.0f) {
            ImGui::SameLine();
            ImGui::TextColored(ImVec4(0.2f, 1.0f, 0.4f, 1.0f), "[Saved to %s]", last_saved_script_path_.c_str());
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

static bool string_contains_ignore_case(const std::string& haystack, const std::string& needle) {
    if (needle.empty()) return true;
    auto it = std::search(
        haystack.begin(), haystack.end(),
        needle.begin(), needle.end(),
        [](char ch1, char ch2) { return std::tolower(ch1) == std::tolower(ch2); }
    );
    return (it != haystack.end());
}

static bool node_or_subtree_matches(const std::shared_ptr<Node3D>& node, const std::string& filter) {
    if (filter.empty()) return true;
    if (string_contains_ignore_case(node->name, filter) || string_contains_ignore_case(node->tag, filter)) {
        return true;
    }
    for (const auto& child : node->children()) {
        if (child && node_or_subtree_matches(child, filter)) return true;
    }
    return false;
}

void EditorManager::render_hierarchy_node_recursive(const std::shared_ptr<Node3D>& node, const std::string& filter) {
    if (!node) return;
    if (!filter.empty() && !node_or_subtree_matches(node, filter)) return;

    std::string badge = "[Grp] ";
    if (std::dynamic_pointer_cast<Light>(node)) {
        badge = "[Light] ";
    } else if (std::dynamic_pointer_cast<Camera>(node)) {
        badge = "[Cam] ";
    } else if (std::dynamic_pointer_cast<ParticleEmitter>(node)) {
        badge = "[Emitter] ";
    } else if (std::dynamic_pointer_cast<Sprite>(node)) {
        badge = "[Sprite] ";
    } else if (std::dynamic_pointer_cast<Points>(node)) {
        badge = "[Points] ";
    } else if (std::dynamic_pointer_cast<SkinnedMesh>(node)) {
        badge = "[Mesh] ";
    } else if (auto ent = std::dynamic_pointer_cast<Entity>(node)) {
        badge = ent->mesh ? "[Mesh] " : "[Grp] ";
    }

    bool is_leaf = node->children().empty();
    ImGuiTreeNodeFlags flags = ImGuiTreeNodeFlags_OpenOnArrow | ImGuiTreeNodeFlags_SpanAvailWidth;
    if (is_leaf) flags |= ImGuiTreeNodeFlags_Leaf;
    if (selected_node_ == node) flags |= ImGuiTreeNodeFlags_Selected;

    std::string label = badge + node->name;
    if (!node->tag.empty()) {
        label += " (" + node->tag + ")";
    }

    bool open = ImGui::TreeNodeEx((void*)(intptr_t)node->id, flags, "%s", label.c_str());
    if (ImGui::IsItemClicked()) {
        selected_node_ = node;
    }

    if (open) {
        for (const auto& child : node->children()) {
            render_hierarchy_node_recursive(child, filter);
        }
        ImGui::TreePop();
    }
}

void EditorManager::render_hierarchy_panel() {
    ImGui::SetNextWindowPos(ImVec2(10.0f, 32.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(320.0f, 480.0f), ImGuiCond_FirstUseEver);

    if (ImGui::Begin("Scene Hierarchy", &show_hierarchy)) {
        // Search Filter Box
        ImGui::InputTextWithHint("##SearchFilter", "Search by name or tag...", search_filter_, sizeof(search_filter_));
        std::string filter_str = search_filter_;

        ImGui::Separator();

        // Quick Action Buttons
        if (ImGui::Button("+ Add Box")) {
            static int box_count = 1;
            auto entity = app_.scene().create_cube(glm::vec4(1.0f, 1.0f, 1.0f, 1.0f));
            entity->name = "Editor_Box_" + std::to_string(box_count++);
            entity->transform.position = app_.camera().position + app_.camera().forward() * 3.5f;
            selected_node_ = entity;
        }
        ImGui::SameLine();
        if (ImGui::Button("+ Add Sphere")) {
            static int sphere_count = 1;
            auto entity = app_.scene().create_sphere(0.5f, 32, 32, glm::vec4(1.0f, 1.0f, 1.0f, 1.0f));
            entity->name = "Editor_Sphere_" + std::to_string(sphere_count++);
            entity->transform.position = app_.camera().position + app_.camera().forward() * 3.5f;
            selected_node_ = entity;
        }

        ImGui::Separator();

        // Root Node Tree Display
        auto root = app_.scene().root_node();
        if (root) {
            if (root->children().empty()) {
                // If root node has no direct children, display entities list as fallback
                for (const auto& entity : app_.scene().entities()) {
                    render_hierarchy_node_recursive(entity, filter_str);
                }
            } else {
                for (const auto& child : root->children()) {
                    render_hierarchy_node_recursive(child, filter_str);
                }
            }
        }
    }
    ImGui::End();
}

void EditorManager::render_inspector_panel() {
    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x - 360.0f, 32.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(350.0f, 560.0f), ImGuiCond_FirstUseEver);

    if (ImGui::Begin("Inspector", &show_inspector)) {
        if (!selected_node_) {
            ImGui::TextDisabled("Select a node from Hierarchy or 3D Viewport");
            ImGui::Separator();

            // Default Global Sun Light Properties
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

        // 1. Node Header
        char name_buf[128];
        std::snprintf(name_buf, sizeof(name_buf), "%s", selected_node_->name.c_str());
        if (ImGui::InputText("Name", name_buf, sizeof(name_buf))) {
            selected_node_->name = name_buf;
        }

        char tag_buf[64];
        std::snprintf(tag_buf, sizeof(tag_buf), "%s", selected_node_->tag.c_str());
        if (ImGui::InputText("Tag", tag_buf, sizeof(tag_buf))) {
            selected_node_->tag = tag_buf;
        }

        ImGui::Checkbox("Visible", &selected_node_->visible);
        ImGui::SameLine();
        ImGui::Checkbox("Cast Shadows", &selected_node_->cast_shadows);
        ImGui::SameLine();
        ImGui::Checkbox("Receive", &selected_node_->receive_shadows);

        auto selected_ent = std::dynamic_pointer_cast<Entity>(selected_node_);
        if (selected_ent) {
            ImGui::SameLine();
            ImGui::Checkbox("Collision", &selected_ent->has_collision);
        }

        ImGui::Separator();

        // 2. Transform Section (Euler deg)
        if (ImGui::CollapsingHeader("Transform", ImGuiTreeNodeFlags_DefaultOpen)) {
            auto& t = selected_node_->transform;
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

            if (selected_ent && selected_ent->has_collision) {
                ImGui::SliderFloat("Collision Scale", &selected_ent->collision_scale, 0.1f, 2.0f, "%.2f");
            }
        }

        // 3. Material Controls
        if (selected_ent && (selected_ent->material || selected_ent->mesh)) {
            if (ImGui::CollapsingHeader("Material & Shading", ImGuiTreeNodeFlags_DefaultOpen)) {
                auto mat = selected_ent->material;
                if (mat) {
                    ImGui::ColorEdit4("Base Color", &mat->base_color.x);
                    ImGui::SliderFloat("Roughness", &mat->roughness, 0.0f, 1.0f);
                    ImGui::SliderFloat("Metallic", &mat->metallic, 0.0f, 1.0f);
                    ImGui::SliderFloat("Emissive Intensity", &mat->emissive_intensity, 0.0f, 20.0f);
                    ImGui::ColorEdit3("Emissive Color", &mat->emissive_color.x);
                    ImGui::DragFloat2("UV Scale", &mat->uv_scale.x, 0.1f, 0.1f, 50.0f);
                } else {
                    ImGui::ColorEdit4("Tint Color", &selected_ent->color.x);
                }
            }
        }

        // 4. Light Controls
        auto selected_light = std::dynamic_pointer_cast<Light>(selected_node_);
        if (selected_light) {
            if (ImGui::CollapsingHeader("Light Controls", ImGuiTreeNodeFlags_DefaultOpen)) {
                ImGui::ColorEdit3("Color", &selected_light->color.x);
                ImGui::DragFloat("Intensity", &selected_light->intensity, 0.05f, 0.0f, 100.0f);

                auto pt_light = std::dynamic_pointer_cast<PointLight>(selected_light);
                if (pt_light) {
                    ImGui::DragFloat("Range", &pt_light->range, 0.1f, 0.1f, 500.0f);
                    ImGui::DragFloat("Decay", &pt_light->decay, 0.05f, 0.0f, 5.0f);
                }

                auto sp_light = std::dynamic_pointer_cast<SpotLight>(selected_light);
                if (sp_light) {
                    ImGui::DragFloat("Range", &sp_light->range, 0.1f, 0.1f, 500.0f);
                    ImGui::SliderFloat("Cone Angle", &sp_light->outer_cone_angle, 0.01f, 1.57f);
                    ImGui::SliderFloat("Penumbra", &sp_light->penumbra, 0.0f, 1.0f);
                }
            }
        }

        // 5. AnimationMixer Controls
        if (ImGui::CollapsingHeader("Animation & Clips", ImGuiTreeNodeFlags_DefaultOpen)) {
            static bool anim_playing = true;
            static float crossfade_dur = 0.3f;
            static char clip_name_buf[64] = "Run";

            ImGui::InputText("Clip Target", clip_name_buf, sizeof(clip_name_buf));
            ImGui::SliderFloat("Crossfade (s)", &crossfade_dur, 0.05f, 2.0f);

            if (ImGui::Button("Play")) {
                anim_playing = true;
            }
            ImGui::SameLine();
            if (ImGui::Button("Pause")) {
                anim_playing = false;
            }
            ImGui::SameLine();
            if (ImGui::Button("Crossfade")) {
                // Crossfade clip
            }
            ImGui::SameLine();
            ImGui::Text(anim_playing ? "[Playing]" : "[Paused]");
        }

        // 6. Focus & Deselect Actions
        ImGui::Separator();
        if (ImGui::Button("Focus Camera")) {
            glm::vec3 wp = selected_node_->world_position();
            app_.camera().set_target(wp.x, wp.y, wp.z);
        }
        ImGui::SameLine();
        if (ImGui::Button("Deselect")) {
            selected_node_ = nullptr;
        }
    }
    ImGui::End();
}

void EditorManager::render_postprocess_panel() {
    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(10.0f, io.DisplaySize.y - 280.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(340.0f, 240.0f), ImGuiCond_FirstUseEver);

    if (ImGui::Begin("Post-Process & Render", &show_postprocess)) {
        // Sync with EffectComposer if present
        std::shared_ptr<BloomPass> bloom_pass = nullptr;
        std::shared_ptr<SSAOPass> ssao_pass = nullptr;
        std::shared_ptr<TonemappingPass> tonemap_pass = nullptr;

        auto composer = app_.composer();
        if (composer) {
            for (const auto& pass : composer->passes()) {
                if (!bloom_pass) bloom_pass = std::dynamic_pointer_cast<BloomPass>(pass);
                if (!ssao_pass) ssao_pass = std::dynamic_pointer_cast<SSAOPass>(pass);
                if (!tonemap_pass) tonemap_pass = std::dynamic_pointer_cast<TonemappingPass>(pass);
            }
        }

        // 1. Bloom Controls
        if (ImGui::CollapsingHeader("Bloom Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
            if (bloom_pass) {
                bloom_threshold_ = bloom_pass->threshold;
                bloom_strength_ = bloom_pass->strength;
                bloom_radius_ = bloom_pass->radius;
            }
            if (ImGui::SliderFloat("Bloom Threshold", &bloom_threshold_, 0.0f, 5.0f)) {
                if (bloom_pass) bloom_pass->threshold = bloom_threshold_;
            }
            if (ImGui::SliderFloat("Bloom Strength", &bloom_strength_, 0.0f, 10.0f)) {
                if (bloom_pass) bloom_pass->strength = bloom_strength_;
            }
            if (ImGui::SliderFloat("Bloom Radius", &bloom_radius_, 0.01f, 2.0f)) {
                if (bloom_pass) bloom_pass->radius = bloom_radius_;
            }
        }

        // 2. SSAO Controls
        if (ImGui::CollapsingHeader("SSAO Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
            if (ssao_pass) {
                ssao_radius_ = ssao_pass->radius;
                ssao_power_ = ssao_pass->power;
            }
            if (ImGui::SliderFloat("SSAO Radius", &ssao_radius_, 0.01f, 3.0f)) {
                if (ssao_pass) ssao_pass->radius = ssao_radius_;
            }
            if (ImGui::SliderFloat("SSAO Power", &ssao_power_, 0.1f, 5.0f)) {
                if (ssao_pass) ssao_pass->power = ssao_power_;
            }
        }

        // 3. Tonemapping Controls
        if (ImGui::CollapsingHeader("Tonemapping Settings", ImGuiTreeNodeFlags_DefaultOpen)) {
            if (tonemap_pass) {
                tonemap_exposure_ = tonemap_pass->exposure;
                tonemap_gamma_ = tonemap_pass->gamma;
                tonemap_mode_ = static_cast<int>(tonemap_pass->mode);
            }
            if (ImGui::SliderFloat("Exposure", &tonemap_exposure_, 0.1f, 10.0f)) {
                if (tonemap_pass) tonemap_pass->exposure = tonemap_exposure_;
            }
            if (ImGui::SliderFloat("Gamma", &tonemap_gamma_, 1.0f, 3.0f)) {
                if (tonemap_pass) tonemap_pass->gamma = tonemap_gamma_;
            }
            const char* modes[] = { "ACESFilmic", "Reinhard", "Cineon", "Linear", "Neutral" };
            if (ImGui::Combo("Mode", &tonemap_mode_, modes, IM_ARRAYSIZE(modes))) {
                if (tonemap_pass) tonemap_pass->mode = static_cast<TonemappingMode>(tonemap_mode_);
            }
        }

        ImGui::Separator();

        // 4. Save Scene to Script Button
        if (ImGui::Button("Save Scene to Python Script", ImVec2(-1, 30.0f))) {
            save_scene_to_script("exported_scene.py");
        }
    }
    ImGui::End();
}

bool EditorManager::save_scene_to_script(const std::string& filepath) {
    std::ofstream out(filepath);
    if (!out.is_open()) return false;

    out << "# Auto-generated by Pielosyty 3D Engine Editor\n";
    out << "import pielosyty as ve\n\n";
    out << "app = ve.EngineApp(\"Pielosyty Exported Scene\", " << app_.width() << ", " << app_.height() << ")\n";
    out << "scene = app.scene\n";
    out << "camera = app.camera\n\n";

    // Setup Sun Light
    auto& sun = app_.scene().light;
    out << "# Sun Light Setup\n";
    out << "scene.light.direction = ve.Vec3(" << sun.direction.x << ", " << sun.direction.y << ", " << sun.direction.z << ")\n";
    out << "scene.light.color = ve.Vec4(" << sun.color.x << ", " << sun.color.y << ", " << sun.color.z << ", 1.0)\n";
    out << "scene.light.intensity = " << sun.intensity << "\n\n";

    // Camera setup
    auto& cam = app_.camera();
    out << "# Camera Setup\n";
    out << "camera.position = ve.Vec3(" << cam.position.x << ", " << cam.position.y << ", " << cam.position.z << ")\n";
    out << "camera.fov = " << cam.fov << "\n\n";

    // Entities
    out << "# Scene Entities\n";
    int ent_idx = 1;
    for (const auto& ent : app_.scene().entities()) {
        if (!ent) continue;
        std::string var = "obj_" + std::to_string(ent_idx++);
        out << var << " = scene.create_box(ve.Vec3(1.0, 1.0, 1.0))\n";
        out << var << ".name = \"" << ent->name << "\"\n";
        out << var << ".transform.position = ve.Vec3(" << ent->transform.position.x << ", "
            << ent->transform.position.y << ", " << ent->transform.position.z << ")\n";
        glm::vec3 r = ent->transform.rotation();
        out << var << ".transform.rotation = ve.Vec3(" << r.x << ", " << r.y << ", " << r.z << ")\n";
        out << var << ".transform.scale = ve.Vec3(" << ent->transform.scale.x << ", "
            << ent->transform.scale.y << ", " << ent->transform.scale.z << ")\n";
        if (ent->material) {
            out << var << ".material.roughness = " << ent->material->roughness << "\n";
            out << var << ".material.metallic = " << ent->material->metallic << "\n";
        }
        out << "\n";
    }

    out << "if __name__ == \"__main__\":\n";
    out << "    app.run()\n";

    last_saved_script_path_ = filepath;
    save_notification_timer_ = 3.0f;
    return true;
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
    if (!selected_node_ || screen_w <= 0.0f || screen_h <= 0.0f) return;

    ImGuizmo::SetOrthographic(false);
    ImGuizmo::SetDrawlist(ImGui::GetForegroundDrawList());
    ImGuizmo::SetRect(0.0f, 0.0f, screen_w, screen_h);

    glm::mat4 view = app_.camera().view_matrix();
    glm::mat4 proj = app_.camera().projection_matrix();
    glm::mat4 model = selected_node_->transform.model_matrix();

    ImGuizmo::OPERATION op = ImGuizmo::TRANSLATE;
    if (gizmo_op_ == 1) op = ImGuizmo::ROTATE;
    else if (gizmo_op_ == 2) op = ImGuizmo::SCALE;

    if (ImGuizmo::Manipulate(glm::value_ptr(view), glm::value_ptr(proj),
                             op, ImGuizmo::WORLD, glm::value_ptr(model))) {
        float translation[3], rotation[3], scale[3];
        ImGuizmo::DecomposeMatrixToComponents(glm::value_ptr(model), translation, rotation, scale);
        selected_node_->transform.set_position(translation[0], translation[1], translation[2]);
        selected_node_->transform.set_rotation(rotation[0], rotation[1], rotation[2]);
        selected_node_->transform.set_scale(scale[0], scale[1], scale[2]);
    }
}

} // namespace engine
