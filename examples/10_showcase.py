"""VelocityEngine Showcase: Comprehensive Demonstration of Core Capabilities.

Showcases:
  1. Three.js Pythonic API (App, OrbitController, SceneFactory, Primitives)
  2. Native glTF 2.0 / GLB loading (duck.glb)
  3. Dynamic Atmospheric Shader Fog (Linear Fog & Exp2 Fog) [Hotkey: F]
  4. ACES Filmic Tone Mapping [Hotkey: T]
  5. BoundingSphere Raycast Pre-Pass & Mouse Picking (@app.on_click)
  6. Easing & Tween Animations (out_bounce, in_out_cubic)
  7. 3D Spatial Audio & Procedural Sound FX
  8. 2D Screen-space UIOverlay & Live Metrics
"""

import sys
import math
from pathlib import Path

# Ensure repo root and python package are in sys.path
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import VelocityEngine as ve
from VelocityEngine import (
    App,
    OrbitController,
    Fog,
    FogExp2,
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
    in_out_cubic,
)


def main():
    print("=" * 78)
    print(" 🌌 VelocityEngine: Full Capabilities Showcase")
    print("=" * 78)
    print("Controls:")
    print("  [LMB Drag]     : Orbit camera around scene")
    print("  [Scroll Wheel] : Smooth zoom in / out")
    print("  [LMB Click]    : Raycast click on 3D objects (triggers bouncy tweens & audio)")
    print("  [F]            : Cycle Atmospheric Fog (Off -> Linear Fog -> Exp2 Fog)")
    print("  [T]            : Toggle ACES Filmic Tone Mapping (On / Off)")
    print("  [ESC]          : Exit application")
    print("=" * 78)

    # 1. Initialize Application Window
    app = App(
        title="VelocityEngine - Full Showcase (Three.js Parity)",
        width=1280,
        height=720,
        clear_color=Color.from_hex("#161822"),
    )

    # 2. Camera Setup (OrbitController with smooth damping)
    orbit = OrbitController(
        target=(0.0, 1.2, 0.0),
        distance=9.5,
        min_distance=2.0,
        max_distance=30.0,
        damping=0.08,
    )
    app.camera = orbit

    # 3. Sunlight & Environment Grid
    app.scene.set_sun(direction=(-1.0, -2.5, -1.2), color=WARM_WHITE, intensity=1.5)
    app.scene.create_grid(size=40.0, step=1.0, color=Color.from_hex("#252838"))

    # 4. Load 3D glTF Model in Center
    duck_path = str(repo_root / "assets" / "duck.glb")
    try:
        duck = app.scene.load_model(duck_path)
        duck.transform.position = (0.0, 0.0, 0.0)
        duck.transform.scale = (1.4, 1.4, 1.4)
        duck.name = "CentralDuck"
    except Exception as e:
        print(f"[Showcase] Warning: Could not load duck model: {e}")
        duck = None

    # 5. Create Circling Procedural 3D Primitives (Boxes, Spheres, Cylinders)
    colors = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE, MAGENTA]
    num_items = len(colors)
    radius = 5.0
    items = []

    for i, col in enumerate(colors):
        angle = (2.0 * math.pi * i) / num_items
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius

        if i % 3 == 0:
            # Sphere
            ent = app.scene.create_sphere(radius=0.7, segments=24, color=col)
            ent.name = f"Sphere_{i}"
        elif i % 3 == 1:
            # Box
            ent = app.scene.create_box(size=(1.2, 1.2, 1.2), color=col)
            ent.name = f"Box_{i}"
        else:
            # Cylinder
            ent = app.scene.create_cylinder(radius=0.55, height=1.6, segments=20, color=col)
            ent.name = f"Cylinder_{i}"

        ent.transform.position = (x, 0.8, z)
        ent.has_collision = True
        items.append((ent, (x, 0.8, z)))

    # 6. Atmospheric Fog Setup
    fog_states = [
        ("Off", None),
        ("Linear Fog (10m - 25m)", Fog(color="#161822", near=8.0, far=22.0)),
        ("Exp2 Fog (density=0.06)", FogExp2(color="#161822", density=0.06)),
    ]
    current_fog_idx = 1
    app.fog = fog_states[current_fog_idx][1]

    # 7. Interaction State & Metrics
    stats = {
        "clicks": 0,
        "last_clicked": "None",
        "fog_name": fog_states[current_fog_idx][0],
        "tone_mapping": True,
    }

    # 8. Raycast Click Handler (@app.on_click) using BoundingSphere Pre-Pass
    @app.on_click
    def on_click(hit):
        if not hit or not hit.hit or not hit.entity:
            return

        ent = hit.entity
        stats["clicks"] += 1
        stats["last_clicked"] = ent.name

        # Play procedural sound FX
        try:
            app.audio.play_sound("jump")
        except Exception:
            pass

        # Trigger bouncy jump tween (out_bounce)
        orig_y = ent.transform.position.y
        (
            app.tweens.to(ent.transform.position, "y", orig_y + 2.2, duration=0.35, easing=in_out_cubic)
            .on_complete(lambda: app.tweens.to(ent.transform.position, "y", orig_y, duration=0.5, easing=out_bounce))
        )

        # Trigger 360 degree spin tween
        orig_rot_y = ent.transform.rotation.y
        app.tweens.to(ent.transform.rotation, "y", orig_rot_y + 360.0, duration=0.8, easing=out_bounce)

    # 9. Frame Update & Input Handling (Hotkeys: F, T)
    prev_f_down = False
    prev_t_down = False
    time_elapsed = 0.0

    @app.on_update
    def update(dt):
        nonlocal prev_f_down, prev_t_down, current_fog_idx, time_elapsed
        time_elapsed += dt

        # Continuous gentle orbital bobbing for duck
        if duck:
            duck.transform.rotation = (0.0, time_elapsed * 30.0, 0.0)

        # Hotkey F: Cycle Fog
        f_down = app.input.is_key_down(ve.Key.F)
        if f_down and not prev_f_down:
            current_fog_idx = (current_fog_idx + 1) % len(fog_states)
            stats["fog_name"] = fog_states[current_fog_idx][0]
            app.fog = fog_states[current_fog_idx][1]
            print(f"[Showcase] Switched Fog Mode: {stats['fog_name']}")
        prev_f_down = f_down

        # Hotkey T: Toggle Tone Mapping
        t_down = app.input.is_key_down(ve.Key.T)
        if t_down and not prev_t_down:
            app.tone_mapping = not app.tone_mapping
            stats["tone_mapping"] = app.tone_mapping
            print(f"[Showcase] ACES Tone Mapping: {'ON' if app.tone_mapping else 'OFF'}")
        prev_t_down = t_down

        # Draw 2D HUD Info Overlay
        app.ui.draw_text("VelocityEngine 3D Showcase (C++20 + Sokol + Nanobind)", (24, 24), size=18, color=CYAN)
        app.ui.draw_text(f"[F] Fog Mode: {stats['fog_name']}", (24, 52), size=14, color=WHITE)
        app.ui.draw_text(f"[T] ACES Filmic Tone Mapping: {'ENABLED' if stats['tone_mapping'] else 'DISABLED'}", (24, 74), size=14, color=WHITE)
        app.ui.draw_text(f"Raycast Clicks: {stats['clicks']} | Last: {stats['last_clicked']}", (24, 96), size=14, color=YELLOW)
        app.ui.draw_text("[LMB Drag] Orbit Cam | [Scroll] Zoom | [Click] Animate Shape", (24, app.height - 36), size=14, color=WARM_WHITE)

    # 10. Automated Test Mode (Exit after 60 frames if --test flag passed)
    if "--test" in sys.argv:
        test_frames = [0]
        def test_step(dt):
            test_frames[0] += 1
            if test_frames[0] >= 60:
                print("[Test] Verified 60 frames in automated test mode. Exiting cleanly.")
                app.close()
        app.on_update(test_step)

    # Launch Engine
    app.run()
    print("[Showcase] Engine closed cleanly.")


if __name__ == "__main__":
    main()
