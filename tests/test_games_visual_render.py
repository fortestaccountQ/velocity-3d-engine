"""Hostile Visual Rendering Verification for 3D Games Suite.

Verifies:
1. `SpaceCombatArena` (6DOF space flight, instanced asteroid field, laser blasters, AI drones).
2. `DungeonCrawler` (Skeletal hero, modular dungeon, torch PointLights, FollowCamera).
3. 0% Black Screen guarantee:
   - Evaluated BOTH with `EffectComposer` active AND without `EffectComposer` active.
   - Strict mathematical image analysis:
     * Mean luminance > 15.0 / 255.0
     * Standard deviation > 10.0 (high spatial contrast, shading, lighting)
     * Color presence > 35.0% (distinct non-black geometry, skybox, particles)
4. Camera motion and View-Projection matrix updates:
   - Starfighter 6DOF camera updates in `SpaceCombatArena`
   - Spring-arm `FollowCamera` updates in `DungeonCrawler`
5. Frame dumping to `tests/output/test_space_combat_frame.png` and `tests/output/test_dungeon_crawler_frame.png`.
"""

from __future__ import annotations

import sys
import math
from pathlib import Path
import pytest
import numpy as np
from PIL import Image

# Ensure package import paths
repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import pielosyty as p
from games.space_combat_arena import SpaceCombatArena
from games.dungeon_crawler import DungeonCrawler

OUTPUT_DIR = repo_root / "tests" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def compute_visual_metrics(rgba_bytes: bytes, width: int, height: int, is_float16: bool = False) -> dict[str, float]:
    """Compute mathematical visual metrics on an RGBA frame buffer.

    Returns:
        dict containing:
        - 'mean_luminance': ITU-R BT.709 relative luminance [0, 255]
        - 'std_luminance': standard deviation of luminance across pixels
        - 'non_black_ratio': fraction of pixels with at least one color channel > 10/255
        - 'max_luminance': peak luminance value
        - 'min_luminance': lowest luminance value
    """
    if is_float16:
        # RGBA16F (8 bytes per pixel)
        raw_arr = np.frombuffer(rgba_bytes, dtype=np.float16).reshape((height, width, 4))
        r = np.clip(raw_arr[:, :, 0].astype(np.float64) * 255.0, 0.0, 255.0)
        g = np.clip(raw_arr[:, :, 1].astype(np.float64) * 255.0, 0.0, 255.0)
        b = np.clip(raw_arr[:, :, 2].astype(np.float64) * 255.0, 0.0, 255.0)
    else:
        # RGBA8 (4 bytes per pixel)
        raw_arr = np.frombuffer(rgba_bytes, dtype=np.uint8).reshape((height, width, 4))
        r = raw_arr[:, :, 0].astype(np.float64)
        g = raw_arr[:, :, 1].astype(np.float64)
        b = raw_arr[:, :, 2].astype(np.float64)

    # Standard ITU-R BT.709 perceived luminance weights
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    mean_lum = float(np.mean(lum))
    std_lum = float(np.std(lum))
    max_lum = float(np.max(lum))
    min_lum = float(np.min(lum))

    # A pixel is considered non-black if any color channel exceeds threshold (10 / 255)
    non_black_mask = (r > 10.0) | (g > 10.0) | (b > 10.0)
    non_black_ratio = float(np.sum(non_black_mask)) / float(width * height)

    return {
        "mean_luminance": mean_lum,
        "std_luminance": std_lum,
        "non_black_ratio": non_black_ratio,
        "max_luminance": max_lum,
        "min_luminance": min_lum,
    }


def save_rgba_image(rgba_bytes: bytes, width: int, height: int, output_path: Path, is_float16: bool = False) -> None:
    """Save raw pixel buffer to a PNG screenshot."""
    if is_float16:
        raw_arr = np.frombuffer(rgba_bytes, dtype=np.float16).reshape((height, width, 4))
        rgb = np.clip(raw_arr[:, :, :3].astype(np.float64) * 255.0, 0.0, 255.0).astype(np.uint8)
        img = Image.fromarray(rgb)
    else:
        img = Image.frombytes("RGBA", (width, height), rgba_bytes)
    img.save(output_path)


# ============================================================================
# 1. Space Combat Arena Visual Rendering Tests
# ============================================================================

def test_space_combat_camera_6dof_update():
    """Verify that starfighter 6DOF flight dynamics updates camera position & VP matrix."""
    arena = SpaceCombatArena(width=320, height=240, self_play=True, max_frames=20)
    cam = arena.app.camera

    p0 = tuple(cam.position)
    v0 = cam.view_matrix()
    vp0 = cam.view_projection_matrix()

    # Advance 15 frames of flight dynamics
    for _ in range(15):
        arena.update_physics(1.0 / 60.0)

    p1 = tuple(cam.position)
    v1 = cam.view_matrix()
    vp1 = cam.view_projection_matrix()

    # Camera must have moved behind accelerating ship
    assert p0 != p1, f"Camera position must change during 6DOF flight! Initial: {p0}, Final: {p1}"
    assert v0 != v1, "View matrix must update as ship turns and thrusts!"
    assert vp0 != vp1, "View-projection matrix must update!"

    # Verify look target is oriented forward
    look_dist = math.hypot(p1[0] - arena.player_pos[0], p1[2] - arena.player_pos[2])
    assert look_dist > 1.0, "Camera should maintain chase distance from player ship"


def test_space_combat_arena_visual_render():
    """Hostile visual rendering verification of SpaceCombatArena with and without EffectComposer."""
    w, h = 320, 240
    arena = SpaceCombatArena(width=w, height=h, self_play=True, max_frames=30)

    # Advance simulation by 20 frames so asteroids tumble, drones patrol, and thrusters burn
    for _ in range(20):
        arena.update_physics(1.0 / 60.0)

    # ------------------------------------------------------------------------
    # Phase A: Direct Render to RenderTarget (WITHOUT EffectComposer)
    # ------------------------------------------------------------------------
    target_direct = p.RenderTarget(w, h, p.RenderTargetFormat.RGBA8, True)
    assert target_direct.is_valid()

    arena.app.render_target(arena.scene, arena.app.camera, target_direct)
    raw_pixels_direct = arena.app.read_pixels(target_direct)
    assert len(raw_pixels_direct) == w * h * 4

    metrics_direct = compute_visual_metrics(raw_pixels_direct, w, h, is_float16=False)
    print(f"\n[SpaceCombatArena - Direct Render]")
    print(f"  Mean Luminance:    {metrics_direct['mean_luminance']:.2f} / 255.0 (req: > 15.0)")
    print(f"  StdDev Luminance:  {metrics_direct['std_luminance']:.2f} (req: > 10.0)")
    print(f"  Non-Black Pixels:  {metrics_direct['non_black_ratio'] * 100.0:.2f}% (req: > 35.0%)")
    print(f"  Max Luminance:     {metrics_direct['max_luminance']:.2f}")

    # Assert strict hostile QA thresholds
    assert metrics_direct["mean_luminance"] > 15.0, (
        f"Mean luminance {metrics_direct['mean_luminance']:.2f} too dark! Must be > 15.0"
    )
    assert metrics_direct["std_luminance"] > 10.0, (
        f"StdDev luminance {metrics_direct['std_luminance']:.2f} too low! Must be > 10.0 (contrast missing)"
    )
    assert metrics_direct["non_black_ratio"] > 0.35, (
        f"Non-black pixels {metrics_direct['non_black_ratio'] * 100.0:.2f}% too low! Must be > 35%"
    )

    # Save visual verification screenshot
    out_png_path = OUTPUT_DIR / "test_space_combat_frame.png"
    save_rgba_image(raw_pixels_direct, w, h, out_png_path, is_float16=False)
    assert out_png_path.exists()
    assert out_png_path.stat().st_size > 1000

    # ------------------------------------------------------------------------
    # Phase B: Render WITH EffectComposer active (HDR + Bloom + Tonemapping)
    # ------------------------------------------------------------------------
    assert arena.composer is not None
    assert arena.composer.enabled is True

    arena.composer.render(arena.scene, arena.app.camera)
    hdr_target = arena.composer.hdr_target
    assert hdr_target.is_valid()

    raw_pixels_hdr = arena.app.read_pixels(hdr_target)
    assert len(raw_pixels_hdr) == w * h * 8  # RGBA16F = 8 bytes per pixel

    metrics_hdr = compute_visual_metrics(raw_pixels_hdr, w, h, is_float16=True)
    print(f"[SpaceCombatArena - EffectComposer HDR]")
    print(f"  Mean Luminance:    {metrics_hdr['mean_luminance']:.2f} / 255.0 (req: > 15.0)")
    print(f"  StdDev Luminance:  {metrics_hdr['std_luminance']:.2f} (req: > 10.0)")
    print(f"  Non-Black Pixels:  {metrics_hdr['non_black_ratio'] * 100.0:.2f}% (req: > 35.0%)")

    assert metrics_hdr["mean_luminance"] > 15.0, (
        f"HDR Mean luminance {metrics_hdr['mean_luminance']:.2f} too dark! Must be > 15.0"
    )
    assert metrics_hdr["std_luminance"] > 10.0, (
        f"HDR StdDev luminance {metrics_hdr['std_luminance']:.2f} too low! Must be > 10.0"
    )
    assert metrics_hdr["non_black_ratio"] > 0.35, (
        f"HDR Non-black pixels {metrics_hdr['non_black_ratio'] * 100.0:.2f}% too low! Must be > 35%"
    )

    out_composer_path = OUTPUT_DIR / "test_space_combat_composer_frame.png"
    save_rgba_image(raw_pixels_hdr, w, h, out_composer_path, is_float16=True)
    assert out_composer_path.exists()
    assert out_composer_path.stat().st_size > 1000


# ============================================================================
# 2. Dungeon Crawler Visual Rendering Tests
# ============================================================================

def test_dungeon_crawler_follow_camera_update():
    """Verify that spring-arm FollowCamera tracks skeletal hero & updates VP matrix."""
    crawler = DungeonCrawler(width=320, height=240, self_play=True, max_frames=20)
    cam = crawler.follow_cam.camera if hasattr(crawler.follow_cam, "camera") else crawler.app.camera

    p0 = tuple(cam.position)
    v0 = cam.view_matrix()
    vp0 = cam.view_projection_matrix()

    # Advance 15 frames of hero navigation towards chest
    for _ in range(15):
        crawler.update(1.0 / 60.0)

    p1 = tuple(cam.position)
    v1 = cam.view_matrix()
    vp1 = cam.view_projection_matrix()

    # Camera must smoothly interpolate position following hero
    assert p0 != p1, f"FollowCamera position must update! Initial: {p0}, Final: {p1}"
    assert v0 != v1, "FollowCamera view matrix must change as hero moves!"
    assert vp0 != vp1, "FollowCamera view-projection matrix must change!"

    # Spring-arm height constraint (camera must stay elevated above ground)
    assert p1[1] > 2.0, f"Camera height {p1[1]} should stay elevated above ground level!"


def test_dungeon_crawler_visual_render():
    """Hostile visual rendering verification of DungeonCrawler with and without EffectComposer."""
    w, h = 320, 240
    crawler = DungeonCrawler(width=w, height=h, self_play=True, max_frames=30)
    cam = crawler.follow_cam.camera if hasattr(crawler.follow_cam, "camera") else crawler.app.camera

    # Advance simulation by 20 frames so torch fire flickers, hero walks, and mixer updates
    for _ in range(20):
        crawler.update(1.0 / 60.0)

    # ------------------------------------------------------------------------
    # Phase A: Direct Render to RenderTarget (WITHOUT EffectComposer)
    # ------------------------------------------------------------------------
    target_direct = p.RenderTarget(w, h, p.RenderTargetFormat.RGBA8, True)
    assert target_direct.is_valid()

    crawler.app.render_target(crawler.scene, cam, target_direct)
    raw_pixels_direct = crawler.app.read_pixels(target_direct)
    assert len(raw_pixels_direct) == w * h * 4

    metrics_direct = compute_visual_metrics(raw_pixels_direct, w, h, is_float16=False)
    print(f"\n[DungeonCrawler - Direct Render]")
    print(f"  Mean Luminance:    {metrics_direct['mean_luminance']:.2f} / 255.0 (req: > 15.0)")
    print(f"  StdDev Luminance:  {metrics_direct['std_luminance']:.2f} (req: > 10.0)")
    print(f"  Non-Black Pixels:  {metrics_direct['non_black_ratio'] * 100.0:.2f}% (req: > 35.0%)")
    print(f"  Max Luminance:     {metrics_direct['max_luminance']:.2f}")

    # Assert strict hostile QA thresholds
    assert metrics_direct["mean_luminance"] > 15.0, (
        f"Mean luminance {metrics_direct['mean_luminance']:.2f} too dark! Must be > 15.0"
    )
    assert metrics_direct["std_luminance"] > 10.0, (
        f"StdDev luminance {metrics_direct['std_luminance']:.2f} too low! Must be > 10.0"
    )
    assert metrics_direct["non_black_ratio"] > 0.35, (
        f"Non-black pixels {metrics_direct['non_black_ratio'] * 100.0:.2f}% too low! Must be > 35%"
    )

    # Save visual verification screenshot
    out_png_path = OUTPUT_DIR / "test_dungeon_crawler_frame.png"
    save_rgba_image(raw_pixels_direct, w, h, out_png_path, is_float16=False)
    assert out_png_path.exists()
    assert out_png_path.stat().st_size > 1000

    # ------------------------------------------------------------------------
    # Phase B: Render WITH EffectComposer active (SSAO + Bloom + Tonemapping)
    # ------------------------------------------------------------------------
    assert crawler.composer is not None
    assert crawler.composer.enabled is True

    crawler.composer.render(crawler.scene, cam)
    hdr_target = crawler.composer.hdr_target
    assert hdr_target.is_valid()

    raw_pixels_hdr = crawler.app.read_pixels(hdr_target)
    assert len(raw_pixels_hdr) == w * h * 8  # RGBA16F = 8 bytes per pixel

    metrics_hdr = compute_visual_metrics(raw_pixels_hdr, w, h, is_float16=True)
    print(f"[DungeonCrawler - EffectComposer HDR]")
    print(f"  Mean Luminance:    {metrics_hdr['mean_luminance']:.2f} / 255.0 (req: > 15.0)")
    print(f"  StdDev Luminance:  {metrics_hdr['std_luminance']:.2f} (req: > 10.0)")
    print(f"  Non-Black Pixels:  {metrics_hdr['non_black_ratio'] * 100.0:.2f}% (req: > 35.0%)")

    assert metrics_hdr["mean_luminance"] > 15.0, (
        f"HDR Mean luminance {metrics_hdr['mean_luminance']:.2f} too dark! Must be > 15.0"
    )
    assert metrics_hdr["std_luminance"] > 10.0, (
        f"HDR StdDev luminance {metrics_hdr['std_luminance']:.2f} too low! Must be > 10.0"
    )
    assert metrics_hdr["non_black_ratio"] > 0.35, (
        f"HDR Non-black pixels {metrics_hdr['non_black_ratio'] * 100.0:.2f}% too low! Must be > 35%"
    )

    out_composer_path = OUTPUT_DIR / "test_dungeon_crawler_composer_frame.png"
    save_rgba_image(raw_pixels_hdr, w, h, out_composer_path, is_float16=True)
    assert out_composer_path.exists()
    assert out_composer_path.stat().st_size > 1000
