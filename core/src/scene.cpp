#include "engine/scene.hpp"

#include <algorithm>

namespace engine {

std::shared_ptr<Mesh> Scene::default_cube_mesh() {
    if (!default_cube_mesh_) {
        default_cube_mesh_ = Mesh::create_cube();
    }
    return default_cube_mesh_;
}

std::shared_ptr<Entity> Scene::create_entity(const std::string& name) {
    auto entity = std::make_shared<Entity>(next_id_++, name);
    entities_.push_back(entity);
    return entity;
}

std::shared_ptr<Entity> Scene::create_cube(const glm::vec4& color) {
    auto entity = create_entity("Cube_" + std::to_string(next_id_));
    entity->color = color;
    // Default cube mesh will be attached automatically when rendering starts
    return entity;
}

void Scene::add_entity(std::shared_ptr<Entity> entity) {
    if (entity) {
        entities_.push_back(entity);
    }
}

void Scene::remove_entity(std::shared_ptr<Entity> entity) {
    auto it = std::remove(entities_.begin(), entities_.end(), entity);
    entities_.erase(it, entities_.end());
}

void Scene::clear() {
    entities_.clear();
    if (default_cube_mesh_) {
        default_cube_mesh_->destroy();
        default_cube_mesh_ = nullptr;
    }
}

} // namespace engine
