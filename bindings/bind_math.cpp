#include "bind_common.hpp"
#include "engine/math_types.hpp"
#include "engine/physics.hpp"
#include "engine/transform.hpp"

void bind_math(nb::module_& m) {
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
}
