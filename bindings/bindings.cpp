#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/unordered_map.h>

#include "engine/math_types.hpp"
#include "engine/node3d.hpp"
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
#include "engine/audio.hpp"
#include "engine/app.hpp"
#include "engine/editor.hpp"
#include "engine/render_target.hpp"
#include "engine/post_process.hpp"

namespace nb = nanobind;
using namespace nb::literals;

NB_MODULE(_VelocityEngine_core, m) {
    m.doc() = "VelocityEngine Core: Native C++20 3D Engine with Sokol GFX, PBR Shading, and ImGui Editor";

    // -----------------------------------------------------------------------
    // Mode Enum
    // -----------------------------------------------------------------------
    nb::enum_<engine::EngineMode>(m, "Mode")
        .value("GAME", engine::EngineMode::GAME)
        .value("EDITOR", engine::EngineMode::EDITOR)
        .export_values();

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
        .value("F1", engine::Key::F1)
        .value("F2", engine::Key::F2)
        .value("F3", engine::Key::F3)
        .value("F4", engine::Key::F4)
        .value("F5", engine::Key::F5)
        .export_values();

    // -----------------------------------------------------------------------
    // GLM Math types (Vec3, Vec4)
    // -----------------------------------------------------------------------
    // -----------------------------------------------------------------------
    // GLM Math types (Vec2, Vec3, Vec4)
    // -----------------------------------------------------------------------
    nb::class_<glm::vec2>(m, "Vec2")
        .def(nb::init<>())
        .def(nb::init<float, float>(), "x"_a, "y"_a)
        .def_rw("x", &glm::vec2::x)
        .def_rw("y", &glm::vec2::y)
        .def("__len__", [](const glm::vec2&) { return 2; })
        .def("__getitem__", [](const glm::vec2& v, size_t i) -> float {
            if (i >= 2) throw nb::index_error();
            return v[static_cast<glm::length_t>(i)];
        })
        .def("__repr__", [](const glm::vec2& v) {
            return "Vec2(" + std::to_string(v.x) + ", " + std::to_string(v.y) + ")";
        });

    // -----------------------------------------------------------------------
    // UI Command Contract (Phase 0.1)
    // -----------------------------------------------------------------------
    nb::enum_<engine::UICommandType>(m, "UICommandType")
        .value("Text", engine::UICommandType::Text)
        .value("Rect", engine::UICommandType::Rect)
        .value("Line", engine::UICommandType::Line)
        .value("Crosshair", engine::UICommandType::Crosshair)
        .export_values();

    nb::class_<engine::UICommand>(m, "UICommand")
        .def(nb::init<>())
        .def_rw("type", &engine::UICommand::type)
        .def_rw("text", &engine::UICommand::text)
        .def_prop_rw("pos",
            [](const engine::UICommand& c) { return c.pos; },
            [](engine::UICommand& c, const nb::object& o) {
                if (nb::isinstance<glm::vec2>(o)) c.pos = nb::cast<glm::vec2>(o);
                else if (nb::isinstance<nb::tuple>(o) || nb::isinstance<nb::list>(o)) {
                    auto s = nb::cast<std::vector<float>>(o);
                    if (s.size() >= 2) c.pos = { s[0], s[1] };
                }
            })
        .def_prop_rw("size",
            [](const engine::UICommand& c) { return c.size; },
            [](engine::UICommand& c, const nb::object& o) {
                if (nb::isinstance<glm::vec2>(o)) c.size = nb::cast<glm::vec2>(o);
                else if (nb::isinstance<nb::tuple>(o) || nb::isinstance<nb::list>(o)) {
                    auto s = nb::cast<std::vector<float>>(o);
                    if (s.size() >= 2) c.size = { s[0], s[1] };
                }
            })
        .def_prop_rw("color",
            [](const engine::UICommand& c) { return c.color; },
            [](engine::UICommand& c, const nb::object& o) {
                if (nb::isinstance<glm::vec4>(o)) c.color = nb::cast<glm::vec4>(o);
                else if (nb::isinstance<nb::tuple>(o) || nb::isinstance<nb::list>(o)) {
                    auto s = nb::cast<std::vector<float>>(o);
                    if (s.size() >= 4) c.color = { s[0], s[1], s[2], s[3] };
                    else if (s.size() == 3) c.color = { s[0], s[1], s[2], 1.0f };
                }
            })
        .def_rw("thickness", &engine::UICommand::thickness);

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

    nb::class_<glm::mat4>(m, "Mat4")
        .def(nb::init<>())
        .def(nb::init<float>(), "diagonal"_a = 1.0f)
        .def("__getitem__", [](const glm::mat4& m, size_t col) -> glm::vec4 {
            if (col >= 4) throw nb::index_error();
            return m[static_cast<glm::length_t>(col)];
        })
        .def("__len__", [](const glm::mat4&) { return 4; })
        .def("to_list", [](const glm::mat4& m) {
            nb::list rows;
            for (int r = 0; r < 4; ++r) {
                nb::list row;
                for (int c = 0; c < 4; ++c) {
                    row.append(m[c][r]);
                }
                rows.append(row);
            }
            return rows;
        })
        .def("__repr__", [](const glm::mat4& m) {
            std::string s = "Mat4(";
            for (int c = 0; c < 4; ++c) {
                for (int r = 0; r < 4; ++r) {
                    s += std::to_string(m[c][r]) + (c == 3 && r == 3 ? ")" : ", ");
                }
            }
            return s;
        });

    // -----------------------------------------------------------------------
    // GLM Math types (Quat) & Quaternion Helper Functions
    // -----------------------------------------------------------------------
    nb::class_<glm::quat>(m, "Quat")
        .def(nb::init<>())
        .def(nb::init<float, float, float, float>(), "w"_a, "x"_a, "y"_a, "z"_a)
        .def_rw("w", &glm::quat::w)
        .def_rw("x", &glm::quat::x)
        .def_rw("y", &glm::quat::y)
        .def_rw("z", &glm::quat::z)
        .def("__len__", [](const glm::quat&) { return 4; })
        .def("__getitem__", [](const glm::quat& q, size_t i) -> float {
            if (i >= 4) throw nb::index_error();
            return q[static_cast<glm::length_t>(i)];
        })
        .def("__mul__", [](const glm::quat& q1, const glm::quat& q2) {
            return q1 * q2;
        })
        .def("__mul__", [](const glm::quat& q, const glm::vec3& v) {
            return q * v;
        })
        .def("__repr__", [](const glm::quat& q) {
            return "Quat(w=" + std::to_string(q.w) + ", x=" + std::to_string(q.x) +
                   ", y=" + std::to_string(q.y) + ", z=" + std::to_string(q.z) + ")";
        });

    m.def("quat_from_euler", [](float pitch, float yaw, float roll, const std::string& order) {
        return engine::quat_from_euler(pitch, yaw, roll, order);
    }, "pitch"_a, "yaw"_a, "roll"_a, "order"_a = "YXZ");
    m.def("quat_to_euler", [](const glm::quat& q, const std::string& order) {
        return engine::quat_to_euler(q, order);
    }, "q"_a, "order"_a = "YXZ");
    m.def("quat_from_axis_angle", [](const glm::vec3& axis, float deg) {
        return engine::quat_from_axis_angle(axis, deg);
    }, "axis"_a, "deg"_a);
    m.def("quat_look_rotation", [](const glm::vec3& forward, const glm::vec3& up) {
        return engine::quat_look_rotation(forward, up);
    }, "forward"_a, "up"_a = glm::vec3(0.0f, 1.0f, 0.0f));
    m.def("quat_slerp", [](const glm::quat& q1, const glm::quat& q2, float t) {
        return engine::quat_slerp(q1, q2, t);
    }, "q1"_a, "q2"_a, "t"_a);

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
        .def("expand", [](engine::AABB& b, nb::handle obj) {
            if (nb::isinstance<glm::vec3>(obj)) {
                b.expand(nb::cast<glm::vec3>(obj));
            } else if (nb::isinstance<engine::AABB>(obj)) {
                b.expand(nb::cast<engine::AABB>(obj));
            } else if (nb::isinstance<nb::tuple>(obj) || nb::isinstance<nb::list>(obj)) {
                auto seq = nb::cast<std::vector<float>>(obj);
                if (seq.size() >= 3) b.expand({ seq[0], seq[1], seq[2] });
            }
        }, "other"_a)
        .def("contains", [](const engine::AABB& b, nb::handle obj) -> bool {
            if (nb::isinstance<glm::vec3>(obj)) {
                return b.contains(nb::cast<glm::vec3>(obj));
            } else if (nb::isinstance<nb::tuple>(obj) || nb::isinstance<nb::list>(obj)) {
                auto seq = nb::cast<std::vector<float>>(obj);
                if (seq.size() >= 3) return b.contains({ seq[0], seq[1], seq[2] });
            }
            return false;
        }, "point"_a)
        .def("intersects", &engine::AABB::intersects, "other"_a)
        .def("scaled", &engine::AABB::scaled, "scale"_a)
        .def("get_penetration", [](const engine::AABB& a, const engine::AABB& b) -> std::optional<glm::vec3> {
            glm::vec3 mtv{0.0f};
            if (a.get_penetration(b, mtv)) {
                return mtv;
            }
            return std::nullopt;
        }, "other"_a)
        .def("transformed", [](const engine::AABB& b, const engine::Transform& t) {
            return b.transformed(t.model_matrix());
        }, "transform"_a)
        .def("__repr__", [](const engine::AABB& b) {
            return "AABB(min=(" + std::to_string(b.min_point.x) + ", " + std::to_string(b.min_point.y) + ", " + std::to_string(b.min_point.z) +
                   "), max=(" + std::to_string(b.max_point.x) + ", " + std::to_string(b.max_point.y) + ", " + std::to_string(b.max_point.z) + "))";
        });

    nb::class_<engine::BoundingSphere>(m, "BoundingSphere")
        .def(nb::init<>())
        .def(nb::init<const glm::vec3&, float>(), "center"_a, "radius"_a)
        .def_rw("center", &engine::BoundingSphere::center)
        .def_rw("radius", &engine::BoundingSphere::radius)
        .def("is_valid", &engine::BoundingSphere::is_valid)
        .def_static("from_aabb", &engine::BoundingSphere::from_aabb, "aabb"_a)
        .def("__repr__", [](const engine::BoundingSphere& s) {
            return "BoundingSphere(center=(" + std::to_string(s.center.x) + ", " +
                   std::to_string(s.center.y) + ", " + std::to_string(s.center.z) +
                   "), radius=" + std::to_string(s.radius) + ")";
        });

    nb::class_<engine::Cylinder>(m, "Cylinder")
        .def(nb::init<>())
        .def(nb::init<const glm::vec3&, float, float>(), "base"_a, "radius"_a = 0.35f, "height"_a = 1.8f)
        .def_prop_rw("base",
            [](engine::Cylinder& c) -> glm::vec3& { return c.base; },
            [](engine::Cylinder& c, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) c.base = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) c.base = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("radius", &engine::Cylinder::radius)
        .def_rw("height", &engine::Cylinder::height)
        .def("aabb", &engine::Cylinder::aabb)
        .def("intersects_aabb", &engine::Cylinder::intersects_aabb, "box"_a)
        .def("get_penetration_aabb", [](const engine::Cylinder& c, const engine::AABB& b) -> nb::tuple {
            glm::vec3 mtv{0.0f};
            bool hit = c.get_penetration_aabb(b, mtv);
            return nb::make_tuple(hit, mtv);
        }, "box"_a)
        .def("__repr__", [](const engine::Cylinder& c) {
            return "Cylinder(base=(" + std::to_string(c.base.x) + ", " + std::to_string(c.base.y) + ", " + std::to_string(c.base.z) +
                   "), r=" + std::to_string(c.radius) + ", h=" + std::to_string(c.height) + ")";
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
        .def("intersect_sphere", [](const engine::Ray& r, const engine::BoundingSphere& s) -> nb::tuple {
            float t = 0.0f;
            bool hit = r.intersect_sphere(s, t);
            return nb::make_tuple(hit, t);
        }, "sphere"_a)
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
    // Plane, Frustum & RenderStats
    // -----------------------------------------------------------------------
    nb::class_<engine::Plane>(m, "Plane")
        .def(nb::init<>())
        .def(nb::init<const glm::vec3&, float>(), "normal"_a, "constant"_a)
        .def_rw("normal", &engine::Plane::normal)
        .def_rw("constant", &engine::Plane::constant)
        .def("distance_to_point", &engine::Plane::distance_to_point, "point"_a);

    nb::class_<engine::Frustum>(m, "Frustum")
        .def(nb::init<>())
        .def("set_from_projection_matrix", &engine::Frustum::set_from_projection_matrix, "matrix"_a)
        .def("intersects_sphere", &engine::Frustum::intersects_sphere, "center"_a, "radius"_a)
        .def("intersects_aabb", [](const engine::Frustum& f, const engine::AABB& box) {
            return f.intersects_aabb(box.min_point, box.max_point);
        }, "box"_a)
        .def("intersects_aabb", [](const engine::Frustum& f, const glm::vec3& min_point, const glm::vec3& max_point) {
            return f.intersects_aabb(min_point, max_point);
        }, "min_point"_a, "max_point"_a);

    nb::class_<engine::RenderStats>(m, "RenderStats")
        .def(nb::init<>())
        .def_ro("draw_calls", &engine::RenderStats::draw_calls)
        .def_ro("culled_objects", &engine::RenderStats::culled_objects)
        .def_ro("total_triangles", &engine::RenderStats::total_triangles)
        .def_ro("total_instances", &engine::RenderStats::total_instances)
        .def("__repr__", [](const engine::RenderStats& s) {
            return "RenderStats(draw_calls=" + std::to_string(s.draw_calls) +
                   ", culled=" + std::to_string(s.culled_objects) +
                   ", triangles=" + std::to_string(s.total_triangles) +
                   ", instances=" + std::to_string(s.total_instances) + ")";
        });

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
    // Transform
    // -----------------------------------------------------------------------
    nb::class_<engine::Transform>(m, "Transform")
        .def(nb::init<>())
        .def(nb::init<const glm::vec3&, const glm::vec3&, const glm::vec3&>(),
             "position"_a = glm::vec3(0.0f), "rotation"_a = glm::vec3(0.0f), "scale"_a = glm::vec3(1.0f))
        .def(nb::init<const glm::vec3&, const glm::quat&, const glm::vec3&>(),
             "position"_a = glm::vec3(0.0f), "orientation"_a = glm::quat(1.0f, 0.0f, 0.0f, 0.0f), "scale"_a = glm::vec3(1.0f))
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
            [](engine::Transform& t) -> glm::vec3& {
                t.sync_euler_from_orientation();
                return t.rotation_euler;
            },
            [](engine::Transform& t, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    t.set_rotation(nb::cast<glm::vec3>(val));
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) t.set_rotation(seq[0], seq[1], seq[2]);
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("orientation",
            [](engine::Transform& t) -> glm::quat& { return t.orientation; },
            [](engine::Transform& t, const nb::object& val) {
                if (nb::isinstance<glm::quat>(val)) {
                    t.set_orientation(nb::cast<glm::quat>(val));
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) t.set_orientation(glm::quat(seq[0], seq[1], seq[2], seq[3]));
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
        .def("set_position", nb::overload_cast<float, float, float>(&engine::Transform::set_position), "x"_a, "y"_a, "z"_a)
        .def("set_rotation", nb::overload_cast<float, float, float>(&engine::Transform::set_rotation), "rx"_a, "ry"_a, "rz"_a)
        .def("set_scale", nb::overload_cast<float, float, float>(&engine::Transform::set_scale), "sx"_a, "sy"_a, "sz"_a)
        .def("translate", &engine::Transform::translate, "v"_a)
        .def("rotate_x", &engine::Transform::rotate_x, "deg"_a)
        .def("rotate_y", &engine::Transform::rotate_y, "deg"_a)
        .def("rotate_z", &engine::Transform::rotate_z, "deg"_a)
        .def("rotate_on_axis", &engine::Transform::rotate_on_axis, "axis"_a, "deg"_a)
        .def("look_at", &engine::Transform::look_at, "target"_a, "up"_a = glm::vec3(0.0f, 1.0f, 0.0f))
        .def("set_orientation", &engine::Transform::set_orientation, "q"_a)
        .def("get_orientation", &engine::Transform::get_orientation)
        .def("model_matrix", &engine::Transform::model_matrix)
        .def("normal_matrix", &engine::Transform::normal_matrix);

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
    // Texture
    // -----------------------------------------------------------------------
    nb::class_<engine::Texture>(m, "Texture")
        .def(nb::init<>())
        .def_static("load_from_file", [](const std::string& filepath, bool is_pixel_art) {
            return engine::Texture::load_from_file(filepath, is_pixel_art);
        }, "filepath"_a, "is_pixel_art"_a = false)
        .def_static("create_from_rgba", [](int width, int height, const nb::bytes& data, bool is_pixel_art) {
            return engine::Texture::create_from_rgba(
                width,
                height,
                reinterpret_cast<const uint8_t*>(data.data()),
                is_pixel_art
            );
        }, "width"_a, "height"_a, "data"_a, "is_pixel_art"_a = false)
        .def_static("create_data_texture", [](int width, int height, const nb::bytes& data, int channels) {
            return engine::Texture::create_data_texture(
                width,
                height,
                reinterpret_cast<const uint8_t*>(data.data()),
                channels
            );
        }, "width"_a, "height"_a, "data"_a, "channels"_a = 4)
        .def_static("create_checkerboard", &engine::Texture::create_checkerboard,
            "width"_a = 64, "height"_a = 64, "tile_size"_a = 8,
            "color1"_a = 0xFFFFFFFF, "color2"_a = 0xFF2A2A38)
        .def_static("create_solid_color", &engine::Texture::create_solid_color,
            "r"_a, "g"_a, "b"_a, "a"_a = 255)
        .def_ro("width", &engine::Texture::width)
        .def_ro("height", &engine::Texture::height)
        .def_ro("channels", &engine::Texture::channels)
        .def_rw("is_pixel_art", &engine::Texture::is_pixel_art)
        .def_rw("wrap_s", &engine::Texture::wrap_s)
        .def_rw("wrap_t", &engine::Texture::wrap_t)
        .def_rw("filter_min", &engine::Texture::filter_min)
        .def_rw("filter_mag", &engine::Texture::filter_mag)
        .def("is_valid", &engine::Texture::is_valid)
        .def("__call__", [](std::shared_ptr<engine::Texture> self) { return self; });

    // -----------------------------------------------------------------------
    // Material Enums
    // -----------------------------------------------------------------------
    nb::enum_<engine::SideMode>(m, "SideMode")
        .value("Front", engine::SideMode::Front)
        .value("Back", engine::SideMode::Back)
        .value("Double", engine::SideMode::Double)
        .export_values();

    nb::enum_<engine::BlendMode>(m, "BlendMode")
        .value("Opaque", engine::BlendMode::Opaque)
        .value("Alpha", engine::BlendMode::Alpha)
        .value("Additive", engine::BlendMode::Additive)
        .value("Multiply", engine::BlendMode::Multiply)
        .export_values();

    nb::enum_<engine::TextureFilter>(m, "TextureFilter")
        .value("Nearest", engine::TextureFilter::Nearest)
        .value("Linear", engine::TextureFilter::Linear)
        .export_values();

    nb::enum_<engine::TextureWrap>(m, "TextureWrap")
        .value("Repeat", engine::TextureWrap::Repeat)
        .value("ClampToEdge", engine::TextureWrap::ClampToEdge)
        .value("MirroredRepeat", engine::TextureWrap::MirroredRepeat)
        .export_values();

    nb::enum_<engine::MaterialType>(m, "MaterialType")
        .value("Standard", engine::MaterialType::Standard)
        .value("Physical", engine::MaterialType::Physical)
        .value("Unlit", engine::MaterialType::Unlit)
        .value("Lambert", engine::MaterialType::Lambert)
        .value("Phong", engine::MaterialType::Phong)
        .value("Toon", engine::MaterialType::Toon)
        .value("CustomShader", engine::MaterialType::CustomShader)
        .value("PBR", engine::MaterialType::PBR)
        .export_values();

    // -----------------------------------------------------------------------
    // Material Hierarchy
    // -----------------------------------------------------------------------
    nb::class_<engine::Material>(m, "Material")
        .def(nb::init<>())
        .def(nb::init<std::shared_ptr<engine::Texture>, float, float>(),
            "texture"_a = nullptr, "roughness"_a = 0.5f, "metallic"_a = 0.0f)
        .def_prop_ro("type", &engine::Material::type)
        .def_rw("transparent", &engine::Material::transparent)
        .def_rw("opacity", &engine::Material::opacity)
        .def_rw("depth_write", &engine::Material::depth_write)
        .def_rw("depth_test", &engine::Material::depth_test)
        .def_rw("wireframe", &engine::Material::wireframe)
        .def_rw("side", &engine::Material::side)
        .def_rw("blend_mode", &engine::Material::blend_mode)
        .def_prop_rw("albedo_map",
            [](engine::Material& m) { return m.albedo_map; },
            [](engine::Material& m, nb::handle obj) {
                if (obj.is_none()) { m.albedo_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { m.albedo_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { m.albedo_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
                else if (nb::hasattr(obj, "texture")) {
                    auto tex = obj.attr("texture");
                    if (nb::isinstance<engine::Texture>(tex)) m.albedo_map = nb::cast<std::shared_ptr<engine::Texture>>(tex);
                    else if (PyCallable_Check(tex.ptr())) {
                        auto res = tex();
                        if (nb::isinstance<engine::Texture>(res)) m.albedo_map = nb::cast<std::shared_ptr<engine::Texture>>(res);
                    }
                }
            })
        .def_prop_rw("normal_map",
            [](engine::Material& m) { return m.normal_map; },
            [](engine::Material& m, nb::handle obj) {
                if (obj.is_none()) { m.normal_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { m.normal_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { m.normal_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_prop_rw("metallic_roughness_map",
            [](engine::Material& m) { return m.metallic_roughness_map; },
            [](engine::Material& m, nb::handle obj) {
                if (obj.is_none()) { m.metallic_roughness_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { m.metallic_roughness_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { m.metallic_roughness_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_prop_rw("occlusion_map",
            [](engine::Material& m) { return m.occlusion_map; },
            [](engine::Material& m, nb::handle obj) {
                if (obj.is_none()) { m.occlusion_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { m.occlusion_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { m.occlusion_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_prop_rw("ao_map",
            [](engine::Material& m) { return m.ao_map; },
            [](engine::Material& m, nb::handle obj) {
                if (obj.is_none()) { m.ao_map = nullptr; m.occlusion_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { m.ao_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); m.occlusion_map = m.ao_map; }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { m.ao_map = nb::cast<engine::RenderTarget&>(obj).texture(); m.occlusion_map = m.ao_map; }
            })
        .def_prop_rw("emissive_map",
            [](engine::Material& m) { return m.emissive_map; },
            [](engine::Material& m, nb::handle obj) {
                if (obj.is_none()) { m.emissive_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { m.emissive_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { m.emissive_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_rw("normal_scale", &engine::Material::normal_scale)
        .def_rw("ao_intensity", &engine::Material::ao_intensity)
        .def_rw("alpha_test", &engine::Material::alpha_test)
        .def_rw("alpha_cutoff", &engine::Material::alpha_cutoff)
        .def_prop_rw("emissive_color",
            [](engine::Material& mat) -> glm::vec3& { return mat.emissive_color; },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    mat.emissive_color = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) mat.emissive_color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("emissive_intensity", &engine::Material::emissive_intensity)
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
        .def_prop_rw("uv_offset",
            [](engine::Material& mat) -> std::pair<float, float> {
                return { mat.uv_offset.x, mat.uv_offset.y };
            },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 2) mat.uv_offset = { seq[0], seq[1] };
                }
            })
        .def("set_color", &engine::Material::set_color, "r"_a, "g"_a, "b"_a, "a"_a = 1.0f)
        .def("set_uv_scale", &engine::Material::set_uv_scale, "u"_a, "v"_a)
        .def("set_uv_offset", &engine::Material::set_uv_offset, "u"_a, "v"_a);

    nb::class_<engine::StandardMaterial, engine::Material>(m, "StandardMaterial")
        .def(nb::init<>())
        .def(nb::init<std::shared_ptr<engine::Texture>, float, float>(),
            "texture"_a = nullptr, "roughness"_a = 0.5f, "metallic"_a = 0.0f);

    nb::class_<engine::PhysicalMaterial, engine::StandardMaterial>(m, "PhysicalMaterial")
        .def(nb::init<>())
        .def_rw("clearcoat", &engine::PhysicalMaterial::clearcoat)
        .def_rw("clearcoat_roughness", &engine::PhysicalMaterial::clearcoat_roughness)
        .def_rw("transmission", &engine::PhysicalMaterial::transmission)
        .def_rw("ior", &engine::PhysicalMaterial::ior)
        .def_prop_rw("sheen",
            [](engine::PhysicalMaterial& mat) -> glm::vec3& { return mat.sheen; },
            [](engine::PhysicalMaterial& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    mat.sheen = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) mat.sheen = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("sheen_roughness", &engine::PhysicalMaterial::sheen_roughness);

    nb::class_<engine::UnlitMaterial, engine::Material>(m, "UnlitMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>, bool>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr, "wireframe"_a = false);

    nb::class_<engine::LambertMaterial, engine::Material>(m, "LambertMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr);

    nb::class_<engine::PhongMaterial, engine::Material>(m, "PhongMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>, float>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr, "shininess"_a = 30.0f)
        .def_rw("shininess", &engine::PhongMaterial::shininess)
        .def_prop_rw("specular_color",
            [](engine::PhongMaterial& mat) -> glm::vec3& { return mat.specular_color; },
            [](engine::PhongMaterial& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    mat.specular_color = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) mat.specular_color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal);

    nb::class_<engine::ToonMaterial, engine::Material>(m, "ToonMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>, int>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr, "steps"_a = 3)
        .def_rw("steps", &engine::ToonMaterial::steps)
        .def_rw("num_steps", &engine::ToonMaterial::num_steps);

    nb::class_<engine::ShaderMaterial, engine::Material>(m, "ShaderMaterial")
        .def(nb::init<>())
        .def(nb::init<std::string, std::string>(), "vertex_shader"_a = "", "fragment_shader"_a = "")
        .def_rw("vertex_shader", &engine::ShaderMaterial::vertex_shader)
        .def_rw("fragment_shader", &engine::ShaderMaterial::fragment_shader)
        .def_rw("uniforms", &engine::ShaderMaterial::uniforms);

    // -----------------------------------------------------------------------
    // PipelineManager
    // -----------------------------------------------------------------------
    nb::class_<engine::PipelineManager>(m, "PipelineManager")
        .def_static("instance", &engine::PipelineManager::instance, nb::rv_policy::reference)
        .def("release_all", &engine::PipelineManager::release_all);

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
            [](engine::Entity& e, std::shared_ptr<engine::Mesh> m) { e.mesh = m; })
        .def_prop_rw("material",
            [](engine::Entity& e) { return e.material; },
            [](engine::Entity& e, std::shared_ptr<engine::Material> m) { e.material = m; })
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
        }, "obj"_a);

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
    // AudioManager
    // -----------------------------------------------------------------------
    nb::class_<engine::AudioManager>(m, "AudioManager")
        .def("play_footstep", &engine::AudioManager::play_footstep)
        .def("play_jump", &engine::AudioManager::play_jump)
        .def("play_hit_3d", [](engine::AudioManager& a, const nb::object& pos) {
            if (nb::isinstance<glm::vec3>(pos)) {
                a.play_hit_3d(nb::cast<glm::vec3>(pos));
            } else if (nb::isinstance<nb::tuple>(pos) || nb::isinstance<nb::list>(pos)) {
                auto seq = nb::cast<std::vector<float>>(pos);
                if (seq.size() >= 3) a.play_hit_3d({ seq[0], seq[1], seq[2] });
            }
        }, "world_pos"_a)
        .def("play_sound_file", &engine::AudioManager::play_sound_file, "filepath"_a, "volume"_a = 1.0f);

    // -----------------------------------------------------------------------
    // EditorManager
    // -----------------------------------------------------------------------
    nb::class_<engine::EditorManager>(m, "EditorManager")
        .def_rw("show_hierarchy", &engine::EditorManager::show_hierarchy)
        .def_rw("show_inspector", &engine::EditorManager::show_inspector)
        .def_rw("show_perf_overlay", &engine::EditorManager::show_perf_overlay)
        .def_prop_rw("gizmo_operation", &engine::EditorManager::gizmo_operation, &engine::EditorManager::set_gizmo_operation)
        .def("select_entity", &engine::EditorManager::select_entity, "entity"_a)
        .def("set_selected_entity", &engine::EditorManager::select_entity, "entity"_a)
        .def_prop_rw("selected_entity",
            &engine::EditorManager::selected_entity,
            &engine::EditorManager::select_entity)
        .def("enable_toggle_hotkey", &engine::EditorManager::enable_toggle_hotkey, "enable"_a, "key"_a = engine::Key::F2);

    // -----------------------------------------------------------------------
    // RenderTarget
    // -----------------------------------------------------------------------
    nb::enum_<engine::RenderTargetFormat>(m, "RenderTargetFormat")
        .value("RGBA8", engine::RenderTargetFormat::RGBA8)
        .value("RGBA16F", engine::RenderTargetFormat::RGBA16F)
        .value("R32F", engine::RenderTargetFormat::R32F)
        .export_values();

    nb::class_<engine::RenderTarget>(m, "RenderTarget")
        .def(nb::init<int, int, engine::RenderTargetFormat, bool, int>(),
             "width"_a, "height"_a, "format"_a = engine::RenderTargetFormat::RGBA8,
             "has_depth"_a = true, "samples"_a = 1)
        .def("resize", &engine::RenderTarget::resize, "width"_a, "height"_a)
        .def_prop_ro("width", &engine::RenderTarget::width)
        .def_prop_ro("height", &engine::RenderTarget::height)
        .def_prop_ro("format", &engine::RenderTarget::format)
        .def_prop_ro("has_depth", &engine::RenderTarget::has_depth)
        .def_prop_ro("samples", &engine::RenderTarget::samples)
        .def_prop_ro("color_image_id", &engine::RenderTarget::color_image_id)
        .def_prop_ro("color_view_id", &engine::RenderTarget::color_view_id)
        .def_prop_ro("depth_image_id", &engine::RenderTarget::depth_image_id)
        .def_prop_ro("depth_view_id", &engine::RenderTarget::depth_view_id)
        .def_prop_ro("depth_tex_view_id", &engine::RenderTarget::depth_tex_view_id)
        .def_prop_ro("tex_view_id", &engine::RenderTarget::tex_view_id)
        .def_prop_ro("sampler_id", &engine::RenderTarget::sampler_id)
        .def("is_valid", [](const engine::RenderTarget& rt) { return rt.color_view_id() != 0; })
        .def_prop_ro("texture", &engine::RenderTarget::texture)
        .def("read_pixels", [](engine::RenderTarget& rt) {
            auto pixels = rt.read_pixels();
            return nb::bytes(pixels.data(), pixels.size());
        });

    // -----------------------------------------------------------------------
    // Post-Processing & EffectComposer
    // -----------------------------------------------------------------------
    nb::enum_<engine::TonemappingMode>(m, "TonemappingMode")
        .value("ACESFilmic", engine::TonemappingMode::ACESFilmic)
        .value("Reinhard", engine::TonemappingMode::Reinhard)
        .value("Cineon", engine::TonemappingMode::Cineon)
        .value("Linear", engine::TonemappingMode::Linear)
        .value("Neutral", engine::TonemappingMode::Neutral)
        .export_values();

    nb::class_<engine::PostProcessPass>(m, "PostProcessPass")
        .def_rw("enabled", &engine::PostProcessPass::enabled)
        .def_prop_ro("name", &engine::PostProcessPass::name);

    nb::class_<engine::BloomPass, engine::PostProcessPass>(m, "BloomPass")
        .def(nb::init<float, float, float>(),
             "threshold"_a = 1.0f, "strength"_a = 1.5f, "radius"_a = 0.5f)
        .def_rw("threshold", &engine::BloomPass::threshold)
        .def_rw("strength", &engine::BloomPass::strength)
        .def_rw("radius", &engine::BloomPass::radius);

    nb::class_<engine::SSAOPass, engine::PostProcessPass>(m, "SSAOPass")
        .def(nb::init<float, float, float>(),
             "radius"_a = 0.5f, "bias"_a = 0.025f, "power"_a = 1.0f)
        .def_rw("radius", &engine::SSAOPass::radius)
        .def_rw("bias", &engine::SSAOPass::bias)
        .def_rw("power", &engine::SSAOPass::power);

    nb::class_<engine::FXAAPass, engine::PostProcessPass>(m, "FXAAPass")
        .def(nb::init<>());

    nb::class_<engine::TonemappingPass, engine::PostProcessPass>(m, "TonemappingPass")
        .def(nb::init<engine::TonemappingMode, float, float>(),
             "mode"_a = engine::TonemappingMode::ACESFilmic, "exposure"_a = 1.0f, "gamma"_a = 2.2f)
        .def_rw("mode", &engine::TonemappingPass::mode)
        .def_rw("exposure", &engine::TonemappingPass::exposure)
        .def_rw("gamma", &engine::TonemappingPass::gamma);

    nb::class_<engine::VignetteChromaticPass, engine::PostProcessPass>(m, "VignetteChromaticPass")
        .def(nb::init<float, float, float>(),
             "vignette"_a = 0.3f, "chromatic"_a = 0.005f, "grain"_a = 0.02f)
        .def_rw("vignette", &engine::VignetteChromaticPass::vignette)
        .def_rw("chromatic", &engine::VignetteChromaticPass::chromatic)
        .def_rw("grain", &engine::VignetteChromaticPass::grain)
        .def_rw("time", &engine::VignetteChromaticPass::time);

    nb::class_<engine::ColorGradingPass, engine::PostProcessPass>(m, "ColorGradingPass")
        .def(nb::init<float, float, float>(),
             "contrast"_a = 1.0f, "saturation"_a = 1.0f, "brightness"_a = 1.0f)
        .def_rw("contrast", &engine::ColorGradingPass::contrast)
        .def_rw("saturation", &engine::ColorGradingPass::saturation)
        .def_rw("brightness", &engine::ColorGradingPass::brightness);

    nb::class_<engine::EffectComposer>(m, "EffectComposer")
        .def(nb::init<>())
        .def(nb::init<int, int>(), "width"_a, "height"_a)
        .def(nb::init<engine::EngineApp&>(), "app"_a)
        .def("add_pass", &engine::EffectComposer::add_pass, "pass"_a)
        .def("remove_pass", &engine::EffectComposer::remove_pass, "pass"_a)
        .def("clear_passes", &engine::EffectComposer::clear_passes)
        .def("resize", &engine::EffectComposer::resize, "width"_a, "height"_a)
        .def_rw("enabled", &engine::EffectComposer::enabled)
        .def_prop_ro("passes", &engine::EffectComposer::passes)
        .def("render", &engine::EffectComposer::render, "scene"_a, "camera"_a)
        .def_prop_ro("hdr_target", &engine::EffectComposer::hdr_target, nb::rv_policy::reference_internal);

    // -----------------------------------------------------------------------
    // EngineApp
    // -----------------------------------------------------------------------
    nb::class_<engine::EngineApp>(m, "EngineApp")
        .def(nb::init<>())
        .def(nb::init<const std::string&, int, int>(),
             "title"_a, "width"_a, "height"_a)
        .def("init", &engine::EngineApp::init,
             "title"_a = "VelocityEngine v0.2-beta",
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
        .def_prop_ro("audio", &engine::EngineApp::audio, nb::rv_policy::reference_internal)
        .def_prop_ro("editor", &engine::EngineApp::editor, nb::rv_policy::reference_internal)

        // Mode
        .def_prop_rw("mode", &engine::EngineApp::get_mode, &engine::EngineApp::set_mode)
        .def("get_mode", &engine::EngineApp::get_mode)
        .def("set_mode", &engine::EngineApp::set_mode, "mode"_a)
        .def("toggle_mode", &engine::EngineApp::toggle_mode)

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
        .def_prop_ro("title", &engine::EngineApp::title)
        .def("set_title", &engine::EngineApp::set_title, "title"_a)

        // HUD and Debug options
        .def("set_show_hud", &engine::EngineApp::set_show_hud, "enable"_a)
        .def_prop_rw("show_hud", &engine::EngineApp::show_hud, &engine::EngineApp::set_show_hud)
        .def("set_show_crosshair", &engine::EngineApp::set_show_crosshair, "show"_a)
        .def_prop_rw("show_crosshair", &engine::EngineApp::show_crosshair, &engine::EngineApp::set_show_crosshair)
        .def("set_hud_score", &engine::EngineApp::set_hud_score, "score"_a)
        .def_prop_rw("hud_score", &engine::EngineApp::hud_score, &engine::EngineApp::set_hud_score)
        .def("set_hud_title", &engine::EngineApp::set_hud_title, "title"_a)
        .def_prop_rw("hud_title", &engine::EngineApp::hud_title, &engine::EngineApp::set_hud_title)
        .def("set_hud_hint", &engine::EngineApp::set_hud_hint, "hint"_a)
        .def_prop_rw("hud_hint", &engine::EngineApp::hud_hint, &engine::EngineApp::set_hud_hint)
        .def("set_debug_hitboxes", &engine::EngineApp::set_debug_hitboxes, "enable"_a)
        .def("toggle_debug_hitboxes", &engine::EngineApp::toggle_debug_hitboxes)
        .def_prop_rw("debug_hitboxes", &engine::EngineApp::is_debug_hitboxes, &engine::EngineApp::set_debug_hitboxes)
        .def("set_target_fps", &engine::EngineApp::set_target_fps, "fps"_a)
        .def_prop_rw("target_fps", &engine::EngineApp::target_fps, &engine::EngineApp::set_target_fps)
        .def("set_vsync", &engine::EngineApp::set_vsync, "enabled"_a)
        .def_prop_rw("vsync", &engine::EngineApp::vsync, &engine::EngineApp::set_vsync)
        .def_prop_ro("fps", &engine::EngineApp::fps)
        .def_prop_ro("frame_time_ms", &engine::EngineApp::frame_time_ms)

        // Fog & Tone Mapping
        .def("set_linear_fog", [](engine::EngineApp& app, const nb::object& color, float near_dist, float far_dist) {
            glm::vec3 c{0.8f, 0.8f, 0.85f};
            if (nb::isinstance<glm::vec3>(color)) c = nb::cast<glm::vec3>(color);
            else if (nb::isinstance<nb::tuple>(color) || nb::isinstance<nb::list>(color)) {
                auto s = nb::cast<std::vector<float>>(color);
                if (s.size() >= 3) c = { s[0], s[1], s[2] };
            }
            app.set_linear_fog(c, near_dist, far_dist);
        }, "color"_a, "near"_a = 1.0f, "far"_a = 100.0f)
        .def("set_exp2_fog", [](engine::EngineApp& app, const nb::object& color, float density) {
            glm::vec3 c{0.8f, 0.8f, 0.85f};
            if (nb::isinstance<glm::vec3>(color)) c = nb::cast<glm::vec3>(color);
            else if (nb::isinstance<nb::tuple>(color) || nb::isinstance<nb::list>(color)) {
                auto s = nb::cast<std::vector<float>>(color);
                if (s.size() >= 3) c = { s[0], s[1], s[2] };
            }
            app.set_exp2_fog(c, density);
        }, "color"_a, "density"_a = 0.02f)
        .def("clear_fog", &engine::EngineApp::clear_fog)
        .def_prop_ro("fog_enabled", &engine::EngineApp::fog_enabled)
        .def_prop_ro("fog_type", &engine::EngineApp::fog_type)
        .def_prop_ro("fog_color", &engine::EngineApp::fog_color)
        .def_prop_ro("fog_near", &engine::EngineApp::fog_near)
        .def_prop_ro("fog_far", &engine::EngineApp::fog_far)
        .def_prop_ro("fog_density", &engine::EngineApp::fog_density)
        .def("set_tone_mapping", &engine::EngineApp::set_tone_mapping, "enable"_a)
        .def_prop_rw("tone_mapping", &engine::EngineApp::tone_mapping_enabled, &engine::EngineApp::set_tone_mapping)
        .def("submit_ui_commands", [](engine::EngineApp& app, const nb::object& cmds_obj) {
            std::vector<engine::UICommand> cmds;
            if (nb::isinstance<nb::list>(cmds_obj) || nb::isinstance<nb::tuple>(cmds_obj)) {
                for (auto handle : cmds_obj) {
                    if (nb::isinstance<engine::UICommand>(handle)) {
                        cmds.push_back(nb::cast<engine::UICommand>(handle));
                    }
                }
            }
            app.submit_ui_commands(cmds);
        }, "cmds"_a)
        .def("clear_ui_commands", &engine::EngineApp::clear_ui_commands)
        .def_prop_ro("custom_ui_commands", &engine::EngineApp::custom_ui_commands)
        .def("evaluate_frustum_culling", &engine::EngineApp::evaluate_frustum_culling)
        .def("render_target", &engine::EngineApp::render_target, "scene"_a, "camera"_a, "target"_a)
        .def("read_pixels", [](engine::EngineApp& app, engine::RenderTarget& target) {
            auto pixels = app.read_pixels(target);
            return nb::bytes(pixels.data(), pixels.size());
        }, "target"_a)
        .def("set_composer", &engine::EngineApp::set_composer, "composer"_a)
        .def_prop_rw("composer", &engine::EngineApp::composer, &engine::EngineApp::set_composer)
        .def_prop_ro("stats", [](engine::EngineApp& app) -> const engine::RenderStats& {
            return app.stats();
        }, nb::rv_policy::reference_internal);
}

