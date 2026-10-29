#include "engine/asset_io.hpp"
#include "engine/mesh.hpp"
#include "engine/model.hpp"
#include "engine/node3d.hpp"
#include "engine/scene.hpp"
#include "engine/app.hpp"
#include "engine/texture.hpp"
#include "engine/material.hpp"
#include "engine/render_target.hpp"
#include "engine/model_loader.hpp"

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include "stb_image_write.h"

#include <fstream>
#include <sstream>
#include <iostream>
#include <algorithm>
#include <filesystem>
#include <cstring>
#include <cstdint>
#include <cmath>
#include <unordered_map>
#include <iomanip>
#include <glm/gtc/type_ptr.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// Base64 Helpers for glTF
// ---------------------------------------------------------------------------
static const char s_b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

static std::string base64_encode(const uint8_t* data, size_t len) {
    std::string out;
    out.reserve(((len + 2) / 3) * 4);
    for (size_t i = 0; i < len; i += 3) {
        uint32_t b = (static_cast<uint32_t>(data[i]) << 16);
        if (i + 1 < len) b |= (static_cast<uint32_t>(data[i + 1]) << 8);
        if (i + 2 < len) b |= static_cast<uint32_t>(data[i + 2]);

        out.push_back(s_b64_table[(b >> 18) & 0x3F]);
        out.push_back(s_b64_table[(b >> 12) & 0x3F]);
        out.push_back((i + 1 < len) ? s_b64_table[(b >> 6) & 0x3F] : '=');
        out.push_back((i + 2 < len) ? s_b64_table[b & 0x3F] : '=');
    }
    return out;
}

// ---------------------------------------------------------------------------
// OBJ Loader
// ---------------------------------------------------------------------------
std::shared_ptr<Mesh> load_obj_mesh(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "[AssetIO] Error opening OBJ file: " << filepath << "\n";
        return nullptr;
    }

    std::vector<glm::vec3> positions;
    std::vector<glm::vec3> normals;
    std::vector<glm::vec2> uvs;

    auto mesh = std::make_shared<Mesh>();

    struct ObjVertexIndex {
        int v{-1};
        int vt{-1};
        int vn{-1};

        bool operator==(const ObjVertexIndex& o) const {
            return v == o.v && vt == o.vt && vn == o.vn;
        }
    };

    struct ObjVertexHash {
        size_t operator()(const ObjVertexIndex& k) const {
            size_t h = std::hash<int>()(k.v);
            h ^= (std::hash<int>()(k.vt) << 1);
            h ^= (std::hash<int>()(k.vn) << 2);
            return h;
        }
    };

    std::unordered_map<ObjVertexIndex, uint16_t, ObjVertexHash> vertex_map;

    auto parse_index = [](int idx, int count) -> int {
        if (idx > 0) return idx - 1;
        if (idx < 0) return count + idx;
        return -1;
    };

    std::string line;
    while (std::getline(file, line)) {
        if (line.empty()) continue;
        // Trim leading spaces
        size_t start = line.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) continue;
        if (line[start] == '#') continue;

        std::istringstream iss(line.substr(start));
        std::string token;
        iss >> token;

        if (token == "v") {
            float x = 0.0f, y = 0.0f, z = 0.0f;
            iss >> x >> y >> z;
            positions.push_back({x, y, z});
        } else if (token == "vn") {
            float x = 0.0f, y = 0.0f, z = 0.0f;
            iss >> x >> y >> z;
            normals.push_back({x, y, z});
        } else if (token == "vt") {
            float u = 0.0f, v = 0.0f;
            iss >> u >> v;
            uvs.push_back({u, v});
        } else if (token == "f") {
            std::vector<ObjVertexIndex> face_indices;
            std::string vert_token;
            while (iss >> vert_token) {
                ObjVertexIndex idx;
                int v = 0, vt = 0, vn = 0;
                size_t p1 = vert_token.find('/');
                if (p1 == std::string::npos) {
                    v = std::stoi(vert_token);
                } else {
                    v = std::stoi(vert_token.substr(0, p1));
                    size_t p2 = vert_token.find('/', p1 + 1);
                    if (p2 == std::string::npos) {
                        if (p1 + 1 < vert_token.size()) {
                            vt = std::stoi(vert_token.substr(p1 + 1));
                        }
                    } else {
                        if (p2 > p1 + 1) {
                            vt = std::stoi(vert_token.substr(p1 + 1, p2 - (p1 + 1)));
                        }
                        if (p2 + 1 < vert_token.size()) {
                            vn = std::stoi(vert_token.substr(p2 + 1));
                        }
                    }
                }
                idx.v = parse_index(v, static_cast<int>(positions.size()));
                idx.vt = parse_index(vt, static_cast<int>(uvs.size()));
                idx.vn = parse_index(vn, static_cast<int>(normals.size()));
                face_indices.push_back(idx);
            }

            if (face_indices.size() >= 3) {
                // Triangulate polygon as fan
                for (size_t i = 1; i + 1 < face_indices.size(); ++i) {
                    ObjVertexIndex tri[3] = { face_indices[0], face_indices[i], face_indices[i + 1] };
                    for (int k = 0; k < 3; ++k) {
                        auto it = vertex_map.find(tri[k]);
                        if (it != vertex_map.end()) {
                            mesh->cpu_indices.push_back(it->second);
                        } else {
                            uint16_t new_idx = static_cast<uint16_t>(mesh->cpu_vertices.size());
                            Vertex vert{};
                            if (tri[k].v >= 0 && tri[k].v < static_cast<int>(positions.size())) {
                                vert.position = positions[tri[k].v];
                            }
                            if (tri[k].vn >= 0 && tri[k].vn < static_cast<int>(normals.size())) {
                                vert.normal = normals[tri[k].vn];
                            }
                            if (tri[k].vt >= 0 && tri[k].vt < static_cast<int>(uvs.size())) {
                                vert.uv = uvs[tri[k].vt];
                            }
                            mesh->cpu_vertices.push_back(vert);
                            mesh->cpu_indices.push_back(new_idx);
                            vertex_map[tri[k]] = new_idx;
                        }
                    }
                }
            }
        }
    }

    if (mesh->cpu_vertices.empty()) {
        std::cerr << "[AssetIO] Warning: No vertices loaded from OBJ: " << filepath << "\n";
        return nullptr;
    }

    // If normals were missing from OBJ, compute smooth per-vertex normals
    if (normals.empty()) {
        for (size_t i = 0; i < mesh->cpu_vertices.size(); ++i) {
            mesh->cpu_vertices[i].normal = glm::vec3(0.0f);
        }
        for (size_t i = 0; i + 2 < mesh->cpu_indices.size(); i += 3) {
            uint16_t i0 = mesh->cpu_indices[i];
            uint16_t i1 = mesh->cpu_indices[i + 1];
            uint16_t i2 = mesh->cpu_indices[i + 2];
            glm::vec3 p0 = mesh->cpu_vertices[i0].position;
            glm::vec3 p1 = mesh->cpu_vertices[i1].position;
            glm::vec3 p2 = mesh->cpu_vertices[i2].position;
            glm::vec3 fn = glm::cross(p1 - p0, p2 - p0);
            mesh->cpu_vertices[i0].normal += fn;
            mesh->cpu_vertices[i1].normal += fn;
            mesh->cpu_vertices[i2].normal += fn;
        }
        for (auto& v : mesh->cpu_vertices) {
            float len = glm::length(v.normal);
            if (len > 1e-6f) v.normal /= len;
            else v.normal = glm::vec3(0.0f, 1.0f, 0.0f);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();

    return mesh;
}

std::shared_ptr<Model> load_obj(Scene& scene, const std::string& filepath) {
    auto mesh = load_obj_mesh(filepath);
    if (!mesh) return nullptr;

    std::string name = std::filesystem::path(filepath).stem().string();
    auto entity = scene.create_entity(name);
    entity->mesh = mesh;
    entity->material = scene.default_material();

    auto model = std::make_shared<Model>(entity, name);
    model->meshes.push_back(entity);
    return model;
}

// ---------------------------------------------------------------------------
// STL Loader
// ---------------------------------------------------------------------------
std::shared_ptr<Mesh> load_stl_mesh(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "[AssetIO] Error opening STL file: " << filepath << "\n";
        return nullptr;
    }

    file.seekg(0, std::ios::end);
    size_t file_size = static_cast<size_t>(file.tellg());
    file.seekg(0, std::ios::beg);

    if (file_size < 84) {
        // Might be tiny ASCII STL
        file.close();
    } else {
        std::vector<uint8_t> header(84);
        file.read(reinterpret_cast<char*>(header.data()), 84);
        uint32_t facet_count = 0;
        std::memcpy(&facet_count, header.data() + 80, sizeof(uint32_t));

        size_t expected_binary_size = 84 + static_cast<size_t>(facet_count) * 50;
        if (file_size == expected_binary_size) {
            // Definite Binary STL
            auto mesh = std::make_shared<Mesh>();
            mesh->cpu_vertices.reserve(facet_count * 3);
            mesh->cpu_indices.reserve(facet_count * 3);

            std::vector<uint8_t> facet_data(facet_count * 50);
            file.read(reinterpret_cast<char*>(facet_data.data()), facet_data.size());

            for (uint32_t i = 0; i < facet_count; ++i) {
                size_t offset = i * 50;
                float normal[3], v1[3], v2[3], v3[3];
                std::memcpy(normal, facet_data.data() + offset, 12);
                std::memcpy(v1, facet_data.data() + offset + 12, 12);
                std::memcpy(v2, facet_data.data() + offset + 24, 12);
                std::memcpy(v3, facet_data.data() + offset + 36, 12);

                glm::vec3 n(normal[0], normal[1], normal[2]);
                glm::vec3 p1(v1[0], v1[1], v1[2]);
                glm::vec3 p2(v2[0], v2[1], v2[2]);
                glm::vec3 p3(v3[0], v3[1], v3[2]);

                if (glm::length(n) < 1e-4f) {
                    glm::vec3 fn = glm::cross(p2 - p1, p3 - p1);
                    float l = glm::length(fn);
                    n = (l > 1e-6f) ? (fn / l) : glm::vec3(0.0f, 1.0f, 0.0f);
                }

                uint16_t base = static_cast<uint16_t>(mesh->cpu_vertices.size());
                mesh->cpu_vertices.push_back(Vertex{ p1, n, glm::vec2(0.0f) });
                mesh->cpu_vertices.push_back(Vertex{ p2, n, glm::vec2(0.0f) });
                mesh->cpu_vertices.push_back(Vertex{ p3, n, glm::vec2(0.0f) });

                mesh->cpu_indices.push_back(base);
                mesh->cpu_indices.push_back(base + 1);
                mesh->cpu_indices.push_back(base + 2);
            }

            mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
            mesh->calculate_aabb();
            mesh->ensure_gpu_buffers();
            return mesh;
        }
        file.seekg(0, std::ios::beg);
    }

    // ASCII STL parser
    auto mesh = std::make_shared<Mesh>();
    std::string line;
    glm::vec3 current_normal(0.0f, 1.0f, 0.0f);
    std::vector<glm::vec3> face_verts;

    while (std::getline(file, line)) {
        size_t start = line.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) continue;
        std::istringstream iss(line.substr(start));
        std::string token;
        iss >> token;

        if (token == "facet") {
            std::string normal_token;
            iss >> normal_token;
            if (normal_token == "normal") {
                iss >> current_normal.x >> current_normal.y >> current_normal.z;
            }
            face_verts.clear();
        } else if (token == "vertex") {
            float x = 0.0f, y = 0.0f, z = 0.0f;
            iss >> x >> y >> z;
            face_verts.push_back({x, y, z});
        } else if (token == "endfacet") {
            if (face_verts.size() == 3) {
                glm::vec3 p1 = face_verts[0];
                glm::vec3 p2 = face_verts[1];
                glm::vec3 p3 = face_verts[2];
                glm::vec3 n = current_normal;
                if (glm::length(n) < 1e-4f) {
                    glm::vec3 fn = glm::cross(p2 - p1, p3 - p1);
                    float l = glm::length(fn);
                    n = (l > 1e-6f) ? (fn / l) : glm::vec3(0.0f, 1.0f, 0.0f);
                }

                uint16_t base = static_cast<uint16_t>(mesh->cpu_vertices.size());
                mesh->cpu_vertices.push_back(Vertex{ p1, n, glm::vec2(0.0f) });
                mesh->cpu_vertices.push_back(Vertex{ p2, n, glm::vec2(0.0f) });
                mesh->cpu_vertices.push_back(Vertex{ p3, n, glm::vec2(0.0f) });

                mesh->cpu_indices.push_back(base);
                mesh->cpu_indices.push_back(base + 1);
                mesh->cpu_indices.push_back(base + 2);
            }
            face_verts.clear();
        }
    }

    if (mesh->cpu_vertices.empty()) {
        std::cerr << "[AssetIO] Warning: No vertices loaded from STL: " << filepath << "\n";
        return nullptr;
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Model> load_stl(Scene& scene, const std::string& filepath) {
    auto mesh = load_stl_mesh(filepath);
    if (!mesh) return nullptr;

    std::string name = std::filesystem::path(filepath).stem().string();
    auto entity = scene.create_entity(name);
    entity->mesh = mesh;
    entity->material = scene.default_material();

    auto model = std::make_shared<Model>(entity, name);
    model->meshes.push_back(entity);
    return model;
}

// ---------------------------------------------------------------------------
// PLY Loader
// ---------------------------------------------------------------------------
std::shared_ptr<Mesh> load_ply_mesh(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "[AssetIO] Error opening PLY file: " << filepath << "\n";
        return nullptr;
    }

    std::string line;
    std::getline(file, line);
    // Remove CR
    if (!line.empty() && line.back() == '\r') line.pop_back();
    if (line != "ply") {
        std::cerr << "[AssetIO] Error: Not a valid PLY file (magic missing): " << filepath << "\n";
        return nullptr;
    }

    bool is_binary = false;
    int num_vertices = 0;
    int num_faces = 0;
    std::vector<std::string> vertex_props;

    while (std::getline(file, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        size_t start = line.find_first_not_of(" \t");
        if (start == std::string::npos) continue;
        std::istringstream iss(line.substr(start));
        std::string token;
        iss >> token;

        if (token == "format") {
            std::string fmt;
            iss >> fmt;
            if (fmt.find("binary") != std::string::npos) {
                is_binary = true;
            }
        } else if (token == "element") {
            std::string elem_type;
            int count = 0;
            iss >> elem_type >> count;
            if (elem_type == "vertex") {
                num_vertices = count;
            } else if (elem_type == "face") {
                num_faces = count;
            }
        } else if (token == "property") {
            std::string prop_type, prop_name;
            iss >> prop_type;
            if (prop_type == "list") {
                // face indices list
            } else {
                iss >> prop_name;
                vertex_props.push_back(prop_name);
            }
        } else if (token == "end_header") {
            break;
        }
    }

    if (num_vertices <= 0) {
        std::cerr << "[AssetIO] Error: PLY file contains 0 vertices.\n";
        return nullptr;
    }

    auto mesh = std::make_shared<Mesh>();
    mesh->cpu_vertices.reserve(num_vertices);

    if (!is_binary) {
        // ASCII PLY
        for (int i = 0; i < num_vertices; ++i) {
            if (!std::getline(file, line)) break;
            std::istringstream iss(line);
            Vertex v{};
            v.color = glm::vec4(1.0f);

            for (const auto& prop : vertex_props) {
                float val = 0.0f;
                iss >> val;
                if (prop == "x") v.position.x = val;
                else if (prop == "y") v.position.y = val;
                else if (prop == "z") v.position.z = val;
                else if (prop == "nx") v.normal.x = val;
                else if (prop == "ny") v.normal.y = val;
                else if (prop == "nz") v.normal.z = val;
                else if (prop == "s" || prop == "u") v.uv.x = val;
                else if (prop == "t" || prop == "v") v.uv.y = val;
                else if (prop == "red" || prop == "r") v.color.r = (val > 1.0f) ? (val / 255.0f) : val;
                else if (prop == "green" || prop == "g") v.color.g = (val > 1.0f) ? (val / 255.0f) : val;
                else if (prop == "blue" || prop == "b") v.color.b = (val > 1.0f) ? (val / 255.0f) : val;
                else if (prop == "alpha" || prop == "a") v.color.a = (val > 1.0f) ? (val / 255.0f) : val;
            }
            mesh->cpu_vertices.push_back(v);
        }

        for (int i = 0; i < num_faces; ++i) {
            if (!std::getline(file, line)) break;
            std::istringstream iss(line);
            int count = 0;
            iss >> count;
            if (count >= 3) {
                std::vector<uint16_t> face_indices(count);
                for (int k = 0; k < count; ++k) {
                    iss >> face_indices[k];
                }
                for (int k = 1; k + 1 < count; ++k) {
                    mesh->cpu_indices.push_back(face_indices[0]);
                    mesh->cpu_indices.push_back(face_indices[k]);
                    mesh->cpu_indices.push_back(face_indices[k + 1]);
                }
            }
        }
    } else {
        // Binary PLY (assume standard float coords, float normals/uchar colors)
        for (int i = 0; i < num_vertices; ++i) {
            Vertex v{};
            v.color = glm::vec4(1.0f);
            for (const auto& prop : vertex_props) {
                if (prop == "x" || prop == "y" || prop == "z" ||
                    prop == "nx" || prop == "ny" || prop == "nz" ||
                    prop == "s" || prop == "t" || prop == "u" || prop == "v") {
                    float f = 0.0f;
                    file.read(reinterpret_cast<char*>(&f), sizeof(float));
                    if (prop == "x") v.position.x = f;
                    else if (prop == "y") v.position.y = f;
                    else if (prop == "z") v.position.z = f;
                    else if (prop == "nx") v.normal.x = f;
                    else if (prop == "ny") v.normal.y = f;
                    else if (prop == "nz") v.normal.z = f;
                    else if (prop == "s" || prop == "u") v.uv.x = f;
                    else if (prop == "t" || prop == "v") v.uv.y = f;
                } else if (prop == "red" || prop == "green" || prop == "blue" || prop == "alpha") {
                    uint8_t c = 255;
                    file.read(reinterpret_cast<char*>(&c), 1);
                    float f = c / 255.0f;
                    if (prop == "red") v.color.r = f;
                    else if (prop == "green") v.color.g = f;
                    else if (prop == "blue") v.color.b = f;
                    else if (prop == "alpha") v.color.a = f;
                }
            }
            mesh->cpu_vertices.push_back(v);
        }

        for (int i = 0; i < num_faces; ++i) {
            uint8_t count = 0;
            file.read(reinterpret_cast<char*>(&count), 1);
            if (count >= 3) {
                std::vector<int32_t> idxs(count);
                file.read(reinterpret_cast<char*>(idxs.data()), count * sizeof(int32_t));
                for (int k = 1; k + 1 < count; ++k) {
                    mesh->cpu_indices.push_back(static_cast<uint16_t>(idxs[0]));
                    mesh->cpu_indices.push_back(static_cast<uint16_t>(idxs[k]));
                    mesh->cpu_indices.push_back(static_cast<uint16_t>(idxs[k + 1]));
                }
            }
        }
    }

    // Recalculate normals if missing
    bool has_normals = false;
    for (const auto& prop : vertex_props) {
        if (prop == "nx") { has_normals = true; break; }
    }
    if (!has_normals && !mesh->cpu_indices.empty()) {
        for (auto& v : mesh->cpu_vertices) v.normal = glm::vec3(0.0f);
        for (size_t i = 0; i + 2 < mesh->cpu_indices.size(); i += 3) {
            uint16_t i0 = mesh->cpu_indices[i];
            uint16_t i1 = mesh->cpu_indices[i + 1];
            uint16_t i2 = mesh->cpu_indices[i + 2];
            glm::vec3 fn = glm::cross(mesh->cpu_vertices[i1].position - mesh->cpu_vertices[i0].position,
                                      mesh->cpu_vertices[i2].position - mesh->cpu_vertices[i0].position);
            mesh->cpu_vertices[i0].normal += fn;
            mesh->cpu_vertices[i1].normal += fn;
            mesh->cpu_vertices[i2].normal += fn;
        }
        for (auto& v : mesh->cpu_vertices) {
            float len = glm::length(v.normal);
            v.normal = (len > 1e-6f) ? (v.normal / len) : glm::vec3(0.0f, 1.0f, 0.0f);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Model> load_ply(Scene& scene, const std::string& filepath) {
    auto mesh = load_ply_mesh(filepath);
    if (!mesh) return nullptr;

    std::string name = std::filesystem::path(filepath).stem().string();
    auto entity = scene.create_entity(name);
    entity->mesh = mesh;
    entity->material = scene.default_material();

    auto model = std::make_shared<Model>(entity, name);
    model->meshes.push_back(entity);
    return model;
}

// ---------------------------------------------------------------------------
// Unified loader
// ---------------------------------------------------------------------------
std::shared_ptr<Mesh> load_mesh_file(const std::string& filepath) {
    std::string ext = std::filesystem::path(filepath).extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);

    if (ext == ".obj") {
        return load_obj_mesh(filepath);
    } else if (ext == ".stl") {
        return load_stl_mesh(filepath);
    } else if (ext == ".ply") {
        return load_ply_mesh(filepath);
    }

    std::cerr << "[AssetIO] Unsupported mesh extension: " << ext << "\n";
    return nullptr;
}

// ---------------------------------------------------------------------------
// Exporters
// ---------------------------------------------------------------------------
bool export_obj(std::shared_ptr<Node3D> node, const std::string& filepath) {
    if (!node) return false;

    std::ofstream out(filepath);
    if (!out.is_open()) return false;

    out << "# Exported by Pielosyty 3D Engine\n";
    out << "# Root Node: " << node->name << "\n";

    glm::mat4 root_inv = glm::inverse(node->world_matrix());
    uint32_t vertex_offset = 1;

    node->traverse([&](Node3D& n) {
        auto ent = dynamic_cast<Entity*>(&n);
        if (ent && ent->mesh && !ent->mesh->cpu_vertices.empty()) {
            glm::mat4 rel_m = root_inv * ent->world_model_matrix();
            glm::mat3 norm_m = glm::transpose(glm::inverse(glm::mat3(rel_m)));

            out << "o " << ent->name << "\n";
            for (const auto& v : ent->mesh->cpu_vertices) {
                glm::vec3 pos = glm::vec3(rel_m * glm::vec4(v.position, 1.0f));
                out << "v " << pos.x << " " << pos.y << " " << pos.z << "\n";
            }
            for (const auto& v : ent->mesh->cpu_vertices) {
                glm::vec3 norm = glm::normalize(norm_m * v.normal);
                out << "vn " << norm.x << " " << norm.y << " " << norm.z << "\n";
            }
            for (const auto& v : ent->mesh->cpu_vertices) {
                out << "vt " << v.uv.x << " " << v.uv.y << "\n";
            }

            const auto& indices = ent->mesh->cpu_indices;
            if (!indices.empty()) {
                for (size_t i = 0; i + 2 < indices.size(); i += 3) {
                    uint32_t i0 = vertex_offset + indices[i];
                    uint32_t i1 = vertex_offset + indices[i + 1];
                    uint32_t i2 = vertex_offset + indices[i + 2];
                    out << "f " << i0 << "/" << i0 << "/" << i0 << " "
                                << i1 << "/" << i1 << "/" << i1 << " "
                                << i2 << "/" << i2 << "/" << i2 << "\n";
                }
            } else {
                for (size_t i = 0; i + 2 < ent->mesh->cpu_vertices.size(); i += 3) {
                    uint32_t i0 = vertex_offset + static_cast<uint32_t>(i);
                    uint32_t i1 = vertex_offset + static_cast<uint32_t>(i + 1);
                    uint32_t i2 = vertex_offset + static_cast<uint32_t>(i + 2);
                    out << "f " << i0 << "/" << i0 << "/" << i0 << " "
                                << i1 << "/" << i1 << "/" << i1 << " "
                                << i2 << "/" << i2 << "/" << i2 << "\n";
                }
            }

            vertex_offset += static_cast<uint32_t>(ent->mesh->cpu_vertices.size());
        }
    });

    return true;
}

bool export_stl(std::shared_ptr<Node3D> node, const std::string& filepath, bool binary) {
    if (!node) return false;

    struct Triangle {
        glm::vec3 normal;
        glm::vec3 p1;
        glm::vec3 p2;
        glm::vec3 p3;
    };
    std::vector<Triangle> triangles;

    glm::mat4 root_inv = glm::inverse(node->world_matrix());

    node->traverse([&](Node3D& n) {
        auto ent = dynamic_cast<Entity*>(&n);
        if (ent && ent->mesh && !ent->mesh->cpu_vertices.empty()) {
            glm::mat4 rel_m = root_inv * ent->world_model_matrix();
            const auto& verts = ent->mesh->cpu_vertices;
            const auto& indices = ent->mesh->cpu_indices;

            auto add_tri = [&](const glm::vec3& p1, const glm::vec3& p2, const glm::vec3& p3) {
                glm::vec3 tp1 = glm::vec3(rel_m * glm::vec4(p1, 1.0f));
                glm::vec3 tp2 = glm::vec3(rel_m * glm::vec4(p2, 1.0f));
                glm::vec3 tp3 = glm::vec3(rel_m * glm::vec4(p3, 1.0f));
                glm::vec3 fn = glm::cross(tp2 - tp1, tp3 - tp1);
                float l = glm::length(fn);
                glm::vec3 n = (l > 1e-6f) ? (fn / l) : glm::vec3(0.0f, 1.0f, 0.0f);
                triangles.push_back({ n, tp1, tp2, tp3 });
            };

            if (!indices.empty()) {
                for (size_t i = 0; i + 2 < indices.size(); i += 3) {
                    add_tri(verts[indices[i]].position,
                            verts[indices[i + 1]].position,
                            verts[indices[i + 2]].position);
                }
            } else {
                for (size_t i = 0; i + 2 < verts.size(); i += 3) {
                    add_tri(verts[i].position, verts[i + 1].position, verts[i + 2].position);
                }
            }
        }
    });

    if (binary) {
        std::ofstream out(filepath, std::ios::binary);
        if (!out.is_open()) return false;

        char header[80] = "Pielosyty 3D Engine STL Export (Binary)";
        out.write(header, 80);

        uint32_t count = static_cast<uint32_t>(triangles.size());
        out.write(reinterpret_cast<const char*>(&count), sizeof(uint32_t));

        for (const auto& tri : triangles) {
            out.write(reinterpret_cast<const char*>(&tri.normal.x), 12);
            out.write(reinterpret_cast<const char*>(&tri.p1.x), 12);
            out.write(reinterpret_cast<const char*>(&tri.p2.x), 12);
            out.write(reinterpret_cast<const char*>(&tri.p3.x), 12);
            uint16_t attr = 0;
            out.write(reinterpret_cast<const char*>(&attr), sizeof(uint16_t));
        }
    } else {
        std::ofstream out(filepath);
        if (!out.is_open()) return false;

        out << "solid PielosytyScene\n";
        for (const auto& tri : triangles) {
            out << "  facet normal " << tri.normal.x << " " << tri.normal.y << " " << tri.normal.z << "\n";
            out << "    outer loop\n";
            out << "      vertex " << tri.p1.x << " " << tri.p1.y << " " << tri.p1.z << "\n";
            out << "      vertex " << tri.p2.x << " " << tri.p2.y << " " << tri.p2.z << "\n";
            out << "      vertex " << tri.p3.x << " " << tri.p3.y << " " << tri.p3.z << "\n";
            out << "    endloop\n";
            out << "  endfacet\n";
        }
        out << "endsolid PielosytyScene\n";
    }

    return true;
}

bool export_gltf(Scene& scene, const std::string& filepath) {
    std::vector<uint8_t> bin_buffer;

    struct PrimitiveMeta {
        uint32_t pos_acc_idx;
        uint32_t norm_acc_idx;
        uint32_t uv_acc_idx;
        uint32_t idx_acc_idx;
        uint32_t mat_idx;
    };

    struct MeshMeta {
        std::string name;
        std::vector<PrimitiveMeta> primitives;
    };

    struct NodeMeta {
        std::string name;
        uint32_t mesh_idx;
        glm::mat4 matrix;
    };

    struct AccessorMeta {
        uint32_t buffer_view_idx;
        uint32_t byte_offset;
        uint32_t component_type; // 5126 (FLOAT) or 5123 (UNSIGNED_SHORT)
        uint32_t count;
        std::string type; // "VEC3", "VEC2", "SCALAR"
        glm::vec3 min_v{0.0f};
        glm::vec3 max_v{0.0f};
        bool has_min_max{false};
    };

    struct BufferViewMeta {
        uint32_t byte_offset;
        uint32_t byte_length;
        uint32_t target; // 34962 (ARRAY_BUFFER) or 34963 (ELEMENT_ARRAY_BUFFER)
    };

    std::vector<BufferViewMeta> buffer_views;
    std::vector<AccessorMeta> accessors;
    std::vector<MeshMeta> meshes;
    std::vector<NodeMeta> nodes;

    for (const auto& ent : scene.entities()) {
        if (!ent || !ent->mesh || ent->mesh->cpu_vertices.empty()) continue;

        const auto& verts = ent->mesh->cpu_vertices;
        const auto& indices = ent->mesh->cpu_indices;

        uint32_t vert_count = static_cast<uint32_t>(verts.size());

        // 1. Positions
        std::vector<glm::vec3> pos_data;
        pos_data.reserve(vert_count);
        glm::vec3 min_p = verts[0].position;
        glm::vec3 max_p = verts[0].position;
        for (const auto& v : verts) {
            pos_data.push_back(v.position);
            min_p = glm::min(min_p, v.position);
            max_p = glm::max(max_p, v.position);
        }

        uint32_t pos_offset = static_cast<uint32_t>(bin_buffer.size());
        uint32_t pos_bytes = vert_count * sizeof(glm::vec3);
        const uint8_t* p_ptr = reinterpret_cast<const uint8_t*>(pos_data.data());
        bin_buffer.insert(bin_buffer.end(), p_ptr, p_ptr + pos_bytes);

        // 2. Normals
        std::vector<glm::vec3> norm_data;
        norm_data.reserve(vert_count);
        for (const auto& v : verts) norm_data.push_back(v.normal);

        uint32_t norm_offset = static_cast<uint32_t>(bin_buffer.size());
        uint32_t norm_bytes = vert_count * sizeof(glm::vec3);
        const uint8_t* n_ptr = reinterpret_cast<const uint8_t*>(norm_data.data());
        bin_buffer.insert(bin_buffer.end(), n_ptr, n_ptr + norm_bytes);

        // 3. UVs
        std::vector<glm::vec2> uv_data;
        uv_data.reserve(vert_count);
        for (const auto& v : verts) uv_data.push_back(v.uv);

        uint32_t uv_offset = static_cast<uint32_t>(bin_buffer.size());
        uint32_t uv_bytes = vert_count * sizeof(glm::vec2);
        const uint8_t* u_ptr = reinterpret_cast<const uint8_t*>(uv_data.data());
        bin_buffer.insert(bin_buffer.end(), u_ptr, u_ptr + uv_bytes);

        // 4. Indices
        std::vector<uint16_t> idx_data = indices;
        if (idx_data.empty()) {
            idx_data.resize(vert_count);
            for (uint32_t i = 0; i < vert_count; ++i) idx_data[i] = static_cast<uint16_t>(i);
        }
        uint32_t idx_count = static_cast<uint32_t>(idx_data.size());
        uint32_t idx_offset = static_cast<uint32_t>(bin_buffer.size());
        uint32_t idx_bytes = idx_count * sizeof(uint16_t);
        const uint8_t* i_ptr = reinterpret_cast<const uint8_t*>(idx_data.data());
        bin_buffer.insert(bin_buffer.end(), i_ptr, i_ptr + idx_bytes);

        // Align buffer to 4 bytes
        while (bin_buffer.size() % 4 != 0) bin_buffer.push_back(0);

        // BufferViews
        uint32_t bv_pos = static_cast<uint32_t>(buffer_views.size());
        buffer_views.push_back({ pos_offset, pos_bytes, 34962 });

        uint32_t bv_norm = static_cast<uint32_t>(buffer_views.size());
        buffer_views.push_back({ norm_offset, norm_bytes, 34962 });

        uint32_t bv_uv = static_cast<uint32_t>(buffer_views.size());
        buffer_views.push_back({ uv_offset, uv_bytes, 34962 });

        uint32_t bv_idx = static_cast<uint32_t>(buffer_views.size());
        buffer_views.push_back({ idx_offset, idx_bytes, 34963 });

        // Accessors
        uint32_t acc_pos = static_cast<uint32_t>(accessors.size());
        accessors.push_back({ bv_pos, 0, 5126, vert_count, "VEC3", min_p, max_p, true });

        uint32_t acc_norm = static_cast<uint32_t>(accessors.size());
        accessors.push_back({ bv_norm, 0, 5126, vert_count, "VEC3", glm::vec3(0.0f), glm::vec3(0.0f), false });

        uint32_t acc_uv = static_cast<uint32_t>(accessors.size());
        accessors.push_back({ bv_uv, 0, 5126, vert_count, "VEC2", glm::vec3(0.0f), glm::vec3(0.0f), false });

        uint32_t acc_idx = static_cast<uint32_t>(accessors.size());
        accessors.push_back({ bv_idx, 0, 5123, idx_count, "SCALAR", glm::vec3(0.0f), glm::vec3(0.0f), false });

        uint32_t current_mesh_idx = static_cast<uint32_t>(meshes.size());
        PrimitiveMeta prim{ acc_pos, acc_norm, acc_uv, acc_idx, 0 };
        meshes.push_back({ ent->name, { prim } });

        nodes.push_back({ ent->name, current_mesh_idx, ent->world_model_matrix() });
    }

    std::string b64_data = base64_encode(bin_buffer.data(), bin_buffer.size());
    std::string uri = "data:application/octet-stream;base64," + b64_data;

    std::ofstream out(filepath);
    if (!out.is_open()) return false;

    out << "{\n";
    out << "  \"asset\": {\n    \"version\": \"2.0\",\n    \"generator\": \"Pielosyty 3D Engine\"\n  },\n";
    out << "  \"scene\": 0,\n";
    out << "  \"scenes\": [\n    {\n      \"nodes\": [";
    for (size_t i = 0; i < nodes.size(); ++i) {
        out << i << (i + 1 < nodes.size() ? ", " : "");
    }
    out << "]\n    }\n  ],\n";

    // Nodes
    out << "  \"nodes\": [\n";
    for (size_t i = 0; i < nodes.size(); ++i) {
        out << "    {\n";
        out << "      \"name\": \"" << nodes[i].name << "\",\n";
        out << "      \"mesh\": " << nodes[i].mesh_idx << ",\n";
        out << "      \"matrix\": [";
        const float* m = glm::value_ptr(nodes[i].matrix);
        for (int k = 0; k < 16; ++k) {
            out << m[k] << (k < 15 ? ", " : "");
        }
        out << "]\n";
        out << "    }" << (i + 1 < nodes.size() ? ",\n" : "\n");
    }
    out << "  ],\n";

    // Meshes
    out << "  \"meshes\": [\n";
    for (size_t i = 0; i < meshes.size(); ++i) {
        out << "    {\n";
        out << "      \"name\": \"" << meshes[i].name << "\",\n";
        out << "      \"primitives\": [\n";
        for (size_t j = 0; j < meshes[i].primitives.size(); ++j) {
            const auto& p = meshes[i].primitives[j];
            out << "        {\n";
            out << "          \"attributes\": {\n";
            out << "            \"POSITION\": " << p.pos_acc_idx << ",\n";
            out << "            \"NORMAL\": " << p.norm_acc_idx << ",\n";
            out << "            \"TEXCOORD_0\": " << p.uv_acc_idx << "\n";
            out << "          },\n";
            out << "          \"indices\": " << p.idx_acc_idx << "\n";
            out << "        }" << (j + 1 < meshes[i].primitives.size() ? ",\n" : "\n");
        }
        out << "      ]\n";
        out << "    }" << (i + 1 < meshes.size() ? ",\n" : "\n");
    }
    out << "  ],\n";

    // Accessors
    out << "  \"accessors\": [\n";
    for (size_t i = 0; i < accessors.size(); ++i) {
        const auto& acc = accessors[i];
        out << "    {\n";
        out << "      \"bufferView\": " << acc.buffer_view_idx << ",\n";
        out << "      \"byteOffset\": " << acc.byte_offset << ",\n";
        out << "      \"componentType\": " << acc.component_type << ",\n";
        out << "      \"count\": " << acc.count << ",\n";
        out << "      \"type\": \"" << acc.type << "\"";
        if (acc.has_min_max) {
            out << ",\n      \"min\": [" << acc.min_v.x << ", " << acc.min_v.y << ", " << acc.min_v.z << "],\n";
            out << "      \"max\": [" << acc.max_v.x << ", " << acc.max_v.y << ", " << acc.max_v.z << "]\n";
        } else {
            out << "\n";
        }
        out << "    }" << (i + 1 < accessors.size() ? ",\n" : "\n");
    }
    out << "  ],\n";

    // BufferViews
    out << "  \"bufferViews\": [\n";
    for (size_t i = 0; i < buffer_views.size(); ++i) {
        const auto& bv = buffer_views[i];
        out << "    {\n";
        out << "      \"buffer\": 0,\n";
        out << "      \"byteOffset\": " << bv.byte_offset << ",\n";
        out << "      \"byteLength\": " << bv.byte_length << ",\n";
        out << "      \"target\": " << bv.target << "\n";
        out << "    }" << (i + 1 < buffer_views.size() ? ",\n" : "\n");
    }
    out << "  ],\n";

    // Buffers
    out << "  \"buffers\": [\n";
    out << "    {\n";
    out << "      \"byteLength\": " << bin_buffer.size() << ",\n";
    out << "      \"uri\": \"" << uri << "\"\n";
    out << "    }\n";
    out << "  ]\n";
    out << "}\n";

    return true;
}

bool save_screenshot(EngineApp& app, const std::string& filepath) {
    int w = app.width() > 0 ? app.width() : 800;
    int h = app.height() > 0 ? app.height() : 600;

    RenderTarget rt(w, h, RenderTargetFormat::RGBA8, true);
    app.render_target(app.scene(), app.camera(), rt);
    std::vector<uint8_t> pixels = app.read_pixels(rt);

    if (pixels.empty() || pixels.size() < static_cast<size_t>(w * h * 4)) {
        // Fallback RGBA buffer (clear color)
        pixels.resize(static_cast<size_t>(w * h * 4), 255);
        auto clr = app.get_clear_color();
        uint8_t r = static_cast<uint8_t>(clr[0] * 255.0f);
        uint8_t g = static_cast<uint8_t>(clr[1] * 255.0f);
        uint8_t b = static_cast<uint8_t>(clr[2] * 255.0f);
        uint8_t a = static_cast<uint8_t>(clr[3] * 255.0f);
        for (size_t i = 0; i < pixels.size(); i += 4) {
            pixels[i] = r;
            pixels[i + 1] = g;
            pixels[i + 2] = b;
            pixels[i + 3] = a;
        }
    }

    int res = stbi_write_png(filepath.c_str(), w, h, 4, pixels.data(), w * 4);
    return (res != 0);
}

// ---------------------------------------------------------------------------
// AssetCache Singleton Implementation
// ---------------------------------------------------------------------------
std::shared_ptr<Mesh> AssetCache::get_mesh(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = meshes_.find(path);
    return (it != meshes_.end()) ? it->second : nullptr;
}

void AssetCache::cache_mesh(const std::string& path, std::shared_ptr<Mesh> mesh) {
    std::lock_guard<std::mutex> lock(mutex_);
    meshes_[path] = mesh;
}

std::shared_ptr<Texture> AssetCache::get_texture(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = textures_.find(path);
    return (it != textures_.end()) ? it->second : nullptr;
}

void AssetCache::cache_texture(const std::string& path, std::shared_ptr<Texture> texture) {
    std::lock_guard<std::mutex> lock(mutex_);
    textures_[path] = texture;
}

std::shared_ptr<Model> AssetCache::get_model(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = models_.find(path);
    return (it != models_.end()) ? it->second : nullptr;
}

void AssetCache::cache_model(const std::string& path, std::shared_ptr<Model> model) {
    std::lock_guard<std::mutex> lock(mutex_);
    models_[path] = model;
}

std::shared_ptr<Mesh> AssetCache::load_mesh(const std::string& path) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = meshes_.find(path);
        if (it != meshes_.end()) return it->second;
    }
    auto mesh = load_mesh_file(path);
    if (mesh) {
        cache_mesh(path, mesh);
    }
    return mesh;
}

std::shared_ptr<Texture> AssetCache::load_texture(const std::string& path, bool srgb) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = textures_.find(path);
        if (it != textures_.end()) return it->second;
    }
    auto tex = Texture::load_from_file(path, srgb);
    if (tex) {
        cache_texture(path, tex);
    }
    return tex;
}

std::shared_ptr<Model> AssetCache::load_model(Scene& scene, const std::string& path) {
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = models_.find(path);
        if (it != models_.end()) return it->second;
    }
    auto model = scene.load_model(path);
    if (model) {
        cache_model(path, model);
    }
    return model;
}

bool AssetCache::has(const std::string& path) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return (meshes_.find(path) != meshes_.end() ||
            textures_.find(path) != textures_.end() ||
            models_.find(path) != models_.end());
}

void AssetCache::remove(const std::string& path) {
    std::lock_guard<std::mutex> lock(mutex_);
    meshes_.erase(path);
    textures_.erase(path);
    models_.erase(path);
}

void AssetCache::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    meshes_.clear();
    textures_.clear();
    models_.clear();
}

size_t AssetCache::size() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return meshes_.size() + textures_.size() + models_.size();
}

} // namespace engine
