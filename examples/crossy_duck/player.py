"""Player Controller and Duck Character Physics for Crossy Duck.

Implements PlayerControllerContract with:
  - 3D glTF duck model (duck.glb) or procedural composite voxel duck fallback.
  - Snappy grid-based hops with parabolic arc (~0.65 height over 0.15s).
  - Procedural squash & stretch animation.
  - Directional yaw rotation.
  - Audio jump sound triggers.
  - River log carrier physics (log drift).
  - Death states: SQUASHED, DROWNED, IDLE TIMEOUT (EATEN).
  - Score and coin tracking.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Optional, Tuple, Any, List

from contracts.crossy_contracts import (
    GRID_STEP,
    CELL_MIN_X,
    CELL_MAX_X,
    PlayerStatus,
    PlayerControllerContract,
    WorldRowContract,
)

# Gameplay Constants
HOP_DURATION: float = 0.15     # Snappy hop time in seconds
JUMP_HEIGHT: float = 0.65      # Peak height of parabolic jump arc
IDLE_TIMEOUT: float = 45.0     # Idle seconds without forward progress before timeout
BASE_SCALE: float = 0.65       # Standard duck visual scale (fits inside 1.0x1.0 grid)


class PlayerController(PlayerControllerContract):
    """Duck character controller managing movement, jumping arcs, hazards, and states."""

    def __init__(
        self,
        app: Optional[Any] = None,
        scene: Optional[Any] = None,
        audio: Optional[Any] = None,
        grid_x: int = 0,
        grid_z: int = 0,
        idle_timeout: Optional[float] = None,
    ) -> None:
        self.app = app
        self.scene = scene or (getattr(app, "scene", None) if app else None)
        self.audio = audio or (getattr(app, "audio", None) if app else None)
        self.idle_timeout: float = float(idle_timeout if idle_timeout is not None else IDLE_TIMEOUT)

        # Grid Coordinates
        self.grid_x: int = int(grid_x)
        self.grid_z: int = int(grid_z)

        # Smooth World Transform
        self.x: float = float(self.grid_x * GRID_STEP)
        self.y: float = 0.0
        self.z: float = float(self.grid_z * GRID_STEP)

        # Hop Interpolation State
        self.start_x: float = self.x
        self.start_z: float = self.z
        self.target_x: float = self.x
        self.target_z: float = self.z
        self.target_grid_x: int = self.grid_x
        self.target_grid_z: int = self.grid_z
        self.hop_timer: float = 0.0

        # Orientation & Scale
        self.rotation_y: float = 0.0
        self.scale_x: float = BASE_SCALE
        self.scale_y: float = BASE_SCALE
        self.scale_z: float = BASE_SCALE

        # Status & Score
        self.status: PlayerStatus = PlayerStatus.IDLE
        self.score: int = 0
        self.highest_z: int = int(grid_z)
        self.coins: int = 0
        self.carrier_vx: float = 0.0

        # Idle & Hazard Tracking
        self.idle_timer: float = 0.0
        self.death_reason: Optional[str] = None
        self.death_timer: float = 0.0

        # Visual Entity
        self.entity: Optional[Any] = None
        self.is_voxel_duck: bool = False
        self.voxel_parts: List[Any] = []

        if self.scene is not None:
            self._init_duck_visual()

    def _init_duck_visual(self) -> None:
        """Load duck.glb 3D model or build composite voxel duck fallback."""
        if self.scene is None:
            return

        # 1. Look for duck.glb asset
        repo_root = Path(__file__).resolve().parent.parent.parent
        model_paths = [
            repo_root / "assets" / "duck.glb",
            Path("assets/duck.glb"),
            Path("../assets/duck.glb"),
        ]

        loaded = False
        for p in model_paths:
            if p.exists():
                try:
                    self.entity = self.scene.load_model(str(p))
                    self.entity.name = "CrossyDuck"
                    self.is_voxel_duck = False
                    loaded = True
                    break
                except Exception:
                    pass

        # 2. Fallback to composite voxel duck if model missing or failed
        if not loaded or self.entity is None:
            self._build_voxel_duck()

        self._sync_transform()

    def _build_voxel_duck(self) -> None:
        """Create a procedural composite voxel duck using scene boxes."""
        if self.scene is None:
            return

        try:
            from VelocityEngine.color import Color
            body_col = Color.from_hex("#f5c400")
            head_col = Color.from_hex("#ffdb1a")
            beak_col = Color.from_hex("#ff6f00")
            eye_col = Color.from_hex("#111111")
        except Exception:
            body_col = (0.96, 0.77, 0.0, 1.0)
            head_col = (1.0, 0.86, 0.1, 1.0)
            beak_col = (1.0, 0.43, 0.0, 1.0)
            eye_col = (0.07, 0.07, 0.07, 1.0)

        try:
            root = self.scene.create_entity("VoxelDuck")
        except Exception:
            try:
                root = self.scene.create_box(size=(0.6, 0.6, 0.6), name="VoxelDuck")
                self.entity = root
                self.is_voxel_duck = True
                return
            except Exception:
                return

        root.transform.position = (self.x, self.y, self.z)
        root.transform.scale = (self.scale_x, self.scale_y, self.scale_z)

        # Body
        body = self.scene.create_box(size=(0.65, 0.50, 0.65), color=body_col, name="DuckBody")
        body.parent = root
        body.transform.position = (0.0, 0.25, 0.0)

        # Head
        head = self.scene.create_box(size=(0.42, 0.42, 0.42), color=head_col, name="DuckHead")
        head.parent = root
        head.transform.position = (0.0, 0.58, 0.15)

        # Beak
        beak = self.scene.create_box(size=(0.28, 0.12, 0.22), color=beak_col, name="DuckBeak")
        beak.parent = root
        beak.transform.position = (0.0, 0.50, 0.40)

        # Eyes
        eye_l = self.scene.create_box(size=(0.07, 0.07, 0.07), color=eye_col, name="DuckEyeL")
        eye_l.parent = root
        eye_l.transform.position = (-0.15, 0.65, 0.28)

        eye_r = self.scene.create_box(size=(0.07, 0.07, 0.07), color=eye_col, name="DuckEyeR")
        eye_r.parent = root
        eye_r.transform.position = (0.15, 0.65, 0.28)

        self.entity = root
        self.is_voxel_duck = True
        self.voxel_parts = [body, head, beak, eye_l, eye_r]

    def _sync_transform(self) -> None:
        """Synchronize physics position, rotation, and scale to visual 3D entity."""
        if self.entity is not None:
            try:
                self.entity.transform.position = (self.x, self.y, self.z)
                self.entity.transform.rotation = (0.0, self.rotation_y, 0.0)
                self.entity.transform.scale = (self.scale_x, self.scale_y, self.scale_z)
            except Exception:
                pass

    def _play_jump_sound(self) -> None:
        """Trigger audio sound effect for hopping."""
        if self.audio is not None:
            try:
                if hasattr(self.audio, "play_sound"):
                    self.audio.play_sound("jump")
                elif hasattr(self.audio, "play_jump"):
                    self.audio.play_jump()
            except Exception:
                pass

    def hop(self, dx: int, dz: int) -> bool:
        """Initiate a snappy grid-based hop in cardinal direction (dx, dz)."""
        if self.status != PlayerStatus.IDLE:
            return False
        if dx == 0 and dz == 0:
            return False

        current_gx = int(round(self.x / GRID_STEP))
        new_gx = current_gx + dx

        # Clamp horizontal boundaries to [-10, 10]
        if new_gx < CELL_MIN_X or new_gx > CELL_MAX_X:
            return False

        new_gz = self.grid_z + dz
        # Prevent backtracking beyond safety window (max 6 cells behind highest Z)
        min_allowed_z = max(0, self.highest_z - 6)
        if new_gz < min_allowed_z:
            return False

        # Snap facing rotation to movement direction
        if dx > 0:
            self.rotation_y = -90.0
        elif dx < 0:
            self.rotation_y = 90.0
        elif dz > 0:
            self.rotation_y = 0.0
        elif dz < 0:
            self.rotation_y = 180.0

        # Start hopping state
        self.status = PlayerStatus.HOPPING
        self.hop_timer = 0.0
        self.start_x = self.x
        self.start_z = self.z
        self.target_grid_x = new_gx
        self.target_grid_z = new_gz
        self.target_x = float(new_gx * GRID_STEP)
        self.target_z = float(new_gz * GRID_STEP)

        # Any player hop resets idle countdown and clears log carrier velocity
        self.idle_timer = 0.0
        self.carrier_vx = 0.0

        self._play_jump_sound()
        return True

    def die(self, status: PlayerStatus, reason: Optional[str] = None) -> None:
        """Trigger player death state with given cause."""
        if self.status in (PlayerStatus.SQUASHED, PlayerStatus.DROWNED, PlayerStatus.EATEN):
            return
        self.status = status
        self.death_reason = reason or status.name
        self.death_timer = 0.0
        self.carrier_vx = 0.0

    def collect_coin(self, amount: int = 1) -> None:
        """Increment collected coins and optionally trigger audio."""
        self.coins += amount
        if self.audio is not None:
            try:
                if hasattr(self.audio, "play_sound"):
                    self.audio.play_sound("coin")
            except Exception:
                pass

    def update(self, dt: float, current_row: Optional[WorldRowContract] = None) -> None:
        """Advance player state, hop animation, carrier physics, and hazard checks."""
        # 1. Handle Death States Animation
        if self.status in (PlayerStatus.SQUASHED, PlayerStatus.DROWNED, PlayerStatus.EATEN):
            self.death_timer += dt
            if self.status == PlayerStatus.SQUASHED:
                # Flatten duck transform scale and knock down
                squash_prog = min(1.0, self.death_timer * 12.0)
                self.scale_y = max(0.06 * BASE_SCALE, BASE_SCALE * (1.0 - squash_prog * 0.92))
                self.scale_x = BASE_SCALE * (1.0 + squash_prog * 0.50)
                self.scale_z = BASE_SCALE * (1.0 + squash_prog * 0.50)
                self.y = 0.04
            elif self.status == PlayerStatus.DROWNED:
                # Sink into water with splash spin
                self.y = max(-0.95, -1.8 * self.death_timer)
                self.rotation_y += 180.0 * dt
                shrink = max(0.2, 1.0 - self.death_timer * 0.8)
                self.scale_x = BASE_SCALE * shrink
                self.scale_y = BASE_SCALE * shrink
                self.scale_z = BASE_SCALE * shrink
            elif self.status == PlayerStatus.EATEN:
                # Comical arcade spin & shrink (clamped, duck never escapes into space)
                self.y = min(1.2, self.y + 1.2 * dt)
                self.rotation_y += 360.0 * dt
                fade = max(0.0, 1.0 - self.death_timer * 1.5)
                self.scale_x = BASE_SCALE * fade
                self.scale_y = BASE_SCALE * fade
                self.scale_z = BASE_SCALE * fade

            self._sync_transform()
            return

        # 2. Hopping Animation (Parabolic Arc & Squash-Stretch)
        if self.status == PlayerStatus.HOPPING:
            self.hop_timer += dt
            t = min(1.0, self.hop_timer / HOP_DURATION)

            # Horizontal Lerp
            self.x = self.start_x + (self.target_x - self.start_x) * t
            self.z = self.start_z + (self.target_z - self.start_z) * t

            # Parabolic Jump Arc: 4 * h * t * (1 - t)
            arc = 4.0 * t * (1.0 - t)
            self.y = JUMP_HEIGHT * arc

            # Squash & Stretch
            if t < 0.2:
                # Take-off squash
                p = t / 0.2
                self.scale_y = BASE_SCALE * (0.80 + 0.20 * p)
                self.scale_x = BASE_SCALE * (1.18 - 0.18 * p)
                self.scale_z = BASE_SCALE * (1.18 - 0.18 * p)
            elif t > 0.8:
                # Landing squash
                p = (t - 0.8) / 0.2
                bounce = math.sin(p * math.pi)
                self.scale_y = BASE_SCALE * (1.0 - 0.22 * bounce)
                self.scale_x = BASE_SCALE * (1.0 + 0.18 * bounce)
                self.scale_z = BASE_SCALE * (1.0 + 0.18 * bounce)
            else:
                # Peak stretch
                air_factor = math.sin((t - 0.2) / 0.6 * math.pi)
                self.scale_y = BASE_SCALE * (1.0 + 0.32 * air_factor)
                self.scale_x = BASE_SCALE * (1.0 - 0.14 * air_factor)
                self.scale_z = BASE_SCALE * (1.0 - 0.14 * air_factor)

            # Hop Completed
            if t >= 1.0:
                self.status = PlayerStatus.IDLE
                self.grid_x = self.target_grid_x
                self.grid_z = self.target_grid_z
                self.x = self.target_x
                self.z = self.target_z
                self.y = 0.0
                self.scale_x = BASE_SCALE
                self.scale_y = BASE_SCALE
                self.scale_z = BASE_SCALE

                if self.grid_z > self.highest_z:
                    self.highest_z = self.grid_z
                    self.score = self.highest_z

        # 3. Check Row Hazards & River Log Carrier Physics
        if current_row is not None:
            is_hazardous, reason, carrier_vx = current_row.check_player_hazard(self.x, self.z)
            if is_hazardous:
                if reason in ("DROWN", "WATER"):
                    self.die(PlayerStatus.DROWNED, reason)
                else:
                    self.die(PlayerStatus.SQUASHED, reason)
                self._sync_transform()
                return

            # Safe on log in River row
            if carrier_vx is not None and self.status == PlayerStatus.IDLE:
                self.carrier_vx = carrier_vx
                self.x += self.carrier_vx * dt
                self.grid_x = int(round(self.x / GRID_STEP))
                # Swept off-screen into river edge
                if self.x < CELL_MIN_X - 0.8 or self.x > CELL_MAX_X + 0.8:
                    self.die(PlayerStatus.DROWNED, "SWEPT_AWAY")
                    self._sync_transform()
                    return
            else:
                self.carrier_vx = 0.0
        else:
            self.carrier_vx = 0.0

        # 4. Idle Timeout Countdown (> idle_timeout seconds without action -> EATEN)
        if self.status == PlayerStatus.IDLE:
            self.idle_timer += dt
            if self.idle_timer >= self.idle_timeout:
                self.die(PlayerStatus.EATEN, "IDLE_TIMEOUT")
                self._sync_transform()
                return

        self._sync_transform()

    def reset(self) -> None:
        """Reset player to initial starting conditions."""
        self.grid_x = 0
        self.grid_z = 0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.start_x = 0.0
        self.start_z = 0.0
        self.target_x = 0.0
        self.target_z = 0.0
        self.target_grid_x = 0
        self.target_grid_z = 0
        self.hop_timer = 0.0

        self.rotation_y = 0.0
        self.scale_x = BASE_SCALE
        self.scale_y = BASE_SCALE
        self.scale_z = BASE_SCALE

        self.status = PlayerStatus.IDLE
        self.score = 0
        self.highest_z = 0
        self.carrier_vx = 0.0

        self.idle_timer = 0.0
        self.death_reason = None
        self.death_timer = 0.0

        self._sync_transform()
