#include "bind_common.hpp"
#include <nanobind/ndarray.h>
#include "engine/mesh.hpp"
#include "engine/curve.hpp"
#include "engine/node3d.hpp"
#include "engine/transform.hpp"
#include "engine/model.hpp"
#include "engine/model_loader.hpp"
#include <cstring>

static inline glm::vec2 parse_vec2(nb::handle h) {
    if (nb::isinstance<glm::vec2>(h)) return nb::cast<glm::vec2>(h);
    if (nb::isinstance<nb::tuple>(h) || nb::isinstance<nb::list>(h)) {
        auto seq = nb::cast<std::vector<float>>(h);
        if (seq.size() >= 2) return { seq[0], seq[1] };
    }
    return {0.0f, 0.0f};
}

static inline glm::vec3 parse_vec3(nb::handle h) {
    if (nb::isinstance<glm::vec3>(h)) return nb::cast<glm::vec3>(h);
    if (nb::isinstance<nb::tuple>(h) || nb::isinstance<nb::list>(h)) {
        auto seq = nb::cast<std::vector<float>>(h);
        if (seq.size() >= 3) return { seq[0], seq[1], seq[2] };
    }
    return {0.0f, 0.0f, 0.0f};
}

static inline glm::vec4 parse_vec4(nb::handle h) {
    if (nb::isinstance<glm::vec4>(h)) return nb::cast<glm::vec4>(h);
    if (nb::isinstance<nb::tuple>(h) || nb::isinstance<nb::list>(h)) {
        auto seq = nb::cast<std::vector<float>>(h);
        if (seq.size() >= 4) return { seq[0], seq[1], seq[2], seq[3] };
        if (seq.size() == 3) return { seq[0], seq[1], seq[2], 1.0f };
    }
    return {0.0f, 0.0f, 0.0f, 1.0f};
}

static inline std::vector<glm::vec3> parse_vec3_list(nb::handle h) {
    std::vector<glm::vec3> res;
    if (nb::isinstance<nb::sequence>(h)) {
        for (auto item : nb::cast<nb::sequence>(h)) {
            res.push_back(parse_vec3(item));
        }
    }
    return res;
}

static inline std::vector<glm::vec2> parse_vec2_list(nb::handle h) {
    std::vector<glm::vec2> res;
    if (nb::isinstance<nb::sequence>(h)) {
        for (auto item : nb::cast<nb::sequence>(h)) {
            res.push_back(parse_vec2(item));
        }
    }
    return res;
}

void bind_geometry(nb::module_& m) {
    // -----------------------------------------------------------------------
    // Vertex & Mesh
    // -----------------------------------------------------------------------
    nb::class_<engine::Vertex>(m, "Vertex")
        .def(nb::init<>())
        .def_rw("position", &engine::Vertex::position)
        .def_rw("normal", &engine::Vertex::normal)
        .def_rw("uv", &engine::Vertex::uv)
        .def_rw("color", &engine::Vertex::color)
        .def_rw("tangent", &engine::Vertex::tangent);

    nb::class_<engine::Mesh>(m, "Mesh")
        .def(nb::init<>())
        .def_ro("vbuf_id", &engine::Mesh::vbuf_id)
        .def_ro("ibuf_id", &engine::Mesh::ibuf_id)
        .def_ro("num_indices", &engine::Mesh::num_indices)
        .def_prop_ro("num_vertices", [](const engine::Mesh& mesh) {
            return mesh.cpu_vertices.size();
        })
        .def_ro("local_aabb", &engine::Mesh::local_aabb)
        .def_prop_ro("aabb", [](const engine::Mesh& mesh) {
            return mesh.local_aabb;
        })
        .def_ro("cpu_vertices", &engine::Mesh::cpu_vertices)
        .def_ro("cpu_indices", &engine::Mesh::cpu_indices)
        .def("calculate_aabb", &engine::Mesh::calculate_aabb)
        .def_rw("is_dynamic", &engine::Mesh::is_dynamic)
        .def("mark_dynamic", &engine::Mesh::mark_dynamic)
        .def("update_vertices_raw", [](engine::Mesh& mesh, nb::ndarray<float, nb::c_contig> data) {
            nb::gil_scoped_release release;
            mesh.update_vertices_raw(data.data(), data.size());
        }, "data"_a)
        .def("update_vertices_from_numpy", [](engine::Mesh& mesh, nb::ndarray<float, nb::c_contig> array, bool recalculate_bounds) {
            if (array.ndim() == 2 && array.shape(1) == 3) {
                size_t n = array.shape(0);
                const float* ptr = array.data();
                nb::gil_scoped_release release;
                if (mesh.cpu_vertices.size() < n) {
                    mesh.cpu_vertices.resize(n);
                }
                if (recalculate_bounds && n > 0) {
                    glm::vec3 min_p(ptr[0], ptr[1], ptr[2]);
                    glm::vec3 max_p = min_p;
                    for (size_t i = 0; i < n; ++i) {
                        glm::vec3 p(ptr[i * 3 + 0], ptr[i * 3 + 1], ptr[i * 3 + 2]);
                        mesh.cpu_vertices[i].position = p;
                        min_p = glm::min(min_p, p);
                        max_p = glm::max(max_p, p);
                    }
                    mesh.local_aabb = engine::AABB(min_p, max_p);
                } else {
                    for (size_t i = 0; i < n; ++i) {
                        mesh.cpu_vertices[i].position = glm::vec3(ptr[i * 3 + 0], ptr[i * 3 + 1], ptr[i * 3 + 2]);
                    }
                }
                mesh.update_vertices_raw(reinterpret_cast<const float*>(mesh.cpu_vertices.data()), mesh.cpu_vertices.size() * (sizeof(engine::Vertex) / sizeof(float)));
            } else if (array.ndim() == 2 && array.shape(1) >= 12) {
                size_t n = array.shape(0);
                const float* ptr = array.data();
                nb::gil_scoped_release release;
                if (mesh.cpu_vertices.size() < n) {
                    mesh.cpu_vertices.resize(n);
                }
                size_t stride = array.shape(1);
                if (stride == 16) {
                    std::memcpy(mesh.cpu_vertices.data(), ptr, n * sizeof(engine::Vertex));
                } else {
                    for (size_t i = 0; i < n; ++i) {
                        const float* vp = ptr + i * stride;
                        mesh.cpu_vertices[i].position = { vp[0], vp[1], vp[2] };
                        mesh.cpu_vertices[i].normal   = { vp[3], vp[4], vp[5] };
                        mesh.cpu_vertices[i].uv       = { vp[6], vp[7] };
                        mesh.cpu_vertices[i].color    = { vp[8], vp[9], vp[10], vp[11] };
                    }
                }
                mesh.update_vertices_raw(reinterpret_cast<const float*>(mesh.cpu_vertices.data()), mesh.cpu_vertices.size() * (sizeof(engine::Vertex) / sizeof(float)));
                if (recalculate_bounds) mesh.calculate_aabb();
            } else {
                size_t total_floats = array.size();
                const float* ptr = array.data();
                nb::gil_scoped_release release;
                if (total_floats % 16 == 0 && total_floats / 16 == mesh.cpu_vertices.size()) {
                    // Exact 16-float stride matching engine::Vertex
                    std::memcpy(mesh.cpu_vertices.data(), ptr, mesh.cpu_vertices.size() * sizeof(engine::Vertex));
                    mesh.update_vertices_raw(reinterpret_cast<const float*>(mesh.cpu_vertices.data()), mesh.cpu_vertices.size() * 16);
                    if (recalculate_bounds) mesh.calculate_aabb();
                } else if (total_floats % 12 == 0) {
                    size_t n = total_floats / 12;
                    if (mesh.cpu_vertices.size() < n) mesh.cpu_vertices.resize(n);
                    for (size_t i = 0; i < n; ++i) {
                        const float* vp = ptr + i * 12;
                        mesh.cpu_vertices[i].position = { vp[0], vp[1], vp[2] };
                        mesh.cpu_vertices[i].normal   = { vp[3], vp[4], vp[5] };
                        mesh.cpu_vertices[i].uv       = { vp[6], vp[7] };
                        mesh.cpu_vertices[i].color    = { vp[8], vp[9], vp[10], vp[11] };
                    }
                    mesh.update_vertices_raw(reinterpret_cast<const float*>(mesh.cpu_vertices.data()), mesh.cpu_vertices.size() * 16);
                    if (recalculate_bounds) mesh.calculate_aabb();
                } else if (total_floats % 3 == 0) {
                    size_t n = total_floats / 3;
                    if (mesh.cpu_vertices.size() < n) mesh.cpu_vertices.resize(n);
                    if (recalculate_bounds && n > 0) {
                        glm::vec3 min_p(ptr[0], ptr[1], ptr[2]);
                        glm::vec3 max_p = min_p;
                        for (size_t i = 0; i < n; ++i) {
                            glm::vec3 p(ptr[i * 3 + 0], ptr[i * 3 + 1], ptr[i * 3 + 2]);
                            mesh.cpu_vertices[i].position = p;
                            min_p = glm::min(min_p, p);
                            max_p = glm::max(max_p, p);
                        }
                        mesh.local_aabb = engine::AABB(min_p, max_p);
                    } else {
                        for (size_t i = 0; i < n; ++i) {
                            mesh.cpu_vertices[i].position = { ptr[i * 3 + 0], ptr[i * 3 + 1], ptr[i * 3 + 2] };
                        }
                    }
                    mesh.update_vertices_raw(reinterpret_cast<const float*>(mesh.cpu_vertices.data()), mesh.cpu_vertices.size() * 16);
                } else {
                    mesh.update_vertices_raw(ptr, total_floats);
                }
            }
        }, "array"_a, "recalculate_bounds"_a = true)
        .def_static("from_numpy", [](nb::args args, nb::kwargs kwargs) -> std::shared_ptr<engine::Mesh> {
            if (args.size() < 1) {
                throw std::runtime_error("Mesh.from_numpy expects at least 1 positional argument");
            }
            nb::handle pos_or_verts = args[0];
            nb::handle arg2 = (args.size() >= 2) ? args[1] : nb::none();
            nb::handle arg3 = (args.size() >= 3) ? args[2] : nb::none();
            nb::handle arg4 = (args.size() >= 4) ? args[3] : nb::none();
            nb::handle arg5 = (args.size() >= 5) ? args[4] : nb::none();

            nb::object normals_obj = nb::none();
            nb::object uvs_obj = nb::none();
            nb::object colors_obj = nb::none();
            nb::object indices_obj = nb::none();

            if (kwargs.contains("indices")) indices_obj = kwargs["indices"];
            if (kwargs.contains("normals")) normals_obj = kwargs["normals"];
            if (kwargs.contains("uvs")) uvs_obj = kwargs["uvs"];
            if (kwargs.contains("colors")) colors_obj = kwargs["colors"];

            auto mesh = std::make_shared<engine::Mesh>();

            auto arr = nb::cast<nb::ndarray<float, nb::c_contig>>(pos_or_verts);
            if (arr.ndim() == 2 && arr.shape(1) >= 12) {
                // Interleaved (N, 12+) array
                size_t n = arr.shape(0);
                mesh->cpu_vertices.resize(n);
                const float* p = arr.data();
                size_t stride = arr.shape(1);
                for (size_t i = 0; i < n; ++i) {
                    const float* vp = p + i * stride;
                    mesh->cpu_vertices[i].position = { vp[0], vp[1], vp[2] };
                    mesh->cpu_vertices[i].normal   = { vp[3], vp[4], vp[5] };
                    mesh->cpu_vertices[i].uv       = { vp[6], vp[7] };
                    mesh->cpu_vertices[i].color    = { vp[8], vp[9], vp[10], vp[11] };
                    mesh->cpu_vertices[i].tangent  = { 1.0f, 0.0f, 0.0f, 1.0f };
                }
                if (indices_obj.is_none() && arg2.is_valid() && !arg2.is_none()) {
                    indices_obj = nb::borrow(arg2);
                }
            } else if (arr.ndim() == 1 && arr.size() >= 12 && (arr.size() % 12 == 0)) {
                // Flat 1D array of 12 floats per vertex
                size_t n = arr.size() / 12;
                mesh->cpu_vertices.resize(n);
                const float* p = arr.data();
                for (size_t i = 0; i < n; ++i) {
                    const float* vp = p + i * 12;
                    mesh->cpu_vertices[i].position = { vp[0], vp[1], vp[2] };
                    mesh->cpu_vertices[i].normal   = { vp[3], vp[4], vp[5] };
                    mesh->cpu_vertices[i].uv       = { vp[6], vp[7] };
                    mesh->cpu_vertices[i].color    = { vp[8], vp[9], vp[10], vp[11] };
                    mesh->cpu_vertices[i].tangent  = { 1.0f, 0.0f, 0.0f, 1.0f };
                }
                if (indices_obj.is_none() && arg2.is_valid() && !arg2.is_none()) {
                    indices_obj = nb::borrow(arg2);
                }
            } else if (arr.ndim() == 2 && arr.shape(1) == 3) {
                // Positions (N, 3)
                size_t n = arr.shape(0);
                mesh->cpu_vertices.resize(n);
                const float* p = arr.data();
                for (size_t i = 0; i < n; ++i) {
                    mesh->cpu_vertices[i].position = { p[i * 3 + 0], p[i * 3 + 1], p[i * 3 + 2] };
                    mesh->cpu_vertices[i].normal   = { 0.0f, 1.0f, 0.0f };
                    mesh->cpu_vertices[i].uv       = { 0.0f, 0.0f };
                    mesh->cpu_vertices[i].color    = { 1.0f, 1.0f, 1.0f, 1.0f };
                    mesh->cpu_vertices[i].tangent  = { 1.0f, 0.0f, 0.0f, 1.0f };
                }
                if (arg2.is_valid() && !arg2.is_none() && normals_obj.is_none()) {
                    normals_obj = nb::borrow(arg2);
                }
                if (arg3.is_valid() && !arg3.is_none() && uvs_obj.is_none()) {
                    uvs_obj = nb::borrow(arg3);
                }
                if (arg4.is_valid() && !arg4.is_none() && colors_obj.is_none()) {
                    colors_obj = nb::borrow(arg4);
                }
                if (arg5.is_valid() && !arg5.is_none() && indices_obj.is_none()) {
                    indices_obj = nb::borrow(arg5);
                }
            } else {
                throw std::runtime_error("Mesh::from_numpy: positions array must be (N, 3), (N, 12), or 1D (N*12,)");
            }

            size_t vertex_count = mesh->cpu_vertices.size();

            if (!normals_obj.is_none()) {
                auto normals = nb::cast<nb::ndarray<float, nb::c_contig>>(normals_obj);
                if (normals.ndim() == 2 && normals.shape(0) == vertex_count && normals.shape(1) == 3) {
                    const float* n_ptr = normals.data();
                    for (size_t i = 0; i < vertex_count; ++i) {
                        mesh->cpu_vertices[i].normal = glm::vec3(n_ptr[i * 3 + 0], n_ptr[i * 3 + 1], n_ptr[i * 3 + 2]);
                    }
                }
            }
            if (!uvs_obj.is_none()) {
                auto uvs = nb::cast<nb::ndarray<float, nb::c_contig>>(uvs_obj);
                if (uvs.ndim() == 2 && uvs.shape(0) == vertex_count && uvs.shape(1) == 2) {
                    const float* uv_ptr = uvs.data();
                    for (size_t i = 0; i < vertex_count; ++i) {
                        mesh->cpu_vertices[i].uv = glm::vec2(uv_ptr[i * 2 + 0], uv_ptr[i * 2 + 1]);
                    }
                }
            }
            if (!colors_obj.is_none()) {
                auto colors = nb::cast<nb::ndarray<float, nb::c_contig>>(colors_obj);
                if (colors.ndim() == 2 && colors.shape(0) == vertex_count && colors.shape(1) == 4) {
                    const float* c_ptr = colors.data();
                    for (size_t i = 0; i < vertex_count; ++i) {
                        mesh->cpu_vertices[i].color = glm::vec4(c_ptr[i * 4 + 0], c_ptr[i * 4 + 1], c_ptr[i * 4 + 2], c_ptr[i * 4 + 3]);
                    }
                }
            }
            if (!indices_obj.is_none()) {
                try {
                    auto idx_u16 = nb::cast<nb::ndarray<uint16_t, nb::c_contig>>(indices_obj);
                    size_t n_idx = idx_u16.size();
                    mesh->cpu_indices.assign(idx_u16.data(), idx_u16.data() + n_idx);
                } catch (...) {
                    auto idx_i32 = nb::cast<nb::ndarray<int32_t, nb::c_contig>>(indices_obj);
                    size_t n_idx = idx_i32.size();
                    mesh->cpu_indices.resize(n_idx);
                    for (size_t i = 0; i < n_idx; ++i) {
                        mesh->cpu_indices[i] = static_cast<uint16_t>(idx_i32.data()[i]);
                    }
                }
            } else {
                mesh->cpu_indices.resize(vertex_count);
                for (size_t i = 0; i < vertex_count; ++i) {
                    mesh->cpu_indices[i] = static_cast<uint16_t>(i);
                }
            }

            mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
            mesh->is_dynamic = true;
            mesh->calculate_aabb();
            mesh->ensure_gpu_buffers();
            return mesh;
        })
        .def_static("create_capsule", &engine::Mesh::create_capsule,
            "radius"_a = 0.5f, "length"_a = 1.0f, "cap_segments"_a = 8, "radial_segments"_a = 16)
        .def_static("create_cone", &engine::Mesh::create_cone,
            "radius"_a = 1.0f, "height"_a = 2.0f, "radial_segments"_a = 32, "open_ended"_a = false)
        .def_static("create_torus", &engine::Mesh::create_torus,
            "radius"_a = 1.0f, "tube"_a = 0.4f, "radial_segments"_a = 16, "tubular_segments"_a = 32)
        .def_static("create_torus_knot", &engine::Mesh::create_torus_knot,
            "radius"_a = 1.0f, "tube"_a = 0.4f, "tubular_segments"_a = 64, "radial_segments"_a = 16, "p"_a = 2, "q"_a = 3)
        .def_static("create_circle", &engine::Mesh::create_circle,
            "radius"_a = 1.0f, "segments"_a = 32)
        .def_static("create_ring", [](nb::args args, nb::kwargs kwargs) {
            float inner = 0.5f;
            float outer = 1.0f;
            int segs = 32;
            if (kwargs.contains("inner_radius")) inner = nb::cast<float>(kwargs["inner_radius"]);
            if (kwargs.contains("outer_radius")) outer = nb::cast<float>(kwargs["outer_radius"]);
            if (kwargs.contains("segments")) segs = nb::cast<int>(kwargs["segments"]);
            if (kwargs.contains("theta_segments")) segs = nb::cast<int>(kwargs["theta_segments"]);
            if (args.size() >= 1) inner = nb::cast<float>(args[0]);
            if (args.size() >= 2) outer = nb::cast<float>(args[1]);
            if (args.size() >= 3) segs = nb::cast<int>(args[2]);
            return engine::Mesh::create_ring(inner, outer, segs);
        })
        .def_static("create_icosahedron", &engine::Mesh::create_icosahedron,
            "radius"_a = 1.0f, "subdivisions"_a = 0)
        .def_static("create_octahedron", &engine::Mesh::create_octahedron,
            "radius"_a = 1.0f)
        .def_static("create_tetrahedron", &engine::Mesh::create_tetrahedron,
            "radius"_a = 1.0f)
        .def_static("create_dodecahedron", &engine::Mesh::create_dodecahedron,
            "radius"_a = 1.0f)
        .def_static("create_tube", [](const engine::Curve3& curve, int tubular_segments, float radius, int radial_segments, bool closed) {
            return engine::Mesh::create_tube(curve, tubular_segments, radius, radial_segments, closed);
        }, "curve"_a, "tubular_segments"_a = 64, "radius"_a = 0.2f, "radial_segments"_a = 8, "closed"_a = false)
        .def_static("create_lathe", [](nb::handle pts_h, int segments, float phi_start, float phi_length) {
            return engine::Mesh::create_lathe(parse_vec2_list(pts_h), segments, phi_start, phi_length);
        }, "points"_a, "segments"_a = 32, "phi_start"_a = 0.0f, "phi_length"_a = 6.283185307179586f)
        .def_static("create_extrude", [](nb::handle poly_h, float depth, float bevel_thickness) {
            return engine::Mesh::create_extrude(parse_vec2_list(poly_h), depth, bevel_thickness);
        }, "polygon"_a, "depth"_a = 1.0f, "bevel_thickness"_a = 0.0f)
        .def_static("create_box", &engine::Mesh::create_box,
            "width"_a = 1.0f, "height"_a = 1.0f, "depth"_a = 1.0f)
        .def_static("create_cube", &engine::Mesh::create_cube)
        .def_static("create_sphere", &engine::Mesh::create_sphere,
            "radius"_a = 1.0f, "rings"_a = 32, "sectors"_a = 32)
        .def_static("create_cylinder", &engine::Mesh::create_cylinder,
            "radius"_a = 0.5f, "height"_a = 2.0f, "segments"_a = 32, "capped"_a = true)
        .def_static("create_plane", [](nb::args args, nb::kwargs kwargs) {
            float width = 10.0f;
            float depth = 10.0f;
            int sub_x = 1;
            int sub_z = 1;

            if (kwargs.contains("size")) {
                width = nb::cast<float>(kwargs["size"]);
                depth = width;
            }
            if (kwargs.contains("uv_tiling")) {
                float tiling = nb::cast<float>(kwargs["uv_tiling"]);
                sub_x = std::max(1, static_cast<int>(tiling));
                sub_z = std::max(1, static_cast<int>(tiling));
            }
            if (kwargs.contains("width")) {
                width = nb::cast<float>(kwargs["width"]);
            }
            if (kwargs.contains("depth")) {
                depth = nb::cast<float>(kwargs["depth"]);
            }
            if (kwargs.contains("subdivisions_x")) {
                sub_x = nb::cast<int>(kwargs["subdivisions_x"]);
            }
            if (kwargs.contains("subdivisions_z")) {
                sub_z = nb::cast<int>(kwargs["subdivisions_z"]);
            }
            if (kwargs.contains("subdivisions")) {
                int s = nb::cast<int>(kwargs["subdivisions"]);
                sub_x = s;
                sub_z = s;
            }

            if (args.size() >= 1) width = nb::cast<float>(args[0]);
            if (args.size() >= 2) depth = nb::cast<float>(args[1]);
            if (args.size() >= 3) sub_x = nb::cast<int>(args[2]);
            if (args.size() >= 4) sub_z = nb::cast<int>(args[3]);

            return engine::Mesh::create_plane(width, depth, sub_x, sub_z);
        })
        .def_static("create_custom", [](const std::vector<float>& vertex_floats, const std::vector<uint16_t>& indices, size_t stride_floats) {
            size_t stride = (stride_floats > 0 ? stride_floats : 12);
            size_t vertex_count = vertex_floats.size() / stride;
            return engine::Mesh::create_custom(vertex_floats.data(), vertex_count, indices.data(), indices.size(), stride * sizeof(float));
        }, "vertex_data"_a, "index_data"_a, "stride_floats"_a = 12);

    // -----------------------------------------------------------------------
    // InstancedMesh
    // -----------------------------------------------------------------------
    nb::class_<engine::InstanceData>(m, "InstanceData")
        .def(nb::init<>())
        .def_rw("color", &engine::InstanceData::color);

    nb::class_<engine::InstancedMesh, engine::Node3D>(m, "InstancedMesh")
        .def(nb::init<std::shared_ptr<engine::Mesh>, size_t>(),
             "mesh"_a = nullptr, "count"_a = 0)
        .def_rw("mesh", &engine::InstancedMesh::mesh)
        .def("set_instance_count", &engine::InstancedMesh::set_instance_count, "count"_a)
        .def("instance_count", &engine::InstancedMesh::instance_count)
        .def("set_instance", [](engine::InstancedMesh& im, size_t idx, const nb::object& col_obj) {
            glm::mat4 mat(1.0f);
            glm::vec4 col(1.0f);
            if (nb::isinstance<glm::vec4>(col_obj)) col = nb::cast<glm::vec4>(col_obj);
            else if (nb::isinstance<nb::tuple>(col_obj) || nb::isinstance<nb::list>(col_obj)) {
                auto seq = nb::cast<std::vector<float>>(col_obj);
                if (seq.size() >= 4) col = { seq[0], seq[1], seq[2], seq[3] };
                else if (seq.size() == 3) col = { seq[0], seq[1], seq[2], 1.0f };
            }
            im.set_instance(idx, mat, col);
        }, "index"_a, "color"_a = nb::make_tuple(1.0f, 1.0f, 1.0f, 1.0f))
        .def_ro("inst_vbuf_id", &engine::InstancedMesh::inst_vbuf_id)
        .def("ensure_gpu_buffers", &engine::InstancedMesh::ensure_gpu_buffers)
        .def("destroy", &engine::InstancedMesh::destroy);

    // -----------------------------------------------------------------------
    // Model
    // -----------------------------------------------------------------------
    nb::class_<engine::Model>(m, "Model")
        .def_rw("name", &engine::Model::name)
        .def_prop_ro("transform", [](engine::Model& mod) -> engine::Transform& {
            return mod.transform();
        }, nb::rv_policy::reference_internal)
        .def_prop_ro("root_entity", [](engine::Model& mod) { return mod.root_entity; })
        .def_prop_ro("meshes", [](engine::Model& mod) { return mod.meshes; })
        .def("set_position", &engine::Model::set_position, "x"_a, "y"_a, "z"_a)
        .def("set_rotation", &engine::Model::set_rotation, "rx"_a, "ry"_a, "rz"_a)
        .def("set_scale", &engine::Model::set_scale, "sx"_a, "sy"_a, "sz"_a)
        .def("set_visible", &engine::Model::set_visible, "visible"_a)
        .def_prop_rw("visible",
            &engine::Model::is_visible,
            &engine::Model::set_visible)
        .def_prop_rw("collision_scale",
            &engine::Model::collision_scale,
            &engine::Model::set_collision_scale)
        .def("set_collision_scale", &engine::Model::set_collision_scale, "scale"_a)
        .def("set_collision_padding", &engine::Model::set_collision_padding, "px"_a, "py"_a, "pz"_a)
        .def("set_cast_shadows", &engine::Model::set_cast_shadows, "cast"_a)
        .def("world_aabb", &engine::Model::world_aabb);

    // -----------------------------------------------------------------------
    // Curves (Phase 5)
    // -----------------------------------------------------------------------
    nb::class_<engine::Curve3>(m, "Curve3")
        .def("get_point", &engine::Curve3::get_point, "t"_a)
        .def("get_tangent", &engine::Curve3::get_tangent, "t"_a)
        .def("get_points", &engine::Curve3::get_points, "divisions"_a = 50);

    nb::class_<engine::CatmullRomCurve3, engine::Curve3>(m, "CatmullRomCurve3")
        .def("__init__", [](engine::CatmullRomCurve3* c, nb::handle pts_h, bool closed, float tension) {
            new (c) engine::CatmullRomCurve3(parse_vec3_list(pts_h), closed, tension);
        }, "points"_a, "closed"_a = false, "tension"_a = 0.5f)
        .def_rw("points", &engine::CatmullRomCurve3::points)
        .def_rw("closed", &engine::CatmullRomCurve3::closed)
        .def_rw("tension", &engine::CatmullRomCurve3::tension);

    nb::class_<engine::CubicBezierCurve3, engine::Curve3>(m, "CubicBezierCurve3")
        .def("__init__", [](engine::CubicBezierCurve3* c, nb::handle v0, nb::handle v1, nb::handle v2, nb::handle v3) {
            new (c) engine::CubicBezierCurve3(parse_vec3(v0), parse_vec3(v1), parse_vec3(v2), parse_vec3(v3));
        }, "v0"_a, "v1"_a, "v2"_a, "v3"_a)
        .def_rw("v0", &engine::CubicBezierCurve3::v0)
        .def_rw("v1", &engine::CubicBezierCurve3::v1)
        .def_rw("v2", &engine::CubicBezierCurve3::v2)
        .def_rw("v3", &engine::CubicBezierCurve3::v3);

    nb::class_<engine::QuadraticBezierCurve3, engine::Curve3>(m, "QuadraticBezierCurve3")
        .def("__init__", [](engine::QuadraticBezierCurve3* c, nb::handle v0, nb::handle v1, nb::handle v2) {
            new (c) engine::QuadraticBezierCurve3(parse_vec3(v0), parse_vec3(v1), parse_vec3(v2));
        }, "v0"_a, "v1"_a, "v2"_a)
        .def_rw("v0", &engine::QuadraticBezierCurve3::v0)
        .def_rw("v1", &engine::QuadraticBezierCurve3::v1)
        .def_rw("v2", &engine::QuadraticBezierCurve3::v2);

    nb::class_<engine::LineCurve3, engine::Curve3>(m, "LineCurve3")
        .def("__init__", [](engine::LineCurve3* c, nb::handle v1, nb::handle v2) {
            new (c) engine::LineCurve3(parse_vec3(v1), parse_vec3(v2));
        }, "v1"_a, "v2"_a)
        .def_rw("v1", &engine::LineCurve3::v1)
        .def_rw("v2", &engine::LineCurve3::v2);

    m.def("create_tube", [](const engine::Curve3& curve, int tubular_segments, float radius, int radial_segments, bool closed) {
        return engine::create_tube(curve, tubular_segments, radius, radial_segments, closed);
    }, "curve"_a, "tubular_segments"_a = 64, "radius"_a = 0.2f, "radial_segments"_a = 8, "closed"_a = false);

    m.def("create_lathe", [](nb::handle pts_h, int segments, float phi_start, float phi_length) {
        return engine::create_lathe(parse_vec2_list(pts_h), segments, phi_start, phi_length);
    }, "points"_a, "segments"_a = 32, "phi_start"_a = 0.0f, "phi_length"_a = 6.283185307179586f);

    m.def("create_extrude", [](nb::handle poly_h, float depth, float bevel_thickness) {
        return engine::create_extrude(parse_vec2_list(poly_h), depth, bevel_thickness);
    }, "polygon"_a, "depth"_a = 1.0f, "bevel_thickness"_a = 0.0f);
}
