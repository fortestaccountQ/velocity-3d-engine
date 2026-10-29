#pragma once

#include "engine/node3d.hpp"
#include "engine/texture.hpp"
#include "engine/material.hpp"
#include "engine/mesh.hpp"
#include "engine/camera.hpp"
#include <glm/glm.hpp>
#include <vector>
#include <memory>
#include <utility>

namespace engine {

struct Particle {
    glm::vec3 position{0.0f};
    glm::vec3 velocity{0.0f};
    glm::vec4 color{1.0f};
    float size{1.0f};
    float age{0.0f};
    float lifetime{1.0f};
    bool alive{false};
};

class ParticleEmitter : public Node3D {
public:
    size_t max_particles{1000};
    float spawn_rate{50.0f}; // particles per second
    std::pair<float, float> lifetime_range{1.0f, 2.0f};
    std::pair<glm::vec3, glm::vec3> velocity_range{ {-1.0f, 1.0f, -1.0f}, {1.0f, 3.0f, 1.0f} };
    glm::vec3 gravity{0.0f, -9.81f, 0.0f};
    glm::vec4 start_color{1.0f, 1.0f, 1.0f, 1.0f};
    glm::vec4 end_color{1.0f, 1.0f, 1.0f, 0.0f};
    float start_size{0.2f};
    float end_size{0.0f};
    std::shared_ptr<Texture> texture{nullptr};
    BlendMode blend_mode{BlendMode::Alpha};
    bool emitting{true};

    ParticleEmitter(size_t max_p = 1000);
    ~ParticleEmitter() override = default;

    void burst(int count);
    void update(float dt);
    void reset();
    size_t active_count() const;

    const std::vector<Particle>& particles() const { return particles_; }
    std::vector<Particle>& particles() { return particles_; }

    AABB world_aabb() const override;

    void generate_billboard_quads(const Camera& camera, std::vector<Vertex>& out_vertices, std::vector<uint16_t>& out_indices) const;
    void update_mesh(const Camera& camera) const;
    std::shared_ptr<Mesh> get_particle_mesh() const { return particle_mesh_; }

private:
    std::vector<Particle> particles_;
    float spawn_accumulator_{0.0f};
    mutable std::shared_ptr<Mesh> particle_mesh_{nullptr};

    void spawn_particle(Particle& p);
};

} // namespace engine
