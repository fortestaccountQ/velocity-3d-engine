#include "bind_common.hpp"
#include "engine/mesh.hpp"
#include "engine/node3d.hpp"
#include "engine/transform.hpp"
#include "engine/model.hpp"
#include "engine/model_loader.hpp"

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
        .def_ro("local_aabb", &engine::Mesh::local_aabb)
        .def_ro("cpu_vertices", &engine::Mesh::cpu_vertices)
        .def_ro("cpu_indices", &engine::Mesh::cpu_indices)
        .def("calculate_aabb", &engine::Mesh::calculate_aabb)
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
}
