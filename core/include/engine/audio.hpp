#pragma once

#include <glm/glm.hpp>
#include <string>
#include <memory>

namespace engine {

class AudioManager {
public:
    AudioManager();
    ~AudioManager();

    bool init();
    void shutdown();
    bool is_initialized() const;

    void update_listener(const glm::vec3& position, const glm::vec3& forward, const glm::vec3& up);

    // Procedural sound effects
    void play_footstep();
    void play_jump();
    void play_hit_3d(const glm::vec3& world_pos);
    void play_sound_file(const std::string& filepath, float volume = 1.0f);

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace engine
