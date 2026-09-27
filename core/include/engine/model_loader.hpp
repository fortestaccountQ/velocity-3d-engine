#pragma once

#include "engine/model.hpp"
#include <string>
#include <memory>

namespace engine {

class Scene;

class ModelLoader {
public:
    static std::shared_ptr<Model> load_model(Scene& scene, const std::string& filepath);
};

} // namespace engine
