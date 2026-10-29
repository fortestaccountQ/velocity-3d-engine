#pragma once

#include "engine/node3d.hpp"
#include "engine/light.hpp"
#include "engine/camera.hpp"
#include "engine/mesh.hpp"
#include <glm/glm.hpp>
#include <vector>
#include <memory>
#include <string>

namespace engine {

struct LineVertex {
    glm::vec3 pos;
    glm::vec4 color;
};

class Helper : public Node3D {
public:
    Helper(const std::string& helper_name = "Helper") : Node3D(helper_name) {
        cast_shadows = false;
        receive_shadows = false;
    }
    ~Helper() override = default;

    virtual void get_line_vertices(std::vector<LineVertex>& out_verts) const = 0;
    virtual void update() {}
};

class GridHelper : public Helper {
public:
    float size{10.0f};
    int divisions{10};
    glm::vec4 color_center{0.8f, 0.8f, 0.8f, 1.0f};
    glm::vec4 color_grid{0.3f, 0.3f, 0.3f, 1.0f};

    GridHelper(float grid_size = 10.0f, int grid_divisions = 10,
               const glm::vec4& col_center = {0.8f, 0.8f, 0.8f, 1.0f},
               const glm::vec4& col_grid = {0.3f, 0.3f, 0.3f, 1.0f});

    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

class AxesHelper : public Helper {
public:
    float size{1.0f};

    explicit AxesHelper(float axes_size = 1.0f);

    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

class BoxHelper : public Helper {
public:
    std::shared_ptr<Node3D> target{nullptr};
    glm::vec4 color{1.0f, 1.0f, 0.0f, 1.0f};

    BoxHelper(std::shared_ptr<Node3D> target_node = nullptr, const glm::vec4& box_color = {1.0f, 1.0f, 0.0f, 1.0f});

    void set_from_object(std::shared_ptr<Node3D> obj);
    void update() override;
    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;

private:
    mutable AABB cached_aabb_{};
};

class ArrowHelper : public Helper {
public:
    glm::vec3 dir{0.0f, 1.0f, 0.0f};
    glm::vec3 origin{0.0f, 0.0f, 0.0f};
    float length{1.0f};
    glm::vec4 color{1.0f, 1.0f, 0.0f, 1.0f};
    float head_length{0.2f};
    float head_width{0.1f};

    ArrowHelper(const glm::vec3& direction = {0.0f, 1.0f, 0.0f},
                const glm::vec3& origin_pos = {0.0f, 0.0f, 0.0f},
                float arrow_length = 1.0f,
                const glm::vec4& arrow_color = {1.0f, 1.0f, 0.0f, 1.0f},
                float arrow_head_length = 0.2f,
                float arrow_head_width = 0.1f);

    void set_direction(const glm::vec3& direction);
    void set_length(float total_length, float arrow_head_length = -1.0f, float arrow_head_width = -1.0f);
    void set_color(const glm::vec4& arrow_color);

    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

class DirectionalLightHelper : public Helper {
public:
    std::shared_ptr<DirectionalLight> light{nullptr};
    float size{1.0f};
    glm::vec4 color{1.0f, 1.0f, 0.0f, 1.0f};

    DirectionalLightHelper(std::shared_ptr<DirectionalLight> dir_light = nullptr,
                           float helper_size = 1.0f,
                           const glm::vec4& helper_color = {1.0f, 1.0f, 0.0f, 1.0f});

    void update() override;
    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

class SpotLightHelper : public Helper {
public:
    std::shared_ptr<SpotLight> light{nullptr};
    glm::vec4 color{1.0f, 1.0f, 0.0f, 1.0f};

    SpotLightHelper(std::shared_ptr<SpotLight> spot_light = nullptr,
                    const glm::vec4& helper_color = {1.0f, 1.0f, 0.0f, 1.0f});

    void update() override;
    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

class PointLightHelper : public Helper {
public:
    std::shared_ptr<PointLight> light{nullptr};
    float sphere_size{0.5f};
    glm::vec4 color{1.0f, 1.0f, 0.0f, 1.0f};

    PointLightHelper(std::shared_ptr<PointLight> point_light = nullptr,
                     float size = 0.5f,
                     const glm::vec4& helper_color = {1.0f, 1.0f, 0.0f, 1.0f});

    void update() override;
    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

class CameraHelper : public Helper {
public:
    std::shared_ptr<Camera> camera{nullptr};
    glm::vec4 color{1.0f, 1.0f, 0.0f, 1.0f};

    CameraHelper(std::shared_ptr<Camera> cam = nullptr,
                 const glm::vec4& helper_color = {1.0f, 1.0f, 0.0f, 1.0f});

    void update() override;
    void get_line_vertices(std::vector<LineVertex>& out_verts) const override;
};

} // namespace engine
