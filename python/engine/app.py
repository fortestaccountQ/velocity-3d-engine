"""High-level Python wrapper around the native _engine_core module."""

from __future__ import annotations

from typing import Callable, Sequence, Optional, Any

try:
    from . import _engine_core
except ImportError:
    import _engine_core


class App:
    """High-level 3D Engine Application facade."""

    def __init__(
        self,
        title: str = "Engine 3D Core",
        width: int = 800,
        height: int = 600,
        clear_color: Optional[Sequence[float]] = None,
    ) -> None:
        """Create and configure a new engine window application."""
        self._core = _engine_core.EngineApp(title, width, height)
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

    @property
    def scene(self) -> _engine_core.Scene:
        """Active 3D scene containing entities and lights."""
        return self._core.scene

    @property
    def camera(self) -> _engine_core.Camera:
        """Active scene camera."""
        return self._core.camera

    @property
    def input(self) -> _engine_core.InputManager:
        """Input manager for keyboard and mouse query."""
        return self._core.input

    def load_texture(self, filepath: str) -> _engine_core.Texture:
        """Load an image file (PNG/JPG/BMP) into a GPU Texture."""
        return self._core.load_texture(filepath)

    def create_checkerboard_texture(
        self, width: int = 64, height: int = 64, tile_size: int = 8
    ) -> _engine_core.Texture:
        """Generate a procedural checkerboard GPU texture."""
        return self._core.create_checkerboard_texture(width, height, tile_size)

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

    def set_mouse_locked(self, locked: bool) -> None:
        """Lock or release mouse cursor (hides and locks cursor to window center)."""
        self._core.set_mouse_locked(bool(locked))

    def is_mouse_locked(self) -> bool:
        """True if the mouse cursor is currently locked/hidden."""
        return self._core.is_mouse_locked()

    @property
    def audio(self) -> Any:
        """AudioManager for 3D spatial and procedural audio."""
        return self._core.audio

    @property
    def show_hud(self) -> bool:
        return self._core.show_hud

    @show_hud.setter
    def show_hud(self, value: bool) -> None:
        self._core.show_hud = bool(value)

    @property
    def hud_score(self) -> int:
        return self._core.hud_score

    @hud_score.setter
    def hud_score(self, value: int) -> None:
        self._core.hud_score = int(value)

    @property
    def debug_hitboxes(self) -> bool:
        return self._core.debug_hitboxes

    @debug_hitboxes.setter
    def debug_hitboxes(self, value: bool) -> None:
        self._core.debug_hitboxes = bool(value)

    def toggle_debug_hitboxes(self) -> None:
        self._core.toggle_debug_hitboxes()

    def set_title(self, title: str) -> None:
        self._core.set_title(str(title))

