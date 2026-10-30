#include "engine/render_target.hpp"
#include "engine/app.hpp"

#include "sokol_gfx.h"

#include <iostream>
#include <cstring>
#include <algorithm>

#if defined(SOKOL_D3D11)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <d3d11.h>
#endif

namespace engine {

RenderTarget::RenderTarget(int width, int height, RenderTargetFormat format, bool has_depth, int samples)
    : width_(width), height_(height), format_(format), has_depth_(has_depth), samples_(samples) {
    create_resources();
}

RenderTarget::~RenderTarget() {
    destroy();
}

RenderTarget::RenderTarget(RenderTarget&& other) noexcept
    : width_(other.width_),
      height_(other.height_),
      format_(other.format_),
      has_depth_(other.has_depth_),
      samples_(other.samples_),
      color_image_id_(other.color_image_id_),
      color_view_id_(other.color_view_id_),
      tex_view_id_(other.tex_view_id_),
      sampler_id_(other.sampler_id_),
      depth_image_id_(other.depth_image_id_),
      depth_view_id_(other.depth_view_id_),
      depth_tex_view_id_(other.depth_tex_view_id_),
      texture_(std::move(other.texture_)) {
    other.width_ = 0;
    other.height_ = 0;
    other.color_image_id_ = 0;
    other.color_view_id_ = 0;
    other.tex_view_id_ = 0;
    other.sampler_id_ = 0;
    other.depth_image_id_ = 0;
    other.depth_view_id_ = 0;
    other.depth_tex_view_id_ = 0;
}

RenderTarget& RenderTarget::operator=(RenderTarget&& other) noexcept {
    if (this != &other) {
        destroy();

        width_ = other.width_;
        height_ = other.height_;
        format_ = other.format_;
        has_depth_ = other.has_depth_;
        samples_ = other.samples_;
        color_image_id_ = other.color_image_id_;
        color_view_id_ = other.color_view_id_;
        tex_view_id_ = other.tex_view_id_;
        sampler_id_ = other.sampler_id_;
        depth_image_id_ = other.depth_image_id_;
        depth_view_id_ = other.depth_view_id_;
        depth_tex_view_id_ = other.depth_tex_view_id_;
        texture_ = std::move(other.texture_);

        other.width_ = 0;
        other.height_ = 0;
        other.color_image_id_ = 0;
        other.color_view_id_ = 0;
        other.tex_view_id_ = 0;
        other.sampler_id_ = 0;
        other.depth_image_id_ = 0;
        other.depth_view_id_ = 0;
        other.depth_tex_view_id_ = 0;
    }
    return *this;
}

void RenderTarget::create_resources() {
    if (!texture_) {
        texture_ = std::make_shared<Texture>();
    }
    texture_->width = (width_ > 0) ? width_ : 0;
    texture_->height = (height_ > 0) ? height_ : 0;
    texture_->channels = (format_ == RenderTargetFormat::R32F) ? 1 : 4;

    if (!sg_isvalid()) {
        EngineApp::ensure_headless_device();
    }

    if (!sg_isvalid() || width_ <= 0 || height_ <= 0 || color_image_id_ != 0) {
        return;
    }

    sg_pixel_format sg_fmt = SG_PIXELFORMAT_RGBA8;
    if (format_ == RenderTargetFormat::RGBA16F) {
        sg_fmt = SG_PIXELFORMAT_RGBA16F;
    } else if (format_ == RenderTargetFormat::R32F) {
        sg_fmt = SG_PIXELFORMAT_R32F;
    }

    // 1. Color attachment image
    sg_image_desc col_desc{};
    col_desc.usage.color_attachment = true;
    col_desc.width = width_;
    col_desc.height = height_;
    col_desc.pixel_format = sg_fmt;
    col_desc.sample_count = samples_;
    col_desc.label = "rendertarget-color-image";
    sg_image col_img = sg_make_image(&col_desc);
    color_image_id_ = col_img.id;

    // 2. View for render-pass color attachment
    sg_view_desc col_view_desc{};
    col_view_desc.color_attachment.image = col_img;
    col_view_desc.label = "rendertarget-color-view";
    sg_view col_view = sg_make_view(&col_view_desc);
    color_view_id_ = col_view.id;

    // 3. View for shader sampling (as a texture)
    sg_view_desc tex_view_desc{};
    tex_view_desc.texture.image = col_img;
    tex_view_desc.label = "rendertarget-texture-view";
    sg_view tex_view = sg_make_view(&tex_view_desc);
    tex_view_id_ = tex_view.id;

    // 4. Default Sampler for shader reading
    sg_sampler_desc smp_desc{};
    smp_desc.min_filter = SG_FILTER_LINEAR;
    smp_desc.mag_filter = SG_FILTER_LINEAR;
    smp_desc.wrap_u = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.wrap_v = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.label = "rendertarget-sampler";
    sg_sampler smp = sg_make_sampler(&smp_desc);
    sampler_id_ = smp.id;

    // 5. Optional Depth Attachment
    if (has_depth_) {
        sg_image_desc depth_desc{};
        depth_desc.usage.depth_stencil_attachment = true;
        depth_desc.width = width_;
        depth_desc.height = height_;
        depth_desc.pixel_format = SG_PIXELFORMAT_DEPTH;
        depth_desc.sample_count = samples_;
        depth_desc.label = "rendertarget-depth-image";
        sg_image depth_img = sg_make_image(&depth_desc);
        depth_image_id_ = depth_img.id;

        sg_view_desc depth_view_desc{};
        depth_view_desc.depth_stencil_attachment.image = depth_img;
        depth_view_desc.label = "rendertarget-depth-view";
        sg_view depth_view = sg_make_view(&depth_view_desc);
        depth_view_id_ = depth_view.id;

        sg_view_desc depth_tex_view_desc{};
        depth_tex_view_desc.texture.image = depth_img;
        depth_tex_view_desc.label = "rendertarget-depth-sample-view";
        sg_view depth_tex_view = sg_make_view(&depth_tex_view_desc);
        depth_tex_view_id_ = depth_tex_view.id;
    }

    // 6. Wrap in engine::Texture for materials/portals/mirrors
    if (!texture_) {
        texture_ = std::make_shared<Texture>();
    }
    texture_->image_id = color_image_id_;
    texture_->view_id = tex_view_id_;
    texture_->sampler_id = sampler_id_;
    texture_->width = width_;
    texture_->height = height_;
    texture_->channels = (format_ == RenderTargetFormat::R32F) ? 1 : 4;
}

void RenderTarget::destroy() {
    if (texture_) {
        // Clear IDs so Texture destructor doesn't attempt to double-destroy
        texture_->image_id = 0;
        texture_->view_id = 0;
        texture_->sampler_id = 0;
    }

    if (tex_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ tex_view_id_ });
        tex_view_id_ = 0;
    }
    if (color_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ color_view_id_ });
        color_view_id_ = 0;
    }
    if (sampler_id_ != 0) {
        if (sg_isvalid()) sg_destroy_sampler(sg_sampler{ sampler_id_ });
        sampler_id_ = 0;
    }
    if (color_image_id_ != 0) {
        if (sg_isvalid()) sg_destroy_image(sg_image{ color_image_id_ });
        color_image_id_ = 0;
    }

    if (depth_tex_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ depth_tex_view_id_ });
        depth_tex_view_id_ = 0;
    }
    if (depth_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ depth_view_id_ });
        depth_view_id_ = 0;
    }
    if (depth_image_id_ != 0) {
        if (sg_isvalid()) sg_destroy_image(sg_image{ depth_image_id_ });
        depth_image_id_ = 0;
    }
}

void RenderTarget::resize(int new_width, int new_height) {
    if (new_width <= 0 || new_height <= 0) return;
    if (new_width == width_ && new_height == height_) return;

    destroy();
    width_ = new_width;
    height_ = new_height;
    create_resources();
}

std::vector<uint8_t> RenderTarget::read_pixels() {
    std::vector<uint8_t> pixels;
    if (width_ <= 0 || height_ <= 0 || color_image_id_ == 0) {
        return pixels;
    }

    size_t bpp = (format_ == RenderTargetFormat::RGBA16F) ? 8 : 4;
    size_t total_size = static_cast<size_t>(width_ * height_ * bpp);
    pixels.resize(total_size, 0);

#if defined(SOKOL_D3D11)
    ID3D11Device* dev = (ID3D11Device*)sg_d3d11_device();
    ID3D11DeviceContext* ctx = (ID3D11DeviceContext*)sg_d3d11_device_context();
    sg_d3d11_image_info info = sg_d3d11_query_image_info(sg_image{ color_image_id_ });
    ID3D11Texture2D* src_tex = (ID3D11Texture2D*)info.tex2d;

    if (dev && ctx && src_tex) {
        D3D11_TEXTURE2D_DESC desc;
        src_tex->GetDesc(&desc);
        desc.Usage = D3D11_USAGE_STAGING;
        desc.BindFlags = 0;
        desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
        desc.MiscFlags = 0;

        ID3D11Texture2D* staging_tex = nullptr;
        HRESULT hr = dev->CreateTexture2D(&desc, nullptr, &staging_tex);
        if (SUCCEEDED(hr) && staging_tex) {
            ctx->CopyResource(staging_tex, src_tex);
            D3D11_MAPPED_SUBRESOURCE mapped{};
            hr = ctx->Map(staging_tex, 0, D3D11_MAP_READ, 0, &mapped);
            if (SUCCEEDED(hr)) {
                const uint8_t* src_ptr = static_cast<const uint8_t*>(mapped.pData);
                uint8_t* dst_ptr = pixels.data();
                size_t row_bytes = static_cast<size_t>(width_ * bpp);
                for (int y = 0; y < height_; ++y) {
                    std::memcpy(dst_ptr + y * row_bytes, src_ptr + y * mapped.RowPitch, row_bytes);
                }
                ctx->Unmap(staging_tex, 0);
            }
            staging_tex->Release();
        }
    }
#endif

    return pixels;
}

std::vector<float> RenderTarget::read_depth_pixels() {
    std::vector<float> depths;
    if (width_ <= 0 || height_ <= 0 || depth_image_id_ == 0) {
        return depths;
    }

    depths.resize(static_cast<size_t>(width_ * height_), 1.0f);

#if defined(SOKOL_D3D11)
    ID3D11Device* dev = (ID3D11Device*)sg_d3d11_device();
    ID3D11DeviceContext* ctx = (ID3D11DeviceContext*)sg_d3d11_device_context();
    sg_d3d11_image_info info = sg_d3d11_query_image_info(sg_image{ depth_image_id_ });
    ID3D11Texture2D* src_tex = (ID3D11Texture2D*)info.tex2d;

    if (dev && ctx && src_tex) {
        D3D11_TEXTURE2D_DESC desc;
        src_tex->GetDesc(&desc);
        desc.Usage = D3D11_USAGE_STAGING;
        desc.BindFlags = 0;
        desc.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
        desc.MiscFlags = 0;
        desc.Format = DXGI_FORMAT_R32_TYPELESS;

        ID3D11Texture2D* staging_tex = nullptr;
        HRESULT hr = dev->CreateTexture2D(&desc, nullptr, &staging_tex);
        if (SUCCEEDED(hr) && staging_tex) {
            ctx->CopyResource(staging_tex, src_tex);
            D3D11_MAPPED_SUBRESOURCE mapped{};
            hr = ctx->Map(staging_tex, 0, D3D11_MAP_READ, 0, &mapped);
            if (SUCCEEDED(hr)) {
                const uint8_t* src_ptr = static_cast<const uint8_t*>(mapped.pData);
                float* dst_ptr = depths.data();
                size_t row_bytes = static_cast<size_t>(width_ * sizeof(float));
                for (int y = 0; y < height_; ++y) {
                    std::memcpy(dst_ptr + y * width_, src_ptr + y * mapped.RowPitch, row_bytes);
                }
                ctx->Unmap(staging_tex, 0);
            }
            staging_tex->Release();
        }
    }
#endif

    return depths;
}

} // namespace engine
