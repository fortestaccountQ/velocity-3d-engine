#define CGLTF_IMPLEMENTATION
#include "cgltf.h"

#include "stb_image.h"

#include "engine/model_loader.hpp"
#include "engine/asset_io.hpp"
#include "engine/scene.hpp"
#include "engine/animation.hpp"
#include "engine/skinned_mesh.hpp"

#include <glm/gtc/type_ptr.hpp>
#include <filesystem>
#include <unordered_map>
#include <functional>
#include <iostream>

namespace engine {

std::shared_ptr<Model> ModelLoader::load_model(Scene& scene, const std::string& filepath) {
    std::string ext = std::filesystem::path(filepath).extension().string();
    std::transform(ext.begin(), ext.end(), ext.begin(), ::tolower);
    if (ext == ".obj") {
        return load_obj(scene, filepath);
    } else if (ext == ".stl") {
        return load_stl(scene, filepath);
    } else if (ext == ".ply") {
        return load_ply(scene, filepath);
    }

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

    // 0. Parse Skins & Skeletons
    std::unordered_map<const cgltf_node*, std::shared_ptr<Bone>> node_to_bone;
    std::shared_ptr<Skeleton> skeleton = nullptr;

    if (data->skins_count > 0) {
        cgltf_skin* gltf_skin = &data->skins[0];
        std::vector<std::shared_ptr<Bone>> bones;
        std::vector<glm::mat4> inv_bind_matrices;

        for (cgltf_size j = 0; j < gltf_skin->joints_count; ++j) {
            cgltf_node* jnode = gltf_skin->joints[j];
            std::string bname = (jnode && jnode->name) ? jnode->name : ("Bone_" + std::to_string(j));
            auto bone = std::make_shared<Bone>(bname, static_cast<int>(j));
            bones.push_back(bone);
            if (jnode) {
                node_to_bone[jnode] = bone;
            }
        }

        if (gltf_skin->inverse_bind_matrices) {
            cgltf_accessor* ibm_acc = gltf_skin->inverse_bind_matrices;
            inv_bind_matrices.resize(gltf_skin->joints_count, glm::mat4(1.0f));
            for (cgltf_size j = 0; j < gltf_skin->joints_count; ++j) {
                float m[16];
                cgltf_accessor_read_float(ibm_acc, j, m, 16);
                inv_bind_matrices[j] = glm::make_mat4(m);
            }
        }

        skeleton = std::make_shared<Skeleton>(bones, inv_bind_matrices);
        model->skeleton = skeleton;
    }

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

        auto mat = std::make_shared<StandardMaterial>();
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
            if (pbr.metallic_roughness_texture.texture) {
                mat->metallic_roughness_map = get_or_load_texture(pbr.metallic_roughness_texture.texture);
            }
        }

        if (gltf_mat->normal_texture.texture) {
            mat->normal_map = get_or_load_texture(gltf_mat->normal_texture.texture);
            mat->normal_scale = (gltf_mat->normal_texture.scale != 0.0f) ? gltf_mat->normal_texture.scale : 1.0f;
        }

        if (gltf_mat->occlusion_texture.texture) {
            mat->ao_map = get_or_load_texture(gltf_mat->occlusion_texture.texture);
            mat->occlusion_map = mat->ao_map;
            mat->ao_intensity = (gltf_mat->occlusion_texture.scale != 0.0f) ? gltf_mat->occlusion_texture.scale : 1.0f;
        }

        if (gltf_mat->emissive_texture.texture) {
            mat->emissive_map = get_or_load_texture(gltf_mat->emissive_texture.texture);
        }
        mat->emissive_color = glm::vec3(
            gltf_mat->emissive_factor[0],
            gltf_mat->emissive_factor[1],
            gltf_mat->emissive_factor[2]
        );

        if (gltf_mat->double_sided) {
            mat->side = SideMode::Double;
        }

        if (gltf_mat->alpha_mode == cgltf_alpha_mode_blend) {
            mat->transparent = true;
            mat->blend_mode = BlendMode::Alpha;
            mat->depth_write = false;
        } else if (gltf_mat->alpha_mode == cgltf_alpha_mode_mask) {
            mat->alpha_cutoff = gltf_mat->alpha_cutoff;
        }

        if (!mat->albedo_map) {
            mat->albedo_map = scene.default_white_texture();
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
        if (parent) {
            parent->add(node_entity);
        }

        if (node->has_matrix) {
            node_entity->transform.set_matrix(local_m);
        } else {
            if (node->has_translation) {
                node_entity->transform.position = glm::vec3(node->translation[0], node->translation[1], node->translation[2]);
            }
            if (node->has_rotation) {
                node_entity->transform.set_orientation(glm::quat(node->rotation[3], node->rotation[0], node->rotation[1], node->rotation[2]));
            }
            if (node->has_scale) {
                node_entity->transform.scale = glm::vec3(node->scale[0], node->scale[1], node->scale[2]);
            }
        }
        node_entity->local_matrix = glm::mat4(1.0f);

        if (node_to_bone.count(node)) {
            auto bone = node_to_bone[node];
            bone->transform.position = glm::vec3(0.0f);
            bone->transform.set_orientation(glm::quat(1.0f, 0.0f, 0.0f, 0.0f));
            bone->transform.scale = glm::vec3(1.0f);
            node_entity->add(bone);
        }

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
                const cgltf_accessor* tan_acc = nullptr;
                const cgltf_accessor* joints_acc = nullptr;
                const cgltf_accessor* weights_acc = nullptr;

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
                    } else if (attr.type == cgltf_attribute_type_tangent && attr.index == 0) {
                        tan_acc = attr.data;
                    } else if (attr.type == cgltf_attribute_type_joints && attr.index == 0) {
                        joints_acc = attr.data;
                    } else if (attr.type == cgltf_attribute_type_weights && attr.index == 0) {
                        weights_acc = attr.data;
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

                    if (tan_acc) {
                        cgltf_accessor_read_float(tan_acc, vi, &v.tangent.x, 4);
                    } else {
                        v.tangent = glm::vec4(1.0f, 0.0f, 0.0f, 1.0f);
                    }

                    if (joints_acc) {
                        cgltf_accessor_read_float(joints_acc, vi, &v.joints.x, 4);
                    } else {
                        v.joints = glm::vec4(0.0f);
                    }

                    if (weights_acc) {
                        cgltf_accessor_read_float(weights_acc, vi, &v.weights.x, 4);
                    } else {
                        v.weights = glm::vec4(0.0f);
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

                // If tangents were not provided by the glTF file, compute analytical MikkTSpace-style tangents
                if (!tan_acc && !mesh->cpu_indices.empty()) {
                    std::vector<glm::vec3> tan1(mesh->cpu_vertices.size(), glm::vec3(0.0f));
                    std::vector<glm::vec3> tan2(mesh->cpu_vertices.size(), glm::vec3(0.0f));
                    size_t tri_count = mesh->cpu_indices.size() / 3;
                    for (size_t ti = 0; ti < tri_count; ++ti) {
                        uint16_t i1 = mesh->cpu_indices[ti * 3 + 0];
                        uint16_t i2 = mesh->cpu_indices[ti * 3 + 1];
                        uint16_t i3 = mesh->cpu_indices[ti * 3 + 2];
                        if (i1 >= mesh->cpu_vertices.size() || i2 >= mesh->cpu_vertices.size() || i3 >= mesh->cpu_vertices.size()) {
                            continue;
                        }
                        const auto& v1 = mesh->cpu_vertices[i1];
                        const auto& v2 = mesh->cpu_vertices[i2];
                        const auto& v3 = mesh->cpu_vertices[i3];

                        glm::vec3 p1 = v1.position;
                        glm::vec3 p2 = v2.position;
                        glm::vec3 p3 = v3.position;

                        glm::vec2 w1 = v1.uv;
                        glm::vec2 w2 = v2.uv;
                        glm::vec2 w3 = v3.uv;

                        float x1 = p2.x - p1.x;
                        float x2 = p3.x - p1.x;
                        float y1 = p2.y - p1.y;
                        float y2 = p3.y - p1.y;
                        float z1 = p2.z - p1.z;
                        float z2 = p3.z - p1.z;

                        float s1 = w2.x - w1.x;
                        float s2 = w3.x - w1.x;
                        float t1 = w2.y - w1.y;
                        float t2 = w3.y - w1.y;

                        float det = (s1 * t2 - s2 * t1);
                        if (std::abs(det) > 1e-6f) {
                            float r = 1.0f / det;
                            glm::vec3 sdir((t2 * x1 - t1 * x2) * r, (t2 * y1 - t1 * y2) * r, (t2 * z1 - t1 * z2) * r);
                            glm::vec3 tdir((s1 * x2 - s2 * x1) * r, (s1 * y2 - s2 * y1) * r, (s1 * z2 - s2 * z1) * r);
                            tan1[i1] += sdir;
                            tan1[i2] += sdir;
                            tan1[i3] += sdir;
                            tan2[i1] += tdir;
                            tan2[i2] += tdir;
                            tan2[i3] += tdir;
                        }
                    }
                    for (size_t a = 0; a < mesh->cpu_vertices.size(); ++a) {
                        const glm::vec3& n = mesh->cpu_vertices[a].normal;
                        const glm::vec3& t = tan1[a];
                        float len2 = glm::dot(t, t);
                        glm::vec3 ortho_t = t - n * glm::dot(n, t);
                        float ortho_len2 = glm::dot(ortho_t, ortho_t);
                        if (len2 > 1e-8f && ortho_len2 > 1e-8f) {
                            glm::vec3 tangent_xyz = glm::normalize(ortho_t);
                            float handedness = (glm::dot(glm::cross(n, t), tan2[a]) < 0.0f) ? -1.0f : 1.0f;
                            mesh->cpu_vertices[a].tangent = glm::vec4(tangent_xyz, handedness);
                        } else {
                            glm::vec3 c1 = glm::cross(n, glm::vec3(0.0f, 0.0f, 1.0f));
                            glm::vec3 c2 = glm::cross(n, glm::vec3(0.0f, 1.0f, 0.0f));
                            glm::vec3 tangent_xyz = glm::dot(c1, c1) > glm::dot(c2, c2) ? glm::normalize(c1) : glm::normalize(c2);
                            mesh->cpu_vertices[a].tangent = glm::vec4(tangent_xyz, 1.0f);
                        }
                    }
                }

                mesh->calculate_aabb();
                if ((joints_acc || node->skin) && skeleton) {
                    mesh->mark_dynamic();
                }
                mesh->ensure_gpu_buffers();

                std::shared_ptr<Entity> prim_entity = node_entity;
                if (pi > 0) {
                    prim_entity = scene.create_entity(node_name + "_prim" + std::to_string(pi));
                    prim_entity->parent = node_entity;
                    node_entity->add(prim_entity);
                }
                prim_entity->mesh = mesh;
                prim_entity->material = get_or_load_material(prim.material);
                model->meshes.push_back(prim_entity);

                if ((joints_acc || node->skin) && skeleton) {
                    auto skinned_mesh = std::make_shared<SkinnedMesh>(mesh, skeleton, prim_entity->material);
                    skinned_mesh->name = node_name + "_SkinnedMesh";
                    node_entity->add(skinned_mesh);
                    scene.add_skinned_mesh(skinned_mesh);
                    model->skinned_meshes.push_back(skinned_mesh);
                    prim_entity->visible = false;
                }
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

    // 4. Parse Animations
    for (cgltf_size ai = 0; ai < data->animations_count; ++ai) {
        const cgltf_animation& gltf_anim = data->animations[ai];
        std::string clip_name = gltf_anim.name ? gltf_anim.name : ("Animation_" + std::to_string(ai));
        auto clip = std::make_shared<AnimationClip>(clip_name);

        for (cgltf_size ci = 0; ci < gltf_anim.channels_count; ++ci) {
            const cgltf_animation_channel& chan = gltf_anim.channels[ci];
            if (!chan.target_node || !chan.sampler || !chan.sampler->input || !chan.sampler->output) {
                continue;
            }

            std::string target_name = chan.target_node->name ? chan.target_node->name : "";
            std::string prop_name = "";
            if (chan.target_path == cgltf_animation_path_type_translation) {
                prop_name = "translation";
            } else if (chan.target_path == cgltf_animation_path_type_rotation) {
                prop_name = "rotation";
            } else if (chan.target_path == cgltf_animation_path_type_scale) {
                prop_name = "scale";
            }
            if (prop_name.empty()) continue;

            Interpolation interp = Interpolation::Linear;
            if (chan.sampler->interpolation == cgltf_interpolation_type_step) {
                interp = Interpolation::Step;
            } else if (chan.sampler->interpolation == cgltf_interpolation_type_cubic_spline) {
                interp = Interpolation::CubicSpline;
            }

            cgltf_size key_count = chan.sampler->input->count;
            std::vector<float> times(key_count);
            for (cgltf_size ti = 0; ti < key_count; ++ti) {
                cgltf_accessor_read_float(chan.sampler->input, ti, &times[ti], 1);
            }

            size_t num_comps = (prop_name == "rotation") ? 4 : 3;
            if (interp == Interpolation::CubicSpline) {
                num_comps *= 3;
            }
            std::vector<float> values(key_count * num_comps);
            for (cgltf_size vi = 0; vi < key_count; ++vi) {
                cgltf_accessor_read_float(chan.sampler->output, vi, &values[vi * num_comps], num_comps);
            }

            KeyframeTrack track(target_name, prop_name, times, values, interp);
            clip->add_track(track);
        }

        clip->reset_duration_from_tracks();
        model->animations.push_back(clip);
    }

    cgltf_free(data);
    std::cout << "[ModelLoader] Successfully loaded '" << filepath << "' with "
              << model->meshes.size() << " mesh primitive(s).\n";
    return model;
}

} // namespace engine
