#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <functional>
#include <glm/glm.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// 3D Event System Contracts
// ---------------------------------------------------------------------------
struct MouseRaycastEvent {
    glm::vec3 point{0.0f};
    glm::vec3 normal{0.0f, 1.0f, 0.0f};
    float distance{0.0f};
    std::shared_ptr<class Node3D> target{nullptr};
};

using EventCallback = std::function<void(const std::string&, void*)>;

} // namespace engine
