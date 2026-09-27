#pragma once

#include "engine/transform.hpp"
#include "engine/mesh.hpp"
#include <string>
#include <memory>

namespace engine {

class Entity {
public:
    uint32_t id{0};
    std::string name{"Entity"};
    Transform transform;
    std::shared_ptr<Mesh> mesh{nullptr};
    glm::vec4 color{1.0f, 1.0f, 1.0f, 1.0f};
    bool visible{true};

    Entity(uint32_t id, const std::string& name = "Entity")
        : id(id), name(name) {}

    void set_color(float r, float g, float b, float a = 1.0f) {
        color = { r, g, b, a };
    }
};

} // namespace engine
