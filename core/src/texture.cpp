#include "engine/texture.hpp"

#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"

#include "sokol_gfx.h"
#include <vector>
#include <iostream>

namespace engine {

Texture::~Texture() {
    destroy();
}

void Texture::destroy() {
    if (view_id != 0) {
        sg_destroy_view(sg_view{view_id});
        view_id = 0;
    }
    if (sampler_id != 0) {
        sg_destroy_sampler(sg_sampler{sampler_id});
        sampler_id = 0;
    }
    if (image_id != 0) {
        sg_destroy_image(sg_image{image_id});
        image_id = 0;
    }
}

std::shared_ptr<Texture> Texture::create_from_rgba(int width, int height, const uint8_t* pixels) {
    if (!pixels || width <= 0 || height <= 0) {
        return nullptr;
    }

    auto tex = std::make_shared<Texture>();
    tex->width = width;
    tex->height = height;
    tex->channels = 4;

    // 1. Create GPU Image
    sg_image_desc img_desc{};
    img_desc.width = width;
    img_desc.height = height;
    img_desc.pixel_format = SG_PIXELFORMAT_RGBA8;
    img_desc.data.mip_levels[0] = { pixels, static_cast<size_t>(width * height * 4) };
    img_desc.label = "texture-rgba-image";
    sg_image img = sg_make_image(&img_desc);
    tex->image_id = img.id;

    // 2. Create GPU Sampler (linear filtering + repeat)
    sg_sampler_desc smp_desc{};
    smp_desc.min_filter = SG_FILTER_LINEAR;
    smp_desc.mag_filter = SG_FILTER_LINEAR;
    smp_desc.wrap_u = SG_WRAP_REPEAT;
    smp_desc.wrap_v = SG_WRAP_REPEAT;
    smp_desc.label = "texture-rgba-sampler";
    sg_sampler smp = sg_make_sampler(&smp_desc);
    tex->sampler_id = smp.id;

    // 3. Create GPU Texture View
    sg_view_desc view_desc{};
    view_desc.texture.image = img;
    view_desc.label = "texture-rgba-view";
    sg_view view = sg_make_view(&view_desc);
    tex->view_id = view.id;

    return tex;
}

std::shared_ptr<Texture> Texture::load_from_file(const std::string& filepath) {
    int w = 0, h = 0, comp = 0;
    stbi_set_flip_vertically_on_load(false);
    uint8_t* data = stbi_load(filepath.c_str(), &w, &h, &comp, 4);

    if (!data) {
        std::cerr << "[Engine::Texture] Warning: Failed to load image '" << filepath
                  << "'. Falling back to procedural checkerboard texture.\n";
        return create_checkerboard();
    }

    auto tex = create_from_rgba(w, h, data);
    stbi_image_free(data);
    return tex;
}

std::shared_ptr<Texture> Texture::create_checkerboard(
    int width,
    int height,
    int tile_size,
    uint32_t color1,
    uint32_t color2
) {
    std::vector<uint32_t> pixels(static_cast<size_t>(width * height));
    for (int y = 0; y < height; ++y) {
        for (int x = 0; x < width; ++x) {
            bool is_tile1 = ((x / tile_size) + (y / tile_size)) % 2 == 0;
            pixels[static_cast<size_t>(y * width + x)] = is_tile1 ? color1 : color2;
        }
    }

    return create_from_rgba(width, height, reinterpret_cast<const uint8_t*>(pixels.data()));
}

std::shared_ptr<Texture> Texture::create_solid_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    uint8_t pixels[16] = {
        r, g, b, a,
        r, g, b, a,
        r, g, b, a,
        r, g, b, a
    };
    return create_from_rgba(2, 2, pixels);
}

} // namespace engine
