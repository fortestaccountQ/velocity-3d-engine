"""Example 02: Dynamic Lights & Bloom in Cyberpunk Room.

Showcase:
- Dark cyberpunk scene with 16 multi-colored PointLights orbiting in 3D Lissajous curves.
- Overhead SpotLight illuminating the central chamber.
- Neon columns and architectural pillars with `emissive_intensity = 4.0`.
- Full-screen post-processing via `EffectComposer` and `BloomPass`.
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

import pielosyty as ve
from pielosyty import (
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

    # 2. Neon architectural pillars with emissive_intensity = 4.0
    pillar_mesh = Mesh.create_box(0.6, 6.0, 0.6)
    neon_colors = [
        (0.0, 1.0, 0.9),   # Neon Cyan
        (1.0, 0.1, 0.8),   # Neon Magenta
        (0.2, 0.4, 1.0),   # Electric Blue
        (0.1, 1.0, 0.4),   # Acid Green
        (1.0, 0.6, 0.0),   # Neon Orange
        (0.8, 0.1, 1.0),   # Ultraviolet
    ]

    num_pillars = 12
    pillar_radius = 9.5
    for i in range(num_pillars):
        angle = (2.0 * math.pi * i) / num_pillars
        px = math.cos(angle) * pillar_radius
        pz = math.sin(angle) * pillar_radius

        c_idx = i % len(neon_colors)
        col = neon_colors[c_idx]

        pillar = scene.create_entity(f"NeonPillar_{i}")
        pillar.mesh = pillar_mesh
        mat = StandardMaterial()
        mat.base_color = (0.1, 0.1, 0.12, 1.0)
        mat.emissive_color = (col[0], col[1], col[2])
        mat.emissive_intensity = 4.0
        mat.roughness = 0.2
        mat.metallic = 0.8
        pillar.material = mat
        pillar.transform.position = (px, 3.0, pz)

    # Central podium totem
    center_podium = scene.create_entity("CenterPodium")
    center_podium.mesh = Mesh.create_cylinder(radius=1.5, height=1.0, segments=32)
    podium_mat = StandardMaterial()
    podium_mat.base_color = (0.15, 0.16, 0.2, 1.0)
    podium_mat.roughness = 0.3
    podium_mat.metallic = 0.9
    center_podium.material = podium_mat
    center_podium.transform.position = (0.0, 0.5, 0.0)

    # Totem crystal floating above podium
    crystal = scene.create_entity("CrystalTotem")
    crystal.mesh = Mesh.create_box(1.2, 2.2, 1.2)
    crystal_mat = StandardMaterial()
    crystal_mat.base_color = (0.9, 0.1, 0.5, 1.0)
    crystal_mat.emissive_color = (1.0, 0.2, 0.6)
    crystal_mat.emissive_intensity = 4.0
    crystal.material = crystal_mat
    crystal.transform.position = (0.0, 2.5, 0.0)

    # 3. Overhead SpotLight illuminating the central crystal
    spot = SpotLight("OverheadSpot", Vec3(0.9, 0.95, 1.0), 6.0, 30.0)
    spot.transform.position = (0.0, 10.0, 0.0)
    spot.direction = Vec3(0.0, -1.0, 0.0)
    spot.set_cone_angles(0.25, 0.65)
    scene.add_light(spot)

    # 4. 16 Multi-colored PointLights with orb indicator meshes
    light_colors = [
        Vec3(1.0, 0.1, 0.2), Vec3(0.1, 1.0, 0.3), Vec3(0.1, 0.5, 1.0), Vec3(1.0, 0.9, 0.1),
        Vec3(0.9, 0.1, 1.0), Vec3(0.1, 1.0, 0.9), Vec3(1.0, 0.5, 0.1), Vec3(0.7, 0.1, 0.9),
        Vec3(0.2, 1.0, 0.7), Vec3(1.0, 0.2, 0.6), Vec3(0.3, 0.8, 1.0), Vec3(1.0, 0.7, 0.2),
        Vec3(0.8, 1.0, 0.1), Vec3(0.5, 0.2, 1.0), Vec3(1.0, 0.3, 0.3), Vec3(0.2, 1.0, 1.0),
    ]

    point_lights: list[PointLight] = []
    light_indicators: list[ve.Entity] = []
    orb_mesh = Mesh.create_sphere(radius=0.15, rings=16, sectors=16)

    for i in range(16):
        col = light_colors[i]
        pt = PointLight(f"LissajousLight_{i}", col, 3.5, 7.5, 2.0)
        scene.add_light(pt)
        point_lights.append(pt)

        # Glowing visual orb representing the light source
        orb = scene.create_entity(f"LightOrb_{i}")
        orb.mesh = orb_mesh
        orb_mat = StandardMaterial()
        orb_mat.base_color = (col.x, col.y, col.z, 1.0)
        orb_mat.emissive_color = (col.x, col.y, col.z)
        orb_mat.emissive_intensity = 4.0
        orb.material = orb_mat
        light_indicators.append(orb)

    return point_lights, light_indicators, spot


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the dynamic lights & bloom example in interactive or headless mode."""
    app = App("Pielosyty - 02 Dynamic Lights & Bloom", width=1280, height=720, clear_color="#07090e")

    # Camera looking at center totem
    orb = OrbitController(target=(0.0, 2.5, 0.0), distance=15.0, min_distance=3.0, max_distance=35.0)
    app.camera = orb

    point_lights, light_indicators, spot = create_cyberpunk_scene(app)

    # Setup Post-Processing EffectComposer with BloomPass
    composer = EffectComposer(app.width, app.height)
    bloom = BloomPass(threshold=0.8, strength=2.8, radius=0.65)
    composer.add_pass(bloom)
    app.composer = composer

    # Setup UI overlay
    app.ui.clear()
    app.ui.draw_text("Pielosyty 3D Engine | 02: Dynamic Lights & BloomPass", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("16 Multi-colored PointLights in Lissajous Orbits + Emissive Pillars (intensity=4.0)", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("Post-Processing: EffectComposer with BloomPass (threshold=0.8, strength=2.8)", (24, 76), size=13, color=MAGENTA)
    app.ui.show_stats(True)

    time_accum = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        # Animate the 16 point lights along 3D Lissajous curves
        for i, pt in enumerate(point_lights):
            phase = (2.0 * math.pi * i) / 16.0
            freq_x = 0.8 + (i % 3) * 0.25
            freq_z = 0.9 + ((i + 1) % 4) * 0.2
            freq_y = 1.2 + (i % 2) * 0.3

            lx = 7.0 * math.sin(time_accum * freq_x + phase)
            lz = 7.0 * math.cos(time_accum * freq_z + phase * 1.3)
            ly = 1.8 + 1.2 * math.sin(time_accum * freq_y + phase * 0.7)

            pos = (lx, ly, lz)
            pt.transform.position = pos
            if i < len(light_indicators):
                light_indicators[i].transform.position = pos

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
