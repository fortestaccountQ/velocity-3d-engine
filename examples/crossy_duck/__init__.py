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
from .textures import (
    TextureRegistry,
    MaterialRegistry,
    CrossyTextureGenerator,
    TextureGenerator,
    StylizedMaterial,
    MaterialConfig,
    ensure_textures_generated,
    generate_grass_texture,
    generate_asphalt_texture,
    generate_water_texture,
    generate_wood_bark_texture,
    generate_wood_rings_texture,
    generate_gravel_texture,
    generate_rail_gravel_texture,
    generate_rail_tie_texture,
    generate_car_grille_texture,
    generate_vehicle_texture,
    generate_duck_texture,
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
    "TextureRegistry",
    "MaterialRegistry",
    "CrossyTextureGenerator",
    "TextureGenerator",
    "StylizedMaterial",
    "MaterialConfig",
    "ensure_textures_generated",
    "generate_grass_texture",
    "generate_asphalt_texture",
    "generate_water_texture",
    "generate_wood_bark_texture",
    "generate_wood_rings_texture",
    "generate_gravel_texture",
    "generate_rail_gravel_texture",
    "generate_rail_tie_texture",
    "generate_car_grille_texture",
    "generate_vehicle_texture",
    "generate_duck_texture",
] + _WORLD_EXPORTS

