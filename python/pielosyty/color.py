"""Color representation and utility functions for VelocityEngine (Three.js Parity)."""

from __future__ import annotations

import colorsys
import math
from typing import Tuple, Sequence, Union, Optional, Any


class Color(tuple):
    """Immutable RGBA Color with float components in range [0.0, 1.0].

    Inherits from tuple for direct unpacking and zero-overhead interop with C++ bindings
    expecting glm::vec4, nanobind tuples, or 4-element sequences.
    """

    __slots__ = ()

    def __new__(
        cls,
        r_or_val: Union[float, Sequence[float], str, "Color"] = 1.0,
        g: Optional[float] = None,
        b: Optional[float] = None,
        a: Optional[float] = None,
    ) -> "Color":
        if isinstance(r_or_val, str):
            # Hex string or named preset
            val = r_or_val.strip().upper()
            if hasattr(cls, val):
                preset = getattr(cls, val)
                alpha_val = 1.0 if a is None else float(a)
                return cls.from_rgb(preset.r, preset.g, preset.b, alpha_val)
            alpha_val = 1.0 if a is None else float(a)
            return cls.from_hex(r_or_val, alpha=alpha_val)

        if isinstance(r_or_val, (tuple, list)):
            seq = r_or_val
            r_val = float(seq[0])
            g_val = float(seq[1]) if len(seq) > 1 else r_val
            b_val = float(seq[2]) if len(seq) > 2 else r_val
            a_val = float(seq[3]) if len(seq) > 3 else (1.0 if a is None else float(a))
            return super().__new__(cls, (r_val, g_val, b_val, a_val))

        if hasattr(r_or_val, "r") and hasattr(r_or_val, "g") and hasattr(r_or_val, "b"):
            r_val = float(r_or_val.r)
            g_val = float(r_or_val.g)
            b_val = float(r_or_val.b)
            a_val = float(r_or_val.a) if hasattr(r_or_val, "a") else (1.0 if a is None else float(a))
            return super().__new__(cls, (r_val, g_val, b_val, a_val))

        r_val = float(r_or_val)
        g_val = float(g) if g is not None else r_val
        b_val = float(b) if b is not None else r_val
        a_val = float(a) if a is not None else 1.0
        return super().__new__(cls, (r_val, g_val, b_val, a_val))

    @property
    def r(self) -> float:
        """Red component in range [0.0, 1.0]."""
        return self[0]

    @property
    def g(self) -> float:
        """Green component in range [0.0, 1.0]."""
        return self[1]

    @property
    def b(self) -> float:
        """Blue component in range [0.0, 1.0]."""
        return self[2]

    @property
    def a(self) -> float:
        """Alpha component in range [0.0, 1.0]."""
        return self[3]

    @classmethod
    def from_hex(cls, hex_str: str, alpha: float = 1.0) -> "Color":
        """Create Color from hex string (e.g., '#RRGGBB', 'RRGGBB', '#RGB', '#RRGGBBAA')."""
        s = hex_str.strip().lstrip("#")
        n = len(s)
        if n == 3:
            s = "".join([c * 2 for c in s]) + "FF"
        elif n == 4:
            s = "".join([c * 2 for c in s])
        elif n == 6:
            s = s + "FF"
        elif n == 8:
            pass
        else:
            raise ValueError(f"Invalid hex color string: '{hex_str}'")

        r = int(s[0:2], 16) / 255.0
        g = int(s[2:4], 16) / 255.0
        b = int(s[4:6], 16) / 255.0
        hex_a = int(s[6:8], 16) / 255.0
        final_a = hex_a if alpha == 1.0 else float(alpha)
        return cls(r, g, b, final_a)

    @classmethod
    def from_rgb(cls, r: float, g: float, b: float, a: float = 1.0) -> "Color":
        """Create Color from RGB(A) values. Values > 1.0 are automatically normalized from 0-255."""
        rf = float(r)
        gf = float(g)
        bf = float(b)
        af = float(a)
        if rf > 1.0 or gf > 1.0 or bf > 1.0:
            rf /= 255.0
            gf /= 255.0
            bf /= 255.0
        if af > 1.0:
            af /= 255.0
        return cls(rf, gf, bf, af)

    @classmethod
    def from_hsv(cls, h: float, s: float, v: float, a: float = 1.0) -> "Color":
        """Create Color from HSV values (h in [0.0, 360.0] or [0.0, 1.0], s and v in [0.0, 1.0] or [0.0, 100.0])."""
        hf = float(h)
        sf = float(s)
        vf = float(v)
        af = float(a)

        if hf > 1.0:
            hf = (hf % 360.0) / 360.0
        if sf > 1.0:
            sf = min(sf / 100.0, 1.0)
        if vf > 1.0:
            vf = min(vf / 100.0, 1.0)
        if af > 1.0:
            af /= 255.0

        r, g, b = colorsys.hsv_to_rgb(hf, sf, vf)
        return cls(r, g, b, af)

    def lerp(self, other: Union["Color", Sequence[float]], t: float) -> "Color":
        """Linearly interpolate towards another color by factor t in [0.0, 1.0]."""
        tf = float(t)
        or_val = float(other[0])
        og_val = float(other[1]) if len(other) > 1 else or_val
        ob_val = float(other[2]) if len(other) > 2 else or_val
        oa_val = float(other[3]) if len(other) > 3 else 1.0

        nr = self[0] + (or_val - self[0]) * tf
        ng = self[1] + (og_val - self[1]) * tf
        nb = self[2] + (ob_val - self[2]) * tf
        na = self[3] + (oa_val - self[3]) * tf
        return Color(nr, ng, nb, na)

    def with_alpha(self, a: float) -> "Color":
        """Return a copy of this color with a new alpha value."""
        return Color(self[0], self[1], self[2], float(a))

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """Return (r, g, b, a) tuple."""
        return (self[0], self[1], self[2], self[3])

    def to_vec4(self) -> Any:
        """Convert to VelocityEngine.Vec4."""
        from . import Vec4
        return Vec4(self[0], self[1], self[2], self[3])

    def to_vec3(self) -> Any:
        """Convert RGB to VelocityEngine.Vec3."""
        from . import Vec3
        return Vec3(self[0], self[1], self[2])

    def to_hex(self, include_alpha: bool = False) -> str:
        """Convert to hex color string."""
        ir = int(round(max(0.0, min(1.0, self[0])) * 255.0))
        ig = int(round(max(0.0, min(1.0, self[1])) * 255.0))
        ib = int(round(max(0.0, min(1.0, self[2])) * 255.0))
        if include_alpha:
            ia = int(round(max(0.0, min(1.0, self[3])) * 255.0))
            return f"#{ir:02X}{ig:02X}{ib:02X}{ia:02X}"
        return f"#{ir:02X}{ig:02X}{ib:02X}"

    def __repr__(self) -> str:
        return f"Color(r={self[0]:.3f}, g={self[1]:.3f}, b={self[2]:.3f}, a={self[3]:.3f})"

    def __add__(self, other: Any) -> "Color":
        if isinstance(other, (tuple, list)):
            return Color(self[0] + other[0], self[1] + other[1], self[2] + other[2], self[3])
        v = float(other)
        return Color(self[0] + v, self[1] + v, self[2] + v, self[3])

    def __sub__(self, other: Any) -> "Color":
        if isinstance(other, (tuple, list)):
            return Color(self[0] - other[0], self[1] - other[1], self[2] - other[2], self[3])
        v = float(other)
        return Color(self[0] - v, self[1] - v, self[2] - v, self[3])

    def __mul__(self, other: Any) -> "Color":
        if isinstance(other, (tuple, list)):
            oa = other[3] if len(other) > 3 else 1.0
            return Color(self[0] * other[0], self[1] * other[1], self[2] * other[2], self[3] * oa)
        v = float(other)
        return Color(self[0] * v, self[1] * v, self[2] * v, self[3])

    def __rmul__(self, other: Any) -> "Color":
        return self.__mul__(other)


# Standard presets
WHITE = Color(1.0, 1.0, 1.0, 1.0)
BLACK = Color(0.0, 0.0, 0.0, 1.0)
RED = Color(1.0, 0.0, 0.0, 1.0)
GREEN = Color(0.0, 1.0, 0.0, 1.0)
BLUE = Color(0.0, 0.0, 1.0, 1.0)
YELLOW = Color(1.0, 1.0, 0.0, 1.0)
CYAN = Color(0.0, 1.0, 1.0, 1.0)
MAGENTA = Color(1.0, 0.0, 1.0, 1.0)
GRAY = Color(0.5, 0.5, 0.5, 1.0)
DARK_GRAY = Color(0.25, 0.25, 0.25, 1.0)
LIGHT_GRAY = Color(0.75, 0.75, 0.75, 1.0)
WARM_WHITE = Color(1.0, 0.95, 0.86, 1.0)
ORANGE = Color(1.0, 0.5, 0.0, 1.0)
PURPLE = Color(0.5, 0.0, 0.5, 1.0)

# Attach presets to class for Color.WHITE access
Color.WHITE = WHITE
Color.BLACK = BLACK
Color.RED = RED
Color.GREEN = GREEN
Color.BLUE = BLUE
Color.YELLOW = YELLOW
Color.CYAN = CYAN
Color.MAGENTA = MAGENTA
Color.GRAY = GRAY
Color.DARK_GRAY = DARK_GRAY
Color.LIGHT_GRAY = LIGHT_GRAY
Color.WARM_WHITE = WARM_WHITE
Color.ORANGE = ORANGE
Color.PURPLE = PURPLE


def as_color(val: Any, default: Optional[Color] = None) -> Color:
    """Coerce any color-like object (Color, tuple, hex string) into a Color instance."""
    if isinstance(val, Color):
        return val
    if val is None:
        return default if default is not None else WHITE
    return Color(val)
