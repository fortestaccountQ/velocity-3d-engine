#include "engine/helpers.hpp"
#include <cmath>
#include <algorithm>

namespace engine {

namespace {
const float PI = 3.14159265358979323846f;
}

// ---------------------------------------------------------------------------
// GridHelper
// ---------------------------------------------------------------------------
GridHelper::GridHelper(float grid_size, int grid_divisions, const glm::vec4& col_center, const glm::vec4& col_grid)
    : Helper("GridHelper"), size(grid_size), divisions(grid_divisions),
      color_center(col_center), color_grid(col_grid) {}

void GridHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (divisions < 1 || size <= 0.0f) return;

    float half = size * 0.5f;
    float step = size / static_cast<float>(divisions);

    out_verts.reserve(out_verts.size() + (divisions + 1) * 4);

    for (int i = 0; i <= divisions; ++i) {
        float k = -half + static_cast<float>(i) * step;
        bool is_center = (i * 2 == divisions);
        const glm::vec4& col = is_center ? color_center : color_grid;

        // Line parallel to Z axis (varying X = k)
        out_verts.push_back({ { k, 0.0f, -half }, col });
        out_verts.push_back({ { k, 0.0f,  half }, col });

        // Line parallel to X axis (varying Z = k)
        out_verts.push_back({ { -half, 0.0f, k }, col });
        out_verts.push_back({ {  half, 0.0f, k }, col });
    }
}

// ---------------------------------------------------------------------------
// AxesHelper
// ---------------------------------------------------------------------------
AxesHelper::AxesHelper(float axes_size)
    : Helper("AxesHelper"), size(axes_size) {}

void AxesHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (size <= 0.0f) return;

    // X axis (Red)
    out_verts.push_back({ { 0.0f, 0.0f, 0.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } });
    out_verts.push_back({ { size, 0.0f, 0.0f }, { 1.0f, 0.0f, 0.0f, 1.0f } });

    // Y axis (Green)
    out_verts.push_back({ { 0.0f, 0.0f, 0.0f }, { 0.0f, 1.0f, 0.0f, 1.0f } });
    out_verts.push_back({ { 0.0f, size, 0.0f }, { 0.0f, 1.0f, 0.0f, 1.0f } });

    // Z axis (Blue)
    out_verts.push_back({ { 0.0f, 0.0f, 0.0f }, { 0.0f, 0.0f, 1.0f, 1.0f } });
    out_verts.push_back({ { 0.0f, 0.0f, size }, { 0.0f, 0.0f, 1.0f, 1.0f } });
}

// ---------------------------------------------------------------------------
// BoxHelper
// ---------------------------------------------------------------------------
BoxHelper::BoxHelper(std::shared_ptr<Node3D> target_node, const glm::vec4& box_color)
    : Helper("BoxHelper"), target(target_node), color(box_color) {
    update();
}

void BoxHelper::set_from_object(std::shared_ptr<Node3D> obj) {
    target = obj;
    update();
}

void BoxHelper::update() {
    if (target) {
        cached_aabb_ = target->world_aabb();
    }
}

void BoxHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (target) {
        cached_aabb_ = target->world_aabb();
    }
    if (!cached_aabb_.is_valid()) return;

    glm::vec3 mn = cached_aabb_.min_point;
    glm::vec3 mx = cached_aabb_.max_point;

    glm::vec3 c[8] = {
        { mn.x, mn.y, mn.z },
        { mx.x, mn.y, mn.z },
        { mx.x, mn.y, mx.z },
        { mn.x, mn.y, mx.z },
        { mn.x, mx.y, mn.z },
        { mx.x, mx.y, mn.z },
        { mx.x, mx.y, mx.z },
        { mn.x, mx.y, mx.z }
    };

    static const int edges[12][2] = {
        {0,1}, {1,2}, {2,3}, {3,0},
        {4,5}, {5,6}, {6,7}, {7,4},
        {0,4}, {1,5}, {2,6}, {3,7}
    };

    out_verts.reserve(out_verts.size() + 24);
    for (int i = 0; i < 12; ++i) {
        out_verts.push_back({ c[edges[i][0]], color });
        out_verts.push_back({ c[edges[i][1]], color });
    }
}

// ---------------------------------------------------------------------------
// ArrowHelper
// ---------------------------------------------------------------------------
ArrowHelper::ArrowHelper(const glm::vec3& direction, const glm::vec3& origin_pos,
                         float arrow_length, const glm::vec4& arrow_color,
                         float arrow_head_length, float arrow_head_width)
    : Helper("ArrowHelper"), origin(origin_pos), length(arrow_length),
      color(arrow_color), head_length(arrow_head_length), head_width(arrow_head_width) {
    set_direction(direction);
}

void ArrowHelper::set_direction(const glm::vec3& direction) {
    float len = glm::length(direction);
    dir = (len > 1e-6f) ? (direction / len) : glm::vec3(0.0f, 1.0f, 0.0f);
}

void ArrowHelper::set_length(float total_length, float arrow_head_length, float arrow_head_width) {
    length = total_length;
    if (arrow_head_length >= 0.0f) head_length = arrow_head_length;
    if (arrow_head_width >= 0.0f) head_width = arrow_head_width;
}

void ArrowHelper::set_color(const glm::vec4& arrow_color) {
    color = arrow_color;
}

void ArrowHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    glm::vec3 shaft_end = origin + dir * std::max(0.0f, length - head_length);
    glm::vec3 tip = origin + dir * length;

    // Shaft line
    out_verts.push_back({ origin, color });
    out_verts.push_back({ shaft_end, color });

    // Build head lines
    glm::vec3 up = (std::abs(dir.y) > 0.9f) ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
    glm::vec3 side = glm::normalize(glm::cross(dir, up)) * head_width;
    glm::vec3 side2 = glm::normalize(glm::cross(dir, side)) * head_width;

    glm::vec3 h0 = shaft_end + side;
    glm::vec3 h1 = shaft_end - side;
    glm::vec3 h2 = shaft_end + side2;
    glm::vec3 h3 = shaft_end - side2;

    // Head base cross
    out_verts.push_back({ h0, color });
    out_verts.push_back({ h1, color });
    out_verts.push_back({ h2, color });
    out_verts.push_back({ h3, color });

    // Lines from base to tip
    out_verts.push_back({ h0, color });
    out_verts.push_back({ tip, color });
    out_verts.push_back({ h1, color });
    out_verts.push_back({ tip, color });
    out_verts.push_back({ h2, color });
    out_verts.push_back({ tip, color });
    out_verts.push_back({ h3, color });
    out_verts.push_back({ tip, color });
}

// ---------------------------------------------------------------------------
// DirectionalLightHelper
// ---------------------------------------------------------------------------
DirectionalLightHelper::DirectionalLightHelper(std::shared_ptr<DirectionalLight> dir_light, float helper_size, const glm::vec4& helper_color)
    : Helper("DirectionalLightHelper"), light(dir_light), size(helper_size), color(helper_color) {
    update();
}

void DirectionalLightHelper::update() {
    if (light) {
        transform.position = light->get_world_position();
    }
}

void DirectionalLightHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (!light) return;

    glm::vec3 pos = light->get_world_position();
    glm::vec3 d = glm::normalize(light->get_world_direction());
    float s = size * 0.5f;

    glm::vec3 up = (std::abs(d.y) > 0.9f) ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
    glm::vec3 right = glm::normalize(glm::cross(d, up)) * s;
    glm::vec3 top = glm::normalize(glm::cross(right, d)) * s;

    // Plane square at pos
    glm::vec3 p0 = pos - right - top;
    glm::vec3 p1 = pos + right - top;
    glm::vec3 p2 = pos + right + top;
    glm::vec3 p3 = pos - right + top;

    out_verts.push_back({ p0, color }); out_verts.push_back({ p1, color });
    out_verts.push_back({ p1, color }); out_verts.push_back({ p2, color });
    out_verts.push_back({ p2, color }); out_verts.push_back({ p3, color });
    out_verts.push_back({ p3, color }); out_verts.push_back({ p0, color });

    // Direction ray
    out_verts.push_back({ pos, color });
    out_verts.push_back({ pos + d * size * 2.0f, color });
}

// ---------------------------------------------------------------------------
// SpotLightHelper
// ---------------------------------------------------------------------------
SpotLightHelper::SpotLightHelper(std::shared_ptr<SpotLight> spot_light, const glm::vec4& helper_color)
    : Helper("SpotLightHelper"), light(spot_light), color(helper_color) {
    update();
}

void SpotLightHelper::update() {
    if (light) {
        transform.position = light->get_world_position();
    }
}

void SpotLightHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (!light) return;

    glm::vec3 pos = light->get_world_position();
    glm::vec3 d = glm::normalize(light->get_world_direction());
    float range = (light->range > 0.0f) ? light->range : 10.0f;
    float cone_r = range * std::tan(light->outer_cone_angle);

    glm::vec3 up = (std::abs(d.y) > 0.9f) ? glm::vec3(0.0f, 0.0f, 1.0f) : glm::vec3(0.0f, 1.0f, 0.0f);
    glm::vec3 right = glm::normalize(glm::cross(d, up));
    glm::vec3 top = glm::normalize(glm::cross(right, d));

    glm::vec3 cone_center = pos + d * range;

    // Cone base ring (16 segments)
    const int segs = 16;
    for (int i = 0; i < segs; ++i) {
        float a0 = (static_cast<float>(i) / segs) * 2.0f * PI;
        float a1 = (static_cast<float>(i + 1) / segs) * 2.0f * PI;

        glm::vec3 pt0 = cone_center + (right * std::cos(a0) + top * std::sin(a0)) * cone_r;
        glm::vec3 pt1 = cone_center + (right * std::cos(a1) + top * std::sin(a1)) * cone_r;

        out_verts.push_back({ pt0, color });
        out_verts.push_back({ pt1, color });

        // Connect 4 main points to apex
        if (i % 4 == 0) {
            out_verts.push_back({ pos, color });
            out_verts.push_back({ pt0, color });
        }
    }
}

// ---------------------------------------------------------------------------
// PointLightHelper
// ---------------------------------------------------------------------------
PointLightHelper::PointLightHelper(std::shared_ptr<PointLight> point_light, float size, const glm::vec4& helper_color)
    : Helper("PointLightHelper"), light(point_light), sphere_size(size), color(helper_color) {
    update();
}

void PointLightHelper::update() {
    if (light) {
        transform.position = light->get_world_position();
    }
}

void PointLightHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (!light) return;

    glm::vec3 pos = light->get_world_position();
    float r = sphere_size;
    const int segs = 16;

    for (int i = 0; i < segs; ++i) {
        float a0 = (static_cast<float>(i) / segs) * 2.0f * PI;
        float a1 = (static_cast<float>(i + 1) / segs) * 2.0f * PI;
        float c0 = std::cos(a0) * r, s0 = std::sin(a0) * r;
        float c1 = std::cos(a1) * r, s1 = std::sin(a1) * r;

        // XZ circle
        out_verts.push_back({ pos + glm::vec3(c0, 0.0f, s0), color });
        out_verts.push_back({ pos + glm::vec3(c1, 0.0f, s1), color });

        // XY circle
        out_verts.push_back({ pos + glm::vec3(c0, s0, 0.0f), color });
        out_verts.push_back({ pos + glm::vec3(c1, s1, 0.0f), color });

        // YZ circle
        out_verts.push_back({ pos + glm::vec3(0.0f, c0, s0), color });
        out_verts.push_back({ pos + glm::vec3(0.0f, c1, s1), color });
    }
}

// ---------------------------------------------------------------------------
// CameraHelper
// ---------------------------------------------------------------------------
CameraHelper::CameraHelper(std::shared_ptr<Camera> cam, const glm::vec4& helper_color)
    : Helper("CameraHelper"), camera(cam), color(helper_color) {
    update();
}

void CameraHelper::update() {
    if (camera) {
        transform.position = camera->position;
    }
}

void CameraHelper::get_line_vertices(std::vector<LineVertex>& out_verts) const {
    if (!camera) return;

    glm::mat4 inv_vp = glm::inverse(camera->view_projection_matrix());

    // 8 NDC Frustum Corners in [-1, 1]
    glm::vec4 ndc[8] = {
        { -1.0f, -1.0f, 0.0f, 1.0f }, // Near
        {  1.0f, -1.0f, 0.0f, 1.0f },
        {  1.0f,  1.0f, 0.0f, 1.0f },
        { -1.0f,  1.0f, 0.0f, 1.0f },
        { -1.0f, -1.0f, 1.0f, 1.0f }, // Far
        {  1.0f, -1.0f, 1.0f, 1.0f },
        {  1.0f,  1.0f, 1.0f, 1.0f },
        { -1.0f,  1.0f, 1.0f, 1.0f }
    };

    glm::vec3 world_corners[8];
    for (int i = 0; i < 8; ++i) {
        glm::vec4 w = inv_vp * ndc[i];
        if (std::abs(w.w) > 1e-6f) {
            world_corners[i] = glm::vec3(w) / w.w;
        } else {
            world_corners[i] = glm::vec3(w);
        }
    }

    static const int edges[12][2] = {
        {0,1}, {1,2}, {2,3}, {3,0}, // Near plane
        {4,5}, {5,6}, {6,7}, {7,4}, // Far plane
        {0,4}, {1,5}, {2,6}, {3,7}  // Edges connecting near to far
    };

    out_verts.reserve(out_verts.size() + 24);
    for (int i = 0; i < 12; ++i) {
        out_verts.push_back({ world_corners[edges[i][0]], color });
        out_verts.push_back({ world_corners[edges[i][1]], color });
    }
}

} // namespace engine
