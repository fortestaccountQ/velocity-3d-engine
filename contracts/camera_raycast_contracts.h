#pragma once

#include <glm/glm.hpp>
#include <memory>
#include "engine/physics.hpp"

namespace engine {

class ICameraRaycast {
public:
    virtual ~ICameraRaycast() = default;

    // Convert 2D viewport coordinates (pixel space) to a 3D ray in world space
    virtual Ray screen_to_ray(float mouse_x, float mouse_y, float screen_w, float screen_h) const = 0;
};

struct OrbitCameraParams {
    glm::vec3 target{0.0f, 0.0f, 0.0f};
    float distance{5.0f};
    float min_distance{0.5f};
    float max_distance{500.0f};
    float yaw{-90.0f};      // Azimuth angle in degrees
    float pitch{20.0f};     // Elevation angle in degrees
    float min_pitch{-89.0f};
    float max_pitch{89.0f};
    float damping{0.1f};
    float rotate_speed{0.3f};
    float zoom_speed{1.0f};
    float pan_speed{0.005f};
};

} // namespace engine
