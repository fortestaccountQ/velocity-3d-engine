"""High-level Python wrapper around the native _engine_core module."""

from __future__ import annotations

from typing import Callable, Sequence, Optional


try:
    from . import _engine_core
except ImportError:
    import _engine_core


class TransformFacade:
    """Convenience facade for 3D transform properties."""

    def __init__(self, core: _engine_core.EngineApp) -> None:
        self._core = core

    @property
    def rotation_x(self) -> float:
        return self._core.rotation_x

    @rotation_x.setter
    def rotation_x(self, val: float) -> None:
        self._core.rotation_x = float(val)

    @property
    def rotation_y(self) -> float:
        return self._core.rotation_y

    @rotation_y.setter
    def rotation_y(self, val: float) -> None:
        self._core.rotation_y = float(val)

    @property
    def rotation_z(self) -> float:
        return self._core.rotation_z

    @rotation_z.setter
    def rotation_z(self, val: float) -> None:
        self._core.rotation_z = float(val)

    @property
    def position_x(self) -> float:
        return self._core.position_x

    @position_x.setter
    def position_x(self, val: float) -> None:
        self._core.position_x = float(val)

    @property
    def position_y(self) -> float:
        return self._core.position_y

    @position_y.setter
    def position_y(self, val: float) -> None:
        self._core.position_y = float(val)

    @property
    def position_z(self) -> float:
        return self._core.position_z

    @position_z.setter
    def position_z(self, val: float) -> None:
        self._core.position_z = float(val)

    def set_rotation(self, rx: float, ry: float, rz: float = 0.0) -> None:
        self._core.set_rotation(float(rx), float(ry), float(rz))

    def set_position(self, x: float, y: float, z: float) -> None:
        self._core.set_position(float(x), float(y), float(z))

    def set_scale(self, sx: float, sy: float, sz: float) -> None:
        self._core.set_scale(float(sx), float(sy), float(sz))


class App:
    """High-level 3D Engine Application facade."""

    def __init__(
        self,
        title: str = "Engine 3D Core",
        width: int = 800,
        height: int = 600,
        clear_color: Optional[Sequence[float]] = None,
    ) -> None:
        """Create and configure a new engine window application.

        Args:
            title: Window caption.
            width: Window width in pixels.
            height: Window height in pixels.
            clear_color: Optional RGBA sequence (e.g. [0.102, 0.102, 0.141, 1.0]).
        """
        self._core = _engine_core.EngineApp(title, width, height)
        self._transform = TransformFacade(self._core)
        self._update_callback: Optional[Callable[[float], None]] = None

        if clear_color is not None:
            r = float(clear_color[0])
            g = float(clear_color[1])
            b = float(clear_color[2])
            a = float(clear_color[3]) if len(clear_color) > 3 else 1.0
            self._core.set_clear_color(r, g, b, a)

    def init(self, title: str = "Engine 3D Core", width: int = 800, height: int = 600) -> None:
        """Reinitialize window configuration parameters."""
        self._core.init(title, width, height)

    def set_update_callback(self, callback: Optional[Callable[[float], None]]) -> None:
        """Register per-frame update callback accepting dt (delta time in seconds)."""
        self._update_callback = callback
        self._core.set_update_callback(callback)

    def on_update(self, func: Callable[[float], None]) -> Callable[[float], None]:
        """Decorator for registering frame update callbacks."""
        self.set_update_callback(func)
        return func

    def run(self) -> None:
        """Launch the Sokol native rendering loop (blocks until window is closed)."""
        try:
            self._core.run()
        finally:
            # Clean up callback reference under active Python GIL to prevent cyclic leaks
            self._core.set_update_callback(None)
            self._update_callback = None

    def close(self) -> None:
        """Request window exit and cleanup."""
        self._core.close()

    # 3D Transform direct access
    @property
    def transform(self) -> TransformFacade:
        return self._transform

    @property
    def rotation_x(self) -> float:
        return self._core.rotation_x

    @rotation_x.setter
    def rotation_x(self, val: float) -> None:
        self._core.rotation_x = float(val)

    @property
    def rotation_y(self) -> float:
        return self._core.rotation_y

    @rotation_y.setter
    def rotation_y(self, val: float) -> None:
        self._core.rotation_y = float(val)

    @property
    def rotation_z(self) -> float:
        return self._core.rotation_z

    @rotation_z.setter
    def rotation_z(self, val: float) -> None:
        self._core.rotation_z = float(val)

    @property
    def position_x(self) -> float:
        return self._core.position_x

    @position_x.setter
    def position_x(self, val: float) -> None:
        self._core.position_x = float(val)

    @property
    def position_y(self) -> float:
        return self._core.position_y

    @position_y.setter
    def position_y(self, val: float) -> None:
        self._core.position_y = float(val)

    @property
    def position_z(self) -> float:
        return self._core.position_z

    @position_z.setter
    def position_z(self, val: float) -> None:
        self._core.position_z = float(val)

    def set_rotation(self, rx: float, ry: float, rz: float = 0.0) -> None:
        self._core.set_rotation(float(rx), float(ry), float(rz))

    def set_position(self, x: float, y: float, z: float) -> None:
        self._core.set_position(float(x), float(y), float(z))

    def set_scale(self, sx: float, sy: float, sz: float) -> None:
        self._core.set_scale(float(sx), float(sy), float(sz))

    # Window properties
    @property
    def is_running(self) -> bool:
        """True if the engine loop is currently executing."""
        return self._core.is_running()

    @property
    def width(self) -> int:
        return self._core.width

    @property
    def height(self) -> int:
        return self._core.height

    @property
    def title(self) -> str:
        return self._core.title

    def set_clear_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
        self._core.set_clear_color(float(r), float(g), float(b), float(a))

    def get_clear_color(self) -> list[float]:
        return list(self._core.get_clear_color())
