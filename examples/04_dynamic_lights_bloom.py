"""Example 04: Dynamic Lights & Bloom in Cyberpunk Room.

Showcase:
- Dark cyberpunk scene with 16 multi-colored PointLights orbiting in 3D Lissajous curves.
- Overhead SpotLight illuminating the central chamber.
- Neon columns and architectural pillars with `emissive_intensity = 4.0`.
- Full-screen post-processing via `EffectComposer` and `BloomPass`.
- Standalone execution and headless/test suite support (--test).
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
    StandardMaterial,
    PointLight,
    SpotLight,
    HemisphereLight,
    EffectComposer,
    BloomPass,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    MAGENTA,
)


def create_cyberpunk_scene(app: App) -> tuple[list[PointLight], list[ve.Entity], SpotLight]:
    """Build the cyberpunk chamber with neon pillars, overhead spotlight, and orbiting point lights."""
    scene = app.scene

    # Ambient / subtle hemispheric night fill
    hemi = HemisphereLight("CyberAmbient", Vec3(0.05, 0.08, 0.15), Vec3(0.02, 0.02, 0.03), 0.4)
    scene.add_light(hemi)

    # 1. Dark reflective floor & grid
    scene.create_grid(size=50.0, step=1.0, color=Color.from_hex("#161a24"))

    floor_mat = StandardMaterial()
    floor_mat.base_color = (0.05, 0.06, 0.08, 1.0)
    floor_mat.roughness = 0.25
    floor_mat.metallic = 0.85

    floor = scene.create_entity("FloorPlane")
    floor.mesh = Mesh.create_plane(width=50.0, depth=50.0, subdivisions_x=2, subdivisions_z=2)
    floor.material = floor_mat
    floor.transform.position = (0.0, 0.0, 0.0)

    # 2. Emissive neon pillars around the room perimeter
    pillars: list[ve.Entity] = []
    cylinder_mesh = Mesh.create_cylinder(radius=0.4, height=6.0, segments=24)
    cube_cap = Mesh.create_box(0.9, 0.3, 0.9)

    pillar_colors = [
        (1.0, 0.05, 0.4, 1.0),   # Neon pink
        (0.0, 0.9, 1.0, 1.0),    # Cyber cyan
        (0.7, 0.1, 1.0, 1.0),    # Neon purple
        (0.2, 1.0, 0.4, 1.0),    # Matrix green
        (1.0, 0.7, 0.0, 1.0),    # Amber
        (0.1, 0.3, 1.0, 1.0),    # Deep blue
        (1.0, 0.1, 0.1, 1.0),    # Vivid red
        (0.0, 1.0, 0.8, 1.0),    # Teal
    ]

    radius = 12.0
    for i, col in enumerate(pillar_colors):
        angle = (2.0 * math.pi / len(pillar_colors)) * i
        px = math.cos(angle) * radius
        pz = math.sin(angle) * radius

        p_ent = scene.create_entity(f"NeonPillar_{i}")
        p_ent.mesh = cylinder_mesh

        mat = StandardMaterial()
        mat.base_color = col
        mat.emissive_color = (col[0], col[1], col[2])
        mat.emissive_intensity = 4.0
        mat.metallic = 0.5
        mat.roughness = 0.2
        p_ent.material = mat
        p_ent.transform.position = (px, 3.0, pz)
        pillars.append(p_ent)

    # 3. Overhead SpotLight aiming down at the center pedestal
    spot = SpotLight(
        "CeilingSpotLight",
        Vec3(1.0, 0.95, 0.9),
        4.5,
        25.0,
    )
    spot.set_cone_angles(math.radians(18.0), math.radians(32.0))
    spot.transform.position = (0.0, 12.0, 0.0)
    spot.set_direction(0.0, -1.0, 0.0)
    scene.add_light(spot)

    # Center pedestal object
    pedestal = scene.create_entity("CenterPedestal")
    pedestal.mesh = Mesh.create_cylinder(radius=1.5, height=1.0, segments=32)
    ped_mat = StandardMaterial()
    ped_mat.base_color = (0.8, 0.82, 0.85, 1.0)
    ped_mat.metallic = 0.9
    ped_mat.roughness = 0.15
    pedestal.material = ped_mat
    pedestal.transform.position = (0.0, 0.5, 0.0)

    center_sphere = scene.create_entity("CenterHeroSphere")
    center_sphere.mesh = Mesh.create_sphere(radius=0.9, rings=32, sectors=32)
    sphere_mat = StandardMaterial()
    sphere_mat.base_color = (0.95, 0.85, 0.6, 1.0)
    sphere_mat.metallic = 0.95
    sphere_mat.roughness = 0.08
    center_sphere.material = sphere_mat
    center_sphere.transform.position = (0.0, 1.9, 0.0)

    # 4. 16 Dynamic PointLights moving in 3D Lissajous orbits
    point_lights: list[PointLight] = []
    light_colors = [
        Vec3(1.0, 0.1, 0.4), Vec3(0.0, 0.8, 1.0), Vec3(0.8, 0.2, 1.0), Vec3(0.2, 1.0, 0.5),
        Vec3(1.0, 0.6, 0.0), Vec3(0.1, 0.4, 1.0), Vec3(1.0, 0.1, 0.1), Vec3(0.0, 1.0, 0.8),
        Vec3(1.0, 0.2, 0.8), Vec3(0.3, 1.0, 0.2), Vec3(0.9, 0.9, 0.1), Vec3(0.1, 0.9, 1.0),
        Vec3(1.0, 0.4, 0.1), Vec3(0.6, 0.1, 1.0), Vec3(0.2, 0.8, 0.4), Vec3(1.0, 0.9, 0.5),
    ]

    for i in range(16):
        col = light_colors[i]
        pt = PointLight(f"LissajousLight_{i}", col, intensity=2.2, range=7.5, decay=2.0)
        scene.add_light(pt)
        point_lights.append(pt)

    return point_lights, pillars, spot


def setup_postprocessing(app: App) -> BloomPass:
    """Initialize HDR Bloom post-processing pipeline."""
    composer = EffectComposer(app.width, app.height)
    bloom = BloomPass(threshold=0.85, strength=1.4, radius=0.6)
    composer.add_pass(bloom)
    app.composer = composer
    return bloom


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run Example 04 in interactive or headless mode."""
    app = App("Velocity - 04 Dynamic Lights & Bloom", width=1280, height=720, clear_color="#07080d")

    orb = OrbitController(target=(0.0, 2.0, 0.0), distance=18.0, min_distance=4.0, max_distance=40.0, pitch=25.0)
    app.camera = orb

    lights, pillars, spot = create_cyberpunk_scene(app)
    bloom_pass = setup_postprocessing(app)

    # UI Overlay setup
    app.ui.clear()
    app.ui.draw_text("Velocity 3D Engine | 04: Dynamic Lights & Bloom", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("16 Orbiting Lissajous PointLights + 8 Emissive Neon Pillars + HDR BloomPass", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("LMB: Orbit Camera | RMB/MMB: Pan | Scroll: Zoom", (24, 76), size=13, color=WHITE)
    app.ui.show_stats(True)

    time_accum = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        # Animate 16 point lights in complex 3D Lissajous orbits
        for i, pt in enumerate(lights):
            speed = 1.0 + (i % 4) * 0.25
            freq_x = 0.8 + (i % 3) * 0.3
            freq_y = 1.2 + (i % 2) * 0.5
            freq_z = 0.9 + (i % 5) * 0.2
            phase = i * (2.0 * math.pi / len(lights))

            lx = math.sin(time_accum * speed * freq_x + phase) * 8.5
            ly = 1.5 + math.sin(time_accum * speed * freq_y + phase * 1.5) * 2.2
            lz = math.cos(time_accum * speed * freq_z + phase) * 8.5

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


if __name__ == "__main__":
    is_headless = "--headless" in sys.argv or "--test" in sys.argv
    run_example(headless=is_headless, frames=60)
