"""Milestone 3 Test: Scene Graph, Multiple Entities, Directional Lighting & Interactive Input."""

import sys
from pathlib import Path

# Ensure 'python' package dir is available if running directly from repo root
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import engine
from engine import Key


def main():
    print("=" * 70)
    print(" Engine 3D: Milestone 3 - Scene Graph, Lighting & Interactive Input")
    print("=" * 70)
    print("Features:")
    print("  - Scene with 2 independently transforming colored cubes")
    print("  - Blinn-Phong Directional Light with Ambient and Specular highlights")
    print("  - Real-time keyboard navigation with Input Subsystem:")
    print("      [W / S]       : Move Camera Forward / Backward")
    print("      [A / D]       : Move Camera Left / Right")
    print("      [UP / DOWN]   : Move Red Cube Up / Down")
    print("      [LEFT / RIGHT]: Move Red Cube Left / Right")
    print("      [ESC]         : Exit Application")
    print("=" * 70)

    app = engine.App(
        title="Engine 3D: Scene Graph & Lighting (Milestone 3)",
        width=800,
        height=600,
        clear_color=[0.08, 0.08, 0.12, 1.0],
    )

    # 1. Setup Camera
    app.camera.position = (0.0, 2.5, 7.0)
    app.camera.target = (0.0, 0.0, 0.0)

    # 2. Setup Directional Light in Scene
    app.scene.light.direction = (-0.6, -1.0, -0.8)
    app.scene.light.color = (1.0, 0.96, 0.88)
    app.scene.light.intensity = 1.2
    app.scene.light.ambient = (0.22, 0.22, 0.30)
    app.scene.light.shininess = 32.0

    # 3. Spawn Entities (Cube 1: Red-Orange, Cube 2: Cyan-Blue)
    cube1 = app.scene.create_cube(color=(0.95, 0.35, 0.25, 1.0))
    cube1.name = "RedCube"
    cube1.transform.position = (-1.8, 0.0, 0.0)
    cube1.transform.scale = (0.85, 0.85, 0.85)

    cube2 = app.scene.create_cube(color=(0.20, 0.75, 0.90, 1.0))
    cube2.name = "CyanCube"
    cube2.transform.position = (1.8, 0.0, 0.0)
    cube2.transform.scale = (0.85, 0.85, 0.85)

    frame_count = 0

    # 4. Frame Update Callback
    @app.on_update
    def update(dt: float):
        nonlocal frame_count
        frame_count += 1

        # Independent continuous rotation for both cubes
        cube1.transform.rotation.x += 40.0 * dt
        cube1.transform.rotation.y += 55.0 * dt

        cube2.transform.rotation.x -= 30.0 * dt
        cube2.transform.rotation.y += 70.0 * dt

        # Interactive Camera movement via W / S / A / D
        cam_speed = 4.0 * dt
        if app.input.is_key_down(Key.W):
            app.camera.move_forward(cam_speed)
        if app.input.is_key_down(Key.S):
            app.camera.move_forward(-cam_speed)
        if app.input.is_key_down(Key.A):
            app.camera.move_right(-cam_speed)
        if app.input.is_key_down(Key.D):
            app.camera.move_right(cam_speed)

        # Interactive Red Cube manipulation via Arrow keys
        cube_speed = 3.0 * dt
        if app.input.is_key_down(Key.UP):
            cube1.transform.position.y += cube_speed
        if app.input.is_key_down(Key.DOWN):
            cube1.transform.position.y -= cube_speed
        if app.input.is_key_down(Key.LEFT):
            cube1.transform.position.x -= cube_speed
        if app.input.is_key_down(Key.RIGHT):
            cube1.transform.position.x += cube_speed

        if frame_count % 120 == 0:
            pos = app.camera.position
            print(
                f"[Frame {frame_count:04d}] Camera=({pos.x:.1f}, {pos.y:.1f}, {pos.z:.1f}) | "
                f"RedCube=({cube1.transform.position.x:.1f}, {cube1.transform.position.y:.1f}) | "
                f"FPS={1.0/dt:.1f}"
            )

    print("Launching scene... Press ESC to close.")
    app.run()
    print("Scene demo exited successfully.")


if __name__ == "__main__":
    main()
