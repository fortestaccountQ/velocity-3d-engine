"""Example 02: Textured PBR Rotating Cube.

Showcase:
- Physically Based Rendering (PBR) metallic-roughness material model.
- Dynamic key PointLight + Directional Sunlight.
- Continuous multi-axis rotation modulated smoothly by delta time (dt).
- Ground reference plane with `scene.create_grid()`.
- 2D `UIOverlay` educational HUD with live statistics.
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
    StandardMaterial,
    PointLight,
    CubeTexture,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
)


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run Example 02 in interactive or headless mode."""
    app = App("VelocityEngine - 02 Rotating Cube", width=1280, height=720, clear_color="#0e131f")

    # Camera looking at cube
    orb = OrbitController(target=(0.0, 1.2, 0.0), distance=4.8, min_distance=1.5, max_distance=20.0)
    app.camera = orb

    # Directional sun and subtle environment
    app.scene.set_sun(direction=(-1.0, -2.5, -1.2), color=WARM_WHITE, intensity=1.6)

    sky = CubeTexture.create_gradient(
        top_color=Vec3(0.10, 0.22, 0.45),
        horizon_color=Vec3(0.45, 0.55, 0.70),
        bottom_color=Vec3(0.06, 0.08, 0.12),
        size=64,
    )
    app.scene.set_environment(sky, 1.0)
    app.scene.set_background_cube(sky)

    # Dynamic orbiting key point light
    key_light = PointLight("KeyLight", Vec3(0.2, 0.7, 1.0), 3.5, 9.0, 2.0)
    key_light.transform.position = (2.5, 3.0, 2.5)
    app.scene.add_light(key_light)

    # Ground reference grid
    app.scene.create_grid(size=24.0, step=1.0, color=Color.from_hex("#1b2230"))

    # Central spinning PBR cube
    cube = app.scene.create_box(size=(1.6, 1.6, 1.6), position=(0.0, 1.2, 0.0))
    mat = StandardMaterial()
    mat.base_color = (0.95, 0.45, 0.15, 1.0)  # Vibrant orange
    mat.metallic = 0.75
    mat.roughness = 0.22
    cube.material = mat

    # 2D UI Overlay
    app.ui.clear()
    app.ui.draw_text("VelocityEngine | 02: Textured PBR Rotating Cube", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("PBR Metallic 0.75, Roughness 0.22, Dual-axis dt-independent rotation", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("Controls: [Mouse Drag] Orbit | [Scroll] Zoom | [ESC] Exit", (24, 76), size=13, color=WHITE)
    app.ui.show_stats(True)

    frame_counter = 0
    time_accum = 0.0

    def update(dt: float) -> None:
        nonlocal frame_counter, time_accum
        frame_counter += 1
        time_accum += dt

        # Smooth dual-axis rotation
        cube.transform.rotate_y(45.0 * dt)
        cube.transform.rotate_x(30.0 * dt)

        # Orbit the key light around the cube
        lx = math.cos(time_accum * 1.5) * 3.0
        lz = math.sin(time_accum * 1.5) * 3.0
        key_light.transform.position = (lx, 2.5 + math.sin(time_accum * 2.0) * 0.8, lz)

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
