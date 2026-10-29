#pragma once

#include <string>
#include <memory>
#include <vector>
#include <unordered_map>
#include <mutex>
#include <glm/glm.hpp>

namespace engine {

class Mesh;
class Model;
class Node3D;
class Scene;
class EngineApp;
class Texture;

// ---------------------------------------------------------------------------
// Mesh & Model Loaders
// ---------------------------------------------------------------------------
// OBJ Parser (fast parser for .obj: vertices, normals, UVs, faces)
std::shared_ptr<Mesh> load_obj_mesh(const std::string& filepath);
std::shared_ptr<Model> load_obj(Scene& scene, const std::string& filepath);

// STL Parser (supports ASCII solid...endsolid and Binary 80-byte header format)
std::shared_ptr<Mesh> load_stl_mesh(const std::string& filepath);
std::shared_ptr<Model> load_stl(Scene& scene, const std::string& filepath);

// PLY Parser (supports ASCII and Binary format)
std::shared_ptr<Mesh> load_ply_mesh(const std::string& filepath);
std::shared_ptr<Model> load_ply(Scene& scene, const std::string& filepath);

// Unified mesh loader dispatching by extension
std::shared_ptr<Mesh> load_mesh_file(const std::string& filepath);

// ---------------------------------------------------------------------------
// Exporters
// ---------------------------------------------------------------------------
bool export_obj(std::shared_ptr<Node3D> node, const std::string& filepath);
bool export_stl(std::shared_ptr<Node3D> node, const std::string& filepath, bool binary = true);
bool export_gltf(Scene& scene, const std::string& filepath);
bool save_screenshot(EngineApp& app, const std::string& filepath);

// ---------------------------------------------------------------------------
// AssetCache Singleton
// ---------------------------------------------------------------------------
class AssetCache {
public:
    static AssetCache& instance() {
        static AssetCache s_instance;
        return s_instance;
    }

    std::shared_ptr<Mesh> get_mesh(const std::string& path);
    void cache_mesh(const std::string& path, std::shared_ptr<Mesh> mesh);

    std::shared_ptr<Texture> get_texture(const std::string& path);
    void cache_texture(const std::string& path, std::shared_ptr<Texture> texture);

    std::shared_ptr<Model> get_model(const std::string& path);
    void cache_model(const std::string& path, std::shared_ptr<Model> model);

    std::shared_ptr<Mesh> load_mesh(const std::string& path);
    std::shared_ptr<Texture> load_texture(const std::string& path, bool srgb = true);
    std::shared_ptr<Model> load_model(Scene& scene, const std::string& path);

    bool has(const std::string& path) const;
    void remove(const std::string& path);
    void clear();
    size_t size() const;

private:
    AssetCache() = default;
    ~AssetCache() = default;
    AssetCache(const AssetCache&) = delete;
    AssetCache& operator=(const AssetCache&) = delete;

    std::unordered_map<std::string, std::shared_ptr<Mesh>> meshes_;
    std::unordered_map<std::string, std::shared_ptr<Texture>> textures_;
    std::unordered_map<std::string, std::shared_ptr<Model>> models_;
    mutable std::mutex mutex_;
};

} // namespace engine
