"""Example 12: High-Performance NumPy Wave Surface (180x180 Grid, 32,400 Vertices).

Showcase:
- Dynamic grid mesh (180 x 180 = 32,400 vertices <= 65,535 uint16 limit).
- Robust quad triangulation indices: (i, i+1, i+nx, i+nx, i+1, i+nx+1).
- Real-time height field synthesis in pure NumPy: y = sin(x*f + t) * cos(z*f + t).
- Zero-copy / low-overhead GPU vertex buffer streaming via mesh.update_vertices_from_numpy() at 60+ FPS.
- Dynamic vertex coloring based on wave amplitude.
- Standalone execution and headless/test suite support (--test).
"""

from __future__ import annotations
import sys
import math
import time
from pathlib import Path
from typing import Optional

# Ensure package import
repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

import numpy as np
import VelocityEngine as ve
from VelocityEngine import (
    App,
    OrbitController,
    Mesh,
    StandardMaterial,
    CubeTexture,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
    GREEN,
)


def create_wave_grid(
    nx: int = 180, nz: int = 180, size_x: float = 60.0, size_z: float = 60.0
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Preallocate 32,400 vertex buffer (180x180) and proper quad triangulation indices."""
    n = nx * nz
    x = np.linspace(-size_x * 0.5, size_x * 0.5, nx, dtype=np.float32)
    z = np.linspace(-size_z * 0.5, size_z * 0.5, nz, dtype=np.float32)
    xx, zz = np.meshgrid(x, z)
    xx_flat = xx.ravel()
    zz_flat = zz.ravel()

    # 16-float vertex stride layout:
    # 0..2: pos(x,y,z), 3..5: normal(x,y,z), 6..7: uv(u,v), 8..11: color(rgba), 12..15: tangent(xyzw)
    buffer = np.zeros((n, 16), dtype=np.float32)
    buffer[:, 0] = xx_flat
    buffer[:, 1] = 0.0
    buffer[:, 2] = zz_flat

    # Default upward normal
    buffer[:, 4] = 1.0

    # UV coordinates
    buffer[:, 6] = (xx_flat + size_x * 0.5) / size_x
    buffer[:, 7] = (zz_flat + size_z * 0.5) / size_z

    # Initial cyan tint
    buffer[:, 8] = 0.1   # R
    buffer[:, 9] = 0.6   # G
    buffer[:, 10] = 0.9  # B
    buffer[:, 11] = 1.0  # A

    # Tangent
    buffer[:, 12] = 1.0
    buffer[:, 15] = 1.0

    # Quad triangulation indices: (i, i+1, i+nx, i+nx, i+1, i+nx+1)
    gx = np.arange(nx - 1, dtype=np.uint32)
    gz = np.arange(nz - 1, dtype=np.uint32)
    gxx, gzz = np.meshgrid(gx, gz)
    i = (gzz * nx + gxx).ravel()

    i_plus_1 = i + 1
    i_plus_nx = i + nx
    i_plus_nx_plus_1 = i + nx + 1

    tri1 = np.stack([i, i_plus_1, i_plus_nx], axis=1)
    tri2 = np.stack([i_plus_nx, i_plus_1, i_plus_nx_plus_1], axis=1)
    indices = np.hstack([tri1, tri2]).reshape(-1).astype(np.uint16)

    return buffer, xx_flat, zz_flat, indices


def run_example(headless: bool = False, frames: int = 60, nx: int = 180, nz: int = 180) -> App:
    """Run the 180x180 vertex wave example in interactive or headless mode."""
    app = App("Velocity - 12 NumPy Wave Surface", width=1280, height=720, clear_color="#090d14")

    # Camera looking at center of the wave
    orb = OrbitController(target=(0.0, 0.0, 0.0), distance=45.0, min_distance=5.0, max_distance=120.0, pitch=35.0)
    app.camera = orb

    # Directional sun and environment reflections
    app.scene.set_sun(direction=(-0.8, -1.8, -1.0), color=WARM_WHITE, intensity=1.5)
    env = CubeTexture.create_gradient(
        top_color=Vec3(0.1, 0.35, 0.7),
        horizon_color=Vec3(0.65, 0.8, 0.9),
        bottom_color=Vec3(0.05, 0.08, 0.12),
        size=64,
    )
    app.scene.set_environment(env, 1.2)

    # 1. Allocate 180x180 (32,400 Vertices) Wave Mesh with Proper Quad Indices
    total_vertices = nx * nz
    buffer, xx_flat, zz_flat, indices = create_wave_grid(nx, nz, 60.0, 60.0)

    wave_mesh = Mesh.from_numpy(buffer, indices=indices)
    wave_mesh.update_vertices_from_numpy(buffer, recalculate_bounds=False)

    wave_entity = app.scene.create_entity("DynamicNumPyWave")
    wave_entity.mesh = wave_mesh

    mat = StandardMaterial()
    mat.base_color = (0.2, 0.7, 1.0, 1.0)
    mat.roughness = 0.25
    mat.metallic = 0.3
    wave_entity.material = mat

    # Ground reference grid
    app.scene.create_grid(size=80.0, step=2.0, color=Color.from_hex("#1b2230"))

    # UI Overlay setup
    app.ui.clear()
    app.ui.draw_text("Velocity 3D Engine | 12: NumPy Wave Surface", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text(f"Dynamic Surface: {total_vertices:,} Vertices (180 x 180 Quad Grid)", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("GPU Buffer Streaming: mesh.update_vertices_from_numpy() @ 60+ FPS", (24, 76), size=13, color=GREEN)
    app.ui.show_stats(True)

    time_accum = 0.0
    frame_counter = 0
    t0_bench = time.perf_counter()

    freq = 0.35
    amp = 2.2

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        t = time_accum * 2.5

        # NumPy Vectorized Height Modulation: Z = sin(X*f + t) * cos(Y*f + t)
        y_height = np.sin(xx_flat * freq + t) * np.cos(zz_flat * freq + t) * amp
        buffer[:, 1] = y_height

        # Dynamic crest/trough color gradient
        norm_h = (y_height + amp) / (2.0 * amp)
        buffer[:, 8] = 0.05 + 0.15 * norm_h  # R
        buffer[:, 9] = 0.35 + 0.55 * norm_h  # G
        buffer[:, 10] = 0.75 + 0.25 * norm_h # B

        # Stream updated vertex buffer directly to GPU
        t_upload_start = time.perf_counter()
        wave_mesh.update_vertices_from_numpy(buffer, recalculate_bounds=False)
        upload_ms = (time.perf_counter() - t_upload_start) * 1000.0

        if frame_counter % 30 == 0:
            app.ui.draw_text(
                f"Upload Latency: {upload_ms:.2f} ms | {total_vertices:,} Vertices Dynamic Stream",
                (24, 100),
                size=12,
                color=YELLOW,
            )

        if (headless or "--test" in sys.argv or "--headless" in sys.argv) and frame_counter >= frames:
            app.close()

    app.on_update(update)

    if not headless and "--headless" not in sys.argv and "--test" not in sys.argv:
        app.run()
    else:
        for _ in range(frames):
            update(1.0 / 60.0)

    elapsed = time.perf_counter() - t0_bench
    fps = frame_counter / max(0.0001, elapsed)
    print(f"NumPy Wave benchmark: {frame_counter} frames in {elapsed:.3f}s ({fps:.1f} FPS)")

    return app


if __name__ == "__main__":
    is_headless = "--headless" in sys.argv or "--test" in sys.argv
    frame_limit = 60
    for idx, arg in enumerate(sys.argv):
        if arg == "--frames" and idx + 1 < len(sys.argv):
            try:
                frame_limit = int(sys.argv[idx + 1])
            except ValueError:
                pass

    run_example(headless=is_headless, frames=frame_limit)
