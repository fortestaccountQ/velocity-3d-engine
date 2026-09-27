#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/tuple.h>

#include "engine/transform.hpp"
#include "engine/camera.hpp"
#include "engine/light.hpp"
#include "engine/mesh.hpp"
#include "engine/physics.hpp"
#include "engine/texture.hpp"
#include "engine/material.hpp"
#include "engine/entity.hpp"
#include "engine/model.hpp"
#include "engine/model_loader.hpp"
#include "engine/scene.hpp"
#include "engine/input.hpp"
#include "engine/app.hpp"

namespace nb = nanobind;
using namespace nb::literals;

NB_MODULE(_engine_core, m) {
    m.doc() = "Native C++20 3D Engine Core with Textures, Materials, and PBR-lite Pipeline";

    // -----------------------------------------------------------------------
    // Key Enum
    // -----------------------------------------------------------------------
    nb::enum_<engine::Key>(m, "Key")
        .value("INVALID", engine::Key::Invalid)
        .value("SPACE", engine::Key::Space)
        .value("APOSTROPHE", engine::Key::Apostrophe)
        .value("COMMA", engine::Key::Comma)
        .value("MINUS", engine::Key::Minus)
        .value("PERIOD", engine::Key::Period)
        .value("SLASH", engine::Key::Slash)
        .value("NUM_0", engine::Key::Num0)
        .value("NUM_1", engine::Key::Num1)
        .value("NUM_2", engine::Key::Num2)
        .value("NUM_3", engine::Key::Num3)
        .value("NUM_4", engine::Key::Num4)
        .value("NUM_5", engine::Key::Num5)
        .value("NUM_6", engine::Key::Num6)
        .value("NUM_7", engine::Key::Num7)
        .value("NUM_8", engine::Key::Num8)
        .value("NUM_9", engine::Key::Num9)
        .value("A", engine::Key::A)
        .value("B", engine::Key::B)
        .value("C", engine::Key::C)
        .value("D", engine::Key::D)
        .value("E", engine::Key::E)
        .value("F", engine::Key::F)
        .value("G", engine::Key::G)
        .value("H", engine::Key::H)
        .value("I", engine::Key::I)
        .value("J", engine::Key::J)
        .value("K", engine::Key::K)
        .value("L", engine::Key::L)
        .value("M", engine::Key::M)
        .value("N", engine::Key::N)
        .value("O", engine::Key::O)
        .value("P", engine::Key::P)
        .value("Q", engine::Key::Q)
        .value("R", engine::Key::R)
        .value("S", engine::Key::S)
        .value("T", engine::Key::T)
        .value("U", engine::Key::U)
        .value("V", engine::Key::V)
        .value("W", engine::Key::W)
        .value("X", engine::Key::X)
        .value("Y", engine::Key::Y)
        .value("Z", engine::Key::Z)
        .value("ESCAPE", engine::Key::Escape)
        .value("ENTER", engine::Key::Enter)
        .value("TAB", engine::Key::Tab)
        .value("BACKSPACE", engine::Key::Backspace)
        .value("RIGHT", engine::Key::Right)
        .value("LEFT", engine::Key::Left)
        .value("DOWN", engine::Key::Down)
        .value("UP", engine::Key::Up)
        .value("PAGE_UP", engine::Key::PageUp)
        .value("PAGE_DOWN", engine::Key::PageDown)
        .value("HOME", engine::Key::Home)
        .value("END", engine::Key::End)
        .value("LEFT_SHIFT", engine::Key::LeftShift)
        .value("LEFT_CONTROL", engine::Key::LeftControl)
        .value("LEFT_ALT", engine::Key::LeftAlt)
        .export_values();

    // -----------------------------------------------------------------------
    // GLM Math types (Vec3, Vec4)
    // -----------------------------------------------------------------------
    nb::class_<glm::vec3>(m, "Vec3")
        .def(nb::init<>())
        .def(nb::init<float, float, float>(), "x"_a, "y"_a, "z"_a)
        .def_rw("x", &glm::vec3::x)
        .def_rw("y", &glm::vec3::y)
        .def_rw("z", &glm::vec3::z)
        .def("__len__", [](const glm::vec3&) { return 3; })
        .def("__getitem__", [](const glm::vec3& v, size_t i) -> float {
            if (i >= 3) throw nb::index_error();
            return v[static_cast<glm::length_t>(i)];
        })
        .def("__repr__", [](const glm::vec3& v) {
            return "Vec3(" + std::to_string(v.x) + ", " + std::to_string(v.y) + ", " + std::to_string(v.z) + ")";
        });

    nb::class_<glm::vec4>(m, "Vec4")
        .def(nb::init<>())
        .def(nb::init<float, float, float, float>(), "x"_a, "y"_a, "z"_a, "w"_a)
        .def_rw("x", &glm::vec4::x)
        .def_rw("y", &glm::vec4::y)
        .def_rw("z", &glm::vec4::z)
        .def_rw("w", &glm::vec4::w)
        .def("__len__", [](const glm::vec4&) { return 4; })
        .def("__getitem__", [](const glm::vec4& v, size_t i) -> float {
            if (i >= 4) throw nb::index_error();
            return v[static_cast<glm::length_t>(i)];
        })
        .def("__repr__", [](const glm::vec4& v) {
            return "Vec4(" + std::to_string(v.x) + ", " + std::to_string(v.y) + ", " + std::to_string(v.z) + ", " + std::to_string(v.w) + ")";
        });

    // -----------------------------------------------------------------------
    // Physics: AABB, Ray, RaycastHit
    // -----------------------------------------------------------------------
    nb::class_<engine::AABB>(m, "AABB")
        .def(nb::init<>())
        .def(nb::init<const glm::vec3&, const glm::vec3&>(), "min_point"_a, "max_point"_a)
        .def_prop_rw("min_point",
            [](engine::AABB& b) -> glm::vec3& { return b.min_point; },
            [](engine::AABB& b, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) b.min_point = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) b.min_point = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("max_point",
            [](engine::AABB& b) -> glm::vec3& { return b.max_point; },
            [](engine::AABB& b, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) b.max_point = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) b.max_point = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def("is_valid", &engine::AABB::is_valid)
        .def("center", &engine::AABB::center)
        .def("size", &engine::AABB::size)
        .def("extents", &engine::AABB::extents)
        .def("expand", [](engine::AABB& b, const nb::object& obj) {
            if (nb::isinstance<glm::vec3>(obj)) {
                b.expand(nb::cast<glm::vec3>(obj));
            } else if (nb::isinstance<engine::AABB>(obj)) {
                b.expand(nb::cast<engine::AABB>(obj));
            } else if (nb::isinstance<nb::tuple>(obj) || nb::isinstance<nb::list>(obj)) {
                auto seq = nb::cast<std::vector<float>>(obj);
                if (seq.size() >= 3) b.expand({ seq[0], seq[1], seq[2] });
            }
        }, "other"_a)
        .def("contains", [](const engine::AABB& b, const nb::object& obj) -> bool {
            if (nb::isinstance<glm::vec3>(obj)) {
                return b.contains(nb::cast<glm::vec3>(obj));
            } else if (nb::isinstance<nb::tuple>(obj) || nb::isinstance<nb::list>(obj)) {
                auto seq = nb::cast<std::vector<float>>(obj);
                if (seq.size() >= 3) return b.contains({ seq[0], seq[1], seq[2] });
            }
            return false;
        }, "point"_a)
        .def("intersects", &engine::AABB::intersects, "other"_a)
        .def("transformed", [](const engine::AABB& b, const engine::Transform& t) {
            return b.transformed(t.model_matrix());
        }, "transform"_a)
        .def("__repr__", [](const engine::AABB& b) {
            return "AABB(min=(" + std::to_string(b.min_point.x) + ", " + std::to_string(b.min_point.y) + ", " + std::to_string(b.min_point.z) +
                   "), max=(" + std::to_string(b.max_point.x) + ", " + std::to_string(b.max_point.y) + ", " + std::to_string(b.max_point.z) + "))";
        });

    nb::class_<engine::Ray>(m, "Ray")
        .def(nb::init<>())
        .def(nb::init<const glm::vec3&, const glm::vec3&>(), "origin"_a, "direction"_a)
        .def_rw("origin", &engine::Ray::origin)
        .def_rw("direction", &engine::Ray::direction)
        .def("point_at", &engine::Ray::point_at, "t"_a)
        .def("intersect_aabb", [](const engine::Ray& r, const engine::AABB& b) -> nb::tuple {
            float t = 0.0f;
            bool hit = r.intersect_aabb(b, t);
            return nb::make_tuple(hit, t);
        }, "aabb"_a)
        .def("__repr__", [](const engine::Ray& r) {
            return "Ray(origin=(" + std::to_string(r.origin.x) + ", " + std::to_string(r.origin.y) + ", " + std::to_string(r.origin.z) +
                   "), dir=(" + std::to_string(r.direction.x) + ", " + std::to_string(r.direction.y) + ", " + std::to_string(r.direction.z) + "))";
        });

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
    // Mesh
    // -----------------------------------------------------------------------
    nb::class_<engine::Mesh>(m, "Mesh")
        .def(nb::init<>())
        .def_ro("vbuf_id", &engine::Mesh::vbuf_id)
        .def_ro("ibuf_id", &engine::Mesh::ibuf_id)
        .def_ro("num_indices", &engine::Mesh::num_indices)
        .def_ro("local_aabb", &engine::Mesh::local_aabb)
        .def("calculate_aabb", &engine::Mesh::calculate_aabb)
        .def_static("create_cube", &engine::Mesh::create_cube)
        .def_static("create_plane", &engine::Mesh::create_plane, "size"_a = 10.0f, "uv_tiling"_a = 5.0f);

    // -----------------------------------------------------------------------
    // Texture
    // -----------------------------------------------------------------------
    nb::class_<engine::Texture>(m, "Texture")
        .def(nb::init<>())
        .def_static("load_from_file", &engine::Texture::load_from_file, "filepath"_a)
        .def_static("create_checkerboard", &engine::Texture::create_checkerboard,
            "width"_a = 64, "height"_a = 64, "tile_size"_a = 8,
            "color1"_a = 0xFFFFFFFF, "color2"_a = 0xFF2A2A38)
        .def_static("create_solid_color", &engine::Texture::create_solid_color,
            "r"_a, "g"_a, "b"_a, "a"_a = 255)
        .def_ro("width", &engine::Texture::width)
        .def_ro("height", &engine::Texture::height)
        .def_ro("channels", &engine::Texture::channels)
        .def("is_valid", &engine::Texture::is_valid);

    // -----------------------------------------------------------------------
    // Material
    // -----------------------------------------------------------------------
    nb::class_<engine::Material>(m, "Material")
        .def(nb::init<>())
        .def(nb::init<std::shared_ptr<engine::Texture>, float, float>(),
            "texture"_a = nullptr, "roughness"_a = 0.5f, "metallic"_a = 0.0f)
        .def_rw("albedo_map", &engine::Material::albedo_map)
        .def_rw("roughness", &engine::Material::roughness)
        .def_rw("metallic", &engine::Material::metallic)
        .def_prop_rw("base_color",
            [](engine::Material& mat) -> glm::vec4& { return mat.base_color; },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec4>(val)) {
                    mat.base_color = nb::cast<glm::vec4>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) mat.base_color = { seq[0], seq[1], seq[2], seq[3] };
                    else if (seq.size() == 3) mat.base_color = { seq[0], seq[1], seq[2], 1.0f };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("uv_scale",
            [](engine::Material& mat) -> std::pair<float, float> {
                return { mat.uv_scale.x, mat.uv_scale.y };
            },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 2) mat.uv_scale = { seq[0], seq[1] };
                }
            })
        .def("set_color", &engine::Material::set_color, "r"_a, "g"_a, "b"_a, "a"_a = 1.0f)
        .def("set_uv_scale", &engine::Material::set_uv_scale, "u"_a, "v"_a);

    // -----------------------------------------------------------------------
    // Transform
    // -----------------------------------------------------------------------
    nb::class_<engine::Transform>(m, "Transform")
        .def(nb::init<>())
        .def_prop_rw("position",
            [](engine::Transform& t) -> glm::vec3& { return t.position; },
            [](engine::Transform& t, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    t.position = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) t.position = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("rotation",
            [](engine::Transform& t) -> glm::vec3& { return t.rotation; },
            [](engine::Transform& t, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    t.rotation = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) t.rotation = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("scale",
            [](engine::Transform& t) -> glm::vec3& { return t.scale; },
            [](engine::Transform& t, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    t.scale = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) t.scale = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def("set_position", &engine::Transform::set_position, "x"_a, "y"_a, "z"_a)
        .def("set_rotation", &engine::Transform::set_rotation, "rx"_a, "ry"_a, "rz"_a)
        .def("set_scale", &engine::Transform::set_scale, "sx"_a, "sy"_a, "sz"_a);

    // -----------------------------------------------------------------------
    // Camera
    // -----------------------------------------------------------------------
    nb::class_<engine::Camera>(m, "Camera")
        .def(nb::init<>())
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
        .def_rw("near_plane", &engine::Camera::near_plane)
        .def_rw("far_plane", &engine::Camera::far_plane)
        .def_rw("yaw", &engine::Camera::yaw)
        .def_rw("pitch", &engine::Camera::pitch)
        .def("set_position", &engine::Camera::set_position, "x"_a, "y"_a, "z"_a)
        .def("set_target", &engine::Camera::set_target, "x"_a, "y"_a, "z"_a)
        .def("rotate", &engine::Camera::rotate, "delta_yaw"_a, "delta_pitch"_a)
        .def("set_yaw_pitch", &engine::Camera::set_yaw_pitch, "yaw"_a, "pitch"_a)
        .def("move_forward", &engine::Camera::move_forward, "distance"_a)
        .def("move_right", &engine::Camera::move_right, "distance"_a)
        .def("move_up", &engine::Camera::move_up, "distance"_a)
        .def("forward", &engine::Camera::forward)
        .def("right", &engine::Camera::right);

    // -----------------------------------------------------------------------
    // DirectionalLight
    // -----------------------------------------------------------------------
    nb::class_<engine::DirectionalLight>(m, "DirectionalLight")
        .def(nb::init<>())
        .def_prop_rw("direction",
            [](engine::DirectionalLight& l) -> glm::vec3& { return l.direction; },
            [](engine::DirectionalLight& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    l.direction = glm::normalize(nb::cast<glm::vec3>(val));
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.direction = glm::normalize(glm::vec3(seq[0], seq[1], seq[2]));
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("color",
            [](engine::DirectionalLight& l) -> glm::vec3& { return l.color; },
            [](engine::DirectionalLight& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    l.color = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("ambient",
            [](engine::DirectionalLight& l) -> glm::vec3& { return l.ambient; },
            [](engine::DirectionalLight& l, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    l.ambient = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) l.ambient = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("intensity", &engine::DirectionalLight::intensity)
        .def_rw("shininess", &engine::DirectionalLight::shininess)
        .def("set_direction", &engine::DirectionalLight::set_direction, "x"_a, "y"_a, "z"_a)
        .def("set_color", &engine::DirectionalLight::set_color, "r"_a, "g"_a, "b"_a)
        .def("set_ambient", &engine::DirectionalLight::set_ambient, "r"_a, "g"_a, "b"_a);

    // -----------------------------------------------------------------------
    // Entity
    // -----------------------------------------------------------------------
    nb::class_<engine::Entity>(m, "Entity")
        .def_ro("id", &engine::Entity::id)
        .def_rw("name", &engine::Entity::name)
        .def_rw("visible", &engine::Entity::visible)
        .def_rw("transform", &engine::Entity::transform)
        .def_rw("mesh", &engine::Entity::mesh)
        .def_rw("material", &engine::Entity::material)
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
        .def_prop_rw("parent",
            [](engine::Entity& e) -> std::shared_ptr<engine::Entity> { return e.parent; },
            [](engine::Entity& e, std::shared_ptr<engine::Entity> p) { e.parent = p; })
        .def("world_aabb", &engine::Entity::world_aabb)
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
        .def("load_model", &engine::Scene::load_model, "filepath"_a)
        .def("create_plane", &engine::Scene::create_plane,
            "size"_a = 10.0f, "uv_tiling"_a = 5.0f, "material"_a = nullptr)
        .def("create_entity", &engine::Scene::create_entity, "name"_a = "Entity")
        .def("add_entity", &engine::Scene::add_entity, "entity"_a)
        .def("remove_entity", &engine::Scene::remove_entity, "entity"_a)
        .def("raycast", &engine::Scene::raycast, "ray"_a, "max_distance"_a = 1000.0f)
        .def("clear", &engine::Scene::clear)
        .def_prop_ro("entities", &engine::Scene::entities);

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
        .def("world_aabb", &engine::Model::world_aabb);

    // -----------------------------------------------------------------------
    // InputManager
    // -----------------------------------------------------------------------
    nb::class_<engine::InputManager>(m, "InputManager")
        .def("is_key_down", &engine::InputManager::is_key_down, "key"_a)
        .def("is_key_pressed", &engine::InputManager::is_key_pressed, "key"_a)
        .def("is_key_released", &engine::InputManager::is_key_released, "key"_a)
        .def("is_mouse_down", &engine::InputManager::is_mouse_down, "button"_a)
        .def_prop_ro("mouse_x", &engine::InputManager::mouse_x)
        .def_prop_ro("mouse_y", &engine::InputManager::mouse_y)
        .def_prop_ro("mouse_dx", &engine::InputManager::mouse_dx)
        .def_prop_ro("mouse_dy", &engine::InputManager::mouse_dy)
        .def("is_mouse_locked", &engine::InputManager::is_mouse_locked)
        .def("set_mouse_locked", &engine::InputManager::set_mouse_locked, "locked"_a);

    // -----------------------------------------------------------------------
    // EngineApp
    // -----------------------------------------------------------------------
    nb::class_<engine::EngineApp>(m, "EngineApp")
        .def(nb::init<>())
        .def(nb::init<const std::string&, int, int>(),
             "title"_a, "width"_a, "height"_a)
        .def("init", &engine::EngineApp::init,
             "title"_a = "Engine 3D Core",
             "width"_a = 800,
             "height"_a = 600)
        .def("run", &engine::EngineApp::run,
             nb::call_guard<nb::gil_scoped_release>())
        .def("close", &engine::EngineApp::close)
        .def("is_running", &engine::EngineApp::is_running)

        // Subsystems
        .def_prop_ro("scene", &engine::EngineApp::scene, nb::rv_policy::reference_internal)
        .def_prop_ro("camera", &engine::EngineApp::camera, nb::rv_policy::reference_internal)
        .def_prop_ro("input", &engine::EngineApp::input, nb::rv_policy::reference_internal)

        // Texture convenience loaders
        .def("load_texture", [](engine::EngineApp&, const std::string& path) {
            return engine::Texture::load_from_file(path);
        }, "filepath"_a)
        .def("create_checkerboard_texture", [](engine::EngineApp&, int w, int h, int tile) {
            return engine::Texture::create_checkerboard(w, h, tile);
        }, "width"_a = 64, "height"_a = 64, "tile_size"_a = 8)

        // Callbacks
        .def("set_update_callback", [](engine::EngineApp& self, std::optional<engine::EngineApp::UpdateCallback> cb) {
            if (cb.has_value()) {
                self.set_update_callback(std::move(*cb));
            } else {
                self.set_update_callback(nullptr);
            }
        }, "callback"_a.none() = nb::none())

        // Color & Window
        .def("set_clear_color", &engine::EngineApp::set_clear_color, "r"_a, "g"_a, "b"_a, "a"_a = 1.0f)
        .def("get_clear_color", &engine::EngineApp::get_clear_color)
        .def("set_mouse_locked", &engine::EngineApp::set_mouse_locked, "locked"_a)
        .def("is_mouse_locked", &engine::EngineApp::is_mouse_locked)
        .def_prop_ro("width", &engine::EngineApp::width)
        .def_prop_ro("height", &engine::EngineApp::height)
        .def_prop_ro("title", &engine::EngineApp::title);
}
