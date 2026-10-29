#pragma once

#include "engine/transform.hpp"
#include "engine/math_types.hpp"
#include "engine/physics.hpp"
#include "contracts/phase7_assets_editor_contracts.h"

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <algorithm>
#include <utility>
#include <unordered_map>

namespace engine {

class Node3D : public std::enable_shared_from_this<Node3D> {
public:
    uint64_t id{0};
    std::string uuid{};
    std::string name{};
    std::string tag{};
    bool visible{true};
    bool cast_shadows{true};
    bool receive_shadows{true};
    uint32_t layers{1}; // Bitmask, default layer 1

    Transform transform{};

    Node3D(const std::string& node_name = "Node3D");
    virtual ~Node3D();

    // Hierarchy
    Node3D* parent() const { return parent_; }
    const std::vector<std::shared_ptr<Node3D>>& children() const { return children_; }

    void add(std::shared_ptr<Node3D> child);
    void remove(std::shared_ptr<Node3D> child);
    void remove_from_parent();
    void clear();

    // Traversal
    void traverse(const std::function<void(Node3D&)>& callback);
    void traverse_visible(const std::function<void(Node3D&)>& callback);
    std::shared_ptr<Node3D> get_by_name(const std::string& target_name);
    std::vector<std::shared_ptr<Node3D>> find_all_by_tag(const std::string& target_tag);

    // Dirty flags & Invalidation
    void invalidate_world_matrix();
    void invalidate_local_matrix();

    // World Space Accessors
    const glm::mat4& world_matrix() const;
    glm::mat4 world_model_matrix() const { return world_matrix(); }
    glm::mat4 world_normal_matrix() const;
    glm::vec3 world_position() const;
    glm::quat world_orientation() const;
    glm::vec3 world_direction() const; // -Z axis transformed by world orientation
    glm::vec3 world_to_local(const glm::vec3& v) const;
    glm::vec3 local_to_world(const glm::vec3& v) const;

    virtual AABB world_aabb() const;
    std::pair<glm::vec3, glm::vec3> world_bounds() const {
        AABB b = world_aabb();
        return { b.min_point, b.max_point };
    }

    // Event System
    using EventCallback = std::function<void(const std::string&, void*)>;
    void on(const std::string& event_name, EventCallback callback);
    void emit(const std::string& event_name, void* data = nullptr);
    bool has_listener(const std::string& event_name) const;
    void off(const std::string& event_name);
    void clear_listeners();

protected:
    Node3D* parent_{nullptr};
    std::vector<std::shared_ptr<Node3D>> children_{};
    std::unordered_map<std::string, std::vector<EventCallback>> event_listeners_{};

    mutable bool local_matrix_dirty_{true};
    mutable bool world_matrix_dirty_{true};
    mutable glm::mat4 local_matrix_{1.0f};
    mutable glm::mat4 world_matrix_{1.0f};

    static std::string generate_uuid();
    static uint64_t next_global_id();
};

class Group : public Node3D {
public:
    Group(const std::string& group_name = "Group")
        : Node3D(group_name) {}
};

} // namespace engine
