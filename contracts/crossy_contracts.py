"""Crossy Duck: Data Contracts and Protocol Specifications.

Defines the rigid interface boundaries between:
  1. World Generation System (world.py)
  2. Player, Hazards & Physics Controller (player.py)
  3. Isometric Camera, Audio & Viral HUD System (camera_vfx.py)
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Tuple, List, Optional, Protocol, Any, Dict

# Grid coordinate resolution
GRID_STEP: float = 1.0  # 1 unit per hop
WORLD_WIDTH_CELLS: int = 21  # [-10 .. +10]
CELL_MIN_X: int = -10
CELL_MAX_X: int = 10


class RowType(Enum):
    START = "START"
    GRASS = "GRASS"
    ROAD = "ROAD"
    RIVER = "RIVER"
    RAIL = "RAIL"


class PlayerStatus(Enum):
    IDLE = auto()
    HOPPING = auto()
    SQUASHED = auto()
    DROWNED = auto()
    EATEN = auto()  # Idle too long / eagle swoop


class ObstacleContract(Protocol):
    """Protocol for active dynamic obstacles (cars, trucks, trains, logs)."""
    x: float
    z: float
    y: float
    width: float
    height: float
    depth: float
    speed: float  # signed (+X or -X)
    is_log: bool  # If True, player can stand on it safely!
    entity: Any

    def update(self, dt: float) -> None: ...
    def check_hit(self, px: float, pz: float, radius: float = 0.35) -> bool: ...


class WorldRowContract(Protocol):
    """Protocol for a single horizontal row in the procedural terrain."""
    z_index: int
    row_type: RowType
    entities: List[Any]
    obstacles: List[ObstacleContract]

    def update(self, dt: float) -> None: ...
    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        """Returns (is_hazardous, hazard_reason, carrier_log_velocity_x)."""
        ...
    def cleanup(self, scene: Any) -> None: ...


class WorldGeneratorContract(Protocol):
    """Protocol for infinite streaming terrain generator."""
    active_rows: Dict[int, WorldRowContract]
    max_generated_z: int
    min_active_z: int

    def generate_ahead(self, player_z: int, lookahead: int = 25) -> None: ...
    def prune_behind(self, player_z: int, keep_behind: int = 8) -> None: ...
    def get_row(self, z: int) -> Optional[WorldRowContract]: ...
    def reset(self) -> None: ...


class PlayerControllerContract(Protocol):
    """Protocol for Duck character movement, hopping tweens, and state."""
    grid_x: int
    grid_z: int
    status: PlayerStatus
    score: int
    highest_z: int
    carrier_vx: float

    def hop(self, dx: int, dz: int) -> bool: ...
    def update(self, dt: float, current_row: Optional[WorldRowContract]) -> None: ...
    def reset(self) -> None: ...
