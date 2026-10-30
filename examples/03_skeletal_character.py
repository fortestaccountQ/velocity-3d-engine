"""Example 03: Skeletal Character & Third-Person Controller.

Showcase:
- 3D character (Soldier.glb) loaded with skeletal animation and skinning.
- Third-person spring-arm FollowCamera smoothly tracking the hero.
- Responsive WASD navigation: Idle when stationary, smooth `mixer.crossfade_to("Run", 0.2)` on movement.
- Real-time ground and obstacle AABB collision detection with wall sliding.
- Production-ready standalone execution and headless/test suite support.
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
    FollowCamera,
    Mesh,
    StandardMaterial,
    AnimationMixer,
    Vec3,
    Color,
    Key,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
    GREEN,
)


def find_asset_path(filename: str) -> Path:
    """Resolve asset filepath across local asset directories."""
    paths = [
        repo_root / "assets" / filename,
        repo_root / "temp" / "threejs" / "examples" / "models" / "gltf" / filename,
    ]
    for p in paths:
        if p.exists():
            return p
    return repo_root / "assets" / filename


def create_arena(app: App) -> list[tuple[float, float, float, float]]:
    """Build the arena floor, boundary perimeter, and obstacle crates.

    Returns:
        List of obstacle tuples: (center_x, center_z, half_width, half_depth)
    """
    scene = app.scene

    # Lighting
    scene.set_sun(direction=(-0.8, -1.8, -1.0), color=WARM_WHITE, intensity=1.5)
    scene.create_grid(size=40.0, step=1.0, color=Color.from_hex("#232733"))

    # Floor plane
    floor_mat = StandardMaterial()
    floor_mat.base_color = (0.12, 0.14, 0.18, 1.0)
    floor_mat.roughness = 0.6
    floor_mat.metallic = 0.2

    floor = scene.create_entity("ArenaFloor")
    floor.mesh = Mesh.create_plane(width=38.0, depth=38.0, subdivisions_x=2, subdivisions_z=2)
    floor.material = floor_mat
    floor.transform.position = (0.0, 0.0, 0.0)

    # Perimeter wall pillars / borders
    wall_mat = StandardMaterial()
    wall_mat.base_color = (0.2, 0.24, 0.32, 1.0)
    wall_mat.roughness = 0.5
    wall_mat.metallic = 0.3

    wall_mesh = Mesh.create_box(1.0, 2.5, 38.0)
    left_wall = scene.create_entity("WallLeft")
    left_wall.mesh = wall_mesh
    left_wall.material = wall_mat
    left_wall.transform.position = (-19.0, 1.25, 0.0)

    right_wall = scene.create_entity("WallRight")
    right_wall.mesh = wall_mesh
    right_wall.material = wall_mat
    right_wall.transform.position = (19.0, 1.25, 0.0)

    wall_mesh_z = Mesh.create_box(38.0, 2.5, 1.0)
    front_wall = scene.create_entity("WallFront")
    front_wall.mesh = wall_mesh_z
    front_wall.material = wall_mat
    front_wall.transform.position = (0.0, 1.25, -19.0)

    back_wall = scene.create_entity("WallBack")
    back_wall.mesh = wall_mesh_z
    back_wall.material = wall_mat
    back_wall.transform.position = (0.0, 1.25, 19.0)

    # Obstacle Crates: (x, z, half_w, half_d)
    obstacles: list[tuple[float, float, float, float]] = []
    crate_mesh = Mesh.create_box(2.4, 2.4, 2.4)
    crate_mat = StandardMaterial()
    crate_mat.base_color = (0.7, 0.45, 0.22, 1.0)
    crate_mat.roughness = 0.7
    crate_mat.metallic = 0.1

    crate_positions = [
        (-6.0, -6.0), (6.0, -6.0),
        (-6.0, 6.0), (6.0, 6.0),
        (0.0, -10.0), (0.0, 10.0),
        (-10.0, 0.0), (10.0, 0.0),
    ]

    for idx, (cx, cz) in enumerate(crate_positions):
        crate = scene.create_entity(f"ObstacleCrate_{idx}")
        crate.mesh = crate_mesh
        crate.material = crate_mat
        crate.transform.position = (cx, 1.2, cz)
        obstacles.append((cx, cz, 1.2, 1.2))

    return obstacles


def check_collision(px: float, pz: float, obstacles: list[tuple[float, float, float, float]], radius: float = 0.5) -> bool:
    """Check circle collision against arena bounds and obstacles."""
    # Arena boundary check
    arena_limit = 18.2 - radius
    if abs(px) > arena_limit or abs(pz) > arena_limit:
        return True

    # AABB vs Circle check
    for ox, oz, hw, hd in obstacles:
        closest_x = max(ox - hw, min(px, ox + hw))
        closest_z = max(oz - hd, min(pz, oz + hd))
        dx = px - closest_x
        dz = pz - closest_z
        if (dx * dx + dz * dz) < (radius * radius):
            return True
    return False


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the skeletal character example in interactive or headless mode."""
    app = App("Velocity - 03 Skeletal Character", width=1280, height=720, clear_color="#0e1117")

    obstacles = create_arena(app)

    # 1. Load Character Model (Soldier.glb)
    soldier_file = find_asset_path("Soldier.glb")
    character = app.scene.load_model(str(soldier_file))

    if character and character.root_entity:
        char_node = character.root_entity
        char_node.transform.position = (0.0, 0.0, 0.0)
    else:
        # Fallback dummy entity if asset unavailable
        char_node = app.scene.create_entity("SoldierFallback")
        char_node.mesh = Mesh.create_box(0.8, 1.8, 0.8)
        char_node.transform.position = (0.0, 0.9, 0.0)

    # 2. Setup AnimationMixer and smooth crossfade
    mixer: Optional[AnimationMixer] = None
    if character and len(character.animations) > 0:
        mixer = AnimationMixer(char_node)
        for anim in character.animations:
            mixer.clip_action(anim)

        idle_action = mixer.get_action("Idle")
        if idle_action:
            idle_action.play()

    current_state = "Idle"

    # 3. Third-Person Spring-Arm FollowCamera
    follow_cam = FollowCamera(
        camera=app.camera,
        target_entity=char_node,
        offset=(0.0, 2.8, 5.2),
        look_at_offset=(0.0, 1.3, 0.0),
        stiffness=14.0,
        damping=0.85,
    )
    app.camera = follow_cam

    # 4. Setup UI Overlay
    app.ui.clear()
    app.ui.draw_text("Velocity 3D Engine | 03: Skeletal Character & Third-Person Camera", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("WASD: Move Character (Smooth Crossfade Idle <-> Run) | FollowCamera Spring-Arm", (24, 52), size=14, color=CYAN)
    app.ui.draw_text(f"State: {current_state} | Obstacle Collision: Active", (24, 76), size=13, color=GREEN)
    app.ui.show_stats(True)

    char_x = 0.0
    char_z = 0.0
    char_heading = 0.0
    move_speed = 5.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal current_state, char_x, char_z, char_heading, frame_counter
        frame_counter += 1

        # WASD Input Query
        inp = app.input
        move_x = 0.0
        move_z = 0.0

        if inp.is_key_down(Key.W):
            move_z -= 1.0
        if inp.is_key_down(Key.S):
            move_z += 1.0
        if inp.is_key_down(Key.A):
            move_x -= 1.0
        if inp.is_key_down(Key.D):
            move_x += 1.0

        length = math.sqrt(move_x * move_x + move_z * move_z)
        is_moving = length > 0.01

        # Animation State Machine & Smooth Crossfade
        if is_moving:
            move_x /= length
            move_z /= length

            if current_state != "Run":
                if mixer is not None:
                    mixer.crossfade_to("Run", 0.2)
                current_state = "Run"

            # Rotate character smoothly towards movement direction
            target_heading = math.degrees(math.atan2(move_x, move_z)) + 180.0
            char_heading = target_heading
            char_node.transform.rotation = (0.0, char_heading, 0.0)

            # Collision Detection & Sliding Physics
            step_x = move_x * move_speed * dt
            step_z = move_z * move_speed * dt

            # Try moving on both axes
            if not check_collision(char_x + step_x, char_z + step_z, obstacles):
                char_x += step_x
                char_z += step_z
            elif not check_collision(char_x + step_x, char_z, obstacles):
                # Slide along X
                char_x += step_x
            elif not check_collision(char_x, char_z + step_z, obstacles):
                # Slide along Z
                char_z += step_z

            char_node.transform.position = (char_x, 0.0, char_z)
        else:
            if current_state != "Idle":
                if mixer is not None:
                    mixer.crossfade_to("Idle", 0.2)
                current_state = "Idle"

        # Advance skeletal animation mixer
        if mixer is not None:
            mixer.update(dt)

        # Update HUD state
        app.ui.draw_text(f"State: {current_state} | Pos: ({char_x:.2f}, {char_z:.2f})", (24, 76), size=13, color=GREEN if current_state == "Run" else YELLOW)

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
