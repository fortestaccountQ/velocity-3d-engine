#include "bind_common.hpp"

NB_MODULE(_VelocityEngine_core, m) {
    m.doc() = "Pielosyty / VelocityEngine Core";
    bind_math(m);
    bind_materials(m);
    bind_scene(m);
    bind_geometry(m);
    bind_environment(m);
    bind_postprocess(m);
    bind_app(m);
}
