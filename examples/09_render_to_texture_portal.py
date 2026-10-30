"""Example 09: Render-to-Texture CCTV Security Monitor & Portal.

Showcase:
- 3D surveillance room with a rotating display exhibit on a central pedestal.
- Ceiling-mounted security camera capturing an overhead live feed into an offscreen `RenderTarget(512, 512)`.
- Wall-mounted 3D TV / flat-panel monitor displaying the live camera texture via `material.albedo_map = target.texture`.
- Main camera observing both the physical room and the live televised broadcast in real-time.
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
    OrbitController,
    PerspectiveCamera,
    RenderTarget,
    RenderTargetFormat,
    Mesh,
    StandardMaterial,
    PointLight,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
    RED,
)


def create_cctv_room(app: App) -> tuple[ve.Entity, ve.Entity, PerspectiveCamera, RenderTarget]:
    """Build the surveillance room, security camera, monitor screen, and rotating centerpiece."""
    scene = app.scene

    # Sunlight and soft room fill
    scene.set_sun(direction=(-0.5, -1.8, -0.6), color=WARM_WHITE, intensity=1.2)
    room_light = PointLight("RoomCeilingLight", Vec3(1.0, 0.95, 0.85), 3.0, 15.0, 2.0)
    room_light.transform.position = (0.0, 5.0, 0.0)
    scene.add_light(room_light)

    # 1. Room Shell (Floor, Ceiling, Walls)
    wall_mat = StandardMaterial()
    wall_mat.base_color = (0.22, 0.25, 0.3, 1.0)
    wall_mat.roughness = 0.7
    wall_mat.metallic = 0.1

    floor = scene.create_entity("Floor")
    floor.mesh = Mesh.create_box(14.0, 0.2, 14.0)
    floor_mat = StandardMaterial()
    floor_mat.base_color = (0.1, 0.12, 0.16, 1.0)
    floor_mat.roughness = 0.4
    floor_mat.metallic = 0.2
    floor.material = floor_mat
    floor.transform.position = (0.0, -0.1, 0.0)

    # Back wall
    back_wall = scene.create_entity("BackWall")
    back_wall.mesh = Mesh.create_box(14.0, 6.0, 0.3)
    back_wall.material = wall_mat
    back_wall.transform.position = (0.0, 3.0, -7.0)

    # Left wall (where TV monitor will be mounted)
    left_wall = scene.create_entity("LeftWall")
    left_wall.mesh = Mesh.create_box(0.3, 6.0, 14.0)
    left_wall.material = wall_mat
    left_wall.transform.position = (-7.0, 3.0, 0.0)

    # Right wall
    right_wall = scene.create_entity("RightWall")
    right_wall.mesh = Mesh.create_box(0.3, 6.0, 14.0)
    right_wall.material = wall_mat
    right_wall.transform.position = (7.0, 3.0, 0.0)

    # 2. Central Pedestal & Rotating Exhibit Object
    pedestal = scene.create_entity("Pedestal")
    pedestal.mesh = Mesh.create_cylinder(radius=1.2, height=1.2, segments=32)
    ped_mat = StandardMaterial()
    ped_mat.base_color = (0.35, 0.38, 0.45, 1.0)
    ped_mat.roughness = 0.3
    ped_mat.metallic = 0.7
    pedestal.material = ped_mat
    pedestal.transform.position = (0.0, 0.6, 0.0)

    # Rotating Exhibit Object (Duck model or Golden Sphere)
    duck_path = repo_root / "assets" / "duck.glb"
    if duck_path.exists():
        model = scene.load_model(str(duck_path))
        exhibit = model.root_entity
        exhibit.transform.position = (0.0, 1.2, 0.0)
        exhibit.transform.scale = (1.8, 1.8, 1.8)
    else:
        exhibit = scene.create_entity("ExhibitObject")
        exhibit.mesh = Mesh.create_sphere(radius=0.75, rings=32, sectors=32)
        ex_mat = StandardMaterial()
        ex_mat.base_color = (1.0, 0.75, 0.2, 1.0)
        ex_mat.metallic = 0.95
        ex_mat.roughness = 0.15
        exhibit.material = ex_mat
        exhibit.transform.position = (0.0, 2.0, 0.0)

    # 3. Security Camera mounted in corner of ceiling
    cctv_cam = PerspectiveCamera(65.0, 1.0, 0.1, 30.0)
    cctv_cam.set_position(5.5, 5.0, 5.5)
    cctv_cam.set_target(0.0, 1.2, 0.0)

    # Camera body mesh for visual realism
    cam_body = scene.create_entity("CCTVCameraBody")
    cam_body.mesh = Mesh.create_cylinder(radius=0.25, height=0.6, segments=16)
    cam_mat = StandardMaterial()
    cam_mat.base_color = (0.8, 0.1, 0.1, 1.0)
    cam_body.material = cam_mat
    cam_body.transform.position = (5.5, 5.0, 5.5)

    # 4. Offscreen RenderTarget (512 x 512)
    cctv_target = RenderTarget(512, 512, RenderTargetFormat.RGBA8, has_depth=True)

    # 5. Wall-Mounted 3D TV Screen
    tv_frame = scene.create_entity("TVFrame")
    tv_frame.mesh = Mesh.create_box(0.2, 2.4, 3.4)
    frame_mat = StandardMaterial()
    frame_mat.base_color = (0.05, 0.05, 0.06, 1.0)
    frame_mat.roughness = 0.8
    tv_frame.material = frame_mat
    tv_frame.transform.position = (-6.85, 3.2, 0.0)

    # Screen displaying the live CCTV camera render texture
    tv_screen = scene.create_entity("TVScreen")
    tv_screen.mesh = Mesh.create_box(0.05, 2.1, 3.1)
    tv_mat = StandardMaterial()
    tv_mat.base_color = (1.0, 1.0, 1.0, 1.0)
    tv_mat.albedo_map = cctv_target.texture
    tv_mat.roughness = 0.2
    tv_mat.metallic = 0.0
    tv_screen.material = tv_mat
    tv_screen.transform.position = (-6.75, 3.2, 0.0)

    return exhibit, tv_screen, cctv_cam, cctv_target


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the render-to-texture portal example in interactive or headless mode."""
    app = App("Velocity - 09 Render to Texture Portal", width=1280, height=720, clear_color="#0b0e14")

    # Main spectator camera looking into the room at both pedestal and wall monitor
    orb = OrbitController(target=(-1.5, 2.2, 0.0), distance=12.0, min_distance=2.0, max_distance=30.0, yaw=-30.0, pitch=15.0)
    app.camera = orb

    exhibit, tv_screen, cctv_cam, cctv_target = create_cctv_room(app)

    # UI Overlay setup
    app.ui.clear()
    app.ui.draw_text("Velocity 3D Engine | 09: Render-to-Texture Security Monitor", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("Ceiling Security Cam renders to RenderTarget(512, 512) -> TV screen albedo_map", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("[REC] LIVE CCTV BROADCAST 1080p | Orbit main camera to observe both feeds", (24, 76), size=13, color=RED)
    app.ui.show_stats(True)

    time_accum = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        # 1. Rotate exhibit object
        exhibit.transform.rotate_y(40.0 * dt)

        # 2. Render surveillance camera viewpoint into offscreen RenderTarget FBO
        app.render_target(app.scene, cctv_cam, cctv_target)

        # Flash recording indicator every second
        rec_dot = "●" if int(time_accum * 2.0) % 2 == 0 else "○"
        app.ui.draw_text(f"{rec_dot} CCTV CAMERA FEED #01 - LIVE", (24, 76), size=13, color=RED)

        if (headless or "--test" in sys.argv or "--headless" in sys.argv) and frame_counter >= frames:
            app.close()

    app.on_update(update)

    if not headless and "--headless" not in sys.argv:
        app.run()
    else:
        for _ in range(frames):
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
