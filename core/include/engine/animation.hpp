#pragma once

#include "engine/node3d.hpp"
#include "engine/helpers.hpp"
#include <glm/glm.hpp>
#include <glm/gtc/quaternion.hpp>
#include <string>
#include <vector>
#include <memory>
#include <unordered_map>

namespace engine {

class Bone : public Node3D {
public:
    int bone_index{-1};

    Bone(const std::string& name = "Bone", int index = -1)
        : Node3D(name), bone_index(index) {}

    int get_bone_index() const { return bone_index; }
    void set_bone_index(int idx) { bone_index = idx; }
};

struct alignas(16) BoneUBO {
    glm::mat4 bone_matrices[128];
};

class Skeleton {
public:
    std::vector<std::shared_ptr<Bone>> bones;
    std::vector<glm::mat4> inverse_bind_matrices;
    std::vector<glm::mat4> bone_matrices;

    Skeleton() = default;
    Skeleton(const std::vector<std::shared_ptr<Bone>>& bone_list,
             const std::vector<glm::mat4>& inv_bind_matrices = {});

    void calculate_inverse_bind_matrices();
    void compute_bone_matrices(const glm::mat4& root_inv_world = glm::mat4(1.0f));
    void update(const glm::mat4& root_inv_world = glm::mat4(1.0f));
    void pose();

    std::shared_ptr<Bone> get_bone_by_name(const std::string& name) const;
    std::shared_ptr<Bone> get_bone_by_index(int index) const;

    size_t num_bones() const { return bones.size(); }
    const std::vector<std::shared_ptr<Bone>>& get_bones() const { return bones; }
    std::vector<std::shared_ptr<Bone>>& get_bones() { return bones; }
    const std::vector<glm::mat4>& get_bone_matrices() const { return bone_matrices; }
};

enum class Interpolation {
    Linear = 0,
    Step = 1,
    CubicSpline = 2
};

enum class PropertyType {
    Translation = 0,
    Rotation = 1,
    Scale = 2
};

struct KeyframeTrack {
    std::string name; // target bone or node name
    std::string property_name{"translation"}; // "translation", "rotation", "scale"
    PropertyType property{PropertyType::Translation};
    std::vector<float> times;
    std::vector<float> values;
    Interpolation interpolation{Interpolation::Linear};

    KeyframeTrack() = default;
    KeyframeTrack(const std::string& target_name,
                  const std::string& prop,
                  const std::vector<float>& track_times,
                  const std::vector<float>& track_values,
                  Interpolation interp = Interpolation::Linear);

    glm::vec3 sample_vec3(float time) const;
    glm::quat sample_quat(float time) const;
    glm::vec3 sample_translation(float time) const { return sample_vec3(time); }
    glm::quat sample_rotation(float time) const { return sample_quat(time); }
    glm::vec3 sample_scale(float time) const { return sample_vec3(time); }
};

class AnimationClip {
public:
    std::string name;
    float duration{0.0f};
    std::vector<KeyframeTrack> tracks;

    AnimationClip(const std::string& clip_name = "", float clip_duration = 0.0f)
        : name(clip_name), duration(clip_duration) {}

    void add_track(const KeyframeTrack& track);
    const KeyframeTrack* find_track(const std::string& node_name, const std::string& prop) const;
    void reset_duration_from_tracks();
};

class AnimationAction : public std::enable_shared_from_this<AnimationAction> {
public:
    std::shared_ptr<AnimationClip> clip{nullptr};
    std::string name;
    float time{0.0f};
    float time_scale{1.0f};
    float weight{1.0f};
    bool is_running{false};
    bool loop{true};
    bool paused{false};

    float fade_duration{0.0f};
    float fade_time{0.0f};
    float fade_start_weight{1.0f};
    float fade_target_weight{1.0f};
    bool is_fading{false};

    AnimationAction(std::shared_ptr<AnimationClip> anim_clip = nullptr);

    void play();
    void stop();
    void pause();
    void resume();
    void reset();
    void set_time_scale(float speed) { time_scale = speed; }
    void set_weight(float w) { weight = w; }
    void set_loop(bool l) { loop = l; }

    void crossfade_to(std::shared_ptr<AnimationAction> target_action, float duration = 0.3f);
    void fade_in(float duration);
    void fade_out(float duration);
    void update_fading(float dt);
};

class AnimationMixer {
public:
    std::shared_ptr<Node3D> root{nullptr};
    std::unordered_map<std::string, std::shared_ptr<AnimationAction>> actions;

    AnimationMixer(std::shared_ptr<Node3D> root_node = nullptr);

    std::shared_ptr<AnimationAction> clip_action(std::shared_ptr<AnimationClip> clip);
    std::shared_ptr<AnimationAction> clip_action(const std::string& clip_name);
    void play(const std::string& clip_name);
    void stop(const std::string& clip_name);
    void stop_all_action();
    void crossfade_to(const std::string& target_clip, float duration = 0.3f);
    void update(float dt);

    std::shared_ptr<AnimationAction> get_action(const std::string& clip_name) const;
    const std::unordered_map<std::string, std::shared_ptr<AnimationAction>>& get_actions() const { return actions; }
};

class SkeletonHelper : public Helper {
public:
    std::shared_ptr<Node3D> root_node{nullptr};
    std::shared_ptr<Skeleton> skeleton{nullptr};
    glm::vec4 bone_color{0.2f, 1.0f, 0.2f, 1.0f};

    SkeletonHelper(std::shared_ptr<Node3D> root = nullptr,
                   std::shared_ptr<Skeleton> skel = nullptr,
                   const glm::vec4& color = glm::vec4(0.2f, 1.0f, 0.2f, 1.0f));

    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

} // namespace engine
