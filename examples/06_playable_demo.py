"""Milestone 7: Polished First-Person 3D Demo with Daylight, Soft Shadows, Audio & HUD.

Features:
  - Daylight Atmosphere: #6ea0d0 sky-blue clear color, warm golden directional sunlight
  - Hemispheric Ambient Light: sky blue bounce from above, warm earth bounce from below
  - Dynamic Soft Shadows: 2048x2048 shadow map pass, 3x3 PCF filter, normal offset bias
  - Spatial 3D Audio (miniaudio): procedural rhythmic footsteps, jump sound, 3D hit chimes
  - 2D HUD: minimalist screen-center crosshair, on-screen FPS and Score display, control hints
  - Depenetration & Sub-stepping: Minimum Translation Vector (MTV) resolving corner collisions
  - Debug Hitboxes: Press F1 to toggle green wireframe AABB bounding boxes
"""

import math
import sys
from pathlib import Path

# Ensure 'python' package dir is available if running directly from repo root
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import engine
from engine import (
    Key,
    Material,
    Texture,
    Vec3,
    AABB,
    Ray,
    FirstPersonController,
)


def ensure_desktop_access():
    if sys.platform == "win32":
        try:
            import ctypes
            u32 = ctypes.windll.user32
            hdesk = u32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                u32.SetThreadDesktop(hdesk)
        except Exception:
            pass


def main():
    ensure_desktop_access()
    print("=" * 80)
    print(" Engine 3D: Milestone 7 - Polished First-Person Game (Daylight, Shadows, Audio)")
    print("=" * 80)
    print("Controls:")
    print("  [Mouse]       : Look around (Mouse Lock active by default)")
    print("  [W / A / S / D]: Walk Forward / Left / Backward / Right")
    print("  [SPACE]       : Jump (with vertical gravity & audio)")
    print("  [L-SHIFT]     : Sprint")
    print("  [LMB (Click)] : Raycast Interact with objects (bounce, flash, 3D spatial chime)")
    print("  [TAB]         : Toggle Mouse Lock / Free Cursor")
    print("  [F1]          : Toggle AABB Hitbox Debug Wireframes")
    print("  [ESC]         : Exit Application")
    print("=" * 80)

    app = engine.App(
        title="Engine 3D: Milestone 8 - Colliders, MSAA & Polish",
        width=960,
        height=720,
        clear_color=[0.4314, 0.6275, 0.8235, 1.0],  # Daylight sky blue #6ea0d0
    )

    if "--debug-hitboxes" in sys.argv:
        app.show_debug_hitboxes = True

    # 1. Daylight Atmosphere & Hemispheric Ambient Lighting Setup
    app.scene.light.set_direction(-0.45, -0.85, -0.45)
    app.scene.light.set_color(1.15, 1.08, 0.95)   # Warm golden sunlight
    app.scene.light.intensity = 1.35
    app.scene.light.set_hemispheric_ambient(0.52, 0.62, 0.78, 0.26, 0.22, 0.20)

    # 2. Textures & Materials (Soft light-gray tile floor with Mipmaps)
    floor_tex = Texture.create_checkerboard(
        width=128, height=128, tile_size=16,
        color1=0xFF9A9AA2, color2=0xFF7A7A85
    )
    floor_mat = Material(floor_tex, roughness=0.82, metallic=0.0)
    floor_mat.base_color = (0.85, 0.85, 0.88, 1.0)

    wall_tex = Texture.create_checkerboard(
        width=64, height=64, tile_size=8,
        color1=0xFF585E70, color2=0xFF424755
    )
    wall_mat = Material(wall_tex, roughness=0.88, metallic=0.05)

    gold_mat = Material(wall_tex, roughness=0.22, metallic=0.85)
    gold_mat.base_color = (1.0, 0.82, 0.28, 1.0)

    ruby_mat = Material(wall_tex, roughness=0.30, metallic=0.15)
    ruby_mat.base_color = (0.92, 0.22, 0.25, 1.0)

    cyan_mat = Material(wall_tex, roughness=0.25, metallic=0.35)
    cyan_mat.base_color = (0.22, 0.88, 0.88, 1.0)

    # 3. Arena Architecture
    floor = app.scene.create_plane(size=32.0, uv_tiling=16.0, material=floor_mat)
    floor.name = "FloorPlane"
    floor.transform.position = (0.0, 0.0, 0.0)
    floor.cast_shadows = False  # Floor receives shadows without self-shadow acne

    def create_wall(name: str, pos: tuple, scale: tuple, mat: Material):
        w = app.scene.create_cube()
        w.name = name
        w.material = mat
        w.transform.position = pos
        w.transform.scale = scale
        return w

    # 4 Perimeter Boundary Walls
    create_wall("Wall_North", (0.0, 1.5, 16.0), (16.0, 1.5, 0.5), wall_mat)
    create_wall("Wall_South", (0.0, 1.5, -16.0), (16.0, 1.5, 0.5), wall_mat)
    create_wall("Wall_East",  (16.0, 1.5, 0.0),  (0.5, 1.5, 16.0), wall_mat)
    create_wall("Wall_West",  (-16.0, 1.5, 0.0), (0.5, 1.5, 16.0), wall_mat)

    # Obstacle Pillars / Platforms
    pillar1 = create_wall("Pillar_Gold", (-4.5, 1.25, 4.5), (0.9, 1.25, 0.9), gold_mat)
    pillar2 = create_wall("Pillar_Ruby", (4.5, 1.25, 4.5), (0.9, 1.25, 0.9), ruby_mat)
    pillar3 = create_wall("Pillar_Cyan", (0.0, 0.6, -2.5), (1.5, 0.6, 0.8), cyan_mat)

    # 4. Load 3D Models into Arena
    assets_dir = repo_root / "assets"

    # Model 1: Duck (Center Pedestal - pedestal is slim so duck shadow falls on pedestal and cascades to floor)
    duck_pedestal = create_wall("Duck_Pedestal", (0.0, 0.25, 4.0), (0.75, 0.25, 0.75), wall_mat)
    duck = app.scene.load_model(str(assets_dir / "duck.glb"))
    duck.name = "DuckModel"
    duck.transform.scale = (1.0, 1.0, 1.0)
    duck.transform.position = (0.0, 0.50, 4.0)
    duck.set_collision_scale(0.78)

    # Model 2: Textured Box
    box = app.scene.load_model(str(assets_dir / "box_textured.glb"))
    box.name = "BoxModel"
    box.transform.scale = (1.1, 1.1, 1.1)
    box.transform.position = (-4.5, 0.55, -3.5)
    box.set_collision_scale(0.85)

    # Model 3: Avocado
    avocado = app.scene.load_model(str(assets_dir / "avocado.glb"))
    avocado.name = "AvocadoModel"
    avocado.transform.scale = (22.0, 22.0, 22.0)
    avocado.transform.position = (4.5, 0.0, -3.5)
    avocado.set_collision_scale(0.75)

    # 5. Setup Camera & First-Person Controller with Audio Integration
    app.camera.set_position(0.0, 1.7, -8.0)
    app.camera.set_target(0.0, 1.7, 0.0)

    controller = FirstPersonController(
        camera=app.camera,
        input_manager=app.input,
        scene=app.scene,
        audio=app.audio,
        move_speed=5.2,
        mouse_sensitivity=0.12,
        gravity=16.0,
        jump_speed=6.2,
        player_height=1.7,
        player_radius=0.35,
        step_height=0.20,
    )

    bouncing_objects = {}

    def trigger_bounce(entity, jump_vel=5.5):
        orig_y = entity.transform.position.y
        if entity not in bouncing_objects:
            bouncing_objects[entity] = {"vy": jump_vel, "base_y": orig_y}

    last_lmb_down = False
    last_tab_down = False
    last_f1_down = False
    score = 0
    frame_count = 0

    # 6. Game Loop Update
    @app.on_update
    def update(dt: float):
        nonlocal last_lmb_down, last_tab_down, last_f1_down, score, frame_count
        frame_count += 1
        if frame_count == 1 and "--test" not in sys.argv:
            app.set_mouse_locked(True)

        # Toggle Mouse Lock with TAB
        tab_down = app.input.is_key_down(Key.TAB)
        if tab_down and not last_tab_down:
            new_lock = not app.is_mouse_locked()
            app.set_mouse_locked(new_lock)
            print(f"[Input] Mouse Locked: {new_lock}")
        last_tab_down = tab_down

        # Toggle Hitbox Wireframe with F1
        f1_down = app.input.is_key_down(Key.F1)
        if f1_down and not last_f1_down:
            app.show_debug_hitboxes = not app.show_debug_hitboxes
            print(f"[Debug] Show Hitboxes: {app.show_debug_hitboxes}")
        last_f1_down = f1_down

        # Update Player Controller (with sub-stepping, depenetration & footstep sound)
        controller.update(dt)

        # Handle Raycast Interaction on Left Mouse Button Press
        lmb_down = app.input.is_mouse_down(0)
        if lmb_down and not last_lmb_down:
            ray = Ray(app.camera.position, app.camera.forward())
            hit = app.scene.raycast(ray, max_distance=25.0)

            if hit.hit and hit.entity:
                target = hit.entity
                while getattr(target, "parent", None) is not None:
                    target = target.parent

                is_static = any(k in target.name.lower() for k in ("wall", "floor", "plane"))
                if not is_static:
                    score += 10
                    app.hud_score = score
                    hit_name = hit.entity.name
                    print(
                        f"🎯 [Raycast HIT!] Object: '{hit_name}' | "
                        f"Dist: {hit.distance:.2f}m | Point: ({hit.point.x:.1f}, {hit.point.y:.1f}, {hit.point.z:.1f}) | Score: {score}"
                    )
                    trigger_bounce(target, jump_vel=4.5)
                    # Play 3D spatial chime at exact world contact point
                    app.audio.play_hit_3d(hit.point)

                    if hit.entity.material:
                        hit.entity.set_color(1.4, 1.4, 0.5, 1.0)
                else:
                    print(f"🧱 [Hit Structure] Object: '{hit.entity.name}' | Dist: {hit.distance:.2f}m")
        last_lmb_down = lmb_down

        # Animate bouncing objects
        ended_bounces = []
        for entity, state in bouncing_objects.items():
            state["vy"] -= 18.0 * dt
            pos = entity.transform.position
            new_y = pos.y + state["vy"] * dt
            if new_y <= state["base_y"]:
                new_y = state["base_y"]
                ended_bounces.append(entity)
            entity.transform.position = (pos.x, new_y, pos.z)

        for e in ended_bounces:
            del bouncing_objects[e]

        # Rotate models slowly for ambient dynamic effect
        duck.transform.rotation.y += 20.0 * dt
        box.transform.rotation.y += 25.0 * dt
        avocado.transform.rotation.y -= 18.0 * dt

        # Update window title with live metrics periodically
        if frame_count % 30 == 0:
            cur_fps = 1.0 / dt if dt > 0 else 0.0
            app.set_title(f"Engine 3D: Milestone 8 | FPS: {cur_fps:.0f} | Score: {score}")

        if frame_count % 120 == 0 or ("--test" in sys.argv and frame_count >= 60):
            pos = app.camera.position
            print(
                f"[Frame {frame_count:04d}] PlayerPos=({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}) | "
                f"Yaw={app.camera.yaw:.1f}° Pitch={app.camera.pitch:.1f}° | Score={score} | FPS={1.0 / dt if dt > 0 else 0.0:.1f}"
            )

        if "--screenshot" in sys.argv:
            if frame_count == 40:
                print("[Screenshot] Capturing game screen via direct computer-use...", flush=True)
                sys.path.append("C:/Users/Admin/.gemini/config/skills/computer-use/scripts")
                from computer import get_windows, capture_rect
                png_name = "milestone8_hitboxes_f1.png" if "--debug-hitboxes" in sys.argv else "milestone8_visual_polish.png"
                out_png = f"C:/Users/Admin/.gemini/antigravity-cli/brain/652d8d55-b5ed-48f3-a093-40b0b4448338/{png_name}"
                target = None
                for w in get_windows():
                    if "Engine 3D" in w["title"]:
                        target = w
                        break
                if target:
                    print(f"[Screenshot] Found window '{target['title']}' at ({target['x']}, {target['y']}, {target['width']}, {target['height']})", flush=True)
                    img = capture_rect(target["x"], target["y"], target["width"], target["height"])
                else:
                    print("[Screenshot] Window not found in list, capturing primary monitor...", flush=True)
                    img = capture_rect(0, 0, 1920, 1080)
                img.save(out_png, "PNG")
                print(f"[Screenshot] Screen capture saved successfully to: {out_png}", flush=True)
            elif frame_count >= 50:
                app.close()

        if "--test" in sys.argv and frame_count >= 60:
            print("[Test] Reached 60 frames in automated test mode. Exiting cleanly.")
            app.close()

    print("Running Milestone 7 Playable Demo. Press ESC to exit.")
    app.run()
    print("Demo exited cleanly.")


if __name__ == "__main__":
    main()
