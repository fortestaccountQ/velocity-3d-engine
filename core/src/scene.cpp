#include "engine/scene.hpp"

#include <algorithm>

namespace engine {

std::shared_ptr<Mesh> Scene::default_cube_mesh() {
    if (!default_cube_mesh_) {
        default_cube_mesh_ = Mesh::create_cube();
    }
    return default_cube_mesh_;
}

std::shared_ptr<Texture> Scene::default_checker_texture() {
    if (!default_checker_texture_) {
        default_checker_texture_ = Texture::create_checkerboard();
    }
    return default_checker_texture_;
}

std::shared_ptr<Material> Scene::default_material() {
    if (!default_material_) {
        default_material_ = std::make_shared<Material>(default_checker_texture(), 0.5f, 0.0f);
    }
    return default_material_;
}

std::shared_ptr<Entity> Scene::create_entity(const std::string& name) {
    auto entity = std::make_shared<Entity>(next_id_++, name);
    entities_.push_back(entity);
    return entity;
}

std::shared_ptr<Entity> Scene::create_cube(const glm::vec4& color) {
    auto entity = create_entity("Cube_" + std::to_string(next_id_));
    entity->color = color;
    entity->material = std::make_shared<Material>(default_checker_texture(), 0.5f, 0.0f);
    entity->material->base_color = color;
    return entity;
}

std::shared_ptr<Entity> Scene::create_plane(float size, float uv_tiling, std::shared_ptr<Material> material) {
    auto entity = create_entity("Plane_" + std::to_string(next_id_));
    entity->mesh = Mesh::create_plane(size, uv_tiling);
    if (!material) {
        material = std::make_shared<Material>(default_checker_texture(), 0.8f, 0.0f);
        material->base_color = glm::vec4(0.85f, 0.85f, 0.90f, 1.0f);
    }
    entity->material = material;
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
    if (default_checker_texture_) {
        default_checker_texture_->destroy();
        default_checker_texture_ = nullptr;
    }
    default_material_ = nullptr;
}

} // namespace engine
