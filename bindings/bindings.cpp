#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>

#include "engine/app.hpp"

namespace nb = nanobind;
using namespace nb::literals;

NB_MODULE(_engine_core, m) {
    m.doc() = "Native C++20 3D Engine Core with Sokol, GLM, and Nanobind";

    nb::class_<engine::EngineApp>(m, "EngineApp")
        .def(nb::init<>())
        .def(nb::init<const std::string&, int, int>(),
             "title"_a, "width"_a, "height"_a)
        .def("init", &engine::EngineApp::init,
             "title"_a = "Engine 3D Core",
             "width"_a = 800,
             "height"_a = 600,
             "Initialize or update window parameters")
        .def("run", &engine::EngineApp::run,
             nb::call_guard<nb::gil_scoped_release>(),
             "Run main event and rendering loop")
        .def("close", &engine::EngineApp::close,
             "Request engine window termination")
        .def("is_running", &engine::EngineApp::is_running,
             "Check if the application is currently running")

        // Callbacks (supports callable or None)
        .def("set_update_callback", [](engine::EngineApp& self, std::optional<engine::EngineApp::UpdateCallback> cb) {
            if (cb.has_value()) {
                self.set_update_callback(std::move(*cb));
            } else {
                self.set_update_callback(nullptr);
            }
        }, "callback"_a.none() = nb::none(),
           "Register per-frame update callback accepting delta_time (dt), or None to clear")

        // Background color
        .def("set_clear_color", &engine::EngineApp::set_clear_color,
             "r"_a, "g"_a, "b"_a, "a"_a = 1.0f,
             "Set RGBA background clear color")
        .def("get_clear_color", &engine::EngineApp::get_clear_color,
             "Get RGBA background clear color")

        // Transform controls
        .def("set_rotation", &engine::EngineApp::set_rotation,
             "rx"_a, "ry"_a, "rz"_a,
             "Set rotation in degrees for X, Y, Z axes")
        .def("set_position", &engine::EngineApp::set_position,
             "x"_a, "y"_a, "z"_a,
             "Set position coordinates")
        .def("set_scale", &engine::EngineApp::set_scale,
             "sx"_a, "sy"_a, "sz"_a,
             "Set scale factors")

        .def_prop_rw("rotation_x",
            &engine::EngineApp::rotation_x,
            &engine::EngineApp::set_rotation_x)
        .def_prop_rw("rotation_y",
            &engine::EngineApp::rotation_y,
            &engine::EngineApp::set_rotation_y)
        .def_prop_rw("rotation_z",
            &engine::EngineApp::rotation_z,
            &engine::EngineApp::set_rotation_z)

        .def_prop_rw("position_x",
            &engine::EngineApp::position_x,
            &engine::EngineApp::set_position_x)
        .def_prop_rw("position_y",
            &engine::EngineApp::position_y,
            &engine::EngineApp::set_position_y)
        .def_prop_rw("position_z",
            &engine::EngineApp::position_z,
            &engine::EngineApp::set_position_z)

        .def_prop_ro("scale_x", &engine::EngineApp::scale_x)
        .def_prop_ro("scale_y", &engine::EngineApp::scale_y)
        .def_prop_ro("scale_z", &engine::EngineApp::scale_z)

        .def_prop_ro("width", &engine::EngineApp::width)
        .def_prop_ro("height", &engine::EngineApp::height)
        .def_prop_ro("title", &engine::EngineApp::title);
}
