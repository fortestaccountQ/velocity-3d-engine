#include "engine/cube_texture.hpp"

#include "stb_image.h"
#include "sokol_gfx.h"

#include <iostream>
#include <algorithm>
#include <cmath>
#include <cstring>

namespace engine {

CubeTexture::~CubeTexture() {
    destroy();
}

void CubeTexture::destroy() {
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
    cpu_faces.clear();
}

bool CubeTexture::ensure_gpu_resources() {
    if (view_id != 0 && sampler_id != 0 && image_id != 0) {
        return true;
    }
    if (!sg_isvalid() || cpu_faces.size() != 6 || size <= 0) {
        return false;
    }

    size_t expected_slice_bytes = static_cast<size_t>(size * size * 4);
    for (size_t f = 0; f < 6; ++f) {
        if (cpu_faces[f].size() < expected_slice_bytes) {
            return false;
        }
    }

    // 1. Calculate mip levels
    int num_mips = 1;
    int cur = size;
    while (cur > 1) {
        cur /= 2;
        num_mips++;
    }
    num_mips = std::min(num_mips, static_cast<int>(SG_MAX_MIPMAPS));

    // 2. Generate mip hierarchy per face
    std::vector<std::vector<uint8_t>> face_mips[6];
    for (int f = 0; f < 6; ++f) {
        face_mips[f].resize(num_mips);
        face_mips[f][0].assign(cpu_faces[f].data(), cpu_faces[f].data() + expected_slice_bytes);

        for (int lvl = 1; lvl < num_mips; ++lvl) {
            int prev_dim = std::max(1, size >> (lvl - 1));
            int curr_dim = std::max(1, size >> lvl);
            face_mips[f][lvl].resize(static_cast<size_t>(curr_dim * curr_dim * 4));

            const uint8_t* prev = face_mips[f][lvl - 1].data();
            uint8_t* curr = face_mips[f][lvl].data();

            for (int y = 0; y < curr_dim; ++y) {
                for (int x = 0; x < curr_dim; ++x) {
                    int x0 = x * 2;
                    int x1 = std::min(x * 2 + 1, prev_dim - 1);
                    int y0 = y * 2;
                    int y1 = std::min(y * 2 + 1, prev_dim - 1);

                    int i00 = (y0 * prev_dim + x0) * 4;
                    int i10 = (y0 * prev_dim + x1) * 4;
                    int i01 = (y1 * prev_dim + x0) * 4;
                    int i11 = (y1 * prev_dim + x1) * 4;

                    int dst = (y * curr_dim + x) * 4;
                    for (int c = 0; c < 4; ++c) {
                        int sum = prev[i00 + c] + prev[i10 + c] + prev[i01 + c] + prev[i11 + c];
                        curr[dst + c] = static_cast<uint8_t>((sum + 2) / 4);
                    }
                }
            }
        }
    }

    // 3. Assemble Sokol mip levels (each mip contains all 6 slices contiguously)
    std::vector<std::vector<uint8_t>> mip_buffers(num_mips);
    for (int lvl = 0; lvl < num_mips; ++lvl) {
        int curr_dim = std::max(1, size >> lvl);
        size_t slice_bytes = static_cast<size_t>(curr_dim * curr_dim * 4);
        mip_buffers[lvl].resize(6 * slice_bytes);

        for (int f = 0; f < 6; ++f) {
            std::memcpy(mip_buffers[lvl].data() + f * slice_bytes, face_mips[f][lvl].data(), slice_bytes);
        }
    }

    // 4. Create Sokol Cube Image
    sg_image_desc img_desc{};
    img_desc.type = SG_IMAGETYPE_CUBE;
    img_desc.num_slices = 6;
    img_desc.num_mipmaps = num_mips;
    img_desc.width = size;
    img_desc.height = size;
    img_desc.pixel_format = SG_PIXELFORMAT_RGBA8;
    for (int lvl = 0; lvl < num_mips; ++lvl) {
        img_desc.data.mip_levels[lvl] = { mip_buffers[lvl].data(), mip_buffers[lvl].size() };
    }
    img_desc.label = "cubemap-image";
    sg_image img = sg_make_image(&img_desc);
    if (img.id == 0) {
        std::cerr << "[CubeTexture] Error: sg_make_image failed for cubemap" << std::endl;
        return false;
    }

    // 5. Create Sokol Sampler with trilinear filtering & clamp to edge
    sg_sampler_desc smp_desc{};
    smp_desc.min_filter = SG_FILTER_LINEAR;
    smp_desc.mag_filter = SG_FILTER_LINEAR;
    smp_desc.mipmap_filter = SG_FILTER_LINEAR;
    smp_desc.wrap_u = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.wrap_v = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.wrap_w = SG_WRAP_CLAMP_TO_EDGE;
    smp_desc.max_lod = static_cast<float>(num_mips - 1);
    smp_desc.label = "cubemap-sampler";
    sg_sampler smp = sg_make_sampler(&smp_desc);

    // 6. Create Sokol View
    sg_view_desc view_desc{};
    view_desc.texture.image = img;
    view_desc.label = "cubemap-view";
    sg_view view = sg_make_view(&view_desc);

    image_id = img.id;
    sampler_id = smp.id;
    view_id = view.id;
    num_mipmaps = num_mips;
    return true;
}

std::shared_ptr<CubeTexture> CubeTexture::create_from_raw_faces(
    int resolution,
    const std::vector<std::vector<uint8_t>>& faces_rgba
) {
    if (faces_rgba.size() != 6 || resolution <= 0) {
        std::cerr << "[CubeTexture] Error: exactly 6 faces required, size=" << faces_rgba.size() << std::endl;
        return nullptr;
    }

    auto cube = std::make_shared<CubeTexture>();
    cube->size = resolution;
    cube->cpu_faces = faces_rgba;

    if (sg_isvalid()) {
        cube->ensure_gpu_resources();
    }
    return cube;
}

std::shared_ptr<CubeTexture> CubeTexture::load_from_files(
    const std::string& px,
    const std::string& nx,
    const std::string& py,
    const std::string& ny,
    const std::string& pz,
    const std::string& nz
) {
    const std::string paths[6] = { px, nx, py, ny, pz, nz };
    std::vector<std::vector<uint8_t>> faces(6);
    int common_res = 0;

    stbi_set_flip_vertically_on_load(false);

    for (int f = 0; f < 6; ++f) {
        int w = 0, h = 0, comp = 0;
        uint8_t* data = stbi_load(paths[f].c_str(), &w, &h, &comp, 4);
        if (!data) {
            std::cerr << "[CubeTexture] Warning: failed to load face " << f << " from '" << paths[f] << "'" << std::endl;
            for (int k = 0; k < f; ++k) {
                // Already stored in faces std::vector, freed automatically
            }
            return create_default();
        }
        if (w != h) {
            std::cerr << "[CubeTexture] Warning: cubemap face not square (" << w << "x" << h << ") at " << paths[f] << std::endl;
        }
        if (f == 0) {
            common_res = w;
        } else if (w != common_res || h != common_res) {
            std::cerr << "[CubeTexture] Warning: face dimension mismatch: " << w << "x" << h
                      << " vs expected " << common_res << "x" << common_res << std::endl;
        }
        faces[f].assign(data, data + (w * h * 4));
        stbi_image_free(data);
    }

    return create_from_raw_faces(common_res, faces);
}

std::shared_ptr<CubeTexture> CubeTexture::load_from_hdr(
    const std::string& path,
    int resolution
) {
    int w = 0, h = 0, comp = 0;
    stbi_set_flip_vertically_on_load(false);
    float* data = stbi_loadf(path.c_str(), &w, &h, &comp, 0);
    if (!data) {
        std::cerr << "[CubeTexture] Warning: failed to load HDR file from '" << path << "', falling back to default sky." << std::endl;
        return create_default(resolution);
    }

    if (resolution <= 0) resolution = 512;
    std::vector<std::vector<uint8_t>> faces(6);
    for (int f = 0; f < 6; ++f) {
        faces[f].resize(resolution * resolution * 4);
    }

    constexpr float PI = 3.14159265358979323846f;

    auto get_rgb = [&](int px, int py) -> glm::vec3 {
        px = (px % w + w) % w;
        py = std::clamp(py, 0, h - 1);
        int idx = (py * w + px) * comp;
        return glm::vec3(data[idx], data[idx + 1], data[idx + 2]);
    };

    for (int f = 0; f < 6; ++f) {
        for (int y = 0; y < resolution; ++y) {
            for (int x = 0; x < resolution; ++x) {
                float u = 2.0f * (static_cast<float>(x) + 0.5f) / static_cast<float>(resolution) - 1.0f;
                float v = 2.0f * (static_cast<float>(y) + 0.5f) / static_cast<float>(resolution) - 1.0f;

                glm::vec3 dir(0.0f);
                switch (f) {
                    case 0: dir = glm::vec3( 1.0f,   -v,   -u); break; // +X
                    case 1: dir = glm::vec3(-1.0f,   -v,    u); break; // -X
                    case 2: dir = glm::vec3(    u,  1.0f,    v); break; // +Y
                    case 3: dir = glm::vec3(    u, -1.0f,   -v); break; // -Y
                    case 4: dir = glm::vec3(    u,   -v,  1.0f); break; // +Z
                    case 5: dir = glm::vec3(   -u,   -v, -1.0f); break; // -Z
                }
                dir = glm::normalize(dir);

                float phi = std::atan2(dir.z, dir.x);
                float theta = std::asin(std::clamp(dir.y, -1.0f, 1.0f));
                float u_hdr = phi / (2.0f * PI) + 0.5f;
                float v_hdr = 0.5f - theta / PI;

                float u_px = u_hdr * static_cast<float>(w - 1);
                float v_px = v_hdr * static_cast<float>(h - 1);
                int x0 = static_cast<int>(std::floor(u_px));
                int y0 = static_cast<int>(std::floor(v_px));
                int x1 = (x0 + 1) % w;
                int y1 = std::clamp(y0 + 1, 0, h - 1);
                float fx = u_px - static_cast<float>(x0);
                float fy = v_px - static_cast<float>(y0);

                glm::vec3 c00 = get_rgb(x0, y0);
                glm::vec3 c10 = get_rgb(x1, y0);
                glm::vec3 c01 = get_rgb(x0, y1);
                glm::vec3 c11 = get_rgb(x1, y1);

                glm::vec3 c0 = glm::mix(c00, c10, fx);
                glm::vec3 c1 = glm::mix(c01, c11, fx);
                glm::vec3 sample_rgb = glm::mix(c0, c1, fy);

                // Tone mapping (Reinhard) + Gamma correction 2.2
                glm::vec3 mapped = sample_rgb / (sample_rgb + glm::vec3(1.0f));
                mapped.r = std::pow(std::max(0.0f, mapped.r), 1.0f / 2.2f);
                mapped.g = std::pow(std::max(0.0f, mapped.g), 1.0f / 2.2f);
                mapped.b = std::pow(std::max(0.0f, mapped.b), 1.0f / 2.2f);

                uint8_t R = static_cast<uint8_t>(std::clamp(mapped.r, 0.0f, 1.0f) * 255.0f);
                uint8_t G = static_cast<uint8_t>(std::clamp(mapped.g, 0.0f, 1.0f) * 255.0f);
                uint8_t B = static_cast<uint8_t>(std::clamp(mapped.b, 0.0f, 1.0f) * 255.0f);
                uint8_t A = 255;

                int dst_idx = (y * resolution + x) * 4;
                faces[f][dst_idx + 0] = R;
                faces[f][dst_idx + 1] = G;
                faces[f][dst_idx + 2] = B;
                faces[f][dst_idx + 3] = A;
            }
        }
    }

    stbi_image_free(data);
    return create_from_raw_faces(resolution, faces);
}

std::shared_ptr<CubeTexture> CubeTexture::create_gradient(
    const glm::vec3& top_color,
    const glm::vec3& horizon_color,
    const glm::vec3& bottom_color,
    int resolution
) {
    if (resolution <= 0) resolution = 256;
    std::vector<std::vector<uint8_t>> faces(6);
    for (int f = 0; f < 6; ++f) {
        faces[f].resize(resolution * resolution * 4);
    }

    for (int f = 0; f < 6; ++f) {
        for (int y = 0; y < resolution; ++y) {
            for (int x = 0; x < resolution; ++x) {
                float u = 2.0f * (static_cast<float>(x) + 0.5f) / static_cast<float>(resolution) - 1.0f;
                float v = 2.0f * (static_cast<float>(y) + 0.5f) / static_cast<float>(resolution) - 1.0f;

                glm::vec3 dir(0.0f);
                switch (f) {
                    case 0: dir = glm::vec3( 1.0f,   -v,   -u); break;
                    case 1: dir = glm::vec3(-1.0f,   -v,    u); break;
                    case 2: dir = glm::vec3(    u,  1.0f,    v); break;
                    case 3: dir = glm::vec3(    u, -1.0f,   -v); break;
                    case 4: dir = glm::vec3(    u,   -v,  1.0f); break;
                    case 5: dir = glm::vec3(   -u,   -v, -1.0f); break;
                }
                dir = glm::normalize(dir);

                glm::vec3 col;
                if (dir.y >= 0.0f) {
                    float t = std::pow(dir.y, 0.7f);
                    col = glm::mix(horizon_color, top_color, t);
                } else {
                    float t = std::pow(-dir.y, 0.7f);
                    col = glm::mix(horizon_color, bottom_color, t);
                }

                uint8_t R = static_cast<uint8_t>(std::clamp(col.r, 0.0f, 1.0f) * 255.0f);
                uint8_t G = static_cast<uint8_t>(std::clamp(col.g, 0.0f, 1.0f) * 255.0f);
                uint8_t B = static_cast<uint8_t>(std::clamp(col.b, 0.0f, 1.0f) * 255.0f);
                uint8_t A = 255;

                int dst_idx = (y * resolution + x) * 4;
                faces[f][dst_idx + 0] = R;
                faces[f][dst_idx + 1] = G;
                faces[f][dst_idx + 2] = B;
                faces[f][dst_idx + 3] = A;
            }
        }
    }

    return create_from_raw_faces(resolution, faces);
}

std::shared_ptr<CubeTexture> CubeTexture::create_default(int resolution) {
    return create_gradient(
        glm::vec3(0.25f, 0.55f, 0.95f),
        glm::vec3(0.70f, 0.82f, 0.95f),
        glm::vec3(0.22f, 0.24f, 0.28f),
        resolution
    );
}

} // namespace engine
