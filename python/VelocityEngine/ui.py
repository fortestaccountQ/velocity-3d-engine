"""2D UI overlay and HUD rendering commands for VelocityEngine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional, Any, List, Union
from .color import Color, WHITE


@dataclass
class UITextCommand:
    text: str
    pos: Tuple[float, float]
    size: float
    color: Color


@dataclass
class UIRectCommand:
    x: float
    y: float
    w: float
    h: float
    color: Color


@dataclass
class UICrosshairCommand:
    size: float
    color: Color


class UIOverlay:
    """High-level 2D UI overlay facade for drawing text, shapes, crosshairs, and stats."""

    def __init__(self, app: Optional[Any] = None) -> None:
        self._app = app
        self._commands: List[Union[UITextCommand, UIRectCommand, UICrosshairCommand]] = []
        self._stats_visible: bool = True

    @property
    def commands(self) -> List[Union[UITextCommand, UIRectCommand, UICrosshairCommand]]:
        """List of active UI draw commands."""
        return self._commands

    @property
    def stats_visible(self) -> bool:
        """True if stats/HUD display is enabled."""
        return self._stats_visible

    def draw_text(
        self,
        text: str,
        pos: Tuple[float, float],
        size: float = 16.0,
        color: Any = WHITE,
    ) -> None:
        """Draw a text string at 2D screen coordinate (x, y)."""
        col = Color(color) if color is not None else WHITE
        cmd = UITextCommand(
            text=str(text),
            pos=(float(pos[0]), float(pos[1])),
            size=float(size),
            color=col,
        )
        self._commands.append(cmd)

    def draw_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        color: Any = WHITE,
    ) -> None:
        """Draw a 2D colored rectangle in screen space."""
        col = Color(color) if color is not None else WHITE
        cmd = UIRectCommand(
            x=float(x),
            y=float(y),
            w=float(w),
            h=float(h),
            color=col,
        )
        self._commands.append(cmd)

    def draw_crosshair(
        self,
        size: float = 10.0,
        color: Any = WHITE,
    ) -> None:
        """Draw a central aiming crosshair of specified size."""
        col = Color(color) if color is not None else WHITE
        cmd = UICrosshairCommand(
            size=float(size),
            color=col,
        )
        self._commands.append(cmd)

    def show_stats(self, show: bool = True) -> None:
        """Enable or disable performance statistics / HUD overlay."""
        self._stats_visible = bool(show)
        if self._app is not None and hasattr(self._app, "show_hud"):
            self._app.show_hud = bool(show)

    def clear(self) -> None:
        """Clear all buffered 2D UI commands."""
        self._commands.clear()
