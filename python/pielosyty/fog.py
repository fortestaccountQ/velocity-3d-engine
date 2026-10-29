"""Three.js Parity: Fog and Atmosphere."""

from __future__ import annotations
from typing import Union, Sequence, Optional
from .color import Color, as_color


class Fog:
    """Linear depth fog (Three.js THREE.Fog parity)."""

    def __init__(
        self,
        color: Union[Color, Sequence[float], str] = "#1a1a24",
        near: float = 10.0,
        far: float = 80.0,
    ) -> None:
        self.color = as_color(color)
        self.near = float(near)
        self.far = float(far)

    def __repr__(self) -> str:
        return f"Fog(color={self.color}, near={self.near}, far={self.far})"


class FogExp2:
    """Exponential squared depth fog (Three.js THREE.FogExp2 parity)."""

    def __init__(
        self,
        color: Union[Color, Sequence[float], str] = "#1a1a24",
        density: float = 0.02,
    ) -> None:
        self.color = as_color(color)
        self.density = float(density)

    def __repr__(self) -> str:
        return f"FogExp2(color={self.color}, density={self.density})"
