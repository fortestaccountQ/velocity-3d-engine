"""Scene factory helper methods and procedural entity generation for VelocityEngine."""

from __future__ import annotations

from typing import Tuple, Sequence, Optional, Any, Union
from .color import Color, WHITE, GRAY, WARM_WHITE

try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core


def _to_vec3_tuple(val: Any) -> Tuple[float, float, float]:
    if isinstance(val, (int, float)):
        return (float(val), float(val), float(val))
    if isinstance(val, (tuple, list)):
        return (float(val[0]), float(val[1]), float(val[2]))
    if hasattr(val, "x") and hasattr(val, "y") and hasattr(val, "z"):
        return (float(val.x), float(val.y), float(val.z))
    raise ValueError(f"Cannot convert {val} to 3-tuple")


def create_box(
    scene: Any,
    size: Union[float, Sequence[float]] = (1.0, 1.0, 1.0),
    position: Sequence[float] = (0.0, 0.0, 0.0),
    color: Any = WHITE,
) -> Any:
    """Create a 3D box entity at specified position with dimensions (width, height, depth)."""
    sx, sy, sz = _to_vec3_tuple(size)
    px, py, pz = _to_vec3_tuple(position)
    col = Color(color) if color is not None else WHITE

    box_mesh = _core.Mesh.create_box(sx, sy, sz)
    entity = scene.create_entity("Box")
    entity.mesh = box_mesh
    entity.transform.set_position(px, py, pz)
    entity.color = col
    entity.has_collision = True
    return entity


def create_sphere(
    scene: Any,
    radius: float = 1.0,
    segments: int = 32,
    position: Sequence[float] = (0.0, 0.0, 0.0),
    color: Any = WHITE,
) -> Any:
    """Create a 3D sphere entity with specified radius and subdivision segments."""
    r = float(radius)
    seg = max(3, int(segments))
    px, py, pz = _to_vec3_tuple(position)
    col = Color(color) if color is not None else WHITE

    sphere_mesh = _core.Mesh.create_sphere(r, rings=seg, sectors=seg)
    entity = scene.create_entity("Sphere")
    entity.mesh = sphere_mesh
    entity.transform.set_position(px, py, pz)
    entity.color = col
    entity.has_collision = True
    return entity


def create_plane(
    scene: Any,
    width: float = 20.0,
    height: Optional[float] = None,
    subdivisions: int = 10,
    position: Sequence[float] = (0.0, 0.0, 0.0),
    color: Any = WHITE,
    **kwargs: Any,
) -> Any:
    """Create a horizontal ground plane with width, height, and texture subdivisions."""
    if "size" in kwargs:
        w = float(kwargs["size"])
        h = float(kwargs["size"]) if height is None else float(height)
    else:
        w = float(width)
        h = float(width) if height is None else float(height)

    subdiv = int(kwargs.get("uv_tiling", subdivisions))
    px, py, pz = _to_vec3_tuple(position)
    col = Color(color) if color is not None else WHITE

    plane_mesh = _core.Mesh.create_plane(width=w, depth=h, subdivisions_x=subdiv, subdivisions_z=subdiv)
    entity = scene.create_entity("Plane")
    entity.mesh = plane_mesh
    if "material" in kwargs and kwargs["material"] is not None:
        entity.material = kwargs["material"]
    entity.transform.set_position(px, py, pz)
    entity.color = col
    entity.has_collision = True
    return entity


def create_cylinder(
    scene: Any,
    radius: float = 0.5,
    height: float = 2.0,
    segments: int = 32,
    position: Sequence[float] = (0.0, 0.0, 0.0),
    color: Any = WHITE,
) -> Any:
    """Create a 3D cylinder entity with radius, height, and circumferential segments."""
    r = float(radius)
    h = float(height)
    seg = max(3, int(segments))
    px, py, pz = _to_vec3_tuple(position)
    col = Color(color) if color is not None else WHITE

    cyl_mesh = _core.Mesh.create_cylinder(radius=r, height=h, segments=seg, capped=True)
    entity = scene.create_entity("Cylinder")
    entity.mesh = cyl_mesh
    entity.transform.set_position(px, py, pz)
    entity.color = col
    entity.has_collision = True
    return entity


def create_grid(
    scene: Any,
    size: float = 50.0,
    step: float = 1.0,
    color: Any = GRAY,
) -> Any:
    """Create a reference floor grid of given size and step spacing."""
    s = float(size)
    st = float(step) if float(step) > 0.0 else 1.0
    subdiv = max(1, int(round(s / st)))
    col = Color(color) if color is not None else GRAY

    grid_mesh = _core.Mesh.create_plane(width=s, depth=s, subdivisions_x=subdiv, subdivisions_z=subdiv)
    entity = scene.create_entity("Grid")
    entity.mesh = grid_mesh
    entity.color = col
    entity.has_collision = False
    return entity


def set_sun(
    scene: Any,
    direction: Sequence[float] = (-1.0, -2.0, -1.0),
    color: Any = WARM_WHITE,
    intensity: float = 1.0,
) -> None:
    """Configure scene directional sun light direction, color, and intensity."""
    dx, dy, dz = _to_vec3_tuple(direction)
    col = Color(color) if color is not None else WARM_WHITE
    scene.light.set_direction(dx, dy, dz)
    scene.light.set_color(col.r, col.g, col.b)
    scene.light.intensity = float(intensity)


class SceneFactory:
    """Factory wrapper wrapping a Scene instance and providing fluent object instantiation."""

    def __init__(self, scene: Any) -> None:
        self.scene = scene

    def create_box(
        self,
        size: Union[float, Sequence[float]] = (1.0, 1.0, 1.0),
        position: Sequence[float] = (0.0, 0.0, 0.0),
        color: Any = WHITE,
    ) -> Any:
        return create_box(self.scene, size, position, color)

    def create_sphere(
        self,
        radius: float = 1.0,
        segments: int = 32,
        position: Sequence[float] = (0.0, 0.0, 0.0),
        color: Any = WHITE,
    ) -> Any:
        return create_sphere(self.scene, radius, segments, position, color)

    def create_plane(
        self,
        width: float = 20.0,
        height: Optional[float] = None,
        subdivisions: int = 10,
        position: Sequence[float] = (0.0, 0.0, 0.0),
        color: Any = WHITE,
        **kwargs: Any,
    ) -> Any:
        return create_plane(self.scene, width, height, subdivisions, position, color, **kwargs)

    def create_cylinder(
        self,
        radius: float = 0.5,
        height: float = 2.0,
        segments: int = 32,
        position: Sequence[float] = (0.0, 0.0, 0.0),
        color: Any = WHITE,
    ) -> Any:
        return create_cylinder(self.scene, radius, height, segments, position, color)

    def create_grid(
        self,
        size: float = 50.0,
        step: float = 1.0,
        color: Any = GRAY,
    ) -> Any:
        return create_grid(self.scene, size, step, color)

    def set_sun(
        self,
        direction: Sequence[float] = (-1.0, -2.0, -1.0),
        color: Any = WARM_WHITE,
        intensity: float = 1.0,
    ) -> None:
        set_sun(self.scene, direction, color, intensity)


def patch_scene() -> None:
    """Attach helper factory methods directly onto the native Scene class."""
    _core.Scene.create_box = lambda self, size=(1.0, 1.0, 1.0), position=(0.0, 0.0, 0.0), color=WHITE: create_box(self, size, position, color)
    _core.Scene.create_sphere = lambda self, radius=1.0, segments=32, position=(0.0, 0.0, 0.0), color=WHITE: create_sphere(self, radius, segments, position, color)
    _core.Scene.create_plane_orig = _core.Scene.create_plane
    _core.Scene.create_plane = lambda self, width=20.0, height=None, subdivisions=10, position=(0.0, 0.0, 0.0), color=WHITE, **kwargs: create_plane(self, width, height, subdivisions, position, color, **kwargs)
    _core.Scene.create_cylinder = lambda self, radius=0.5, height=2.0, segments=32, position=(0.0, 0.0, 0.0), color=WHITE: create_cylinder(self, radius, height, segments, position, color)
    _core.Scene.create_grid = lambda self, size=50.0, step=1.0, color=GRAY: create_grid(self, size, step, color)
    _core.Scene.set_sun = lambda self, direction=(-1.0, -2.0, -1.0), color=WARM_WHITE, intensity=1.0: set_sun(self, direction, color, intensity)
