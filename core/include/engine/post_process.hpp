#pragma once

#include <cstdint>
#include <memory>
#include <vector>
#include <string>
#include <glm/glm.hpp>
#include "engine/render_target.hpp"

namespace engine {

class Scene;
class Camera;
class EngineApp;

enum class TonemappingMode {
    ACESFilmic = 0,
    Reinhard = 1,
    Cineon = 2,
    Linear = 3,
    Neutral = 4
};

class PostProcessPass {
public:
    virtual ~PostProcessPass() = default;
    virtual const std::string& name() const = 0;
    virtual void render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) = 0;
    virtual void destroy() {}

    bool enabled{true};
};

class BloomPass : public PostProcessPass {
public:
    float threshold{1.0f};
    float strength{1.5f};
    float radius{0.5f};

    BloomPass(float threshold = 1.0f, float strength = 1.5f, float radius = 0.5f);
    ~BloomPass() override;
    void destroy() override;

    const std::string& name() const override { static std::string n = "BloomPass"; return n; }
    void render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) override;

private:
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
    void init_pipeline();
};

class SSAOPass : public PostProcessPass {
public:
    float radius{0.5f};
    float bias{0.025f};
    float power{1.0f};

    SSAOPass(float radius = 0.5f, float bias = 0.025f, float power = 1.0f);
    ~SSAOPass() override;
    void destroy() override;

    const std::string& name() const override { static std::string n = "SSAOPass"; return n; }
    void render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) override;

private:
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
    void init_pipeline();
};

class FXAAPass : public PostProcessPass {
public:
    FXAAPass();
    ~FXAAPass() override;
    void destroy() override;

    const std::string& name() const override { static std::string n = "FXAAPass"; return n; }
    void render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) override;

private:
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
    void init_pipeline();
};

class TonemappingPass : public PostProcessPass {
public:
    TonemappingMode mode{TonemappingMode::ACESFilmic};
    float exposure{1.0f};
    float gamma{2.2f};

    TonemappingPass(TonemappingMode mode = TonemappingMode::ACESFilmic, float exposure = 1.0f, float gamma = 2.2f);
    ~TonemappingPass() override;
    void destroy() override;

    const std::string& name() const override { static std::string n = "TonemappingPass"; return n; }
    void render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) override;

private:
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
    void init_pipeline();
};

class VignetteChromaticPass : public PostProcessPass {
public:
    float vignette{0.3f};
    float chromatic{0.005f};
    float grain{0.02f};
    float time{0.0f};

    VignetteChromaticPass(float vignette = 0.3f, float chromatic = 0.005f, float grain = 0.02f);
    ~VignetteChromaticPass() override;
    void destroy() override;

    const std::string& name() const override { static std::string n = "VignetteChromaticPass"; return n; }
    void render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) override;

private:
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
    void init_pipeline();
};

class ColorGradingPass : public PostProcessPass {
public:
    float contrast{1.0f};
    float saturation{1.0f};
    float brightness{1.0f};

    ColorGradingPass(float contrast = 1.0f, float saturation = 1.0f, float brightness = 1.0f);
    ~ColorGradingPass() override;
    void destroy() override;

    const std::string& name() const override { static std::string n = "ColorGradingPass"; return n; }
    void render(RenderTarget& input, RenderTarget& depth_source, RenderTarget& output, uint32_t quad_vbuf, uint32_t quad_ibuf) override;

private:
    uint32_t pip_id_{0};
    uint32_t shd_id_{0};
    void init_pipeline();
};

class EffectComposer {
public:
    EffectComposer(int width = 800, int height = 600);
    explicit EffectComposer(EngineApp& app);
    ~EffectComposer();

    void add_pass(std::shared_ptr<PostProcessPass> pass);
    void remove_pass(std::shared_ptr<PostProcessPass> pass);
    void clear_passes();
    const std::vector<std::shared_ptr<PostProcessPass>>& passes() const { return passes_; }

    void render(Scene& scene, Camera& camera);
    void render_passes(EngineApp& app, Scene& scene, Camera& camera);
    void blit_to_swapchain(RenderTarget& source);

    RenderTarget* hdr_target() { return hdr_target_.get(); }
    RenderTarget* final_target() { return final_target_; }

    void set_app(EngineApp* app) { app_ = app; }
    EngineApp* app() const { return app_; }

    bool enabled{true};
    void resize(int width, int height);
    void destroy();

private:
    void init_resources();

    int width_{800};
    int height_{600};
    EngineApp* app_{nullptr};

    std::unique_ptr<RenderTarget> hdr_target_{nullptr};
    std::unique_ptr<RenderTarget> ping_pong_[2];
    RenderTarget* final_target_{nullptr};

    std::vector<std::shared_ptr<PostProcessPass>> passes_;

    // Fullscreen quad resources
    uint32_t quad_vbuf_id_{0};
    uint32_t quad_ibuf_id_{0};

    // Swapchain blit pipeline
    uint32_t blit_pip_id_{0};
    uint32_t blit_shd_id_{0};
    void init_blit_pipeline();
};

} // namespace engine
