#define MINIAUDIO_IMPLEMENTATION
#include "miniaudio.h"

#include "engine/audio.hpp"
#include <vector>
#include <cmath>
#include <iostream>
#include <algorithm>

namespace engine {

namespace {

// Synthesize low-frequency footstep thud (duration ~0.06s, 44.1kHz)
std::vector<int16_t> generate_footstep_pcm(uint32_t sample_rate = 44100) {
    float duration = 0.065f;
    uint32_t total_samples = static_cast<uint32_t>(sample_rate * duration);
    std::vector<int16_t> pcm(total_samples);

    for (uint32_t i = 0; i < total_samples; ++i) {
        float t = static_cast<float>(i) / sample_rate;
        // Pitch sweep from 130 Hz down to 40 Hz
        float freq = 130.0f - (90.0f * (t / duration));
        float env = std::exp(-t * 55.0f);
        float sine_val = std::sin(2.0f * 3.14159265f * freq * t);
        // Small amount of high-frequency noise for floor contact texture
        float noise = ((float)rand() / (float)RAND_MAX * 2.0f - 1.0f) * 0.15f;
        float sample = (sine_val * 0.85f + noise) * env * 24000.0f;
        sample = std::clamp(sample, -32767.0f, 32767.0f);
        pcm[i] = static_cast<int16_t>(sample);
    }
    return pcm;
}

// Synthesize upward jump whoosh (duration ~0.14s, 44.1kHz)
std::vector<int16_t> generate_jump_pcm(uint32_t sample_rate = 44100) {
    float duration = 0.14f;
    uint32_t total_samples = static_cast<uint32_t>(sample_rate * duration);
    std::vector<int16_t> pcm(total_samples);

    for (uint32_t i = 0; i < total_samples; ++i) {
        float t = static_cast<float>(i) / sample_rate;
        // Frequency sweeps up from 140 Hz to 460 Hz
        float freq = 140.0f + 320.0f * (t / duration);
        float env = std::sin(3.14159265f * (t / duration)); // parabolic bell envelope
        float sine_val = std::sin(2.0f * 3.14159265f * freq * t);
        float sample = sine_val * env * 22000.0f;
        sample = std::clamp(sample, -32767.0f, 32767.0f);
        pcm[i] = static_cast<int16_t>(sample);
    }
    return pcm;
}

// Synthesize rewarding harmonic 3D chime for raycast hit (duration ~0.22s, 44.1kHz)
std::vector<int16_t> generate_hit_pcm(uint32_t sample_rate = 44100) {
    float duration = 0.22f;
    uint32_t total_samples = static_cast<uint32_t>(sample_rate * duration);
    std::vector<int16_t> pcm(total_samples);

    for (uint32_t i = 0; i < total_samples; ++i) {
        float t = static_cast<float>(i) / sample_rate;
        // 660 Hz (E5) + 880 Hz (A5) chord with exponential decay
        float env = std::exp(-t * 18.0f);
        float s1 = std::sin(2.0f * 3.14159265f * 660.0f * t);
        float s2 = std::sin(2.0f * 3.14159265f * 880.0f * t) * 0.6f;
        float sample = (s1 + s2) * 0.65f * env * 26000.0f;
        sample = std::clamp(sample, -32767.0f, 32767.0f);
        pcm[i] = static_cast<int16_t>(sample);
    }
    return pcm;
}

} // namespace

struct AudioManager::Impl {
    ma_engine engine{};
    bool initialized{false};

    // Buffer data storage
    std::vector<int16_t> footstep_pcm;
    std::vector<int16_t> jump_pcm;
    std::vector<int16_t> hit_pcm;

    ma_audio_buffer footstep_buf{};
    ma_audio_buffer jump_buf{};
    ma_audio_buffer hit_buf{};

    // Sound pools for concurrency
    static constexpr size_t POOL_SIZE = 4;
    ma_sound footstep_sounds[POOL_SIZE]{};
    size_t footstep_idx{0};

    ma_sound jump_sounds[POOL_SIZE]{};
    size_t jump_idx{0};

    ma_sound hit_sounds[POOL_SIZE]{};
    size_t hit_idx{0};

    bool init() {
        if (initialized) return true;

        ma_engine_config engine_config = ma_engine_config_init();
        ma_result res = ma_engine_init(&engine_config, &engine);
        if (res != MA_SUCCESS) {
            std::cerr << "[AudioManager] Failed to initialize miniaudio engine: " << res << std::endl;
            return false;
        }

        // 1. Synthesize procedural sound data
        footstep_pcm = generate_footstep_pcm();
        jump_pcm = generate_jump_pcm();
        hit_pcm = generate_hit_pcm();

        // 2. Initialize audio buffers
        ma_audio_buffer_config f_cfg = ma_audio_buffer_config_init(ma_format_s16, 1, footstep_pcm.size(), footstep_pcm.data(), NULL);
        ma_audio_buffer_init(&f_cfg, &footstep_buf);

        ma_audio_buffer_config j_cfg = ma_audio_buffer_config_init(ma_format_s16, 1, jump_pcm.size(), jump_pcm.data(), NULL);
        ma_audio_buffer_init(&j_cfg, &jump_buf);

        ma_audio_buffer_config h_cfg = ma_audio_buffer_config_init(ma_format_s16, 1, hit_pcm.size(), hit_pcm.data(), NULL);
        ma_audio_buffer_init(&h_cfg, &hit_buf);

        // 3. Initialize sound pools
        for (size_t i = 0; i < POOL_SIZE; ++i) {
            ma_sound_init_from_data_source(&engine, &footstep_buf, 0, NULL, &footstep_sounds[i]);
            ma_sound_set_spatialization_enabled(&footstep_sounds[i], MA_FALSE);
            ma_sound_set_volume(&footstep_sounds[i], 0.7f);

            ma_sound_init_from_data_source(&engine, &jump_buf, 0, NULL, &jump_sounds[i]);
            ma_sound_set_spatialization_enabled(&jump_sounds[i], MA_FALSE);
            ma_sound_set_volume(&jump_sounds[i], 0.85f);

            ma_sound_init_from_data_source(&engine, &hit_buf, 0, NULL, &hit_sounds[i]);
            ma_sound_set_spatialization_enabled(&hit_sounds[i], MA_TRUE);
            ma_sound_set_min_distance(&hit_sounds[i], 1.5f);
            ma_sound_set_max_distance(&hit_sounds[i], 35.0f);
            ma_sound_set_attenuation_model(&hit_sounds[i], ma_attenuation_model_inverse);
            ma_sound_set_volume(&hit_sounds[i], 1.0f);
        }

        initialized = true;
        std::cout << "[AudioManager] Initialized successfully with 3D Spatial Audio & procedural sound banks." << std::endl;
        return true;
    }

    void shutdown() {
        if (!initialized) return;

        for (size_t i = 0; i < POOL_SIZE; ++i) {
            ma_sound_uninit(&footstep_sounds[i]);
            ma_sound_uninit(&jump_sounds[i]);
            ma_sound_uninit(&hit_sounds[i]);
        }

        ma_audio_buffer_uninit(&footstep_buf);
        ma_audio_buffer_uninit(&jump_buf);
        ma_audio_buffer_uninit(&hit_buf);

        ma_engine_uninit(&engine);
        initialized = false;
    }
};

AudioManager::AudioManager()
    : impl_(std::make_unique<Impl>()) {}

AudioManager::~AudioManager() {
    shutdown();
}

bool AudioManager::init() {
    return impl_->init();
}

void AudioManager::shutdown() {
    if (impl_) {
        impl_->shutdown();
    }
}

bool AudioManager::is_initialized() const {
    return impl_ && impl_->initialized;
}

void AudioManager::update_listener(const glm::vec3& position, const glm::vec3& forward, const glm::vec3& up) {
    if (!impl_ || !impl_->initialized) return;
    ma_engine_listener_set_position(&impl_->engine, 0, position.x, position.y, position.z);
    ma_engine_listener_set_direction(&impl_->engine, 0, forward.x, forward.y, forward.z);
    ma_engine_listener_set_world_up(&impl_->engine, 0, up.x, up.y, up.z);
}

void AudioManager::play_footstep() {
    if (!impl_ || !impl_->initialized) return;
    auto& snd = impl_->footstep_sounds[impl_->footstep_idx];
    impl_->footstep_idx = (impl_->footstep_idx + 1) % Impl::POOL_SIZE;
    ma_sound_seek_to_pcm_frame(&snd, 0);
    ma_sound_start(&snd);
}

void AudioManager::play_jump() {
    if (!impl_ || !impl_->initialized) return;
    auto& snd = impl_->jump_sounds[impl_->jump_idx];
    impl_->jump_idx = (impl_->jump_idx + 1) % Impl::POOL_SIZE;
    ma_sound_seek_to_pcm_frame(&snd, 0);
    ma_sound_start(&snd);
}

void AudioManager::play_hit_3d(const glm::vec3& world_pos) {
    if (!impl_ || !impl_->initialized) return;
    auto& snd = impl_->hit_sounds[impl_->hit_idx];
    impl_->hit_idx = (impl_->hit_idx + 1) % Impl::POOL_SIZE;
    ma_sound_set_position(&snd, world_pos.x, world_pos.y, world_pos.z);
    ma_sound_seek_to_pcm_frame(&snd, 0);
    ma_sound_start(&snd);
}

void AudioManager::play_sound_file(const std::string& filepath, float volume) {
    if (!impl_ || !impl_->initialized) return;
    ma_sound sound;
    ma_result res = ma_sound_init_from_file(&impl_->engine, filepath.c_str(), 0, NULL, NULL, &sound);
    if (res == MA_SUCCESS) {
        ma_sound_set_volume(&sound, volume);
        ma_sound_start(&sound);
    }
}

} // namespace engine
