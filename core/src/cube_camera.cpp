#include "engine/cube_camera.hpp"
#include "engine/app.hpp"
#include "engine/scene.hpp"
#include "sokol_gfx.h"

#include <iostream>

namespace engine {

CubeRenderTarget::CubeRenderTarget(int resolution) : resolution_(resolution) {
    create_resources();
}

CubeRenderTarget::~CubeRenderTarget() {
    destroy();
}

void CubeRenderTarget::destroy() {
    for (int f = 0; f < 6; ++f) {
        if (face_view_ids_[f] != 0) {
            if (sg_isvalid()) sg_destroy_view(sg_view{ face_view_ids_[f] });
            face_view_ids_[f] = 0;
        }
    }
    if (depth_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ depth_view_id_ });
        depth_view_id_ = 0;
    }
    if (depth_img_id_ != 0) {
        if (sg_isvalid()) sg_destroy_image(sg_image{ depth_img_id_ });
        depth_img_id_ = 0;
    }
    if (tex_view_id_ != 0) {
        if (sg_isvalid()) sg_destroy_view(sg_view{ tex_view_id_ });
        tex_view_id_ = 0;
    }
    if (sampler_id_ != 0) {
        if (sg_isvalid()) sg_destroy_sampler(sg_sampler{ sampler_id_ });
        sampler_id_ = 0;
    }
    if (color_img_id_ != 0) {
        if (sg_isvalid()) sg_destroy_image(sg_image{ color_img_id_ });
        color_img_id_ = 0;
    }
    if (cube_texture_) {
        // Clear handles inside cube_texture so it doesn't double-free
        cube_texture_->image_id = 0;
        cube_texture_->view_id = 0;
        cube_texture_->sampler_id = 0;
        cube_texture_ = nullptr;
    }
}

void CubeRenderTarget::create_resources() {
    if (!cube_texture_) {
        cube_texture_ = std::make_shared<CubeTexture>();
    }
    cube_texture_->size = (resolution_ > 0) ? resolution_ : 0;

    if (!sg_isvalid() || resolution_ <= 0) return;

    // 1. Color cubemap image
    sg_image_desc col_desc{};
    col_desc.type = SG_IMAGETYPE_CUBE;
    col_desc.usage.color_attachment = true;
    col_desc.width = resolution_;
    col_desc.height = resolution_;
    col_desc.num_slices = 6;
    col_desc.pixel_format = SG_PIXELFORMAT_RGBA8;
    col_desc.label = "cuberendertarget-color-image";
    sg_image col_img = sg_make_image(&col_desc);
    color_img_id_ = col_img.id;

    // 2. 6 color attachment views for each face
    for (int f = 0; f < 6; ++f) {
        sg_view_desc rtv_desc{};
        rtv_desc.color_attachment.image = col_img;
        rtv_desc.color_attachment.slice = f;
        rtv_desc.color_attachment.mip_level = 0;
        rtv_desc.label = "cuberendertarget-face-rtv";
        sg_view rtv = sg_make_view(&rtv_desc);
        face_view_ids_[f] = rtv.id;
    }

    // 3. Shared 2D depth attachment image
    sg_image_desc depth_desc{};
    depth_desc.usage.depth_stencil_attachment = true;
    depth_desc.width = resolution_;
    depth_desc.height = resolution_;
    depth_desc.pixel_format = SG_PIXELFORMAT_DEPTH;
    depth_desc.label = "cuberendertarget-depth-image";
    sg_image depth_img = sg_make_image(&depth_desc);
    depth_img_id_ = depth_img.id;

    sg_view_desc depth_view_desc{};
    depth_view_desc.depth_stencil_attachment.image = depth_img;
    depth_view_desc.label = "cuberendertarget-depth-view";
    sg_view depth_view = sg_make_view(&depth_view_desc);
    depth_view_id_ = depth_view.id;

    // 4. View for shader cubemap sampling
    sg_view_desc srv_desc{};
    srv_desc.texture.image = col_img;
    srv_desc.label = "cuberendertarget-texture-srv";
    sg_view srv = sg_make_view(&srv_desc);
    tex_view_id_ = srv.id;

    sg_sampler_desc smp_desc{};
    smp_desc.min_filter = SG_FILTER_LINEAR;
    smp_desc.mag_filter = SG_FILTER_LINEAR;
    smp_desc.wrap_u = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.wrap_v = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.wrap_w = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.label = "cuberendertarget-sampler";
    sg_sampler smp = sg_make_sampler(&smp_desc);
    sampler_id_ = smp.id;

    cube_texture_->image_id = col_img.id;
    cube_texture_->view_id = srv.id;
    cube_texture_->sampler_id = smp.id;
    cube_texture_->size = resolution_;
    cube_texture_->num_mipmaps = 1;
}

CubeCamera::CubeCamera(float near_p, float far_p, int resolution)
    : Node3D("CubeCamera"), near_(near_p), far_(far_p), resolution_(resolution) {
    render_target_ = std::make_shared<CubeRenderTarget>(resolution_);
}

void CubeCamera::update(EngineApp& app, Scene& scene) {
    app.render_cube_camera(scene, *this);
}

} // namespace engine
