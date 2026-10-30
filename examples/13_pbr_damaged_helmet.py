"""Example 13: PBR Damaged Helmet Showcase with Rich Dynamic Lighting.

Demonstrates:
- Loaded glTF 2.0 DamagedHelmet with full PBR maps:
  * normal_map (surface relief & micro-details)
  * emissive_map (glowing orange HUD elements)
  * metallic_roughness_map (metallic reflections & roughness)
  * ao_map / occlusion_map (crevice shadows)
- Rich Lighting Pipeline:
  * Directional Sunlight with warm white spectrum
  * Hemispheric ambient fill preventing pitch-black shadows
  * Key frontal PointLight for specular gleam
  * 8 Multi-colored PointLights orbiting in 3D paths
- Semi-transparent glass cube in front (PhysicalMaterial: transparent=True, transmission=0.9).
- Semi-transparent glass sphere behind the helmet.
- Standalone execution and headless/test suite support (--test).
"""

from __future__ import annotations
import math
import sys
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
    CubeTexture,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    Mesh,
    StandardMaterial,
    PhysicalMaterial,
    PointLight,
    HemisphereLight,
    BlendMode,
    Vec3,
)

ASSETS_DIR = repo_root / "assets"
HELMET_PATH = ASSETS_DIR / "DamagedHelmet.glb"
if not HELMET_PATH.exists():
    HELMET_PATH = (
        repo_root
        / "temp"
        / "threejs"
        / "examples"
        / "models"
        / "gltf"
        / "DamagedHelmet"
        / "glTF"
        / "DamagedHelmet.gltf"
    )


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run Example 13 in interactive or headless mode."""
    app = App("Velocity - 13 PBR Damaged Helmet", width=1280, height=720, clear_color="#0d1117")

    # Orbit controller looking at helmet center
    orb = OrbitController(target=(0.0, 1.0, 0.0), distance=4.5, min_distance=1.0, max_distance=15.0)
    app.camera = orb

    # Environment Cubemap for PBR specular reflections
    env = CubeTexture.create_gradient(
        top_color=Vec3(0.18, 0.35, 0.65),
        horizon_color=Vec3(0.60, 0.70, 0.85),
        bottom_color=Vec3(0.12, 0.14, 0.18),
        size=64,
    )
    app.scene.set_environment(env, 1.4)
    app.scene.set_background_cube(env)

    # Generous hemispheric ambient fill (eliminates pitch-black shadow crevices)
    hemi = HemisphereLight("SkyGround", Vec3(0.45, 0.50, 0.65), Vec3(0.25, 0.22, 0.20), 1.2)
    app.scene.add_light(hemi)

    # Directional sun
    app.scene.set_sun(direction=(-1.0, -2.0, -1.0), color=WARM_WHITE, intensity=1.8)

    # Dedicated key pointlight for frontal brilliance
    key_light = PointLight("KeyFrontLight", Vec3(1.0, 0.95, 0.85), 3.5, 10.0, 2.0)
    key_light.transform.position = (1.5, 2.5, 2.5)
    app.scene.add_light(key_light)

    # Ground grid
    app.scene.create_grid(size=30.0, step=1.0, color=Color.from_hex("#21262d"))

    # 1. Load DamagedHelmet
    helmet = app.scene.load_model(str(HELMET_PATH))
    if helmet and len(helmet.meshes) > 0:
        helmet.root_entity.transform.position = (0.0, 1.0, 0.0)
        helmet.root_entity.transform.scale = (1.2, 1.2, 1.2)

    # 2. Add 8 Multi-colored PointLights
    colors = [
        Vec3(1.0, 0.1, 0.1),   # Red
        Vec3(0.1, 1.0, 0.1),   # Green
        Vec3(0.1, 0.3, 1.0),   # Blue
        Vec3(1.0, 0.9, 0.1),   # Yellow
        Vec3(0.1, 1.0, 0.9),   # Cyan
        Vec3(1.0, 0.1, 0.9),   # Magenta
        Vec3(1.0, 1.0, 1.0),   # White
        Vec3(1.0, 0.5, 0.1),   # Orange
    ]

    lights: list[PointLight] = []
    for i, col in enumerate(colors):
        pt = PointLight(f"PointLight_{i}", col, 3.2, 7.0, 2.0)
        app.scene.add_light(pt)
        lights.append(pt)

    # 3. Semi-transparent glass cube in FRONT of the helmet
    front_glass = app.scene.create_entity("GlassCubeFront")
    front_glass.mesh = Mesh.create_box(1.2, 1.2, 1.2)
    front_glass.transform.position = (0.0, 1.0, 1.8)

    glass_front_mat = PhysicalMaterial()
    glass_front_mat.transparent = True
    glass_front_mat.opacity = 0.35
    glass_front_mat.depth_write = False
    glass_front_mat.blend_mode = BlendMode.Alpha
    glass_front_mat.transmission = 0.9
    glass_front_mat.ior = 1.52
    glass_front_mat.roughness = 0.05
    glass_front_mat.set_color(0.9, 0.95, 1.0, 0.35)
    front_glass.material = glass_front_mat

    # 4. Semi-transparent glass sphere BEHIND the helmet
    rear_glass = app.scene.create_entity("GlassSphereRear")
    rear_glass.mesh = Mesh.create_sphere(0.8, 24, 24)
    rear_glass.transform.position = (0.0, 1.0, -2.2)

    glass_rear_mat = StandardMaterial()
    glass_rear_mat.transparent = True
    glass_rear_mat.opacity = 0.50
    glass_rear_mat.depth_write = False
    glass_rear_mat.blend_mode = BlendMode.Alpha
    glass_rear_mat.roughness = 0.1
    glass_rear_mat.set_color(1.0, 0.3, 0.6, 0.50)
    rear_glass.material = glass_rear_mat

    # UI overlay
    app.ui.clear()
    app.ui.draw_text("VelocityEngine | 13: PBR Damaged Helmet Showcase", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("DamagedHelmet PBR (Normal, Emissive, AO, Metallic-Roughness)", (24, 52), size=16, color=CYAN)
    app.ui.draw_text("Sun + Balanced Ambient + Frontal Key + 8 Orbiting PointLights", (24, 76), size=14, color=WHITE)
    app.ui.show_stats(True)

    # Animation loop
    time_accum = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        # Rotate helmet slowly
        if helmet and len(helmet.meshes) > 0:
            helmet.root_entity.transform.rotate_y(15.0 * dt)

        # Orbit 8 lights
        radius = 2.6
        for i, pt in enumerate(lights):
            speed = 1.0 if (i % 2 == 0) else -0.8
            angle = (2.0 * math.pi / 8.0) * i + time_accum * speed
            lx = math.cos(angle) * radius
            lz = math.sin(angle) * radius
            ly = 1.0 + 0.6 * math.sin(time_accum * 1.5 + i)
            pt.transform.position = (lx, ly, lz)

        if (headless or "--test" in sys.argv or "--headless" in sys.argv) and frame_counter >= frames:
            app.close()

    app.on_update(update)

    if not headless and "--headless" not in sys.argv and "--test" not in sys.argv:
        app.run()
    else:
        for _ in range(frames):
            update(1.0 / 60.0)

    return app


# Module-level app for backward compatibility
app = None

if __name__ == "__main__":
    is_headless = "--headless" in sys.argv or "--test" in sys.argv
    app = run_example(headless=is_headless, frames=60)
