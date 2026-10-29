#pragma once

#include "engine/node3d.hpp"
#include "contracts/phase4_environment_contracts.h"
#include <glm/glm.hpp>
#include <memory>
#include <string>

namespace engine {

class ProceduralSky : public Node3D {
public:
    SkyParams params;

    ProceduralSky(const std::string& name = "ProceduralSky");

    void set_sun_direction(float x, float y, float z);
    void set_sun_direction(const glm::vec3& dir);
    glm::vec3 sun_direction() const { return params.sun_direction; }

    void set_turbidity(float val) { params.turbidity = val; }
    float turbidity() const { return params.turbidity; }

    void set_rayleigh(float val) { params.rayleigh = val; }
    float rayleigh() const { return params.rayleigh; }

    void set_mie_coefficient(float val) { params.mie_coefficient = val; }
    float mie_coefficient() const { return params.mie_coefficient; }

    void set_mie_directional_g(float val) { params.mie_directional_g = val; }
    float mie_directional_g() const { return params.mie_directional_g; }

    void set_time_of_day(float hours);
    float time_of_day() const { return params.time_of_day; }

    void set_rayleigh_color(const glm::vec3& col) { params.rayleigh_color = col; }
    void set_rayleigh_color(float r, float g, float b) { params.rayleigh_color = { r, g, b }; }
    glm::vec3 rayleigh_color() const { return params.rayleigh_color; }

    void set_mie_color(const glm::vec3& col) { params.mie_color = col; }
    void set_mie_color(float r, float g, float b) { params.mie_color = { r, g, b }; }
    glm::vec3 mie_color() const { return params.mie_color; }
};

} // namespace engine
