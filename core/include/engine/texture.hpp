#pragma once

#include <string>
#include <memory>
#include <cstdint>
#include <vector>

#include "contracts/phase2_materials_contracts.h"

namespace engine {

class Texture {
public:
    uint32_t image_id{0};
    uint32_t sampler_id{0};
    uint32_t view_id{0};
    int width{0};
    int height{0};
    int channels{0};
    bool is_pixel_art{false};

    TextureWrap wrap_s{TextureWrap::Repeat};
    TextureWrap wrap_t{TextureWrap::Repeat};
    TextureFilter filter_min{TextureFilter::Linear};
    TextureFilter filter_mag{TextureFilter::Linear};

    std::vector<uint8_t> cpu_pixels;

    Texture() = default;
    ~Texture();

    bool ensure_gpu_resources();
    void destroy();
    bool is_valid() const { return image_id != 0 && view_id != 0 && sampler_id != 0; }

    static std::shared_ptr<Texture> load_from_file(const std::string& filepath, bool is_pixel_art = false);
    static std::shared_ptr<Texture> create_from_rgba(int width, int height, const uint8_t* pixels, bool is_pixel_art = false);
    static std::shared_ptr<Texture> create_data_texture(int width, int height, const uint8_t* data, int channels = 4);
    static std::shared_ptr<Texture> create_checkerboard(
        int width = 64,
        int height = 64,
        int tile_size = 8,
        uint32_t color1 = 0xFFFFFFFF,
        uint32_t color2 = 0xFF2A2A38
    );
    static std::shared_ptr<Texture> create_solid_color(uint8_t r, uint8_t g, uint8_t b, uint8_t a = 255);
};

} // namespace engine
