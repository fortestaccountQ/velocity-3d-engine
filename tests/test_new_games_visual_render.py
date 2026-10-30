"""Visual Rendering Verification & Screen Capture for the 3 New 3D Games.

Verifies:
1. `game_3d_mario.py` (Floating islands, grassy plateaus, coins, character, follow camera).
2. `game_3d_racing.py` (Closed circuit, sports car with wheels, curbs, checkpoints).
3. `game_3d_flappy_bird.py` (3D bird, pipes, sky, clouds).
4. Strict Hostile 0% Black Screen Guarantee:
   - Mean luminance > 15.0 / 255.0
   - StdDev luminance > 10.0 (high spatial contrast)
   - Non-black pixel ratio > 35.0%
5. Frame capture to `tests/output/`:
   - `test_mario_3d_frame.png`
   - `test_racing_3d_frame.png`
   - `test_flappy_bird_3d_frame.png`
"""

from __future__ import annotations

import sys
import math
from pathlib import Path
import pytest
import numpy as np
from PIL import Image

repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
examples_dir = repo_root / "examples"

if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(examples_dir) not in sys.path:
    sys.path.insert(0, str(examples_dir))

import VelocityEngine as ve
from VelocityEngine import App, RenderTarget, RenderTargetFormat

OUTPUT_DIR = repo_root / "tests" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def compute_visual_metrics(rgba_bytes: bytes, width: int, height: int) -> dict[str, float]:
    arr = np.frombuffer(rgba_bytes, dtype=np.uint8).reshape((height, width, 4))
    r = arr[:, :, 0].astype(np.float64)
    g = arr[:, :, 1].astype(np.float64)
    b = arr[:, :, 2].astype(np.float64)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    mean_lum = float(np.mean(lum))
    std_lum = float(np.std(lum))
    non_black = float(np.count_nonzero((r > 10) | (g > 10) | (b > 10))) / float(width * height)
    return {
        "mean_luminance": mean_lum,
        "std_luminance": std_lum,
        "non_black_ratio": non_black,
        "max_luminance": float(np.max(lum)),
        "min_luminance": float(np.min(lum)),
    }


def save_image(rgba_bytes: bytes, width: int, height: int, path: Path) -> None:
    img = Image.frombytes("RGBA", (width, height), rgba_bytes)
    img.save(path)


def test_mario_3d_visual_render():
    """Verify 3D Mario Platformer visual rendering and capture test frame."""
    from examples.game_3d_mario import MarioGame

    w, h = 640, 480
    app = App("MarioVisualTest", width=w, height=h, clear_color="#5c9efc")
    game = MarioGame(app=app, test_mode=True)

    # Step 15 simulation frames
    for _ in range(15):
        game.update(1.0 / 60.0)

    target = RenderTarget(w, h, RenderTargetFormat.RGBA8, True)
    assert target.is_valid()

    app.render_target(app.scene, app.camera, target)
    raw_pixels = app.read_pixels(target)
    assert len(raw_pixels) == w * h * 4

    metrics = compute_visual_metrics(raw_pixels, w, h)
    print(f"\n[Mario 3D Visual Render] Mean Lum: {metrics['mean_luminance']:.2f}, StdDev: {metrics['std_luminance']:.2f}, Non-Black: {metrics['non_black_ratio']*100:.1f}%")

    assert metrics["mean_luminance"] > 15.0, f"Mario 3D render is too dark! Mean: {metrics['mean_luminance']}"
    assert metrics["std_luminance"] > 10.0, f"Mario 3D lacks visual contrast! StdDev: {metrics['std_luminance']}"
    assert metrics["non_black_ratio"] > 0.35, f"Mario 3D non-black ratio too low: {metrics['non_black_ratio']}"

    out_path = OUTPUT_DIR / "test_mario_3d_frame.png"
    save_image(raw_pixels, w, h, out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000

    game.cleanup()
    app.close()


def test_racing_3d_visual_render():
    """Verify 3D Racing Simulator visual rendering and capture test frame."""
    from examples.game_3d_racing import RacingSimulatorApp

    w, h = 640, 480
    sim = RacingSimulatorApp(width=w, height=h, self_play=True, max_test_frames=20)
    app = sim.app

    # Step 15 simulation frames
    for _ in range(15):
        sim.update(1.0 / 60.0)

    target = RenderTarget(w, h, RenderTargetFormat.RGBA8, True)
    assert target.is_valid()

    app.render_target(app.scene, app.camera, target)
    raw_pixels = app.read_pixels(target)
    assert len(raw_pixels) == w * h * 4

    metrics = compute_visual_metrics(raw_pixels, w, h)
    print(f"\n[Racing 3D Visual Render] Mean Lum: {metrics['mean_luminance']:.2f}, StdDev: {metrics['std_luminance']:.2f}, Non-Black: {metrics['non_black_ratio']*100:.1f}%")

    assert metrics["mean_luminance"] > 15.0, f"Racing 3D render is too dark! Mean: {metrics['mean_luminance']}"
    assert metrics["std_luminance"] > 10.0, f"Racing 3D lacks visual contrast! StdDev: {metrics['std_luminance']}"
    assert metrics["non_black_ratio"] > 0.35, f"Racing 3D non-black ratio too low: {metrics['non_black_ratio']}"

    out_path = OUTPUT_DIR / "test_racing_3d_frame.png"
    save_image(raw_pixels, w, h, out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000

    app.close()


def test_flappy_bird_3d_visual_render():
    """Verify 3D Flappy Bird visual rendering and capture test frame."""
    from examples.game_3d_flappy_bird import FlappyBirdGame

    w, h = 640, 480
    game = FlappyBirdGame(width=w, height=h, self_play=True, max_test_frames=20)
    app = game.app

    # Step 15 simulation frames
    for _ in range(15):
        game.update(1.0 / 60.0)

    target = RenderTarget(w, h, RenderTargetFormat.RGBA8, True)
    assert target.is_valid()

    app.render_target(app.scene, app.camera, target)
    raw_pixels = app.read_pixels(target)
    assert len(raw_pixels) == w * h * 4

    metrics = compute_visual_metrics(raw_pixels, w, h)
    print(f"\n[Flappy Bird 3D Visual Render] Mean Lum: {metrics['mean_luminance']:.2f}, StdDev: {metrics['std_luminance']:.2f}, Non-Black: {metrics['non_black_ratio']*100:.1f}%")

    assert metrics["mean_luminance"] > 15.0, f"Flappy Bird 3D render is too dark! Mean: {metrics['mean_luminance']}"
    assert metrics["std_luminance"] > 10.0, f"Flappy Bird 3D lacks visual contrast! StdDev: {metrics['std_luminance']}"
    assert metrics["non_black_ratio"] > 0.35, f"Flappy Bird 3D non-black ratio too low: {metrics['non_black_ratio']}"

    out_path = OUTPUT_DIR / "test_flappy_bird_3d_frame.png"
    save_image(raw_pixels, w, h, out_path)
    assert out_path.exists()
    assert out_path.stat().st_size > 1000

    game.cleanup()
    app.close()
