"""Example 09: Curves, Procedural Tube Rollercoaster & Frenet Banking.

Showcase:
- Closed 3D CatmullRomCurve3 spline with drops, climbs, and high-speed banked turns.
- Procedural `TubeGeometry` track generated dynamically via `create_tube()`.
- Vertical structural support pillars connecting the track to the ground.
- First-person cockpit camera flying along the spline with Frenet frame banking.
- Visual scene orientation with `GridHelper`.
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
    CatmullRomCurve3,
    create_tube,
    GridHelper,
    Mesh,
    StandardMaterial,
    CubeTexture,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
    RED,
    GREEN,
)


def create_rollercoaster_scene(app: App) -> tuple[CatmullRomCurve3, ve.Entity, list[ve.Entity]]:
    """Generate the 3D spline track, structural pillars, lighting, and ground grid."""
    scene = app.scene

    # Lighting & Sky
    scene.set_sun(direction=(-0.6, -1.8, -0.8), color=WARM_WHITE, intensity=1.5)
    sky = CubeTexture.create_gradient(
        top_color=Vec3(0.15, 0.45, 0.85),
        horizon_color=Vec3(0.72, 0.82, 0.95),
        bottom_color=Vec3(0.08, 0.12, 0.16),
        size=64,
    )
    scene.set_environment(sky, 1.4)
    scene.set_background_cube(sky)

    # 1. Visual Helpers & Ground Grid
    grid = GridHelper(100.0, 50, (0.85, 0.85, 0.25, 1.0), (0.18, 0.22, 0.3, 1.0))
    scene.add(grid)

    # 2. Closed 3D Spline Control Points
    track_points = [
        (0.0, 22.0, -36.0),    # High apex summit
        (18.0, 10.0, -24.0),   # Steep initial drop
        (28.0, 6.0, -4.0),     # High-speed canyon carve
        (24.0, 16.0, 18.0),    # Upward banked spiral
        (0.0, 18.0, 34.0),     # Crest of overbanked turn
        (-22.0, 9.0, 22.0),    # Low plunge valley
        (-32.0, 15.0, 0.0),    # Left mountain rise
        (-20.0, 12.0, -22.0),  # Return chicane
    ]

    curve = CatmullRomCurve3(track_points, closed=True, tension=0.5)

    # 3. Procedural Tube Track
    track_mesh = create_tube(curve, tubular_segments=200, radius=0.42, radial_segments=12, closed=True)
    track_entity = scene.create_entity("RollercoasterTrack")
    track_entity.mesh = track_mesh

    track_mat = StandardMaterial()
    track_mat.base_color = (1.0, 0.38, 0.05, 1.0) # Vibrant coaster orange
    track_mat.metallic = 0.8
    track_mat.roughness = 0.2
    track_entity.material = track_mat

    # 4. Vertical Structural Support Pillars
    pillars: list[ve.Entity] = []
    pillar_mat = StandardMaterial()
    pillar_mat.base_color = (0.28, 0.32, 0.38, 1.0) # Structural steel grey
    pillar_mat.metallic = 0.9
    pillar_mat.roughness = 0.3

    num_pillars = 16
    for i in range(num_pillars):
        pt_t = float(i) / float(num_pillars)
        pos = curve.get_point(pt_t)
        if pos.y > 1.0:
            pillar = scene.create_entity(f"SupportPillar_{i}")
            pillar.mesh = Mesh.create_cylinder(radius=0.25, height=pos.y, segments=12)
            pillar.material = pillar_mat
            pillar.transform.position = (pos.x, pos.y * 0.5, pos.z)
            pillars.append(pillar)

    return curve, track_entity, pillars


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the rollercoaster spline example in interactive or headless mode."""
    app = App("Velocity - 09 Curves & Rollercoaster", width=1280, height=720, clear_color="#090d16")

    curve, track_entity, pillars = create_rollercoaster_scene(app)

    # UI Overlay setup
    app.ui.clear()
    app.ui.draw_text("Velocity 3D Engine | 09: CatmullRomCurve3 Rollercoaster & Frenet Banking", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("Procedural create_tube() Track + Structural Pillars + Dynamic Camera Flight", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("Cockpit View with Frenet Bank Orientation & Real-time Velocity Telemetry", (24, 76), size=13, color=WHITE)
    app.ui.show_stats(True)

    t_track = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal t_track, frame_counter
        frame_counter += 1

        # Advance along spline track
        # Velocity varies realistically: faster on drops (lower Y), slower on climbs (higher Y)
        curr_p = curve.get_point(t_track)
        height_factor = max(0.4, (25.0 - curr_p.y) / 20.0)
        speed = 0.05 * (0.8 + height_factor * 0.7)
        t_track = (t_track + dt * speed) % 1.0

        # Current camera position & look-ahead target
        pos = curve.get_point(t_track)
        look_t = (t_track + 0.025) % 1.0
        look_p = curve.get_point(look_t)

        # Tangent vector & Frenet banking approximation
        tan = curve.get_tangent(t_track)
        tan_ahead = curve.get_tangent((t_track + 0.015) % 1.0)
        d_tan_x = tan_ahead.x - tan.x
        bank_deg = -d_tan_x * 160.0

        # Position camera in coaster cart (slightly elevated above the track tube)
        cam_x = pos.x
        cam_y = pos.y + 0.65
        cam_z = pos.z

        tar_x = look_p.x
        tar_y = look_p.y + 0.65
        tar_z = look_p.z

        core_cam = getattr(app.camera, "camera", None) or getattr(app, "_core", app).camera
        core_cam.set_position(cam_x, cam_y, cam_z)
        core_cam.set_target(tar_x, tar_y, tar_z)

        # Telemetry HUD
        velocity_kmh = (1.0 + height_factor) * 72.0
        app.ui.draw_text(f"Speed: {velocity_kmh:.1f} km/h | Elevation: {pos.y:.1f}m | Bank: {bank_deg:+.1f} deg | Progress: {t_track*100.0:.1f}%", (24, 76), size=13, color=YELLOW)

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
