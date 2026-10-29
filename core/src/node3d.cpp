#include "engine/node3d.hpp"
#include <atomic>
#include <random>
#include <sstream>
#include <iomanip>

namespace engine {

static std::atomic<uint64_t> s_global_node_id{1};

uint64_t Node3D::next_global_id() {
    return s_global_node_id.fetch_add(1, std::memory_order_relaxed);
}

std::string Node3D::generate_uuid() {
    static thread_local std::mt19937_64 rng(std::random_device{}());
    static thread_local std::uniform_int_distribution<uint64_t> dist;

    uint64_t part1 = dist(rng);
    uint64_t part2 = dist(rng);

    // RFC 4122 v4 UUID format: 8-4-4-4-12 hex digits
    std::ostringstream oss;
    oss << std::hex << std::setfill('0')
        << std::setw(8) << (part1 >> 32) << "-"
        << std::setw(4) << ((part1 >> 16) & 0xFFFF) << "-"
        << std::setw(4) << ((part1 & 0x0FFF) | 0x4000) << "-" // Version 4
        << std::setw(4) << (((part2 >> 48) & 0x3FFF) | 0x8000) << "-" // Variant 1
        << std::setw(12) << (part2 & 0xFFFFFFFFFFFFULL);
    return oss.str();
}

Node3D::Node3D(const std::string& node_name)
    : id(next_global_id()), uuid(generate_uuid()), name(node_name) {}

Node3D::~Node3D() {
    clear();
    remove_from_parent();
}

void Node3D::add(std::shared_ptr<Node3D> child) {
    if (!child || child.get() == this) return;

    // Cycle check: verify child is not an ancestor of this
    Node3D* curr = this;
    while (curr) {
        if (curr == child.get()) {
            return; // Prevent cyclic dependency
        }
        curr = curr->parent_;
    }

    // Unparent from previous parent if any
    if (child->parent_) {
        child->parent_->remove(child);
    }

    // Check if already in children
    for (const auto& c : children_) {
        if (c == child) return;
    }

    child->parent_ = this;
    children_.push_back(child);
    child->invalidate_world_matrix();
}

void Node3D::remove(std::shared_ptr<Node3D> child) {
    if (!child) return;

    auto it = std::find(children_.begin(), children_.end(), child);
    if (it != children_.end()) {
        (*it)->parent_ = nullptr;
        (*it)->invalidate_world_matrix();
        children_.erase(it);
    }
}

void Node3D::remove_from_parent() {
    if (parent_) {
        Node3D* p = parent_;
        parent_ = nullptr;
        invalidate_world_matrix();
        for (auto it = p->children_.begin(); it != p->children_.end(); ++it) {
            if (it->get() == this) {
                p->children_.erase(it);
                break;
            }
        }
    }
}

void Node3D::clear() {
    for (auto& child : children_) {
        if (child) {
            child->parent_ = nullptr;
            child->invalidate_world_matrix();
        }
    }
    children_.clear();
}

void Node3D::traverse(const std::function<void(Node3D&)>& callback) {
    callback(*this);
    for (auto& child : children_) {
        if (child) {
            child->traverse(callback);
        }
    }
}

void Node3D::traverse_visible(const std::function<void(Node3D&)>& callback) {
    if (!visible) return;
    callback(*this);
    for (auto& child : children_) {
        if (child && child->visible) {
            child->traverse_visible(callback);
        }
    }
}

std::shared_ptr<Node3D> Node3D::get_by_name(const std::string& target_name) {
    if (name == target_name) {
        return shared_from_this();
    }
    for (auto& child : children_) {
        if (child) {
            auto found = child->get_by_name(target_name);
            if (found) return found;
        }
    }
    return nullptr;
}

std::vector<std::shared_ptr<Node3D>> Node3D::find_all_by_tag(const std::string& target_tag) {
    std::vector<std::shared_ptr<Node3D>> result;
    traverse([&](Node3D& node) {
        if (node.tag == target_tag) {
            result.push_back(node.shared_from_this());
        }
    });
    return result;
}

void Node3D::invalidate_world_matrix() {
    world_matrix_dirty_ = true;
    for (auto& child : children_) {
        if (child) {
            child->invalidate_world_matrix();
        }
    }
}

void Node3D::invalidate_local_matrix() {
    local_matrix_dirty_ = true;
    invalidate_world_matrix();
}

const glm::mat4& Node3D::world_matrix() const {
    glm::mat4 local = transform.model_matrix();
    if (parent_) {
        world_matrix_ = parent_->world_matrix() * local;
    } else {
        world_matrix_ = local;
    }
    world_matrix_dirty_ = false;
    return world_matrix_;
}

glm::mat4 Node3D::world_normal_matrix() const {
    glm::mat3 m3(world_matrix());
    return glm::mat4(glm::transpose(glm::inverse(m3)));
}

glm::vec3 Node3D::world_position() const {
    return glm::vec3(world_matrix()[3]);
}

glm::quat Node3D::world_orientation() const {
    glm::mat3 m3(world_matrix());
    float lx = glm::length(m3[0]);
    float ly = glm::length(m3[1]);
    float lz = glm::length(m3[2]);
    if (lx > 1e-6f) m3[0] /= lx;
    if (ly > 1e-6f) m3[1] /= ly;
    if (lz > 1e-6f) m3[2] /= lz;
    return glm::normalize(glm::quat_cast(m3));
}

glm::vec3 Node3D::world_direction() const {
    return world_orientation() * glm::vec3(0.0f, 0.0f, -1.0f);
}

glm::vec3 Node3D::world_to_local(const glm::vec3& v) const {
    return glm::vec3(glm::inverse(world_matrix()) * glm::vec4(v, 1.0f));
}

glm::vec3 Node3D::local_to_world(const glm::vec3& v) const {
    return glm::vec3(world_matrix() * glm::vec4(v, 1.0f));
}

AABB Node3D::world_aabb() const {
    return AABB{ world_position(), world_position() };
}

void Node3D::on(const std::string& event_name, EventCallback callback) {
    if (callback) {
        event_listeners_[event_name].push_back(std::move(callback));
    }
}

void Node3D::emit(const std::string& event_name, void* data) {
    auto it = event_listeners_.find(event_name);
    if (it != event_listeners_.end()) {
        auto callbacks = it->second;
        for (const auto& cb : callbacks) {
            if (cb) {
                cb(event_name, data);
            }
        }
    }
}

bool Node3D::has_listener(const std::string& event_name) const {
    auto it = event_listeners_.find(event_name);
    return (it != event_listeners_.end() && !it->second.empty());
}

void Node3D::off(const std::string& event_name) {
    event_listeners_.erase(event_name);
}

void Node3D::clear_listeners() {
    event_listeners_.clear();
}

} // namespace engine
