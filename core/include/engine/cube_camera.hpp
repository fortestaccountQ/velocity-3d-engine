#pragma once

#include "engine/node3d.hpp"
#include "engine/cube_texture.hpp"
#include <array>
#include <memory>
#include <cstdint>
#include <glm/glm.hpp>

namespace engine {

class EngineApp;
class Scene;

class CubeRenderTarget {
public:
    CubeRenderTarget(int resolution = 256);
    ~CubeRenderTarget();

    void destroy();
    int resolution() const { return resolution_; }

    uint32_t face_view_id(int face) const {
        return (face >= 0 && face < 6) ? face_view_ids_[face] : 0;
    }
    uint32_t depth_view_id() const { return depth_view_id_; }
    uint32_t color_img_id() const { return color_img_id_; }
    uint32_t tex_view_id() const { return tex_view_id_; }
    uint32_t sampler_id() const { return sampler_id_; }

    std::shared_ptr<CubeTexture> cube_texture() const { return cube_texture_; }

private:
    void create_resources();

    int resolution_{256};
    uint32_t color_img_id_{0};
    uint32_t depth_img_id_{0};
    uint32_t depth_view_id_{0};
    std::array<uint32_t, 6> face_view_ids_{{0, 0, 0, 0, 0, 0}};
    uint32_t tex_view_id_{0};
    uint32_t sampler_id_{0};
    std::shared_ptr<CubeTexture> cube_texture_{nullptr};
};

class CubeCamera : public Node3D {
public:
    CubeCamera(float near_p = 0.1f, float far_p = 100.0f, int resolution = 256);

    float near_plane() const { return near_; }
    void set_near_plane(float n) { near_ = n; }

    float far_plane() const { return far_; }
    void set_far_plane(float f) { far_ = f; }

    int resolution() const { return resolution_; }

    std::shared_ptr<CubeRenderTarget> render_target() const { return render_target_; }
    std::shared_ptr<CubeTexture> cube_texture() const {
        return render_target_ ? render_target_->cube_texture() : nullptr;
    }

    void update(EngineApp& app, Scene& scene);

private:
    float near_{0.1f};
    float far_{100.0f};
    int resolution_{256};
    std::shared_ptr<CubeRenderTarget> render_target_{nullptr};
};

} // namespace engine
