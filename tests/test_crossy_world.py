"""Comprehensive Unit Tests for Crossy Duck Procedural World Generation.

Tests:
  1. Data contract conformance (WorldGeneratorContract, WorldRowContract, ObstacleContract).
  2. Procedural terrain generation, row streaming, and type distribution.
  3. Obstacle physics, horizontal movement, and wrap-around math.
  4. Exact circle-to-AABB collision math.
  5. River log riding detection and drowning hazards.
  6. Road traffic squashing and safe crossing gaps.
  7. Railway warning light beacon blinking and bullet train collision.
  8. Grass procedural tree obstruction and open path guarantees.
  9. Streaming row pruning and 3D scene entity cleanup (500+ FPS preservation).
 10. World reset and deterministic seed reproducibility.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure repository root and package path are in sys.path
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(1, str(repo_root))

crossy_dir = repo_root / "examples" / "crossy_duck"
if str(crossy_dir) not in sys.path:
    sys.path.insert(0, str(crossy_dir))

try:
    from examples.crossy_duck import world, textures, player
except ImportError:
    import world
    import textures
    import player

from contracts.crossy_contracts import (
    GRID_STEP,
    CELL_MIN_X,
    CELL_MAX_X,
    WORLD_WIDTH_CELLS,
    RowType,
    ObstacleContract,
    WorldRowContract,
    WorldGeneratorContract,
)

try:
    import VelocityEngine as ve
except ImportError:
    ve = None


# =============================================================================
# 1. Contract & Interface Adherence
# =============================================================================
def test_contract_adherence() -> None:
    """Verify that all classes satisfy the required contracts and protocol signatures."""
    wg = world.WorldGenerator(seed=1)
    assert hasattr(wg, "active_rows")
    assert hasattr(wg, "max_generated_z")
    assert hasattr(wg, "min_active_z")
    assert callable(wg.generate_ahead)
    assert callable(wg.prune_behind)
    assert callable(wg.get_row)
    assert callable(wg.reset)
    assert callable(wg.check_hazard)
    assert callable(wg.is_cell_blocked)
    assert callable(wg.update)

    row_classes = [
        world.StartRow(0),
        world.GrassRow(1),
        world.RoadRow(2),
        world.RiverRow(3),
        world.RailRow(4),
    ]
    for row in row_classes:
        assert hasattr(row, "z_index")
        assert hasattr(row, "row_type")
        assert hasattr(row, "entities")
        assert hasattr(row, "obstacles")
        assert callable(row.update)
        assert callable(row.check_player_hazard)
        assert callable(row.cleanup)

    obstacles = [
        world.CarObstacle(x=0.0, z=0.0, speed=5.0),
        world.TruckObstacle(x=0.0, z=0.0, speed=4.0),
        world.LogObstacle(x=0.0, z=0.0, speed=3.0),
        world.TrainObstacle(x=0.0, z=0.0, speed=45.0),
    ]
    for obs in obstacles:
        assert hasattr(obs, "x")
        assert hasattr(obs, "y")
        assert hasattr(obs, "z")
        assert hasattr(obs, "width")
        assert hasattr(obs, "height")
        assert hasattr(obs, "depth")
        assert hasattr(obs, "speed")
        assert hasattr(obs, "is_log")
        assert hasattr(obs, "entity")
        assert callable(obs.update)
        assert callable(obs.check_hit)
        assert callable(obs.cleanup)


# =============================================================================
# 2. Row Creation and Type Distribution
# =============================================================================
def test_world_generation_initial_span_and_start_rows() -> None:
    """Verify safe starting rows at spawn and initial lookahead of 25 rows."""
    wg = world.WorldGenerator(seed=42)

    assert wg.min_active_z == -5
    assert wg.max_generated_z == 25
    assert len(wg.active_rows) == 31  # -5 to +25 inclusive

    # Spawn rows [-5 .. 0] must be safe START zones
    for z in range(-5, 1):
        row = wg.get_row(z)
        assert row is not None
        assert row.row_type == RowType.START
        hazard, reason, vx = row.check_player_hazard(0.0, float(z))
        assert hazard is False
        assert reason is None
        assert vx is None


def test_row_type_distribution() -> None:
    """Verify procedural generation produces all 4 active row types in balanced proportions."""
    wg = world.WorldGenerator(seed=123)
    wg.generate_ahead(player_z=0, lookahead=120)

    assert wg.max_generated_z >= 120

    type_counts = {
        RowType.GRASS: 0,
        RowType.ROAD: 0,
        RowType.RIVER: 0,
        RowType.RAIL: 0,
    }

    for z in range(1, wg.max_generated_z + 1):
        row = wg.get_row(z)
        assert row is not None
        if row.row_type in type_counts:
            type_counts[row.row_type] += 1

    total_procedural = sum(type_counts.values())
    assert total_procedural >= 120

    # Ensure every terrain type has healthy presence
    assert type_counts[RowType.GRASS] >= 15, f"Grass count too low: {type_counts[RowType.GRASS]}"
    assert type_counts[RowType.ROAD] >= 20, f"Road count too low: {type_counts[RowType.ROAD]}"
    assert type_counts[RowType.RIVER] >= 10, f"River count too low: {type_counts[RowType.RIVER]}"
    assert type_counts[RowType.RAIL] >= 5, f"Rail count too low: {type_counts[RowType.RAIL]}"


def test_seed_determinism() -> None:
    """Verify identical random seeds generate the exact same sequence of row types."""
    wg1 = world.WorldGenerator(seed=999)
    wg2 = world.WorldGenerator(seed=999)

    wg1.generate_ahead(0, lookahead=50)
    wg2.generate_ahead(0, lookahead=50)

    assert wg1.max_generated_z == wg2.max_generated_z

    for z in range(-5, 51):
        r1 = wg1.get_row(z)
        r2 = wg2.get_row(z)
        assert r1 is not None and r2 is not None
        assert r1.row_type == r2.row_type
        assert len(r1.obstacles) == len(r2.obstacles)


# =============================================================================
# 3. Obstacle Movement and Wrap-Around Math
# =============================================================================
def test_obstacle_movement_and_wrap_around() -> None:
    """Verify horizontal displacement and boundary wrap-around in [-18, 18]."""
    # 1. Positive speed moving right (+X)
    car = world.CarObstacle(x=17.0, z=2.0, speed=10.0, min_wrap_x=-18.0, max_wrap_x=18.0)
    car.update(0.05)  # 17.0 + 0.5 = 17.5 <= 18.0
    assert pytest.approx(car.x, rel=1e-4) == 17.5

    car.update(0.10)  # 17.5 + 1.0 = 18.5 > 18.0 -> wrap to -18.0 + 0.5 = -17.5
    assert pytest.approx(car.x, rel=1e-4) == -17.5

    # 2. Negative speed moving left (-X)
    car_neg = world.CarObstacle(x=-17.0, z=2.0, speed=-10.0, min_wrap_x=-18.0, max_wrap_x=18.0)
    car_neg.update(0.05)  # -17.0 - 0.5 = -17.5 >= -18.0
    assert pytest.approx(car_neg.x, rel=1e-4) == -17.5

    car_neg.update(0.10)  # -17.5 - 1.0 = -18.5 < -18.0 -> wrap to 18.0 - 0.5 = 17.5
    assert pytest.approx(car_neg.x, rel=1e-4) == 17.5


# =============================================================================
# 4. Exact Circle-to-AABB Collision Math
# =============================================================================
def test_collision_circle_aabb_math() -> None:
    """Verify exact 2D circle-to-box collision detection in the horizontal plane."""
    # Obstacle centered at (0, 0), width = 2.0 (X: [-1, +1]), depth = 1.0 (Z: [-0.5, +0.5])
    car = world.CarObstacle(x=0.0, z=0.0, speed=0.0)
    car.width = 2.0
    car.depth = 1.0

    # 1. Inside center
    assert car.check_hit(0.0, 0.0, radius=0.35) is True

    # 2. Near right edge: px = 1.2 -> distance to edge (1.0) is 0.2 <= 0.35
    assert car.check_hit(1.2, 0.0, radius=0.35) is True

    # 3. Far right outside: px = 1.5 -> distance to edge (1.0) is 0.5 > 0.35
    assert car.check_hit(1.5, 0.0, radius=0.35) is False

    # 4. Corner proximity: corner is at (1.0, 0.5)
    # Test point at (1.1, 0.6) -> dx=0.1, dz=0.1 -> dist^2 = 0.02 <= 0.35^2 (0.1225)
    assert car.check_hit(1.1, 0.6, radius=0.35) is True

    # Test point at (1.3, 0.8) -> dx=0.3, dz=0.3 -> dist^2 = 0.18 > 0.1225
    assert car.check_hit(1.3, 0.8, radius=0.35) is False


# =============================================================================
# 5. River Log Riding Detection and Drowning
# =============================================================================
def test_river_log_riding_and_drowning() -> None:
    """Verify log riding returns (False, None, speed) and water returns (True, 'drowned', None)."""
    river = world.RiverRow(z_index=5, speed=3.5, log_count=2)
    assert len(river.obstacles) >= 2

    log0 = river.obstacles[0]
    assert log0.is_log is True
    assert log0.speed != 0.0

    # Player standing directly on log0
    hazard, reason, vx = river.check_player_hazard(log0.x, 5.0)
    assert hazard is False
    assert reason is None
    assert vx == log0.speed, "Player must inherit log horizontal velocity"

    # Player standing far away in open water
    water_x = log0.x + 8.0
    # Ensure water_x does not accidentally hit another log
    for obs in river.obstacles:
        if obs.check_hit(water_x, 5.0):
            water_x += 5.0

    hazard, reason, vx = river.check_player_hazard(water_x, 5.0)
    assert hazard is True
    assert reason == "drowned"
    assert vx is None


def test_log_movement_carries_player() -> None:
    """Verify logs move dynamically with update(dt) and player collision tracks moving log."""
    river = world.RiverRow(z_index=7, speed=4.0, log_count=1)
    log = river.obstacles[0]
    log.x = 0.0
    initial_x = log.x

    dt = 0.5
    river.update(dt)
    expected_x = initial_x + log.speed * dt
    assert pytest.approx(log.x, rel=1e-4) == expected_x

    # Querying old position now drowns, querying new position rides log
    hazard_new, _, vx_new = river.check_player_hazard(log.x, 7.0)
    assert hazard_new is False
    assert vx_new == log.speed


# =============================================================================
# 6. Road Traffic Squashing Hazard
# =============================================================================
def test_road_car_squashing_and_clear_gaps() -> None:
    """Verify vehicles squash the player on collision, but clear road is safe."""
    road = world.RoadRow(z_index=3, speed=7.0, vehicle_count=1)
    assert len(road.obstacles) >= 1
    car = road.obstacles[0]

    # 1. Direct hit with vehicle
    hazard, reason, _ = road.check_player_hazard(car.x, 3.0)
    assert hazard is True
    assert reason == "squashed"

    # 2. Safe gap on road
    safe_x = car.x + 10.0
    if safe_x > 18.0:
        safe_x -= 36.0
    hazard_safe, reason_safe, _ = road.check_player_hazard(safe_x, 3.0)
    assert hazard_safe is False
    assert reason_safe is None


# =============================================================================
# 7. Railway Warning Light Beacon and Bullet Train
# =============================================================================
def test_railway_warning_beacon_and_train_pass() -> None:
    """Verify train warning phase and high-speed bullet train collision."""
    rail = world.RailRow(z_index=8, cycle_interval=4.0, train_speed=50.0)

    # 1. Initially idle: train off-screen
    assert rail.is_train_passing is False
    hazard, reason, _ = rail.check_player_hazard(0.0, 8.0)
    assert hazard is False
    assert reason is None

    # 2. Advance time into warning phase
    rail.train_timer = rail.cycle_interval - rail.warning_duration + 0.1
    rail.update(0.02)
    assert rail.is_warning is True

    # 3. Trigger bullet train pass
    rail.trigger_train(immediate=True)
    assert rail.is_train_passing is True
    assert rail.train.speed != 0.0

    # 4. Player hit by speeding train
    hazard_hit, reason_hit, _ = rail.check_player_hazard(rail.train.x, 8.0)
    assert hazard_hit is True
    assert reason_hit == "squashed"


# =============================================================================
# 8. Procedural Voxel Trees and Path Guarantees
# =============================================================================
def test_grass_row_trees_block_cells_and_maintain_open_paths() -> None:
    """Verify trees block movement, boundary trees block edges, and open paths exist."""
    grass = world.GrassRow(z_index=2)

    # Boundary trees must always block out-of-bounds movement
    for bx in [-13, -12, -11, 11, 12, 13]:
        assert grass.is_blocked(float(bx), 2.0) is True

    # Check playable span [-10 .. +10]
    blocked_count = sum(1 for x in range(CELL_MIN_X, CELL_MAX_X + 1) if grass.is_blocked(float(x), 2.0))
    open_count = sum(1 for x in range(CELL_MIN_X, CELL_MAX_X + 1) if not grass.is_blocked(float(x), 2.0))

    assert blocked_count >= 1, "At least one procedural tree should be placed"
    assert open_count >= 14, "Must guarantee open paths forward for the player"


# =============================================================================
# 9. Streaming Row Pruning and Entity Cleanup
# =============================================================================
def test_streaming_pruning_and_entity_cleanup() -> None:
    """Verify pruning removes old rows and cleans up 3D entities to preserve 500+ FPS."""
    scene = ve.Scene() if ve is not None else None
    wg = world.WorldGenerator(scene=scene, seed=42)

    initial_entity_count = len(scene.entities) if scene is not None else 0
    if scene is not None:
        assert initial_entity_count > 0, "Initial scene entities must be created"

    # Player hops forward to Z = 20
    player_z = 20
    wg.generate_ahead(player_z=player_z, lookahead=25)
    assert wg.max_generated_z == 45

    # Prune rows behind player_z - 8 = 12
    wg.prune_behind(player_z=player_z, keep_behind=8)
    assert wg.min_active_z == 12

    # All rows with Z < 12 must be cleaned up
    for z in range(-5, 12):
        assert z not in wg.active_rows
        assert wg.get_row(z) is None

    if scene is not None:
        # Pruning must prevent unbounded entity growth
        active_entities = len(scene.entities)
        assert active_entities < initial_entity_count * 2.5


# =============================================================================
# 10. World Generator Reset and Full Cycle
# =============================================================================
def test_world_generator_reset() -> None:
    """Verify reset() restores world state, clears old entities, and restarts at Z=0."""
    scene = ve.Scene() if ve is not None else None
    wg = world.WorldGenerator(scene=scene, seed=55)

    # Stream forward heavily
    wg.generate_ahead(50, lookahead=30)
    assert wg.max_generated_z == 80
    wg.prune_behind(50, keep_behind=8)

    # Perform full reset
    wg.reset()
    assert wg.min_active_z == -5
    assert wg.max_generated_z == 25
    assert len(wg.active_rows) == 31
    assert wg.get_row(0) is not None
    assert wg.get_row(0).row_type == RowType.START


def test_generator_query_helpers() -> None:
    """Verify check_hazard and is_cell_blocked on WorldGenerator."""
    wg = world.WorldGenerator(seed=77)

    # 1. Bounds check
    assert wg.is_cell_blocked(-15, 0) is True  # Out of bounds left
    assert wg.is_cell_blocked(15, 0) is True   # Out of bounds right
    assert wg.is_cell_blocked(0, 0) is False   # Safe center spawn

    # 2. Hazard at spawn is safe
    hazard, reason, _ = wg.check_hazard(0.0, 0.0)
    assert hazard is False
    assert reason is None


# =============================================================================
# 11. Stylized Material Wiring & TextureRegistry Integration
# =============================================================================
class MockTransform:
    def __init__(self, position=(0.0, 0.0, 0.0)):
        self.position = position
        self.scale = (1.0, 1.0, 1.0)
        self.rotation = (0.0, 0.0, 0.0)

    def set_position(self, x: float, y: float, z: float) -> None:
        self.position = (x, y, z)

    def set_rotation(self, x: float, y: float, z: float) -> None:
        self.rotation = (x, y, z)


class MockEntity:
    def __init__(
        self,
        name: str = "",
        size=(1.0, 1.0, 1.0),
        position=(0.0, 0.0, 0.0),
        color=None,
        material=None,
        cast_shadows: bool = False,
        has_collision: bool = False,
    ):
        self.name = name
        self.size = size
        self.color = color
        self.material = material
        self.cast_shadows = cast_shadows
        self.has_collision = has_collision
        self.transform = MockTransform(position)
        self.parent = None
        self.root_entity = None


class MockScene:
    def __init__(self):
        self.entities = []

    def create_box(
        self,
        size=(1.0, 1.0, 1.0),
        position=(0.0, 0.0, 0.0),
        color=None,
        material=None,
        cast_shadows: bool = False,
        has_collision: bool = False,
        name: str = "",
    ) -> MockEntity:
        ent = MockEntity(
            name=name,
            size=size,
            position=position,
            color=color,
            material=material,
            cast_shadows=cast_shadows,
            has_collision=has_collision,
        )
        self.entities.append(ent)
        return ent

    def create_entity(self, name: str = "") -> MockEntity:
        ent = MockEntity(name=name)
        self.entities.append(ent)
        return ent

    def remove_entity(self, ent: Any) -> None:
        if ent in self.entities:
            self.entities.remove(ent)


def test_material_wiring_on_rows() -> None:
    """Verify that rows assign stylized materials with expected uv_scale."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    # 1. StartRow and GrassRow: material "grass" with uv_scale (infinite terrain 140.0 or standard 44.0)
    start_row = world.StartRow(0, scene=scene, material_registry=reg)
    assert len(start_row.entities) > 0
    ground_start = start_row.entities[0]
    assert ground_start.material is not None
    assert ground_start.material.name == "grass"
    assert ground_start.material.uv_scale in ((44.0, 1.0), (110.0, 1.0), (140.0, 1.0))

    grass_row = world.GrassRow(1, scene=scene, material_registry=reg)
    ground_grass = grass_row.entities[0]
    assert ground_grass.material is not None
    assert ground_grass.material.name == "grass"
    assert ground_grass.material.uv_scale in ((44.0, 1.0), (110.0, 1.0), (140.0, 1.0))

    # 2. RoadRow: material "asphalt"
    road_row = world.RoadRow(2, scene=scene, material_registry=reg)
    ground_road = road_row.entities[0]
    assert ground_road.material is not None
    assert ground_road.material.name == "asphalt"
    assert ground_road.material.uv_scale in ((44.0, 1.0), (110.0, 1.0), (140.0, 1.0))

    # 3. RiverRow: material "water"
    river_row = world.RiverRow(3, scene=scene, material_registry=reg)
    ground_river = river_row.entities[0]
    assert ground_river.material is not None
    assert ground_river.material.name == "water"
    assert ground_river.material.uv_scale in ((44.0, 1.0), (110.0, 1.0), (140.0, 1.0))

    # 4. RailRow: gravel with material "rail_gravel" and rail ties with "rail_tie"
    rail_row = world.RailRow(4, scene=scene, material_registry=reg)
    ground_rail = rail_row.entities[0]
    assert ground_rail.material is not None
    assert ground_rail.material.name == "rail_gravel"
    assert ground_rail.material.uv_scale in ((44.0, 1.0), (110.0, 1.0), (140.0, 1.0))

    tie_materials = [e.material.name for e in rail_row.entities[1:] if e.material is not None]
    assert "rail_tie" in tie_materials


def test_material_wiring_on_obstacles() -> None:
    """Verify obstacle materials (wood bark/rings, trees, stylized vehicle textures)."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    # 1. LogObstacle: log trunk with material "wood_bark" (uv_scale=(width, 1.0)) and end rings "wood_rings"
    width = 3.5
    log = world.LogObstacle(0.0, 0.0, speed=2.0, width=width, scene=scene, material_registry=reg)
    assert log.entity is not None
    assert log.entity.material is not None
    assert log.entity.material.name == "wood_bark"
    assert log.entity.material.uv_scale == (width, 1.0)

    assert len(log.sub_entities) >= 2
    for ring_ent, _ in log.sub_entities:
        assert ring_ent.material is not None
        assert ring_ent.material.name == "wood_rings"

    # 2. VoxelTree: trunk with material "wood_bark" and foliage with "tree_leaves"
    tree = world.VoxelTree(0.0, 0.0, scene=scene, material_registry=reg)
    assert len(tree.entities) == 2
    trunk, foliage = tree.entities[0], tree.entities[1]
    assert trunk.material is not None
    assert trunk.material.name == "wood_bark"
    assert foliage.material is not None
    assert foliage.material.name == "tree_leaves"

    # 3. CarObstacle and TruckObstacle: cab/chassis, cabin, cargo, and wheel textures
    car = world.CarObstacle(0.0, 0.0, speed=5.0, scene=scene, material_registry=reg)
    assert car.entity is not None
    assert car.entity.material is not None
    assert car.entity.material.name in ("vehicle", "car_grille")

    car_cabin = [ent for ent, _ in car.sub_entities if ent.name == "CarCabin"][0]
    assert car_cabin.material is not None
    assert car_cabin.material.name == "car_cabin"

    car_wheels = [ent for ent, _ in car.sub_entities if ent.name == "CarWheel"]
    assert len(car_wheels) == 4
    for w in car_wheels:
        assert w.material is not None
        assert w.material.name == "car_wheel"

    truck = world.TruckObstacle(0.0, 0.0, speed=4.0, scene=scene, material_registry=reg)
    assert truck.entity is not None
    assert truck.entity.material is not None
    assert truck.entity.material.name in ("truck_cargo", "vehicle", "car_grille")

    truck_cabin = [ent for ent, _ in truck.sub_entities if ent.name == "TruckCabin"][0]
    assert truck_cabin.material is not None
    assert truck_cabin.material.name == "car_cabin"

    truck_wheels = [ent for ent, _ in truck.sub_entities if ent.name == "TruckWheel"]
    assert len(truck_wheels) == 6
    for w in truck_wheels:
        assert w.material is not None
        assert w.material.name == "car_wheel"

    # 4. TrainObstacle: body with train_body, windows with train_window, nose with train_front
    train = world.TrainObstacle(0.0, 0.0, speed=45.0, scene=scene, material_registry=reg)
    assert train.entity is not None
    assert train.entity.material is not None
    assert train.entity.material.name == "train_body"

    train_windows = [ent for ent, _ in train.sub_entities if ent.name == "BulletTrainWindows"][0]
    assert train_windows.material is not None
    assert train_windows.material.name == "train_window"

    train_nose = [ent for ent, _ in train.sub_entities if ent.name == "BulletTrainNose"][0]
    assert train_nose.material is not None
    assert train_nose.material.name == "train_front"

    # Roof fluting receives train_body material
    roof_flutes = [ent for ent, _ in train.sub_entities if "RoofFlute" in ent.name]
    assert len(roof_flutes) == 2
    for rf in roof_flutes:
        assert rf.material is not None
        assert rf.material.name == "train_body"

    # Headlights present
    headlights = [ent for ent, _ in train.sub_entities if "Headlight" in ent.name or "HighBeam" in ent.name]
    assert len(headlights) == 3


def test_material_wiring_on_player() -> None:
    """Verify duck material application on PlayerController fallback voxel duck."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    p = player.PlayerController(scene=scene, material_registry=reg)
    assert p.entity is not None
    assert p.entity.material is not None
    assert p.entity.material.name == "duck"

    # Verify voxel body and head parts received duck material
    duck_parts_with_mat = [part for part in p.voxel_parts if getattr(part, "material", None) is not None]
    assert len(duck_parts_with_mat) >= 2
    for part in duck_parts_with_mat:
        assert part.material.name == "duck"


def test_world_generator_material_propagation() -> None:
    """Verify WorldGenerator propagates material_registry to newly streamed rows."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    wg = world.WorldGenerator(scene=scene, material_registry=reg, seed=99)
    wg.generate_ahead(0, lookahead=15)

    for z, row in wg.active_rows.items():
        assert row.material_registry is reg
        if row.entities:
            ground = row.entities[0]
            assert ground.material is not None


def test_backward_compatibility_none_scene_and_registry() -> None:
    """Verify full backward compatibility when scene and material_registry are None."""
    rows = [
        world.StartRow(0, scene=None, material_registry=None),
        world.GrassRow(1, scene=None, material_registry=None),
        world.RoadRow(2, scene=None, material_registry=None),
        world.RiverRow(3, scene=None, material_registry=None),
        world.RailRow(4, scene=None, material_registry=None),
    ]
    for r in rows:
        assert len(r.entities) == 0
        r.update(0.016)
        r.cleanup(None)

    obstacles = [
        world.CarObstacle(0.0, 0.0, speed=5.0, scene=None, material_registry=None),
        world.TruckObstacle(0.0, 0.0, speed=4.0, scene=None, material_registry=None),
        world.LogObstacle(0.0, 0.0, speed=2.0, scene=None, material_registry=None),
        world.TrainObstacle(0.0, 0.0, speed=40.0, scene=None, material_registry=None),
    ]
    for obs in obstacles:
        obs.update(0.016)
        obs.cleanup(None)

    tree = world.VoxelTree(0.0, 0.0, scene=None, material_registry=None)
    assert len(tree.entities) == 0
    tree.cleanup(None)

    p = player.PlayerController(scene=None, material_registry=None)
    assert p.entity is None
    p.hop(0, 1)
    p.update(0.016)


# =============================================================================
# 12. Road Markings & Multi-Lane Configuration
# =============================================================================

def test_road_markings_single_lane() -> None:
    """Verify single-direction standalone road has outer edge lines and no center dashes."""
    scene = MockScene()
    road = world.RoadRow(z_index=4, scene=scene)

    entity_names = [e.name for e in road.entities]
    assert "RoadAsphalt_4" in entity_names
    assert "RoadEdgeSouth_4" in entity_names
    assert "RoadEdgeNorth_4" in entity_names

    # Verify positions: outer borders at z ± 0.45
    south_edge = [e for e in road.entities if e.name == "RoadEdgeSouth_4"][0]
    north_edge = [e for e in road.entities if e.name == "RoadEdgeNorth_4"][0]
    assert pytest.approx(south_edge.transform.position[2], abs=0.01) == 4.0 - 0.45
    assert pytest.approx(north_edge.transform.position[2], abs=0.01) == 4.0 + 0.45

    # A single-direction road lane must NOT have a dashed line down the center
    center_dashes = [e for e in road.entities if "LaneMarker_4" in e.name or (
        pytest.approx(e.transform.position[2], abs=0.05) == 4.0 and e.name != "RoadAsphalt_4"
    )]
    assert len(center_dashes) == 0


def test_road_markings_consecutive_same_direction() -> None:
    """Verify consecutive road rows going in the same direction place dashed divider along shared border."""
    scene = MockScene()
    # Lane 1 at z=4 going right (+1.0) with next road at z=5 also going right (+1.0)
    road1 = world.RoadRow(
        z_index=4,
        scene=scene,
        has_prev_road=False,
        has_next_road=True,
        direction=1.0,
        next_direction=1.0,
    )

    names1 = [e.name for e in road1.entities]
    assert "RoadEdgeSouth_4" in names1
    assert "RoadEdgeNorth_4" not in names1  # Shared border, not outer north edge

    dashed_dividers = [e for e in road1.entities if "LaneDivider_4" in e.name]
    assert len(dashed_dividers) > 0
    # Shared border is at z = 4 + 0.5 = 4.5
    for div in dashed_dividers:
        assert pytest.approx(div.transform.position[2], abs=0.01) == 4.5


def test_road_markings_consecutive_opposing_directions() -> None:
    """Verify consecutive road rows with opposing traffic place distinct center divider."""
    scene = MockScene()
    # Lane 1 at z=2 going right (+1.0), lane 2 at z=3 going left (-1.0)
    road1 = world.RoadRow(
        z_index=2,
        scene=scene,
        has_prev_road=False,
        has_next_road=True,
        direction=1.0,
        next_direction=-1.0,
    )

    names1 = [e.name for e in road1.entities]
    assert "RoadEdgeSouth_2" in names1
    assert "RoadEdgeNorth_2" not in names1
    assert "CenterDividerA_2" in names1
    assert "CenterDividerB_2" in names1

    # Distinct center divider placed along shared border z = 2.5
    div_a = [e for e in road1.entities if e.name == "CenterDividerA_2"][0]
    div_b = [e for e in road1.entities if e.name == "CenterDividerB_2"][0]
    assert pytest.approx(div_a.transform.position[2], abs=0.1) == 2.5
    assert pytest.approx(div_b.transform.position[2], abs=0.1) == 2.5


def test_vehicle_and_train_offscreen_spawning_and_wrap() -> None:
    """Verify vehicles wrap at [-48, 48], trains at ±60, and logs at [-38, 38] to stay off-screen."""
    # 1. RoadRow cars & trucks wrap outside visible screen
    road = world.RoadRow(z_index=3, speed=8.0, vehicle_count=2)
    for obs in road.obstacles:
        assert obs.min_wrap_x == -48.0
        assert obs.max_wrap_x == 48.0

    # 2. RailRow train pass starts and exits far off-screen (±60.0)
    rail = world.RailRow(z_index=5, train_speed=45.0)
    rail._start_train_pass()
    assert abs(rail.train.x) >= 60.0  # Spawn position far off-screen
    assert rail.is_train_passing is True

    # 3. RiverRow logs wrap at [-38, 38]
    river = world.RiverRow(z_index=6, speed=3.5, log_count=2)
    for obs in river.obstacles:
        assert obs.min_wrap_x == -38.0
        assert obs.max_wrap_x == 38.0


def test_horizon_mountain_backdrop() -> None:
    """Verify panoramic voxel mountain backdrop initializes, streams with lookahead, and cleans up."""
    scene = MockScene()
    backdrop = world.HorizonBackdrop(scene=scene)
    assert len(backdrop.entities) > 30

    # Check peaks span panoramic width [-72 .. 72]
    xs = [rel_x for _, rel_x, _, _ in backdrop.peak_data]
    assert min(xs) <= -60.0
    assert max(xs) >= 60.0

    # Update forward Z coordinate
    backdrop.update(forward_z=80.0)
    assert backdrop.current_forward_z == 80.0

    # Cleanup removes all backdrop entities
    backdrop.cleanup()
    assert len(backdrop.entities) == 0
    assert len(backdrop.peak_data) == 0

    # WorldGenerator seamlessly manages backdrop
    wg = world.WorldGenerator(scene=scene, seed=42)
    assert wg.backdrop is not None
    assert len(wg.backdrop.entities) > 0
    wg.generate_ahead(0, lookahead=50)
    assert wg.backdrop.current_forward_z >= 24.0



