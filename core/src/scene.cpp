#include "engine/scene.hpp"
#include "engine/model_loader.hpp"

#include <algorithm>

namespace engine {

std::shared_ptr<Model> Scene::load_model(const std::string& filepath) {
    return ModelLoader::load_model(*this, filepath);
}

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

std::shared_ptr<Texture> Scene::default_white_texture() {
    if (!default_white_texture_) {
        default_white_texture_ = Texture::create_solid_color(255, 255, 255, 255);
    }
    return default_white_texture_;
}

std::shared_ptr<Material> Scene::default_material() {
    if (!default_material_) {
        default_material_ = std::make_shared<Material>(default_white_texture(), 0.5f, 0.0f);
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
    entity->mesh = default_cube_mesh();
    entity->color = color;
    entity->material = std::make_shared<Material>(default_white_texture(), 0.5f, 0.0f);
    entity->material->base_color = color;
    return entity;
}

std::shared_ptr<Entity> Scene::create_box(const glm::vec3& size, const glm::vec4& color) {
    auto entity = create_entity("Box_" + std::to_string(next_id_));
    entity->mesh = Mesh::create_box(size.x, size.y, size.z);
    entity->color = color;
    entity->material = std::make_shared<Material>(default_white_texture(), 0.5f, 0.0f);
    entity->material->base_color = color;
    return entity;
}

std::shared_ptr<Entity> Scene::create_sphere(float radius, int rings, int sectors, const glm::vec4& color) {
    auto entity = create_entity("Sphere_" + std::to_string(next_id_));
    entity->mesh = Mesh::create_sphere(radius, rings, sectors);
    entity->color = color;
    entity->material = std::make_shared<Material>(default_white_texture(), 0.3f, 0.0f);
    entity->material->base_color = color;
    return entity;
}

std::shared_ptr<Entity> Scene::create_cylinder(float radius, float height, int segments, bool capped, const glm::vec4& color) {
    auto entity = create_entity("Cylinder_" + std::to_string(next_id_));
    entity->mesh = Mesh::create_cylinder(radius, height, segments, capped);
    entity->color = color;
    entity->material = std::make_shared<Material>(default_white_texture(), 0.5f, 0.0f);
    entity->material->base_color = color;
    return entity;
}

std::shared_ptr<Entity> Scene::create_plane(float size, float uv_tiling, std::shared_ptr<Material> material) {
    auto entity = create_entity("Plane_" + std::to_string(next_id_));
    entity->mesh = Mesh::create_plane(size, size, 1, 1);
    if (!material) {
        material = std::make_shared<Material>(default_white_texture(), 0.8f, 0.0f);
        material->base_color = glm::vec4(0.85f, 0.85f, 0.90f, 1.0f);
        material->uv_scale = glm::vec2(uv_tiling, uv_tiling);
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

void Scene::add_instanced_mesh(std::shared_ptr<InstancedMesh> mesh) {
    if (mesh) {
        instanced_meshes_.push_back(mesh);
    }
}

void Scene::remove_instanced_mesh(std::shared_ptr<InstancedMesh> mesh) {
    auto it = std::remove(instanced_meshes_.begin(), instanced_meshes_.end(), mesh);
    instanced_meshes_.erase(it, instanced_meshes_.end());
}

void Scene::clear() {
    entities_.clear();
    instanced_meshes_.clear();
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

RaycastHit Scene::raycast(const Ray& ray, float max_distance) const {
    RaycastHit closest_hit;
    closest_hit.distance = max_distance;

    for (const auto& entity : entities_) {
        if (!entity || !entity->visible || !entity->has_collision || !entity->mesh) {
            continue;
        }

        // BoundingSphere pre-pass: fast rejection before matrix inversion and 6-plane AABB test
        BoundingSphere bsphere = entity->world_bounding_sphere();
        float t_sphere = 0.0f;
        if (bsphere.is_valid()) {
            if (!ray.intersect_sphere(bsphere, t_sphere)) {
                continue; // Ray misses bounding sphere completely
            }
            if (t_sphere > closest_hit.distance) {
                continue; // Nearest point on sphere is further than current closest hit
            }
        }

        AABB lbox = entity->local_collision_box();
        if (!lbox.is_valid()) {
            continue;
        }

        glm::mat4 model = entity->world_model_matrix();
        glm::mat4 inv_model = glm::inverse(model);

        glm::vec3 orig_local = glm::vec3(inv_model * glm::vec4(ray.origin, 1.0f));
        glm::vec3 dir_local = glm::vec3(inv_model * glm::vec4(ray.direction, 0.0f));

        Ray local_ray{ orig_local, dir_local };
        float t = 0.0f;
        if (local_ray.intersect_aabb(lbox, t)) {
            if (t >= 0.0f && t < closest_hit.distance) {
                closest_hit.hit = true;
                closest_hit.distance = t;
                closest_hit.point = ray.point_at(t);
                closest_hit.entity = entity;
            }
        }
    }

    return closest_hit;
}

} // namespace engine
