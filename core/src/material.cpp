#include "engine/material.hpp"

namespace engine {

PipelineManager& PipelineManager::instance() {
    static PipelineManager s_inst;
    return s_inst;
}

PipelineManager::~PipelineManager() {
    release_all();
}

void PipelineManager::release_all() {
    for (auto& [key, pip] : cache_) {
        if (pip.id != 0 && sg_isvalid()) {
            sg_destroy_pipeline(pip);
        }
    }
    cache_.clear();
}

uint64_t PipelineManager::make_key(
    uint32_t shader_id,
    SideMode side,
    bool depth_write,
    bool depth_test,
    BlendMode blend_mode,
    bool wireframe,
    bool is_instanced,
    int sample_count
) {
    uint64_t key = 0;
    key |= (static_cast<uint64_t>(shader_id) & 0xFFFF);
    key |= (static_cast<uint64_t>(side) & 0x3) << 16;
    key |= (static_cast<uint64_t>(depth_write ? 1 : 0) & 0x1) << 18;
    key |= (static_cast<uint64_t>(depth_test ? 1 : 0) & 0x1) << 19;
    key |= (static_cast<uint64_t>(blend_mode) & 0x7) << 20;
    key |= (static_cast<uint64_t>(wireframe ? 1 : 0) & 0x1) << 23;
    key |= (static_cast<uint64_t>(is_instanced ? 1 : 0) & 0x1) << 24;
    key |= (static_cast<uint64_t>(sample_count) & 0xF) << 25;
    return key;
}

sg_pipeline PipelineManager::get_or_create(uint64_t key, const sg_pipeline_desc& desc_template) {
    auto it = cache_.find(key);
    if (it != cache_.end()) {
        return it->second;
    }
    sg_pipeline pip = sg_make_pipeline(&desc_template);
    cache_[key] = pip;
    return pip;
}

} // namespace engine
