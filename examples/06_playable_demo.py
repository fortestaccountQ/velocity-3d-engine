"""Milestone 6: Playable First-Person 3D Demo with AABB Collisions & Raycast Interactions.

Features:
  - First-Person Controller (W/A/S/D walking, Space jumping, Shift sprint)
  - Smooth Mouse Look with Pitch/Yaw clamping and cursor lock (Toggle with TAB / ESC)
  - C++ AABB Physics: sliding along walls, landing on obstacles, standing on floor
  - Real-time C++ Raycast on Left Mouse Click:
      * Highlights target entities
      * Triggers physical bounce / jump animation on objects
  - Enclosed arena with boundary walls, crates/pillars, and loaded 3D models (Duck, Box, Avocado)
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


def main():
    print("=" * 80)
    print(" Engine 3D: Milestone 6 - Playable First-Person Demo")
    print("=" * 80)
    print("Controls:")
    print("  [Mouse]       : Look around (Mouse Lock active by default)")
    print("  [W / A / S / D]: Walk Forward / Left / Backward / Right")
    print("  [SPACE]       : Jump (with vertical gravity & landing)")
    print("  [L-SHIFT]     : Sprint")
    print("  [LMB (Click)] : Raycast Interact with objects (bounce & color flash)")
    print("  [TAB]         : Toggle Mouse Lock / Free Cursor")
    print("  [ESC]         : Exit Application")
    print("=" * 80)

    app = engine.App(
        title="Engine 3D: Milestone 6 - First-Person Game Demo",
        width=960,
        height=720,
        clear_color=[0.08, 0.09, 0.12, 1.0],
    )

    # 1. Lighting Setup
    app.scene.light.direction = (0.5, -1.0, 0.4)
    app.scene.light.color = (1.0, 0.98, 0.92)
    app.scene.light.intensity = 1.35
    app.scene.light.ambient = (0.22, 0.22, 0.26)

    # 2. Textures & Materials
    floor_tex = Texture.create_checkerboard(
        width=128, height=128, tile_size=16,
        color1=0xFF262832, color2=0xFF181A22
    )
    floor_mat = Material(floor_tex, roughness=0.85, metallic=0.0)
    floor_mat.base_color = (0.9, 0.9, 0.95, 1.0)

    wall_tex = Texture.create_checkerboard(
        width=64, height=64, tile_size=8,
        color1=0xFF4A4E5C, color2=0xFF383B46
    )
    wall_mat = Material(wall_tex, roughness=0.9, metallic=0.05)

    gold_mat = Material(wall_tex, roughness=0.2, metallic=0.85)
    gold_mat.base_color = (1.0, 0.82, 0.25, 1.0)

    ruby_mat = Material(wall_tex, roughness=0.3, metallic=0.1)
    ruby_mat.base_color = (0.9, 0.2, 0.2, 1.0)

    cyan_mat = Material(wall_tex, roughness=0.25, metallic=0.3)
    cyan_mat.base_color = (0.2, 0.85, 0.85, 1.0)

    # 3. Arena Architecture
    # Floor (30 x 30 units)
    floor = app.scene.create_plane(size=30.0, uv_tiling=15.0, material=floor_mat)
    floor.name = "FloorPlane"
    floor.transform.position = (0.0, 0.0, 0.0)

    # Helper to create boundary wall blocks
    def create_wall(name: str, pos: tuple, scale: tuple, mat: Material):
        w = app.scene.create_cube()
        w.name = name
        w.material = mat
        w.transform.position = pos
        w.transform.scale = scale
        return w

    # 4 Perimeter Boundary Walls
    create_wall("Wall_North", (0.0, 1.5, 15.0), (15.0, 1.5, 0.5), wall_mat)
    create_wall("Wall_South", (0.0, 1.5, -15.0), (15.0, 1.5, 0.5), wall_mat)
    create_wall("Wall_East",  (15.0, 1.5, 0.0),  (0.5, 1.5, 15.0), wall_mat)
    create_wall("Wall_West",  (-15.0, 1.5, 0.0), (0.5, 1.5, 15.0), wall_mat)

    # Obstacle Pillars / Crates in the Arena
    pillar1 = create_wall("Pillar_Gold", (-4.5, 1.25, 4.5), (0.9, 1.25, 0.9), gold_mat)
    pillar2 = create_wall("Pillar_Ruby", (4.5, 1.25, 4.5), (0.9, 1.25, 0.9), ruby_mat)
    pillar3 = create_wall("Pillar_Cyan", (0.0, 0.6, -2.5), (1.5, 0.6, 0.8), cyan_mat)

    # 4. Load 3D Models into Arena
    assets_dir = repo_root / "assets"

    # Model 1: Duck (Center Pedestal)
    duck_pedestal = create_wall("Duck_Pedestal", (0.0, 0.4, 4.0), (1.2, 0.4, 1.2), wall_mat)
    duck = app.scene.load_model(str(assets_dir / "duck.glb"))
    duck.name = "DuckModel"
    duck.transform.scale = (1.0, 1.0, 1.0)
    duck.transform.position = (0.0, 0.8, 4.0)

    # Model 2: Textured Box
    box = app.scene.load_model(str(assets_dir / "box_textured.glb"))
    box.name = "BoxModel"
    box.transform.scale = (1.1, 1.1, 1.1)
    box.transform.position = (-4.5, 0.55, -3.5)

    # Model 3: Avocado
    avocado = app.scene.load_model(str(assets_dir / "avocado.glb"))
    avocado.name = "AvocadoModel"
    avocado.transform.scale = (22.0, 22.0, 22.0)
    avocado.transform.position = (4.5, 0.0, -3.5)

    # 5. Setup Camera & First-Person Controller
    app.camera.set_position(0.0, 1.7, -8.0)
    app.camera.set_target(0.0, 1.7, 0.0)

    controller = FirstPersonController(
        camera=app.camera,
        input_manager=app.input,
        scene=app.scene,
        move_speed=5.2,
        mouse_sensitivity=0.12,
        gravity=16.0,
        jump_speed=6.2,
        player_height=1.7,
        player_radius=0.35,
    )

    # Lock mouse initially for FPS gameplay
    if "--test" not in sys.argv:
        app.set_mouse_locked(True)

    # Interactive bouncing animations dict: entity -> { 'vy': float, 'orig_y': float }
    bouncing_objects = {}

    def trigger_bounce(entity, jump_vel=5.5):
        orig_y = entity.transform.position.y
        if entity not in bouncing_objects:
            bouncing_objects[entity] = {"vy": jump_vel, "base_y": orig_y}

    last_lmb_down = False
    last_tab_down = False
    score = 0
    frame_count = 0

    # 6. Game Loop Update
    @app.on_update
    def update(dt: float):
        nonlocal last_lmb_down, last_tab_down, score, frame_count
        frame_count += 1

        # Toggle Mouse Lock with TAB
        tab_down = app.input.is_key_down(Key.TAB)
        if tab_down and not last_tab_down:
            new_lock = not app.is_mouse_locked()
            app.set_mouse_locked(new_lock)
            print(f"[Input] Mouse Locked: {new_lock}")
        last_tab_down = tab_down

        # Update Player Controller
        controller.update(dt)

        # Handle Raycast Interaction on Left Mouse Button Press
        lmb_down = app.input.is_mouse_down(0)
        if lmb_down and not last_lmb_down:
            # Cast ray straight from center of screen (camera eye along forward direction)
            ray = Ray(app.camera.position, app.camera.forward())
            hit = app.scene.raycast(ray, max_distance=25.0)

            if hit.hit and hit.entity:
                score += 10
                hit_name = hit.entity.name
                print(
                    f"🎯 [Raycast HIT!] Object: '{hit_name}' | "
                    f"Dist: {hit.distance:.2f}m | Point: ({hit.point.x:.1f}, {hit.point.y:.1f}, {hit.point.z:.1f}) | Score: {score}"
                )

                # Visual feedback: flash color and bounce model / object
                target = hit.entity
                while target.parent and target.parent.parent:
                    target = target.parent
                trigger_bounce(target, jump_vel=4.5)

                if hit.entity.material:
                    hit.entity.set_color(1.4, 1.4, 0.5, 1.0)
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

        if frame_count % 120 == 0 or ("--test" in sys.argv and frame_count >= 60):
            pos = app.camera.position
            print(
                f"[Frame {frame_count:04d}] PlayerPos=({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}) | "
                f"Yaw={app.camera.yaw:.1f}° Pitch={app.camera.pitch:.1f}° | Score={score} | FPS={1.0 / dt if dt > 0 else 0.0:.1f}"
            )

        if "--test" in sys.argv and frame_count >= 60:
            print("[Test] Reached 60 frames in automated test mode. Exiting cleanly.")
            app.close()

    print("Running Milestone 6 Playable Demo. Press ESC to exit.")
    app.run()
    print("Demo exited cleanly.")


if __name__ == "__main__":
    main()
