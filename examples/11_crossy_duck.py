"""11_crossy_duck.py - Standalone Crossy Duck 3D Arcade Game.

Wires up VelocityEngine, procedural streaming WorldGenerator,
PlayerController (Duck), Isometric Camera, and Viral 2D HUD Overlay.
Supports automated CI testing with `--test` flag.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Ensure repository root and python directory are in sys.path
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import VelocityEngine as ve
from VelocityEngine import App, Key, Color

from contracts.crossy_contracts import (
    GRID_STEP,
    CELL_MIN_X,
    CELL_MAX_X,
    WORLD_WIDTH_CELLS,
    RowType,
    PlayerStatus,
    ObstacleContract,
    WorldRowContract,
    WorldGeneratorContract,
)
from examples.crossy_duck.player import PlayerController, JUMP_HEIGHT, HOP_DURATION
from examples.crossy_duck.camera_vfx import IsometricCamera, CrossyHUD


def ensure_desktop_access() -> None:
    """Ensure Windows desktop station access when running from background services."""
    if sys.platform == "win32":
        try:
            import ctypes
            u32 = ctypes.windll.user32
            hdesk = u32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                u32.SetThreadDesktop(hdesk)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Robust World Row & Generator Implementations
# (Used directly or seamlessly as fallback if world.py is not yet loaded)
# ---------------------------------------------------------------------------

class BasicObstacle(ObstacleContract):
    """Dynamic obstacle entity (Car, Truck, Train, or Log)."""

    def __init__(
        self,
        scene: Any,
        x: float,
        y: float,
        z: float,
        width: float,
        height: float,
        depth: float,
        speed: float,
        is_log: bool = False,
        color: Any = None,
    ) -> None:
        self.x: float = float(x)
        self.y: float = float(y)
        self.z: float = float(z)
        self.width: float = float(width)
        self.height: float = float(height)
        self.depth: float = float(depth)
        self.speed: float = float(speed)
        self.is_log: bool = bool(is_log)

        self.scene = scene
        self.entity = None
        if self.scene is not None:
            try:
                col = color or (Color.from_hex("#8b5a2b") if is_log else Color.from_hex("#ef4444"))
                self.entity = self.scene.create_cube()
                self.entity.name = f"Obstacle_{int(x)}_{int(z)}"
                self.entity.color = col
                self.entity.has_collision = False
                self.entity.cast_shadows = True
                self.entity.transform.position = (self.x, self.y, self.z)
                self.entity.transform.scale = (self.width, self.height, self.depth)
            except Exception:
                pass

    def update(self, dt: float) -> None:
        self.x += self.speed * dt
        # Wrap around screen edges
        limit = 14.0
        if self.speed > 0 and self.x > limit:
            self.x = -limit
        elif self.speed < 0 and self.x < -limit:
            self.x = limit

        if self.entity is not None:
            try:
                self.entity.transform.position = (self.x, self.y, self.z)
            except Exception:
                pass

    def check_hit(self, px: float, pz: float, radius: float = 0.35) -> bool:
        """Check AABB intersection with circular duck radius."""
        half_w = self.width * 0.5
        half_d = self.depth * 0.5
        closest_x = max(self.x - half_w, min(px, self.x + half_w))
        closest_z = max(self.z - half_d, min(pz, self.z + half_d))
        dx = px - closest_x
        dz = pz - closest_z
        return (dx * dx + dz * dz) < (radius * radius)

    def cleanup(self) -> None:
        if self.entity is not None and self.scene is not None:
            try:
                self.scene.remove_entity(self.entity)
            except Exception:
                pass
            self.entity = None


class BasicWorldRow(WorldRowContract):
    """Single horizontal terrain row (START, GRASS, ROAD, RIVER, RAIL)."""

    def __init__(self, scene: Any, z_index: int, row_type: RowType) -> None:
        self.scene = scene
        self.z_index: int = int(z_index)
        self.row_type: RowType = row_type
        self.entities: List[Any] = []
        self.obstacles: List[ObstacleContract] = []

        self._build_row()

    def _build_row(self) -> None:
        if self.scene is None:
            return

        z_pos = float(self.z_index * GRID_STEP)
        y_pos = -0.15
        row_w = 26.0

        # Base tile color per row type
        if self.row_type == RowType.START or self.row_type == RowType.GRASS:
            c_hex = "#4ade80" if (self.z_index % 2 == 0) else "#22c55e"
        elif self.row_type == RowType.ROAD:
            c_hex = "#334155"
        elif self.row_type == RowType.RIVER:
            c_hex = "#38bdf8"
        elif self.row_type == RowType.RAIL:
            c_hex = "#475569"
        else:
            c_hex = "#64748b"

        try:
            tile = self.scene.create_cube()
            tile.name = f"Row_{self.z_index}"
            tile.color = Color.from_hex(c_hex)
            tile.has_collision = False
            tile.cast_shadows = False
            tile.transform.position = (0.0, y_pos, z_pos)
            tile.transform.scale = (row_w, 0.3, 1.0)
            self.entities.append(tile)
        except Exception:
            pass

        # Spawn Dynamic Obstacles
        if self.row_type == RowType.ROAD:
            speed = random.choice([-3.5, -2.8, 2.8, 3.5])
            spacing = 8.0
            car_colors = [Color.from_hex("#ef4444"), Color.from_hex("#3b82f6"), Color.from_hex("#eab308")]
            for i in range(3):
                ox = -10.0 + i * spacing + random.uniform(-1.0, 1.0)
                car = BasicObstacle(
                    self.scene,
                    x=ox,
                    y=0.25,
                    z=z_pos,
                    width=1.5,
                    height=0.55,
                    depth=0.8,
                    speed=speed,
                    is_log=False,
                    color=car_colors[i % len(car_colors)],
                )
                self.obstacles.append(car)

        elif self.row_type == RowType.RIVER:
            speed = random.choice([-2.2, -1.8, 1.8, 2.2])
            spacing = 9.0
            log_col = Color.from_hex("#854d0e")
            for i in range(3):
                ox = -10.0 + i * spacing + random.uniform(-0.8, 0.8)
                log = BasicObstacle(
                    self.scene,
                    x=ox,
                    y=-0.02,
                    z=z_pos,
                    width=2.4,
                    height=0.22,
                    depth=0.75,
                    speed=speed,
                    is_log=True,
                    color=log_col,
                )
                self.obstacles.append(log)

    def update(self, dt: float) -> None:
        for obs in self.obstacles:
            obs.update(dt)

    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        """Returns (is_hazardous, hazard_reason, carrier_log_velocity_x)."""
        if self.row_type == RowType.ROAD:
            for obs in self.obstacles:
                if obs.check_hit(px, pz, radius=0.35):
                    return True, "CAR", None
            return False, None, None

        elif self.row_type == RowType.RIVER:
            # Safe only if on top of a log
            for obs in self.obstacles:
                if obs.is_log and obs.check_hit(px, pz, radius=0.35):
                    return False, None, obs.speed
            # Fell into water!
            return True, "DROWN", None

        return False, None, None

    def cleanup(self, scene: Any) -> None:
        for obs in self.obstacles:
            if hasattr(obs, "cleanup"):
                obs.cleanup()
        for ent in self.entities:
            if scene is not None:
                try:
                    scene.remove_entity(ent)
                except Exception:
                    pass
        self.obstacles.clear()
        self.entities.clear()


class BasicWorldGenerator(WorldGeneratorContract):
    """Infinite streaming procedural world generator."""

    def __init__(self, scene: Any) -> None:
        self.scene = scene
        self.active_rows: Dict[int, WorldRowContract] = {}
        self.max_generated_z: int = -1
        self.min_active_z: int = 0

    def generate_ahead(self, player_z: int, lookahead: int = 25) -> None:
        target_max_z = player_z + lookahead
        while self.max_generated_z < target_max_z:
            z = self.max_generated_z + 1
            if z <= 2:
                row_type = RowType.START
            else:
                weights = [RowType.GRASS] * 4 + [RowType.ROAD] * 4 + [RowType.RIVER] * 3
                row_type = random.choice(weights)

            row = BasicWorldRow(self.scene, z, row_type)
            self.active_rows[z] = row
            self.max_generated_z = z

    def prune_behind(self, player_z: int, keep_behind: int = 8) -> None:
        cutoff = player_z - keep_behind
        to_remove = [z for z in self.active_rows if z < cutoff]
        for z in to_remove:
            row = self.active_rows.pop(z)
            row.cleanup(self.scene)
        if to_remove:
            self.min_active_z = max(self.min_active_z, cutoff)

    def get_row(self, z: int) -> Optional[WorldRowContract]:
        return self.active_rows.get(z)

    def reset(self) -> None:
        for row in list(self.active_rows.values()):
            row.cleanup(self.scene)
        self.active_rows.clear()
        self.max_generated_z = -1
        self.min_active_z = 0
        self.generate_ahead(0, lookahead=25)


# Seamlessly import external WorldGenerator if available
try:
    from examples.crossy_duck.world import WorldGenerator
except ImportError:
    try:
        from crossy_duck.world import WorldGenerator
    except ImportError:
        WorldGenerator = BasicWorldGenerator


# ---------------------------------------------------------------------------
# Main Game Application
# ---------------------------------------------------------------------------

def main() -> None:
    ensure_desktop_access()

    print("=" * 78)
    print(" 🦆 VelocityEngine: Crossy Duck 3D")
    print("=" * 78)
    print("Controls:")
    print("  [W / UP]     : Hop Forward")
    print("  [S / DOWN]   : Hop Backward")
    print("  [A / LEFT]   : Hop Left")
    print("  [D / RIGHT]  : Hop Right")
    print("  [R]          : Restart Game")
    print("  [ESC]        : Exit to Desktop")
    print("=" * 78)

    # 1. Initialize Engine Window
    app = App(
        title="Crossy Duck 3D",
        width=1280,
        height=720,
        clear_color=Color.from_hex("#70b0e0"),  # Vibrant daylight sky
    )

    # 2. Setup Lighting & Atmosphere
    app.scene.set_sun(
        direction=(-0.55, -1.25, -0.65),
        color=Color.from_hex("#fffdf0"),
        intensity=1.45,
    )

    # 3. Instantiate Subsystems
    world = WorldGenerator(app.scene)
    world.generate_ahead(0, lookahead=28)

    player = PlayerController(app=app, scene=app.scene, audio=app.audio, grid_x=0, grid_z=0)
    iso_camera = IsometricCamera(camera=app.camera, app=app, damping=8.5)
    iso_camera.snap_to(player)

    hud = CrossyHUD(app=app)

    # Input state transition debouncing
    prev_keys: Dict[int, bool] = {}

    def is_just_pressed(k: int) -> bool:
        down = app.input.is_key_down(k)
        was_down = prev_keys.get(k, False)
        prev_keys[k] = down
        return down and not was_down

    frame_count = 0

    # 4. Main Game Loop Callback
    @app.on_update
    def update(dt: float) -> None:
        nonlocal frame_count
        frame_count += 1

        # ESC to close
        if app.input.is_key_down(Key.ESCAPE):
            app.close()
            return

        # R to restart
        if is_just_pressed(Key.R):
            player.reset()
            world.reset()
            iso_camera.snap_to(player)
            print("[Game] Restarted!")

        # Movement Inputs (when alive)
        if player.status in (PlayerStatus.IDLE, PlayerStatus.HOPPING):
            if is_just_pressed(Key.W) or is_just_pressed(Key.UP):
                player.hop(0, 1)
            elif is_just_pressed(Key.S) or is_just_pressed(Key.DOWN):
                player.hop(0, -1)
            elif is_just_pressed(Key.A) or is_just_pressed(Key.LEFT):
                player.hop(-1, 0)
            elif is_just_pressed(Key.D) or is_just_pressed(Key.RIGHT):
                player.hop(1, 0)

        # Update World Streaming
        world.update(dt)
        world.generate_ahead(player.grid_z, lookahead=28)
        world.prune_behind(player.grid_z, keep_behind=8)

        # Update Player & Physics
        current_row = world.get_row(player.grid_z)
        player.update(dt, current_row)

        # Update Camera & HUD
        iso_camera.update(dt, player)
        hud.render(dt, player)

        # Automated CI Test Flag (--test)
        if "--test" in sys.argv:
            # Trigger test hops at preset frames
            if frame_count == 5:
                player.hop(0, 1)
            elif frame_count == 20:
                player.hop(0, 1)
            elif frame_count == 35:
                player.hop(1, 0)

            if frame_count >= 60:
                print(f"[CI Test] 60 frames verified successfully! Score: {player.score}. Exiting cleanly.")
                app.close()

    # 5. Run Game Loop
    app.run()
    print("[Game] Crossy Duck exited cleanly.")


if __name__ == "__main__":
    main()
