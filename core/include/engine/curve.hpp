#pragma once

#include <glm/glm.hpp>
#include <vector>
#include <memory>
#include <cmath>
#include <algorithm>

namespace engine {

class Mesh;

struct FrenetFrames {
    std::vector<glm::vec3> tangents;
    std::vector<glm::vec3> normals;
    std::vector<glm::vec3> binormals;
};

class Curve3 {
public:
    virtual ~Curve3() = default;

    virtual glm::vec3 get_point(float t) const = 0;

    virtual glm::vec3 get_tangent(float t) const {
        const float delta = 0.0001f;
        float t1 = std::max(0.0f, t - delta);
        float t2 = std::min(1.0f, t + delta);
        glm::vec3 pt1 = get_point(t1);
        glm::vec3 pt2 = get_point(t2);
        glm::vec3 d = pt2 - pt1;
        float len = glm::length(d);
        return (len > 1e-6f) ? (d / len) : glm::vec3(0.0f, 1.0f, 0.0f);
    }

    std::vector<glm::vec3> get_points(int divisions = 50) const {
        if (divisions < 1) divisions = 1;
        std::vector<glm::vec3> points;
        points.reserve(divisions + 1);
        for (int i = 0; i <= divisions; ++i) {
            float t = static_cast<float>(i) / static_cast<float>(divisions);
            points.push_back(get_point(t));
        }
        return points;
    }

    FrenetFrames compute_frenet_frames(int segments, bool closed = false) const;
};

class CatmullRomCurve3 : public Curve3 {
public:
    std::vector<glm::vec3> points;
    bool closed{false};
    float tension{0.5f};

    CatmullRomCurve3() = default;
    CatmullRomCurve3(const std::vector<glm::vec3>& pts, bool is_closed = false, float t = 0.5f)
        : points(pts), closed(is_closed), tension(t) {}

    glm::vec3 get_point(float t) const override;
};

class CubicBezierCurve3 : public Curve3 {
public:
    glm::vec3 v0{0.0f};
    glm::vec3 v1{0.0f};
    glm::vec3 v2{0.0f};
    glm::vec3 v3{0.0f};

    CubicBezierCurve3() = default;
    CubicBezierCurve3(const glm::vec3& p0, const glm::vec3& p1, const glm::vec3& p2, const glm::vec3& p3)
        : v0(p0), v1(p1), v2(p2), v3(p3) {}

    glm::vec3 get_point(float t) const override;
    glm::vec3 get_tangent(float t) const override;
};

class QuadraticBezierCurve3 : public Curve3 {
public:
    glm::vec3 v0{0.0f};
    glm::vec3 v1{0.0f};
    glm::vec3 v2{0.0f};

    QuadraticBezierCurve3() = default;
    QuadraticBezierCurve3(const glm::vec3& p0, const glm::vec3& p1, const glm::vec3& p2)
        : v0(p0), v1(p1), v2(p2) {}

    glm::vec3 get_point(float t) const override;
    glm::vec3 get_tangent(float t) const override;
};

class LineCurve3 : public Curve3 {
public:
    glm::vec3 v1{0.0f};
    glm::vec3 v2{0.0f};

    LineCurve3() = default;
    LineCurve3(const glm::vec3& p1, const glm::vec3& p2)
        : v1(p1), v2(p2) {}

    glm::vec3 get_point(float t) const override;
    glm::vec3 get_tangent(float t) const override;
};

// Procedural Geometry Generators
std::shared_ptr<Mesh> create_tube(const Curve3& curve, int tubular_segments = 64, float radius = 0.2f, int radial_segments = 8, bool closed = false);
std::shared_ptr<Mesh> create_lathe(const std::vector<glm::vec2>& points, int segments = 32, float phi_start = 0.0f, float phi_length = 6.283185307179586f);
std::shared_ptr<Mesh> create_extrude(const std::vector<glm::vec2>& polygon, float depth = 1.0f, float bevel_thickness = 0.0f);

} // namespace engine
