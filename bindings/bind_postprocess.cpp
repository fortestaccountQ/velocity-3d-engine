#include "bind_common.hpp"
#include "engine/render_target.hpp"
#include "engine/post_process.hpp"
#include "engine/app.hpp"
#include "engine/scene.hpp"
#include "engine/camera.hpp"

void bind_postprocess(nb::module_& m) {
    // -----------------------------------------------------------------------
    // RenderTarget
    // -----------------------------------------------------------------------
    nb::enum_<engine::RenderTargetFormat>(m, "RenderTargetFormat")
        .value("RGBA8", engine::RenderTargetFormat::RGBA8)
        .value("RGBA16F", engine::RenderTargetFormat::RGBA16F)
        .value("R32F", engine::RenderTargetFormat::R32F)
        .export_values();

    nb::class_<engine::RenderTarget>(m, "RenderTarget")
        .def(nb::init<int, int, engine::RenderTargetFormat, bool, int>(),
             "width"_a, "height"_a, "format"_a = engine::RenderTargetFormat::RGBA8,
             "has_depth"_a = true, "samples"_a = 1)
        .def("resize", &engine::RenderTarget::resize, "width"_a, "height"_a)
        .def("destroy", &engine::RenderTarget::destroy)
        .def_prop_ro("width", &engine::RenderTarget::width)
        .def_prop_ro("height", &engine::RenderTarget::height)
        .def_prop_ro("format", &engine::RenderTarget::format)
        .def_prop_ro("has_depth", &engine::RenderTarget::has_depth)
        .def_prop_ro("samples", &engine::RenderTarget::samples)
        .def_prop_ro("color_image_id", &engine::RenderTarget::color_image_id)
        .def_prop_ro("color_view_id", &engine::RenderTarget::color_view_id)
        .def_prop_ro("depth_image_id", &engine::RenderTarget::depth_image_id)
        .def_prop_ro("depth_view_id", &engine::RenderTarget::depth_view_id)
        .def_prop_ro("depth_tex_view_id", &engine::RenderTarget::depth_tex_view_id)
        .def_prop_ro("tex_view_id", &engine::RenderTarget::tex_view_id)
        .def_prop_ro("sampler_id", &engine::RenderTarget::sampler_id)
        .def("is_valid", [](const engine::RenderTarget& rt) { return rt.color_view_id() != 0; })
        .def_prop_ro("texture", &engine::RenderTarget::texture)
        .def("read_pixels", [](engine::RenderTarget& rt) {
            auto pixels = rt.read_pixels();
            return nb::bytes(pixels.data(), pixels.size());
        })
        .def("read_depth_pixels", [](engine::RenderTarget& rt) {
            return rt.read_depth_pixels();
        });

    // -----------------------------------------------------------------------
    // Post-Processing & EffectComposer
    // -----------------------------------------------------------------------
    nb::enum_<engine::TonemappingMode>(m, "TonemappingMode")
        .value("ACESFilmic", engine::TonemappingMode::ACESFilmic)
        .value("Reinhard", engine::TonemappingMode::Reinhard)
        .value("Cineon", engine::TonemappingMode::Cineon)
        .value("Linear", engine::TonemappingMode::Linear)
        .value("Neutral", engine::TonemappingMode::Neutral)
        .export_values();

    nb::class_<engine::PostProcessPass>(m, "PostProcessPass")
        .def_rw("enabled", &engine::PostProcessPass::enabled)
        .def_prop_ro("name", &engine::PostProcessPass::name);

    nb::class_<engine::BloomPass, engine::PostProcessPass>(m, "BloomPass")
        .def(nb::init<float, float, float>(),
             "threshold"_a = 1.0f, "strength"_a = 1.5f, "radius"_a = 0.5f)
        .def_rw("threshold", &engine::BloomPass::threshold)
        .def_rw("strength", &engine::BloomPass::strength)
        .def_rw("radius", &engine::BloomPass::radius);

    nb::class_<engine::SSAOPass, engine::PostProcessPass>(m, "SSAOPass")
        .def(nb::init<float, float, float>(),
             "radius"_a = 0.5f, "bias"_a = 0.025f, "power"_a = 1.0f)
        .def_rw("radius", &engine::SSAOPass::radius)
        .def_rw("bias", &engine::SSAOPass::bias)
        .def_rw("power", &engine::SSAOPass::power);

    nb::class_<engine::FXAAPass, engine::PostProcessPass>(m, "FXAAPass")
        .def(nb::init<>());

    nb::class_<engine::TonemappingPass, engine::PostProcessPass>(m, "TonemappingPass")
        .def(nb::init<engine::TonemappingMode, float, float>(),
             "mode"_a = engine::TonemappingMode::ACESFilmic, "exposure"_a = 1.0f, "gamma"_a = 2.2f)
        .def_rw("mode", &engine::TonemappingPass::mode)
        .def_rw("exposure", &engine::TonemappingPass::exposure)
        .def_rw("gamma", &engine::TonemappingPass::gamma);

    nb::class_<engine::VignetteChromaticPass, engine::PostProcessPass>(m, "VignetteChromaticPass")
        .def(nb::init<float, float, float>(),
             "vignette"_a = 0.3f, "chromatic"_a = 0.005f, "grain"_a = 0.02f)
        .def_rw("vignette", &engine::VignetteChromaticPass::vignette)
        .def_rw("chromatic", &engine::VignetteChromaticPass::chromatic)
        .def_rw("grain", &engine::VignetteChromaticPass::grain)
        .def_rw("time", &engine::VignetteChromaticPass::time);

    nb::class_<engine::ColorGradingPass, engine::PostProcessPass>(m, "ColorGradingPass")
        .def(nb::init<float, float, float>(),
             "contrast"_a = 1.0f, "saturation"_a = 1.0f, "brightness"_a = 1.0f)
        .def_rw("contrast", &engine::ColorGradingPass::contrast)
        .def_rw("saturation", &engine::ColorGradingPass::saturation)
        .def_rw("brightness", &engine::ColorGradingPass::brightness);

    nb::class_<engine::EffectComposer>(m, "EffectComposer")
        .def(nb::init<>())
        .def(nb::init<int, int>(), "width"_a, "height"_a)
        .def(nb::init<engine::EngineApp&>(), "app"_a)
        .def("add_pass", &engine::EffectComposer::add_pass, "pass"_a)
        .def("remove_pass", &engine::EffectComposer::remove_pass, "pass"_a)
        .def("clear_passes", &engine::EffectComposer::clear_passes)
        .def("resize", &engine::EffectComposer::resize, "width"_a, "height"_a)
        .def_rw("enabled", &engine::EffectComposer::enabled)
        .def_prop_ro("passes", &engine::EffectComposer::passes)
        .def("render", &engine::EffectComposer::render, "scene"_a, "camera"_a)
        .def_prop_ro("hdr_target", &engine::EffectComposer::hdr_target, nb::rv_policy::reference_internal);
}
