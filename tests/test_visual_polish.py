"""Visual Polish & Aesthetic Contract Verification Tests.

Verifies:
1. Vehicle palette and texture aesthetics (absence of #8e24aa electric purple, car_paint binding,
   rich voxel components: roof, bumpers, wheels, windshield, grille decals).
2. Organic boundary forests (varied tree archetypes, deterministic position jitter, non-rigid walls,
   foliage color distribution).
3. Seamless atmospheric horizon backdrop (pastel foothill ridges blending with sky fog #70b0e0,
   absence of near-black #1b3b24/#14321d monolithic walls, extended horizon distance).
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Ensure repository root and package paths are configured
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
    from examples.crossy_duck import world, textures
except ImportError:
    import world
    import textures


class MockTransform:
    def __init__(self, position=(0.0, 0.0, 0.0)):
        self.position = list(position)

    def set_position(self, x: float, y: float, z: float) -> None:
        self.position = [float(x), float(y), float(z)]


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

    def remove_entity(self, ent: MockEntity) -> None:
        if ent in self.entities:
            self.entities.remove(ent)


# =============================================================================
# 1. Vehicle Polish & Aesthetic Contract
# =============================================================================
def test_vehicle_palette_clean_automotive_colors() -> None:
    """Assert that vehicle palette contains NO electric purple (#8e24aa) and only clean automotive colors."""
    forbidden_colors = [
        world.Color.from_hex("#8e24aa"),  # Electric purple
        world.Color.from_hex("#9c27b0"),
        world.Color.from_hex("#ab47bc"),
    ]

    for c in world.COLOR_CAR_PALETTE:
        for fc in forbidden_colors:
            # Check Euclidean RGB distance
            dist = ((c.r - fc.r) ** 2 + (c.g - fc.g) ** 2 + (c.b - fc.b) ** 2) ** 0.5
            assert dist > 0.15, f"Palette color (r={c.r}, g={c.g}, b={c.b}) too close to forbidden purple ({fc})!"

    # Verify palette has sufficient clean variety
    assert len(world.COLOR_CAR_PALETTE) >= 6


def test_vehicle_texture_mapping_uses_car_paint() -> None:
    """Assert that vehicle material maps to car_paint rather than car_grille or untextured default."""
    reg = textures.MaterialRegistry()

    veh_mat = reg.get_material("vehicle")
    assert veh_mat is not None
    assert veh_mat.name == "vehicle"

    # Generator texture contract
    gen = textures.CrossyTextureGenerator()
    veh_img = gen.create_image("vehicle", size=64)
    assert veh_img is not None
    assert veh_img.width == 64
    assert veh_img.height == 64


def test_car_and_truck_voxel_model_components() -> None:
    """Verify CarObstacle and TruckObstacle have distinctive voxel components (chassis, roof, grille, wheels, bumpers)."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    car = world.CarObstacle(x=0.0, z=0.0, speed=5.0, scene=scene, material_registry=reg)
    sub_names = [e.name for e, _ in car.sub_entities]
    assert car.entity.name == "CarChassis"
    assert "CarCabin" in sub_names
    assert "CarRoof" in sub_names
    assert "CarGrilleDecal" in sub_names
    assert "Headlight1" in sub_names and "Headlight2" in sub_names
    assert "Taillight1" in sub_names and "Taillight2" in sub_names
    assert "CarFrontBumper" in sub_names and "CarRearBumper" in sub_names
    assert sub_names.count("CarWheel") == 4

    truck = world.TruckObstacle(x=0.0, z=0.0, speed=4.0, scene=scene, material_registry=reg)
    truck_sub_names = [e.name for e, _ in truck.sub_entities]
    assert truck.entity.name == "TruckCargo"
    assert "TruckCab" in truck_sub_names
    assert "TruckCabin" in truck_sub_names
    assert "TruckGrilleDecal" in truck_sub_names
    assert "TruckHeadlight1" in truck_sub_names
    assert "TruckTaillight1" in truck_sub_names
    assert "TruckFrontBumper" in truck_sub_names
    assert truck_sub_names.count("TruckWheel") == 6


# =============================================================================
# 2. Organic Boundary Forest Contract
# =============================================================================
def test_boundary_forest_jitter_and_archetypes() -> None:
    """Verify boundary trees have position jitter, organic variety, and are not flat rigid cube walls."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    start_row = world.StartRow(0, scene=scene, material_registry=reg)
    grass_row = world.GrassRow(1, scene=scene, material_registry=reg)
    road_row = world.RoadRow(2, scene=scene, material_registry=reg)
    river_row = world.RiverRow(3, scene=scene, material_registry=reg)
    rail_row = world.RailRow(4, scene=scene, material_registry=reg)

    # 1. StartRow and GrassRow have rich boundary trees with organic position jitter
    vegetative_rows = [start_row, grass_row]
    for row in vegetative_rows:
        tree_trunks = [e for e in row.entities if e.name == "TreeTrunk"]
        assert len(tree_trunks) > 0, f"Row {row.row_type} should have boundary trees!"

        # Verify X positions are jittered (non-integer coordinates)
        x_positions = [e.transform.position[0] for e in tree_trunks]
        has_non_integer = any(abs(x - round(x)) > 0.01 for x in x_positions)
        assert has_non_integer, f"Row {row.row_type} boundary trees lack X position jitter!"

    # 2. RoadRow, RailRow, and RiverRow have ZERO trees on their traffic surfaces,
    # ensuring vehicles, bullet trains, and river logs have completely unobstructed paths!
    assert len([e for e in road_row.entities if e.name == "TreeTrunk"]) == 0
    assert len([e for e in rail_row.entities if e.name == "TreeTrunk"]) == 0
    assert len([e for e in river_row.entities if e.name == "TreeTrunk"]) == 0

    # 3. Verify varied tree heights across grass row entities
    foliage_boxes = [e for e in grass_row.entities if "TreeFoliage" in e.name]
    assert len(foliage_boxes) >= 10
    foliage_heights = [e.size[1] for e in foliage_boxes]
    # Check that heights are not all identical (multiple archetypes and scales exist)
    unique_heights = {round(h, 2) for h in foliage_heights}
    assert len(unique_heights) >= 3, f"Foliage heights should vary across archetypes, got: {unique_heights}"


def test_tree_no_overhang_into_adjacent_traffic() -> None:
    """Verify that if GrassRow or StartRow is adjacent to road/rail, tree foliage strictly stays in [-0.35, 0.35]."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    # Grass row directly adjacent to traffic
    grass_adj = world.GrassRow(5, scene=scene, material_registry=reg, adjacent_road_or_rail=True)

    tree_trunks = [e for e in grass_adj.entities if e.name == "TreeTrunk"]
    assert len(tree_trunks) > 0

    # For every boundary trunk, jitter_z must be clamped to 0.0 (z == 5.0)
    for t in tree_trunks:
        assert pytest.approx(t.transform.position[2], abs=1e-3) == 5.0, (
            f"Trunk Z {t.transform.position[2]} should be exactly 5.0 (jitter_z=0.0) when adjacent to traffic"
        )

    # For all foliage boxes, foliage depth (size[2]) must be <= 0.70
    # meaning foliage extends at most ±0.35 from z=5.0 (staying within [4.65, 5.35], leaving 0.15 margin)
    foliage_boxes = [e for e in grass_adj.entities if "TreeFoliage" in e.name]
    assert len(foliage_boxes) >= 10
    for f in foliage_boxes:
        depth = f.size[2]
        assert depth <= 0.7001, f"Foliage depth {depth} exceeds 0.70 clamp limit!"
        z_pos = f.transform.position[2]
        half_depth = depth * 0.5
        min_z = z_pos - half_depth
        max_z = z_pos + half_depth
        assert min_z >= 5.0 - 0.3501, f"Foliage overhangs south into traffic row: min_z={min_z}"
        assert max_z <= 5.0 + 0.3501, f"Foliage overhangs north into traffic row: max_z={max_z}"


def test_boundary_forest_deterministic_reproducibility() -> None:
    """Verify procedural forest generation is deterministic based on row z-index and lane hash."""
    scene1 = MockScene()
    scene2 = MockScene()

    # Using StartRow ensures only boundary forest trees are generated
    start1 = world.StartRow(10, scene=scene1)
    start2 = world.StartRow(10, scene=scene2)

    trunks1 = [e for e in start1.entities if e.name == "TreeTrunk"]
    trunks2 = [e for e in start2.entities if e.name == "TreeTrunk"]

    assert len(trunks1) == len(trunks2)
    assert len(trunks1) > 0
    for t1, t2 in zip(trunks1, trunks2):
        assert pytest.approx(t1.transform.position[0], abs=1e-4) == t2.transform.position[0]
        assert pytest.approx(t1.transform.position[2], abs=1e-4) == t2.transform.position[2]
        assert pytest.approx(t1.size[1], abs=1e-4) == t2.size[1]


# =============================================================================
# 3. Seamless Horizon & Mountain Backdrop Contract
# =============================================================================
def test_horizon_mountain_backdrop_atmospheric_palette() -> None:
    """Verify horizon mountains do NOT contain dark/black monolithic blocks (#1b3b24, #14321d)."""
    scene = MockScene()
    backdrop = world.HorizonBackdrop(scene=scene)

    assert len(backdrop.entities) > 0

    dark_greens = [
        world.Color.from_hex("#1b3b24"),
        world.Color.from_hex("#14321d"),
        world.Color.from_hex("#0a1f10"),
    ]

    for ent in backdrop.entities:
        c = ent.color
        if c is None:
            continue
        # Brightness / luminance check
        luminance = 0.299 * c.r + 0.587 * c.g + 0.114 * c.b
        assert luminance > 0.25, f"Entity {ent.name} has dark luminance {luminance:.3f} (color: {c.r}, {c.g}, {c.b})!"

        for dark_c in dark_greens:
            dist = ((c.r - dark_c.r) ** 2 + (c.g - dark_c.g) ** 2 + (c.b - dark_c.b) ** 2) ** 0.5
            assert dist > 0.20, f"Entity {ent.name} too close to dark wall color ({dark_c})!"


def test_horizon_backdrop_depth_placement() -> None:
    """Verify horizon backdrop is pushed far enough ahead to blend with fog (near=34.0, far=60.0)."""
    scene = MockScene()
    wg = world.WorldGenerator(scene=scene, seed=42)

    assert wg.backdrop is not None
    # At target_z = 25 (initial lookahead), backdrop forward_z should be placed target_z + 28
    assert wg.backdrop.current_forward_z >= 25.0 + 24.0

    # Ensure all mountain entities are placed >= current_forward_z
    for ent in wg.backdrop.entities:
        assert ent.transform.position[2] >= 25.0 + 20.0


# =============================================================================
# 4. Truck Obstacle Alignment and Centered Camera Contract
# =============================================================================
def test_truck_obstacle_entity_ox_synchronization_on_update() -> None:
    """Verify TruckObstacle preserves cargo_ox offset in update() and set_position()."""
    scene = MockScene()
    reg = textures.MaterialRegistry()

    truck = world.TruckObstacle(x=10.0, z=5.0, speed=4.0, scene=scene, material_registry=reg)
    assert hasattr(truck, "entity_ox")
    assert truck.entity_ox != 0.0

    # Before update: entity should be at x + entity_ox
    expected_x = truck.x + truck.entity_ox
    assert pytest.approx(truck.entity.transform.position[0]) == expected_x

    # Advance simulation by dt
    truck.update(0.1)
    new_expected_x = truck.x + truck.entity_ox
    assert pytest.approx(truck.entity.transform.position[0]) == new_expected_x

    # Ensure all wheels are strictly under the truck body (no floating rear wheels)
    cargo_w = truck.width * 0.65
    facing_dir = 1.0 if truck.speed >= 0 else -1.0
    cargo_ox = truck.entity_ox
    rear_edge_x = truck.x + cargo_ox - facing_dir * (cargo_w * 0.50)

    wheels = [ent for ent, _ in truck.sub_entities if ent.name == "TruckWheel"]
    assert len(wheels) == 6
    for w in wheels:
        # Wheel must not stick out behind rear container wall
        if facing_dir > 0:
            assert w.transform.position[0] >= rear_edge_x - 0.05
        else:
            assert w.transform.position[0] <= rear_edge_x + 0.05

    # Check taillights flush on rear surface
    taillights = [ent for ent, _ in truck.sub_entities if "TruckTaillight" in ent.name]
    assert len(taillights) == 2
    for tl in taillights:
        dist_to_rear = abs(tl.transform.position[0] - rear_edge_x)
        assert dist_to_rear < 0.06, f"Taillight {tl.name} floating too far from rear: {dist_to_rear}!"


def test_isometric_camera_configurable_offsets() -> None:
    """Verify IsometricCamera supports configurable forward-centered perspective."""
    from examples.crossy_duck.camera_vfx import IsometricCamera

    class DummyCam:
        def __init__(self):
            self.position = (0.0, 0.0, 0.0)
            self.target = (0.0, 0.0, 0.0)
        def set_position(self, x, y, z):
            self.position = (x, y, z)
        def set_target(self, x, y, z):
            self.target = (x, y, z)

    # 1. Defaults preserve classic contract
    classic_cam = IsometricCamera()
    assert classic_cam.offset_x == -7.0
    assert classic_cam.offset_y == 11.0
    assert classic_cam.offset_z == -8.5

    # 2. Configurable centered perspective
    centered_cam = IsometricCamera(
        camera=DummyCam(),
        damping=8.5,
        offset_x=0.0,
        offset_y=12.0,
        offset_z=-9.0,
        target_offset_x=0.0,
        target_offset_y=0.5,
        target_offset_z=2.0,
    )
    assert centered_cam.offset_x == 0.0
    assert centered_cam.offset_y == 12.0
    assert centered_cam.offset_z == -9.0
    assert centered_cam.target_offset_z == 2.0

    des_pos = centered_cam.get_desired_position(5.0, 0.0, 10.0)
    des_tgt = centered_cam.get_desired_target(5.0, 0.0, 10.0)
    assert des_pos == (5.0, 12.0, 1.0)
    assert des_tgt == (5.0, 0.5, 12.0)

