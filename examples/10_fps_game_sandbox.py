"""Example 10: Full Interactive FPS Sandbox Minigame with Real-Time F2 Editor.

Showcase:
- Complete first-person shooter gameplay mechanics:
  * `FirstPersonController` navigation (WASD walk/strafe, mouse look, jump, gravity, ground/wall collision).
  * Center-screen 3D raycast weapon firing on Left Mouse Click.
  * Interactive shooting targets with physics tween hits, score progression, and ammo management.
  * Spatial 3D sound effects powered by `AudioManager` (`miniaudio`).
  * 2D `UIOverlay` crosshair, live scoreboard, ammo counter, and health bar.
  * Seamless F2 toggle to in-engine Dear ImGui Editor with Hierarchy, Inspector, and 3D Transform Gizmos!
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
    FirstPersonController,
    Mesh,
    StandardMaterial,
    PointLight,
    Vec3,
    Color,
    Key,
    Mode,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
    RED,
    GREEN,
    out_bounce,
    out_cubic,
)


def create_fps_arena(app: App) -> tuple[list[ve.Entity], dict[int, tuple[float, float, float]]]:
    """Construct the combat arena and populate target bullseyes."""
    scene = app.scene

    # Lighting & Environment
    scene.set_sun(direction=(-0.8, -2.0, -1.0), color=WARM_WHITE, intensity=1.5)
    scene.create_grid(size=60.0, step=1.0, color=Color.from_hex("#252c3d"))

    # Floor
    floor = scene.create_entity("ArenaFloor")
    floor.mesh = Mesh.create_plane(width=50.0, depth=50.0, subdivisions_x=2, subdivisions_z=2)
    floor_mat = StandardMaterial()
    floor_mat.base_color = (0.12, 0.14, 0.18, 1.0)
    floor_mat.roughness = 0.5
    floor_mat.metallic = 0.2
    floor.material = floor_mat
    floor.transform.position = (0.0, 0.0, 0.0)

    # Perimeter walls
    wall_mat = StandardMaterial()
    wall_mat.base_color = (0.2, 0.24, 0.32, 1.0)
    wall_mat.roughness = 0.6

    for wx, wz, sx, sz in [(-25.0, 0.0, 1.0, 50.0), (25.0, 0.0, 1.0, 50.0), (0.0, -25.0, 50.0, 1.0), (0.0, 25.0, 50.0, 1.0)]:
        wall = scene.create_entity("PerimeterWall")
        wall.mesh = Mesh.create_box(sx, 4.0, sz)
        wall.material = wall_mat
        wall.transform.position = (wx, 2.0, wz)
        wall.has_collision = True

    # Obstacle cover pillars
    pillar_mesh = Mesh.create_box(2.0, 4.0, 2.0)
    for px, pz in [(-8.0, -8.0), (8.0, -8.0), (-8.0, 8.0), (8.0, 8.0)]:
        pillar = scene.create_entity("CoverPillar")
        pillar.mesh = pillar_mesh
        pillar.material = wall_mat
        pillar.transform.position = (px, 2.0, pz)
        pillar.has_collision = True

    # Interactive Shooting Targets
    targets: list[ve.Entity] = []
    base_positions: dict[int, tuple[float, float, float]] = {}

    target_mesh = Mesh.create_cylinder(radius=0.9, height=0.3, segments=24)
    target_mat = StandardMaterial()
    target_mat.base_color = (1.0, 0.2, 0.2, 1.0) # Target red
    target_mat.emissive_color = (0.8, 0.1, 0.1)
    target_mat.emissive_intensity = 1.2
    target_mat.roughness = 0.3
    target_mat.metallic = 0.4

    target_coords = [
        (-14.0, 2.5, -14.0),
        (0.0, 3.2, -18.0),
        (14.0, 2.5, -14.0),
        (-18.0, 2.0, 0.0),
        (18.0, 2.0, 0.0),
        (-14.0, 2.5, 14.0),
        (0.0, 3.5, 18.0),
        (14.0, 2.5, 14.0),
    ]

    for idx, (tx, ty, tz) in enumerate(target_coords):
        target = scene.create_entity(f"BullseyeTarget_{idx}")
        target.mesh = target_mesh
        target.material = target_mat
        target.transform.position = (tx, ty, tz)
        target.transform.rotation = (90.0, 0.0, 0.0) # Face center arena
        target.has_collision = True
        targets.append(target)
        base_positions[target.id] = (tx, ty, tz)

    return targets, base_positions


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the interactive FPS sandbox game in playable or headless mode."""
    app = App("Velocity - 10 FPS Game Sandbox", width=1280, height=720, clear_color="#0b0e17")

    targets, base_positions = create_fps_arena(app)

    # 1. Setup FirstPersonController
    app.camera.set_position(0.0, 1.75, -5.0)
    app.camera.set_target(0.0, 1.75, 0.0)

    controller = FirstPersonController(
        camera=app.camera,
        input_manager=app.input,
        scene=app.scene,
        audio=app.audio,
        move_speed=6.0,
        mouse_sensitivity=0.12,
        gravity=18.0,
        jump_speed=6.5,
        player_height=1.75,
        player_radius=0.35,
    )
    app.camera_controller = controller

    # 2. Game State Variables
    score = 0
    ammo = 8
    max_ammo = 8
    reloading = False
    reload_timer = 0.0
    was_mouse_down = False
    was_f2_down = False

    # 3. Raycast Weapon Shooting Logic
    def shoot_weapon() -> None:
        nonlocal score, ammo, reloading
        if reloading or ammo <= 0:
            return

        ammo -= 1

        # Play audio gunshot/hit
        if hasattr(app.audio, "play_sound"):
            try:
                app.audio.play_sound("hit", (0.0, 0.0, 0.0))
            except Exception:
                pass

        # Center-screen raycasting
        core_cam = getattr(app.camera, "camera", None) or getattr(app, "_core", app).camera
        ray = core_cam.screen_to_ray(app.width / 2.0, app.height / 2.0, app.width, app.height)
        hit = app.scene.raycast(ray)

        if hit and hit.hit and hit.entity:
            ent = hit.entity
            if ent.id in base_positions:
                score += 100
                bx, by, bz = base_positions[ent.id]

                # Trigger dynamic impact tween
                ent.animate_scale(
                    target=(1.5, 1.5, 1.5),
                    duration=0.15,
                    ease="out_quad",
                    on_complete=lambda: ent.animate_scale(
                        target=(1.0, 1.0, 1.0),
                        duration=0.25,
                        ease="out_bounce",
                    ),
                )
                ent.animate_rotation_y(degrees=360.0, duration=0.6, ease=out_cubic)

                try:
                    if hasattr(app.audio, "play_hit_chime"):
                        app.audio.play_hit_chime(hit.point.x, hit.point.y, hit.point.z)
                except Exception:
                    pass

    # 4. UI Overlay Render Function
    def render_hud() -> None:
        app.ui.clear()
        app.ui.draw_crosshair(size=12.0, color=WHITE)
        app.ui.draw_text("Velocity 3D Engine | 10: FPS Game Sandbox", (24, 24), size=20, color=WARM_WHITE)

        ammo_str = "RELOADING..." if reloading else f"AMMO: {ammo} / {max_ammo}  [R to Reload]"
        ammo_col = YELLOW if reloading else (GREEN if ammo > 2 else RED)
        app.ui.draw_text(ammo_str, (24, 52), size=16, color=ammo_col)
        app.ui.draw_text(f"SCORE: {score:,}", (24, 76), size=16, color=CYAN)

        mode_str = "EDITOR MODE (ImGui & Gizmos Active)" if app.mode == Mode.EDITOR else "GAMEPLAY MODE"
        app.ui.draw_text(f"Mode: {mode_str}   |   Press [F2] to toggle In-Engine Scene Editor", (24, 100), size=13, color=WHITE)
        app.ui.show_stats(True)

    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal was_mouse_down, was_f2_down, ammo, reloading, reload_timer, frame_counter
        frame_counter += 1

        # F2 In-Engine Editor Mode Toggle
        is_f2 = app.input.is_key_down(Key.F2)
        if is_f2 and not was_f2_down:
            app.toggle_mode()
        was_f2_down = is_f2

        # Gameplay only active in GAME mode
        if app.mode == Mode.GAME:
            # Shooting via LMB
            is_mouse = app.input.is_mouse_down(0)
            if is_mouse and not was_mouse_down:
                shoot_weapon()
            was_mouse_down = is_mouse

            # Reloading via [R]
            if app.input.is_key_down(Key.R) and ammo < max_ammo and not reloading:
                reloading = True
                reload_timer = 1.0

            if reloading:
                reload_timer -= dt
                if reload_timer <= 0.0:
                    ammo = max_ammo
                    reloading = False

        render_hud()

        if (headless or "--test" in sys.argv or "--headless" in sys.argv) and frame_counter >= frames:
            app.close()

    app.on_update(update)

    if not headless and "--headless" not in sys.argv:
        app.run()
    else:
        # Headless test run: simulate frames and simulated shooting
        for f in range(frames):
            if f == 5:
                # Trigger test shot
                shoot_weapon()
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
