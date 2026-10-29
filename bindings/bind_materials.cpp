#include "bind_common.hpp"
#include "engine/texture.hpp"
#include "engine/material.hpp"
#include "engine/render_target.hpp"

void bind_materials(nb::module_& m) {
    // -----------------------------------------------------------------------
    // Texture
    // -----------------------------------------------------------------------
    nb::class_<engine::Texture>(m, "Texture")
        .def(nb::init<>())
        .def_static("load_from_file", [](const std::string& filepath, bool is_pixel_art) {
            return engine::Texture::load_from_file(filepath, is_pixel_art);
        }, "filepath"_a, "is_pixel_art"_a = false)
        .def_static("create_from_rgba", [](int width, int height, const nb::bytes& data, bool is_pixel_art) {
            return engine::Texture::create_from_rgba(
                width,
                height,
                reinterpret_cast<const uint8_t*>(data.data()),
                is_pixel_art
            );
        }, "width"_a, "height"_a, "data"_a, "is_pixel_art"_a = false)
        .def_static("create_data_texture", [](int width, int height, const nb::bytes& data, int channels) {
            return engine::Texture::create_data_texture(
                width,
                height,
                reinterpret_cast<const uint8_t*>(data.data()),
                channels
            );
        }, "width"_a, "height"_a, "data"_a, "channels"_a = 4)
        .def_static("create_checkerboard", &engine::Texture::create_checkerboard,
            "width"_a = 64, "height"_a = 64, "tile_size"_a = 8,
            "color1"_a = 0xFFFFFFFF, "color2"_a = 0xFF2A2A38)
        .def_static("create_solid_color", &engine::Texture::create_solid_color,
            "r"_a, "g"_a, "b"_a, "a"_a = 255)
        .def_ro("width", &engine::Texture::width)
        .def_ro("height", &engine::Texture::height)
        .def_ro("channels", &engine::Texture::channels)
        .def_rw("is_pixel_art", &engine::Texture::is_pixel_art)
        .def_rw("wrap_s", &engine::Texture::wrap_s)
        .def_rw("wrap_t", &engine::Texture::wrap_t)
        .def_rw("filter_min", &engine::Texture::filter_min)
        .def_rw("filter_mag", &engine::Texture::filter_mag)
        .def("is_valid", &engine::Texture::is_valid)
        .def("__call__", [](std::shared_ptr<engine::Texture> self) { return self; });

    // -----------------------------------------------------------------------
    // Material Enums
    // -----------------------------------------------------------------------
    nb::enum_<engine::SideMode>(m, "SideMode")
        .value("Front", engine::SideMode::Front)
        .value("Back", engine::SideMode::Back)
        .value("Double", engine::SideMode::Double)
        .export_values();

    nb::enum_<engine::BlendMode>(m, "BlendMode")
        .value("Opaque", engine::BlendMode::Opaque)
        .value("Alpha", engine::BlendMode::Alpha)
        .value("Additive", engine::BlendMode::Additive)
        .value("Multiply", engine::BlendMode::Multiply)
        .export_values();

    nb::enum_<engine::TextureFilter>(m, "TextureFilter")
        .value("Nearest", engine::TextureFilter::Nearest)
        .value("Linear", engine::TextureFilter::Linear)
        .export_values();

    nb::enum_<engine::TextureWrap>(m, "TextureWrap")
        .value("Repeat", engine::TextureWrap::Repeat)
        .value("ClampToEdge", engine::TextureWrap::ClampToEdge)
        .value("MirroredRepeat", engine::TextureWrap::MirroredRepeat)
        .export_values();

    nb::enum_<engine::MaterialType>(m, "MaterialType")
        .value("Standard", engine::MaterialType::Standard)
        .value("Physical", engine::MaterialType::Physical)
        .value("Unlit", engine::MaterialType::Unlit)
        .value("Lambert", engine::MaterialType::Lambert)
        .value("Phong", engine::MaterialType::Phong)
        .value("Toon", engine::MaterialType::Toon)
        .value("CustomShader", engine::MaterialType::CustomShader)
        .value("PBR", engine::MaterialType::PBR)
        .export_values();

    // -----------------------------------------------------------------------
    // Material Hierarchy
    // -----------------------------------------------------------------------
    nb::class_<engine::Material>(m, "Material")
        .def(nb::init<>())
        .def(nb::init<std::shared_ptr<engine::Texture>, float, float>(),
            "texture"_a = nullptr, "roughness"_a = 0.5f, "metallic"_a = 0.0f)
        .def_prop_ro("type", &engine::Material::type)
        .def_rw("transparent", &engine::Material::transparent)
        .def_rw("opacity", &engine::Material::opacity)
        .def_rw("depth_write", &engine::Material::depth_write)
        .def_rw("depth_test", &engine::Material::depth_test)
        .def_rw("wireframe", &engine::Material::wireframe)
        .def_rw("side", &engine::Material::side)
        .def_rw("blend_mode", &engine::Material::blend_mode)
        .def_prop_rw("albedo_map",
            [](engine::Material& mat) { return mat.albedo_map; },
            [](engine::Material& mat, nb::handle obj) {
                if (obj.is_none()) { mat.albedo_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { mat.albedo_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { mat.albedo_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
                else if (nb::hasattr(obj, "texture")) {
                    auto tex = obj.attr("texture");
                    if (nb::isinstance<engine::Texture>(tex)) mat.albedo_map = nb::cast<std::shared_ptr<engine::Texture>>(tex);
                    else if (PyCallable_Check(tex.ptr())) {
                        auto res = tex();
                        if (nb::isinstance<engine::Texture>(res)) mat.albedo_map = nb::cast<std::shared_ptr<engine::Texture>>(res);
                    }
                }
            })
        .def_prop_rw("normal_map",
            [](engine::Material& mat) { return mat.normal_map; },
            [](engine::Material& mat, nb::handle obj) {
                if (obj.is_none()) { mat.normal_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { mat.normal_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { mat.normal_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_prop_rw("metallic_roughness_map",
            [](engine::Material& mat) { return mat.metallic_roughness_map; },
            [](engine::Material& mat, nb::handle obj) {
                if (obj.is_none()) { mat.metallic_roughness_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { mat.metallic_roughness_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { mat.metallic_roughness_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_prop_rw("occlusion_map",
            [](engine::Material& mat) { return mat.occlusion_map; },
            [](engine::Material& mat, nb::handle obj) {
                if (obj.is_none()) { mat.occlusion_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { mat.occlusion_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { mat.occlusion_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_prop_rw("ao_map",
            [](engine::Material& mat) { return mat.ao_map; },
            [](engine::Material& mat, nb::handle obj) {
                if (obj.is_none()) { mat.ao_map = nullptr; mat.occlusion_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { mat.ao_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); mat.occlusion_map = mat.ao_map; }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { mat.ao_map = nb::cast<engine::RenderTarget&>(obj).texture(); mat.occlusion_map = mat.ao_map; }
            })
        .def_prop_rw("emissive_map",
            [](engine::Material& mat) { return mat.emissive_map; },
            [](engine::Material& mat, nb::handle obj) {
                if (obj.is_none()) { mat.emissive_map = nullptr; }
                else if (nb::isinstance<engine::Texture>(obj)) { mat.emissive_map = nb::cast<std::shared_ptr<engine::Texture>>(obj); }
                else if (nb::isinstance<engine::RenderTarget>(obj)) { mat.emissive_map = nb::cast<engine::RenderTarget&>(obj).texture(); }
            })
        .def_rw("normal_scale", &engine::Material::normal_scale)
        .def_rw("ao_intensity", &engine::Material::ao_intensity)
        .def_rw("alpha_test", &engine::Material::alpha_test)
        .def_rw("alpha_cutoff", &engine::Material::alpha_cutoff)
        .def_prop_rw("emissive_color",
            [](engine::Material& mat) -> glm::vec3& { return mat.emissive_color; },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    mat.emissive_color = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) mat.emissive_color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("emissive_intensity", &engine::Material::emissive_intensity)
        .def_rw("roughness", &engine::Material::roughness)
        .def_rw("metallic", &engine::Material::metallic)
        .def_prop_rw("base_color",
            [](engine::Material& mat) -> glm::vec4& { return mat.base_color; },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec4>(val)) {
                    mat.base_color = nb::cast<glm::vec4>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 4) mat.base_color = { seq[0], seq[1], seq[2], seq[3] };
                    else if (seq.size() == 3) mat.base_color = { seq[0], seq[1], seq[2], 1.0f };
                }
            }, nb::rv_policy::reference_internal)
        .def_prop_rw("uv_scale",
            [](engine::Material& mat) -> std::pair<float, float> {
                return { mat.uv_scale.x, mat.uv_scale.y };
            },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 2) mat.uv_scale = { seq[0], seq[1] };
                }
            })
        .def_prop_rw("uv_offset",
            [](engine::Material& mat) -> std::pair<float, float> {
                return { mat.uv_offset.x, mat.uv_offset.y };
            },
            [](engine::Material& mat, const nb::object& val) {
                if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 2) mat.uv_offset = { seq[0], seq[1] };
                }
            })
        .def("set_color", &engine::Material::set_color, "r"_a, "g"_a, "b"_a, "a"_a = 1.0f)
        .def("set_uv_scale", &engine::Material::set_uv_scale, "u"_a, "v"_a)
        .def("set_uv_offset", &engine::Material::set_uv_offset, "u"_a, "v"_a);

    nb::class_<engine::StandardMaterial, engine::Material>(m, "StandardMaterial")
        .def(nb::init<>())
        .def(nb::init<std::shared_ptr<engine::Texture>, float, float>(),
            "texture"_a = nullptr, "roughness"_a = 0.5f, "metallic"_a = 0.0f);

    nb::class_<engine::PhysicalMaterial, engine::StandardMaterial>(m, "PhysicalMaterial")
        .def(nb::init<>())
        .def_rw("clearcoat", &engine::PhysicalMaterial::clearcoat)
        .def_rw("clearcoat_roughness", &engine::PhysicalMaterial::clearcoat_roughness)
        .def_rw("transmission", &engine::PhysicalMaterial::transmission)
        .def_rw("ior", &engine::PhysicalMaterial::ior)
        .def_prop_rw("sheen",
            [](engine::PhysicalMaterial& mat) -> glm::vec3& { return mat.sheen; },
            [](engine::PhysicalMaterial& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    mat.sheen = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) mat.sheen = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal)
        .def_rw("sheen_roughness", &engine::PhysicalMaterial::sheen_roughness);

    nb::class_<engine::UnlitMaterial, engine::Material>(m, "UnlitMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>, bool>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr, "wireframe"_a = false);

    nb::class_<engine::LambertMaterial, engine::Material>(m, "LambertMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr);

    nb::class_<engine::PhongMaterial, engine::Material>(m, "PhongMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>, float>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr, "shininess"_a = 30.0f)
        .def_rw("shininess", &engine::PhongMaterial::shininess)
        .def_prop_rw("specular_color",
            [](engine::PhongMaterial& mat) -> glm::vec3& { return mat.specular_color; },
            [](engine::PhongMaterial& mat, const nb::object& val) {
                if (nb::isinstance<glm::vec3>(val)) {
                    mat.specular_color = nb::cast<glm::vec3>(val);
                } else if (nb::isinstance<nb::tuple>(val) || nb::isinstance<nb::list>(val)) {
                    auto seq = nb::cast<std::vector<float>>(val);
                    if (seq.size() >= 3) mat.specular_color = { seq[0], seq[1], seq[2] };
                }
            }, nb::rv_policy::reference_internal);

    nb::class_<engine::ToonMaterial, engine::Material>(m, "ToonMaterial")
        .def(nb::init<>())
        .def(nb::init<const glm::vec4&, std::shared_ptr<engine::Texture>, int>(),
            "color"_a = glm::vec4(1.0f), "map"_a = nullptr, "steps"_a = 3)
        .def_rw("steps", &engine::ToonMaterial::steps)
        .def_rw("num_steps", &engine::ToonMaterial::num_steps);

    nb::class_<engine::ShaderMaterial, engine::Material>(m, "ShaderMaterial")
        .def(nb::init<>())
        .def(nb::init<std::string, std::string>(), "vertex_shader"_a = "", "fragment_shader"_a = "")
        .def_rw("vertex_shader", &engine::ShaderMaterial::vertex_shader)
        .def_rw("fragment_shader", &engine::ShaderMaterial::fragment_shader)
        .def_rw("uniforms", &engine::ShaderMaterial::uniforms);

    // -----------------------------------------------------------------------
    // PipelineManager
    // -----------------------------------------------------------------------
    nb::class_<engine::PipelineManager>(m, "PipelineManager")
        .def_static("instance", &engine::PipelineManager::instance, nb::rv_policy::reference)
        .def("release_all", &engine::PipelineManager::release_all);
}
