#pragma once

#include "engine/entity.hpp"
#include "engine/light.hpp"
#include <vector>
#include <memory>

namespace engine {

class Scene {
public:
    DirectionalLight light;

    Scene() = default;

    std::shared_ptr<Entity> create_cube(const glm::vec4& color = glm::vec4(1.0f));
    std::shared_ptr<Entity> create_entity(const std::string& name = "Entity");

    void add_entity(std::shared_ptr<Entity> entity);
    void remove_entity(std::shared_ptr<Entity> entity);
    void clear();

    const std::vector<std::shared_ptr<Entity>>& entities() const { return entities_; }
    std::shared_ptr<Mesh> default_cube_mesh();

private:
    std::vector<std::shared_ptr<Entity>> entities_;
    uint32_t next_id_{1};
    std::shared_ptr<Mesh> default_cube_mesh_{nullptr};
};

} // namespace engine
