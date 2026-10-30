"""Example 12: Phase 2 Acceptance Criteria Showcase.

Demonstrates:
- Loaded .glb DamagedHelmet with full PBR maps:
  * normal_map (surface relief & micro-details)
  * emissive_map (glowing orange HUD elements)
  * metallic_roughness_map (metallic reflections & roughness)
  * ao_map / occlusion_map (crevice shadows)
- 8 Multi-colored PointLights orbiting the helmet.
- Semi-transparent glass cube in front (PhysicalMaterial: transparent=True, depth_write=False, transmission=0.9).
- Semi-transparent glass sphere behind the helmet.
- Render Queues: Transparent objects sorted strictly back-to-front by distance to camera.
"""

from __future__ import annotations
import math
import sys
from pathlib import Path

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

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
HELMET_PATH = ASSETS_DIR / "DamagedHelmet.glb"
if not HELMET_PATH.exists():
    HELMET_PATH = (
        Path(__file__).resolve().parent.parent
        / "temp"
        / "threejs"
        / "examples"
        / "models"
        / "gltf"
        / "DamagedHelmet"
        / "glTF"
        / "DamagedHelmet.gltf"
    )

app = App("VelocityEngine - Phase 2 PBR DamagedHelmet Showcase", width=1280, height=720, clear_color="#0d1117")

# Orbit controller looking at helmet center
orb = OrbitController(target=(0.0, 1.0, 0.0), distance=4.5, min_distance=1.0, max_distance=15.0)
app.camera = orb

# Environment & Reflections
env = CubeTexture.create_gradient(
    top_color=Vec3(0.18, 0.35, 0.65),
    horizon_color=Vec3(0.60, 0.70, 0.85),
    bottom_color=Vec3(0.12, 0.14, 0.18),
    size=64,
)
app.scene.set_environment(env, 1.4)
app.scene.set_background_cube(env)

# Generous hemispheric ambient fill
hemi = HemisphereLight("SkyGround", Vec3(0.45, 0.50, 0.65), Vec3(0.25, 0.22, 0.20), 1.2)
app.scene.add_light(hemi)

# Directional sun
app.scene.set_sun(direction=(-1.0, -2.0, -1.0), color=WARM_WHITE, intensity=1.8)

# Dedicated key spotlight/pointlight for frontal brilliance
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
    pt = PointLight(f"PointLight_{i}", col, 2.5, 5.0, 2.0)
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
app.ui.draw_text("VelocityEngine | Phase 2 PBR Showcase", (24, 24), size=20, color=WARM_WHITE)
app.ui.draw_text("DamagedHelmet (Normal, Emissive, AO, Metallic-Roughness)", (24, 52), size=16, color=CYAN)
app.ui.draw_text("8 Multi-colored PointLights + Transparent Front/Rear Glass", (24, 76), size=14, color=WHITE)
app.ui.show_stats(True)

# Animation loop
time_accum = 0.0

def update(dt: float) -> None:
    global time_accum
    time_accum += dt

    # Rotate helmet slowly
    if helmet and len(helmet.meshes) > 0:
        helmet.root_entity.transform.rotate_y(15.0 * dt)

    # Orbit 8 lights
    radius = 2.4
    for i, pt in enumerate(lights):
        speed = 1.0 if (i % 2 == 0) else -0.8
        angle = (2.0 * math.pi / 8.0) * i + time_accum * speed
        lx = math.cos(angle) * radius
        lz = math.sin(angle) * radius
        ly = 1.0 + 0.6 * math.sin(time_accum * 1.5 + i)
        pt.transform.position = (lx, ly, lz)

app.on_update(update)

if "--test" in sys.argv:
    app.on_update(lambda dt: app.close())

if __name__ == "__main__":
    app.run()
