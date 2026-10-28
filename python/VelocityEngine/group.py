"""Three.js Parity: Hierarchical Transform Group."""

from __future__ import annotations
from typing import Sequence, Optional, List, Any
try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core


class Group:
    """Hierarchical transform container without geometry (Three.js THREE.Group parity).
    
    Allows grouping multiple child entities so transformations (position, rotation, scale)
    applied to the Group naturally propagate to all attached children.
    """

    def __init__(self, name: str = "Group", position: Sequence[float] = (0.0, 0.0, 0.0)) -> None:
        self.entity = _core.Entity()
        self.entity.name = name
        self.entity.visible = True
        self.entity.has_collision = False
        self.transform.position = (float(position[0]), float(position[1]), float(position[2]))
        self.children: List[Any] = []

    @property
    def name(self) -> str:
        return self.entity.name

    @name.setter
    def name(self, val: str) -> None:
        self.entity.name = str(val)

    @property
    def transform(self) -> _core.Transform:
        return self.entity.transform

    @property
    def position(self) -> _core.Vec3:
        return self.entity.transform.position

    @position.setter
    def position(self, val: Sequence[float]) -> None:
        self.entity.transform.position = (float(val[0]), float(val[1]), float(val[2]))

    @property
    def rotation(self) -> _core.Vec3:
        return self.entity.transform.rotation

    @rotation.setter
    def rotation(self, val: Sequence[float]) -> None:
        self.entity.transform.rotation = (float(val[0]), float(val[1]), float(val[2]))

    @property
    def scale(self) -> _core.Vec3:
        return self.entity.transform.scale

    @scale.setter
    def scale(self, val: Sequence[float]) -> None:
        self.entity.transform.scale = (float(val[0]), float(val[1]), float(val[2]))

    def add(self, *children: Any) -> Group:
        """Add one or more child entities to this group."""
        for child in children:
            if hasattr(child, "parent"):
                child.parent = self.entity
            elif hasattr(child, "entity") and hasattr(child.entity, "parent"):
                child.entity.parent = self.entity
            self.children.append(child)
        return self

    def remove(self, child: Any) -> None:
        """Remove a child entity from this group."""
        if child in self.children:
            self.children.remove(child)
            if hasattr(child, "parent"):
                child.parent = None
            elif hasattr(child, "entity") and hasattr(child.entity, "parent"):
                child.entity.parent = None

    def animate_position(self, target: Any, duration: float = 1.0, ease: str = "linear", **kwargs: Any) -> Any:
        return self.entity.animate_position(target, duration, ease, **kwargs)

    def animate_rotation_y(self, degrees: float, duration: float = 1.0, ease: str = "linear", **kwargs: Any) -> Any:
        return self.entity.animate_rotation_y(degrees, duration, ease, **kwargs)

    def animate_scale(self, target: Any, duration: float = 1.0, ease: str = "linear", **kwargs: Any) -> Any:
        return self.entity.animate_scale(target, duration, ease, **kwargs)
