"""Crossy Duck - Procedural World Generator and Voxel Geometry System.

Implements high-performance streaming procedural terrain and voxel obstacles
for Crossy Duck in VelocityEngine, adhering strictly to contracts/crossy_contracts.py.
"""

from __future__ import annotations

import math
import random
from typing import Tuple, List, Optional, Any, Dict, Set, Sequence

from contracts.crossy_contracts import (
    GRID_STEP,
    WORLD_WIDTH_CELLS,
    CELL_MIN_X,
    CELL_MAX_X,
    RowType,
    PlayerStatus,
    ObstacleContract,
    WorldRowContract,
    WorldGeneratorContract,
)

try:
    import VelocityEngine as ve
    from VelocityEngine import (
        Color,
        WHITE,
        RED,
        GREEN,
        BLUE,
        YELLOW,
        CYAN,
        MAGENTA,
        GRAY,
        DARK_GRAY,
        WARM_WHITE,
    )
except ImportError:
    ve = None

    class Color:  # type: ignore
        def __init__(self, r: float = 1.0, g: float = 1.0, b: float = 1.0, a: float = 1.0) -> None:
            self.r = float(r)
            self.g = float(g)
            self.b = float(b)
            self.a = float(a)

        @classmethod
        def from_hex(cls, hex_str: str) -> "Color":
            h = hex_str.lstrip("#")
            if len(h) == 6:
                r, g, b = int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0
                return cls(r, g, b, 1.0)
            return cls(1.0, 1.0, 1.0, 1.0)

    WHITE = Color(1.0, 1.0, 1.0, 1.0)
    RED = Color(1.0, 0.0, 0.0, 1.0)
    GREEN = Color(0.0, 1.0, 0.0, 1.0)
    BLUE = Color(0.0, 0.0, 1.0, 1.0)
    YELLOW = Color(1.0, 1.0, 0.0, 1.0)
    CYAN = Color(0.0, 1.0, 1.0, 1.0)
    MAGENTA = Color(1.0, 0.0, 1.0, 1.0)
    GRAY = Color(0.5, 0.5, 0.5, 1.0)
    DARK_GRAY = Color(0.2, 0.2, 0.2, 1.0)
    WARM_WHITE = Color(1.0, 0.95, 0.85, 1.0)


# =============================================================================
# Color Palette for Voxel Aesthetics
# =============================================================================
COLOR_GRASS_EVEN = Color.from_hex("#55a840")
COLOR_GRASS_ODD = Color.from_hex("#4c9938")
COLOR_START_ZONE = Color.from_hex("#5cb85c")

COLOR_ROAD_ASPHALT = Color.from_hex("#21252b")
COLOR_ROAD_MARKER = Color.from_hex("#f5d76e")

COLOR_RIVER_WATER = Color.from_hex("#0288d1")
COLOR_LOG_WOOD = Color.from_hex("#795548")
COLOR_LOG_END_RING = Color.from_hex("#a1887f")

COLOR_RAIL_GRAVEL = Color.from_hex("#616161")
COLOR_RAIL_TIE = Color.from_hex("#3e2723")
COLOR_RAIL_STEEL = Color.from_hex("#b0bec5")

COLOR_TRAIN_BODY = Color.from_hex("#e53935")
COLOR_TRAIN_WINDOWS = Color.from_hex("#263238")

COLOR_BEACON_ACTIVE = Color.from_hex("#ff1744")
COLOR_BEACON_IDLE = Color.from_hex("#37474f")
COLOR_BEACON_POST = Color.from_hex("#212121")

COLOR_TREE_TRUNK = Color.from_hex("#5d4037")
COLOR_TREE_FOLIAGE = [
    Color.from_hex("#2e7d32"),
    Color.from_hex("#388e3c"),
    Color.from_hex("#1b5e20"),
]

COLOR_CAR_PALETTE = [
    Color.from_hex("#e53935"),  # Cherry Red
    Color.from_hex("#1e88e5"),  # Sporty Blue
    Color.from_hex("#fbc02d"),  # Taxi Yellow
    Color.from_hex("#fb8c00"),  # Vibrant Orange
    Color.from_hex("#8e24aa"),  # Electric Purple
    Color.from_hex("#00897b"),  # Mint Teal
]
COLOR_HEADLIGHT = Color.from_hex("#fff59d")
COLOR_CABIN_WINDOW = Color.from_hex("#37474f")
COLOR_TRUCK_CARGO = Color.from_hex("#eceff1")


# =============================================================================
# Obstacle Implementations (Vehicles, Trains, Floating Logs)
# =============================================================================
class BaseObstacle:
    """Base class for all dynamic horizontal obstacles in the world."""

    def __init__(
        self,
        x: float,
        y: float,
        z: float,
        width: float,
        height: float,
        depth: float,
        speed: float,
        is_log: bool = False,
        min_wrap_x: float = -18.0,
        max_wrap_x: float = 18.0,
        scene: Optional[Any] = None,
    ) -> None:
        self.x: float = float(x)
        self.y: float = float(y)
        self.z: float = float(z)
        self.width: float = float(width)
        self.height: float = float(height)
        self.depth: float = float(depth)
        self.speed: float = float(speed)
        self.is_log: bool = bool(is_log)
        self.min_wrap_x: float = float(min_wrap_x)
        self.max_wrap_x: float = float(max_wrap_x)
        self.entity: Any = None
        self.sub_entities: List[Tuple[Any, Tuple[float, float, float]]] = []

    def update(self, dt: float) -> None:
        """Advance obstacle horizontally and handle wrap-around."""
        if dt <= 0.0 or self.speed == 0.0:
            return

        self.x += self.speed * dt

        # Wrap around boundary
        wrap_span = self.max_wrap_x - self.min_wrap_x
        if self.speed > 0.0 and self.x > self.max_wrap_x:
            self.x = self.min_wrap_x + ((self.x - self.max_wrap_x) % wrap_span)
        elif self.speed < 0.0 and self.x < self.min_wrap_x:
            self.x = self.max_wrap_x - ((self.min_wrap_x - self.x) % wrap_span)

        # Synchronize 3D scene entity transform
        if self.entity is not None and hasattr(self.entity, "transform"):
            self.entity.transform.set_position(self.x, self.y, self.z)

        for sub_ent, (ox, oy, oz) in self.sub_entities:
            if hasattr(sub_ent, "transform"):
                sub_ent.transform.set_position(self.x + ox, self.y + oy, self.z + oz)

    def check_hit(self, px: float, pz: float, radius: float = 0.35) -> bool:
        """Check circle-to-AABB intersection in the XZ horizontal ground plane."""
        half_w = self.width * 0.5
        half_d = self.depth * 0.5

        clamped_x = max(self.x - half_w, min(px, self.x + half_w))
        clamped_z = max(self.z - half_d, min(pz, self.z + half_d))

        dx = px - clamped_x
        dz = pz - clamped_z

        return (dx * dx + dz * dz) <= (radius * radius)

    def cleanup(self, scene: Any) -> None:
        """Remove all 3D scene entities associated with this obstacle."""
        if scene is not None:
            if self.entity is not None:
                try:
                    scene.remove_entity(self.entity)
                except Exception:
                    pass
                self.entity = None

            for sub_ent, _ in self.sub_entities:
                try:
                    scene.remove_entity(sub_ent)
                except Exception:
                    pass
            self.sub_entities.clear()


class CarObstacle(BaseObstacle):
    """Voxel car with colored chassis, tinted cabin, headlights, and shadow casting."""

    def __init__(
        self,
        x: float,
        z: float,
        speed: float,
        color: Optional[Color] = None,
        min_wrap_x: float = -18.0,
        max_wrap_x: float = 18.0,
        scene: Optional[Any] = None,
    ) -> None:
        width = 2.0
        height = 0.75
        depth = 0.85
        y = 0.35
        super().__init__(
            x=x,
            y=y,
            z=z,
            width=width,
            height=height,
            depth=depth,
            speed=speed,
            is_log=False,
            min_wrap_x=min_wrap_x,
            max_wrap_x=max_wrap_x,
            scene=scene,
        )

        car_col = color if color is not None else random.choice(COLOR_CAR_PALETTE)

        if scene is not None:
            # 1. Main chassis
            self.entity = scene.create_box(
                size=(width, 0.45, depth),
                position=(self.x, self.y, self.z),
                color=car_col,
                cast_shadows=True,
                name="CarChassis",
            )
            # 2. Cabin top
            cabin = scene.create_box(
                size=(width * 0.55, 0.35, depth * 0.8),
                position=(self.x, self.y + 0.38, self.z),
                color=COLOR_CABIN_WINDOW,
                cast_shadows=True,
                name="CarCabin",
            )
            self.sub_entities.append((cabin, (0.0, 0.38, 0.0)))

            # 3. Headlights (in direction of movement)
            facing_dir = 1.0 if speed >= 0 else -1.0
            hl_x = facing_dir * (width * 0.48)
            hl1 = scene.create_box(
                size=(0.12, 0.15, 0.18),
                position=(self.x + hl_x, self.y, self.z - 0.22),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="Headlight1",
            )
            hl2 = scene.create_box(
                size=(0.12, 0.15, 0.18),
                position=(self.x + hl_x, self.y, self.z + 0.22),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="Headlight2",
            )
            self.sub_entities.append((hl1, (hl_x, 0.0, -0.22)))
            self.sub_entities.append((hl2, (hl_x, 0.0, 0.22)))


class TruckObstacle(BaseObstacle):
    """Voxel delivery truck with cab, large cargo container, and headlights."""

    def __init__(
        self,
        x: float,
        z: float,
        speed: float,
        color: Optional[Color] = None,
        min_wrap_x: float = -18.0,
        max_wrap_x: float = 18.0,
        scene: Optional[Any] = None,
    ) -> None:
        width = 3.6
        height = 1.15
        depth = 0.90
        y = 0.55
        super().__init__(
            x=x,
            y=y,
            z=z,
            width=width,
            height=height,
            depth=depth,
            speed=speed,
            is_log=False,
            min_wrap_x=min_wrap_x,
            max_wrap_x=max_wrap_x,
            scene=scene,
        )

        cab_col = color if color is not None else random.choice(COLOR_CAR_PALETTE)

        if scene is not None:
            facing_dir = 1.0 if speed >= 0 else -1.0
            cargo_w = width * 0.65
            cab_w = width * 0.35

            cargo_ox = -facing_dir * (cab_w * 0.5)
            cab_ox = facing_dir * (cargo_w * 0.5)

            # 1. Main cargo container
            self.entity = scene.create_box(
                size=(cargo_w, height, depth),
                position=(self.x + cargo_ox, self.y, self.z),
                color=COLOR_TRUCK_CARGO,
                cast_shadows=True,
                name="TruckCargo",
            )

            # 2. Cab
            cab = scene.create_box(
                size=(cab_w, height * 0.75, depth * 0.88),
                position=(self.x + cab_ox, self.y - 0.12, self.z),
                color=cab_col,
                cast_shadows=True,
                name="TruckCab",
            )
            self.sub_entities.append((cab, (cab_ox, -0.12, 0.0)))

            # 3. Headlights
            hl_x = cab_ox + facing_dir * (cab_w * 0.48)
            hl1 = scene.create_box(
                size=(0.12, 0.18, 0.18),
                position=(self.x + hl_x, self.y - 0.2, self.z - 0.25),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="TruckHeadlight1",
            )
            hl2 = scene.create_box(
                size=(0.12, 0.18, 0.18),
                position=(self.x + hl_x, self.y - 0.2, self.z + 0.25),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="TruckHeadlight2",
            )
            self.sub_entities.append((hl1, (hl_x, -0.2, -0.25)))
            self.sub_entities.append((hl2, (hl_x, -0.2, 0.25)))


class LogObstacle(BaseObstacle):
    """Floating wooden river log that acts as a safe player carrier."""

    def __init__(
        self,
        x: float,
        z: float,
        speed: float,
        width: float = 3.2,
        min_wrap_x: float = -19.0,
        max_wrap_x: float = 19.0,
        scene: Optional[Any] = None,
    ) -> None:
        height = 0.35
        depth = 0.78
        y = 0.08
        super().__init__(
            x=x,
            y=y,
            z=z,
            width=width,
            height=height,
            depth=depth,
            speed=speed,
            is_log=True,
            min_wrap_x=min_wrap_x,
            max_wrap_x=max_wrap_x,
            scene=scene,
        )

        if scene is not None:
            # 1. Main log trunk
            self.entity = scene.create_box(
                size=(width, height, depth),
                position=(self.x, self.y, self.z),
                color=COLOR_LOG_WOOD,
                cast_shadows=True,
                name="RiverLog",
            )
            # 2. Voxel end rings (lighter wood rings)
            ring_w = 0.18
            ring_l = scene.create_box(
                size=(ring_w, height * 0.85, depth * 0.85),
                position=(self.x - width * 0.5 + ring_w * 0.5, self.y, self.z),
                color=COLOR_LOG_END_RING,
                cast_shadows=False,
                name="LogRingL",
            )
            ring_r = scene.create_box(
                size=(ring_w, height * 0.85, depth * 0.85),
                position=(self.x + width * 0.5 - ring_w * 0.5, self.y, self.z),
                color=COLOR_LOG_END_RING,
                cast_shadows=False,
                name="LogRingR",
            )
            self.sub_entities.append((ring_l, (-width * 0.5 + ring_w * 0.5, 0.0, 0.0)))
            self.sub_entities.append((ring_r, (width * 0.5 - ring_w * 0.5, 0.0, 0.0)))


class TrainObstacle(BaseObstacle):
    """High-speed aerodynamic bullet train that zooms past on RailRow."""

    def __init__(
        self,
        x: float,
        z: float,
        speed: float = 45.0,
        width: float = 24.0,
        scene: Optional[Any] = None,
    ) -> None:
        height = 1.25
        depth = 0.85
        y = 0.65
        super().__init__(
            x=x,
            y=y,
            z=z,
            width=width,
            height=height,
            depth=depth,
            speed=speed,
            is_log=False,
            min_wrap_x=-100.0,
            max_wrap_x=100.0,
            scene=scene,
        )

        if scene is not None:
            # 1. Main train locomotive body
            self.entity = scene.create_box(
                size=(width, height, depth),
                position=(self.x, self.y, self.z),
                color=COLOR_TRAIN_BODY,
                cast_shadows=True,
                name="BulletTrainBody",
            )
            # 2. Window strip
            win = scene.create_box(
                size=(width * 0.94, height * 0.28, depth * 1.04),
                position=(self.x, self.y + 0.18, self.z),
                color=COLOR_TRAIN_WINDOWS,
                cast_shadows=False,
                name="BulletTrainWindows",
            )
            self.sub_entities.append((win, (0.0, 0.18, 0.0)))


# =============================================================================
# Procedural Voxel Tree
# =============================================================================
class VoxelTree:
    """Procedural 2-tier voxel tree (brown trunk + vibrant foliage box)."""

    def __init__(
        self,
        x: float,
        z: float,
        foliage_color: Optional[Color] = None,
        scene: Optional[Any] = None,
    ) -> None:
        self.x: float = float(x)
        self.z: float = float(z)
        self.entities: List[Any] = []

        if scene is not None:
            trunk = scene.create_box(
                size=(0.4, 0.7, 0.4),
                position=(self.x, 0.35, self.z),
                color=COLOR_TREE_TRUNK,
                cast_shadows=True,
                has_collision=True,
                name="TreeTrunk",
            )
            fol_col = foliage_color if foliage_color is not None else random.choice(COLOR_TREE_FOLIAGE)
            foliage = scene.create_box(
                size=(0.92, 1.15, 0.92),
                position=(self.x, 1.25, self.z),
                color=fol_col,
                cast_shadows=True,
                has_collision=True,
                name="TreeFoliage",
            )
            self.entities.extend([trunk, foliage])

    def cleanup(self, scene: Any) -> None:
        if scene is not None:
            for ent in self.entities:
                try:
                    scene.remove_entity(ent)
                except Exception:
                    pass
        self.entities.clear()


# =============================================================================
# World Row Implementations
# =============================================================================
class BaseRow:
    """Base class for all procedural terrain rows."""

    def __init__(self, z_index: int, row_type: RowType, scene: Optional[Any] = None) -> None:
        self.z_index: int = int(z_index)
        self.row_type: RowType = row_type
        self.entities: List[Any] = []
        self.obstacles: List[ObstacleContract] = []
        self.scene: Optional[Any] = scene

    def update(self, dt: float) -> None:
        """Update all active obstacles in this row."""
        for obs in self.obstacles:
            obs.update(dt)

    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        """Returns (is_hazardous, hazard_reason, carrier_log_velocity_x)."""
        return False, None, None

    def is_blocked(self, px: float, pz: float) -> bool:
        """Check if grid position is obstructed by solid static geometry (e.g. tree)."""
        return False

    def cleanup(self, scene: Any) -> None:
        """Cleanly remove all entities and obstacles from the scene."""
        target_scene = scene if scene is not None else self.scene
        if target_scene is not None:
            for ent in self.entities:
                try:
                    target_scene.remove_entity(ent)
                except Exception:
                    pass
        self.entities.clear()

        for obs in self.obstacles:
            obs.cleanup(target_scene)
        self.obstacles.clear()


class StartRow(BaseRow):
    """Safe starting zone row with wide green ground and boundary trees."""

    def __init__(self, z_index: int, scene: Optional[Any] = None) -> None:
        super().__init__(z_index, RowType.START, scene)
        self.blocked_lanes: Set[int] = set()

        if scene is not None:
            ground = scene.create_box(
                size=(44.0, 0.45, 1.0),
                position=(0.0, -0.225, float(self.z_index)),
                color=COLOR_START_ZONE,
                has_collision=False,
                name="StartGround",
            )
            self.entities.append(ground)

        # Place outer perimeter trees outside playable width [-10, 10]
        for bx in [-13, -12, -11, 11, 12, 13]:
            self.blocked_lanes.add(bx)
            tree = VoxelTree(bx, float(self.z_index), scene=scene)
            self.entities.extend(tree.entities)

    def is_blocked(self, px: float, pz: float) -> bool:
        if abs(pz - self.z_index) <= 0.6:
            return int(round(px)) in self.blocked_lanes
        return False


class GrassRow(BaseRow):
    """Vibrant meadow row with procedural trees blocking player movement."""

    def __init__(
        self,
        z_index: int,
        tree_density: float = 0.22,
        rng: Optional[random.Random] = None,
        scene: Optional[Any] = None,
    ) -> None:
        super().__init__(z_index, RowType.GRASS, scene)
        r = rng if rng is not None else random.Random()
        self.blocked_lanes: Set[int] = set()

        # Alternate strip color slightly for satisfying voxel checkerboard pattern
        ground_col = COLOR_GRASS_EVEN if (abs(z_index) % 2 == 0) else COLOR_GRASS_ODD
        if scene is not None:
            ground = scene.create_box(
                size=(44.0, 0.45, 1.0),
                position=(0.0, -0.225, float(self.z_index)),
                color=ground_col,
                has_collision=False,
                name=f"GrassGround_{z_index}",
            )
            self.entities.append(ground)

        # Boundary trees outside playable grid
        for bx in [-13, -12, -11, 11, 12, 13]:
            self.blocked_lanes.add(bx)
            tree = VoxelTree(bx, float(self.z_index), scene=scene)
            self.entities.extend(tree.entities)

        # In-bounds trees: pick 2 to 4 lanes to block, ensuring at least 3 contiguous paths exist
        candidates = list(range(CELL_MIN_X, CELL_MAX_X + 1))
        r.shuffle(candidates)
        target_tree_count = min(r.randint(2, 5), len(candidates) - 4)

        placed_count = 0
        for cand_x in candidates:
            if placed_count >= target_tree_count:
                break
            # Don't completely box off lane 0 at spawn
            if abs(z_index) <= 1 and abs(cand_x) <= 1:
                continue

            self.blocked_lanes.add(cand_x)
            fol_col = r.choice(COLOR_TREE_FOLIAGE)
            tree = VoxelTree(cand_x, float(self.z_index), foliage_color=fol_col, scene=scene)
            self.entities.extend(tree.entities)
            placed_count += 1

    def is_blocked(self, px: float, pz: float) -> bool:
        if abs(pz - self.z_index) <= 0.6:
            return int(round(px)) in self.blocked_lanes
        return False

    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        return False, None, None


class RoadRow(BaseRow):
    """Dark asphalt road with lane markers and moving cars/trucks."""

    def __init__(
        self,
        z_index: int,
        speed: Optional[float] = None,
        vehicle_count: Optional[int] = None,
        rng: Optional[random.Random] = None,
        scene: Optional[Any] = None,
    ) -> None:
        super().__init__(z_index, RowType.ROAD, scene)
        r = rng if rng is not None else random.Random()

        # Direction and speed
        direction = 1.0 if (abs(z_index) % 2 == 0) else -1.0
        base_spd = speed if speed is not None else r.uniform(5.0, 9.5)
        signed_speed = abs(base_spd) * direction

        # 1. Dark asphalt strip
        if scene is not None:
            asphalt = scene.create_box(
                size=(44.0, 0.40, 1.0),
                position=(0.0, -0.20, float(self.z_index)),
                color=COLOR_ROAD_ASPHALT,
                has_collision=False,
                name=f"RoadAsphalt_{z_index}",
            )
            self.entities.append(asphalt)

            # Dashed lane markers
            for mx in range(-16, 17, 4):
                marker = scene.create_box(
                    size=(1.4, 0.03, 0.12),
                    position=(float(mx), 0.015, float(self.z_index)),
                    color=COLOR_ROAD_MARKER,
                    has_collision=False,
                    name=f"LaneMarker_{z_index}_{mx}",
                )
                self.entities.append(marker)

        # 2. Vehicles (1-2 cars or trucks)
        count = vehicle_count if vehicle_count is not None else r.choice([1, 2])
        wrap_min = -18.0
        wrap_max = 18.0

        if count == 1:
            spawn_x_positions = [r.uniform(-10.0, 10.0)]
        else:
            first_x = r.uniform(-14.0, -4.0)
            second_x = first_x + r.uniform(14.0, 18.0)
            if second_x > wrap_max:
                second_x -= (wrap_max - wrap_min)
            spawn_x_positions = [first_x, second_x]

        for vx in spawn_x_positions:
            is_truck = r.random() < 0.35
            v_color = r.choice(COLOR_CAR_PALETTE)
            if is_truck:
                truck = TruckObstacle(
                    x=vx,
                    z=float(self.z_index),
                    speed=signed_speed,
                    color=v_color,
                    min_wrap_x=wrap_min,
                    max_wrap_x=wrap_max,
                    scene=scene,
                )
                self.obstacles.append(truck)
            else:
                car = CarObstacle(
                    x=vx,
                    z=float(self.z_index),
                    speed=signed_speed,
                    color=v_color,
                    min_wrap_x=wrap_min,
                    max_wrap_x=wrap_max,
                    scene=scene,
                )
                self.obstacles.append(car)

    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        if abs(pz - self.z_index) <= 0.6:
            for obs in self.obstacles:
                if obs.check_hit(px, pz, radius=0.35):
                    return True, "squashed", None
        return False, None, None


class RiverRow(BaseRow):
    """Vibrant water stream with floating wooden logs carrying the player."""

    def __init__(
        self,
        z_index: int,
        speed: Optional[float] = None,
        log_count: Optional[int] = None,
        rng: Optional[random.Random] = None,
        scene: Optional[Any] = None,
    ) -> None:
        super().__init__(z_index, RowType.RIVER, scene)
        r = rng if rng is not None else random.Random()

        # Water speed direction alternates per river row
        direction = 1.0 if (abs(z_index) % 2 == 1) else -1.0
        base_spd = speed if speed is not None else r.uniform(2.5, 5.0)
        signed_speed = abs(base_spd) * direction

        # 1. Vibrant water box (slightly lowered)
        if scene is not None:
            water = scene.create_box(
                size=(44.0, 0.35, 1.0),
                position=(0.0, -0.22, float(self.z_index)),
                color=COLOR_RIVER_WATER,
                has_collision=False,
                name=f"RiverWater_{z_index}",
            )
            self.entities.append(water)

        # 2. Wooden logs (2-3 logs spaced out)
        count = log_count if log_count is not None else r.choice([2, 3])
        wrap_min = -19.0
        wrap_max = 19.0
        span = wrap_max - wrap_min

        spacing = span / float(count)
        start_offset = r.uniform(0.0, spacing)

        for i in range(count):
            lx = wrap_min + start_offset + (i * spacing)
            if lx > wrap_max:
                lx -= span
            log_w = r.uniform(2.8, 3.8)
            log = LogObstacle(
                x=lx,
                z=float(self.z_index),
                speed=signed_speed,
                width=log_w,
                min_wrap_x=wrap_min,
                max_wrap_x=wrap_max,
                scene=scene,
            )
            self.obstacles.append(log)

    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        if abs(pz - self.z_index) <= 0.6:
            # Check if player is safely riding any log
            for obs in self.obstacles:
                if obs.check_hit(px, pz, radius=0.35):
                    return False, None, obs.speed
            # Not on any log -> player drowns in the river!
            return True, "drowned", None
        return False, None, None


class RailRow(BaseRow):
    """Gravel railway with rails, warning light beacon, and bullet train."""

    def __init__(
        self,
        z_index: int,
        cycle_interval: float = 6.0,
        train_speed: float = 45.0,
        rng: Optional[random.Random] = None,
        scene: Optional[Any] = None,
    ) -> None:
        super().__init__(z_index, RowType.RAIL, scene)
        r = rng if rng is not None else random.Random()

        self.cycle_interval: float = float(cycle_interval)
        self.warning_duration: float = 1.35
        self.train_speed: float = float(train_speed)
        self.train_direction: float = 1.0 if (abs(z_index) % 2 == 0) else -1.0

        self.train_timer: float = r.uniform(0.0, max(0.1, self.cycle_interval - self.warning_duration - 0.5))
        self.is_warning: bool = False
        self.is_train_passing: bool = False
        self.blink_timer: float = 0.0
        self.beacon_lit: bool = False

        self.beacon_light_entity: Optional[Any] = None

        if scene is not None:
            # 1. Gravel strip
            gravel = scene.create_box(
                size=(44.0, 0.40, 1.0),
                position=(0.0, -0.20, float(self.z_index)),
                color=COLOR_RAIL_GRAVEL,
                has_collision=False,
                name=f"RailGravel_{z_index}",
            )
            self.entities.append(gravel)

            # 2. Wooden sleepers (ties)
            for tx in range(-18, 19, 2):
                tie = scene.create_box(
                    size=(0.4, 0.04, 0.85),
                    position=(float(tx), 0.02, float(self.z_index)),
                    color=COLOR_RAIL_TIE,
                    has_collision=False,
                    name=f"RailTie_{z_index}_{tx}",
                )
                self.entities.append(tie)

            # 3. Metallic rails (2 parallel steel tracks)
            r1 = scene.create_box(
                size=(44.0, 0.06, 0.08),
                position=(0.0, 0.05, float(self.z_index) - 0.22),
                color=COLOR_RAIL_STEEL,
                has_collision=False,
                name=f"RailSteel1_{z_index}",
            )
            r2 = scene.create_box(
                size=(44.0, 0.06, 0.08),
                position=(0.0, 0.05, float(self.z_index) + 0.22),
                color=COLOR_RAIL_STEEL,
                has_collision=False,
                name=f"RailSteel2_{z_index}",
            )
            self.entities.extend([r1, r2])

            # 4. Warning beacon post and light
            post = scene.create_box(
                size=(0.15, 1.2, 0.15),
                position=(11.5, 0.60, float(self.z_index)),
                color=COLOR_BEACON_POST,
                has_collision=False,
                name=f"BeaconPost_{z_index}",
            )
            self.beacon_light_entity = scene.create_box(
                size=(0.30, 0.30, 0.30),
                position=(11.5, 1.35, float(self.z_index)),
                color=COLOR_BEACON_IDLE,
                has_collision=False,
                name=f"BeaconLight_{z_index}",
            )
            self.entities.extend([post, self.beacon_light_entity])

        # 5. Bullet train obstacle (starts off-screen)
        initial_train_x = -999.0
        self.train = TrainObstacle(
            x=initial_train_x,
            z=float(self.z_index),
            speed=0.0,
            scene=scene,
        )
        self.obstacles.append(self.train)

    def trigger_train(self, immediate: bool = False) -> None:
        """Trigger warning or instant bullet train pass."""
        if immediate:
            self._start_train_pass()
        else:
            self.train_timer = self.cycle_interval - self.warning_duration
            self.is_warning = True

    def _start_train_pass(self) -> None:
        self.is_warning = False
        self.is_train_passing = True
        self.beacon_lit = True
        if self.beacon_light_entity is not None:
            self.beacon_light_entity.color = COLOR_BEACON_ACTIVE

        # Position train at approach edge
        if self.train_direction > 0.0:
            self.train.x = -32.0
            self.train.speed = self.train_speed
        else:
            self.train.x = 32.0
            self.train.speed = -self.train_speed

        if self.train.entity is not None:
            self.train.entity.transform.set_position(self.train.x, self.train.y, self.train.z)

    def update(self, dt: float) -> None:
        if dt <= 0.0:
            return

        self.train_timer += dt

        # Warning phase (before train enters)
        time_to_train = self.cycle_interval - self.train_timer
        if 0.0 < time_to_train <= self.warning_duration and not self.is_train_passing:
            self.is_warning = True
            self.blink_timer += dt
            # 4 Hz blink rate
            self.beacon_lit = int(self.blink_timer * 8.0) % 2 == 0
            if self.beacon_light_entity is not None:
                self.beacon_light_entity.color = COLOR_BEACON_ACTIVE if self.beacon_lit else COLOR_BEACON_IDLE

        # Train arrival trigger
        if self.train_timer >= self.cycle_interval and not self.is_train_passing:
            self._start_train_pass()

        # Update train during passing phase
        if self.is_train_passing:
            self.train.update(dt)

            # Check if train has fully exited the visible area
            has_exited = (
                (self.train_direction > 0.0 and self.train.x > 32.0 + self.train.width * 0.5)
                or (self.train_direction < 0.0 and self.train.x < -32.0 - self.train.width * 0.5)
            )

            if has_exited:
                self.is_train_passing = False
                self.is_warning = False
                self.train_timer = 0.0
                self.train.speed = 0.0
                self.train.x = -999.0
                if self.train.entity is not None:
                    self.train.entity.transform.set_position(self.train.x, self.train.y, self.train.z)
                if self.beacon_light_entity is not None:
                    self.beacon_light_entity.color = COLOR_BEACON_IDLE

    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        if abs(pz - self.z_index) <= 0.6:
            if self.is_train_passing and self.train.check_hit(px, pz, radius=0.35):
                return True, "squashed", None
        return False, None, None


# =============================================================================
# High-Performance Streaming World Generator
# =============================================================================
class WorldGenerator:
    """Manages procedural infinite world generation and row pruning."""

    def __init__(
        self,
        scene: Optional[Any] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.scene: Optional[Any] = scene
        self.seed: Optional[int] = seed
        self.rng: random.Random = random.Random(seed)

        self.active_rows: Dict[int, WorldRowContract] = {}
        self.max_generated_z: int = -1
        self.min_active_z: int = 0

        # Clumping state machine for procedural generation
        self._current_clump_type: RowType = RowType.GRASS
        self._clump_remaining: int = 0
        self._last_major_type: RowType = RowType.GRASS

        self.reset()

    def reset(self) -> None:
        """Clear all active rows, remove scene entities, and reseed world at Z=0."""
        # Clean up existing rows
        for row in list(self.active_rows.values()):
            row.cleanup(self.scene)
        self.active_rows.clear()

        if self.seed is not None:
            self.rng = random.Random(self.seed)

        self.max_generated_z = -1
        self.min_active_z = -5
        self._current_clump_type = RowType.GRASS
        self._clump_remaining = 0
        self._last_major_type = RowType.GRASS

        # 1. Safe start rows behind and around spawn [-5 .. 0]
        for z in range(-5, 1):
            start_row = StartRow(z, scene=self.scene)
            self.active_rows[z] = start_row
            self.max_generated_z = z

        # 2. Initial forward lookahead terrain (Z = 1 .. 25)
        self.generate_ahead(player_z=0, lookahead=25)

    def _choose_next_clump(self) -> Tuple[RowType, int]:
        """Procedurally choose next terrain clump with authentic pacing."""
        # Pacing weights: ensure fair variety and no impossible river chains
        if self._last_major_type == RowType.RIVER:
            # Always follow water with a meadow to give the duck a safe landing
            next_type = RowType.GRASS
            length = self.rng.randint(1, 3)
        elif self._last_major_type == RowType.RAIL:
            next_type = self.rng.choice([RowType.GRASS, RowType.ROAD])
            length = self.rng.randint(1, 3)
        else:
            weights = [
                (RowType.GRASS, 0.30),
                (RowType.ROAD, 0.35),
                (RowType.RIVER, 0.22),
                (RowType.RAIL, 0.13),
            ]
            types, probs = zip(*weights)
            next_type = self.rng.choices(types, weights=probs, k=1)[0]
            if next_type == RowType.ROAD:
                length = self.rng.randint(1, 4)
            elif next_type == RowType.RIVER:
                length = self.rng.randint(1, 3)
            elif next_type == RowType.RAIL:
                length = self.rng.randint(1, 2)
            else:
                length = self.rng.randint(1, 3)

        self._last_major_type = next_type
        return next_type, length

    def _create_row_by_type(self, z: int, row_type: RowType) -> BaseRow:
        """Instantiate row of specified type."""
        if row_type == RowType.GRASS:
            return GrassRow(z, rng=self.rng, scene=self.scene)
        elif row_type == RowType.ROAD:
            return RoadRow(z, rng=self.rng, scene=self.scene)
        elif row_type == RowType.RIVER:
            return RiverRow(z, rng=self.rng, scene=self.scene)
        elif row_type == RowType.RAIL:
            return RailRow(z, rng=self.rng, scene=self.scene)
        else:
            return StartRow(z, scene=self.scene)

    def generate_ahead(self, player_z: int, lookahead: int = 25) -> None:
        """Stream new rows forward up to player_z + lookahead."""
        target_z = int(player_z + lookahead)
        while self.max_generated_z < target_z:
            next_z = self.max_generated_z + 1

            if self._clump_remaining <= 0:
                self._current_clump_type, self._clump_remaining = self._choose_next_clump()

            row = self._create_row_by_type(next_z, self._current_clump_type)
            self.active_rows[next_z] = row
            self.max_generated_z = next_z
            self._clump_remaining -= 1

    def prune_behind(self, player_z: int, keep_behind: int = 8) -> None:
        """Remove and cleanup rows behind player_z - keep_behind to maintain 500+ FPS."""
        min_retained_z = int(player_z - keep_behind)
        stale_z = [z for z in self.active_rows.keys() if z < min_retained_z]

        for z in stale_z:
            row = self.active_rows.pop(z)
            row.cleanup(self.scene)

        if self.active_rows:
            self.min_active_z = min(self.active_rows.keys())
        else:
            self.min_active_z = min_retained_z

    def get_row(self, z: int) -> Optional[WorldRowContract]:
        """Fetch active row at Z index."""
        return self.active_rows.get(int(z))

    def check_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        """Query hazard state at player coordinate (px, pz)."""
        row_z = int(round(pz))
        row = self.active_rows.get(row_z)
        if row is not None:
            return row.check_player_hazard(px, pz)
        return False, None, None

    def is_cell_blocked(self, grid_x: int, grid_z: int) -> bool:
        """Check if grid cell is blocked by boundary walls or static obstacles."""
        if grid_x < CELL_MIN_X or grid_x > CELL_MAX_X:
            return True
        row = self.active_rows.get(int(grid_z))
        if row is not None and hasattr(row, "is_blocked"):
            return row.is_blocked(float(grid_x), float(grid_z))
        return False

    def update(self, dt: float) -> None:
        """Update simulation for all active rows."""
        for row in list(self.active_rows.values()):
            row.update(dt)
