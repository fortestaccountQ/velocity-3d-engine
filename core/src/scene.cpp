#include "engine/scene.hpp"
#include "engine/model_loader.hpp"
#include "engine/helpers.hpp"
#include "engine/lod.hpp"
#include "engine/skinned_mesh.hpp"
#include "engine/sprite.hpp"
#include "engine/points.hpp"
#include "engine/particle.hpp"

#include <algorithm>

namespace engine {

Scene::Scene() {
    root_node_ = std::make_shared<Group>("SceneRoot");
}

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

void Scene::add(std::shared_ptr<Node3D> node) {
    if (!node) return;
    if (root_node_) {
        root_node_->add(node);
    }

    std::function<void(const std::shared_ptr<Node3D>&)> collect = [&](const std::shared_ptr<Node3D>& n) {
        if (!n) return;
        auto ent = std::dynamic_pointer_cast<Entity>(n);
        if (ent) {
            if (std::find(entities_.begin(), entities_.end(), ent) == entities_.end()) {
                entities_.push_back(ent);
            }
        }
        auto lit = std::dynamic_pointer_cast<Light>(n);
        if (lit) {
            if (std::find(lights_.begin(), lights_.end(), lit) == lights_.end()) {
                lights_.push_back(lit);
            }
        }
        auto im = std::dynamic_pointer_cast<InstancedMesh>(n);
        if (im) {
            if (std::find(instanced_meshes_.begin(), instanced_meshes_.end(), im) == instanced_meshes_.end()) {
                instanced_meshes_.push_back(im);
            }
        }
        auto hlp = std::dynamic_pointer_cast<Helper>(n);
        if (hlp) {
            if (std::find(helpers_.begin(), helpers_.end(), hlp) == helpers_.end()) {
                helpers_.push_back(hlp);
            }
        }
        auto lod = std::dynamic_pointer_cast<LOD>(n);
        if (lod) {
            if (std::find(lods_.begin(), lods_.end(), lod) == lods_.end()) {
                lods_.push_back(lod);
            }
        }
        auto skm = std::dynamic_pointer_cast<SkinnedMesh>(n);
        if (skm) {
            if (std::find(skinned_meshes_.begin(), skinned_meshes_.end(), skm) == skinned_meshes_.end()) {
                skinned_meshes_.push_back(skm);
            }
        }
        auto spr = std::dynamic_pointer_cast<Sprite>(n);
        if (spr) {
            if (std::find(sprites_.begin(), sprites_.end(), spr) == sprites_.end()) {
                sprites_.push_back(spr);
            }
        }
        auto pts = std::dynamic_pointer_cast<Points>(n);
        if (pts) {
            if (std::find(points_.begin(), points_.end(), pts) == points_.end()) {
                points_.push_back(pts);
            }
        }
        auto pe = std::dynamic_pointer_cast<ParticleEmitter>(n);
        if (pe) {
            if (std::find(particle_emitters_.begin(), particle_emitters_.end(), pe) == particle_emitters_.end()) {
                particle_emitters_.push_back(pe);
            }
        }
        auto sky = std::dynamic_pointer_cast<ProceduralSky>(n);
        if (sky) {
            set_procedural_sky(sky);
        }
        for (const auto& child : n->children()) {
            collect(child);
        }
    };

    collect(node);
}

void Scene::remove(std::shared_ptr<Node3D> node) {
    if (!node) return;
    if (root_node_) {
        root_node_->remove(node);
    }

    std::function<void(const std::shared_ptr<Node3D>&)> purge = [&](const std::shared_ptr<Node3D>& n) {
        if (!n) return;
        auto ent = std::dynamic_pointer_cast<Entity>(n);
        if (ent) {
            auto it = std::find(entities_.begin(), entities_.end(), ent);
            if (it != entities_.end()) entities_.erase(it);
        }
        auto lit = std::dynamic_pointer_cast<Light>(n);
        if (lit) {
            auto it = std::find(lights_.begin(), lights_.end(), lit);
            if (it != lights_.end()) lights_.erase(it);
        }
        auto im = std::dynamic_pointer_cast<InstancedMesh>(n);
        if (im) {
            auto it = std::find(instanced_meshes_.begin(), instanced_meshes_.end(), im);
            if (it != instanced_meshes_.end()) instanced_meshes_.erase(it);
        }
        auto hlp = std::dynamic_pointer_cast<Helper>(n);
        if (hlp) {
            auto it = std::find(helpers_.begin(), helpers_.end(), hlp);
            if (it != helpers_.end()) helpers_.erase(it);
        }
        auto lod = std::dynamic_pointer_cast<LOD>(n);
        if (lod) {
            auto it = std::find(lods_.begin(), lods_.end(), lod);
            if (it != lods_.end()) lods_.erase(it);
        }
        auto skm = std::dynamic_pointer_cast<SkinnedMesh>(n);
        if (skm) {
            auto it = std::find(skinned_meshes_.begin(), skinned_meshes_.end(), skm);
            if (it != skinned_meshes_.end()) skinned_meshes_.erase(it);
        }
        auto spr = std::dynamic_pointer_cast<Sprite>(n);
        if (spr) {
            auto it = std::find(sprites_.begin(), sprites_.end(), spr);
            if (it != sprites_.end()) sprites_.erase(it);
        }
        auto pts = std::dynamic_pointer_cast<Points>(n);
        if (pts) {
            auto it = std::find(points_.begin(), points_.end(), pts);
            if (it != points_.end()) points_.erase(it);
        }
        auto pe = std::dynamic_pointer_cast<ParticleEmitter>(n);
        if (pe) {
            auto it = std::find(particle_emitters_.begin(), particle_emitters_.end(), pe);
            if (it != particle_emitters_.end()) particle_emitters_.erase(it);
        }
        for (const auto& child : n->children()) {
            purge(child);
        }
    };

    purge(node);
}

std::shared_ptr<Entity> Scene::create_entity(const std::string& name) {
    auto entity = std::make_shared<Entity>(next_id_++, name);
    add(entity);
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
    add(entity);
}

void Scene::remove_entity(std::shared_ptr<Entity> entity) {
    remove(entity);
}

void Scene::add_instanced_mesh(std::shared_ptr<InstancedMesh> mesh) {
    add(mesh);
}

void Scene::remove_instanced_mesh(std::shared_ptr<InstancedMesh> mesh) {
    remove(mesh);
}

void Scene::add_light(std::shared_ptr<Light> l) {
    add(l);
}

void Scene::remove_light(std::shared_ptr<Light> l) {
    remove(l);
}

void Scene::add_skinned_mesh(std::shared_ptr<SkinnedMesh> sm) {
    add(sm);
}

void Scene::remove_skinned_mesh(std::shared_ptr<SkinnedMesh> sm) {
    remove(sm);
}

void Scene::add_sprite(std::shared_ptr<Sprite> spr) {
    add(spr);
}

void Scene::remove_sprite(std::shared_ptr<Sprite> spr) {
    remove(spr);
}

void Scene::add_points(std::shared_ptr<Points> pts) {
    add(pts);
}

void Scene::remove_points(std::shared_ptr<Points> pts) {
    remove(pts);
}

void Scene::add_particle_emitter(std::shared_ptr<ParticleEmitter> pe) {
    add(pe);
}

void Scene::remove_particle_emitter(std::shared_ptr<ParticleEmitter> pe) {
    remove(pe);
}

void Scene::clear() {
    if (root_node_) {
        root_node_->clear();
    }
    entities_.clear();
    instanced_meshes_.clear();
    lights_.clear();
    helpers_.clear();
    lods_.clear();
    skinned_meshes_.clear();
    sprites_.clear();
    points_.clear();
    particle_emitters_.clear();
    procedural_sky_ = nullptr;
    background_cube_ = nullptr;
    environment_ = nullptr;
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

        AABB box = entity->world_aabb();
        if (!box.is_valid()) {
            continue;
        }

        float t = 0.0f;
        if (ray.intersect_aabb(box, t)) {
            if (t > 0.0f && t < closest_hit.distance) {
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
