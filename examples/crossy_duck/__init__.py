"""Crossy Duck - 3D Arcade Hopper for VelocityEngine.

Exposes player controller, isometric camera math, viral HUD overlay,
and gameplay contracts.
"""

from __future__ import annotations

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
    PlayerControllerContract,
)
from .player import (
    PlayerController,
    BASE_SCALE,
    HOP_DURATION,
    JUMP_HEIGHT,
    IDLE_TIMEOUT,
)
from .camera_vfx import (
    IsometricCamera,
    CrossyHUD,
)

try:
    from .world import WorldGenerator, WorldRow
    _WORLD_EXPORTS = ["WorldGenerator", "WorldRow"]
except ImportError:
    _WORLD_EXPORTS = []

__all__ = [
    "GRID_STEP",
    "CELL_MIN_X",
    "CELL_MAX_X",
    "WORLD_WIDTH_CELLS",
    "RowType",
    "PlayerStatus",
    "ObstacleContract",
    "WorldRowContract",
    "WorldGeneratorContract",
    "PlayerControllerContract",
    "PlayerController",
    "IsometricCamera",
    "CrossyHUD",
    "BASE_SCALE",
    "HOP_DURATION",
    "JUMP_HEIGHT",
    "IDLE_TIMEOUT",
] + _WORLD_EXPORTS

