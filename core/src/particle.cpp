#include "engine/particle.hpp"
#include <random>
#include <algorithm>

namespace engine {

static float rand_range(float a, float b) {
    if (a >= b) return a;
    static thread_local std::mt19937 rng(42);
    std::uniform_real_distribution<float> dist(a, b);
    return dist(rng);
}

ParticleEmitter::ParticleEmitter(size_t max_p)
    : Node3D("ParticleEmitter"), max_particles(max_p) {
    particles_.resize(max_particles);
    cast_shadows = false;
}

void ParticleEmitter::spawn_particle(Particle& p) {
    p.position = world_position();
    p.velocity = glm::vec3(
        rand_range(velocity_range.first.x, velocity_range.second.x),
        rand_range(velocity_range.first.y, velocity_range.second.y),
        rand_range(velocity_range.first.z, velocity_range.second.z)
    );
    p.lifetime = rand_range(lifetime_range.first, lifetime_range.second);
    p.age = 0.0f;
    p.color = start_color;
    p.size = start_size;
    p.alive = true;
}

void ParticleEmitter::burst(int count) {
    int spawned = 0;
    for (auto& p : particles_) {
        if (!p.alive) {
            spawn_particle(p);
            spawned++;
            if (spawned >= count) break;
        }
    }
}

void ParticleEmitter::update(float dt) {
    if (particles_.size() != max_particles) {
        particles_.resize(max_particles);
    }

    if (emitting && spawn_rate > 0.0f) {
        spawn_accumulator_ += dt * spawn_rate;
        int to_spawn = static_cast<int>(spawn_accumulator_);
        if (to_spawn > 0) {
            spawn_accumulator_ -= static_cast<float>(to_spawn);
            int spawned = 0;
            for (auto& p : particles_) {
                if (!p.alive) {
                    spawn_particle(p);
                    spawned++;
                    if (spawned >= to_spawn) break;
                }
            }
        }
    }

    for (auto& p : particles_) {
        if (!p.alive) continue;

        p.age += dt;
        if (p.age >= p.lifetime) {
            p.alive = false;
            continue;
        }

        p.velocity += gravity * dt;
        p.position += p.velocity * dt;

        float t = (p.lifetime > 1e-5f) ? (p.age / p.lifetime) : 1.0f;
        p.color = glm::mix(start_color, end_color, t);
        p.size = glm::mix(start_size, end_size, t);
    }
}

void ParticleEmitter::reset() {
    for (auto& p : particles_) {
        p.alive = false;
    }
    spawn_accumulator_ = 0.0f;
}

size_t ParticleEmitter::active_count() const {
    size_t count = 0;
    for (const auto& p : particles_) {
        if (p.alive) count++;
    }
    return count;
}

AABB ParticleEmitter::world_aabb() const {
    glm::vec3 min_p(1e9f);
    glm::vec3 max_p(-1e9f);
    bool any_alive = false;

    for (const auto& p : particles_) {
        if (p.alive) {
            any_alive = true;
            float r = p.size * 0.5f;
            min_p = glm::min(min_p, p.position - glm::vec3(r));
            max_p = glm::max(max_p, p.position + glm::vec3(r));
        }
    }

    if (!any_alive) {
        glm::vec3 w = world_position();
        return AABB{ w, w };
    }
    return AABB{ min_p, max_p };
}

void ParticleEmitter::generate_billboard_quads(const Camera& camera,
                                               std::vector<Vertex>& out_vertices,
                                               std::vector<uint16_t>& out_indices) const {
    glm::mat4 v = camera.view_matrix();
    glm::vec3 right(v[0][0], v[1][0], v[2][0]);
    glm::vec3 up(v[0][1], v[1][1], v[2][1]);

    for (const auto& p : particles_) {
        if (!p.alive) continue;

        float half_s = p.size * 0.5f;
        glm::vec3 r_offset = right * half_s;
        glm::vec3 u_offset = up * half_s;

        uint16_t base_idx = static_cast<uint16_t>(out_vertices.size());

        Vertex v0{};
        v0.position = p.position - r_offset - u_offset;
        v0.normal = -camera.forward();
        v0.uv = glm::vec2(0.0f, 1.0f);
        v0.color = p.color;

        Vertex v1{};
        v1.position = p.position + r_offset - u_offset;
        v1.normal = -camera.forward();
        v1.uv = glm::vec2(1.0f, 1.0f);
        v1.color = p.color;

        Vertex v2{};
        v2.position = p.position + r_offset + u_offset;
        v2.normal = -camera.forward();
        v2.uv = glm::vec2(1.0f, 0.0f);
        v2.color = p.color;

        Vertex v3{};
        v3.position = p.position - r_offset + u_offset;
        v3.normal = -camera.forward();
        v3.uv = glm::vec2(0.0f, 0.0f);
        v3.color = p.color;

        out_vertices.push_back(v0);
        out_vertices.push_back(v1);
        out_vertices.push_back(v2);
        out_vertices.push_back(v3);

        out_indices.push_back(base_idx + 0);
        out_indices.push_back(base_idx + 1);
        out_indices.push_back(base_idx + 2);
        out_indices.push_back(base_idx + 0);
        out_indices.push_back(base_idx + 2);
        out_indices.push_back(base_idx + 3);
    }
}

void ParticleEmitter::update_mesh(const Camera& camera) const {
    if (!particle_mesh_) {
        particle_mesh_ = std::make_shared<Mesh>();
        particle_mesh_->mark_dynamic();
    }
    particle_mesh_->cpu_vertices.clear();
    particle_mesh_->cpu_indices.clear();
    generate_billboard_quads(camera, particle_mesh_->cpu_vertices, particle_mesh_->cpu_indices);
    particle_mesh_->num_indices = static_cast<int>(particle_mesh_->cpu_indices.size());
    particle_mesh_->ensure_gpu_buffers();
}

} // namespace engine
