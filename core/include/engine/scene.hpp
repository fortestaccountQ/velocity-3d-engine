#pragma once

#include "engine/node3d.hpp"
#include "engine/entity.hpp"
#include "engine/mesh.hpp"
#include "engine/light.hpp"
#include "engine/texture.hpp"
#include "engine/material.hpp"
#include "engine/model.hpp"
#include <vector>
#include <memory>
#include <string>

namespace engine {

class Scene {
public:
    DirectionalLight light;

    Scene();

    std::shared_ptr<Group> root_node() const { return root_node_; }

    void add(std::shared_ptr<Node3D> node);
    void remove(std::shared_ptr<Node3D> node);

    std::shared_ptr<Model> load_model(const std::string& filepath);
    std::shared_ptr<Entity> create_cube(const glm::vec4& color = glm::vec4(1.0f));
    std::shared_ptr<Entity> create_box(const glm::vec3& size = glm::vec3(1.0f), const glm::vec4& color = glm::vec4(1.0f));
    std::shared_ptr<Entity> create_sphere(float radius = 1.0f, int rings = 32, int sectors = 32, const glm::vec4& color = glm::vec4(1.0f));
    std::shared_ptr<Entity> create_cylinder(float radius = 0.5f, float height = 2.0f, int segments = 32, bool capped = true, const glm::vec4& color = glm::vec4(1.0f));
    std::shared_ptr<Entity> create_plane(float size = 10.0f, float uv_tiling = 5.0f, std::shared_ptr<Material> material = nullptr);
    std::shared_ptr<Entity> create_entity(const std::string& name = "Entity");

    void add_entity(std::shared_ptr<Entity> entity);
    void remove_entity(std::shared_ptr<Entity> entity);
    void add_instanced_mesh(std::shared_ptr<InstancedMesh> mesh);
    void remove_instanced_mesh(std::shared_ptr<InstancedMesh> mesh);
    void add_light(std::shared_ptr<Light> l);
    void remove_light(std::shared_ptr<Light> l);
    void clear();

    RaycastHit raycast(const Ray& ray, float max_distance = 1000.0f) const;

    const std::vector<std::shared_ptr<Entity>>& entities() const { return entities_; }
    const std::vector<std::shared_ptr<InstancedMesh>>& instanced_meshes() const { return instanced_meshes_; }
    std::vector<std::shared_ptr<InstancedMesh>>& instanced_meshes() { return instanced_meshes_; }
    const std::vector<std::shared_ptr<Light>>& lights() const { return lights_; }
    std::vector<std::shared_ptr<Light>>& lights() { return lights_; }

    std::shared_ptr<Mesh> default_cube_mesh();
    std::shared_ptr<Texture> default_checker_texture();
    std::shared_ptr<Texture> default_white_texture();
    std::shared_ptr<Material> default_material();

private:
    std::shared_ptr<Group> root_node_{nullptr};
    std::vector<std::shared_ptr<Entity>> entities_;
    std::vector<std::shared_ptr<InstancedMesh>> instanced_meshes_;
    std::vector<std::shared_ptr<Light>> lights_;

    uint32_t next_id_{1};
    std::shared_ptr<Mesh> default_cube_mesh_{nullptr};
    std::shared_ptr<Texture> default_checker_texture_{nullptr};
    std::shared_ptr<Texture> default_white_texture_{nullptr};
    std::shared_ptr<Material> default_material_{nullptr};
};

} // namespace engine
