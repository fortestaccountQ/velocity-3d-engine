#include "engine/sky.hpp"
#include <cmath>
#include <algorithm>

namespace engine {

ProceduralSky::ProceduralSky(const std::string& name) : Node3D(name) {
    set_time_of_day(12.0f);
}

void ProceduralSky::set_sun_direction(float x, float y, float z) {
    set_sun_direction(glm::vec3(x, y, z));
}

void ProceduralSky::set_sun_direction(const glm::vec3& dir) {
    if (glm::length(dir) > 0.0001f) {
        params.sun_direction = glm::normalize(dir);
    }
}

void ProceduralSky::set_time_of_day(float hours) {
    params.time_of_day = std::clamp(hours, 0.0f, 24.0f);

    // Compute sun direction based on time of day (0 to 24 hours)
    // 6:00 is sunrise (east), 12:00 is solar noon (zenith), 18:00 is sunset (west)
    constexpr float PI = 3.14159265358979323846f;
    float solar_angle = (params.time_of_day - 6.0f) / 12.0f * PI; // 0 at dawn, PI/2 at noon, PI at dusk

    float sun_y = std::sin(solar_angle);
    float sun_x = -std::cos(solar_angle);
    float sun_z = 0.25f; // Slight tilt towards south for realistic shadows

    params.sun_direction = glm::normalize(glm::vec3(sun_x, sun_y, sun_z));
}

} // namespace engine
