#include "engine/animation.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>

namespace engine {

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------
Skeleton::Skeleton(const std::vector<std::shared_ptr<Bone>>& bone_list,
                   const std::vector<glm::mat4>& inv_bind_matrices)
    : bones(bone_list), inverse_bind_matrices(inv_bind_matrices) {
    if (inverse_bind_matrices.size() < bones.size()) {
        inverse_bind_matrices.resize(bones.size(), glm::mat4(1.0f));
    }
    bone_matrices.resize(bones.size(), glm::mat4(1.0f));
    compute_bone_matrices();
}

void Skeleton::calculate_inverse_bind_matrices() {
    inverse_bind_matrices.resize(bones.size(), glm::mat4(1.0f));
    for (size_t i = 0; i < bones.size(); ++i) {
        if (bones[i]) {
            inverse_bind_matrices[i] = glm::inverse(bones[i]->world_matrix());
        }
    }
}

void Skeleton::compute_bone_matrices(const glm::mat4& root_inv_world) {
    if (bone_matrices.size() != bones.size()) {
        bone_matrices.resize(bones.size(), glm::mat4(1.0f));
    }
    for (size_t i = 0; i < bones.size(); ++i) {
        if (bones[i]) {
            glm::mat4 inv_bind = (i < inverse_bind_matrices.size()) ? inverse_bind_matrices[i] : glm::mat4(1.0f);
            bone_matrices[i] = root_inv_world * bones[i]->world_matrix() * inv_bind;
        } else {
            bone_matrices[i] = glm::mat4(1.0f);
        }
    }
}

void Skeleton::update(const glm::mat4& root_inv_world) {
    compute_bone_matrices(root_inv_world);
}

void Skeleton::pose() {
    compute_bone_matrices();
}

std::shared_ptr<Bone> Skeleton::get_bone_by_name(const std::string& name) const {
    for (const auto& b : bones) {
        if (b && b->name == name) {
            return b;
        }
    }
    return nullptr;
}

std::shared_ptr<Bone> Skeleton::get_bone_by_index(int index) const {
    if (index >= 0 && index < static_cast<int>(bones.size())) {
        return bones[index];
    }
    for (const auto& b : bones) {
        if (b && b->bone_index == index) {
            return b;
        }
    }
    return nullptr;
}

// ---------------------------------------------------------------------------
// KeyframeTrack
// ---------------------------------------------------------------------------
KeyframeTrack::KeyframeTrack(const std::string& target_name,
                             const std::string& prop,
                             const std::vector<float>& track_times,
                             const std::vector<float>& track_values,
                             Interpolation interp)
    : name(target_name), property_name(prop), times(track_times), values(track_values), interpolation(interp) {
    if (prop == "rotation" || prop == "quaternion") {
        property = PropertyType::Rotation;
    } else if (prop == "scale") {
        property = PropertyType::Scale;
    } else {
        property = PropertyType::Translation;
    }
}

glm::vec3 KeyframeTrack::sample_vec3(float time) const {
    if (times.empty() || values.empty()) {
        return glm::vec3(0.0f);
    }

    size_t n = times.size();
    bool is_cubic = (interpolation == Interpolation::CubicSpline) && (values.size() >= n * 9);
    size_t stride = is_cubic ? 9 : 3;

    if (time <= times[0] || n == 1) {
        size_t offset = is_cubic ? 3 : 0;
        return glm::vec3(values[offset], values[offset + 1], values[offset + 2]);
    }
    if (time >= times.back()) {
        size_t last_idx = n - 1;
        size_t offset = is_cubic ? (last_idx * 9 + 3) : (last_idx * 3);
        return glm::vec3(values[offset], values[offset + 1], values[offset + 2]);
    }

    // Binary search
    auto it = std::upper_bound(times.begin(), times.end(), time);
    size_t k1 = static_cast<size_t>(std::distance(times.begin(), it));
    size_t k0 = k1 - 1;

    float t0 = times[k0];
    float t1 = times[k1];
    float dt = t1 - t0;
    float alpha = (dt > 1e-6f) ? ((time - t0) / dt) : 0.0f;

    if (interpolation == Interpolation::Step) {
        size_t off = is_cubic ? (k0 * 9 + 3) : (k0 * 3);
        return glm::vec3(values[off], values[off + 1], values[off + 2]);
    }

    if (is_cubic) {
        // Hermite spline: [in-tangent, value, out-tangent]
        size_t off0 = k0 * 9;
        size_t off1 = k1 * 9;
        glm::vec3 p0(values[off0 + 3], values[off0 + 4], values[off0 + 5]);
        glm::vec3 m0(values[off0 + 6], values[off0 + 7], values[off0 + 8]);
        glm::vec3 m1(values[off1 + 0], values[off1 + 1], values[off1 + 2]);
        glm::vec3 p1(values[off1 + 3], values[off1 + 4], values[off1 + 5]);

        float a2 = alpha * alpha;
        float a3 = a2 * alpha;
        return (2.0f * a3 - 3.0f * a2 + 1.0f) * p0 +
               dt * (a3 - 2.0f * a2 + alpha) * m0 +
               (-2.0f * a3 + 3.0f * a2) * p1 +
               dt * (a3 - a2) * m1;
    }

    size_t off0 = k0 * 3;
    size_t off1 = k1 * 3;
    glm::vec3 v0(values[off0], values[off0 + 1], values[off0 + 2]);
    glm::vec3 v1(values[off1], values[off1 + 1], values[off1 + 2]);
    return glm::mix(v0, v1, alpha);
}

glm::quat KeyframeTrack::sample_quat(float time) const {
    if (times.empty() || values.empty()) {
        return glm::quat(1.0f, 0.0f, 0.0f, 0.0f);
    }

    size_t n = times.size();
    bool is_cubic = (interpolation == Interpolation::CubicSpline) && (values.size() >= n * 12);

    auto make_quat = [&](size_t offset) -> glm::quat {
        // glTF quaternion order: x, y, z, w -> glm::quat(w, x, y, z)
        return glm::normalize(glm::quat(values[offset + 3], values[offset + 0], values[offset + 1], values[offset + 2]));
    };

    if (time <= times[0] || n == 1) {
        size_t offset = is_cubic ? 4 : 0;
        return make_quat(offset);
    }
    if (time >= times.back()) {
        size_t last_idx = n - 1;
        size_t offset = is_cubic ? (last_idx * 12 + 4) : (last_idx * 4);
        return make_quat(offset);
    }

    auto it = std::upper_bound(times.begin(), times.end(), time);
    size_t k1 = static_cast<size_t>(std::distance(times.begin(), it));
    size_t k0 = k1 - 1;

    float t0 = times[k0];
    float t1 = times[k1];
    float dt = t1 - t0;
    float alpha = (dt > 1e-6f) ? ((time - t0) / dt) : 0.0f;

    if (interpolation == Interpolation::Step) {
        size_t off = is_cubic ? (k0 * 12 + 4) : (k0 * 4);
        return make_quat(off);
    }

    size_t off0 = is_cubic ? (k0 * 12 + 4) : (k0 * 4);
    size_t off1 = is_cubic ? (k1 * 12 + 4) : (k1 * 4);
    glm::quat q0 = make_quat(off0);
    glm::quat q1 = make_quat(off1);
    return glm::slerp(q0, q1, alpha);
}

// ---------------------------------------------------------------------------
// AnimationClip
// ---------------------------------------------------------------------------
void AnimationClip::add_track(const KeyframeTrack& track) {
    tracks.push_back(track);
    if (!track.times.empty()) {
        duration = std::max(duration, track.times.back());
    }
}

const KeyframeTrack* AnimationClip::find_track(const std::string& node_name, const std::string& prop) const {
    for (const auto& trk : tracks) {
        if (trk.name == node_name && trk.property_name == prop) {
            return &trk;
        }
    }
    return nullptr;
}

void AnimationClip::reset_duration_from_tracks() {
    duration = 0.0f;
    for (const auto& trk : tracks) {
        if (!trk.times.empty()) {
            duration = std::max(duration, trk.times.back());
        }
    }
}

// ---------------------------------------------------------------------------
// AnimationAction
// ---------------------------------------------------------------------------
AnimationAction::AnimationAction(std::shared_ptr<AnimationClip> anim_clip)
    : clip(anim_clip) {
    if (clip) {
        name = clip->name;
    }
}

void AnimationAction::play() {
    is_running = true;
    paused = false;
}

void AnimationAction::stop() {
    is_running = false;
    paused = false;
    time = 0.0f;
    is_fading = false;
}

void AnimationAction::pause() {
    paused = true;
}

void AnimationAction::resume() {
    paused = false;
}

void AnimationAction::reset() {
    time = 0.0f;
}

void AnimationAction::fade_in(float duration) {
    fade_duration = std::max(0.001f, duration);
    fade_time = 0.0f;
    if (!is_running || weight >= 1.0f) {
        weight = 0.0f;
    }
    fade_start_weight = weight;
    fade_target_weight = 1.0f;
    is_fading = true;
    play();
}

void AnimationAction::fade_out(float duration) {
    fade_duration = std::max(0.001f, duration);
    fade_time = 0.0f;
    fade_start_weight = weight;
    fade_target_weight = 0.0f;
    is_fading = true;
}

void AnimationAction::crossfade_to(std::shared_ptr<AnimationAction> target_action, float duration) {
    fade_out(duration);
    if (target_action) {
        target_action->fade_in(duration);
    }
}

void AnimationAction::update_fading(float dt) {
    if (!is_fading) return;
    fade_time += dt;
    float t = std::min(1.0f, fade_time / fade_duration);
    weight = glm::mix(fade_start_weight, fade_target_weight, t);
    if (t >= 1.0f) {
        is_fading = false;
        if (fade_target_weight <= 0.0f) {
            is_running = false;
        }
    }
}

// ---------------------------------------------------------------------------
// AnimationMixer
// ---------------------------------------------------------------------------
AnimationMixer::AnimationMixer(std::shared_ptr<Node3D> root_node)
    : root(root_node) {}

std::shared_ptr<AnimationAction> AnimationMixer::clip_action(std::shared_ptr<AnimationClip> clip) {
    if (!clip) return nullptr;
    auto it = actions.find(clip->name);
    if (it != actions.end()) {
        return it->second;
    }
    auto action = std::make_shared<AnimationAction>(clip);
    actions[clip->name] = action;
    return action;
}

std::shared_ptr<AnimationAction> AnimationMixer::clip_action(const std::string& clip_name) {
    auto it = actions.find(clip_name);
    if (it != actions.end()) {
        return it->second;
    }
    auto clip = std::make_shared<AnimationClip>(clip_name);
    auto action = std::make_shared<AnimationAction>(clip);
    actions[clip_name] = action;
    return action;
}

void AnimationMixer::play(const std::string& clip_name) {
    auto it = actions.find(clip_name);
    if (it != actions.end() && it->second) {
        it->second->play();
    }
}

void AnimationMixer::stop(const std::string& clip_name) {
    auto it = actions.find(clip_name);
    if (it != actions.end() && it->second) {
        it->second->stop();
    }
}

void AnimationMixer::stop_all_action() {
    for (auto& [_, action] : actions) {
        if (action) {
            action->stop();
        }
    }
}

void AnimationMixer::crossfade_to(const std::string& target_clip, float duration) {
    std::shared_ptr<AnimationAction> target = nullptr;
    auto it = actions.find(target_clip);
    if (it != actions.end()) {
        target = it->second;
    }
    for (auto& [_, act] : actions) {
        if (act && act->is_running && act != target) {
            act->fade_out(duration);
        }
    }
    if (target) {
        target->fade_in(duration);
    }
}

std::shared_ptr<AnimationAction> AnimationMixer::get_action(const std::string& clip_name) const {
    auto it = actions.find(clip_name);
    if (it != actions.end()) {
        return it->second;
    }
    return nullptr;
}

void AnimationMixer::update(float dt) {
    if (!root) return;

    struct NodeTransformAccum {
        glm::vec3 translation{0.0f};
        float t_weight{0.0f};
        glm::vec3 scale{0.0f};
        float s_weight{0.0f};
        glm::quat rotation{1.0f, 0.0f, 0.0f, 0.0f};
        float r_weight{0.0f};
    };

    std::unordered_map<std::string, NodeTransformAccum> accum_map;

    for (auto& [_, action] : actions) {
        if (!action || !action->is_running || action->paused || !action->clip) continue;

        action->update_fading(dt);
        action->time += dt * action->time_scale;

        float clip_dur = action->clip->duration;
        if (clip_dur > 0.0f) {
            if (action->loop) {
                action->time = std::fmod(action->time, clip_dur);
                if (action->time < 0.0f) action->time += clip_dur;
            } else if (action->time > clip_dur) {
                action->time = clip_dur;
                action->is_running = false;
            }
        }

        float w = action->weight;
        if (w <= 0.0f) continue;

        for (const auto& track : action->clip->tracks) {
            auto& acc = accum_map[track.name];
            if (track.property == PropertyType::Translation) {
                acc.translation += track.sample_vec3(action->time) * w;
                acc.t_weight += w;
            } else if (track.property == PropertyType::Scale) {
                acc.scale += track.sample_vec3(action->time) * w;
                acc.s_weight += w;
            } else if (track.property == PropertyType::Rotation) {
                glm::quat q = track.sample_quat(action->time);
                if (acc.r_weight <= 0.0f) {
                    acc.rotation = q;
                } else {
                    float blend_factor = w / (acc.r_weight + w);
                    acc.rotation = glm::slerp(acc.rotation, q, blend_factor);
                }
                acc.r_weight += w;
            }
        }
    }

    for (const auto& [name, acc] : accum_map) {
        std::string target_name = name;
        auto dot_pos = name.find('.');
        if (dot_pos != std::string::npos) {
            target_name = name.substr(0, dot_pos);
        }
        std::shared_ptr<Node3D> node = nullptr;
        if (root->name == target_name) {
            node = root;
        } else {
            node = root->get_by_name(target_name);
        }
        if (!node) continue;

        if (acc.t_weight > 0.0001f) {
            node->transform.position = acc.translation / acc.t_weight;
        }
        if (acc.s_weight > 0.0001f) {
            node->transform.scale = acc.scale / acc.s_weight;
        }
        if (acc.r_weight > 0.0001f) {
            node->transform.set_orientation(glm::normalize(acc.rotation));
        }
        node->invalidate_local_matrix();
    }
}

// ---------------------------------------------------------------------------
// SkeletonHelper
// ---------------------------------------------------------------------------
SkeletonHelper::SkeletonHelper(std::shared_ptr<Node3D> root,
                               std::shared_ptr<Skeleton> skel,
                               const glm::vec4& color)
    : Helper("SkeletonHelper"), root_node(root), skeleton(skel), bone_color(color) {}

void SkeletonHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (skeleton) {
        for (const auto& bone : skeleton->bones) {
            if (!bone) continue;
            auto p = bone->parent();
            if (p) {
                out_verts.push_back({ p->world_position(), bone_color });
                out_verts.push_back({ bone->world_position(), bone_color });
            }
        }
    } else if (root_node) {
        std::function<void(const std::shared_ptr<Node3D>&)> recurse = [&](const std::shared_ptr<Node3D>& n) {
            if (!n) return;
            for (const auto& child : n->children()) {
                if (child) {
                    out_verts.push_back({ n->world_position(), bone_color });
                    out_verts.push_back({ child->world_position(), bone_color });
                    recurse(child);
                }
            }
        };
        recurse(root_node);
    }
}

} // namespace engine
