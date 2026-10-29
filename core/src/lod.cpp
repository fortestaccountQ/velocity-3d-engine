#include "engine/lod.hpp"
#include <algorithm>

namespace engine {

LOD::LOD(const std::string& name) : Node3D(name) {}

void LOD::add_level(std::shared_ptr<Node3D> node, float distance) {
    if (!node) return;
    add(node);
    levels_.push_back({ node, distance });

    // Sort levels ascending by distance
    std::sort(levels_.begin(), levels_.end(), [](const LODLevel& a, const LODLevel& b) {
        return a.distance < b.distance;
    });

    // Default: level 0 visible, others hidden
    for (size_t i = 0; i < levels_.size(); ++i) {
        if (levels_[i].node) {
            levels_[i].node->visible = (i == 0);
        }
    }
    current_level_index_ = levels_.empty() ? -1 : 0;
}

std::shared_ptr<Node3D> LOD::get_level(size_t index) const {
    if (index < levels_.size()) {
        return levels_[index].node;
    }
    return nullptr;
}

void LOD::update_lod(const glm::vec3& camera_position) {
    if (levels_.empty()) return;

    float dist = glm::distance(world_position(), camera_position);

    int best_index = 0;
    for (size_t i = 0; i < levels_.size(); ++i) {
        if (dist >= levels_[i].distance) {
            best_index = static_cast<int>(i);
        }
    }

    current_level_index_ = best_index;
    for (size_t i = 0; i < levels_.size(); ++i) {
        if (levels_[i].node) {
            levels_[i].node->visible = (static_cast<int>(i) == best_index);
        }
    }
}

} // namespace engine
