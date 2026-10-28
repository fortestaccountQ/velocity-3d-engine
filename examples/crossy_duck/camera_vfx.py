"""Isometric Follow Camera and Viral 2D HUD Overlay for Crossy Duck.

Implements:
  - Isometric follow camera with smooth exponential damping / lerp:
      Position: (player.x - 7.0, 11.0, player.z - 8.5)
      Target:   (player.x, 0.5, player.z + 1.5)
  - 2D HUD Overlay:
      * Top-left slate card: "🐍 PYTHON 3.13.14 (64-bit) | Sokol GFX D3D11 | 500+ FPS"
      * Big arcade score top-center: "SCORE: <score>   HIGH: <high>"
      * Game over banner with "[R] Press R to Restart" and death reason
"""

from __future__ import annotations

import sys
from typing import Optional, Any, Tuple

from contracts.crossy_contracts import PlayerStatus

try:
    from VelocityEngine.color import Color
except ImportError:
    Color = lambda *args, **kwargs: args[0] if args else (1.0, 1.0, 1.0, 1.0)


class IsometricCamera:
    """Smooth-damping isometric follow camera tracking the player character."""

    def __init__(
        self,
        camera: Optional[Any] = None,
        app: Optional[Any] = None,
        damping: float = 8.5,
    ) -> None:
        self.camera = camera or (getattr(app, "camera", None) if app else None)
        self.app = app
        self.damping: float = float(damping)

        # Fixed Isometric Offsets from Contract
        self.offset_x: float = -7.0
        self.offset_y: float = 11.0
        self.offset_z: float = -8.5

        self.target_offset_x: float = 0.0
        self.target_offset_y: float = 0.5
        self.target_offset_z: float = 1.5

        # Current Camera Coordinates
        self.pos_x: float = self.offset_x
        self.pos_y: float = self.offset_y
        self.pos_z: float = self.offset_z

        self.tgt_x: float = self.target_offset_x
        self.tgt_y: float = self.target_offset_y
        self.tgt_z: float = self.target_offset_z

    def get_desired_position(self, px: float, py: float, pz: float) -> Tuple[float, float, float]:
        """Compute ideal camera position in world space given player coords."""
        return (px + self.offset_x, self.offset_y, pz + self.offset_z)

    def get_desired_target(self, px: float, py: float, pz: float) -> Tuple[float, float, float]:
        """Compute ideal camera look-at target in world space given player coords."""
        clamped_py = min(2.0, max(-0.5, py))
        return (px + self.target_offset_x, clamped_py + self.target_offset_y, pz + self.target_offset_z)

    def snap_to(self, player: Any) -> None:
        """Immediately teleport camera to ideal follow pose without damping."""
        px = getattr(player, "x", 0.0)
        py = getattr(player, "y", 0.0)
        pz = getattr(player, "z", 0.0)

        self.pos_x, self.pos_y, self.pos_z = self.get_desired_position(px, py, pz)
        self.tgt_x, self.tgt_y, self.tgt_z = self.get_desired_target(px, py, pz)

        if self.camera is not None:
            try:
                self.camera.set_position(self.pos_x, self.pos_y, self.pos_z)
                self.camera.set_target(self.tgt_x, self.tgt_y, self.tgt_z)
            except Exception:
                pass

    def update(self, dt: float, player: Any) -> None:
        """Smoothly interpolate camera position and target toward ideal player offsets."""
        px = getattr(player, "x", 0.0)
        py = getattr(player, "y", 0.0)
        pz = getattr(player, "z", 0.0)

        des_pos_x, des_pos_y, des_pos_z = self.get_desired_position(px, py, pz)
        des_tgt_x, des_tgt_y, des_tgt_z = self.get_desired_target(px, py, pz)

        # Smooth exponential damping
        alpha = min(1.0, max(0.0, dt * self.damping))

        self.pos_x += (des_pos_x - self.pos_x) * alpha
        self.pos_y += (des_pos_y - self.pos_y) * alpha
        self.pos_z += (des_pos_z - self.pos_z) * alpha

        self.tgt_x += (des_tgt_x - self.tgt_x) * alpha
        self.tgt_y += (des_tgt_y - self.tgt_y) * alpha
        self.tgt_z += (des_tgt_z - self.tgt_z) * alpha

        if self.camera is not None:
            try:
                self.camera.set_position(self.pos_x, self.pos_y, self.pos_z)
                self.camera.set_target(self.tgt_x, self.tgt_y, self.tgt_z)
            except Exception:
                pass


class CrossyHUD:
    """Arcade 2D HUD rendering high-performance stats, scores, and banners."""

    def __init__(self, app: Optional[Any] = None) -> None:
        self.app = app
        self.high_score: int = 0
        self.smoothed_fps: float = 500.0

        py_ver = sys.version.split()[0]
        self.py_version_tag: str = f"🐍 PYTHON {py_ver} (64-bit) | Sokol GFX D3D11 | 500+ FPS"

    def update_high_score(self, score: int) -> None:
        """Update persistent high score if current score exceeds it."""
        if score > self.high_score:
            self.high_score = score

    def render(self, dt: float, player: Any) -> None:
        """Draw 2D HUD overlays via app.ui commands."""
        if self.app is None or not hasattr(self.app, "ui"):
            return

        score = getattr(player, "score", 0)
        self.update_high_score(score)

        if dt > 0.0:
            fps = 1.0 / dt
            self.smoothed_fps = self.smoothed_fps * 0.9 + fps * 0.1

        ui = self.app.ui
        ui.clear()

        screen_w = float(getattr(self.app, "width", 1280))
        screen_h = float(getattr(self.app, "height", 720))

        # 1. Top-left Slate Card
        card_w = 540.0
        card_h = 38.0
        slate_col = Color(0.11, 0.13, 0.18, 0.88)
        cyan_col = Color.from_hex("#38bdf8") if hasattr(Color, "from_hex") else (0.22, 0.74, 0.97, 1.0)
        ui.draw_rect(16.0, 16.0, card_w, card_h, slate_col)
        ui.draw_text(self.py_version_tag, (26.0, 25.0), size=14, color=cyan_col)

        # 2. Big Arcade Score Top-Center: SCORE: <score>   HIGH: <high>
        score_text = f"SCORE: {score}   HIGH: {self.high_score}"
        score_card_w = 360.0
        score_card_h = 44.0
        center_x = max(20.0, (screen_w - score_card_w) / 2.0)
        gold_col = Color.from_hex("#fbbf24") if hasattr(Color, "from_hex") else (0.98, 0.75, 0.14, 1.0)
        ui.draw_rect(center_x, 14.0, score_card_w, score_card_h, Color(0.08, 0.09, 0.12, 0.92))
        ui.draw_text(score_text, (center_x + 22.0, 24.0), size=22, color=gold_col)

        # Coins counter (if any)
        coins = getattr(player, "coins", 0)
        if coins > 0:
            coin_col = Color.from_hex("#facc15") if hasattr(Color, "from_hex") else (0.98, 0.80, 0.08, 1.0)
            ui.draw_text(f"COINS: {coins}", (center_x + score_card_w + 16.0, 27.0), size=16, color=coin_col)

        # Idle timeout warning
        idle_timer = getattr(player, "idle_timer", 0.0)
        timeout_limit = getattr(player, "IDLE_TIMEOUT", 8.0)
        rem = timeout_limit - idle_timer
        if 0.0 < rem < 3.0 and getattr(player, "status", None) == PlayerStatus.IDLE:
            red_col = Color.from_hex("#ef4444") if hasattr(Color, "from_hex") else (0.94, 0.27, 0.27, 1.0)
            ui.draw_text(f"⚠️ EAGLE INCOMING: {rem:.1f}s", (center_x + 70.0, 64.0), size=15, color=red_col)

        # 3. Game Over Banner
        player_status = getattr(player, "status", PlayerStatus.IDLE)
        if player_status in (PlayerStatus.SQUASHED, PlayerStatus.DROWNED, PlayerStatus.EATEN):
            banner_w = 480.0
            banner_h = 160.0
            bx = max(20.0, (screen_w - banner_w) / 2.0)
            by = max(40.0, (screen_h - banner_h) / 2.0)

            ui.draw_rect(bx, by, banner_w, banner_h, Color(0.06, 0.07, 0.10, 0.95))

            reason = getattr(player, "death_reason", None) or player_status.name
            danger_red = Color.from_hex("#ef4444") if hasattr(Color, "from_hex") else (0.94, 0.27, 0.27, 1.0)
            light_gray = Color.from_hex("#cbd5e1") if hasattr(Color, "from_hex") else (0.80, 0.84, 0.88, 1.0)
            bright_yellow = Color.from_hex("#facc15") if hasattr(Color, "from_hex") else (0.98, 0.80, 0.08, 1.0)

            ui.draw_text("GAME OVER", (bx + 160.0, by + 24.0), size=28, color=danger_red)
            ui.draw_text(f"Cause: {reason}", (bx + 140.0, by + 68.0), size=16, color=light_gray)
            ui.draw_text("[R] Press R to Restart", (bx + 120.0, by + 108.0), size=20, color=bright_yellow)

        # 4. Footer controls
        hint_col = Color.from_hex("#94a3b8") if hasattr(Color, "from_hex") else (0.58, 0.64, 0.72, 1.0)
        ui.draw_text(
            "[W/A/S/D or Arrows] Hop  |  [R] Restart  |  [ESC] Exit",
            (24.0, screen_h - 28.0),
            size=14,
            color=hint_col,
        )
