"""Milestone 5: glTF 2.0 / GLB 3D Model Loading Showcase.

Demonstrates:
  - Loading monolithic binary .glb models with embedded textures and geometry
  - Hierarchical node transforms and mesh primitives via cgltf
  - Multiple models rendered concurrently with textures and PBR-lite lighting:
      * Center: Iconic Duck model (assets/duck.glb, ~12.6k indices)
      * Left: Textured Box (assets/box_textured.glb)
      * Right: High-detail Avocado (assets/avocado.glb)
  - Interactive Camera (W/S/A/D) and dynamic orbiting light
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
from engine import Key, Material, Texture


def main():
    print("=" * 80)
    print(" Engine 3D: Milestone 5 - glTF 2.0 / GLB Model Loading Showcase")
    print("=" * 80)
    print("Models Loaded:")
    print("  [1] Center : Duck (assets/duck.glb) - 12,636 indices, embedded albedo texture")
    print("  [2] Left   : Textured Box (assets/box_textured.glb) - Cube with UV unwrap")
    print("  [3] Right  : Avocado (assets/avocado.glb) - High-res PBR scan")
    print("Controls:")
    print("  [W / S]    : Move Camera Forward / Backward")
    print("  [A / D]    : Move Camera Left / Right")
    print("  [ESC]      : Exit Application")
    print("=" * 80)

    app = engine.App(
        title="Engine 3D: glTF 2.0 / GLB Model Loading (Milestone 5)",
        width=960,
        height=720,
        clear_color=[0.06, 0.07, 0.10, 1.0],
    )

    # 1. Setup Camera (framing all three models nicely on the floor)
    app.camera.position = (0.0, 2.6, 6.2)
    app.camera.target = (0.0, 0.7, 0.0)

    # 2. Setup Lighting (warm key light + subtle ambient fill)
    app.scene.light.color = (1.0, 0.96, 0.90)
    app.scene.light.intensity = 1.35
    app.scene.light.ambient = (0.22, 0.22, 0.28)

    # 3. Floor Plane with Dark Elegant Checkerboard
    floor_tex = Texture.create_checkerboard(
        width=128, height=128, tile_size=16,
        color1=0xFF22242D, color2=0xFF16171F
    )
    floor_mat = Material(floor_tex, roughness=0.85, metallic=0.0)
    floor_mat.base_color = (0.85, 0.85, 0.90, 1.0)
    floor = app.scene.create_plane(size=18.0, uv_tiling=9.0, material=floor_mat)
    floor.name = "FloorPlane"
    floor.transform.position = (0.0, 0.0, 0.0)

    # 4. Load glTF 2.0 / GLB Models
    assets_dir = repo_root / "assets"

    # [Model 1] Center: Iconic Duck
    duck_path = str(assets_dir / "duck.glb")
    print(f"Loading '{duck_path}'...")
    duck_model = app.scene.load_model(duck_path)
    # duck.glb node hierarchy already applies 0.01 scale, giving natural height of ~1.64m
    duck_model.transform.scale = (1.0, 1.0, 1.0)
    duck_model.transform.position = (0.0, 0.0, 0.0)
    print(f"  -> Duck loaded: {len(duck_model.meshes)} mesh primitive(s)")

    # [Model 2] Left: Textured Box
    box_path = str(assets_dir / "box_textured.glb")
    print(f"Loading '{box_path}'...")
    box_model = app.scene.load_model(box_path)
    box_model.transform.scale = (1.1, 1.1, 1.1)
    box_model.transform.position = (-2.5, 0.55, 0.0)
    print(f"  -> Box loaded: {len(box_model.meshes)} mesh primitive(s)")

    # [Model 3] Right: High-Res Avocado
    avocado_path = str(assets_dir / "avocado.glb")
    print(f"Loading '{avocado_path}'...")
    avocado_model = app.scene.load_model(avocado_path)
    # Raw avocado height is ~0.063m, scale by 24.0 gives ~1.5 units
    avocado_model.transform.scale = (24.0, 24.0, 24.0)
    avocado_model.transform.position = (2.7, 0.0, 0.0)
    print(f"  -> Avocado loaded: {len(avocado_model.meshes)} mesh primitive(s)")

    frame_count = 0
    light_angle = 0.0

    # 5. Interactive Update Callback
    @app.on_update
    def update(dt: float):
        nonlocal frame_count, light_angle
        frame_count += 1
        light_angle += 0.6 * dt

        # Orbit light to highlight dynamic PBR reflections on all models
        lx = math.cos(light_angle) * 0.9
        lz = math.sin(light_angle) * 0.9
        app.scene.light.direction = (lx, -1.0, lz)

        # Smoothly rotate models
        duck_model.transform.rotation.y += 25.0 * dt
        box_model.transform.rotation.y += 35.0 * dt
        box_model.transform.rotation.x += 12.0 * dt
        avocado_model.transform.rotation.y -= 20.0 * dt

        # Interactive Camera Controls via W / S / A / D
        cam_speed = 4.5 * dt
        if app.input.is_key_down(Key.W):
            app.camera.move_forward(cam_speed)
        if app.input.is_key_down(Key.S):
            app.camera.move_forward(-cam_speed)
        if app.input.is_key_down(Key.A):
            app.camera.move_right(-cam_speed)
        if app.input.is_key_down(Key.D):
            app.camera.move_right(cam_speed)

        if frame_count % 120 == 0 or ("--test" in sys.argv and frame_count >= 60):
            print(
                f"[Frame {frame_count:04d}] DuckRotY={duck_model.transform.rotation.y % 360.0:5.1f}° | "
                f"LightDir=({lx:.2f}, -1.00, {lz:.2f}) | FPS={1.0 / dt if dt > 0 else 0.0:.1f}"
            )

        if "--test" in sys.argv and frame_count >= 60:
            print("[Test] Reached 60 frames in automated test mode. Exiting cleanly.")
            app.close()

    print("Running Milestone 5 glTF Model Loading demo. Press ESC to exit.")
    app.run()
    print("Demo closed cleanly.")


if __name__ == "__main__":
    main()
