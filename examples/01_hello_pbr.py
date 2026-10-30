"""Example 01: Hello PBR (Physically Based Rendering) Sphere Grid.

Showcase:
- 5x5 grid of spheres varying Metallic (0.0 -> 1.0 on X-axis) and Roughness (0.05 -> 1.0 on Y-axis).
- Environment Cubemap IBL reflections (Image-Based Lighting) and sky gradient.
- Directional Sunlight with soft PBR BRDF response.
- OrbitController for intuitive camera inspection.
- Production-ready standalone and headless/test execution.
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
    CubeTexture,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
)


def create_pbr_scene(app: App) -> list[ve.Entity]:
    """Populate the scene with the 5x5 PBR sphere grid and environment."""
    scene = app.scene

    # 1. Procedural High-Dynamic-Range Environment Cubemap for IBL
    env_cube = CubeTexture.create_gradient(
        top_color=Vec3(0.2, 0.45, 0.85),
        horizon_color=Vec3(0.75, 0.82, 0.95),
        bottom_color=Vec3(0.12, 0.14, 0.18),
        size=128,
    )
    scene.set_background_cube(env_cube)
    scene.set_environment(env_cube, 1.4)

    # 2. Directional Sunlight
    scene.set_sun(direction=(-1.0, -2.0, -1.2), color=WARM_WHITE, intensity=1.5)

    # 3. Ground Grid
    scene.create_grid(size=40.0, step=1.0, color=Color.from_hex("#252836"))

    # Shared high-polygon sphere geometry
    sphere_mesh = Mesh.create_sphere(radius=0.75, rings=32, sectors=32)

    spheres: list[ve.Entity] = []
    rows = 5
    cols = 5
    spacing = 2.0

    # Base color: metallic gold-copper alloy tint
    base_tint = (1.0, 0.78, 0.35, 1.0)

    for row in range(rows):
        roughness = max(0.05, float(row) / float(rows - 1))
        y = (row - (rows - 1) / 2.0) * spacing + 5.0

        for col in range(cols):
            metallic = float(col) / float(cols - 1)
            x = (col - (cols - 1) / 2.0) * spacing

            ent = scene.create_entity(f"PBR_Sphere_M{col}_R{row}")
            ent.mesh = sphere_mesh

            mat = StandardMaterial()
            mat.base_color = base_tint
            mat.metallic = metallic
            mat.roughness = roughness
            ent.material = mat

            ent.transform.position = (x, y, 0.0)
            spheres.append(ent)

    return spheres


def setup_ui(app: App) -> None:
    """Configure UI Overlay with educational HUD information."""
    app.ui.clear()
    app.ui.draw_text("Velocity 3D Engine | 01: Hello PBR Grid", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("X-Axis: Metallic (0.0 -> 1.0)   |   Y-Axis: Roughness (0.05 -> 1.0)", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("LMB: Orbit Camera | RMB/MMB: Pan | Scroll: Zoom", (24, 76), size=13, color=WHITE)
    app.ui.show_stats(True)


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the Hello PBR example in interactive or headless test mode."""
    app = App("Velocity - 01 Hello PBR", width=1280, height=720, clear_color="#0e1117")

    # OrbitController centered on the sphere grid center (Y=5.0)
    orb = OrbitController(target=(0.0, 5.0, 0.0), distance=12.5, min_distance=2.0, max_distance=35.0)
    app.camera = orb

    spheres = create_pbr_scene(app)
    setup_ui(app)

    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal frame_counter
        frame_counter += 1

        # Subtle rotation of each sphere to showcase dynamic specular highlights
        for i, s in enumerate(spheres):
            s.transform.rotate_y(15.0 * dt)

        if (headless or "--test" in sys.argv or "--headless" in sys.argv) and frame_counter >= frames:
            app.close()

    app.on_update(update)

    if not headless and "--headless" not in sys.argv:
        app.run()
    else:
        # Headless simulation loop without window creation
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
