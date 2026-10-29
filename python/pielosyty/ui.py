"""2D UI overlay and HUD rendering commands for Pielosyty 3D Engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Optional, Any, List, Union, Sequence
from .color import Color, as_color, WHITE

# Core native module import
try:
    from . import _pielosyty_core as _core
except ImportError:
    try:
        from . import _VelocityEngine_core as _core
    except ImportError:
        try:
            import _pielosyty_core as _core
        except ImportError:
            import _VelocityEngine_core as _core

UICommandType = getattr(_core, "UICommandType", None)
UICommand = getattr(_core, "UICommand", None)

if UICommandType is None:
    class UICommandType:  # type: ignore
        Text = 0
        Rect = 1
        Line = 2
        Crosshair = 3

if UICommand is None:
    class UICommand:  # type: ignore
        def __init__(self):
            self.type = UICommandType.Rect
            self.text = ""
            self.pos = (0.0, 0.0)
            self.size = (0.0, 0.0)
            self.color = (1.0, 1.0, 1.0, 1.0)
            self.thickness = 1.0


@dataclass
class UITextCommand:
    """2D screen-space text drawing command."""
    text: str
    pos: Tuple[float, float]
    size: float = 16.0
    color: Color = WHITE

    def to_native(self) -> UICommand:
        cmd = UICommand()
        cmd.type = UICommandType.Text
        cmd.text = str(self.text)
        cmd.pos = (float(self.pos[0]), float(self.pos[1]))
        cmd.size = (float(self.size), float(self.size))
        cmd.color = as_color(self.color)
        cmd.thickness = 1.0
        return cmd


@dataclass
class UIRectCommand:
    """2D screen-space rectangle drawing command."""
    x: float
    y: float
    w: float
    h: float
    color: Color = WHITE
    thickness: float = 1.0

    def to_native(self) -> UICommand:
        cmd = UICommand()
        cmd.type = UICommandType.Rect
        cmd.pos = (float(self.x), float(self.y))
        cmd.size = (float(self.w), float(self.h))
        cmd.color = as_color(self.color)
        cmd.thickness = float(self.thickness)
        return cmd


@dataclass
class UICrosshairCommand:
    """2D screen-space central aiming crosshair command."""
    size: float = 10.0
    color: Color = WHITE
    pos: Tuple[float, float] = (0.0, 0.0)
    thickness: float = 1.0

    def to_native(self) -> UICommand:
        cmd = UICommand()
        cmd.type = UICommandType.Crosshair
        cmd.pos = (float(self.pos[0]), float(self.pos[1]))
        cmd.size = (float(self.size), float(self.size))
        cmd.color = as_color(self.color)
        cmd.thickness = float(self.thickness)
        return cmd


@dataclass
class UILineCommand:
    """2D screen-space line segment drawing command."""
    p0: Tuple[float, float]
    p1: Tuple[float, float]
    color: Color = WHITE
    thickness: float = 1.0

    def to_native(self) -> UICommand:
        cmd = UICommand()
        cmd.type = UICommandType.Line
        cmd.pos = (float(self.p0[0]), float(self.p0[1]))
        cmd.size = (float(self.p1[0] - self.p0[0]), float(self.p1[1] - self.p0[1]))
        cmd.color = as_color(self.color)
        cmd.thickness = float(self.thickness)
        return cmd


class UIOverlay:
    """High-level 2D UI overlay facade for drawing text, shapes, crosshairs, and stats."""

    def __init__(self, app: Optional[Any] = None) -> None:
        self._app = app
        self._commands: List[Union[UITextCommand, UIRectCommand, UICrosshairCommand, UILineCommand]] = []
        self._stats_visible: bool = True

    @property
    def commands(self) -> List[Union[UITextCommand, UIRectCommand, UICrosshairCommand, UILineCommand]]:
        """List of active UI draw commands."""
        return self._commands

    @property
    def stats_visible(self) -> bool:
        """True if stats/HUD display is enabled."""
        return self._stats_visible

    def draw_text(
        self,
        text: str,
        *args: Any,
        pos: Optional[Tuple[float, float]] = None,
        size: float = 16.0,
        color: Any = WHITE,
        **kwargs: Any,
    ) -> None:
        """Draw a text string at 2D screen coordinate (x, y).

        Supported signatures:
            draw_text("Hello", 100, 100)
            draw_text("Hello", 100, 100, size=24, color=RED)
            draw_text("Hello", 100, 100, 24, RED)
            draw_text("Hello", (100, 100))
            draw_text("Hello", (100, 100), 24, RED)
            draw_text("Hello", pos=(100, 100), size=24, color=RED)
        """
        if "sz" in kwargs:
            size = float(kwargs["sz"])
        if "col" in kwargs:
            color = kwargs["col"]

        final_pos: Tuple[float, float] = (0.0, 0.0)

        if pos is not None:
            final_pos = (float(pos[0]), float(pos[1]))
            if len(args) >= 1:
                size = float(args[0])
            if len(args) >= 2:
                color = args[1]
        elif len(args) >= 2 and isinstance(args[0], (int, float)) and isinstance(args[1], (int, float)):
            final_pos = (float(args[0]), float(args[1]))
            if len(args) >= 3:
                size = float(args[2])
            if len(args) >= 4:
                color = args[3]
        elif len(args) >= 1 and (isinstance(args[0], (tuple, list)) or hasattr(args[0], "__getitem__")):
            final_pos = (float(args[0][0]), float(args[0][1]))
            if len(args) >= 2:
                size = float(args[1])
            if len(args) >= 3:
                color = args[2]
        else:
            raise TypeError(f"Invalid arguments for draw_text: text={text!r}, args={args!r}, pos={pos!r}")

        col = as_color(color) if color is not None else WHITE
        cmd = UITextCommand(
            text=str(text),
            pos=final_pos,
            size=float(size),
            color=col,
        )
        self._commands.append(cmd)

    def draw_rect(
        self,
        *args: Any,
        x: Optional[float] = None,
        y: Optional[float] = None,
        w: Optional[float] = None,
        h: Optional[float] = None,
        color: Any = WHITE,
        thickness: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Draw a 2D colored rectangle in screen space.

        Supported signatures:
            draw_rect(x, y, w, h, color=WHITE, thickness=1.0)
            draw_rect((x, y, w, h), color=WHITE)
        """
        if "col" in kwargs:
            color = kwargs["col"]
        if "thick" in kwargs:
            thickness = float(kwargs["thick"])

        rx, ry, rw, rh = 0.0, 0.0, 0.0, 0.0
        if len(args) >= 4 and isinstance(args[0], (int, float)):
            rx, ry, rw, rh = float(args[0]), float(args[1]), float(args[2]), float(args[3])
            if len(args) >= 5:
                color = args[4]
            if len(args) >= 6:
                thickness = float(args[5])
        elif len(args) == 1 and (isinstance(args[0], (tuple, list)) or hasattr(args[0], "__getitem__")) and len(args[0]) >= 4:
            rx, ry, rw, rh = float(args[0][0]), float(args[0][1]), float(args[0][2]), float(args[0][3])
            if len(args) >= 2:
                color = args[1]
            if len(args) >= 3:
                thickness = float(args[2])
        elif x is not None and y is not None and w is not None and h is not None:
            rx, ry, rw, rh = float(x), float(y), float(w), float(h)
        else:
            raise TypeError(f"Invalid arguments for draw_rect: args={args!r}")

        col = as_color(color) if color is not None else WHITE
        cmd = UIRectCommand(
            x=rx,
            y=ry,
            w=rw,
            h=rh,
            color=col,
            thickness=float(thickness),
        )
        self._commands.append(cmd)

    def draw_crosshair(
        self,
        size: float = 10.0,
        color: Any = WHITE,
        pos: Tuple[float, float] = (0.0, 0.0),
        thickness: float = 1.0,
        **kwargs: Any,
    ) -> None:
        """Draw an aiming crosshair of specified size."""
        if isinstance(color, (tuple, list)) and len(color) == 2 and not isinstance(color, Color):
            pos, color = color, WHITE
        if "thick" in kwargs:
            thickness = float(kwargs["thick"])
        if "col" in kwargs:
            color = kwargs["col"]
        if "pos" in kwargs and kwargs["pos"] is not None:
            pos = kwargs["pos"]

        col = as_color(color) if color is not None else WHITE
        cmd = UICrosshairCommand(
            size=float(size),
            color=col,
            pos=(float(pos[0]), float(pos[1])),
            thickness=float(thickness),
        )
        self._commands.append(cmd)

    def draw_line(
        self,
        *args: Any,
        thickness: float = 1.0,
        color: Any = WHITE,
        **kwargs: Any,
    ) -> None:
        """Draw a 2D line segment between two points.

        Supported call signatures:
            draw_line((x0, y0), (x1, y1), thickness=1.0, color=WHITE)
            draw_line(x0, y0, x1, y1, color=WHITE, thickness=1.0)
            draw_line((x0, y0), (x1, y1), color)
        """
        if "thick" in kwargs:
            thickness = float(kwargs["thick"])
        if "col" in kwargs:
            color = kwargs["col"]

        p0 = (0.0, 0.0)
        p1 = (0.0, 0.0)

        if len(args) >= 4 and isinstance(args[0], (int, float)) and isinstance(args[1], (int, float)):
            p0 = (float(args[0]), float(args[1]))
            p1 = (float(args[2]), float(args[3]))
            if len(args) >= 5:
                color = args[4]
            if len(args) >= 6:
                thickness = float(args[5])
        elif len(args) >= 2:
            p0 = (float(args[0][0]), float(args[0][1]))
            p1 = (float(args[1][0]), float(args[1][1]))
            if len(args) >= 3:
                if isinstance(args[2], (int, float)):
                    thickness = float(args[2])
                    if len(args) >= 4:
                        color = args[3]
                else:
                    color = args[2]
                    if len(args) >= 4:
                        thickness = float(args[3])
        elif len(args) == 1 and isinstance(args[0], (tuple, list)) and len(args[0]) >= 4:
            p0 = (float(args[0][0]), float(args[0][1]))
            p1 = (float(args[0][2]), float(args[0][3]))
        else:
            raise TypeError(f"Invalid arguments for draw_line: {args}")

        col = as_color(color) if color is not None else WHITE
        cmd = UILineCommand(
            p0=p0,
            p1=p1,
            color=col,
            thickness=float(thickness),
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

    def flush(self, app: Optional[Any] = None) -> List[UICommand]:
        """Convert all buffered UI commands to native C++ UICommand objects and submit to app."""
        target = app if app is not None else self._app
        if not self._commands:
            return []

        native_cmds: List[UICommand] = []
        for cmd in self._commands:
            if hasattr(cmd, "to_native"):
                native_cmds.append(cmd.to_native())
            elif isinstance(cmd, UICommand):
                native_cmds.append(cmd)

        if target is not None:
            if hasattr(target, "submit_ui_commands"):
                target.submit_ui_commands(native_cmds)
            elif hasattr(target, "_core") and hasattr(target._core, "submit_ui_commands"):
                target._core.submit_ui_commands(native_cmds)

        self._commands.clear()
        return native_cmds


__all__ = [
    "UICommandType",
    "UICommand",
    "UITextCommand",
    "UIRectCommand",
    "UICrosshairCommand",
    "UILineCommand",
    "UIOverlay",
]
