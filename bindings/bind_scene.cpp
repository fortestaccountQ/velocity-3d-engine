#include "bind_common.hpp"
#include "engine/node3d.hpp"
#include "engine/transform.hpp"
#include "engine/camera.hpp"
#include "engine/light.hpp"
#include "engine/mesh.hpp"
#include "engine/material.hpp"
#include "engine/entity.hpp"
#include "engine/model.hpp"
#include "engine/model_loader.hpp"
#include "engine/scene.hpp"
#include "engine/physics.hpp"
#include "engine/cube_texture.hpp"
#include "engine/sky.hpp"
#include "engine/cube_camera.hpp"
#include "engine/helpers.hpp"
#include "engine/lod.hpp"

static inline glm::vec3 parse_scene_vec3(nb::handle h) {
    if (nb::isinstance<glm::vec3>(h)) return nb::cast<glm::vec3>(h);
    if (nb::isinstance<nb::tuple>(h) || nb::isinstance<nb::list>(h)) {
        auto seq = nb::cast<std::vector<float>>(h);
        if (seq.size() >= 3) return { seq[0], seq[1], seq[2] };
    }
    return {0.0f, 0.0f, 0.0f};
}

static inline glm::vec4 parse_scene_vec4(nb::handle h) {
    if (nb::isinstance<glm::vec4>(h)) return nb::cast<glm::vec4>(h);
    if (nb::isinstance<nb::tuple>(h) || nb::isinstance<nb::list>(h)) {
        auto seq = nb::cast<std::vector<float>>(h);
        if (seq.size() >= 4) return { seq[0], seq[1], seq[2], seq[3] };
        if (seq.size() == 3) return { seq[0], seq[1], seq[2], 1.0f };
    }
    return {0.0f, 0.0f, 0.0f, 1.0f};
}

void bind_scene(nb::module_& m) {
    // -----------------------------------------------------------------------
    // Node3D & Group
    // -----------------------------------------------------------------------
    nb::class_<engine::Node3D>(m, "Node3D")
        .def(nb::init<const std::string&>(), "name"_a = "Node3D")
        .def_rw("id", &engine::Node3D::id)
        .def_rw("uuid", &engine::Node3D::uuid)
        .def_rw("name", &engine::Node3D::name)
        .def_rw("tag", &engine::Node3D::tag)
        .def_rw("visible", &engine::Node3D::visible)
        .def_rw("cast_shadows", &engine::Node3D::cast_shadows)
        .def_rw("receive_shadows", &engine::Node3D::receive_shadows)
        .def_rw("layers", &engine::Node3D::layers)
        .def_rw("transform", &engine::Node3D::transform)
        .def_prop_ro("parent", &engine::Node3D::parent, nb::rv_policy::reference)
        .def_prop_ro("children", &engine::Node3D::children)
        .def("add", &engine::Node3D::add, "child"_a)
        .def("remove", &engine::Node3D::remove, "child"_a)
        .def("remove_from_parent", &engine::Node3D::remove_from_parent)
        .def("clear", &engine::Node3D::clear)
        .def("get_by_name", &engine::Node3D::get_by_name, "name"_a)
        .def("find_all_by_tag", &engine::Node3D::find_all_by_tag, "tag"_a)
        .def("world_matrix", &engine::Node3D::world_matrix)
        .def("world_position", &engine::Node3D::world_position)
        .def("world_orientation", &engine::Node3D::world_orientation)
        .def("world_direction", &engine::Node3D::world_direction)
        .def("world_to_local", &engine::Node3D::world_to_local, "point"_a)
        .def("local_to_world", &engine::Node3D::local_to_world, "point"_a)
        .def("world_aabb", &engine::Node3D::world_aabb);

    nb::class_<engine::Group, engine::Node3D>(m, "Group")
        .def(nb::init<const std::string&>(), "name"_a = "Group");

    // -----------------------------------------------------------------------
    // RaycastHit
    // -----------------------------------------------------------------------
    nb::class_<engine::RaycastHit>(m, "RaycastHit")
        .def(nb::init<>())
        .def_ro("hit", &engine::RaycastHit::hit)
        .def_ro("distance", &engine::RaycastHit::distance)
        .def_ro("point", &engine::RaycastHit::point)
        .def_ro("entity", &engine::RaycastHit::entity)
        .def("__repr__", [](const engine::RaycastHit& h) {
            if (!h.hit) return std::string("RaycastHit(miss)");
            return "RaycastHit(dist=" + std::to_string(h.distance) +
                   ", point=(" + std::to_string(h.point.x) + ", " + std::to_string(h.point.y) + ", " + std::to_string(h.point.z) + "))";
        });

    // -----------------------------------------------------------------------
    // Camera
    // -----------------------------------------------------------------------
    nb::enum_<engine::CameraType>(m, "CameraType")
        .value("Perspective", engine::CameraType::Perspective)
        .value("Orthographic", engine::CameraType::Orthographic)
        .export_values();

    nb::class_<engine::Camera, engine::Node3D>(m, "Camera")
        .def(nb::init<>())
        .def_rw("type", &engine::Camera::type)
        .def_prop_rw("position",
            [](engine::Camera& c) -> glm::vec3& { return c.position; },
            [](engine::Camera& c, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    c.position = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) c.position = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("target",
            [](engine::Camera& c) -> glm::vec3& { return c.target; },
            [](engine::Camera& c, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    c.target = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) c.target = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("up",
            [](engine::Camera& c) -> glm::vec3& { return c.up; },
            [](engine::Camera& c, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    c.up = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) c.up = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("fov", &engine::Camera::fov)
        .def_rw("aspect", &engine::Camera::aspect)
        .def_rw("near_plane", &engine::Camera::near_plane)
        .def_rw("far_plane", &engine::Camera::far_plane)
        .def_rw("yaw", &engine::Camera::yaw)
        .def_rw("pitch", &engine::Camera::pitch)
        .def_prop_rw("viewport",
            [](engine::Camera& c) -> glm::vec4& { return c.viewport; },
            [](engine::Camera& c, const nb::object& val) {
                if (nb::isinstance<glm::vec4>(val)) {
                    c.viewport = nb::cast<glm::vec4>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) c.viewport = { seq[0], seq[1], seq[2], seq[3] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("scissor",
            [](engine::Camera& c) -> glm::vec4& { return c.scissor; },
            [](engine::Camera& c, const nb::object& val) {
                if (nb::isinstance<glm::vec4>(val)) {
                    c.scissor = nb::cast<glm::vec4>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) c.scissor = { seq[0], seq[1], seq[2], seq[3] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("has_scissor", &engine::Camera::has_scissor)
        .def_prop_rw("clear_color",
            [](engine::Camera& c) -> glm::vec4& { return c.clear_color; },
            [](engine::Camera& c, const nb::object& val) {
                if (nb::isinstance<glm::vec4>(val)) {
                    c.clear_color = nb::cast<glm::vec4>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) c.clear_color = { seq[0], seq[1], seq[2], seq[3] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("ortho_left", &engine::Camera::ortho_left)
        .def_rw("ortho_right", &engine::Camera::ortho_right)
        .def_rw("ortho_bottom", &engine::Camera::ortho_bottom)
        .def_rw("ortho_top", &engine::Camera::ortho_top)
        .def_rw("zoom", &engine::Camera::zoom)
        .def("set_perspective", &engine::Camera::set_perspective, "fov"_a, "aspect"_a, "near_z"_a, "far_z"_a)
        .def("set_orthographic", &engine::Camera::set_orthographic,
             "left"_a, "right"_a, "bottom"_a, "top"_a, "near_z"_a = 0.1f, "far_z"_a = 100.0f, "zoom_val"_a = 1.0f)
        .def("set_position", &engine::Camera::set_position, "x"_a, "y"_a, "z"_a)
        .def("set_target", &engine::Camera::set_target, "x"_a, "y"_a, "z"_a)
        .def("rotate", &engine::Camera::rotate, "delta_yaw"_a, "delta_pitch"_a)
        .def("set_yaw_pitch", &engine::Camera::set_yaw_pitch, "yaw"_a, "pitch"_a)
        .def("move_forward", &engine::Camera::move_forward, "distance"_a)
        .def("move_right", &engine::Camera::move_right, "distance"_a)
        .def("move_up", &engine::Camera::move_up, "distance"_a)
        .def("forward", &engine::Camera::forward)
        .def("right", &engine::Camera::right)
        .def("view_matrix", &engine::Camera::view_matrix)
        .def("projection_matrix", &engine::Camera::projection_matrix)
        .def("view_projection_matrix", &engine::Camera::view_projection_matrix)
        .def("screen_to_ray", &engine::Camera::screen_to_ray,
             "mouse_x"_a, "mouse_y"_a, "screen_w"_a, "screen_h"_a);

    nb::class_<engine::PerspectiveCamera, engine::Camera>(m, "PerspectiveCamera")
        .def(nb::init<float, float, float, float>(),
             "fov"_a = 60.0f, "aspect"_a = 1.333f, "near_z"_a = 0.1f, "far_z"_a = 1000.0f);

    nb::class_<engine::OrthographicCamera, engine::Camera>(m, "OrthographicCamera")
        .def(nb::init<float, float, float, float, float, float>(),
             "left"_a = -10.0f, "right"_a = 10.0f, "bottom"_a = -10.0f, "top"_a = 10.0f, "near_z"_a = -100.0f, "far_z"_a = 1000.0f)
        .def_prop_rw("left", &engine::OrthographicCamera::left, &engine::OrthographicCamera::set_left)
        .def_prop_rw("right", &engine::OrthographicCamera::right, &engine::OrthographicCamera::set_right)
        .def_prop_rw("bottom", &engine::OrthographicCamera::bottom, &engine::OrthographicCamera::set_bottom)
        .def_prop_rw("top", &engine::OrthographicCamera::top, &engine::OrthographicCamera::set_top);

    // -----------------------------------------------------------------------
    // Light & Light Types
    // -----------------------------------------------------------------------
    nb::enum_<engine::LightType>(m, "LightType")
        .value("Directional", engine::LightType::Directional)
        .value("Point", engine::LightType::Point)
        .value("Spot", engine::LightType::Spot)
        .value("Hemisphere", engine::LightType::Hemisphere)
        .value("Ambient", engine::LightType::Ambient)
        .export_values();

    nb::class_<engine::Light, engine::Node3D>(m, "Light")
        .def(nb::init<const std::string&, engine::LightType>(), "name"_a = "Light", "type"_a = engine::LightType::Directional)
        .def_rw("type", &engine::Light::type)
        .def_prop_rw("direction",
            [](engine::Light& l) -> glm::vec3& { return l.direction; },
            [](engine::Light& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    auto v = nb::cast<glm::vec3>(val);
                    l.set_direction(v.x, v.y, v.z);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.set_direction(seq[0], seq[1], seq[2]);
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("color",
            [](engine::Light& l) -> glm::vec3& { return l.color; },
            [](engine::Light& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    l.color = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("ambient",
            [](engine::Light& l) -> glm::vec3& { return l.ambient; },
            [](engine::Light& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    l.ambient = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.ambient = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("ambient_sky",
            [](engine::Light& l) -> glm::vec3& { return l.ambient_sky; },
            [](engine::Light& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) l.ambient_sky = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.ambient_sky = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("ambient_ground",
            [](engine::Light& l) -> glm::vec3& { return l.ambient_ground; },
            [](engine::Light& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) l.ambient_ground = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.ambient_ground = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("intensity", &engine::Light::intensity)
        .def_rw("shininess", &engine::Light::shininess)
        .def_rw("range", &engine::Light::range)
        .def("set_direction", &engine::Light::set_direction, "x"_a, "y"_a, "z"_a)
        .def("set_color", &engine::Light::set_color, "r"_a, "g"_a, "b"_a)
        .def("set_ambient", &engine::Light::set_ambient, "r"_a, "g"_a, "b"_a)
        .def("set_hemispheric_ambient", &engine::Light::set_hemispheric_ambient,
             "sr"_a, "sg"_a, "sb"_a, "gr"_a, "gg"_a, "gb"_a)
        .def("get_world_direction", &engine::Light::get_world_direction)
        .def("get_world_position", &engine::Light::get_world_position);

    nb::class_<engine::DirectionalLight, engine::Light>(m, "DirectionalLight")
        .def(nb::init<>())
        .def(nb::init<const std::string&>(), "name"_a = "DirectionalLight")
        .def(nb::init<const std::string&, const glm::vec3&, const glm::vec3&, float>(),
             "name"_a, "direction"_a, "color"_a = glm::vec3(1.0f), "intensity"_a = 1.0f)
        .def_rw("cast_shadow", &engine::DirectionalLight::cast_shadow);

    nb::class_<engine::PointLight, engine::Light>(m, "PointLight")
        .def(nb::init<const std::string&, const glm::vec3&, float, float, float>(),
             "name"_a = "PointLight", "color"_a = glm::vec3(1.0f), "intensity"_a = 1.0f, "range"_a = 10.0f, "decay"_a = 2.0f)
        .def_rw("decay", &engine::PointLight::decay);

    nb::class_<engine::SpotLight, engine::Light>(m, "SpotLight")
        .def(nb::init<const std::string&, const glm::vec3&, float, float>(),
             "name"_a = "SpotLight", "color"_a = glm::vec3(1.0f), "intensity"_a = 1.0f, "range"_a = 15.0f)
        .def_rw("inner_cone_angle", &engine::SpotLight::inner_cone_angle)
        .def_rw("outer_cone_angle", &engine::SpotLight::outer_cone_angle)
        .def_rw("penumbra", &engine::SpotLight::penumbra)
        .def_rw("cast_shadow", &engine::SpotLight::cast_shadow)
        .def("set_cone_angles", &engine::SpotLight::set_cone_angles, "inner_rad"_a, "outer_rad"_a);

    nb::class_<engine::HemisphereLight, engine::Light>(m, "HemisphereLight")
        .def(nb::init<const std::string&, const glm::vec3&, const glm::vec3&, float>(),
             "name"_a = "HemisphereLight", "sky_color"_a = glm::vec3(0.6f, 0.7f, 0.9f),
             "ground_color"_a = glm::vec3(0.3f, 0.25f, 0.2f), "intensity"_a = 1.0f)
        .def_prop_rw("sky_color",
            [](engine::HemisphereLight& l) -> glm::vec3& { return l.sky_color; },
            [](engine::HemisphereLight& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) l.sky_color = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.sky_color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("ground_color",
            [](engine::HemisphereLight& l) -> glm::vec3& { return l.ground_color; },
            [](engine::HemisphereLight& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) l.ground_color = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.ground_color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal);

    nb::class_<engine::AmbientLight, engine::Light>(m, "AmbientLight")
        .def(nb::init<const std::string&, const glm::vec3&, float>(),
             "name"_a = "AmbientLight", "color"_a = glm::vec3(1.0f), "intensity"_a = 0.2f);

    // -----------------------------------------------------------------------
    // Entity
    // -----------------------------------------------------------------------
    nb::class_<engine::Entity, engine::Node3D>(m, "Entity")
        .def(nb::init<>())
        .def(nb::init<const std::string&>(), "name"_a)
        .def(nb::init<uint32_t, const std::string&>(), "id"_a = 0, "name"_a = "Entity")
        .def_prop_rw("mesh",
            [](engine::Entity& e) { return e.mesh; },
            [](engine::Entity& e, std::shared_ptr<engine::Mesh> mesh_ptr) { e.mesh = mesh_ptr; })
        .def_prop_rw("material",
            [](engine::Entity& e) { return e.material; },
            [](engine::Entity& e, std::shared_ptr<engine::Material> mat_ptr) { e.material = mat_ptr; })
        .def_prop_rw("color",
            [](engine::Entity& e) -> glm::vec4& { return e.color; },
            [](engine::Entity& e, const nb::object& val) {
                if (nb::isinstance<glm::vec4>(val)) {
                    e.color = nb::cast<glm::vec4>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) e.color = { seq[0], seq[1], seq[2], seq[3] };
                    else if (seq.size() == 3) e.color = { seq[0], seq[1], seq[2], 1.0f };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("has_collision", &engine::Entity::has_collision)
        .def_rw("collision_scale", &engine::Entity::collision_scale)
        .def_rw("script_path", &engine::Entity::script_path)
        .def_prop_rw("collision_padding",
            [](engine::Entity& e) -> glm::vec3& { return e.collision_padding; },
            [](engine::Entity& e, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) e.collision_padding = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) e.collision_padding = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("parent",
            [](engine::Entity& e) -> std::shared_ptr<engine::Entity> { return e.parent; },
            [](engine::Entity& e, std::shared_ptr<engine::Entity> p) { e.parent = p; })
        .def("world_aabb", &engine::Entity::world_aabb)
        .def("world_bounding_sphere", &engine::Entity::world_bounding_sphere)
        .def("local_collision_box", &engine::Entity::local_collision_box)
        .def("world_obb_corners", [](const engine::Entity& e) {
            auto arr = e.world_obb_corners();
            nb::list res;
            for (const auto& pt : arr) {
                res.append(pt);
            }
            return res;
        })
        .def("set_color", &engine::Entity::set_color, "r"_a, "g"_a, "b"_a, "a"_a = 1.0f);

    // -----------------------------------------------------------------------
    // Scene
    // -----------------------------------------------------------------------
    nb::class_<engine::Scene>(m, "Scene")
        .def(nb::init<>())
        .def_rw("light", &engine::Scene::light)
        .def("create_cube", [](engine::Scene& s, const nb::object& color_obj) {
            glm::vec4 col(1.0f);
            if (nb::isinstance<glm::vec4>(color_obj)) {
                col = nb::cast<glm::vec4>(color_obj);
            } else if (nb::isinstance<nb::tuple>(color_obj) || nb::isinstance<nb::list>(color_obj)) {
                auto seq = nb::cast<std::vector<float>>(color_obj);
                if (seq.size() >= 4) col = { seq[0], seq[1], seq[2], seq[3] };
                else if (seq.size() == 3) col = { seq[0], seq[1], seq[2], 1.0f };
            }
            return s.create_cube(col);
        }, "color"_a = nb::make_tuple(1.0f, 1.0f, 1.0f, 1.0f))
        .def("create_box", [](engine::Scene& s, const nb::object& size_obj, const nb::object& color_obj) {
            glm::vec3 sz(1.0f);
            if (nb::isinstance<glm::vec3>(size_obj)) sz = nb::cast<glm::vec3>(size_obj);
            else if (nb::isinstance<nb::tuple>(size_obj) || nb::isinstance<nb::list>(size_obj)) {
                auto seq = nb::cast<std::vector<float>>(size_obj);
                if (seq.size() >= 3) sz = { seq[0], seq[1], seq[2] };
                else if (seq.size() == 1) sz = { seq[0], seq[0], seq[0] };
            }
            glm::vec4 col(1.0f);
            if (nb::isinstance<glm::vec4>(color_obj)) col = nb::cast<glm::vec4>(color_obj);
            else if (nb::isinstance<nb::tuple>(color_obj) || nb::isinstance<nb::list>(color_obj)) {
                auto seq = nb::cast<std::vector<float>>(color_obj);
                if (seq.size() >= 4) col = { seq[0], seq[1], seq[2], seq[3] };
                else if (seq.size() == 3) col = { seq[0], seq[1], seq[2], 1.0f };
            }
            return s.create_box(sz, col);
        }, "size"_a = nb::make_tuple(1.0f, 1.0f, 1.0f), "color"_a = nb::make_tuple(1.0f, 1.0f, 1.0f, 1.0f))
        .def("create_sphere", [](engine::Scene& s, float radius, int rings, int sectors, const nb::object& color_obj) {
            glm::vec4 col(1.0f);
            if (nb::isinstance<glm::vec4>(color_obj)) col = nb::cast<glm::vec4>(color_obj);
            else if (nb::isinstance<nb::tuple>(color_obj) || nb::isinstance<nb::list>(color_obj)) {
                auto seq = nb::cast<std::vector<float>>(color_obj);
                if (seq.size() >= 4) col = { seq[0], seq[1], seq[2], seq[3] };
                else if (seq.size() == 3) col = { seq[0], seq[1], seq[2], 1.0f };
            }
            return s.create_sphere(radius, rings, sectors, col);
        }, "radius"_a = 1.0f, "rings"_a = 32, "sectors"_a = 32, "color"_a = nb::make_tuple(1.0f, 1.0f, 1.0f, 1.0f))
        .def("create_cylinder", [](engine::Scene& s, float radius, float height, int segments, bool capped, const nb::object& color_obj) {
            glm::vec4 col(1.0f);
            if (nb::isinstance<glm::vec4>(color_obj)) col = nb::cast<glm::vec4>(color_obj);
            else if (nb::isinstance<nb::tuple>(color_obj) || nb::isinstance<nb::list>(color_obj)) {
                auto seq = nb::cast<std::vector<float>>(color_obj);
                if (seq.size() >= 4) col = { seq[0], seq[1], seq[2], seq[3] };
                else if (seq.size() == 3) col = { seq[0], seq[1], seq[2], 1.0f };
            }
            return s.create_cylinder(radius, height, segments, capped, col);
        }, "radius"_a = 0.5f, "height"_a = 2.0f, "segments"_a = 32, "capped"_a = true, "color"_a = nb::make_tuple(1.0f, 1.0f, 1.0f, 1.0f))
        .def("load_model", &engine::Scene::load_model, "filepath"_a)
        .def("create_plane", &engine::Scene::create_plane,
            "size"_a = 10.0f, "uv_tiling"_a = 5.0f, "material"_a = nullptr)
        .def("create_entity", &engine::Scene::create_entity, "name"_a = "Entity")
        .def("add_entity", &engine::Scene::add_entity, "entity"_a)
        .def("remove_entity", &engine::Scene::remove_entity, "entity"_a)
        .def("raycast", &engine::Scene::raycast, "ray"_a, "max_distance"_a = 1000.0f)
        .def("clear", &engine::Scene::clear)
        .def_prop_ro("entities", &engine::Scene::entities)
        .def("add_light", &engine::Scene::add_light, "light"_a)
        .def("remove_light", &engine::Scene::remove_light, "light"_a)
        .def_prop_ro("lights", [](engine::Scene& s) -> const std::vector<std::shared_ptr<engine::Light>>& {
            return s.lights();
        })
        .def("add_instanced_mesh", &engine::Scene::add_instanced_mesh, "mesh"_a)
        .def("remove_instanced_mesh", &engine::Scene::remove_instanced_mesh, "mesh"_a)
        .def_prop_ro("instanced_meshes", [](engine::Scene& s) -> const std::vector<std::shared_ptr<engine::InstancedMesh>>& {
            return s.instanced_meshes();
        })
        .def_prop_ro("root_node", &engine::Scene::root_node)
        .def("add", [](engine::Scene& s, nb::handle obj) {
            if (nb::isinstance<std::shared_ptr<engine::Node3D>>(obj)) {
                s.add(nb::cast<std::shared_ptr<engine::Node3D>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::Entity>>(obj)) {
                s.add_entity(nb::cast<std::shared_ptr<engine::Entity>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::InstancedMesh>>(obj)) {
                s.add_instanced_mesh(nb::cast<std::shared_ptr<engine::InstancedMesh>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::Light>>(obj)) {
                s.add_light(nb::cast<std::shared_ptr<engine::Light>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::ProceduralSky>>(obj)) {
                s.set_procedural_sky(nb::cast<std::shared_ptr<engine::ProceduralSky>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::CubeCamera>>(obj)) {
                s.add(nb::cast<std::shared_ptr<engine::Node3D>>(obj));
            }
        }, "obj"_a)
        .def("remove", [](engine::Scene& s, nb::handle obj) {
            if (nb::isinstance<std::shared_ptr<engine::Node3D>>(obj)) {
                s.remove(nb::cast<std::shared_ptr<engine::Node3D>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::Entity>>(obj)) {
                s.remove_entity(nb::cast<std::shared_ptr<engine::Entity>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::InstancedMesh>>(obj)) {
                s.remove_instanced_mesh(nb::cast<std::shared_ptr<engine::InstancedMesh>>(obj));
            } else if (nb::isinstance<std::shared_ptr<engine::Light>>(obj)) {
                s.remove_light(nb::cast<std::shared_ptr<engine::Light>>(obj));
            }
        }, "obj"_a)
        .def_prop_rw("environment",
            &engine::Scene::environment,
            [](engine::Scene& s, std::optional<std::shared_ptr<engine::CubeTexture>> val) {
                s.set_environment(val.value_or(nullptr), s.environment_intensity());
            })
        .def_prop_rw("environment_intensity", &engine::Scene::environment_intensity, &engine::Scene::set_environment_intensity)
        .def_prop_rw("background_type", &engine::Scene::background_type, &engine::Scene::set_background_type)
        .def_prop_rw("background_cube",
            &engine::Scene::background_cube,
            [](engine::Scene& s, std::optional<std::shared_ptr<engine::CubeTexture>> val) {
                s.set_background_cube(val.value_or(nullptr));
            })
        .def_prop_rw("procedural_sky",
            &engine::Scene::procedural_sky,
            [](engine::Scene& s, std::optional<std::shared_ptr<engine::ProceduralSky>> val) {
                s.set_procedural_sky(val.value_or(nullptr));
            })
        .def_prop_rw("background_color",
            [](engine::Scene& s) -> glm::vec4 { return s.background_color(); },
            [](engine::Scene& s, nb::handle val) {
                if (nb::isinstance<glm::vec4>(val)) s.set_background_color(nb::cast<glm::vec4>(val));
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) s.set_background_color({ seq[0], seq[1], seq[2], seq[3] });
                    else if (seq.size() == 3) s.set_background_color({ seq[0], seq[1], seq[2], 1.0f });
                }
            })
        .def_prop_rw("background",
            [](engine::Scene& s) -> nb::object {
                switch (s.background_type()) {
                    case engine::BackgroundType::ProceduralSky:
                        return nb::cast(s.procedural_sky());
                    case engine::BackgroundType::CubeMap:
                        return nb::cast(s.background_cube());
                    case engine::BackgroundType::Color:
                    default:
                        return nb::cast(s.background_color());
                }
            },
            [](engine::Scene& s, nb::handle val) {
                if (!val.is_valid() || val.is_none()) {
                    s.set_background_color(glm::vec4(0.43137f, 0.62745f, 0.82353f, 1.0f));
                } else if (nb::isinstance<std::shared_ptr<engine::ProceduralSky>>(val)) {
                    s.set_procedural_sky(nb::cast<std::shared_ptr<engine::ProceduralSky>>(val));
                } else if (nb::isinstance<std::shared_ptr<engine::CubeTexture>>(val)) {
                    s.set_background_cube(nb::cast<std::shared_ptr<engine::CubeTexture>>(val));
                } else if (nb::isinstance<glm::vec4>(val)) {
                    s.set_background_color(nb::cast<glm::vec4>(val));
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) s.set_background_color({ seq[0], seq[1], seq[2], seq[3] });
                    else if (seq.size() == 3) s.set_background_color({ seq[0], seq[1], seq[2], 1.0f });
                } else if (nb::hasattr(val, "r") && nb::hasattr(val, "g") && nb::hasattr(val, "b")) {
                    float r = nb::cast<float>(val.attr("r"));
                    float g = nb::cast<float>(val.attr("g"));
                    float b = nb::cast<float>(val.attr("b"));
                    float a = nb::hasattr(val, "a") ? nb::cast<float>(val.attr("a")) : 1.0f;
                    s.set_background_color({ r, g, b, a });
                }
            })
        .def("set_background_cube", [](engine::Scene& s, std::shared_ptr<engine::CubeTexture> cube) {
            s.set_background_cube(cube);
        }, "cube"_a.none() = nb::none())
        .def("set_procedural_sky", [](engine::Scene& s, std::shared_ptr<engine::ProceduralSky> sky) {
            s.set_procedural_sky(sky);
        }, "sky"_a.none() = nb::none())
        .def("set_background_color", [](engine::Scene& s, float r, float g, float b, float a) {
            s.set_background_color(glm::vec4(r, g, b, a));
        }, "r"_a, "g"_a, "b"_a, "a"_a = 1.0f)
        .def("set_environment", [](engine::Scene& s, std::shared_ptr<engine::CubeTexture> env, float intensity) {
            s.set_environment(env, intensity);
        }, "env"_a.none() = nb::none(), "intensity"_a = 1.0f)
        .def_prop_ro("helpers", [](engine::Scene& s) { return s.helpers(); })
        .def_prop_ro("lods", [](engine::Scene& s) { return s.lods(); });

    // -----------------------------------------------------------------------
    // Level of Detail (LOD)
    // -----------------------------------------------------------------------
    nb::class_<engine::LODLevel>(m, "LODLevel")
        .def_ro("node", &engine::LODLevel::node)
        .def_ro("distance", &engine::LODLevel::distance);

    nb::class_<engine::LOD, engine::Node3D>(m, "LOD")
        .def(nb::init<const std::string&>(), "name"_a = "LOD")
        .def("add_level", &engine::LOD::add_level, "node"_a, "distance"_a)
        .def("num_levels", &engine::LOD::num_levels)
        .def("get_level", &engine::LOD::get_level, "index"_a)
        .def("current_level_index", &engine::LOD::current_level_index)
        .def("update_lod", [](engine::LOD& lod, nb::handle cam_pos) {
            lod.update_lod(parse_scene_vec3(cam_pos));
        }, "camera_position"_a)
        .def_prop_ro("levels", [](const engine::LOD& lod) { return lod.levels(); });

    // -----------------------------------------------------------------------
    // Visual Helpers (Phase 5)
    // -----------------------------------------------------------------------
    nb::class_<engine::Helper, engine::Node3D>(m, "Helper")
        .def("update", &engine::Helper::update);

    nb::class_<engine::GridHelper, engine::Helper>(m, "GridHelper")
        .def("__init__", [](engine::GridHelper* h, float size, int divisions, nb::handle col_c, nb::handle col_g) {
            new (h) engine::GridHelper(size, divisions, parse_scene_vec4(col_c), parse_scene_vec4(col_g));
        }, "size"_a = 10.0f, "divisions"_a = 10,
           "color_center"_a = nb::make_tuple(0.8f, 0.8f, 0.8f, 1.0f),
           "color_grid"_a = nb::make_tuple(0.3f, 0.3f, 0.3f, 1.0f))
        .def_rw("size", &engine::GridHelper::size)
        .def_rw("divisions", &engine::GridHelper::divisions)
        .def_rw("color_center", &engine::GridHelper::color_center)
        .def_rw("color_grid", &engine::GridHelper::color_grid);

    nb::class_<engine::AxesHelper, engine::Helper>(m, "AxesHelper")
        .def(nb::init<float>(), "size"_a = 1.0f)
        .def_rw("size", &engine::AxesHelper::size);

    nb::class_<engine::BoxHelper, engine::Helper>(m, "BoxHelper")
        .def("__init__", [](engine::BoxHelper* h, std::shared_ptr<engine::Node3D> target, nb::handle color_obj) {
            new (h) engine::BoxHelper(target, parse_scene_vec4(color_obj));
        }, "target"_a = nullptr, "color"_a = nb::make_tuple(1.0f, 1.0f, 0.0f, 1.0f))
        .def_rw("target", &engine::BoxHelper::target)
        .def_rw("color", &engine::BoxHelper::color)
        .def("set_from_object", &engine::BoxHelper::set_from_object, "obj"_a)
        .def("update", &engine::BoxHelper::update);

    nb::class_<engine::ArrowHelper, engine::Helper>(m, "ArrowHelper")
        .def("__init__", [](engine::ArrowHelper* h, nb::handle dir, nb::handle origin, float length, nb::handle color, float head_length, float head_width) {
            new (h) engine::ArrowHelper(parse_scene_vec3(dir), parse_scene_vec3(origin), length, parse_scene_vec4(color), head_length, head_width);
        }, "dir"_a = nb::make_tuple(0.0f, 1.0f, 0.0f), "origin"_a = nb::make_tuple(0.0f, 0.0f, 0.0f),
           "length"_a = 1.0f, "color"_a = nb::make_tuple(1.0f, 1.0f, 0.0f, 1.0f),
           "head_length"_a = 0.2f, "head_width"_a = 0.1f)
        .def_rw("dir", &engine::ArrowHelper::dir)
        .def_rw("origin", &engine::ArrowHelper::origin)
        .def_rw("length", &engine::ArrowHelper::length)
        .def_rw("color", &engine::ArrowHelper::color)
        .def_rw("head_length", &engine::ArrowHelper::head_length)
        .def_rw("head_width", &engine::ArrowHelper::head_width)
        .def("set_direction", [](engine::ArrowHelper& a, nb::handle dir) {
            a.set_direction(parse_scene_vec3(dir));
        }, "dir"_a)
        .def("set_length", &engine::ArrowHelper::set_length,
             "length"_a, "head_length"_a = -1.0f, "head_width"_a = -1.0f)
        .def("set_color", [](engine::ArrowHelper& a, nb::handle color) {
            a.set_color(parse_scene_vec4(color));
        }, "color"_a);

    nb::class_<engine::DirectionalLightHelper, engine::Helper>(m, "DirectionalLightHelper")
        .def("__init__", [](engine::DirectionalLightHelper* h, std::shared_ptr<engine::DirectionalLight> light, float size, nb::handle color) {
            new (h) engine::DirectionalLightHelper(light, size, parse_scene_vec4(color));
        }, "light"_a = nullptr, "size"_a = 1.0f, "color"_a = nb::make_tuple(1.0f, 1.0f, 0.0f, 1.0f))
        .def_rw("light", &engine::DirectionalLightHelper::light)
        .def_rw("size", &engine::DirectionalLightHelper::size)
        .def_rw("color", &engine::DirectionalLightHelper::color)
        .def("update", &engine::DirectionalLightHelper::update);

    nb::class_<engine::SpotLightHelper, engine::Helper>(m, "SpotLightHelper")
        .def("__init__", [](engine::SpotLightHelper* h, std::shared_ptr<engine::SpotLight> light, nb::handle color) {
            new (h) engine::SpotLightHelper(light, parse_scene_vec4(color));
        }, "light"_a = nullptr, "color"_a = nb::make_tuple(1.0f, 1.0f, 0.0f, 1.0f))
        .def_rw("light", &engine::SpotLightHelper::light)
        .def_rw("color", &engine::SpotLightHelper::color)
        .def("update", &engine::SpotLightHelper::update);

    nb::class_<engine::PointLightHelper, engine::Helper>(m, "PointLightHelper")
        .def("__init__", [](engine::PointLightHelper* h, std::shared_ptr<engine::PointLight> light, float sphere_size, nb::handle color) {
            new (h) engine::PointLightHelper(light, sphere_size, parse_scene_vec4(color));
        }, "light"_a = nullptr, "sphere_size"_a = 0.5f, "color"_a = nb::make_tuple(1.0f, 1.0f, 0.0f, 1.0f))
        .def_rw("light", &engine::PointLightHelper::light)
        .def_rw("sphere_size", &engine::PointLightHelper::sphere_size)
        .def_rw("color", &engine::PointLightHelper::color)
        .def("update", &engine::PointLightHelper::update);

    nb::class_<engine::CameraHelper, engine::Helper>(m, "CameraHelper")
        .def("__init__", [](engine::CameraHelper* h, std::shared_ptr<engine::Camera> cam, nb::handle color) {
            new (h) engine::CameraHelper(cam, parse_scene_vec4(color));
        }, "camera"_a = nullptr, "color"_a = nb::make_tuple(1.0f, 1.0f, 0.0f, 1.0f))
        .def_rw("camera", &engine::CameraHelper::camera)
        .def_rw("color", &engine::CameraHelper::color)
        .def("update", &engine::CameraHelper::update);
}
