#pragma once

#include <glm/glm.hpp>
#include <glm/gtc/matrix_transform.hpp>

namespace engine {

class Transform {
public:
    glm::vec3 position{0.0f, 0.0f, 0.0f};
    glm::vec3 rotation{0.0f, 0.0f, 0.0f}; // Euler angles in degrees (Pitch, Yaw, Roll)
    glm::vec3 scale{1.0f, 1.0f, 1.0f};

    Transform() = default;
    Transform(const glm::vec3& pos, const glm::vec3& rot = glm::vec3(0.0f), const glm::vec3& sc = glm::vec3(1.0f))
        : position(pos), rotation(rot), scale(sc) {}

    void set_position(float x, float y, float z) { position = { x, y, z }; }
    void set_rotation(float rx, float ry, float rz) { rotation = { rx, ry, rz }; }
    void set_scale(float sx, float sy, float sz) { scale = { sx, sy, sz }; }

    glm::mat4 model_matrix() const {
        glm::mat4 m = glm::mat4(1.0f);
        m = glm::translate(m, position);
        m = glm::rotate(m, glm::radians(rotation.x), glm::vec3(1.0f, 0.0f, 0.0f));
        m = glm::rotate(m, glm::radians(rotation.y), glm::vec3(0.0f, 1.0f, 0.0f));
        m = glm::rotate(m, glm::radians(rotation.z), glm::vec3(0.0f, 0.0f, 1.0f));
        m = glm::scale(m, scale);
        return m;
    }

    glm::mat4 normal_matrix() const {
        glm::mat3 m3 = glm::mat3(model_matrix());
        return glm::mat4(glm::transpose(glm::inverse(m3)));
    }
};

} // namespace engine
