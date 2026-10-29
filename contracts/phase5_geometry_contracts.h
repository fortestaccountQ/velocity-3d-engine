#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <glm/glm.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// Curve3 Interface Contract
// ---------------------------------------------------------------------------
struct FrenetFrames {
    std::vector<glm::vec3> tangents;
    std::vector<glm::vec3> normals;
    std::vector<glm::vec3> binormals;
};

// ---------------------------------------------------------------------------
// LOD Level Entry Contract
// ---------------------------------------------------------------------------
struct LODLevel {
    float distance{0.0f};
    std::shared_ptr<class Node3D> node{nullptr};
};

} // namespace engine
