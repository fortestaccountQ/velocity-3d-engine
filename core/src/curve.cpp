#include "engine/curve.hpp"
#include "engine/mesh.hpp"

#include <cmath>
#include <algorithm>
#include <limits>

namespace engine {

namespace {
const float PI = 3.14159265358979323846f;

// Helper: Rodrigues' rotation formula
glm::vec3 rotate_vector(const glm::vec3& v, const glm::vec3& axis, float angle) {
    return v * std::cos(angle) + glm::cross(axis, v) * std::sin(angle) + axis * glm::dot(axis, v) * (1.0f - std::cos(angle));
}

// 2D polygon area
float polygon_area(const std::vector<glm::vec2>& poly) {
    float area = 0.0f;
    size_t n = poly.size();
    for (size_t i = 0; i < n; ++i) {
        size_t j = (i + 1) % n;
        area += poly[i].x * poly[j].y - poly[j].x * poly[i].y;
    }
    return area * 0.5f;
}

// Check if point P is inside triangle ABC
bool point_in_triangle(const glm::vec2& p, const glm::vec2& a, const glm::vec2& b, const glm::vec2& c) {
    auto sign = [](const glm::vec2& p1, const glm::vec2& p2, const glm::vec2& p3) {
        return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y);
    };
    float d1 = sign(p, a, b);
    float d2 = sign(p, b, c);
    float d3 = sign(p, c, a);
    bool has_neg = (d1 < 0.0f) || (d2 < 0.0f) || (d3 < 0.0f);
    bool has_pos = (d1 > 0.0f) || (d2 > 0.0f) || (d3 > 0.0f);
    return !(has_neg && has_pos);
}

// Ear clipping polygon triangulation
std::vector<uint16_t> triangulate_polygon(const std::vector<glm::vec2>& poly) {
    std::vector<uint16_t> indices;
    size_t n = poly.size();
    if (n < 3) return indices;

    std::vector<uint16_t> V(n);
    if (polygon_area(poly) > 0.0f) {
        for (size_t i = 0; i < n; ++i) V[i] = static_cast<uint16_t>(i);
    } else {
        for (size_t i = 0; i < n; ++i) V[i] = static_cast<uint16_t>(n - 1 - i);
    }

    size_t count = n;
    int safety = 2 * static_cast<int>(n);
    while (count > 2 && safety-- > 0) {
        bool ear_found = false;
        for (size_t i = 0; i < count; ++i) {
            size_t prev = (i == 0) ? count - 1 : i - 1;
            size_t next = (i + 1 == count) ? 0 : i + 1;

            glm::vec2 a = poly[V[prev]];
            glm::vec2 b = poly[V[i]];
            glm::vec2 c = poly[V[next]];

            // Check if reflex
            float cross = (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x);
            if (cross <= 0.0f) continue;

            // Check if any other vertex is inside triangle
            bool has_point = false;
            for (size_t p = 0; p < count; ++p) {
                if (p == prev || p == i || p == next) continue;
                if (point_in_triangle(poly[V[p]], a, b, c)) {
                    has_point = true;
                    break;
                }
            }

            if (!has_point) {
                indices.push_back(V[prev]);
                indices.push_back(V[i]);
                indices.push_back(V[next]);
                V.erase(V.begin() + i);
                count--;
                ear_found = true;
                break;
            }
        }
        if (!ear_found) break;
    }
    return indices;
}
} // namespace

FrenetFrames Curve3::compute_frenet_frames(int segments, bool closed) const {
    FrenetFrames frames;
    if (segments < 1) segments = 1;

    frames.tangents.resize(segments + 1);
    frames.normals.resize(segments + 1);
    frames.binormals.resize(segments + 1);

    for (int i = 0; i <= segments; ++i) {
        float t = static_cast<float>(i) / static_cast<float>(segments);
        frames.tangents[i] = get_tangent(t);
    }

    // Initial normal
    glm::vec3 t0 = frames.tangents[0];
    glm::vec3 up(0.0f, 1.0f, 0.0f);
    if (std::abs(t0.y) > 0.9f) {
        up = glm::vec3(0.0f, 0.0f, 1.0f);
    }
    frames.binormals[0] = glm::normalize(glm::cross(t0, up));
    frames.normals[0] = glm::normalize(glm::cross(frames.binormals[0], t0));

    // Parallel transport
    for (int i = 1; i <= segments; ++i) {
        glm::vec3 prev_t = frames.tangents[i - 1];
        glm::vec3 cur_t = frames.tangents[i];
        glm::vec3 v = glm::cross(prev_t, cur_t);
        float v_len = glm::length(v);

        if (v_len > 1e-5f) {
            glm::vec3 axis = v / v_len;
            float angle = std::acos(std::clamp(glm::dot(prev_t, cur_t), -1.0f, 1.0f));
            frames.normals[i] = glm::normalize(rotate_vector(frames.normals[i - 1], axis, angle));
        } else {
            frames.normals[i] = frames.normals[i - 1];
        }

        frames.binormals[i] = glm::normalize(glm::cross(cur_t, frames.normals[i]));
        frames.normals[i] = glm::normalize(glm::cross(frames.binormals[i], cur_t));
    }

    if (closed && segments > 1) {
        float theta = std::acos(std::clamp(glm::dot(frames.normals[0], frames.normals[segments]), -1.0f, 1.0f));
        if (glm::dot(frames.tangents[0], glm::cross(frames.normals[0], frames.normals[segments])) < 0.0f) {
            theta = -theta;
        }
        for (int i = 1; i <= segments; ++i) {
            float frac = static_cast<float>(i) / static_cast<float>(segments);
            frames.normals[i] = rotate_vector(frames.normals[i], frames.tangents[i], -theta * frac);
            frames.binormals[i] = glm::normalize(glm::cross(frames.tangents[i], frames.normals[i]));
        }
    }

    return frames;
}

// ---------------------------------------------------------------------------
// CatmullRomCurve3
// ---------------------------------------------------------------------------
glm::vec3 CatmullRomCurve3::get_point(float t) const {
    if (points.empty()) return glm::vec3(0.0f);
    if (points.size() == 1) return points[0];
    if (points.size() == 2) return glm::mix(points[0], points[1], t);

    t = std::clamp(t, 0.0f, 1.0f);

    size_t num_points = points.size();
    if (closed) {
        float u = t * static_cast<float>(num_points);
        int i = static_cast<int>(std::floor(u));
        float f = u - static_cast<float>(i);

        int p0_idx = (i - 1 + static_cast<int>(num_points)) % static_cast<int>(num_points);
        int p1_idx = i % static_cast<int>(num_points);
        int p2_idx = (i + 1) % static_cast<int>(num_points);
        int p3_idx = (i + 2) % static_cast<int>(num_points);

        const glm::vec3& p0 = points[p0_idx];
        const glm::vec3& p1 = points[p1_idx];
        const glm::vec3& p2 = points[p2_idx];
        const glm::vec3& p3 = points[p3_idx];

        float f2 = f * f;
        float f3 = f2 * f;

        return 0.5f * (
            (2.0f * p1) +
            (-p0 + p2) * f +
            (2.0f * p0 - 5.0f * p1 + 4.0f * p2 - p3) * f2 +
            (-p0 + 3.0f * p1 - 3.0f * p2 + p3) * f3
        );
    } else {
        int num_segments = static_cast<int>(num_points) - 1;
        float u = t * static_cast<float>(num_segments);
        int i = std::clamp(static_cast<int>(std::floor(u)), 0, num_segments - 1);
        float f = u - static_cast<float>(i);

        glm::vec3 p1 = points[i];
        glm::vec3 p2 = points[i + 1];
        glm::vec3 p0 = (i == 0) ? (p1 + (p1 - p2)) : points[i - 1];
        glm::vec3 p3 = (i + 2 < static_cast<int>(num_points)) ? points[i + 2] : (p2 + (p2 - p1));

        float f2 = f * f;
        float f3 = f2 * f;

        return 0.5f * (
            (2.0f * p1) +
            (-p0 + p2) * f +
            (2.0f * p0 - 5.0f * p1 + 4.0f * p2 - p3) * f2 +
            (-p0 + 3.0f * p1 - 3.0f * p2 + p3) * f3
        );
    }
}

// ---------------------------------------------------------------------------
// CubicBezierCurve3
// ---------------------------------------------------------------------------
glm::vec3 CubicBezierCurve3::get_point(float t) const {
    t = std::clamp(t, 0.0f, 1.0f);
    float u = 1.0f - t;
    return (u * u * u) * v0 + (3.0f * u * u * t) * v1 + (3.0f * u * t * t) * v2 + (t * t * t) * v3;
}

glm::vec3 CubicBezierCurve3::get_tangent(float t) const {
    t = std::clamp(t, 0.0f, 1.0f);
    float u = 1.0f - t;
    glm::vec3 d = 3.0f * u * u * (v1 - v0) + 6.0f * u * t * (v2 - v1) + 3.0f * t * t * (v3 - v2);
    float len = glm::length(d);
    return (len > 1e-6f) ? (d / len) : glm::vec3(0.0f, 1.0f, 0.0f);
}

// ---------------------------------------------------------------------------
// QuadraticBezierCurve3
// ---------------------------------------------------------------------------
glm::vec3 QuadraticBezierCurve3::get_point(float t) const {
    t = std::clamp(t, 0.0f, 1.0f);
    float u = 1.0f - t;
    return (u * u) * v0 + (2.0f * u * t) * v1 + (t * t) * v2;
}

glm::vec3 QuadraticBezierCurve3::get_tangent(float t) const {
    t = std::clamp(t, 0.0f, 1.0f);
    float u = 1.0f - t;
    glm::vec3 d = 2.0f * u * (v1 - v0) + 2.0f * t * (v2 - v1);
    float len = glm::length(d);
    return (len > 1e-6f) ? (d / len) : glm::vec3(0.0f, 1.0f, 0.0f);
}

// ---------------------------------------------------------------------------
// LineCurve3
// ---------------------------------------------------------------------------
glm::vec3 LineCurve3::get_point(float t) const {
    t = std::clamp(t, 0.0f, 1.0f);
    return glm::mix(v1, v2, t);
}

glm::vec3 LineCurve3::get_tangent(float /*t*/) const {
    glm::vec3 d = v2 - v1;
    float len = glm::length(d);
    return (len > 1e-6f) ? (d / len) : glm::vec3(0.0f, 1.0f, 0.0f);
}

// ---------------------------------------------------------------------------
// Procedural Geometry Generators
// ---------------------------------------------------------------------------
std::shared_ptr<Mesh> create_tube(const Curve3& curve, int tubular_segments, float radius, int radial_segments, bool closed) {
    auto mesh = std::make_shared<Mesh>();
    if (tubular_segments < 2) tubular_segments = 2;
    if (radial_segments < 3) radial_segments = 3;

    FrenetFrames frames = curve.compute_frenet_frames(tubular_segments, closed);
    mesh->cpu_vertices.reserve((tubular_segments + 1) * (radial_segments + 1));

    for (int i = 0; i <= tubular_segments; ++i) {
        float t = static_cast<float>(i) / static_cast<float>(tubular_segments);
        glm::vec3 P = curve.get_point(t);
        glm::vec3 N = frames.normals[i];
        glm::vec3 B = frames.binormals[i];
        glm::vec3 T = frames.tangents[i];

        for (int j = 0; j <= radial_segments; ++j) {
            float v = static_cast<float>(j) / static_cast<float>(radial_segments) * 2.0f * PI;
            float cos_v = std::cos(v);
            float sin_v = std::sin(v);

            glm::vec3 normal = glm::normalize(cos_v * N + sin_v * B);
            glm::vec3 pos = P + radius * normal;
            glm::vec2 uv(t, static_cast<float>(j) / static_cast<float>(radial_segments));
            glm::vec4 tan(T, 1.0f);

            mesh->cpu_vertices.push_back({ pos, normal, uv, glm::vec4(1.0f), tan });
        }
    }

    for (int i = 0; i < tubular_segments; ++i) {
        for (int j = 0; j < radial_segments; ++j) {
            uint16_t a = static_cast<uint16_t>(i * (radial_segments + 1) + j);
            uint16_t b = static_cast<uint16_t>((i + 1) * (radial_segments + 1) + j);
            uint16_t c = static_cast<uint16_t>((i + 1) * (radial_segments + 1) + (j + 1));
            uint16_t d = static_cast<uint16_t>(i * (radial_segments + 1) + (j + 1));

            mesh->cpu_indices.push_back(a);
            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(d);

            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(c);
            mesh->cpu_indices.push_back(d);
        }
    }

    if (!closed) {
        // Start cap
        uint16_t start_center = static_cast<uint16_t>(mesh->cpu_vertices.size());
        glm::vec3 start_p = curve.get_point(0.0f);
        glm::vec3 start_n = -frames.tangents[0];
        glm::vec3 start_up = (std::abs(start_n.y) > 0.9f) ? glm::vec3(0, 0, 1) : glm::vec3(0, 1, 0);
        glm::vec4 start_tan(glm::normalize(glm::cross(start_up, start_n)), 1.0f);
        mesh->cpu_vertices.push_back({ start_p, start_n, { 0.5f, 0.5f }, glm::vec4(1.0f), start_tan });

        for (int j = 0; j <= radial_segments; ++j) {
            float v = static_cast<float>(j) / static_cast<float>(radial_segments) * 2.0f * PI;
            glm::vec3 normal = glm::normalize(std::cos(v) * frames.normals[0] + std::sin(v) * frames.binormals[0]);
            glm::vec3 pos = start_p + radius * normal;
            mesh->cpu_vertices.push_back({ pos, start_n, { 0.5f + 0.5f * std::cos(v), 0.5f + 0.5f * std::sin(v) }, glm::vec4(1.0f), start_tan });
        }
        for (int j = 0; j < radial_segments; ++j) {
            mesh->cpu_indices.push_back(start_center);
            mesh->cpu_indices.push_back(static_cast<uint16_t>(start_center + 1 + j + 1));
            mesh->cpu_indices.push_back(static_cast<uint16_t>(start_center + 1 + j));
        }

        // End cap
        uint16_t end_center = static_cast<uint16_t>(mesh->cpu_vertices.size());
        glm::vec3 end_p = curve.get_point(1.0f);
        glm::vec3 end_n = frames.tangents[tubular_segments];
        glm::vec3 end_up = (std::abs(end_n.y) > 0.9f) ? glm::vec3(0, 0, 1) : glm::vec3(0, 1, 0);
        glm::vec4 end_tan(glm::normalize(glm::cross(end_up, end_n)), 1.0f);
        mesh->cpu_vertices.push_back({ end_p, end_n, { 0.5f, 0.5f }, glm::vec4(1.0f), end_tan });

        for (int j = 0; j <= radial_segments; ++j) {
            float v = static_cast<float>(j) / static_cast<float>(radial_segments) * 2.0f * PI;
            glm::vec3 normal = glm::normalize(std::cos(v) * frames.normals[tubular_segments] + std::sin(v) * frames.binormals[tubular_segments]);
            glm::vec3 pos = end_p + radius * normal;
            mesh->cpu_vertices.push_back({ pos, end_n, { 0.5f + 0.5f * std::cos(v), 0.5f + 0.5f * std::sin(v) }, glm::vec4(1.0f), end_tan });
        }
        for (int j = 0; j < radial_segments; ++j) {
            mesh->cpu_indices.push_back(end_center);
            mesh->cpu_indices.push_back(static_cast<uint16_t>(end_center + 1 + j));
            mesh->cpu_indices.push_back(static_cast<uint16_t>(end_center + 1 + j + 1));
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> create_lathe(const std::vector<glm::vec2>& points, int segments, float phi_start, float phi_length) {
    auto mesh = std::make_shared<Mesh>();
    if (points.size() < 2 || segments < 3) return mesh;

    size_t num_pts = points.size();
    mesh->cpu_vertices.reserve((segments + 1) * num_pts);

    for (int s = 0; s <= segments; ++s) {
        float u = static_cast<float>(s) / static_cast<float>(segments);
        float phi = phi_start + u * phi_length;
        float cos_phi = std::cos(phi);
        float sin_phi = std::sin(phi);

        for (size_t p = 0; p < num_pts; ++p) {
            float r = points[p].x;
            float y = points[p].y;
            glm::vec3 pos(r * sin_phi, y, r * cos_phi);

            glm::vec2 d(0.0f);
            if (p == 0) {
                d = points[1] - points[0];
            } else if (p == num_pts - 1) {
                d = points[p] - points[p - 1];
            } else {
                d = points[p + 1] - points[p - 1];
            }
            float d_len = glm::length(d);
            glm::vec2 profile_norm = (d_len > 1e-6f) ? glm::normalize(glm::vec2(d.y, -d.x)) : glm::vec2(1.0f, 0.0f);
            glm::vec3 normal(profile_norm.x * sin_phi, profile_norm.y, profile_norm.x * cos_phi);
            glm::vec4 tan(cos_phi, 0.0f, -sin_phi, 1.0f);
            float v = static_cast<float>(p) / static_cast<float>(num_pts - 1);

            mesh->cpu_vertices.push_back({ pos, normal, { u, v }, glm::vec4(1.0f), tan });
        }
    }

    for (int s = 0; s < segments; ++s) {
        for (size_t p = 0; p < num_pts - 1; ++p) {
            uint16_t a = static_cast<uint16_t>(s * num_pts + p);
            uint16_t b = static_cast<uint16_t>((s + 1) * num_pts + p);
            uint16_t c = static_cast<uint16_t>((s + 1) * num_pts + (p + 1));
            uint16_t d = static_cast<uint16_t>(s * num_pts + (p + 1));

            mesh->cpu_indices.push_back(a);
            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(d);

            mesh->cpu_indices.push_back(b);
            mesh->cpu_indices.push_back(c);
            mesh->cpu_indices.push_back(d);
        }
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

std::shared_ptr<Mesh> create_extrude(const std::vector<glm::vec2>& polygon, float depth, float /*bevel_thickness*/) {
    auto mesh = std::make_shared<Mesh>();
    size_t n = polygon.size();
    if (n < 3) return mesh;

    float half_d = depth * 0.5f;
    std::vector<uint16_t> poly_tris = triangulate_polygon(polygon);

    // 1. Front face (+Z)
    uint16_t front_base = static_cast<uint16_t>(mesh->cpu_vertices.size());
    for (size_t i = 0; i < n; ++i) {
        mesh->cpu_vertices.push_back({
            { polygon[i].x, polygon[i].y, half_d },
            { 0.0f, 0.0f, 1.0f },
            { polygon[i].x, polygon[i].y },
            glm::vec4(1.0f),
            { 1.0f, 0.0f, 0.0f, 1.0f }
        });
    }
    for (size_t i = 0; i < poly_tris.size(); i += 3) {
        mesh->cpu_indices.push_back(static_cast<uint16_t>(front_base + poly_tris[i]));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(front_base + poly_tris[i + 1]));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(front_base + poly_tris[i + 2]));
    }

    // 2. Back face (-Z)
    uint16_t back_base = static_cast<uint16_t>(mesh->cpu_vertices.size());
    for (size_t i = 0; i < n; ++i) {
        mesh->cpu_vertices.push_back({
            { polygon[i].x, polygon[i].y, -half_d },
            { 0.0f, 0.0f, -1.0f },
            { polygon[i].x, polygon[i].y },
            glm::vec4(1.0f),
            { -1.0f, 0.0f, 0.0f, 1.0f }
        });
    }
    for (size_t i = 0; i < poly_tris.size(); i += 3) {
        mesh->cpu_indices.push_back(static_cast<uint16_t>(back_base + poly_tris[i]));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(back_base + poly_tris[i + 2]));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(back_base + poly_tris[i + 1]));
    }

    // 3. Side walls
    for (size_t i = 0; i < n; ++i) {
        size_t next = (i + 1) % n;
        glm::vec2 p0 = polygon[i];
        glm::vec2 p1 = polygon[next];
        glm::vec2 edge = p1 - p0;
        float edge_len = glm::length(edge);
        glm::vec2 edge_dir = (edge_len > 1e-6f) ? (edge / edge_len) : glm::vec2(1.0f, 0.0f);

        glm::vec3 norm(edge_dir.y, -edge_dir.x, 0.0f);
        glm::vec4 tan(edge_dir.x, edge_dir.y, 0.0f, 1.0f);

        uint16_t wall_base = static_cast<uint16_t>(mesh->cpu_vertices.size());
        mesh->cpu_vertices.push_back({ { p0.x, p0.y,  half_d }, norm, { 0.0f, 1.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ { p1.x, p1.y,  half_d }, norm, { 1.0f, 1.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ { p1.x, p1.y, -half_d }, norm, { 1.0f, 0.0f }, glm::vec4(1.0f), tan });
        mesh->cpu_vertices.push_back({ { p0.x, p0.y, -half_d }, norm, { 0.0f, 0.0f }, glm::vec4(1.0f), tan });

        mesh->cpu_indices.push_back(wall_base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(wall_base + 1));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(wall_base + 2));

        mesh->cpu_indices.push_back(wall_base);
        mesh->cpu_indices.push_back(static_cast<uint16_t>(wall_base + 2));
        mesh->cpu_indices.push_back(static_cast<uint16_t>(wall_base + 3));
    }

    mesh->num_indices = static_cast<int>(mesh->cpu_indices.size());
    mesh->calculate_aabb();
    mesh->ensure_gpu_buffers();
    return mesh;
}

} // namespace engine
