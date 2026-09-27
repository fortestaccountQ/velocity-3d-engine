#pragma once

#include "engine/entity.hpp"
#include "engine/light.hpp"
#include "engine/texture.hpp"
#include "engine/material.hpp"
#include "engine/model.hpp"
#include <vector>
#include <memory>

namespace engine {

class Scene {
public:
    DirectionalLight light;

    Scene() = default;

    std::shared_ptr<Model> load_model(const std::string& filepath);
    std::shared_ptr<Entity> create_cube(const glm::vec4& color = glm::vec4(1.0f));
    std::shared_ptr<Entity> create_plane(float size = 10.0f, float uv_tiling = 5.0f, std::shared_ptr<Material> material = nullptr);
    std::shared_ptr<Entity> create_entity(const std::string& name = "Entity");

    void add_entity(std::shared_ptr<Entity> entity);
    void remove_entity(std::shared_ptr<Entity> entity);
    void clear();

    RaycastHit raycast(const Ray& ray, float max_distance = 1000.0f) const;

    const std::vector<std::shared_ptr<Entity>>& entities() const { return entities_; }
    std::shared_ptr<Mesh> default_cube_mesh();
    std::shared_ptr<Texture> default_checker_texture();
    std::shared_ptr<Material> default_material();

private:
    std::vector<std::shared_ptr<Entity>> entities_;
    uint32_t next_id_{1};
    std::shared_ptr<Mesh> default_cube_mesh_{nullptr};
    std::shared_ptr<Texture> default_checker_texture_{nullptr};
    std::shared_ptr<Material> default_material_{nullptr};
};

} // namespace engine
