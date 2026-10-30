"""Example 05: Custom Shader Water with Sine Wave Displacement & Fresnel.

Showcase:
- Water plane driven by `ShaderMaterial` with custom vertex & fragment shaders.
- Vertex shader: Multi-frequency sine wave height displacement based on `u_time`.
- Fragment shader: Deep ocean absorption, shallow cyan transmission, Fresnel reflection, and sun specular highlights.
- Dynamic floating props (buoys & duck) bobbing realistically on the waves.
- Standalone execution and headless/test suite support.
"""

from __future__ import annotations
import sys
import math
from pathlib import Path
from typing import Optional

# Ensure package import
repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

import VelocityEngine as ve
from VelocityEngine import (
    App,
    OrbitController,
    Mesh,
    ShaderMaterial,
    StandardMaterial,
    CubeTexture,
    Vec3,
    Vec4,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
)

WATER_VERTEX_SHADER = """
// Water Vertex Shader: Displaces vertices with compounding waves
cbuffer WaterUniforms : register(b0) {
    float4 u_time;          // x = time, y = freq, z = amp, w = unused
    float4 u_sun_dir;       // xyz = sun direction, w = specular exponent
    float4 u_deep_color;    // deep ocean rgba
    float4 u_shallow_color; // shallow crest rgba
};

struct VS_INPUT {
    float3 position : POSITION;
    float3 normal   : NORMAL;
    float2 uv       : TEXCOORD0;
};

struct VS_OUTPUT {
    float4 position : SV_POSITION;
    float3 world_pos : TEXCOORD1;
    float3 normal   : NORMAL;
    float2 uv       : TEXCOORD0;
};

VS_OUTPUT main_vs(VS_INPUT input) {
    VS_OUTPUT output;
    float t = u_time.x;
    float freq = u_time.y;
    float amp = u_time.z;

    float3 pos = input.position;
    // Compounding sine waves
    float wave1 = sin(pos.x * freq + t * 2.0) * cos(pos.z * freq + t * 1.5) * amp;
    float wave2 = sin(pos.x * (freq * 2.2) - t * 3.0) * cos(pos.z * (freq * 1.8) + t * 2.5) * (amp * 0.4);
    pos.y += wave1 + wave2;

    output.world_pos = pos;
    output.position = float4(pos, 1.0);
    output.uv = input.uv;
    output.normal = normalize(float3(-cos(pos.x * freq + t) * amp, 1.0, -sin(pos.z * freq + t) * amp));
    return output;
}
"""

WATER_FRAGMENT_SHADER = """
// Water Fragment Shader: Deep ocean color, sun specular, and Fresnel transparency
cbuffer WaterUniforms : register(b0) {
    float4 u_time;
    float4 u_sun_dir;
    float4 u_deep_color;
    float4 u_shallow_color;
};

float4 main_fs(float3 world_pos : TEXCOORD1, float3 normal : NORMAL, float2 uv : TEXCOORD0) : SV_TARGET {
    float3 N = normalize(normal);
    float3 L = normalize(u_sun_dir.xyz);
    float3 V = normalize(-world_pos);

    // Fresnel reflectance factor: (1 - dot(N, V))^4
    float NdotV = max(0.0, dot(N, V));
    float fresnel = pow(1.0 - NdotV, 4.0);

    // Specular highlight from directional sun
    float3 H = normalize(L + V);
    float NdotH = max(0.0, dot(N, H));
    float specular = pow(NdotH, u_sun_dir.w);

    // Blend between deep oceanic water and shallow turquoise crests
    float4 base_col = lerp(u_deep_color, u_shallow_color, fresnel);
    base_col.rgb += specular * float3(1.0, 0.95, 0.85);

    return saturate(base_col);
}
"""


def create_water_scene(app: App) -> tuple[ve.Entity, list[ve.Entity], ShaderMaterial]:
    """Assemble water surface, sky reflections, and decorative floating objects."""
    scene = app.scene

    # Lighting & Sky
    scene.set_sun(direction=(-0.6, -1.8, -0.5), color=WARM_WHITE, intensity=1.6)
    sky = CubeTexture.create_gradient(
        top_color=Vec3(0.1, 0.4, 0.8),
        horizon_color=Vec3(0.7, 0.85, 0.95),
        bottom_color=Vec3(0.02, 0.08, 0.15),
        size=64,
    )
    scene.set_environment(sky, 1.5)
    scene.set_background_cube(sky)

    # 1. Custom ShaderMaterial Water Plane
    water_mesh = Mesh.create_plane(width=60.0, depth=60.0, subdivisions_x=64, subdivisions_z=64)
    water_mat = ShaderMaterial(WATER_VERTEX_SHADER, WATER_FRAGMENT_SHADER)
    water_mat.uniforms = {
        "u_time": Vec4(0.0, 0.35, 1.2, 0.0),
        "u_sun_dir": Vec4(-0.6, 1.8, -0.5, 64.0),
        "u_deep_color": Vec4(0.02, 0.12, 0.28, 0.92),
        "u_shallow_color": Vec4(0.15, 0.70, 0.88, 0.75),
    }
    # Set fallback standard properties in case native driver uses PBR pass
    water_mat.base_color = (0.05, 0.35, 0.65, 0.85)
    water_mat.roughness = 0.08
    water_mat.metallic = 0.2

    water_entity = scene.create_entity("ShaderWaterPlane")
    water_entity.mesh = water_mesh
    water_entity.material = water_mat
    water_entity.transform.position = (0.0, 0.0, 0.0)

    # 2. Decorative Floating Buoys bobbing on waves
    buoys: list[ve.Entity] = []
    buoy_mesh = Mesh.create_cylinder(radius=0.7, height=1.6, segments=24)
    buoy_mat = StandardMaterial()
    buoy_mat.base_color = (0.95, 0.2, 0.1, 1.0) # Safety orange
    buoy_mat.roughness = 0.3
    buoy_mat.metallic = 0.5

    positions = [(-10.0, -8.0), (12.0, -6.0), (0.0, 10.0), (-12.0, 10.0)]
    for idx, (bx, bz) in enumerate(positions):
        b = scene.create_entity(f"FloatingBuoy_{idx}")
        b.mesh = buoy_mesh
        b.material = buoy_mat
        b.transform.position = (bx, 0.0, bz)
        buoys.append(b)

    # Floating Duck in center
    duck_path = repo_root / "assets" / "duck.glb"
    if duck_path.exists():
        duck_model = scene.load_model(str(duck_path))
        if duck_model and duck_model.root_entity:
            duck_model.root_entity.transform.scale = (1.5, 1.5, 1.5)
            buoys.append(duck_model.root_entity)

    return water_entity, buoys, water_mat


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the custom shader water example in interactive or headless mode."""
    app = App("Velocity - 05 Custom Shader Water", width=1280, height=720, clear_color="#07121e")

    # Camera looking over the ocean
    orb = OrbitController(target=(0.0, 0.0, 0.0), distance=26.0, min_distance=4.0, max_distance=70.0, pitch=25.0)
    app.camera = orb

    water_entity, buoys, water_mat = create_water_scene(app)

    # UI Overlay setup
    app.ui.clear()
    app.ui.draw_text("Velocity 3D Engine | 05: Custom Shader Water", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("ShaderMaterial: Custom Vertex (Sine Wave Displacement) & Fragment (Fresnel + Specular)", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("Realistic Wave Kinematics & Floating Buoy Bobbing Dynamics", (24, 76), size=13, color=WHITE)
    app.ui.show_stats(True)

    time_accum = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        # Update shader uniform time parameter
        water_mat.uniforms["u_time"] = Vec4(time_accum, 0.35, 1.2, 0.0)

        # Bobbing physics for floating buoys
        for idx, buoy in enumerate(buoys):
            bp = buoy.transform.position
            # Evaluate water height at buoy location
            w1 = math.sin(bp.x * 0.35 + time_accum * 2.0) * math.cos(bp.z * 0.35 + time_accum * 1.5) * 1.2
            w2 = math.sin(bp.x * 0.77 - time_accum * 3.0) * math.cos(bp.z * 0.63 + time_accum * 2.5) * 0.48
            water_y = w1 + w2

            buoy.transform.position = (bp.x, water_y + 0.3, bp.z)
            # Tilt with wave slope
            tilt_x = math.cos(bp.z * 0.35 + time_accum * 1.5) * 12.0
            tilt_z = math.sin(bp.x * 0.35 + time_accum * 2.0) * 12.0
            buoy.transform.rotation = (tilt_x, idx * 30.0 + time_accum * 10.0, tilt_z)

        if (headless or "--test" in sys.argv or "--headless" in sys.argv) and frame_counter >= frames:
            app.close()

    app.on_update(update)

    if not headless and "--headless" not in sys.argv:
        app.run()
    else:
        for _ in range(frames):
            update(1.0 / 60.0)

    return app


if __name__ == "__main__":
    is_headless = "--headless" in sys.argv
    frame_limit = 60
    for idx, arg in enumerate(sys.argv):
        if arg == "--frames" and idx + 1 < len(sys.argv):
            try:
                frame_limit = int(sys.argv[idx + 1])
            except ValueError:
                pass

    run_example(headless=is_headless, frames=frame_limit)
