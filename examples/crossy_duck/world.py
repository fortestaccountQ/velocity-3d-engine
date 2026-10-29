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


try:
    from examples.crossy_duck.textures import MaterialRegistry
except ImportError:
    try:
        from crossy_duck.textures import MaterialRegistry
    except ImportError:
        MaterialRegistry = None


_DEFAULT_REGISTRY: Optional[Any] = None


def get_default_material_registry() -> Optional[Any]:
    """Provide a singleton fallback MaterialRegistry for standalone row/obstacle usage."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None and MaterialRegistry is not None:
        try:
            _DEFAULT_REGISTRY = MaterialRegistry()
        except Exception:
            _DEFAULT_REGISTRY = None
    return _DEFAULT_REGISTRY


def _get_mat(registry: Any, name: str, uv_scale: Optional[Tuple[float, float]] = None) -> Any:
    """Safely fetch material from registry with optional uv_scale override."""
    if registry is None:
        return None
    try:
        if uv_scale is not None:
            try:
                return registry.get_material(name, uv_scale=uv_scale)
            except TypeError:
                mat = registry.get_material(name)
                if hasattr(mat, "uv_scale"):
                    mat.uv_scale = uv_scale
                elif hasattr(mat, "set_uv_scale"):
                    mat.set_uv_scale(*uv_scale)
                return mat
        return registry.get_material(name)
    except Exception:
        return None


# =============================================================================
# Color Palette for Voxel Aesthetics
# =============================================================================
COLOR_GRASS_EVEN = Color.from_hex("#55a840")
COLOR_GRASS_ODD = Color.from_hex("#4c9938")
COLOR_START_ZONE = Color.from_hex("#5cb85c")

COLOR_ROAD_ASPHALT = Color.from_hex("#21252b")
COLOR_ROAD_MARKER = Color.from_hex("#f5d76e")
COLOR_ROAD_EDGE_WHITE = Color.from_hex("#ffffff")
COLOR_ROAD_DASH_WHITE = Color.from_hex("#f8fafc")
COLOR_ROAD_DIVIDER_CENTER = Color.from_hex("#facc15")

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
    Color.from_hex("#2e7d32"),  # Rich Emerald
    Color.from_hex("#388e3c"),  # Vibrant Forest
    Color.from_hex("#1b5e20"),  # Deep Evergreen
    Color.from_hex("#43a047"),  # Fresh Clover
    Color.from_hex("#558b2f"),  # Olive Moss
    Color.from_hex("#66bb6a"),  # Bright Mint
]

COLOR_CAR_PALETTE = [
    Color.from_hex("#dc2626"),  # Classic Crimson Red
    Color.from_hex("#2563eb"),  # Royal Blue
    Color.from_hex("#eab308"),  # Taxi Yellow
    Color.from_hex("#ea580c"),  # Tangerine Orange
    Color.from_hex("#16a34a"),  # Emerald Green
    Color.from_hex("#0284c7"),  # Sky Blue
    Color.from_hex("#f8fafc"),  # Arctic White
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
        min_wrap_x: float = -48.0,
        max_wrap_x: float = 48.0,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
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
        self.material_registry: Optional[Any] = (
            material_registry if material_registry is not None
            else (get_default_material_registry() if scene is not None else None)
        )
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

    def set_position(self, x: float, y: float, z: float) -> None:
        """Explicitly set obstacle position and synchronize all sub-entity transforms."""
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
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
        min_wrap_x: float = -48.0,
        max_wrap_x: float = 48.0,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
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
            material_registry=material_registry,
        )

        car_col = color if color is not None else random.choice(COLOR_CAR_PALETTE)

        if scene is not None:
            veh_mat = _get_mat(self.material_registry, "vehicle")
            grille_mat = _get_mat(self.material_registry, "car_grille")
            facing_dir = 1.0 if speed >= 0 else -1.0

            # 1. Main chassis / body: vibrant glossy car paint
            self.entity = scene.create_box(
                size=(width, 0.44, depth),
                position=(self.x, self.y, self.z),
                color=car_col,
                material=veh_mat,
                cast_shadows=True,
                name="CarChassis",
            )

            # 2. Cabin top (tinted windshield and windows)
            cabin_ox = -facing_dir * 0.08
            cabin_mat = _get_mat(self.material_registry, "car_cabin")
            cabin = scene.create_box(
                size=(width * 0.54, 0.35, depth * 0.82),
                position=(self.x + cabin_ox, self.y + 0.36, self.z),
                color=COLOR_CABIN_WINDOW if cabin_mat is None else WHITE,
                material=cabin_mat,
                cast_shadows=True,
                name="CarCabin",
            )
            self.sub_entities.append((cabin, (cabin_ox, 0.36, 0.0)))

            # 2b. Painted Roof Cap (Crossy Road voxel roof)
            roof = scene.create_box(
                size=(width * 0.50, 0.06, depth * 0.80),
                position=(self.x + cabin_ox, self.y + 0.36 + 0.175 + 0.03, self.z),
                color=car_col,
                material=veh_mat,
                cast_shadows=False,
                name="CarRoof",
            )
            self.sub_entities.append((roof, (cabin_ox, 0.36 + 0.175 + 0.03, 0.0)))

            # 3. Dedicated Front Grille Decal Plate (facing direction of travel)
            grille_ox = facing_dir * (width * 0.50 + 0.01)
            grille = scene.create_box(
                size=(0.04, 0.34, depth * 0.86),
                position=(self.x + grille_ox, self.y, self.z),
                color=WHITE if grille_mat is not None else Color.from_hex("#334155"),
                material=grille_mat,
                cast_shadows=False,
                name="CarGrilleDecal",
            )
            self.sub_entities.append((grille, (grille_ox, 0.0, 0.0)))

            # 4. Front Headlights (in direction of movement)
            hl_x = facing_dir * (width * 0.50 + 0.02)
            hl1 = scene.create_box(
                size=(0.06, 0.12, 0.18),
                position=(self.x + hl_x, self.y + 0.04, self.z - 0.24),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="Headlight1",
            )
            hl2 = scene.create_box(
                size=(0.06, 0.12, 0.18),
                position=(self.x + hl_x, self.y + 0.04, self.z + 0.24),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="Headlight2",
            )
            self.sub_entities.append((hl1, (hl_x, 0.04, -0.24)))
            self.sub_entities.append((hl2, (hl_x, 0.04, 0.24)))

            # 5. Rear Taillights (red brake markers)
            rear_x = -facing_dir * (width * 0.50 + 0.02)
            tl_col = Color.from_hex("#dc2626")
            tl1 = scene.create_box(
                size=(0.05, 0.10, 0.16),
                position=(self.x + rear_x, self.y + 0.04, self.z - 0.24),
                color=tl_col,
                cast_shadows=False,
                name="Taillight1",
            )
            tl2 = scene.create_box(
                size=(0.05, 0.10, 0.16),
                position=(self.x + rear_x, self.y + 0.04, self.z + 0.24),
                color=tl_col,
                cast_shadows=False,
                name="Taillight2",
            )
            self.sub_entities.append((tl1, (rear_x, 0.04, -0.24)))
            self.sub_entities.append((tl2, (rear_x, 0.04, 0.24)))

            # 6. Wheels (4 dark corner wheels)
            wheel_mat = _get_mat(self.material_registry, "car_wheel")
            wheel_col = Color.from_hex("#0f172a") if wheel_mat is None else WHITE
            for wx_dir in (0.32, -0.32):
                for wz_dir in (0.42, -0.42):
                    wheel = scene.create_box(
                        size=(0.36, 0.20, 0.08),
                        position=(self.x + wx_dir * width, self.y - 0.14, self.z + wz_dir * depth),
                        color=wheel_col,
                        material=wheel_mat,
                        cast_shadows=False,
                        name="CarWheel",
                    )
                    self.sub_entities.append((wheel, (wx_dir * width, -0.14, wz_dir * depth)))

            # 7. Front & Rear Chrome Bumpers
            f_bumper_x = facing_dir * (width * 0.50 + 0.03)
            f_bumper = scene.create_box(
                size=(0.06, 0.14, depth * 0.90),
                position=(self.x + f_bumper_x, self.y - 0.12, self.z),
                color=Color.from_hex("#cbd5e1"),
                cast_shadows=False,
                name="CarFrontBumper",
            )
            r_bumper_x = -facing_dir * (width * 0.50 + 0.03)
            r_bumper = scene.create_box(
                size=(0.06, 0.14, depth * 0.90),
                position=(self.x + r_bumper_x, self.y - 0.12, self.z),
                color=Color.from_hex("#cbd5e1"),
                cast_shadows=False,
                name="CarRearBumper",
            )
            self.sub_entities.append((f_bumper, (f_bumper_x, -0.12, 0.0)))
            self.sub_entities.append((r_bumper, (r_bumper_x, -0.12, 0.0)))


class TruckObstacle(BaseObstacle):
    """Voxel delivery truck with cab, large cargo container, and headlights."""

    def __init__(
        self,
        x: float,
        z: float,
        speed: float,
        color: Optional[Color] = None,
        min_wrap_x: float = -48.0,
        max_wrap_x: float = 48.0,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
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
            material_registry=material_registry,
        )

        cab_col = color if color is not None else random.choice(COLOR_CAR_PALETTE)

        if scene is not None:
            veh_mat = _get_mat(self.material_registry, "vehicle")
            grille_mat = _get_mat(self.material_registry, "car_grille")
            facing_dir = 1.0 if speed >= 0 else -1.0
            cargo_w = width * 0.65
            cab_w = width * 0.35

            cargo_ox = -facing_dir * (cab_w * 0.5)
            cab_ox = facing_dir * (cargo_w * 0.5)

            # 1. Main cargo container (clean freight white with crisp shadow)
            cargo_mat = _get_mat(self.material_registry, "truck_cargo")
            self.entity = scene.create_box(
                size=(cargo_w, height, depth),
                position=(self.x + cargo_ox, self.y, self.z),
                color=COLOR_TRUCK_CARGO if cargo_mat is None else WHITE,
                material=cargo_mat,
                cast_shadows=True,
                name="TruckCargo",
            )

            # 2. Cab with glossy paint and tinted cabin windshield
            cab = scene.create_box(
                size=(cab_w, height * 0.75, depth * 0.88),
                position=(self.x + cab_ox, self.y - 0.12, self.z),
                color=cab_col,
                material=veh_mat,
                cast_shadows=True,
                name="TruckCab",
            )
            self.sub_entities.append((cab, (cab_ox, -0.12, 0.0)))

            cabin_mat = _get_mat(self.material_registry, "car_cabin")
            cabin = scene.create_box(
                size=(cab_w * 0.70, height * 0.38, depth * 0.90),
                position=(self.x + cab_ox, self.y + 0.14, self.z),
                color=COLOR_CABIN_WINDOW if cabin_mat is None else WHITE,
                material=cabin_mat,
                cast_shadows=False,
                name="TruckCabin",
            )
            self.sub_entities.append((cabin, (cab_ox, 0.14, 0.0)))

            # 3. Dedicated Front Grille Decal Plate on Cab Face
            grille_ox = cab_ox + facing_dir * (cab_w * 0.50 + 0.01)
            grille = scene.create_box(
                size=(0.04, height * 0.60, depth * 0.82),
                position=(self.x + grille_ox, self.y - 0.15, self.z),
                color=WHITE if grille_mat is not None else Color.from_hex("#334155"),
                material=grille_mat,
                cast_shadows=False,
                name="TruckGrilleDecal",
            )
            self.sub_entities.append((grille, (grille_ox, -0.15, 0.0)))

            # 4. Headlights
            hl_x = cab_ox + facing_dir * (cab_w * 0.50 + 0.02)
            hl1 = scene.create_box(
                size=(0.06, 0.14, 0.18),
                position=(self.x + hl_x, self.y - 0.18, self.z - 0.25),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="TruckHeadlight1",
            )
            hl2 = scene.create_box(
                size=(0.06, 0.14, 0.18),
                position=(self.x + hl_x, self.y - 0.18, self.z + 0.25),
                color=COLOR_HEADLIGHT,
                cast_shadows=False,
                name="TruckHeadlight2",
            )
            self.sub_entities.append((hl1, (hl_x, -0.18, -0.25)))
            self.sub_entities.append((hl2, (hl_x, -0.18, 0.25)))

            # 5. Rear Taillights
            rear_x = cargo_ox - facing_dir * (cargo_w * 0.50 + 0.02)
            tl_col = Color.from_hex("#dc2626")
            tl1 = scene.create_box(
                size=(0.05, 0.12, 0.16),
                position=(self.x + rear_x, self.y - 0.25, self.z - 0.28),
                color=tl_col,
                cast_shadows=False,
                name="TruckTaillight1",
            )
            tl2 = scene.create_box(
                size=(0.05, 0.12, 0.16),
                position=(self.x + rear_x, self.y - 0.25, self.z + 0.28),
                color=tl_col,
                cast_shadows=False,
                name="TruckTaillight2",
            )
            self.sub_entities.append((tl1, (rear_x, -0.25, -0.28)))
            self.sub_entities.append((tl2, (rear_x, -0.25, 0.28)))

            # 6. Wheels (6 heavy wheels for cargo truck)
            wheel_mat = _get_mat(self.material_registry, "car_wheel")
            wheel_col = Color.from_hex("#0f172a") if wheel_mat is None else WHITE
            wheel_x_positions = [
                cab_ox + facing_dir * (cab_w * 0.20),
                cargo_ox - facing_dir * (cargo_w * 0.15),
                cargo_ox - facing_dir * (cargo_w * 0.38),
            ]
            for wx in wheel_x_positions:
                for wz_dir in (0.42, -0.42):
                    wheel = scene.create_box(
                        size=(0.42, 0.24, 0.08),
                        position=(self.x + wx, self.y - 0.42, self.z + wz_dir * depth),
                        color=wheel_col,
                        material=wheel_mat,
                        cast_shadows=False,
                        name="TruckWheel",
                    )
                    self.sub_entities.append((wheel, (wx, -0.42, wz_dir * depth)))

            # 7. Heavy Front Bumper
            f_bumper_x = cab_ox + facing_dir * (cab_w * 0.50 + 0.03)
            f_bumper = scene.create_box(
                size=(0.06, 0.18, depth * 0.92),
                position=(self.x + f_bumper_x, self.y - 0.32, self.z),
                color=Color.from_hex("#94a3b8"),
                cast_shadows=False,
                name="TruckFrontBumper",
            )
            self.sub_entities.append((f_bumper, (f_bumper_x, -0.32, 0.0)))


class LogObstacle(BaseObstacle):
    """Floating wooden river log that acts as a safe player carrier."""

    def __init__(
        self,
        x: float,
        z: float,
        speed: float,
        width: float = 3.2,
        min_wrap_x: float = -38.0,
        max_wrap_x: float = 38.0,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
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
            material_registry=material_registry,
        )

        if scene is not None:
            bark_mat = _get_mat(self.material_registry, "wood_bark", uv_scale=(self.width, 1.0))
            rings_mat = _get_mat(self.material_registry, "wood_rings")

            # Eliminate coplanar Z-fighting: trunk ends where ring caps begin
            ring_w = 0.16
            trunk_w = max(0.4, width - ring_w * 2.0)

            # 1. Main log trunk
            self.entity = scene.create_box(
                size=(trunk_w, height, depth),
                position=(self.x, self.y, self.z),
                color=COLOR_LOG_WOOD if bark_mat is None else WHITE,
                material=bark_mat,
                cast_shadows=True,
                name="RiverLog",
            )
            # 2. Voxel end rings (non-overlapping caps on outer ends)
            ring_l = scene.create_box(
                size=(ring_w, height * 0.90, depth * 0.90),
                position=(self.x - trunk_w * 0.5 - ring_w * 0.5, self.y, self.z),
                color=COLOR_LOG_END_RING if rings_mat is None else WHITE,
                material=rings_mat,
                cast_shadows=False,
                name="LogRingL",
            )
            ring_r = scene.create_box(
                size=(ring_w, height * 0.90, depth * 0.90),
                position=(self.x + trunk_w * 0.5 + ring_w * 0.5, self.y, self.z),
                color=COLOR_LOG_END_RING if rings_mat is None else WHITE,
                material=rings_mat,
                cast_shadows=False,
                name="LogRingR",
            )
            self.sub_entities.append((ring_l, (-trunk_w * 0.5 - ring_w * 0.5, 0.0, 0.0)))
            self.sub_entities.append((ring_r, (trunk_w * 0.5 + ring_w * 0.5, 0.0, 0.0)))


class TrainObstacle(BaseObstacle):
    """High-speed aerodynamic bullet train that zooms past on RailRow."""

    def __init__(
        self,
        x: float,
        z: float,
        speed: float = 45.0,
        width: float = 24.0,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
        direction: Optional[float] = None,
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
            material_registry=material_registry,
        )

        facing_dir = 1.0 if (direction is not None and direction >= 0) or (direction is None and speed >= 0) else -1.0

        if scene is not None:
            body_mat = _get_mat(self.material_registry, "train_body")
            win_mat = _get_mat(self.material_registry, "train_window")
            front_mat = _get_mat(self.material_registry, "train_front")

            # 1. Main train locomotive body with sleek white/silver livery
            body_col = WHITE if body_mat is not None else Color.from_hex("#f1f5f9")
            self.entity = scene.create_box(
                size=(width, height, depth),
                position=(self.x, self.y, self.z),
                color=body_col,
                material=body_mat,
                cast_shadows=True,
                name="BulletTrainBody",
            )

            # 2. Window strip
            win_col = WHITE if win_mat is not None else COLOR_TRAIN_WINDOWS
            win = scene.create_box(
                size=(width * 0.94, height * 0.28, depth * 1.04),
                position=(self.x, self.y + 0.18, self.z),
                color=win_col,
                material=win_mat,
                cast_shadows=False,
                name="BulletTrainWindows",
            )
            self.sub_entities.append((win, (0.0, 0.18, 0.0)))

            # 3. Aerodynamic front nose wedge/plate decal in travel direction
            nose_ox = facing_dir * (width * 0.50 + 0.08)
            nose_col = WHITE if front_mat is not None else Color.from_hex("#e2e8f0")
            nose = scene.create_box(
                size=(0.16, height * 0.88, depth * 0.96),
                position=(self.x + nose_ox, self.y, self.z),
                color=nose_col,
                material=front_mat,
                cast_shadows=True,
                name="BulletTrainNose",
            )
            self.sub_entities.append((nose, (nose_ox, 0.0, 0.0)))

            # 4. Luminous front headlights
            hl_x = facing_dir * (width * 0.50 + 0.17)
            hl_col = Color.from_hex("#fff59d")
            hl1 = scene.create_box(
                size=(0.08, 0.14, 0.18),
                position=(self.x + hl_x, self.y - 0.10, self.z - 0.22),
                color=hl_col,
                cast_shadows=False,
                name="TrainHeadlight1",
            )
            hl2 = scene.create_box(
                size=(0.08, 0.14, 0.18),
                position=(self.x + hl_x, self.y - 0.10, self.z + 0.22),
                color=hl_col,
                cast_shadows=False,
                name="TrainHeadlight2",
            )
            hl_top = scene.create_box(
                size=(0.08, 0.12, 0.14),
                position=(self.x + hl_x, self.y + 0.26, self.z),
                color=WHITE,
                cast_shadows=False,
                name="TrainHighBeam",
            )
            self.sub_entities.append((hl1, (hl_x, -0.10, -0.22)))
            self.sub_entities.append((hl2, (hl_x, -0.10, 0.22)))
            self.sub_entities.append((hl_top, (hl_x, 0.26, 0.0)))

            # 5. Roof fluting (aerodynamic metallic ribs along the roof)
            flute_col = Color.from_hex("#cbd5e1")
            flute1 = scene.create_box(
                size=(width * 0.96, 0.05, 0.12),
                position=(self.x, self.y + height * 0.51, self.z - 0.18),
                color=flute_col,
                material=body_mat,
                cast_shadows=False,
                name="BulletTrainRoofFlute1",
            )
            flute2 = scene.create_box(
                size=(width * 0.96, 0.05, 0.12),
                position=(self.x, self.y + height * 0.51, self.z + 0.18),
                color=flute_col,
                material=body_mat,
                cast_shadows=False,
                name="BulletTrainRoofFlute2",
            )
            self.sub_entities.append((flute1, (0.0, height * 0.51, -0.18)))
            self.sub_entities.append((flute2, (0.0, height * 0.51, 0.18)))


# =============================================================================
# Procedural Voxel Tree
# =============================================================================
class VoxelTree:
    """Procedural voxel tree with organic shape variety, layered tiers, and authentic Crossy Road styling."""

    def __init__(
        self,
        x: float,
        z: float,
        foliage_color: Optional[Color] = None,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
        cast_shadows: bool = True,
        tree_type: str = "standard",
        scale: float = 1.0,
        max_foliage_depth: Optional[float] = None,
    ) -> None:
        self.x: float = float(x)
        self.z: float = float(z)
        self.material_registry: Optional[Any] = (
            material_registry if material_registry is not None
            else (get_default_material_registry() if scene is not None else None)
        )
        self.entities: List[Any] = []

        if scene is not None:
            trunk_mat = _get_mat(self.material_registry, "wood_bark")
            foliage_mat = _get_mat(self.material_registry, "tree_leaves")
            fol_col = foliage_color if foliage_color is not None else random.choice(COLOR_TREE_FOLIAGE)

            def _clamp_d(val: float) -> float:
                return min(val, max_foliage_depth) if max_foliage_depth is not None else val

            if tree_type == "shrub":
                # Low ground bush / shrub
                trunk = scene.create_box(
                    size=(0.30 * scale, 0.30 * scale, 0.30 * scale),
                    position=(self.x, 0.15 * scale, self.z),
                    color=COLOR_TREE_TRUNK if trunk_mat is None else WHITE,
                    material=trunk_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeTrunk",
                )
                foliage = scene.create_box(
                    size=(0.95 * scale, 0.65 * scale, _clamp_d(0.95 * scale)),
                    position=(self.x, 0.50 * scale, self.z),
                    color=fol_col if foliage_mat is None else WHITE,
                    material=foliage_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeFoliage",
                )
                self.entities.extend([trunk, foliage])

            elif tree_type == "pine":
                # 2-tier conical alpine pine tree
                trunk = scene.create_box(
                    size=(0.35 * scale, 0.85 * scale, 0.35 * scale),
                    position=(self.x, 0.425 * scale, self.z),
                    color=COLOR_TREE_TRUNK if trunk_mat is None else WHITE,
                    material=trunk_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeTrunk",
                )
                fol_tier1 = scene.create_box(
                    size=(1.25 * scale, 0.70 * scale, _clamp_d(1.25 * scale)),
                    position=(self.x, 1.10 * scale, self.z),
                    color=fol_col if foliage_mat is None else WHITE,
                    material=foliage_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeFoliage",
                )
                fol_tier2 = scene.create_box(
                    size=(0.80 * scale, 0.80 * scale, _clamp_d(0.80 * scale)),
                    position=(self.x, 1.75 * scale, self.z),
                    color=fol_col if foliage_mat is None else WHITE,
                    material=foliage_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeFoliageTop",
                )
                self.entities.extend([trunk, fol_tier1, fol_tier2])

            elif tree_type == "tall":
                # Tall canopy tree
                trunk = scene.create_box(
                    size=(0.40 * scale, 1.40 * scale, 0.40 * scale),
                    position=(self.x, 0.70 * scale, self.z),
                    color=COLOR_TREE_TRUNK if trunk_mat is None else WHITE,
                    material=trunk_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeTrunk",
                )
                foliage = scene.create_box(
                    size=(1.15 * scale, 1.25 * scale, _clamp_d(1.15 * scale)),
                    position=(self.x, 1.90 * scale, self.z),
                    color=fol_col if foliage_mat is None else WHITE,
                    material=foliage_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeFoliage",
                )
                self.entities.extend([trunk, foliage])

            elif tree_type == "arch":
                # Flanking highway/river arch tree (tall clearance so vehicles/logs pass underneath)
                trunk = scene.create_box(
                    size=(0.38 * scale, 2.40 * scale, 0.38 * scale),
                    position=(self.x, 1.20 * scale, self.z),
                    color=COLOR_TREE_TRUNK if trunk_mat is None else WHITE,
                    material=trunk_mat,
                    cast_shadows=cast_shadows,
                    has_collision=False,
                    name="TreeTrunk",
                )
                foliage = scene.create_box(
                    size=(1.50 * scale, 1.20 * scale, _clamp_d(1.50 * scale)),
                    position=(self.x, 2.80 * scale, self.z),
                    color=fol_col if foliage_mat is None else WHITE,
                    material=foliage_mat,
                    cast_shadows=cast_shadows,
                    has_collision=False,
                    name="TreeFoliage",
                )
                self.entities.extend([trunk, foliage])

            else:
                # Default "standard" Crossy Road voxel tree (EXACTLY 2 entities: trunk, foliage)
                trunk = scene.create_box(
                    size=(0.4 * scale, 0.7 * scale, 0.4 * scale),
                    position=(self.x, 0.35 * scale, self.z),
                    color=COLOR_TREE_TRUNK if trunk_mat is None else WHITE,
                    material=trunk_mat,
                    cast_shadows=cast_shadows,
                    has_collision=True,
                    name="TreeTrunk",
                )
                foliage = scene.create_box(
                    size=(0.92 * scale, 1.15 * scale, _clamp_d(0.92 * scale)),
                    position=(self.x, 1.25 * scale, self.z),
                    color=fol_col if foliage_mat is None else WHITE,
                    material=foliage_mat,
                    cast_shadows=cast_shadows,
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

    def __init__(
        self,
        z_index: int,
        row_type: RowType,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
    ) -> None:
        self.z_index: int = int(z_index)
        self.row_type: RowType = row_type
        self.entities: List[Any] = []
        self.obstacles: List[ObstacleContract] = []
        self.scene: Optional[Any] = scene
        self.material_registry: Optional[Any] = (
            material_registry if material_registry is not None
            else (get_default_material_registry() if scene is not None else None)
        )

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


BOUNDARY_FOREST_LANES: List[int] = [
    -24, -20, -18, -16, -14, -13, -12, -11,
    11, 12, 13, 14, 16, 18, 20, 24,
]


def _forest_hash(z: int, lane: int, salt: int = 0) -> int:
    """Deterministic 32-bit integer hash for procedural forest jitter and tree attributes."""
    h = ((int(z) * 374761393) ^ (int(lane) * 668265263) ^ (int(salt) * 1442695040888963407 & 0xFFFFFFFF)) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return (h ^ (h >> 16)) & 0x7FFFFFFF


def populate_boundary_forest(
    row: BaseRow,
    z_index: int,
    scene: Optional[Any],
    material_registry: Optional[Any],
    is_road_or_river: bool = False,
    adjacent_road_or_rail: bool = False,
) -> None:
    """Generate organic, varied, and layered voxel forest framing the playable corridor."""
    # Ensure boundary lanes are marked as blocked in row
    for bx in BOUNDARY_FOREST_LANES:
        if hasattr(row, "blocked_lanes"):
            row.blocked_lanes.add(bx)
    if hasattr(row, "blocked_lanes"):
        for bx in range(-25, -10):
            row.blocked_lanes.add(bx)
        for bx in range(11, 26):
            row.blocked_lanes.add(bx)

    if scene is None or is_road_or_river:
        return

    max_fol_depth = 0.70 if adjacent_road_or_rail else None

    # Deterministic generation per lane
    for lane in BOUNDARY_FOREST_LANES:
        h = _forest_hash(z_index, lane)

        # For grass & start rows: full rich organic forest
        jitter_x = (((h % 1000) / 1000.0) - 0.5) * 0.44  # +/- 0.22 X jitter
        if adjacent_road_or_rail:
            jitter_z = 0.0  # Clamp Z jitter so trees strictly remain inside grass row
        else:
            jitter_z = ((((h >> 8) % 1000) / 1000.0) - 0.5) * 0.30  # +/- 0.15 Z jitter
        tx = float(lane) + jitter_x
        tz = float(z_index) + jitter_z

        type_code = (h >> 16) % 6
        if type_code == 0:
            tree_type = "shrub"
        elif type_code in (1, 2):
            tree_type = "pine"
        elif type_code == 3:
            tree_type = "tall"
        else:
            tree_type = "standard"

        col_idx = (h >> 20) % len(COLOR_TREE_FOLIAGE)
        fol_col = COLOR_TREE_FOLIAGE[col_idx]
        scale = 0.85 + (((h >> 12) % 35) / 100.0)

        tree = VoxelTree(
            tx, tz,
            foliage_color=fol_col,
            scene=scene,
            material_registry=material_registry,
            cast_shadows=False,
            tree_type=tree_type,
            scale=scale,
            max_foliage_depth=max_fol_depth,
        )
        row.entities.extend(tree.entities)

        # Deep forest layering: for lanes far out (abs >= 14), add secondary staggered shrub/tree
        if abs(lane) >= 14 and ((h >> 24) % 3 == 0):
            h2 = _forest_hash(z_index, lane, salt=77)
            stagger_z = tz + (0.0 if adjacent_road_or_rail else (0.32 if (h2 % 2 == 0) else -0.32))
            stagger_x = tx + (0.30 if (h2 % 3 == 0) else -0.30)
            sub_col = COLOR_TREE_FOLIAGE[(h2 >> 4) % len(COLOR_TREE_FOLIAGE)]
            sub_tree = VoxelTree(
                stagger_x, stagger_z,
                foliage_color=sub_col,
                scene=scene,
                material_registry=material_registry,
                cast_shadows=False,
                tree_type="shrub",
                scale=0.75,
                max_foliage_depth=max_fol_depth,
            )
            row.entities.extend(sub_tree.entities)


class StartRow(BaseRow):
    """Safe starting zone row with wide green ground and authentic organic voxel boundary trees."""

    def __init__(
        self,
        z_index: int,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
        adjacent_road_or_rail: bool = False,
    ) -> None:
        super().__init__(z_index, RowType.START, scene, material_registry)
        self.blocked_lanes: Set[int] = set()
        self.adjacent_road_or_rail: bool = bool(adjacent_road_or_rail)

        if scene is not None:
            mat = _get_mat(self.material_registry, "grass", uv_scale=(140.0, 1.0))
            ground = scene.create_box(
                size=(140.0, 0.45, 1.0),
                position=(0.0, -0.225, float(self.z_index)),
                color=COLOR_START_ZONE if mat is None else WHITE,
                material=mat,
                cast_shadows=False,
                has_collision=False,
                name="StartGround",
            )
            self.entities.append(ground)

        # Populate organic boundary forest outside playable corridor [-10, 10]
        populate_boundary_forest(
            self,
            self.z_index,
            scene,
            self.material_registry,
            is_road_or_river=False,
            adjacent_road_or_rail=self.adjacent_road_or_rail,
        )

    def is_blocked(self, px: float, pz: float) -> bool:
        if abs(pz - self.z_index) <= 0.6:
            return int(round(px)) in self.blocked_lanes
        return False


class GrassRow(BaseRow):
    """Vibrant meadow row with procedural trees and authentic voxel pine forest borders."""

    def __init__(
        self,
        z_index: int,
        tree_density: float = 0.22,
        rng: Optional[random.Random] = None,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
        adjacent_road_or_rail: bool = False,
    ) -> None:
        super().__init__(z_index, RowType.GRASS, scene, material_registry)
        self.adjacent_road_or_rail: bool = bool(adjacent_road_or_rail)
        r = rng if rng is not None else random.Random()
        self.blocked_lanes: Set[int] = set()

        # Alternate strip color slightly for satisfying voxel checkerboard pattern
        ground_col = COLOR_GRASS_EVEN if (abs(z_index) % 2 == 0) else COLOR_GRASS_ODD
        if scene is not None:
            mat = _get_mat(self.material_registry, "grass", uv_scale=(140.0, 1.0))
            ground = scene.create_box(
                size=(140.0, 0.45, 1.0),
                position=(0.0, -0.225, float(self.z_index)),
                color=ground_col if mat is None else WHITE,
                material=mat,
                cast_shadows=False,
                has_collision=False,
                name=f"GrassGround_{z_index}",
            )
            self.entities.append(ground)

        # Dense organic voxel boundary trees outside playable grid
        populate_boundary_forest(
            self,
            self.z_index,
            scene,
            self.material_registry,
            is_road_or_river=False,
            adjacent_road_or_rail=self.adjacent_road_or_rail,
        )

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
            tree = VoxelTree(
                cand_x,
                float(self.z_index),
                foliage_color=fol_col,
                scene=scene,
                material_registry=self.material_registry,
                cast_shadows=True,
                max_foliage_depth=0.70 if self.adjacent_road_or_rail else None,
            )
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
        material_registry: Optional[Any] = None,
        has_prev_road: bool = False,
        has_next_road: bool = False,
        prev_direction: Optional[float] = None,
        next_direction: Optional[float] = None,
        direction: Optional[float] = None,
        place_prev_divider: bool = False,
    ) -> None:
        super().__init__(z_index, RowType.ROAD, scene, material_registry)
        self.blocked_lanes: Set[int] = set()
        r = rng if rng is not None else random.Random()

        # Direction and speed
        if direction is not None:
            self.direction = 1.0 if direction >= 0 else -1.0
        else:
            self.direction = 1.0 if (abs(z_index) % 2 == 0) else -1.0
        base_spd = speed if speed is not None else r.uniform(5.0, 9.5)
        signed_speed = abs(base_spd) * self.direction

        self.has_prev_road = has_prev_road
        self.has_next_road = has_next_road
        self.prev_direction = prev_direction
        self.next_direction = next_direction

        # 1. Dark asphalt strip
        if scene is not None:
            asphalt_mat = _get_mat(self.material_registry, "asphalt", uv_scale=(140.0, 1.0))
            asphalt = scene.create_box(
                size=(140.0, 0.40, 1.0),
                position=(0.0, -0.20, float(self.z_index)),
                color=COLOR_ROAD_ASPHALT if asphalt_mat is None else WHITE,
                material=asphalt_mat,
                cast_shadows=False,
                has_collision=False,
                name=f"RoadAsphalt_{z_index}",
            )
            self.entities.append(asphalt)

            # Road Markings:
            # A single-direction road lane does NOT have a dashed line down the center.
            # Outer borders have solid white edge lines (at z ± 0.45).
            if not self.has_prev_road:
                edge_south = scene.create_box(
                    size=(140.0, 0.03, 0.08),
                    position=(0.0, 0.025, float(self.z_index) - 0.45),
                    color=COLOR_ROAD_EDGE_WHITE,
                    cast_shadows=False,
                    has_collision=False,
                    name=f"RoadEdgeSouth_{z_index}",
                )
                self.entities.append(edge_south)

            if not self.has_next_road:
                edge_north = scene.create_box(
                    size=(140.0, 0.03, 0.08),
                    position=(0.0, 0.025, float(self.z_index) + 0.45),
                    color=COLOR_ROAD_EDGE_WHITE,
                    cast_shadows=False,
                    has_collision=False,
                    name=f"RoadEdgeNorth_{z_index}",
                )
                self.entities.append(edge_north)

            # Shared border with next road (z + 0.5):
            if self.has_next_road:
                z_shared = float(self.z_index) + 0.5
                target_next_dir = (
                    self.next_direction
                    if self.next_direction is not None
                    else (1.0 if (abs(z_index + 1) % 2 == 0) else -1.0)
                )
                is_opposing = (self.direction * target_next_dir) < 0

                if is_opposing:
                    # Opposing directions meet -> distinct center divider (double solid yellow lines)
                    div_a = scene.create_box(
                        size=(140.0, 0.03, 0.04),
                        position=(0.0, 0.025, z_shared - 0.04),
                        color=COLOR_ROAD_DIVIDER_CENTER,
                        cast_shadows=False,
                        has_collision=False,
                        name=f"CenterDividerA_{z_index}",
                    )
                    div_b = scene.create_box(
                        size=(140.0, 0.03, 0.04),
                        position=(0.0, 0.025, z_shared + 0.04),
                        color=COLOR_ROAD_DIVIDER_CENTER,
                        cast_shadows=False,
                        has_collision=False,
                        name=f"CenterDividerB_{z_index}",
                    )
                    self.entities.append(div_a)
                    self.entities.append(div_b)
                else:
                    # Same direction lanes -> dashed white lane divider
                    for mx in range(-28, 29, 4):
                        marker = scene.create_box(
                            size=(1.4, 0.03, 0.10),
                            position=(float(mx), 0.025, z_shared),
                            color=COLOR_ROAD_DASH_WHITE,
                            cast_shadows=False,
                            has_collision=False,
                            name=f"LaneDivider_{z_index}_{mx}",
                        )
                        self.entities.append(marker)

            # Optional divider along prev border (z - 0.5) when requested
            if self.has_prev_road and place_prev_divider:
                z_shared_prev = float(self.z_index) - 0.5
                target_prev_dir = (
                    self.prev_direction
                    if self.prev_direction is not None
                    else (1.0 if (abs(z_index - 1) % 2 == 0) else -1.0)
                )
                is_opposing_prev = (self.direction * target_prev_dir) < 0
                if is_opposing_prev:
                    div_a = scene.create_box(
                        size=(140.0, 0.03, 0.04),
                        position=(0.0, 0.025, z_shared_prev - 0.04),
                        color=COLOR_ROAD_DIVIDER_CENTER,
                        cast_shadows=False,
                        has_collision=False,
                        name=f"CenterDividerPrevA_{z_index}",
                    )
                    div_b = scene.create_box(
                        size=(140.0, 0.03, 0.04),
                        position=(0.0, 0.025, z_shared_prev + 0.04),
                        color=COLOR_ROAD_DIVIDER_CENTER,
                        cast_shadows=False,
                        has_collision=False,
                        name=f"CenterDividerPrevB_{z_index}",
                    )
                    self.entities.append(div_a)
                    self.entities.append(div_b)
                else:
                    for mx in range(-28, 29, 4):
                        marker = scene.create_box(
                            size=(1.4, 0.03, 0.10),
                            position=(float(mx), 0.025, z_shared_prev),
                            color=COLOR_ROAD_DASH_WHITE,
                            cast_shadows=False,
                            has_collision=False,
                            name=f"LaneDividerPrev_{z_index}_{mx}",
                        )
                        self.entities.append(marker)



        # 2. Vehicles (3-4 cars or trucks spawning and wrapping far off-screen)
        count = vehicle_count if vehicle_count is not None else r.choice([3, 4])
        wrap_min = -48.0
        wrap_max = 48.0
        span = wrap_max - wrap_min

        spacing = span / float(max(1, count))
        start_offset = r.uniform(0.0, spacing)

        spawn_x_positions = []
        for i in range(count):
            vx = wrap_min + start_offset + (i * spacing)
            if vx > wrap_max:
                vx -= span
            spawn_x_positions.append(vx)

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
                    material_registry=self.material_registry,
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
                    material_registry=self.material_registry,
                )
                self.obstacles.append(car)

        # 3. Unobstructed open roadway (no trees on traffic surface; mark boundary lanes blocked)
        for bx in range(-25, -10):
            self.blocked_lanes.add(bx)
        for bx in range(11, 26):
            self.blocked_lanes.add(bx)

    def is_blocked(self, px: float, pz: float) -> bool:
        if abs(pz - self.z_index) <= 0.6:
            return int(round(px)) in self.blocked_lanes
        return False

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
        material_registry: Optional[Any] = None,
    ) -> None:
        super().__init__(z_index, RowType.RIVER, scene, material_registry)
        self.blocked_lanes: Set[int] = set()
        r = rng if rng is not None else random.Random()

        # Water speed direction alternates per river row
        direction = 1.0 if (abs(z_index) % 2 == 1) else -1.0
        base_spd = speed if speed is not None else r.uniform(2.5, 5.0)
        signed_speed = abs(base_spd) * direction

        # 1. Vibrant water box (slightly lowered)
        if scene is not None:
            water_mat = _get_mat(self.material_registry, "water", uv_scale=(140.0, 1.0))
            water = scene.create_box(
                size=(140.0, 0.35, 1.0),
                position=(0.0, -0.22, float(self.z_index)),
                color=COLOR_RIVER_WATER if water_mat is None else WHITE,
                material=water_mat,
                cast_shadows=False,
                has_collision=False,
                name=f"RiverWater_{z_index}",
            )
            self.entities.append(water)

            # Riverbank stone boulders set back along the shoreline
            for rx in [-17.0, 17.0]:
                boulder = scene.create_box(
                    size=(1.5, 0.45, 0.40),
                    position=(rx, 0.08, float(self.z_index) - 0.38),
                    color=Color.from_hex("#57756f"),
                    cast_shadows=False,
                    has_collision=False,
                    name=f"RiverBoulder_{z_index}_{int(rx)}",
                )
                self.entities.append(boulder)

        # 2. Wooden logs (3-4 logs spaced out across widened span)
        count = log_count if log_count is not None else r.choice([3, 4])
        wrap_min = -38.0
        wrap_max = 38.0
        span = wrap_max - wrap_min

        spacing = span / float(max(1, count))
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
                material_registry=self.material_registry,
            )
            self.obstacles.append(log)

        # 3. Unobstructed open water channel (no trees on water; mark boundary lanes blocked)
        for bx in range(-25, -10):
            self.blocked_lanes.add(bx)
        for bx in range(11, 26):
            self.blocked_lanes.add(bx)

    def is_blocked(self, px: float, pz: float) -> bool:
        if abs(pz - self.z_index) <= 0.6:
            return int(round(px)) in self.blocked_lanes
        return False

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
        material_registry: Optional[Any] = None,
    ) -> None:
        super().__init__(z_index, RowType.RAIL, scene, material_registry)
        self.blocked_lanes: Set[int] = set()
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
        self.beacon_light_r: Optional[Any] = None

        if scene is not None:
            gravel_mat = _get_mat(self.material_registry, "rail_gravel", uv_scale=(140.0, 1.0))
            tie_mat = _get_mat(self.material_registry, "rail_tie")

            # 1. Gravel strip (full infinite span)
            gravel = scene.create_box(
                size=(140.0, 0.40, 1.0),
                position=(0.0, -0.20, float(self.z_index)),
                color=COLOR_RAIL_GRAVEL if gravel_mat is None else WHITE,
                material=gravel_mat,
                cast_shadows=False,
                has_collision=False,
                name=f"RailGravel_{z_index}",
            )
            self.entities.append(gravel)

            # 2. Wooden sleepers (ties) - step of 3 across the entire span
            for tx in range(-25, 26, 3):
                tie = scene.create_box(
                    size=(0.4, 0.05, 0.85),
                    position=(float(tx), 0.028, float(self.z_index)),
                    color=COLOR_RAIL_TIE if tie_mat is None else WHITE,
                    material=tie_mat,
                    cast_shadows=False,
                    has_collision=False,
                    name=f"RailTie_{z_index}_{tx}",
                )
                self.entities.append(tie)

            # 3. Metallic rails (2 parallel steel tracks)
            r1 = scene.create_box(
                size=(140.0, 0.06, 0.08),
                position=(0.0, 0.075, float(self.z_index) - 0.22),
                color=COLOR_RAIL_STEEL,
                cast_shadows=False,
                has_collision=False,
                name=f"RailSteel1_{z_index}",
            )
            r2 = scene.create_box(
                size=(140.0, 0.06, 0.08),
                position=(0.0, 0.075, float(self.z_index) + 0.22),
                color=COLOR_RAIL_STEEL,
                cast_shadows=False,
                has_collision=False,
                name=f"RailSteel2_{z_index}",
            )
            self.entities.extend([r1, r2])

            # 4. Authentic Railway Crossing Signal (Mast, Crossbuck, Dual Flashing Red Beacons)
            beacon_x = -11.5 if self.train_direction > 0.0 else 11.5
            beacon_z = float(self.z_index) - 0.44

            # Cast iron mast base
            base = scene.create_box(
                size=(0.40, 0.08, 0.40),
                position=(beacon_x, 0.04, beacon_z),
                color=Color.from_hex("#1e293b"),
                has_collision=False,
                name=f"BeaconBase_{z_index}",
            )
            # Heavy dark industrial steel post
            post = scene.create_box(
                size=(0.12, 1.35, 0.12),
                position=(beacon_x, 0.70, beacon_z),
                color=Color.from_hex("#334155"),
                has_collision=False,
                name=f"BeaconPost_{z_index}",
            )
            # High-visibility crossbuck warning sign ('X' plate)
            crossbuck = scene.create_box(
                size=(0.65, 0.14, 0.04),
                position=(beacon_x, 1.35, beacon_z + 0.02),
                color=Color.from_hex("#f8fafc"),
                has_collision=False,
                name=f"BeaconCross_{z_index}",
            )
            # Signal flasher housing bar
            head = scene.create_box(
                size=(0.56, 0.22, 0.16),
                position=(beacon_x, 1.12, beacon_z + 0.02),
                color=Color.from_hex("#0f172a"),
                has_collision=False,
                name=f"BeaconHead_{z_index}",
            )
            # Dual alternating warning flasher lenses
            self.beacon_light_entity = scene.create_box(
                size=(0.18, 0.18, 0.08),
                position=(beacon_x - 0.17, 1.12, beacon_z - 0.07),
                color=COLOR_BEACON_IDLE,
                has_collision=False,
                name=f"BeaconLightL_{z_index}",
            )
            self.beacon_light_r = scene.create_box(
                size=(0.18, 0.18, 0.08),
                position=(beacon_x + 0.17, 1.12, beacon_z - 0.07),
                color=COLOR_BEACON_IDLE,
                has_collision=False,
                name=f"BeaconLightR_{z_index}",
            )
            self.entities.extend([base, post, crossbuck, head, self.beacon_light_entity, self.beacon_light_r])



        # 5. Bullet train obstacle (starts off-screen)
        initial_train_x = -999.0
        self.train = TrainObstacle(
            x=initial_train_x,
            z=float(self.z_index),
            speed=0.0,
            scene=scene,
            material_registry=self.material_registry,
            direction=self.train_direction,
        )
        self.obstacles.append(self.train)

        # 6. Unobstructed railroad tracks (no trees on tracks; mark boundary lanes blocked)
        for bx in range(-25, -10):
            self.blocked_lanes.add(bx)
        for bx in range(11, 26):
            self.blocked_lanes.add(bx)

    def is_blocked(self, px: float, pz: float) -> bool:
        if abs(pz - self.z_index) <= 0.6:
            return int(round(px)) in self.blocked_lanes
        return False

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
        if getattr(self, "beacon_light_r", None) is not None:
            self.beacon_light_r.color = COLOR_BEACON_ACTIVE

        # Position train at approach edge (far off-screen)
        spawn_edge = 60.0
        if self.train_direction > 0.0:
            self.train.speed = self.train_speed
            self.train.set_position(-spawn_edge, self.train.y, self.train.z)
        else:
            self.train.speed = -self.train_speed
            self.train.set_position(spawn_edge, self.train.y, self.train.z)

    def update(self, dt: float) -> None:
        if dt <= 0.0:
            return

        self.train_timer += dt

        # Warning phase (before train enters)
        time_to_train = self.cycle_interval - self.train_timer
        if 0.0 < time_to_train <= self.warning_duration and not self.is_train_passing:
            self.is_warning = True
            self.blink_timer += dt
            # 6 Hz alternating flasher blink
            blink_state = int(self.blink_timer * 6.0) % 2 == 0
            self.beacon_lit = blink_state
            if self.beacon_light_entity is not None:
                self.beacon_light_entity.color = COLOR_BEACON_ACTIVE if blink_state else COLOR_BEACON_IDLE
            if getattr(self, "beacon_light_r", None) is not None:
                self.beacon_light_r.color = COLOR_BEACON_IDLE if blink_state else COLOR_BEACON_ACTIVE

        # Train arrival trigger
        if self.train_timer >= self.cycle_interval and not self.is_train_passing:
            self._start_train_pass()

        # Update train during passing phase
        if self.is_train_passing:
            self.train.update(dt)

            # Check if train has fully exited the visible area (far off-screen)
            spawn_edge = 60.0
            has_exited = (
                (self.train_direction > 0.0 and self.train.x > spawn_edge + self.train.width * 0.5)
                or (self.train_direction < 0.0 and self.train.x < -spawn_edge - self.train.width * 0.5)
            )

            if has_exited:
                self.is_train_passing = False
                self.is_warning = False
                self.train_timer = 0.0
                self.train.speed = 0.0
                self.train.set_position(-999.0, self.train.y, self.train.z)
                if self.beacon_light_entity is not None:
                    self.beacon_light_entity.color = COLOR_BEACON_IDLE
                if getattr(self, "beacon_light_r", None) is not None:
                    self.beacon_light_r.color = COLOR_BEACON_IDLE

    def check_player_hazard(self, px: float, pz: float) -> Tuple[bool, Optional[str], Optional[float]]:
        if abs(pz - self.z_index) <= 0.6:
            if self.is_train_passing and self.train.check_hit(px, pz, radius=0.35):
                return True, "squashed", None
        return False, None, None


# =============================================================================
# Panoramic Alpine Mountain Horizon Backdrop
# =============================================================================
class HorizonBackdrop:
    """Majestic low-poly voxel alpine mountain range and rolling foothill ridges framing the horizon."""

    def __init__(
        self,
        scene: Optional[Any] = None,
        material_registry: Optional[Any] = None,
    ) -> None:
        self.scene: Optional[Any] = scene
        self.material_registry: Optional[Any] = material_registry
        self.entities: List[Any] = []
        self.peak_data: List[Tuple[Any, float, float, float]] = []  # (entity, rel_x, y, rel_z)
        self.current_forward_z: float = 24.0

        if scene is not None:
            self._build_mountain_range()

    def _build_mountain_range(self) -> None:
        """Construct soft pastel low-poly rolling foothill ridges across the panoramic horizon."""
        if self.scene is None:
            return

        # 15 gentle rolling foothill peaks spanning X from -68 to +68 (width >= 132)
        peak_x_positions = [
            -66.0, -56.0, -46.0, -36.0, -26.0, -18.0, -10.0,
            0.0, 10.0, 18.0, 26.0, 36.0, 46.0, 56.0, 66.0,
        ]

        # Soft pastel atmospheric palette harmonious with sky fog #70b0e0
        col_foothill = Color.from_hex("#8ecae6")   # Soft pastel sky azure
        col_ridge = Color.from_hex("#90e0ef")      # Misty morning cyan
        col_crest = Color.from_hex("#bde0fe")      # Powder blue summit haze
        col_snow = Color.from_hex("#f1f5f9")       # Soft alpine snow crest
        col_soft_pine = Color.from_hex("#88ab98")  # Misty pastel sage pine
        col_soft_trunk = Color.from_hex("#7c9a92") # Soft slate sage trunk

        for i, px in enumerate(peak_x_positions):
            # Gentle, low rolling foothill dimensions
            w1 = 16.0 + float((i * 7) % 6)
            h1 = 2.8 + float((i * 3) % 3) * 0.4
            d1 = 7.0 + float((i * 5) % 3)

            w2 = w1 * 0.70
            h2 = 2.4 + float((i * 5) % 3) * 0.3
            d2 = d1 * 0.65

            w3 = w2 * 0.55
            h3 = 1.8 + float((i * 2) % 2) * 0.3
            d3 = d2 * 0.60

            rel_z = float(((i * 11) % 5) * 1.8)

            y_base = -0.5 + (h1 * 0.5)
            y_crag = -0.5 + h1 + (h2 * 0.5)
            y_snow = -0.5 + h1 + h2 + (h3 * 0.5)

            # Tier 1: Soft Rolling Foothill Base
            base_box = self.scene.create_box(
                size=(w1, h1, d1),
                position=(px, y_base, self.current_forward_z + rel_z),
                color=col_foothill,
                cast_shadows=False,
                has_collision=False,
                name=f"HorizonMountainBase_{i}",
            )
            self.entities.append(base_box)
            self.peak_data.append((base_box, px, y_base, rel_z))

            # Tier 2: Misty Pastel Ridge
            crag_box = self.scene.create_box(
                size=(w2, h2, d2),
                position=(px, y_crag, self.current_forward_z + rel_z),
                color=col_ridge,
                cast_shadows=False,
                has_collision=False,
                name=f"HorizonMountainCrag_{i}",
            )
            self.entities.append(crag_box)
            self.peak_data.append((crag_box, px, y_crag, rel_z))

            # Tier 3: Soft Blue-White Crest
            snow_box = self.scene.create_box(
                size=(w3, h3, d3),
                position=(px, y_snow, self.current_forward_z + rel_z),
                color=col_snow if (i % 2 == 0) else col_crest,
                cast_shadows=False,
                has_collision=False,
                name=f"HorizonMountainSnow_{i}",
            )
            self.entities.append(snow_box)
            self.peak_data.append((snow_box, px, y_snow, rel_z))

            # Soft Misty Pine Silhouettes along shoulder
            for sign in (-1.0, 1.0):
                tree_x = px + (sign * w1 * 0.35)
                tree_y = -0.5 + h1 + 0.5
                pine_trunk = self.scene.create_box(
                    size=(0.4, 1.0, 0.4),
                    position=(tree_x, tree_y, self.current_forward_z + rel_z + (sign * 1.5)),
                    color=col_soft_trunk,
                    cast_shadows=False,
                    has_collision=False,
                    name=f"MountainPineTrunk_{i}_{int(sign)}",
                )
                pine_foliage = self.scene.create_box(
                    size=(1.5, 1.8, 1.5),
                    position=(tree_x, tree_y + 1.2, self.current_forward_z + rel_z + (sign * 1.5)),
                    color=col_soft_pine,
                    cast_shadows=False,
                    has_collision=False,
                    name=f"MountainPineFoliage_{i}_{int(sign)}",
                )
                self.entities.extend([pine_trunk, pine_foliage])
                self.peak_data.append((pine_trunk, tree_x, tree_y, rel_z + (sign * 1.5)))
                self.peak_data.append((pine_foliage, tree_x, tree_y + 1.2, rel_z + (sign * 1.5)))



    def update(self, forward_z: float) -> None:
        """Stream forward mountain range to remain seamlessly aligned with the horizon."""
        base_z = float(forward_z)
        if abs(base_z - self.current_forward_z) < 0.2:
            return

        self.current_forward_z = base_z
        for ent, rel_x, y, rel_z in self.peak_data:
            if ent is not None and hasattr(ent, "transform"):
                ent.transform.set_position(rel_x, y, base_z + rel_z)

    def cleanup(self) -> None:
        """Remove all backdrop mountain entities from scene."""
        if self.scene is not None:
            for ent in self.entities:
                try:
                    self.scene.remove_entity(ent)
                except Exception:
                    pass
        self.entities.clear()
        self.peak_data.clear()


# =============================================================================
# High-Performance Streaming World Generator
# =============================================================================
class WorldGenerator:
    """Manages procedural infinite world generation and row pruning."""

    def __init__(
        self,
        scene: Optional[Any] = None,
        seed: Optional[int] = None,
        material_registry: Optional[Any] = None,
    ) -> None:
        self.scene: Optional[Any] = scene
        self.seed: Optional[int] = seed
        self.rng: random.Random = random.Random(seed)

        if material_registry is not None:
            self.material_registry = material_registry
        elif MaterialRegistry is not None and scene is not None:
            try:
                self.material_registry = MaterialRegistry()
            except Exception:
                self.material_registry = None
        else:
            self.material_registry = None

        self.registry = self.material_registry

        self.active_rows: Dict[int, WorldRowContract] = {}
        self.max_generated_z: int = -1
        self.min_active_z: int = 0
        self.backdrop: Optional[HorizonBackdrop] = None
        self._planned_row_types: Dict[int, RowType] = {}

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

        if self.backdrop is not None:
            self.backdrop.cleanup()
        self.backdrop = HorizonBackdrop(scene=self.scene, material_registry=self.material_registry)

        if self.seed is not None:
            self.rng = random.Random(self.seed)

        self.max_generated_z = -1
        self.min_active_z = -5
        self._planned_row_types.clear()
        for z in range(-5, 1):
            self._planned_row_types[z] = RowType.START
        self._current_clump_type = RowType.GRASS
        self._clump_remaining = 0
        self._clump_size = 0
        self._clump_step = 0
        self._last_major_type = RowType.GRASS

        # 1. Safe start rows behind and around spawn [-5 .. 0]
        next_1_type = self._get_planned_row_type(1)
        for z in range(-5, 1):
            adj = (z == 0 and next_1_type in (RowType.ROAD, RowType.RAIL))
            start_row = StartRow(z, scene=self.scene, material_registry=self.material_registry, adjacent_road_or_rail=adj)
            self.active_rows[z] = start_row
            self.max_generated_z = z

        # 2. Initial forward lookahead terrain (Z = 1 .. 25)
        self.generate_ahead(player_z=0, lookahead=25)

    def _get_planned_row_type(self, z: int) -> RowType:
        """Fetch or procedurally advance planned row type for row z."""
        if z in self._planned_row_types:
            return self._planned_row_types[z]

        # Advance planning until z is reached
        last_z = max(self._planned_row_types.keys()) if self._planned_row_types else 0
        while last_z < z:
            plan_z = last_z + 1
            if self._clump_remaining <= 0:
                self._current_clump_type, self._clump_remaining = self._choose_next_clump()
                self._clump_size = self._clump_remaining
                self._clump_step = 0
            else:
                self._clump_step += 1

            self._planned_row_types[plan_z] = self._current_clump_type
            self._clump_remaining -= 1
            last_z = plan_z

        return self._planned_row_types[z]

    def _get_road_lane_direction(self, step: int, total_lanes: int, z: int) -> float:
        """Calculate traffic flow direction for a road lane within a multi-lane roadway."""
        if total_lanes <= 1:
            return 1.0 if (abs(z) % 2 == 0) else -1.0
        # Multi-lane roadway: opposing traffic on either side of the center divider
        half = total_lanes // 2
        return 1.0 if step < half else -1.0

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
        prev_type = self._get_planned_row_type(z - 1)
        next_type = self._get_planned_row_type(z + 1)
        is_adjacent_to_traffic = (
            prev_type in (RowType.ROAD, RowType.RAIL)
            or next_type in (RowType.ROAD, RowType.RAIL)
        )

        if row_type == RowType.GRASS:
            return GrassRow(
                z,
                rng=self.rng,
                scene=self.scene,
                material_registry=self.material_registry,
                adjacent_road_or_rail=is_adjacent_to_traffic,
            )
        elif row_type == RowType.ROAD:
            total_lanes = getattr(self, "_clump_size", 1)
            step = getattr(self, "_clump_step", 0)
            has_prev = (prev_type == RowType.ROAD)
            has_next = (next_type == RowType.ROAD)
            dir_curr = self._get_road_lane_direction(step, total_lanes, z)
            dir_next = self._get_road_lane_direction(step + 1, total_lanes, z + 1) if has_next else None
            dir_prev = self._get_road_lane_direction(step - 1, total_lanes, z - 1) if (has_prev and step > 0) else None

            return RoadRow(
                z,
                rng=self.rng,
                scene=self.scene,
                material_registry=self.material_registry,
                has_prev_road=has_prev,
                has_next_road=has_next,
                prev_direction=dir_prev,
                next_direction=dir_next,
                direction=dir_curr,
            )
        elif row_type == RowType.RIVER:
            return RiverRow(z, rng=self.rng, scene=self.scene, material_registry=self.material_registry)
        elif row_type == RowType.RAIL:
            return RailRow(z, rng=self.rng, scene=self.scene, material_registry=self.material_registry)
        else:
            return StartRow(
                z,
                scene=self.scene,
                material_registry=self.material_registry,
                adjacent_road_or_rail=is_adjacent_to_traffic,
            )

    def generate_ahead(self, player_z: int, lookahead: int = 25) -> None:
        """Stream new rows forward up to player_z + lookahead."""
        target_z = int(player_z + lookahead)
        while self.max_generated_z < target_z:
            next_z = self.max_generated_z + 1
            row_type = self._get_planned_row_type(next_z)
            row = self._create_row_by_type(next_z, row_type)
            self.active_rows[next_z] = row
            self.max_generated_z = next_z

        if getattr(self, "backdrop", None) is not None:
            self.backdrop.update(float(target_z + 28.0))

    def prune_behind(self, player_z: int, keep_behind: int = 8) -> None:
        """Remove and cleanup rows behind player_z - keep_behind to maintain 500+ FPS."""
        min_retained_z = int(player_z - keep_behind)
        stale_z = [z for z in self.active_rows.keys() if z < min_retained_z]

        for z in stale_z:
            row = self.active_rows.pop(z)
            row.cleanup(self.scene)

        stale_plan_z = [pz for pz in self._planned_row_types.keys() if pz < min_retained_z - 5]
        for pz in stale_plan_z:
            self._planned_row_types.pop(pz, None)

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

    def cleanup(self) -> None:
        """Clean up all active rows and horizon backdrop."""
        for row in list(self.active_rows.values()):
            row.cleanup(self.scene)
        self.active_rows.clear()
        if getattr(self, "backdrop", None) is not None:
            self.backdrop.cleanup()
