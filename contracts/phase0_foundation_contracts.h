#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <glm/glm.hpp>

namespace engine {

// ---------------------------------------------------------------------------
// UI Command Contract for Phase 0.1
// ---------------------------------------------------------------------------
enum class UICommandType : uint8_t {
    Text = 0,
    Rect = 1,
    Line = 2,
    Crosshair = 3
};

struct UICommand {
    UICommandType type{UICommandType::Rect};
    std::string text{};
    glm::vec2 pos{0.0f, 0.0f};      // (x, y) position
    glm::vec2 size{0.0f, 0.0f};     // (w, h) or (size, scale)
    glm::vec4 color{1.0f, 1.0f, 1.0f, 1.0f};
    float thickness{1.0f};
};

// ---------------------------------------------------------------------------
// Instanced Rendering Contract for Phase 0.2
// ---------------------------------------------------------------------------
// Must be strictly 16-byte aligned for GPU buffer compatibility
// Total size: 80 bytes (64 bytes mat4 + 16 bytes vec4)
struct InstanceAttributes {
    glm::mat4 model_matrix{1.0f};
    glm::vec4 color{1.0f, 1.0f, 1.0f, 1.0f};
};

} // namespace engine
