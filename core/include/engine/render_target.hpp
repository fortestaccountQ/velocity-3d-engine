#pragma once

#include <cstdint>
#include <memory>
#include <vector>
#include <string>
#include <glm/glm.hpp>
#include "engine/texture.hpp"

namespace engine {

enum class RenderTargetFormat {
    RGBA8 = 0,
    RGBA16F = 1,
    R32F = 2
};

class RenderTarget {
public:
    RenderTarget(int width, int height, RenderTargetFormat format = RenderTargetFormat::RGBA8, bool has_depth = true, int samples = 1);
    ~RenderTarget();

    RenderTarget(const RenderTarget&) = delete;
    RenderTarget& operator=(const RenderTarget&) = delete;
    RenderTarget(RenderTarget&& other) noexcept;
    RenderTarget& operator=(RenderTarget&& other) noexcept;

    int width() const { return width_; }
    int height() const { return height_; }
    RenderTargetFormat format() const { return format_; }
    bool has_depth() const { return has_depth_; }
    int samples() const { return samples_; }

    uint32_t color_image_id() const { ensure_lazy_resources(); return color_image_id_; }
    uint32_t color_view_id() const { ensure_lazy_resources(); return color_view_id_; }
    uint32_t depth_image_id() const { ensure_lazy_resources(); return depth_image_id_; }
    uint32_t depth_view_id() const { ensure_lazy_resources(); return depth_view_id_; }
    uint32_t depth_tex_view_id() const { ensure_lazy_resources(); return depth_tex_view_id_; }
    uint32_t tex_view_id() const { ensure_lazy_resources(); return tex_view_id_; }
    uint32_t sampler_id() const { ensure_lazy_resources(); return sampler_id_; }
    bool is_valid() const { ensure_lazy_resources(); return color_view_id_ != 0; }

    std::shared_ptr<Texture> texture() const { return texture_; }
    std::vector<uint8_t> read_pixels();
    std::vector<float> read_depth_pixels();

    void resize(int new_width, int new_height);
    void destroy();
    void create_resources();

private:
    void ensure_lazy_resources() const;

    int width_{0};
    int height_{0};
    RenderTargetFormat format_{RenderTargetFormat::RGBA8};
    bool has_depth_{true};
    int samples_{1};

    uint32_t color_image_id_{0};
    uint32_t color_view_id_{0};
    uint32_t tex_view_id_{0};
    uint32_t sampler_id_{0};

    uint32_t depth_image_id_{0};
    uint32_t depth_view_id_{0};
    uint32_t depth_tex_view_id_{0};
    mutable bool is_destroyed_{false};

    std::shared_ptr<Texture> texture_{nullptr};
};

} // namespace engine
