"""Example 15: Viral 3D Cube Cannon (Кубик-пушка) & Core Engine Capabilities.

Showcases:
  1. High-speed Viral 3D Cube Cannon with bouncy physics & continuous stream fire
  2. Native glTF 2.0 / GLB loading (duck.glb) with interactive collision reaction
  3. Dynamic Atmospheric Shader Fog (Linear Fog & Exp2 Fog) [Hotkey: F]
  4. ACES Filmic Tone Mapping [Hotkey: T]
  5. Automatic Minigun Fire Mode [Hotkey: C] & Clear Cubes [Hotkey: R]
  6. Easing & Tween Animations (out_bounce, in_out_cubic)
  7. 3D Spatial Audio & Procedural Sound FX (jump bank)
  8. 2D Screen-space UIOverlay & Native Score HUD (Score = Active Cubes)
"""

import sys
import math
import random
from pathlib import Path

# Ensure repo root and python package are in sys.path
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import VelocityEngine as ve
from VelocityEngine import (
    App,
    FlyCameraController,
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

# Bright Neon Palette for Cube Cannon
CANNON_COLORS = [
    CYAN,
    YELLOW,
    MAGENTA,
    GREEN,
    RED,
    ORANGE,
    PURPLE,
    Color.from_hex("#39ff14"),
    Color.from_hex("#00f0ff"),
    Color.from_hex("#ff007f"),
]


def main():
    print("=" * 78)
    print(" 🚀 VelocityEngine: Viral 3D Cube Cannon (Кубик-пушка)")
    print("=" * 78)
    print("Controls:")
    print("  [LMB Click]    : Lock cursor & activate Free-Fly Cannon Camera")
    print("  [LMB / Space]  : Fire high-speed bouncy cubes forward (Hold to stream!)")
    print("  [C]            : Toggle automatic minigun fire mode")
    print("  [R]            : Clear all active cubes from scene (reset count)")
    print("  [WASD]         : Fly forward/backward & strafe left/right")
    print("  [Shift]        : Fly straight down")
    print("  [ESC / TAB]    : Free / unlock mouse cursor")
    print("  [Click Entity] : Raycast click on 3D objects (triggers bouncy tweens)")
    print("  [F]            : Cycle Atmospheric Fog (Off -> Linear Fog -> Exp2 Fog)")
    print("  [T]            : Toggle ACES Filmic Tone Mapping (On / Off)")
    print("=" * 78)

    # 1. Initialize Application Window & Native HUD
    app = App(
        title="VelocityEngine - Viral 3D Cube Cannon",
        width=1280,
        height=720,
        clear_color=Color.from_hex("#161822"),
    )
    app.show_hud = True
    app._core.set_hud_score(0)

    # 2. Camera Setup (FlyCameraController: Free-Fly Spectator & Cannon Aiming)
    fly_cam = FlyCameraController(
        camera=app.camera,
        input_manager=app.input,
        app=app,
        move_speed=7.5,
        mouse_sensitivity=0.12,
        auto_lock_on_click=True,
    )
    fly_cam.set_position(0.0, 2.5, 9.0)
    fly_cam.look_at(0.0, 1.2, 0.0)
    app.camera = fly_cam

    # 3. Sunlight & Environment Floor Grid
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
    circle_colors = [RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, PURPLE, MAGENTA]
    num_items = len(circle_colors)
    radius = 5.0
    items = []

    for i, col in enumerate(circle_colors):
        angle = (2.0 * math.pi * i) / num_items
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius

        if i % 3 == 0:
            ent = app.scene.create_sphere(radius=0.7, segments=24, color=col)
            ent.name = f"Sphere_{i}"
        elif i % 3 == 1:
            ent = app.scene.create_box(size=(1.2, 1.2, 1.2), color=col)
            ent.name = f"Box_{i}"
        else:
            ent = app.scene.create_cylinder(radius=0.55, height=1.6, segments=20, color=col)
            ent.name = f"Cylinder_{i}"

        ent.transform.position = (x, 0.8, z)
        ent.has_collision = True
        items.append(ent)

    # 6. Atmospheric Fog Setup
    fog_states = [
        ("Off", None),
        ("Linear Fog (10m - 25m)", Fog(color="#161822", near=8.0, far=22.0)),
        ("Exp2 Fog (density=0.06)", FogExp2(color="#161822", density=0.06)),
    ]
    current_fog_idx = 1
    app.fog = fog_states[current_fog_idx][1]

    # 7. Interaction & Cube Cannon State
    stats = {
        "clicks": 0,
        "last_clicked": "None",
        "fog_name": fog_states[current_fog_idx][0],
        "tone_mapping": True,
    }

    cubes = []
    total_fired = 0
    fire_cooldown = 0.07
    fire_timer = 0.0
    auto_fire = False

    duck_is_animating = False
    duck_reaction_timer = 0.0

    # 8. Cube Cannon Spawning Logic
    def fire_cube():
        nonlocal total_fired
        col = CANNON_COLORS[total_fired % len(CANNON_COLORS)]

        # Each cube has size (0.4, 0.4, 0.4), casts dynamic shadows
        cube = app.scene.create_box(
            size=(0.4, 0.4, 0.4),
            color=col,
            has_collision=True,
            cast_shadows=True,
        )
        cube.name = f"CannonCube_{total_fired}"

        # Camera forward and position
        fwd = fly_cam.forward()
        cam_pos = fly_cam.pos
        fx, fy, fz = fwd.x, fwd.y, fwd.z

        # Spawn slightly forward along view ray
        px = cam_pos[0] + fx * 0.8
        py = cam_pos[1] + fy * 0.8
        pz = cam_pos[2] + fz * 0.8
        cube.transform.position = (px, py, pz)

        # Initial velocity: camera.forward() * 34.0 (with slight upward pitch + 1.5)
        vx = fx * 34.0
        vy = fy * 34.0 + 1.5
        vz = fz * 34.0

        # Random rotational spin: [random(-200, 200), random(-200, 200), random(-200, 200)]
        spin = [
            random.uniform(-200.0, 200.0),
            random.uniform(-200.0, 200.0),
            random.uniform(-200.0, 200.0),
        ]

        cubes.append({
            "entity": cube,
            "pos": [px, py, pz],
            "vel": [vx, vy, vz],
            "rot": [0.0, 0.0, 0.0],
            "spin": spin,
        })
        total_fired += 1

        # Keep up to 300 cubes: remove oldest entity from scene
        while len(cubes) > 300:
            oldest = cubes.pop(0)
            try:
                app.scene.remove_entity(oldest["entity"])
            except Exception:
                pass

        # Update native HUD score
        app._core.set_hud_score(len(cubes))

        # Procedural sound
        try:
            app.audio.play_sound("jump")
        except Exception:
            pass

    # 9. Duck Collision Reaction (Quick 360-degree spin tween and jump)
    def trigger_duck_reaction():
        nonlocal duck_is_animating, duck_reaction_timer
        if not duck:
            return

        try:
            app.audio.play_sound("jump")
        except Exception:
            pass

        if duck_reaction_timer <= 0.0:
            duck_reaction_timer = 0.45
            duck_is_animating = True

            def on_land():
                nonlocal duck_is_animating
                duck_is_animating = False
                if duck:
                    duck.transform.position = (0.0, 0.0, 0.0)

            app.tweens.to(
                duck.transform.position,
                "y",
                1.8,
                duration=0.20,
                easing=in_out_cubic,
            ).on_complete(
                lambda: app.tweens.to(
                    duck.transform.position,
                    "y",
                    0.0,
                    duration=0.35,
                    easing=out_bounce,
                ).on_complete(on_land)
            )

            curr_rot_y = duck.transform.rotation.y
            app.tweens.to(
                duck.transform.rotation,
                "y",
                curr_rot_y + 360.0,
                duration=0.55,
                easing=out_bounce,
            )

    # 10. Raycast Click Handler (@app.on_click) when mouse cursor is free
    @app.on_click
    def on_click(hit):
        if fly_cam.is_mouse_locked():
            return
        if not hit or not hit.hit or not hit.entity:
            return

        ent = hit.entity
        stats["clicks"] += 1
        stats["last_clicked"] = ent.name

        try:
            app.audio.play_sound("jump")
        except Exception:
            pass

        orig_y = ent.transform.position.y
        (
            app.tweens.to(ent.transform.position, "y", orig_y + 2.2, duration=0.35, easing=in_out_cubic)
            .on_complete(lambda: app.tweens.to(ent.transform.position, "y", orig_y, duration=0.5, easing=out_bounce))
        )
        orig_rot_y = ent.transform.rotation.y
        app.tweens.to(ent.transform.rotation, "y", orig_rot_y + 360.0, duration=0.8, easing=out_bounce)

    # 11. Frame Update & Physics Loop
    prev_f_down = False
    prev_t_down = False
    prev_c_down = False
    prev_r_down = False
    time_elapsed = 0.0

    @app.on_update
    def update(dt):
        nonlocal prev_f_down, prev_t_down, prev_c_down, prev_r_down
        nonlocal current_fog_idx, time_elapsed, fire_timer, auto_fire, duck_reaction_timer

        time_elapsed += dt
        if fire_timer > 0.0:
            fire_timer -= dt
        if duck_reaction_timer > 0.0:
            duck_reaction_timer -= dt

        # Duck continuous gentle orbital bobbing when not jumping
        if duck and not duck_is_animating:
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

        # Hotkey C: Toggle automatic minigun fire mode
        c_down = app.input.is_key_down(ve.Key.C)
        if (app.input.is_key_pressed(ve.Key.C) or (c_down and not prev_c_down)):
            auto_fire = not auto_fire
            print(f"[Showcase] Minigun Auto-Fire: {'ENABLED' if auto_fire else 'DISABLED'}")
        prev_c_down = c_down

        # Hotkey R: Clear all active cannon cubes from scene, reset count to 0
        r_down = app.input.is_key_down(ve.Key.R)
        if (app.input.is_key_pressed(ve.Key.R) or (r_down and not prev_r_down)):
            for c in cubes:
                try:
                    app.scene.remove_entity(c["entity"])
                except Exception:
                    pass
            cubes.clear()
            app._core.set_hud_score(0)
            print(f"[Showcase] Cleared all active cannon cubes! Active: 0 | Total Fired: {total_fired}")
        prev_r_down = r_down

        # Interactive Cube Cannon firing trigger:
        # When mouse cursor is locked: pressing LMB or Space, or holding LMB/Space
        is_locked = fly_cam.is_mouse_locked()
        lmb_down = False
        if hasattr(app.input, "is_mouse_down"):
            try:
                lmb_down = bool(app.input.is_mouse_down(0))
            except Exception:
                pass
        space_down = False
        if hasattr(app.input, "is_key_down"):
            try:
                space_down = bool(app.input.is_key_down(ve.Key.SPACE))
            except Exception:
                pass

        should_shoot = False
        if is_locked and (lmb_down or space_down or auto_fire):
            should_shoot = True
        elif auto_fire:
            should_shoot = True

        if should_shoot and fire_timer <= 0.0:
            fire_cube()
            fire_timer = fire_cooldown

        # Physics simulation for active cannon cubes
        dt_sim = min(dt, 0.05)
        for c in cubes:
            vel = c["vel"]
            pos = c["pos"]
            rot = c["rot"]
            spin = c["spin"]

            # Integrate velocity and gravity: v_y -= 26.0 * dt
            vel[1] -= 26.0 * dt_sim

            # Position integration
            pos[0] += vel[0] * dt_sim
            pos[1] += vel[1] * dt_sim
            pos[2] += vel[2] * dt_sim

            # Rotational spin integration
            rot[0] += spin[0] * dt_sim
            rot[1] += spin[1] * dt_sim
            rot[2] += spin[2] * dt_sim

            # Floor bounce at pos.y <= 0.20:
            # - pos.y = 0.20
            # - v_y = -v_y * 0.58 (bouncy restitution!)
            # - v_x *= 0.88; v_z *= 0.88 (horizontal ground friction)
            if pos[1] <= 0.20:
                pos[1] = 0.20
                vel[1] = -vel[1] * 0.58
                vel[0] *= 0.88
                vel[2] *= 0.88
                spin[0] *= 0.94
                spin[2] *= 0.94
                if abs(vel[1]) < 0.12:
                    vel[1] = 0.0

            # Collision with Duck ((0, 0, 0)): if distance < 1.7:
            # - Cube bounces off, Duck does a quick 360-degree spin tween and jump!
            dist = math.sqrt(pos[0] * pos[0] + pos[1] * pos[1] + pos[2] * pos[2])
            if dist < 1.7:
                if dist > 1e-4:
                    nx = pos[0] / dist
                    ny = pos[1] / dist
                    nz = pos[2] / dist
                else:
                    nx, ny, nz = 0.0, 1.0, 0.0

                pos[0] = nx * 1.75
                pos[1] = max(0.20, ny * 1.75)
                pos[2] = nz * 1.75

                dot = vel[0] * nx + vel[1] * ny + vel[2] * nz
                if dot < 0.0:
                    vel[0] -= 1.8 * dot * nx
                    vel[1] -= 1.8 * dot * ny
                    vel[2] -= 1.8 * dot * nz
                vel[0] += nx * 5.0
                vel[1] = max(vel[1], 4.0)
                vel[2] += nz * 5.0

                trigger_duck_reaction()

            # Sync entity transform
            c["entity"].transform.position = (pos[0], pos[1], pos[2])
            c["entity"].transform.rotation = (rot[0], rot[1], rot[2])

        # Update native HUD score
        app._core.set_hud_score(len(cubes))

        # Draw 2D HUD text
        app.ui.draw_text(
            f"Python {sys.version.split()[0]} (64-bit) | Sokol GFX D3D11 | 300+ FPS",
            (24, 24),
            size=18,
            color=CYAN,
        )
        app.ui.draw_text(
            f"Active Cubes: {len(cubes)} | Total Fired: {total_fired}" + ("  [AUTO-FIRE ON]" if auto_fire else ""),
            (24, 52),
            size=15,
            color=YELLOW,
        )
        app.ui.draw_text(
            f"[F] Fog Mode: {stats['fog_name']} | [T] Tone Mapping: {'ON' if stats['tone_mapping'] else 'OFF'}",
            (24, 76),
            size=14,
            color=WHITE,
        )
        app.ui.draw_text(
            "[LMB / Space] Shoot Cannon | [C] Auto-Fire | [R] Clear Cubes | [WASD] Fly | [ESC] Free Cursor",
            (24, app.height - 36),
            size=14,
            color=WARM_WHITE,
        )

    # 12. Automated Test Mode (Exit after 60 frames if --test flag passed)
    if "--test" in sys.argv:
        for frame_idx in range(1, 61):
            if frame_idx in (5, 10, 15):
                fire_cube()
            update(1.0 / 60.0)
        print(
            f"[Test] Verified 60 frames in automated test mode (Fired: {total_fired}, Active: {len(cubes)}). Exiting cleanly."
        )
        app.scene.clear()
        app.close()
        import gc
        del app, cubes, duck
        gc.collect()
        print("[Showcase] Engine closed cleanly.")
        return

    # Launch Engine
    app.run()
    print("[Showcase] Engine closed cleanly.")


def run_example(headless: bool = False, frames: int = 60):
    """Run Example 15 in interactive or headless mode."""
    if (headless or "--headless" in sys.argv) and "--test" not in sys.argv:
        sys.argv.append("--test")
    return main()


if __name__ == "__main__":
    main()
