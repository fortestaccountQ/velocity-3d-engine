"""Example 01: Hello Window & Procedural Background.

Showcase:
- Clean window initialization with Sokol GFX backend via `App`.
- Procedural HDR Gradient Skybox via `CubeTexture.create_gradient()`.
- Directional Sunlight with warm white spectrum and intensity.
- Ground reference plane with `scene.create_grid()`.
- Centered spinning metallic engine cube with `StandardMaterial`.
- 2D `UIOverlay` title banner and live performance HUD stats.
- Standalone execution and headless/test suite support (--test).
"""

from __future__ import annotations
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
    StandardMaterial,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
)


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run Example 01 in interactive or headless mode."""
    app = App("VelocityEngine - 01 Hello Window", width=1280, height=720, clear_color="#0d1117")

    # OrbitController inspecting the origin
    orb = OrbitController(target=(0.0, 1.0, 0.0), distance=6.0, min_distance=2.0, max_distance=30.0)
    app.camera = orb

    # Directional sunlight
    app.scene.set_sun(direction=(-1.0, -2.0, -1.0), color=WARM_WHITE, intensity=1.5)

    # Procedural gradient skybox and ambient environment
    sky = CubeTexture.create_gradient(
        top_color=Vec3(0.12, 0.28, 0.55),
        horizon_color=Vec3(0.55, 0.70, 0.88),
        bottom_color=Vec3(0.08, 0.10, 0.14),
        size=64,
    )
    app.scene.set_environment(sky, 1.2)
    app.scene.set_background_cube(sky)

    # Ground reference grid
    app.scene.create_grid(size=30.0, step=1.0, color=Color.from_hex("#21262d"))

    # Centered metallic hero box
    box = app.scene.create_box(size=(1.4, 1.4, 1.4), position=(0.0, 1.2, 0.0))
    mat = StandardMaterial()
    mat.base_color = (0.2, 0.6, 1.0, 1.0)
    mat.metallic = 0.85
    mat.roughness = 0.20
    box.material = mat

    # 2D Screen-space UIOverlay
    app.ui.clear()
    app.ui.draw_text("VelocityEngine | 01: Hello Window", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("Procedural HDR Gradient Sky, Sun Directional Light, Ground Grid", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("Controls: [Mouse Drag] Orbit | [Scroll] Zoom | [ESC] Exit", (24, 76), size=13, color=WHITE)
    app.ui.show_stats(True)

    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal frame_counter
        frame_counter += 1

        box.transform.rotate_y(30.0 * dt)

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
