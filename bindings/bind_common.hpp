#pragma once

#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>
#include <nanobind/stl/array.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/shared_ptr.h>
#include <nanobind/stl/function.h>
#include <nanobind/stl/optional.h>
#include <nanobind/stl/tuple.h>
#include <nanobind/stl/pair.h>
#include <nanobind/stl/unordered_map.h>

namespace nb = nanobind;
using namespace nb::literals;

void bind_math(nb::module_& m);
void bind_materials(nb::module_& m);
void bind_geometry(nb::module_& m);
void bind_scene(nb::module_& m);
void bind_environment(nb::module_& m);
void bind_postprocess(nb::module_& m);
void bind_app(nb::module_& m);
