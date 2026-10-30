"""Example 16: VelocityEngine Dynamic Visual Scene Editor.

Features:
  - Global Rebranding: import VelocityEngine as ve
  - Dual Mode Architecture: Mode.GAME vs Mode.EDITOR with runtime switching
  - F2 Hotkey: Seamless live toggle between immersive game and visual editor
  - Integrated Sokol ImGui: Unity dark theme, Hierarchy & Inspector panels
  - 3D Manipulator Gizmo (ImGuizmo): Translate (W), Rotate (E), Scale (R)
  - PBR Material Presets: ve.Material.gold(), ve.Material.metal(), ve.Material.plastic(), ve.Material.rubber()
  - VS Code Integration: One-click opening of entity script in VS Code
"""

import math
import sys
from pathlib import Path

# Ensure 'python' package dir is available if running directly from repo root
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import VelocityEngine as ve


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
    print(" VelocityEngine: 16 - Dynamic Visual Scene Editor Demo")
    print("=" * 80)
    print("Controls:")
    print("  [F2]          : Toggle between EDITOR Mode and GAME Mode")
    print("  [W / E / R]   : Switch Gizmo tool (Translate / Rotate / Scale) in Editor")
    print("  [F1]          : Toggle Hitbox Debug Wireframes")
    print("  [TAB]         : Toggle Mouse Lock in Game Mode")
    print("  [ESC]         : Exit Application")
    print("  Editor Mode   : Use Mouse to select objects, inspect properties, adjust lighting")
    print("  Game Mode     : WASD + Mouse look + Space jump (FPS character controller)")
    print("=" * 80)

    # 1. Create Engine Application in EDITOR Mode
    app = ve.App(
        title="VelocityEngine - 16 Visual Scene Editor",
        width=1280,
        height=720,
        mode=ve.Mode.EDITOR,
        clear_color=(0.43, 0.63, 0.82, 1.0),  # Daylight sky blue
    )

    # Configure Editor hotkey toggle
    app.editor.enable_toggle_hotkey(True, key=ve.Key.F2)
    app.editor.show_hierarchy = True
    app.editor.show_inspector = True

    # 2. Camera Setup
    camera = app.camera
    camera.set_yaw_pitch(90.0, -14.0)
    camera.set_position(0.0, 2.4, -6.5)
    camera.fov = 60.0

    # 3. Daylight Lighting Setup
    light = app.scene.light
    light.direction = (0.55, -0.80, 0.35)
    light.color = (1.0, 0.96, 0.88)       # Warm sunlight
    light.intensity = 1.35
    light.set_ambient(0.35, 0.40, 0.46)
    light.set_hemispheric_ambient(0.38, 0.46, 0.58, 0.28, 0.24, 0.20)

    # 4. Environment: Elegant Floor Plane
    assets_dir = repo_root / "assets"
    floor_tex = app.create_checkerboard_texture(width=128, height=128, tile_size=16)
    floor_mat = ve.Material(floor_tex, roughness=0.82, metallic=0.0)
    floor_mat.base_color = (0.85, 0.86, 0.88, 1.0)
    floor_mat.set_uv_scale(12.0, 12.0)
    ground = app.scene.create_plane(size=36.0, uv_tiling=12.0, material=floor_mat)
    ground.name = "Ground_Plane"
    ground.cast_shadows = False
    ground.has_collision = False

    # 5. Load glTF 3D Models
    duck_path = assets_dir / "duck.glb"
    box_path = assets_dir / "box_textured.glb"
    avocado_path = assets_dir / "avocado.glb"

    duck_model = None
    if duck_path.exists():
        duck_model = app.scene.load_model(str(duck_path))
        duck_model.name = "Duck_Hero"
        duck_model.set_position(0.0, 0.0, -0.5)
        duck_model.set_scale(0.012, 0.012, 0.012)
        duck_model.set_rotation(0.0, 180.0, 0.0)
        duck_model.collision_scale = 0.80
        duck_model.set_cast_shadows(True)
        if duck_model.root_entity:
            duck_model.root_entity.script_path = str(Path(__file__).resolve())

    box_model = None
    if box_path.exists():
        box_model = app.scene.load_model(str(box_path))
        box_model.name = "Box_Textured"
        box_model.set_position(-3.0, 0.65, 0.5)
        box_model.set_scale(0.65, 0.65, 0.65)
        box_model.collision_scale = 0.90
        box_model.set_cast_shadows(True)
        if box_model.root_entity:
            box_model.root_entity.script_path = str(Path(__file__).resolve())

    avocado_model = None
    if avocado_path.exists():
        avocado_model = app.scene.load_model(str(avocado_path))
        avocado_model.name = "Avocado_Prop"
        avocado_model.set_position(3.0, 0.60, 0.5)
        avocado_model.set_scale(18.0, 18.0, 18.0)
        avocado_model.collision_scale = 0.75
        avocado_model.set_cast_shadows(True)
        if avocado_model.root_entity:
            avocado_model.root_entity.script_path = str(Path(__file__).resolve())

    # 6. Showcase PBR Material Presets on Procedural Cubes
    # Gold Metal Cube
    gold_cube = app.scene.create_cube()
    gold_cube.name = "PBR_Gold_Cube"
    gold_cube.transform.position = (-1.5, 0.5, 1.8)
    gold_cube.transform.scale = (0.7, 0.7, 0.7)
    gold_cube.material = ve.Material.gold(roughness=0.20)
    gold_cube.script_path = str(Path(__file__).resolve())

    # Chrome / Metal Cube
    metal_cube = app.scene.create_cube()
    metal_cube.name = "PBR_Chrome_Cube"
    metal_cube.transform.position = (0.0, 0.5, 2.5)
    metal_cube.transform.scale = (0.7, 0.7, 0.7)
    metal_cube.material = ve.Material.metal(roughness=0.08, color=(0.85, 0.90, 1.0))
    metal_cube.script_path = str(Path(__file__).resolve())

    # Red Plastic Cube
    plastic_cube = app.scene.create_cube()
    plastic_cube.name = "PBR_Plastic_Cube"
    plastic_cube.transform.position = (1.5, 0.5, 1.8)
    plastic_cube.transform.scale = (0.7, 0.7, 0.7)
    plastic_cube.material = ve.Material.plastic(roughness=0.30, color=(0.90, 0.15, 0.15))
    plastic_cube.script_path = str(Path(__file__).resolve())

    # Rubber Cube
    rubber_cube = app.scene.create_cube()
    rubber_cube.name = "PBR_Rubber_Cube"
    rubber_cube.transform.position = (3.0, 0.5, 2.5)
    rubber_cube.transform.scale = (0.7, 0.7, 0.7)
    rubber_cube.material = ve.Material.rubber(roughness=0.85, color=(0.12, 0.12, 0.15))
    rubber_cube.script_path = str(Path(__file__).resolve())

    # Pre-select Gold Cube in Editor to showcase Gizmo and Inspector
    app.editor.select_entity(gold_cube)

    # 7. First-Person Controller (active when in Game Mode)
    controller = ve.FirstPersonController(
        camera=camera,
        input_manager=app.input,
        scene=app.scene,
        audio=app.audio,
        move_speed=5.2,
        jump_speed=6.0,
        player_height=1.7,
        player_radius=0.35,
    )

    frame_count = 0

    @app.on_update
    def update(dt: float):
        nonlocal frame_count
        frame_count += 1

        # Hotkeys for Editor Gizmo operations
        if app.mode == ve.Mode.EDITOR:
            if app.input.is_key_pressed(ve.Key.W):
                app.editor.gizmo_operation = 0  # Translate
            elif app.input.is_key_pressed(ve.Key.E):
                app.editor.gizmo_operation = 1  # Rotate
            elif app.input.is_key_pressed(ve.Key.R):
                app.editor.gizmo_operation = 2  # Scale

        # Update FPS controller only in Game mode
        if app.mode == ve.Mode.GAME:
            controller.update(dt)

        # Log occasionally
        if frame_count % 60 == 0:
            mode_name = "EDITOR" if app.mode == ve.Mode.EDITOR else "GAME"
            pos = camera.position
            print(
                f"[Frame {frame_count:04d}] Mode={mode_name} | "
                f"CameraPos=({pos.x:.2f}, {pos.y:.2f}, {pos.z:.2f}) | "
                f"FPS={1.0 / dt if dt > 0 else 0.0:.1f}"
            )

        # Screenshot capture support for verification
        if "--screenshot" in sys.argv:
            if frame_count == 35:
                out_png = "screenshot_editor.png"
                ve.save_screenshot(app, out_png)
                print(f"[Screenshot] Editor screen capture saved to: {out_png}", flush=True)
            elif frame_count >= 45:
                app.close()

        if "--test" in sys.argv and frame_count >= 60:
            print("[Test] Reached 60 frames in automated test mode. Exiting cleanly.")
            app.close()

    print("Running VelocityEngine Editor Demo. Press ESC to exit.")
    app.run()
    print("VelocityEngine Editor Demo exited cleanly.")


def run_example(headless: bool = False, frames: int = 60):
    """Run Example 16 in interactive or headless mode."""
    if (headless or "--headless" in sys.argv) and "--test" not in sys.argv:
        sys.argv.append("--test")
    return main()


if __name__ == "__main__":
    main()
