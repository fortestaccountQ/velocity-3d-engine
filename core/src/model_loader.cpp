#define CGLTF_IMPLEMENTATION
#include "cgltf.h"

#include "stb_image.h"

#include "engine/model_loader.hpp"
#include "engine/scene.hpp"

#include <glm/gtc/type_ptr.hpp>
#include <filesystem>
#include <unordered_map>
#include <functional>
#include <iostream>

namespace engine {

std::shared_ptr<Model> ModelLoader::load_model(Scene& scene, const std::string& filepath) {
    cgltf_options options{};
    cgltf_data* data = nullptr;
    cgltf_result result = cgltf_parse_file(&options, filepath.c_str(), &data);
    if (result != cgltf_result_success || !data) {
        std::cerr << "[ModelLoader] Error: Failed to parse glTF file: " << filepath
                  << " (error code: " << result << ")\n";
        return nullptr;
    }

    result = cgltf_load_buffers(&options, data, filepath.c_str());
    if (result != cgltf_result_success) {
        std::cerr << "[ModelLoader] Error: Failed to load binary buffers for: " << filepath << "\n";
        cgltf_free(data);
        return nullptr;
    }

    std::string model_name = std::filesystem::path(filepath).stem().string();
    auto root_entity = scene.create_entity(model_name + "_Root");
    auto model = std::make_shared<Model>(root_entity, model_name);

    std::filesystem::path base_dir = std::filesystem::path(filepath).parent_path();

    // 1. Texture Cache
    std::unordered_map<const cgltf_image*, std::shared_ptr<Texture>> texture_cache;

    auto get_or_load_texture = [&](const cgltf_texture* gltf_tex) -> std::shared_ptr<Texture> {
        if (!gltf_tex || !gltf_tex->image) {
            return nullptr;
        }

        const cgltf_image* img = gltf_tex->image;
        auto it = texture_cache.find(img);
        if (it != texture_cache.end()) {
            return it->second;
        }

        std::shared_ptr<Texture> loaded_tex = nullptr;

        // Embedded image buffer view (GLB)
        if (img->buffer_view && img->buffer_view->buffer) {
            const uint8_t* ptr = cgltf_buffer_view_data(img->buffer_view);
            size_t size = img->buffer_view->size;
            if (ptr && size > 0) {
                int w = 0, h = 0, comp = 0;
                stbi_set_flip_vertically_on_load(false);
                uint8_t* pixels = stbi_load_from_memory(ptr, static_cast<int>(size), &w, &h, &comp, 4);
                if (pixels) {
                    loaded_tex = Texture::create_from_rgba(w, h, pixels);
                    stbi_image_free(pixels);
                }
            }
        }
        // External file image URI (glTF)
        else if (img->uri && strlen(img->uri) > 0) {
            std::string uri(img->uri);
            // Ignore data URI for now if already handled
            if (uri.rfind("data:", 0) != 0) {
                std::string full_path = (base_dir / uri).string();
                loaded_tex = Texture::load_from_file(full_path);
            }
        }

        if (loaded_tex) {
            texture_cache[img] = loaded_tex;
        }
        return loaded_tex;
    };

    // 2. Material Cache
    std::unordered_map<const cgltf_material*, std::shared_ptr<Material>> material_cache;

    auto get_or_load_material = [&](const cgltf_material* gltf_mat) -> std::shared_ptr<Material> {
        if (!gltf_mat) {
            return scene.default_material();
        }

        auto it = material_cache.find(gltf_mat);
        if (it != material_cache.end()) {
            return it->second;
        }

        auto mat = std::make_shared<Material>();
        if (gltf_mat->has_pbr_metallic_roughness) {
            const auto& pbr = gltf_mat->pbr_metallic_roughness;
            mat->base_color = glm::vec4(
                pbr.base_color_factor[0],
                pbr.base_color_factor[1],
                pbr.base_color_factor[2],
                pbr.base_color_factor[3]
            );
            mat->metallic = pbr.metallic_factor;
            mat->roughness = pbr.roughness_factor;

            if (pbr.base_color_texture.texture) {
                mat->albedo_map = get_or_load_texture(pbr.base_color_texture.texture);
            }
        }

        if (!mat->albedo_map) {
            mat->albedo_map = scene.default_checker_texture();
        }

        material_cache[gltf_mat] = mat;
        return mat;
    };

    // 3. Node Hierarchy & Mesh extraction
    std::function<void(cgltf_node*, std::shared_ptr<Entity>)> process_node =
        [&](cgltf_node* node, std::shared_ptr<Entity> parent) {
        if (!node) return;

        float mat_arr[16];
        cgltf_node_transform_local(node, mat_arr);
        glm::mat4 local_m = glm::make_mat4(mat_arr);

        std::string node_name = node->name ? node->name : (model_name + "_Node");
        auto node_entity = scene.create_entity(node_name);
        node_entity->parent = parent;
        node_entity->local_matrix = local_m;

        if (node->mesh) {
            for (cgltf_size pi = 0; pi < node->mesh->primitives_count; ++pi) {
                const cgltf_primitive& prim = node->mesh->primitives[pi];
                if (prim.type != cgltf_primitive_type_triangles) {
                    continue;
                }

                const cgltf_accessor* pos_acc = nullptr;
                const cgltf_accessor* norm_acc = nullptr;
                const cgltf_accessor* uv_acc = nullptr;
                const cgltf_accessor* col_acc = nullptr;

                for (cgltf_size ai = 0; ai < prim.attributes_count; ++ai) {
                    const auto& attr = prim.attributes[ai];
                    if (attr.type == cgltf_attribute_type_position) {
                        pos_acc = attr.data;
                    } else if (attr.type == cgltf_attribute_type_normal) {
                        norm_acc = attr.data;
                    } else if (attr.type == cgltf_attribute_type_texcoord && attr.index == 0) {
                        uv_acc = attr.data;
                    } else if (attr.type == cgltf_attribute_type_color && attr.index == 0) {
                        col_acc = attr.data;
                    }
                }

                if (!pos_acc || pos_acc->count == 0) {
                    continue;
                }

                auto mesh = std::make_shared<Mesh>();
                mesh->cpu_vertices.resize(pos_acc->count);

                for (cgltf_size vi = 0; vi < pos_acc->count; ++vi) {
                    Vertex& v = mesh->cpu_vertices[vi];
                    cgltf_accessor_read_float(pos_acc, vi, &v.position.x, 3);

                    if (norm_acc) {
                        cgltf_accessor_read_float(norm_acc, vi, &v.normal.x, 3);
                    } else {
                        v.normal = glm::vec3(0.0f, 1.0f, 0.0f);
                    }

                    if (uv_acc) {
                        cgltf_accessor_read_float(uv_acc, vi, &v.uv.x, 2);
                    } else {
                        v.uv = glm::vec2(0.0f, 0.0f);
                    }

                    if (col_acc) {
                        cgltf_accessor_read_float(col_acc, vi, &v.color.x, 4);
                    } else {
                        v.color = glm::vec4(1.0f);
                    }
                }

                if (prim.indices) {
                    mesh->cpu_indices.resize(prim.indices->count);
                    for (cgltf_size ii = 0; ii < prim.indices->count; ++ii) {
                        mesh->cpu_indices[ii] = static_cast<uint16_t>(cgltf_accessor_read_index(prim.indices, ii));
                    }
                    mesh->num_indices = static_cast<int>(prim.indices->count);
                } else {
                    mesh->cpu_indices.resize(pos_acc->count);
                    for (cgltf_size ii = 0; ii < pos_acc->count; ++ii) {
                        mesh->cpu_indices[ii] = static_cast<uint16_t>(ii);
                    }
                    mesh->num_indices = static_cast<int>(pos_acc->count);
                }

                mesh->ensure_gpu_buffers();

                std::shared_ptr<Entity> prim_entity = node_entity;
                if (pi > 0) {
                    prim_entity = scene.create_entity(node_name + "_prim" + std::to_string(pi));
                    prim_entity->parent = node_entity;
                }
                prim_entity->mesh = mesh;
                prim_entity->material = get_or_load_material(prim.material);
                model->meshes.push_back(prim_entity);
            }
        }

        for (cgltf_size ci = 0; ci < node->children_count; ++ci) {
            process_node(node->children[ci], node_entity);
        }
    };

    cgltf_scene* active_scene = data->scene ? data->scene : (data->scenes_count > 0 ? &data->scenes[0] : nullptr);
    if (active_scene) {
        for (cgltf_size ni = 0; ni < active_scene->nodes_count; ++ni) {
            process_node(active_scene->nodes[ni], root_entity);
        }
    } else {
        for (cgltf_size ni = 0; ni < data->nodes_count; ++ni) {
            if (!data->nodes[ni].parent) {
                process_node(&data->nodes[ni], root_entity);
            }
        }
    }

    cgltf_free(data);
    std::cout << "[ModelLoader] Successfully loaded '" << filepath << "' with "
              << model->meshes.size() << " mesh primitive(s).\n";
    return model;
}

} // namespace engine
