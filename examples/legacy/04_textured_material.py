"""Milestone 4 Test: Textures, Materials & PBR-lite Metallic-Roughness Pipeline."""

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
    print("=" * 75)
    print(" Engine 3D: Milestone 4 - Textures, Materials & PBR-lite Pipeline")
    print("=" * 75)
    print("Features:")
    print("  - Textured Plane ('Floor') with tiling procedural checkerboard")
    print("  - Cube 1: Rough Matte Red Material (roughness=0.85, metallic=0.05)")
    print("  - Cube 2: Smooth Metallic Gold Material (roughness=0.18, metallic=0.92)")
    print("  - Cube 3: Glossy Emerald Material (roughness=0.25, metallic=0.35)")
    print("  - Dynamic rotating directional light showcasing specular highlights")
    print("Controls:")
    print("  [W / S]       : Move Camera Forward / Backward")
    print("  [A / D]       : Move Camera Left / Right")
    print("  [ESC]         : Exit Application")
    print("=" * 75)

    app = engine.App(
        title="Engine 3D: Textures & Materials (Milestone 4)",
        width=800,
        height=600,
        clear_color=[0.05, 0.05, 0.08, 1.0],
    )

    # 1. Setup Camera (Framing all 3 cubes & textured floor)
    app.camera.position = (0.0, 3.5, 9.5)
    app.camera.target = (0.0, 0.4, 0.0)

    # 2. Setup Lighting (Initial light direction)
    app.scene.light.color = (1.0, 0.98, 0.92)
    app.scene.light.intensity = 1.3
    app.scene.light.ambient = (0.18, 0.18, 0.24)

    # 3. Textures
    # High-contrast floor checkerboard
    floor_tex = app.create_checkerboard_texture(width=128, height=128, tile_size=16)

    # Secondary fine-grain checkerboard for cubes
    cube_tex = Texture.create_checkerboard(
        width=64, height=64, tile_size=8, color1=0xFFFFFFFF, color2=0xFFB0B0C0
    )

    # 4. Create Materials
    # Floor: slightly matte, non-metallic
    floor_mat = Material(floor_tex, roughness=0.75, metallic=0.0)
    floor_mat.base_color = (0.9, 0.9, 0.95, 1.0)
    floor_mat.set_uv_scale(1.0, 1.0)

    # Cube 1: Rough Matte Red (diffuse dominated)
    mat_rough_red = Material(cube_tex, roughness=0.85, metallic=0.05)
    mat_rough_red.base_color = (0.95, 0.25, 0.20, 1.0)
    mat_rough_red.set_uv_scale(2.0, 2.0)

    # Cube 2: Glossy Metallic Gold (sharp specular highlights)
    mat_metal_gold = Material(cube_tex, roughness=0.18, metallic=0.92)
    mat_metal_gold.base_color = (1.00, 0.82, 0.25, 1.0)
    mat_metal_gold.set_uv_scale(2.0, 2.0)

    # Cube 3: Smooth Glossy Emerald
    mat_glossy_emerald = Material(cube_tex, roughness=0.25, metallic=0.40)
    mat_glossy_emerald.base_color = (0.15, 0.85, 0.45, 1.0)
    mat_glossy_emerald.set_uv_scale(2.0, 2.0)

    # 5. Populate Scene
    # Textured Floor
    floor = app.scene.create_plane(size=16.0, uv_tiling=8.0, material=floor_mat)
    floor.transform.position = (0.0, -1.0, 0.0)

    # 3 Cubes with different materials
    cube1 = app.scene.create_cube()
    cube1.name = "MatteRed"
    cube1.material = mat_rough_red
    cube1.transform.position = (-2.3, 0.3, 0.0)
    cube1.transform.scale = (0.75, 0.75, 0.75)

    cube2 = app.scene.create_cube()
    cube2.name = "MetallicGold"
    cube2.material = mat_metal_gold
    cube2.transform.position = (0.0, 0.5, 0.0)
    cube2.transform.scale = (0.90, 0.90, 0.90)

    cube3 = app.scene.create_cube()
    cube3.name = "GlossyEmerald"
    cube3.material = mat_glossy_emerald
    cube3.transform.position = (2.3, 0.3, 0.0)
    cube3.transform.scale = (0.75, 0.75, 0.75)

    frame_count = 0
    light_angle = 0.0

    # 6. Interactive Update Loop
    @app.on_update
    def update(dt: float):
        nonlocal frame_count, light_angle
        frame_count += 1
        light_angle += 0.8 * dt

        # Slowly rotate light source in a circular orbit to demonstrate specular glints
        lx = math.cos(light_angle) * 0.8
        lz = math.sin(light_angle) * 0.8
        app.scene.light.direction = (lx, -1.0, lz)

        # Rotate cubes at different speeds and axes
        cube1.transform.rotation.x += 25.0 * dt
        cube1.transform.rotation.y += 35.0 * dt

        cube2.transform.rotation.y += 45.0 * dt
        cube2.transform.rotation.z += 20.0 * dt

        cube3.transform.rotation.x -= 30.0 * dt
        cube3.transform.rotation.y += 50.0 * dt

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
                f"[Frame {frame_count:04d}] LightDir=({lx:.2f}, -1.00, {lz:.2f}) | "
                f"GoldCubeRotY={cube2.transform.rotation.y % 360.0:5.1f}° | "
                f"FPS={1.0/dt:.1f}"
            )

        if "--test" in sys.argv and frame_count >= 60:
            print("[Test] Reached 60 frames in automated test mode. Exiting cleanly.")
            app.close()

    print("Running textured material demo. Press ESC to exit.")
    app.run()
    print("Milestone 4 demo closed cleanly.")


if __name__ == "__main__":
    main()
