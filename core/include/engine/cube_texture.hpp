#pragma once

#include <string>
#include <memory>
#include <cstdint>
#include <vector>
#include <glm/glm.hpp>

namespace engine {

class CubeTexture {
public:
    uint32_t image_id{0};
    uint32_t sampler_id{0};
    uint32_t view_id{0};
    int size{0};
    int num_mipmaps{1};
    std::vector<std::vector<uint8_t>> cpu_faces;

    CubeTexture() = default;
    ~CubeTexture();

    void destroy();
    bool is_valid() const { return image_id != 0 && view_id != 0 && sampler_id != 0; }
    bool ensure_gpu_resources();

    static std::shared_ptr<CubeTexture> load_from_files(
        const std::string& px,
        const std::string& nx,
        const std::string& py,
        const std::string& ny,
        const std::string& pz,
        const std::string& nz
    );

    static std::shared_ptr<CubeTexture> load_from_hdr(
        const std::string& path,
        int resolution = 512
    );

    static std::shared_ptr<CubeTexture> create_default(int resolution = 256);

    static std::shared_ptr<CubeTexture> create_gradient(
        const glm::vec3& top_color = glm::vec3(0.25f, 0.55f, 0.95f),
        const glm::vec3& horizon_color = glm::vec3(0.7f, 0.8f, 0.95f),
        const glm::vec3& bottom_color = glm::vec3(0.2f, 0.22f, 0.25f),
        int resolution = 256
    );

    static std::shared_ptr<CubeTexture> create_from_raw_faces(
        int resolution,
        const std::vector<std::vector<uint8_t>>& faces_rgba
    );
};

} // namespace engine
