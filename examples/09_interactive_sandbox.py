"""Example B: Interactive Sandbox with Cubes, FirstPersonController, Click Raycast, and Tweens.

Demonstrates:
  - Three.js parity scene construction (App, Camera, Sunlight, Grid)
  - FirstPersonController navigation (WASD, mouse look, jump, collision)
  - Screen-to-world raycasting on mouse click (@app.on_click)
  - Tweening system: bouncy jumps (out_bounce), 360-degree rotations (out_cubic), and scale pulses
  - 2D UIOverlay: screen-center crosshair, live interaction stats, and instructions
"""

import sys
import math
from pathlib import Path

# Ensure 'python' package dir is available if running directly from repo root
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

from VelocityEngine import (
    App,
    FirstPersonController,
    Color,
    WHITE,
    WARM_WHITE,
    CYAN,
    YELLOW,
    RED,
    GREEN,
    BLUE,
    MAGENTA,
    ORANGE,
    PURPLE,
    out_bounce,
    out_cubic,
)


def main():
    print("=" * 75)
    print(" VelocityEngine: Example B - Interactive Sandbox (Three.js Parity)")
    print("=" * 75)
    print("Controls:")
    print("  [W / A / S / D] : Move player (Walk)")
    print("  [Mouse]         : Look around (Hold RMB or Free Cursor)")
    print("  [SPACE]         : Jump")
    print("  [Left Click]    : Raycast click on cubes to trigger tweens & animations")
    print("  [TAB]           : Toggle Mouse Cursor Lock")
    print("  [ESC]           : Exit application")
    print("=" * 75)

    # 1. Initialize Window Application
    app = App(
        title="VelocityEngine - Interactive Sandbox",
        width=1280,
        height=720,
        clear_color=Color.from_hex("#1b1e28"),
    )

    # 2. Sunlight & Environment
    app.scene.set_sun(direction=(-0.8, -1.8, -1.0), color=WARM_WHITE, intensity=1.4)
    app.scene.create_grid(size=50.0, step=1.0, color=Color.from_hex("#2a2e3d"))

    # 3. Create Interactive Colored Cubes in a Circle
    cubes = []
    base_positions = {}
    colors = [RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA, ORANGE, PURPLE]
    num_cubes = len(colors)
    radius = 6.0

    for i, col in enumerate(colors):
        angle = (2.0 * math.pi * i) / num_cubes
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius
        y = 0.5  # Rest on grid

        cube = app.scene.create_box(size=(1.2, 1.2, 1.2), position=(x, y, z), color=col)
        cube.name = f"InteractiveCube_{i}"
        cube.has_collision = True
        cubes.append(cube)
        base_positions[cube.id] = (x, y, z)

    # Center floating totem
    totem = app.scene.create_cylinder(radius=0.6, height=2.5, segments=24, position=(0, 1.25, 0), color=Color.from_hex("#e0a842"))
    totem.name = "CenterTotem"
    totem.has_collision = True
    base_positions[totem.id] = (0.0, 1.25, 0.0)

    # 4. First-Person Camera Controller
    app.camera.set_position(0.0, 1.7, -9.0)
    app.camera.set_target(0.0, 1.2, 0.0)

    controller = FirstPersonController(
        camera=app.camera,
        input_manager=app.input,
        scene=app.scene,
        audio=app.audio,
        move_speed=5.5,
        mouse_sensitivity=0.12,
        gravity=16.0,
        jump_speed=6.0,
        player_height=1.7,
        player_radius=0.35,
    )
    app.camera_controller = controller

    # 5. Interaction State & UI
    stats = {"clicks": 0, "last_target": "None"}
    app.ui.show_stats(True)

    # 6. Click Raycasting & Tween Animations
    @app.on_click
    def on_scene_click(hit):
        if not hit or not hit.hit or not hit.entity:
            return

        ent = hit.entity
        stats["clicks"] += 1
        stats["last_target"] = ent.name
        print(f"[Raycast Hit] Clicked entity '{ent.name}' at point {hit.point}")

        if ent.id in base_positions:
            bx, by, bz = base_positions[ent.id]

            # Tween 1: Bounce upward with elastic return
            ent.animate_position(
                target=(bx, by + 1.8, bz),
                duration=0.35,
                ease="out_quad",
                on_complete=lambda: ent.animate_position(
                    target=(bx, by, bz),
                    duration=0.55,
                    ease=out_bounce,
                ),
            )

            # Tween 2: 360-degree rotation spin
            ent.animate_rotation_y(degrees=360.0, duration=0.75, ease=out_cubic)

            # Tween 3: Scale punch
            ent.animate_scale(
                target=(1.4, 1.4, 1.4),
                duration=0.18,
                ease="out_quad",
                on_complete=lambda: ent.animate_scale(
                    target=(1.0, 1.0, 1.0),
                    duration=0.35,
                    ease="in_out_quad",
                ),
            )

        # Procedural 3D audio feedback
        try:
            if hasattr(app.audio, "play_hit_chime"):
                app.audio.play_hit_chime(hit.point.x, hit.point.y, hit.point.z)
        except Exception:
            pass

    frame_count = 0

    # 7. Per-frame UI Rendering & automated test mode
    @app.on_update
    def update(dt: float):
        nonlocal frame_count
        frame_count += 1

        # Render 2D UI Overlay commands
        app.ui.clear()
        app.ui.draw_crosshair(size=10.0, color=WHITE)
        app.ui.draw_text("VelocityEngine Interactive Sandbox", (24, 24), size=20, color=WARM_WHITE)
        app.ui.draw_text("Controls: [W/A/S/D] Walk | [SPACE] Jump | [Click] Raycast Tween", (24, 52), size=14, color=WHITE)
        app.ui.draw_text(f"Interactions: {stats['clicks']} | Last Target: {stats['last_target']}", (24, 76), size=14, color=CYAN)

        # Subtle continuous rotation of the center totem
        totem.transform.rotation.y += 20.0 * dt

        if "--test" in sys.argv and frame_count >= 60:
            print("[Test] Verified 60 frames in automated test mode. Exiting cleanly.")
            app.close()

    print("Running Interactive Sandbox demo. Press ESC to exit.")
    if __name__ == "__main__":
        app.run()
    print("Interactive Sandbox closed cleanly.")


if __name__ == "__main__":
    main()
