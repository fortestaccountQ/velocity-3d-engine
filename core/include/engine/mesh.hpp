#pragma once

#include <glm/glm.hpp>
#include <memory>
#include <cstdint>

namespace engine {

struct Vertex {
    glm::vec3 position;
    glm::vec3 normal;
    glm::vec4 color;
};

class Mesh {
public:
    Mesh() = default;
    ~Mesh();

    uint32_t vbuf_id{0};
    uint32_t ibuf_id{0};
    int num_indices{0};

    static std::shared_ptr<Mesh> create_cube();
    void destroy();
};

} // namespace engine
