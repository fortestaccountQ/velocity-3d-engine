"""Tweening and animation system for VelocityEngine."""

from __future__ import annotations

import math
from typing import Callable, Optional, Sequence, Union, Any, List

try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core


# ---------------------------------------------------------------------------
# Easing Curves
# ---------------------------------------------------------------------------

def linear(t: float) -> float:
    return t


def in_quad(t: float) -> float:
    return t * t


def out_quad(t: float) -> float:
    return t * (2.0 - t)


def in_out_quad(t: float) -> float:
    if t < 0.5:
        return 2.0 * t * t
    return -1.0 + (4.0 - 2.0 * t) * t


def in_cubic(t: float) -> float:
    return t * t * t


def out_cubic(t: float) -> float:
    t -= 1.0
    return t * t * t + 1.0


def in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4.0 * t * t * t
    t -= 1.0
    return 1.0 + 4.0 * t * t * t


def out_bounce(t: float) -> float:
    n1 = 7.5625
    d1 = 2.75
    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def in_bounce(t: float) -> float:
    return 1.0 - out_bounce(1.0 - t)


def in_out_bounce(t: float) -> float:
    if t < 0.5:
        return (1.0 - out_bounce(1.0 - 2.0 * t)) * 0.5
    return (1.0 + out_bounce(2.0 * t - 1.0)) * 0.5


def in_elastic(t: float) -> float:
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    c4 = (2.0 * math.pi) / 3.0
    return -math.pow(2.0, 10.0 * t - 10.0) * math.sin((t * 10.0 - 10.75) * c4)


def out_elastic(t: float) -> float:
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    c4 = (2.0 * math.pi) / 3.0
    return math.pow(2.0, -10.0 * t) * math.sin((t * 10.0 - 0.75) * c4) + 1.0


def in_out_elastic(t: float) -> float:
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    c5 = (2.0 * math.pi) / 4.5
    if t < 0.5:
        return -(math.pow(2.0, 20.0 * t - 10.0) * math.sin((20.0 * t - 11.125) * c5)) / 2.0
    return (math.pow(2.0, -20.0 * t + 10.0) * math.sin((20.0 * t - 11.125) * c5)) / 2.0 + 1.0


EASING_MAP: dict[str, Callable[[float], float]] = {
    "linear": linear,
    "in_quad": in_quad,
    "out_quad": out_quad,
    "in_out_quad": in_out_quad,
    "in_cubic": in_cubic,
    "out_cubic": out_cubic,
    "in_out_cubic": in_out_cubic,
    "in_bounce": in_bounce,
    "out_bounce": out_bounce,
    "in_out_bounce": in_out_bounce,
    "in_elastic": in_elastic,
    "out_elastic": out_elastic,
    "in_out_elastic": in_out_elastic,
    # Common aliases
    "ease_in_quad": in_quad,
    "ease_out_quad": out_quad,
    "ease_in_out_quad": in_out_quad,
    "ease_in_cubic": in_cubic,
    "ease_out_cubic": out_cubic,
    "ease_in_out_cubic": in_out_cubic,
    "ease_in_bounce": in_bounce,
    "ease_out_bounce": out_bounce,
    "ease_in_out_bounce": in_out_bounce,
    "ease_in_elastic": in_elastic,
    "ease_out_elastic": out_elastic,
    "ease_in_out_elastic": in_out_elastic,
}


def get_easing(ease: Union[str, Callable[[float], float]]) -> Callable[[float], float]:
    """Retrieve easing function from name or callable."""
    if callable(ease):
        return ease
    key = str(ease).lower().strip().replace("-", "_")
    if key in EASING_MAP:
        return EASING_MAP[key]
    return linear


# ---------------------------------------------------------------------------
# Tween
# ---------------------------------------------------------------------------

class Tween:
    """Interpolates values over time using easing curves."""

    def __init__(
        self,
        start_value: Any,
        target_value: Any,
        duration: float = 1.0,
        ease: Union[str, Callable[[float], float]] = "linear",
        on_update: Optional[Callable[[Any], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
        loop: bool = False,
    ):
        self.start_value = self._extract_value(start_value)
        self.target_value = self._extract_value(target_value)
        self.duration = max(0.0001, float(duration))
        self.ease_func = get_easing(ease)
        self.on_update_callback = on_update
        self.on_complete_callback = on_complete
        self.loop = bool(loop)

        self.elapsed: float = 0.0
        self.cancelled: bool = False
        self.completed: bool = False

    @staticmethod
    def _extract_value(val: Any) -> Any:
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, (tuple, list)):
            return tuple(float(x) for x in val)
        if hasattr(val, "x") and hasattr(val, "y") and hasattr(val, "z"):
            return (float(val.x), float(val.y), float(val.z))
        if hasattr(val, "r") and hasattr(val, "g") and hasattr(val, "b"):
            a = float(val.a) if hasattr(val, "a") else 1.0
            return (float(val.r), float(val.g), float(val.b), a)
        return val

    def update(self, dt: float) -> bool:
        """Update tween state. Returns True if tween has finished, False otherwise."""
        if self.cancelled or self.completed:
            return True

        self.elapsed += max(0.0, float(dt))
        progress = min(max(self.elapsed / self.duration, 0.0), 1.0)
        eased_t = self.ease_func(progress)

        # Interpolate
        if isinstance(self.start_value, (int, float)) and isinstance(self.target_value, (int, float)):
            current = self.start_value + (self.target_value - self.start_value) * eased_t
        elif isinstance(self.start_value, tuple) and isinstance(self.target_value, tuple):
            current = tuple(
                s + (t - s) * eased_t
                for s, t in zip(self.start_value, self.target_value)
            )
        else:
            current = self.target_value if progress >= 1.0 else self.start_value

        if self.on_update_callback is not None:
            self.on_update_callback(current)

        if self.elapsed >= self.duration:
            if self.on_complete_callback is not None:
                self.on_complete_callback()
            if self.loop:
                self.elapsed = self.elapsed % self.duration
                return False
            else:
                self.completed = True
                return True

        return False

    def cancel(self) -> None:
        """Cancel the tween early."""
        self.cancelled = True
        self.completed = True

    def on_complete(self, callback: Callable[[], None]) -> "Tween":
        """Register completion callback. Returns self for fluent chaining."""
        self.on_complete_callback = callback
        return self


# ---------------------------------------------------------------------------
# TweenManager
# ---------------------------------------------------------------------------

class TweenManager:
    """Manages active tweens and advances them each frame."""

    _default_instance: Optional["TweenManager"] = None

    def __init__(self) -> None:
        self._tweens: List[Tween] = []

    @classmethod
    def default(cls) -> "TweenManager":
        """Return global default TweenManager instance."""
        if cls._default_instance is None:
            cls._default_instance = TweenManager()
        return cls._default_instance

    def add(self, tween: Tween) -> Tween:
        """Register a tween to be updated each frame."""
        self._tweens.append(tween)
        return tween

    def cancel(self, tween: Tween) -> None:
        """Cancel a specific tween and remove it."""
        tween.cancel()
        if tween in self._tweens:
            self._tweens.remove(tween)

    def clear(self) -> None:
        """Cancel and remove all active tweens."""
        for t in self._tweens:
            t.cancel()
        self._tweens.clear()

    def update(self, dt: float) -> None:
        """Advance all active tweens by dt seconds."""
        active: List[Tween] = []
        for tween in self._tweens:
            finished = tween.update(dt)
            if not finished and not tween.cancelled:
                active.append(tween)
        self._tweens = active

    @property
    def count(self) -> int:
        """Number of currently active tweens."""
        return len(self._tweens)


# ---------------------------------------------------------------------------
# Entity and Model Animation Extensions
# ---------------------------------------------------------------------------

def _extract_3vec(val: Any) -> Tuple[float, float, float]:
    if isinstance(val, (int, float)):
        return (float(val), float(val), float(val))
    if isinstance(val, (tuple, list)):
        return (float(val[0]), float(val[1]), float(val[2]))
    if hasattr(val, "x") and hasattr(val, "y") and hasattr(val, "z"):
        return (float(val.x), float(val.y), float(val.z))
    raise ValueError(f"Cannot convert {val} to 3-component vector")


def entity_animate_position(
    self: Any,
    target: Any,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
) -> Tween:
    """Animate position smoothly towards target (x, y, z)."""
    curr = self.transform.position
    start_pos = (float(curr.x), float(curr.y), float(curr.z))
    target_pos = _extract_3vec(target)

    def update_pos(val: Tuple[float, float, float]) -> None:
        self.transform.set_position(val[0], val[1], val[2])

    tween = Tween(
        start_value=start_pos,
        target_value=target_pos,
        duration=duration,
        ease=ease,
        on_update=update_pos,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


def entity_animate_rotation(
    self: Any,
    target: Any,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
) -> Tween:
    """Animate Euler angles rotation smoothly towards target (rx, ry, rz)."""
    curr = self.transform.rotation
    start_rot = (float(curr.x), float(curr.y), float(curr.z))
    target_rot = _extract_3vec(target)

    def update_rot(val: Tuple[float, float, float]) -> None:
        self.transform.set_rotation(val[0], val[1], val[2])

    tween = Tween(
        start_value=start_rot,
        target_value=target_rot,
        duration=duration,
        ease=ease,
        on_update=update_rot,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


def entity_animate_rotation_y(
    self: Any,
    degrees: float,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
    relative: bool = True,
) -> Tween:
    """Animate Y-axis rotation by or to specified degrees."""
    curr = self.transform.rotation
    rx = float(curr.x)
    ry = float(curr.y)
    rz = float(curr.z)
    target_ry = (ry + float(degrees)) if relative else float(degrees)

    def update_rot_y(val: float) -> None:
        self.transform.set_rotation(rx, val, rz)

    tween = Tween(
        start_value=ry,
        target_value=target_ry,
        duration=duration,
        ease=ease,
        on_update=update_rot_y,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


def entity_animate_scale(
    self: Any,
    target: Any,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
) -> Tween:
    """Animate 3D scale smoothly towards target."""
    curr = self.transform.scale
    start_scale = (float(curr.x), float(curr.y), float(curr.z))
    target_scale = _extract_3vec(target)

    def update_scale(val: Tuple[float, float, float]) -> None:
        self.transform.set_scale(val[0], val[1], val[2])

    tween = Tween(
        start_value=start_scale,
        target_value=target_scale,
        duration=duration,
        ease=ease,
        on_update=update_scale,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


# Model equivalents
def model_animate_position(
    self: Any,
    target: Any,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
) -> Tween:
    curr = self.transform.position
    start_pos = (float(curr.x), float(curr.y), float(curr.z))
    target_pos = _extract_3vec(target)

    def update_pos(val: Tuple[float, float, float]) -> None:
        self.set_position(val[0], val[1], val[2])

    tween = Tween(
        start_value=start_pos,
        target_value=target_pos,
        duration=duration,
        ease=ease,
        on_update=update_pos,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


def model_animate_rotation(
    self: Any,
    target: Any,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
) -> Tween:
    curr = self.transform.rotation
    start_rot = (float(curr.x), float(curr.y), float(curr.z))
    target_rot = _extract_3vec(target)

    def update_rot(val: Tuple[float, float, float]) -> None:
        self.set_rotation(val[0], val[1], val[2])

    tween = Tween(
        start_value=start_rot,
        target_value=target_rot,
        duration=duration,
        ease=ease,
        on_update=update_rot,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


def model_animate_rotation_y(
    self: Any,
    degrees: float,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
    relative: bool = True,
) -> Tween:
    curr = self.transform.rotation
    rx = float(curr.x)
    ry = float(curr.y)
    rz = float(curr.z)
    target_ry = (ry + float(degrees)) if relative else float(degrees)

    def update_rot_y(val: float) -> None:
        self.set_rotation(rx, val, rz)

    tween = Tween(
        start_value=ry,
        target_value=target_ry,
        duration=duration,
        ease=ease,
        on_update=update_rot_y,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


def model_animate_scale(
    self: Any,
    target: Any,
    duration: float = 1.0,
    ease: Union[str, Callable[[float], float]] = "linear",
    on_complete: Optional[Callable[[], None]] = None,
    loop: bool = False,
) -> Tween:
    curr = self.transform.scale
    start_scale = (float(curr.x), float(curr.y), float(curr.z))
    target_scale = _extract_3vec(target)

    def update_scale(val: Tuple[float, float, float]) -> None:
        self.set_scale(val[0], val[1], val[2])

    tween = Tween(
        start_value=start_scale,
        target_value=target_scale,
        duration=duration,
        ease=ease,
        on_update=update_scale,
        on_complete=on_complete,
        loop=loop,
    )
    return TweenManager.default().add(tween)


def patch_entity_and_model():
    """Attach animation helper methods to Entity and Model classes."""
    _core.Entity.animate_position = entity_animate_position
    _core.Entity.animate_rotation = entity_animate_rotation
    _core.Entity.animate_rotation_y = entity_animate_rotation_y
    _core.Entity.animate_scale = entity_animate_scale

    _core.Model.animate_position = model_animate_position
    _core.Model.animate_rotation = model_animate_rotation
    _core.Model.animate_rotation_y = model_animate_rotation_y
    _core.Model.animate_scale = model_animate_scale
