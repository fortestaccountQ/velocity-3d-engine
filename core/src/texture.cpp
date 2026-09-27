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
        if (sg_isvalid()) {
            sg_destroy_view(sg_view{view_id});
        }
        view_id = 0;
    }
    if (sampler_id != 0) {
        if (sg_isvalid()) {
            sg_destroy_sampler(sg_sampler{sampler_id});
        }
        sampler_id = 0;
    }
    if (image_id != 0) {
        if (sg_isvalid()) {
            sg_destroy_image(sg_image{image_id});
        }
        image_id = 0;
    }
}

bool Texture::ensure_gpu_resources() {
    if (view_id != 0 && sampler_id != 0 && image_id != 0) {
        return true;
    }
    if (!sg_isvalid()) {
        return false;
    }
    if (cpu_pixels.empty() || width <= 0 || height <= 0) {
        return false;
    }

    // Compute number of mip levels
    int num_mips = 1;
    int tw = width;
    int th = height;
    while (tw > 1 || th > 1) {
        tw = std::max(1, tw / 2);
        th = std::max(1, th / 2);
        num_mips++;
    }
    num_mips = std::min(num_mips, static_cast<int>(SG_MAX_MIPMAPS));

    // Generate mip buffers with 2x2 box filtering
    std::vector<std::vector<uint8_t>> mip_buffers(num_mips);
    mip_buffers[0] = cpu_pixels;

    for (int lvl = 1; lvl < num_mips; ++lvl) {
        int prev_w = std::max(1, width >> (lvl - 1));
        int prev_h = std::max(1, height >> (lvl - 1));
        int curr_w = std::max(1, width >> lvl);
        int curr_h = std::max(1, height >> lvl);

        const uint8_t* prev_data = mip_buffers[lvl - 1].data();
        std::vector<uint8_t> curr_data(static_cast<size_t>(curr_w * curr_h * 4));

        for (int y = 0; y < curr_h; ++y) {
            for (int x = 0; x < curr_w; ++x) {
                int src_x0 = x * 2;
                int src_x1 = std::min(x * 2 + 1, prev_w - 1);
                int src_y0 = y * 2;
                int src_y1 = std::min(y * 2 + 1, prev_h - 1);

                int idx00 = (src_y0 * prev_w + src_x0) * 4;
                int idx10 = (src_y0 * prev_w + src_x1) * 4;
                int idx01 = (src_y1 * prev_w + src_x0) * 4;
                int idx11 = (src_y1 * prev_w + src_x1) * 4;

                int dst_idx = (y * curr_w + x) * 4;
                for (int c = 0; c < 4; ++c) {
                    int sum = prev_data[idx00 + c] +
                              prev_data[idx10 + c] +
                              prev_data[idx01 + c] +
                              prev_data[idx11 + c];
                    curr_data[dst_idx + c] = static_cast<uint8_t>((sum + 2) / 4);
                }
            }
        }
        mip_buffers[lvl] = std::move(curr_data);
    }

    // 1. Create GPU Image with Mipmaps
    sg_image_desc img_desc{};
    img_desc.width = width;
    img_desc.height = height;
    img_desc.num_mipmaps = num_mips;
    img_desc.pixel_format = SG_PIXELFORMAT_RGBA8;
    for (int lvl = 0; lvl < num_mips; ++lvl) {
        img_desc.data.mip_levels[lvl] = { mip_buffers[lvl].data(), mip_buffers[lvl].size() };
    }
    img_desc.label = "texture-rgba-image";
    sg_image img = sg_make_image(&img_desc);
    image_id = img.id;

    // 2. Create GPU Sampler (Trilinear + Anisotropy 8x)
    sg_sampler_desc smp_desc{};
    smp_desc.min_filter = SG_FILTER_LINEAR;
    smp_desc.mag_filter = SG_FILTER_LINEAR;
    smp_desc.mipmap_filter = SG_FILTER_LINEAR;
    smp_desc.max_anisotropy = 8;
    smp_desc.wrap_u = SG_WRAP_REPEAT;
    smp_desc.wrap_v = SG_WRAP_REPEAT;
    smp_desc.label = "texture-rgba-sampler";
    sg_sampler smp = sg_make_sampler(&smp_desc);
    sampler_id = smp.id;

    // 3. Create GPU Texture View
    sg_view_desc view_desc{};
    view_desc.texture.image = img;
    view_desc.label = "texture-rgba-view";
    sg_view view = sg_make_view(&view_desc);
    view_id = view.id;

    return is_valid();
}

std::shared_ptr<Texture> Texture::create_from_rgba(int width, int height, const uint8_t* pixels) {
    if (!pixels || width <= 0 || height <= 0) {
        return nullptr;
    }

    auto tex = std::make_shared<Texture>();
    tex->width = width;
    tex->height = height;
    tex->channels = 4;
    tex->cpu_pixels.assign(pixels, pixels + (width * height * 4));

    tex->ensure_gpu_resources();
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
