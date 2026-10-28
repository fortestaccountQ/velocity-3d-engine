"""High-level Python wrapper around the native _VelocityEngine_core module."""

from __future__ import annotations

from typing import Callable, Sequence, Optional, Any, List, Union

try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core

from .color import Color, as_color
from .tween import TweenManager
from .ui import UIOverlay


class App:
    """High-level VelocityEngine Application facade."""

    def __init__(
        self,
        title: str = "VelocityEngine v0.2-beta",
        width: int = 1280,
        height: int = 720,
        mode: Optional[Any] = None,
        clear_color: Optional[Union[Sequence[float], str, Color]] = None,
        target_fps: int = 0,
        show_crosshair: bool = True,
    ) -> None:
        """Create and configure a new engine window application."""
        self._core = _core.EngineApp(title, width, height)
        self._update_callback: Optional[Callable[[float], None]] = None

        # Camera & Subsystem extensions
        self._camera_controller: Optional[Any] = None
        self._custom_camera: Optional[Any] = None
        self._ui = UIOverlay(app=self)
        self._tweens = TweenManager.default()

        # Raycasting event listeners
        self._click_callbacks: List[Callable] = []
        self._hover_callbacks: List[Callable] = []
        self._prev_mouse_down = [False] * 8
        self._fog: Optional[Any] = None

        # Frame limiter & crosshair config
        if target_fps != 0:
            self._core.target_fps = int(target_fps)
        if not show_crosshair:
            self._core.show_crosshair = bool(show_crosshair)

        # Hook internal frame update callback
        self._core.set_update_callback(self._on_internal_frame)

        if mode is not None:
            self.mode = mode

        if clear_color is not None:
            col = as_color(clear_color)
            self._core.set_clear_color(col.r, col.g, col.b, col.a)

    def _on_internal_frame(self, dt: float) -> None:
        """Internal frame callback driving tweens, active camera controllers, and raycasting."""
        # 1. Update tweens
        self._tweens.update(dt)

        # 2. Update active camera controller
        if self._camera_controller is not None:
            ctrl = self._camera_controller
            core_cam = self._custom_camera or self._core.camera
            if hasattr(ctrl, "update"):
                try:
                    # Preferred: update(camera, input_mgr, dt, width, height)
                    ctrl.update(core_cam, self.input, dt, self.width, self.height)
                except TypeError:
                    try:
                        # Contract fallback: update(dt, input_mgr, width, height)
                        ctrl.update(dt, self.input, self.width, self.height)
                    except TypeError:
                        try:
                            ctrl.update(dt)
                        except Exception:
                            pass

        # 3. Process event-driven screen raycasting
        self._process_raycast_events()

        # 4. User update callback
        if self._update_callback is not None:
            self._update_callback(dt)

    def _process_raycast_events(self) -> None:
        """Raycast against scene under mouse cursor and dispatch hover/click events."""
        if not self._click_callbacks and not self._hover_callbacks:
            return

        core_cam = self._custom_camera or self._core.camera
        if not hasattr(core_cam, "screen_to_ray"):
            from .camera_utils import patch_camera
            patch_camera()

        mx = self.input.mouse_x
        my = self.input.mouse_y
        w = max(1, self.width)
        h = max(1, self.height)

        ray = None
        hit = None

        def get_hit():
            nonlocal ray, hit
            if hit is None:
                ray = core_cam.screen_to_ray(mx, my, w, h)
                hit = self.scene.raycast(ray)
            return hit

        # Hover callbacks
        if self._hover_callbacks:
            ht = get_hit()
            for cb in self._hover_callbacks:
                try:
                    cb(ht)
                except TypeError:
                    try:
                        cb(ht.entity if ht.hit else None)
                    except Exception:
                        pass

        # Click callbacks (detect transition from up to down on mouse button 0)
        is_down = self.input.is_mouse_down(0)
        was_down = self._prev_mouse_down[0]
        self._prev_mouse_down[0] = is_down

        if is_down and not was_down:
            ht = get_hit()
            for cb in self._click_callbacks:
                try:
                    cb(ht)
                except TypeError:
                    try:
                        cb(ht.entity if ht.hit else None)
                    except Exception:
                        pass

    def init(self, title: str = "VelocityEngine v0.2-beta", width: int = 1280, height: int = 720) -> None:
        """Reinitialize window configuration parameters."""
        self._core.init(title, width, height)

    @property
    def scene(self) -> _core.Scene:
        """Active 3D scene containing entities and lights."""
        return self._core.scene

    @property
    def camera(self) -> Any:
        """Active scene camera or active camera controller."""
        if self._camera_controller is not None:
            return self._camera_controller
        if self._custom_camera is not None:
            return self._custom_camera
        return self._core.camera

    @camera.setter
    def camera(self, value: Any) -> None:
        if isinstance(value, _core.Camera):
            self._custom_camera = value
            self._camera_controller = None
        elif hasattr(value, "update"):
            self._camera_controller = value
            if hasattr(value, "camera") and getattr(value, "camera") is None:
                value.camera = self._core.camera
        else:
            self._camera_controller = value

    @property
    def camera_controller(self) -> Optional[Any]:
        """Active camera navigation controller (e.g. OrbitController, FollowCamera)."""
        return self._camera_controller

    @camera_controller.setter
    def camera_controller(self, value: Optional[Any]) -> None:
        self.camera = value

    @property
    def ui(self) -> UIOverlay:
        """2D UI overlay for drawing text, shapes, crosshairs, and stats."""
        return self._ui

    @property
    def tweens(self) -> TweenManager:
        """Active TweenManager instance."""
        return self._tweens

    @property
    def input(self) -> _core.InputManager:
        """Input manager for keyboard and mouse query."""
        return self._core.input

    @property
    def audio(self) -> Any:
        """AudioManager for 3D spatial and procedural audio."""
        return self._core.audio

    @property
    def editor(self) -> _core.EditorManager:
        """Visual scene editor manager and gizmos."""
        return self._core.editor

    @property
    def mode(self) -> _core.Mode:
        """Current engine execution mode (Mode.GAME or Mode.EDITOR)."""
        return self._core.mode

    @mode.setter
    def mode(self, value: _core.Mode) -> None:
        self._core.mode = value

    def set_mode(self, mode: _core.Mode) -> None:
        """Set engine execution mode (Mode.GAME or Mode.EDITOR)."""
        self._core.set_mode(mode)

    def get_mode(self) -> _core.Mode:
        """Get current engine execution mode."""
        return self._core.get_mode()

    def toggle_mode(self) -> None:
        """Toggle between Mode.GAME and Mode.EDITOR."""
        self._core.toggle_mode()

    def load_texture(self, filepath: str) -> _core.Texture:
        """Load an image file (PNG/JPG/BMP) into a GPU Texture."""
        return self._core.load_texture(filepath)

    def create_checkerboard_texture(
        self, width: int = 64, height: int = 64, tile_size: int = 8
    ) -> _core.Texture:
        """Generate a procedural checkerboard GPU texture."""
        return self._core.create_checkerboard_texture(width, height, tile_size)

    def set_update_callback(self, callback: Optional[Callable[[float], None]]) -> None:
        """Register per-frame update callback accepting dt (delta time in seconds)."""
        self._update_callback = callback

    def on_update(self, func: Callable[[float], None]) -> Callable[[float], None]:
        """Decorator for registering frame update callbacks."""
        self.set_update_callback(func)
        return func

    def on_click(self, func: Optional[Callable] = None) -> Callable:
        """Decorator for registering mouse click raycast hit callbacks."""
        def decorator(fn: Callable) -> Callable:
            self._click_callbacks.append(fn)
            return fn
        if func is not None:
            return decorator(func)
        return decorator

    def on_hover(self, func: Optional[Callable] = None) -> Callable:
        """Decorator for registering mouse hover raycast hit callbacks."""
        def decorator(fn: Callable) -> Callable:
            self._hover_callbacks.append(fn)
            return fn
        if func is not None:
            return decorator(func)
        return decorator

    def run(self) -> None:
        """Launch the Sokol native rendering loop (blocks until window is closed)."""
        try:
            self._core.run()
        finally:
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

    def set_title(self, title: str) -> None:
        self._core.set_title(str(title))

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
    def show_hud(self) -> bool:
        return self._core.show_hud

    @show_hud.setter
    def show_hud(self, value: bool) -> None:
        self._core.show_hud = bool(value)

    @property
    def show_crosshair(self) -> bool:
        """Whether the HUD center crosshair is visible."""
        return self._core.show_crosshair

    @show_crosshair.setter
    def show_crosshair(self, value: bool) -> None:
        self._core.show_crosshair = bool(value)

    def set_show_crosshair(self, show: bool) -> None:
        """Set whether the HUD center crosshair is visible."""
        self._core.set_show_crosshair(bool(show))

    @property
    def hud_score(self) -> int:
        return self._core.hud_score

    @hud_score.setter
    def hud_score(self, value: int) -> None:
        self._core.hud_score = int(value)

    def set_hud_score(self, score: int) -> None:
        """Set HUD score value."""
        self._core.hud_score = int(score)

    @property
    def hud_title(self) -> str:
        return self._core.hud_title

    @hud_title.setter
    def hud_title(self, value: str) -> None:
        self._core.hud_title = str(value)

    def set_hud_title(self, title: str) -> None:
        """Set HUD custom title tag."""
        self._core.hud_title = str(title)

    @property
    def hud_hint(self) -> str:
        return self._core.hud_hint

    @hud_hint.setter
    def hud_hint(self, value: str) -> None:
        self._core.hud_hint = str(value)

    def set_hud_hint(self, hint: str) -> None:
        """Set HUD bottom hint string."""
        self._core.hud_hint = str(hint)

    @property
    def target_fps(self) -> int:
        """Target frames per second limiter (0 for uncapped)."""
        return self._core.target_fps

    @target_fps.setter
    def target_fps(self, value: int) -> None:
        self._core.target_fps = int(value)

    def set_target_fps(self, fps: int) -> None:
        """Set target frames per second limiter (0 for uncapped)."""
        self._core.set_target_fps(int(fps))

    @property
    def debug_hitboxes(self) -> bool:
        return self._core.debug_hitboxes

    @debug_hitboxes.setter
    def debug_hitboxes(self, value: bool) -> None:
        self._core.debug_hitboxes = bool(value)

    @property
    def show_debug_hitboxes(self) -> bool:
        return self._core.debug_hitboxes

    @show_debug_hitboxes.setter
    def show_debug_hitboxes(self, value: bool) -> None:
        self._core.debug_hitboxes = bool(value)

    def toggle_debug_hitboxes(self) -> None:
        self._core.toggle_debug_hitboxes()

    @property
    def fog(self) -> Optional[Any]:
        """Atmospheric depth fog (Fog or FogExp2)."""
        return self._fog

    @fog.setter
    def fog(self, value: Optional[Any]) -> None:
        self._fog = value
        if value is None:
            self._core.clear_fog()
            return

        from .color import as_color
        from .fog import Fog, FogExp2

        col = as_color(value.color)
        c_tuple = (col.r, col.g, col.b)
        if isinstance(value, FogExp2):
            self._core.set_exp2_fog(c_tuple, float(value.density))
        else:
            self._core.set_linear_fog(c_tuple, float(getattr(value, "near", 1.0)), float(getattr(value, "far", 100.0)))

    @property
    def tone_mapping(self) -> bool:
        """ACES Filmic Tone Mapping enable state."""
        return self._core.tone_mapping

    @tone_mapping.setter
    def tone_mapping(self, value: bool) -> None:
        self._core.tone_mapping = bool(value)
