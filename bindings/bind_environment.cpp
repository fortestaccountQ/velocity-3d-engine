#include "bind_common.hpp"
#include "engine/node3d.hpp"
#include "engine/cube_texture.hpp"
#include "engine/sky.hpp"
#include "engine/cube_camera.hpp"
#include "engine/app.hpp"
#include "engine/scene.hpp"
#include "contracts/phase4_environment_contracts.h"

void bind_environment(nb::module_& m) {
    // -----------------------------------------------------------------------
    // CubeTexture (Phase 4.1)
    // -----------------------------------------------------------------------
    nb::class_<engine::CubeTexture>(m, "CubeTexture")
        .def(nb::init<>())
        .def_static("load_from_files", &engine::CubeTexture::load_from_files,
            "right"_a, "left"_a, "top"_a, "bottom"_a, "front"_a, "back"_a)
        .def_static("load_from_hdr", &engine::CubeTexture::load_from_hdr,
            "filepath"_a, "cube_size"_a = 512)
        .def_static("create_default", &engine::CubeTexture::create_default, "resolution"_a = 256)
        .def_static("create_gradient", &engine::CubeTexture::create_gradient,
            "top_color"_a = glm::vec3(0.25f, 0.55f, 0.95f),
            "horizon_color"_a = glm::vec3(0.7f, 0.8f, 0.95f),
            "bottom_color"_a = glm::vec3(0.2f, 0.22f, 0.25f),
            "size"_a = 256)
        .def_ro("size", &engine::CubeTexture::size)
        .def("is_valid", &engine::CubeTexture::is_valid)
        .def_prop_ro("is_valid_prop", &engine::CubeTexture::is_valid)
        .def("destroy", &engine::CubeTexture::destroy)
        .def("__call__", [](std::shared_ptr<engine::CubeTexture> self) { return self; });

    // -----------------------------------------------------------------------
    // Phase 4 Environment Enums & Structs
    // -----------------------------------------------------------------------
    nb::enum_<engine::BackgroundType>(m, "BackgroundType")
        .value("Color", engine::BackgroundType::Color)
        .value("Texture2D", engine::BackgroundType::Texture2D)
        .value("CubeMap", engine::BackgroundType::CubeMap)
        .value("ProceduralSky", engine::BackgroundType::ProceduralSky)
        .export_values();

    nb::class_<engine::ShadowSettings>(m, "ShadowSettings")
        .def(nb::init<>())
        .def_rw("resolution", &engine::ShadowSettings::resolution)
        .def_rw("bias", &engine::ShadowSettings::bias)
        .def_rw("normal_bias", &engine::ShadowSettings::normal_bias)
        .def_rw("ortho_size", &engine::ShadowSettings::ortho_size)
        .def_rw("near_z", &engine::ShadowSettings::near_z)
        .def_rw("far_z", &engine::ShadowSettings::far_z)
        .def_rw("texel_snapping", &engine::ShadowSettings::texel_snapping)
        .def_rw("pcf_16_tap", &engine::ShadowSettings::pcf_16_tap);

    nb::class_<engine::SkyParams>(m, "SkyParams")
        .def(nb::init<>())
        .def_prop_rw("sun_direction",
            [](engine::SkyParams& p) -> glm::vec3& { return p.sun_direction; },
            [](engine::SkyParams& p, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) p.sun_direction = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto s = nb::cast<std::vector<float>>(val);
                    if (s.size() >= 3) p.sun_direction = { s[0], s[1], s[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("rayleigh_color",
            [](engine::SkyParams& p) -> glm::vec3& { return p.rayleigh_color; },
            [](engine::SkyParams& p, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) p.rayleigh_color = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto s = nb::cast<std::vector<float>>(val);
                    if (s.size() >= 3) p.rayleigh_color = { s[0], s[1], s[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("mie_color",
            [](engine::SkyParams& p) -> glm::vec3& { return p.mie_color; },
            [](engine::SkyParams& p, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) p.mie_color = nb::cast<glm::vec3>(val);
                else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto s = nb::cast<std::vector<float>>(val);
                    if (s.size() >= 3) p.mie_color = { s[0], s[1], s[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("turbidity", &engine::SkyParams::turbidity)
        .def_rw("rayleigh", &engine::SkyParams::rayleigh)
        .def_rw("mie_coefficient", &engine::SkyParams::mie_coefficient)
        .def_rw("mie_directional_g", &engine::SkyParams::mie_directional_g)
        .def_rw("time_of_day", &engine::SkyParams::time_of_day);

    nb::class_<engine::ProceduralSky, engine::Node3D>(m, "ProceduralSky")
        .def(nb::init<>())
        .def(nb::init<const std::string&>(), "name"_a = "ProceduralSky")
        .def_rw("params", &engine::ProceduralSky::params)
        .def_prop_rw("sun_direction",
            &engine::ProceduralSky::sun_direction,
            [](engine::ProceduralSky& s, const glm::vec3& v) { s.set_sun_direction(v); })
        .def_prop_rw("rayleigh_color",
            &engine::ProceduralSky::rayleigh_color,
            [](engine::ProceduralSky& s, const glm::vec3& v) { s.set_rayleigh_color(v); })
        .def_prop_rw("mie_color",
            &engine::ProceduralSky::mie_color,
            [](engine::ProceduralSky& s, const glm::vec3& v) { s.set_mie_color(v); })
        .def_prop_rw("turbidity", &engine::ProceduralSky::turbidity, &engine::ProceduralSky::set_turbidity)
        .def_prop_rw("rayleigh", &engine::ProceduralSky::rayleigh, &engine::ProceduralSky::set_rayleigh)
        .def_prop_rw("mie_coefficient", &engine::ProceduralSky::mie_coefficient, &engine::ProceduralSky::set_mie_coefficient)
        .def_prop_rw("mie_directional_g", &engine::ProceduralSky::mie_directional_g, &engine::ProceduralSky::set_mie_directional_g)
        .def_prop_rw("time_of_day", &engine::ProceduralSky::time_of_day, &engine::ProceduralSky::set_time_of_day)
        .def("set_sun_direction", [](engine::ProceduralSky& s, float x, float y, float z) {
            s.set_sun_direction(x, y, z);
        }, "x"_a, "y"_a, "z"_a)
        .def("set_rayleigh_color", [](engine::ProceduralSky& s, float r, float g, float b) {
            s.set_rayleigh_color(r, g, b);
        }, "r"_a, "g"_a, "b"_a)
        .def("set_mie_color", [](engine::ProceduralSky& s, float r, float g, float b) {
            s.set_mie_color(r, g, b);
        }, "r"_a, "g"_a, "b"_a)
        .def("set_turbidity", &engine::ProceduralSky::set_turbidity, "val"_a)
        .def("set_rayleigh", &engine::ProceduralSky::set_rayleigh, "val"_a)
        .def("set_mie_coefficient", &engine::ProceduralSky::set_mie_coefficient, "val"_a)
        .def("set_mie_directional_g", &engine::ProceduralSky::set_mie_directional_g, "val"_a)
        .def("set_time_of_day", &engine::ProceduralSky::set_time_of_day, "hours"_a);

    nb::class_<engine::CubeRenderTarget>(m, "CubeRenderTarget")
        .def(nb::init<int>(), "resolution"_a = 256)
        .def_prop_ro("resolution", &engine::CubeRenderTarget::resolution)
        .def_prop_ro("cube_texture", &engine::CubeRenderTarget::cube_texture)
        .def("destroy", &engine::CubeRenderTarget::destroy);

    nb::class_<engine::CubeCamera, engine::Node3D>(m, "CubeCamera")
        .def(nb::init<float, float, int>(), "near_p"_a = 0.1f, "far_p"_a = 100.0f, "resolution"_a = 256)
        .def_prop_rw("near_plane", &engine::CubeCamera::near_plane, &engine::CubeCamera::set_near_plane)
        .def_prop_rw("far_plane", &engine::CubeCamera::far_plane, &engine::CubeCamera::set_far_plane)
        .def("set_near_plane", &engine::CubeCamera::set_near_plane, "near_p"_a)
        .def("set_far_plane", &engine::CubeCamera::set_far_plane, "far_p"_a)
        .def_prop_ro("resolution", &engine::CubeCamera::resolution)
        .def_prop_ro("render_target", &engine::CubeCamera::render_target)
        .def_prop_ro("cube_texture", &engine::CubeCamera::cube_texture)
        .def("update", &engine::CubeCamera::update, "app"_a, "scene"_a);
}
