// Sokol implementation translation unit
#ifndef SOKOL_IMPL
#define SOKOL_IMPL
#endif

#ifndef SOKOL_NO_ENTRY
#define SOKOL_NO_ENTRY
#endif

#include "sokol_app.h"
#include "sokol_gfx.h"
#include "sokol_log.h"
#include "sokol_glue.h"

#include "imgui.h"
#ifndef SOKOL_IMGUI_IMPL
#define SOKOL_IMGUI_IMPL
#endif
#include "util/sokol_imgui.h"

extern "C" void sapp_set_swap_interval(int interval) {
    _sapp.desc.swap_interval = interval;
    _sapp.desc.disable_vsync = (interval == 0);
}

