#pragma once

#include "engine/node3d.hpp"
#include <vector>
#include <memory>
#include <string>

namespace engine {

struct LODLevel {
    std::shared_ptr<Node3D> node{nullptr};
    float distance{0.0f};
};

class LOD : public Node3D {
public:
    LOD(const std::string& name = "LOD");
    ~LOD() override = default;

    void add_level(std::shared_ptr<Node3D> node, float distance);
    size_t num_levels() const { return levels_.size(); }
    std::shared_ptr<Node3D> get_level(size_t index) const;
    int current_level_index() const { return current_level_index_; }

    void update_lod(const glm::vec3& camera_position);

    const std::vector<LODLevel>& levels() const { return levels_; }

private:
    std::vector<LODLevel> levels_;
    int current_level_index_{-1};
};

} // namespace engine
