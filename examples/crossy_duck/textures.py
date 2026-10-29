"""Crossy Duck - Stylized Procedural Voxel / Pixel-Art Textures and Materials.

Implements high-fidelity procedural 64x64 and 128x128 stylized voxel/pixel-art
texture generators using Pillow (PIL) and NumPy for VelocityEngine.
Strictly adheres to contracts/texture_contracts.py.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

from contracts.texture_contracts import (
    MaterialPaletteContract,
    TextureGeneratorContract,
)

# Optional VelocityEngine native import
try:
    import VelocityEngine as ve
    from VelocityEngine import Material, Texture
except ImportError:
    ve = None
    Texture = None
    Material = None


# -----------------------------------------------------------------------------
# PBR Material Configuration Descriptor
# -----------------------------------------------------------------------------

@dataclass
class MaterialConfig:
    """PBR material configuration for Crossy Duck stylized voxels."""
    name: str
    roughness: float = 0.5
    metallic: float = 0.0
    base_color: Tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    uv_scale: Tuple[float, float] = (1.0, 1.0)
    is_pixel_art: bool = True
    animated: bool = False


# Default PBR material parameters tuned for Sokol GFX PBR-lite pipeline
MATERIAL_PRESETS: Dict[str, MaterialConfig] = {
    "grass": MaterialConfig(
        name="grass",
        roughness=0.85,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "asphalt": MaterialConfig(
        name="asphalt",
        roughness=0.90,
        metallic=0.02,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "water": MaterialConfig(
        name="water",
        roughness=0.15,
        metallic=0.05,
        base_color=(1.0, 1.0, 1.0, 0.95),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
        animated=True,
    ),
    "wood_bark": MaterialConfig(
        name="wood_bark",
        roughness=0.80,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "wood_rings": MaterialConfig(
        name="wood_rings",
        roughness=0.75,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "rail_gravel": MaterialConfig(
        name="rail_gravel",
        roughness=0.95,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "gravel": MaterialConfig(
        name="gravel",
        roughness=0.95,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "rail_tie": MaterialConfig(
        name="rail_tie",
        roughness=0.70,
        metallic=0.20,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "car_paint": MaterialConfig(
        name="vehicle",
        roughness=0.25,
        metallic=0.15,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "car_grille": MaterialConfig(
        name="car_grille",
        roughness=0.30,
        metallic=0.60,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "vehicle": MaterialConfig(
        name="vehicle",
        roughness=0.25,
        metallic=0.15,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "duck": MaterialConfig(
        name="duck",
        roughness=0.45,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "tree_leaves": MaterialConfig(
        name="tree_leaves",
        roughness=0.80,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "lilypad": MaterialConfig(
        name="lilypad",
        roughness=0.60,
        metallic=0.00,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
}


# -----------------------------------------------------------------------------
# Stylized Material Class
# -----------------------------------------------------------------------------

if Material is not None:
    class StylizedMaterial(Material):
        """Native VelocityEngine Material with pixel-art metadata and safe uv_scale."""

        def __init__(
            self,
            texture: Any = None,
            roughness: float = 0.5,
            metallic: float = 0.0,
            is_pixel_art: bool = True,
            uv_scale: Tuple[float, float] = (1.0, 1.0),
            name: str = "",
        ) -> None:
            super().__init__(texture=texture, roughness=roughness, metallic=metallic)
            self.is_pixel_art = is_pixel_art
            self._uv_scale = (float(uv_scale[0]), float(uv_scale[1]))
            self._uv_offset = (0.0, 0.0)
            self.name = name
            self.set_uv_scale(self._uv_scale[0], self._uv_scale[1])

        @property
        def uv_scale(self) -> Tuple[float, float]:
            return self._uv_scale

        @uv_scale.setter
        def uv_scale(self, val: Sequence[float]) -> None:
            self._uv_scale = (float(val[0]), float(val[1]))
            self.set_uv_scale(self._uv_scale[0], self._uv_scale[1])

        @property
        def uv_offset(self) -> Tuple[float, float]:
            try:
                return super().uv_offset
            except Exception:
                return self._uv_offset

        @uv_offset.setter
        def uv_offset(self, val: Sequence[float]) -> None:
            self._uv_offset = (float(val[0]), float(val[1]))
            self.set_uv_offset(self._uv_offset[0], self._uv_offset[1])
else:
    class StylizedMaterial:  # type: ignore
        """Fallback mock Material when native VelocityEngine is not loaded."""

        def __init__(
            self,
            texture: Any = None,
            roughness: float = 0.5,
            metallic: float = 0.0,
            is_pixel_art: bool = True,
            uv_scale: Tuple[float, float] = (1.0, 1.0),
            name: str = "",
        ) -> None:
            self.albedo_map = texture
            self.roughness = roughness
            self.metallic = metallic
            self.is_pixel_art = is_pixel_art
            self._uv_scale = (float(uv_scale[0]), float(uv_scale[1]))
            self._uv_offset = (0.0, 0.0)
            self.name = name
            self.base_color = (1.0, 1.0, 1.0, 1.0)

        def set_color(self, r: float, g: float, b: float, a: float = 1.0) -> None:
            self.base_color = (r, g, b, a)

        def set_uv_scale(self, u: float, v: float) -> None:
            self._uv_scale = (float(u), float(v))

        @property
        def uv_scale(self) -> Tuple[float, float]:
            return self._uv_scale

        @uv_scale.setter
        def uv_scale(self, val: Sequence[float]) -> None:
            self._uv_scale = (float(val[0]), float(val[1]))

        def set_uv_offset(self, u: float, v: float) -> None:
            self._uv_offset = (float(u), float(v))

        @property
        def uv_offset(self) -> Tuple[float, float]:
            return self._uv_offset

        @uv_offset.setter
        def uv_offset(self, val: Sequence[float]) -> None:
            self._uv_offset = (float(val[0]), float(val[1]))


# -----------------------------------------------------------------------------
# Procedural Texture Generators (PIL & NumPy)
# -----------------------------------------------------------------------------

def create_grass_image(size: int = 64, seed: int = 1337) -> Image.Image:
    """Generate vibrant lush green meadow with pixel blade clusters, flower dots & earth tones."""
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[:size, :size]

    # Macro tone variations using smooth periodic harmonics for seamless tiling
    fx = 2.0 * np.pi * 2.0 / size
    fy = 2.0 * np.pi * 2.0 / size
    macro = 0.5 + 0.35 * np.sin(x * fx) * np.cos(y * fy)

    # Base green: lush meadow green (88, 180, 52)
    r = 74 + macro * 28 + rng.randint(-5, 6, (size, size))
    g = 162 + macro * 34 + rng.randint(-6, 7, (size, size))
    b = 38 + macro * 24 + rng.randint(-5, 6, (size, size))

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = np.clip(r, 0, 255)
    arr[..., 1] = np.clip(g, 0, 255)
    arr[..., 2] = np.clip(b, 0, 255)
    arr[..., 3] = 255

    # Discrete voxel blade tufts (root: dark green, tip: sunny lime)
    num_tufts = int(size * size * 0.05)
    tx = rng.randint(0, size, num_tufts)
    ty = rng.randint(1, size, num_tufts)
    for px, py in zip(tx, ty):
        arr[py, px, :3] = [52, 126, 28]  # dark root
        arr[(py - 1) % size, px, :3] = [128, 220, 70]  # bright tip
        if rng.rand() > 0.5:
            arr[(py - 1) % size, (px + 1) % size, :3] = [112, 206, 62]

    # Earthy soil/clover speckles
    num_earth = int(size * size * 0.02)
    ex = rng.randint(0, size, num_earth)
    ey = rng.randint(0, size, num_earth)
    for px, py in zip(ex, ey):
        arr[py, px, :3] = [76, 110, 38]  # warm olive soil

    # Wildflower daisies & poppy flecks
    num_flowers = max(3, size // 16)
    fx_pts = rng.randint(2, size - 2, num_flowers)
    fy_pts = rng.randint(2, size - 2, num_flowers)
    for i, (px, py) in enumerate(zip(fx_pts, fy_pts)):
        if i % 3 == 0:
            # Red/pink poppy dot
            arr[py, px, :3] = [238, 68, 88]
            arr[py - 1, px, :3] = [255, 110, 125]
        else:
            # Daisy with yellow center & 4 white petals
            arr[py - 1, px, :3] = [255, 255, 255]
            arr[py + 1, px, :3] = [255, 255, 255]
            arr[py, px - 1, :3] = [255, 255, 255]
            arr[py, px + 1, :3] = [255, 255, 255]
            arr[py, px, :3] = [255, 220, 35]

    return Image.fromarray(arr)


def create_asphalt_image(size: int = 64, seed: int = 2026) -> Image.Image:
    """Generate dark slate pavement with aggregate stone flecks and subtle tire wear grain."""
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[:size, :size]

    # Base dark slate noise
    base_val = 46.0 + rng.uniform(-5.0, 5.0, (size, size))

    # Tire wear tracks: 2 longitudinal wear bands along Y
    y_rel = y / float(size)
    tire_band1 = np.exp(-((y_rel - 0.28) ** 2) / 0.012)
    tire_band2 = np.exp(-((y_rel - 0.72) ** 2) / 0.012)
    tire_wear = np.maximum(tire_band1, tire_band2) * 11.0

    val = np.clip(base_val - tire_wear, 22, 68)

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = val.astype(np.uint8)
    arr[..., 1] = np.clip(val + 3.0, 0, 255).astype(np.uint8)  # cool slate undertone
    arr[..., 2] = np.clip(val + 8.0, 0, 255).astype(np.uint8)
    arr[..., 3] = 255

    # Aggregate stone flecks: quartz chips, limestone, dark bitumen
    num_flecks = int(size * size * 0.08)
    fx = rng.randint(0, size, num_flecks)
    fy = rng.randint(0, size, num_flecks)
    for px, py in zip(fx, fy):
        c_type = rng.rand()
        if c_type < 0.22:
            # Quartz chip (light gray / white fleck)
            arr[py, px, :3] = [152, 158, 168]
        elif c_type < 0.60:
            # Midtone gravel stone
            arr[py, px, :3] = [98, 104, 114]
        else:
            # Dark bitumen crevice
            arr[py, px, :3] = [26, 28, 32]

    return Image.fromarray(arr)


def create_water_image(size: int = 64, phase: float = 0.0) -> Image.Image:
    """Generate crystal turquoise-blue water with animated wave ripples, caustics, and foam."""
    y, x = np.mgrid[:size, :size]

    # Perfectly periodic frequencies ensuring 100% seamless tiling
    fx = 2.0 * np.pi * 3.0 / size
    fy = 2.0 * np.pi * 3.0 / size

    # Caustic wave interference
    c1 = np.sin(x * fx + phase) * np.cos(y * fy - phase * 0.75)
    c2 = np.sin((x + y) * fx * 0.6 + phase * 1.25) * np.cos((x - y) * fy * 0.6 - phase * 0.65)
    caustics = np.abs(c1 + 0.65 * c2)

    # Base tropical turquoise gradient: deep (20, 142, 178) to bright (36, 196, 226)
    diag = (x + y) / (2.0 * size)
    base_r = 18.0 + 14.0 * diag
    base_g = 144.0 + 26.0 * diag
    base_b = 186.0 + 36.0 * diag

    # Add dynamic caustic highlights
    r = np.clip(base_r + caustics * 62.0, 0, 255)
    g = np.clip(base_g + caustics * 56.0, 0, 255)
    b = np.clip(base_b + caustics * 42.0, 0, 255)

    # Wave crest ripples & foam crests
    crest = np.sin(y * (2.0 * np.pi * 4.0 / size) + np.sin(x * (2.0 * np.pi * 2.0 / size)) + phase * 2.2)
    foam_mask = crest > 0.80
    foam_crest = crest > 0.92

    r[foam_mask] = np.clip(r[foam_mask] + 68.0, 0, 255)
    g[foam_mask] = np.clip(g[foam_mask] + 58.0, 0, 255)
    b[foam_mask] = np.clip(b[foam_mask] + 44.0, 0, 255)

    r[foam_crest] = 238
    g[foam_crest] = 252
    b[foam_crest] = 255

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = r.astype(np.uint8)
    arr[..., 1] = g.astype(np.uint8)
    arr[..., 2] = b.astype(np.uint8)
    arr[..., 3] = 255

    return Image.fromarray(arr)


def create_wood_bark_image(size: int = 64, seed: int = 777) -> Image.Image:
    """Generate warm brown tree bark with vertical wood grain fibers and weathered furrows."""
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[:size, :size]

    # Strong vertical fibers: correlated down columns
    col_noise = rng.uniform(-18.0, 18.0, (1, size))
    col_noise_rep = np.repeat(col_noise, size, axis=0)
    fine_noise = rng.uniform(-7.0, 7.0, (size, size))

    # Vertical furrows spaced periodically
    furrow_freq = 2.0 * np.pi * (size / 8.0) / size
    furrow = np.sin(x * furrow_freq + 0.8 * np.sin(2.0 * np.pi * 2.0 * y / size))
    is_crevice = furrow > 0.70
    is_ridge = (furrow > 0.42) & (~is_crevice)

    base_r = 114.0 + col_noise_rep + fine_noise
    base_g = 72.0 + (col_noise_rep + fine_noise) * 0.65
    base_b = 40.0 + (col_noise_rep + fine_noise) * 0.45

    # Dark crevice shadow
    base_r[is_crevice] = 52
    base_g[is_crevice] = 32
    base_b[is_crevice] = 18

    # Raised ridge highlight
    base_r[is_ridge] += 26.0
    base_g[is_ridge] += 18.0
    base_b[is_ridge] += 12.0

    # Moss/lichen flecks
    num_moss = int(size * size * 0.03)
    mx = rng.randint(0, size, num_moss)
    my = rng.randint(0, size, num_moss)
    for px, py in zip(mx, my):
        if not is_crevice[py, px]:
            base_r[py, px] = 86
            base_g[py, px] = 114
            base_b[py, px] = 56

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = np.clip(base_r, 0, 255).astype(np.uint8)
    arr[..., 1] = np.clip(base_g, 0, 255).astype(np.uint8)
    arr[..., 2] = np.clip(base_b, 0, 255).astype(np.uint8)
    arr[..., 3] = 255

    return Image.fromarray(arr)


def create_wood_rings_image(size: int = 64, seed: int = 888) -> Image.Image:
    """Generate concentric tree growth rings with dark heartwood center and lighter sapwood ring."""
    rng = np.random.RandomState(seed)
    cy, cx = (size - 1.0) / 2.0, (size - 1.0) / 2.0
    y, x = np.mgrid[:size, :size]
    dx = x - cx
    dy = y - cy
    r = np.hypot(dx, dy)
    r_norm = r / (size / 2.0)
    theta = np.arctan2(dy, dx)

    # Subtle organic eccentric wobble
    wobble = 0.035 * np.sin(5.0 * theta) + 0.02 * np.cos(3.0 * theta)
    r_eff = r_norm + wobble

    # Concentric growth rings
    ring_osc = 0.5 + 0.5 * np.sin(r_eff * np.pi * 14.0)

    # Base heartwood alternating latewood & earlywood
    base_r = 132.0 + ring_osc * 44.0
    base_g = 82.0 + ring_osc * 36.0
    base_b = 44.0 + ring_osc * 26.0

    # Dark central heartwood core / pith
    is_pith = r_eff < 0.12
    base_r[is_pith] = 88
    base_g[is_pith] = 48
    base_b[is_pith] = 22

    # Lighter sapwood outer band (0.74 <= r_eff < 0.88)
    is_sapwood = (r_eff >= 0.74) & (r_eff < 0.88)
    base_r[is_sapwood] = 196
    base_g[is_sapwood] = 148
    base_b[is_sapwood] = 98

    # Craggy dark bark outer rim (r_eff >= 0.88)
    is_bark = r_eff >= 0.88
    base_r[is_bark] = 58
    base_g[is_bark] = 35
    base_b[is_bark] = 18

    # Micro grain noise
    noise = rng.uniform(-6.0, 6.0, (size, size))
    base_r += noise
    base_g += noise * 0.7
    base_b += noise * 0.5

    # Radial drying micro-crack
    crack_angle = 0.65
    crack_mask = (np.abs(theta - crack_angle) < 0.05) & (r_eff > 0.1) & (r_eff < 0.76)
    base_r[crack_mask] = 46
    base_g[crack_mask] = 28
    base_b[crack_mask] = 14

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = np.clip(base_r, 0, 255).astype(np.uint8)
    arr[..., 1] = np.clip(base_g, 0, 255).astype(np.uint8)
    arr[..., 2] = np.clip(base_b, 0, 255).astype(np.uint8)
    arr[..., 3] = 255

    return Image.fromarray(arr)


def create_rail_gravel_image(size: int = 64, seed: int = 456) -> Image.Image:
    """Generate coarse railroad stone ballast gravel with multi-tone shaded pebbles."""
    rng = np.random.RandomState(seed)
    arr = np.zeros((size, size, 4), dtype=np.uint8)

    # Deep interstitial shadow crevices
    arr[..., 0] = 34
    arr[..., 1] = 36
    arr[..., 2] = 40
    arr[..., 3] = 255

    # Discrete packed stone pebble grid
    pebble_size = max(3, size // 16)
    cols = (size + pebble_size - 1) // pebble_size
    rows = (size + pebble_size - 1) // pebble_size

    for r in range(rows):
        for c in range(cols):
            x0 = c * pebble_size
            y0 = r * pebble_size
            tone = rng.rand()
            if tone < 0.20:
                mid = np.array([126, 96, 92])   # granite pink
            elif tone < 0.42:
                mid = np.array([136, 132, 118])  # limestone tan
            elif tone < 0.75:
                mid = np.array([106, 112, 120])  # slate gray
            else:
                mid = np.array([76, 80, 88])     # dark basalt

            px0 = x0 + rng.randint(0, 2)
            py0 = y0 + rng.randint(0, 2)
            px1 = min(size, px0 + pebble_size - rng.randint(0, 2))
            py1 = min(size, py0 + pebble_size - rng.randint(0, 2))

            if px1 > px0 and py1 > py0:
                arr[py0:py1, px0:px1, :3] = mid
                # 3D relief: top and left highlight
                high = np.clip(mid + 38, 0, 255)
                arr[py0, px0:px1, :3] = high
                arr[py0:py1, px0, :3] = high
                # 3D relief: bottom and right shadow
                shad = np.clip(mid - 32, 0, 255)
                arr[py1 - 1, px0:px1, :3] = shad
                arr[py0:py1, px1 - 1, :3] = shad

    return Image.fromarray(arr)


def create_gravel_image(size: int = 64, seed: int = 456) -> Image.Image:
    """Alias for create_rail_gravel_image."""
    return create_rail_gravel_image(size=size, seed=seed)


def create_rail_tie_image(size: int = 64, seed: int = 999) -> Image.Image:
    """Generate weathered timber railroad tie with steel tie plates and mounting bolt accents."""
    rng = np.random.RandomState(seed)

    # Weathered timber sleeper: horizontal wood grain
    row_noise = rng.uniform(-14.0, 14.0, (size, 1))
    row_noise_rep = np.repeat(row_noise, size, axis=1)
    fine_noise = rng.uniform(-6.0, 6.0, (size, size))

    timber_r = np.clip(65.0 + row_noise_rep + fine_noise, 30, 110)
    timber_g = np.clip(46.0 + (row_noise_rep + fine_noise) * 0.7, 20, 85)
    timber_b = np.clip(32.0 + (row_noise_rep + fine_noise) * 0.5, 12, 60)

    # Weathered horizontal fissure
    fissure_y = int(size * 0.46)
    timber_r[fissure_y, :] = 32
    timber_g[fissure_y, :] = 22
    timber_b[fissure_y, :] = 14

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = timber_r.astype(np.uint8)
    arr[..., 1] = timber_g.astype(np.uint8)
    arr[..., 2] = timber_b.astype(np.uint8)
    arr[..., 3] = 255

    # Two steel tie plates where rails sit
    pw = max(8, int(size * 0.22))
    ph = max(20, int(size * 0.74))
    py0 = (size - ph) // 2
    py1 = py0 + ph

    p1_x0 = int(size * 0.14)
    p1_x1 = p1_x0 + pw
    p2_x0 = int(size * 0.64)
    p2_x1 = p2_x0 + pw

    for px0, px1 in [(p1_x0, p1_x1), (p2_x0, p2_x1)]:
        # Plate body: steel gray (108, 116, 126)
        arr[py0:py1, px0:px1, :3] = [108, 116, 126]
        # Top and left highlight bevel
        arr[py0, px0:px1, :3] = [156, 166, 178]
        arr[py0:py1, px0, :3] = [156, 166, 178]
        # Bottom and right shadow bevel
        arr[py1 - 1, px0:px1, :3] = [62, 68, 76]
        arr[py0:py1, px1 - 1, :3] = [62, 68, 76]

        # 4 Mounting bolts / spikes
        bolt_inset = max(2, int(pw * 0.20))
        bolt_coords = [
            (px0 + bolt_inset, py0 + bolt_inset),
            (px1 - 1 - bolt_inset, py0 + bolt_inset),
            (px0 + bolt_inset, py1 - 1 - bolt_inset),
            (px1 - 1 - bolt_inset, py1 - 1 - bolt_inset),
        ]
        bolt_rad = max(1, size // 64)
        for bx, by in bolt_coords:
            arr[by : by + bolt_rad, bx : bx + bolt_rad, :3] = [192, 202, 218]
            if by + bolt_rad < size:
                arr[by + bolt_rad, bx : bx + bolt_rad, :3] = [38, 42, 50]

    return Image.fromarray(arr)


def create_car_grille_image(size: int = 64, seed: int = 321) -> Image.Image:
    """Generate vehicle radiator grille and tinted windshield/windows detailing."""
    arr = np.zeros((size, size, 4), dtype=np.uint8)

    h_windshield = int(size * 0.42)
    h_hood = int(size * 0.52)
    h_grille_bottom = int(size * 0.88)

    # 1. Windshield: reflective cyan tinted glass
    arr[:h_windshield, :, 0] = 24
    arr[:h_windshield, :, 1] = 46
    arr[:h_windshield, :, 2] = 66
    arr[:h_windshield, :, 3] = 255

    # Diagonal glare streaks across windshield
    y_ws, x_ws = np.mgrid[:h_windshield, :size]
    glare1 = np.abs((x_ws - y_ws * 1.5) - int(size * 0.2)) < max(1, size // 32)
    glare2 = np.abs((x_ws - y_ws * 1.5) - int(size * 0.5)) < max(2, size // 20)
    arr[:h_windshield, :][glare1, :3] = [86, 146, 186]
    arr[:h_windshield, :][glare2, :3] = [206, 236, 255]

    # Windshield rubber seal
    arr[0, :, :3] = [18, 20, 24]
    arr[h_windshield - 1, :, :3] = [18, 20, 24]
    arr[:h_windshield, 0, :3] = [18, 20, 24]
    arr[:h_windshield, size - 1, :3] = [18, 20, 24]

    # 2. Hood / Chrome Trim divider
    arr[h_windshield:h_hood, :, 0] = 196
    arr[h_windshield:h_hood, :, 1] = 202
    arr[h_windshield:h_hood, :, 2] = 212
    arr[h_windshield:h_hood, :, 3] = 255
    cx = size // 2
    emblem_w = max(2, size // 16)
    arr[h_windshield + 1 : h_hood - 1, cx - emblem_w : cx + emblem_w, :3] = [242, 212, 62]

    # 3. Grille and Headlights
    for cy in range(h_hood, h_grille_bottom):
        slat = (cy % 3 == 0)
        col = [22, 24, 28] if slat else [50, 54, 62]
        arr[cy, :, :3] = col
        arr[cy, :, 3] = 255

    gx0 = int(size * 0.25)
    gx1 = int(size * 0.75)
    for px in range(gx0, gx1, max(3, size // 16)):
        arr[h_hood:h_grille_bottom, px, :3] = [142, 152, 166]

    hl_w = max(6, int(size * 0.16))
    hl_left_x0 = int(size * 0.06)
    hl_left_x1 = hl_left_x0 + hl_w
    hl_right_x1 = size - int(size * 0.06)
    hl_right_x0 = hl_right_x1 - hl_w

    hl_y0 = h_hood + max(2, int(size * 0.05))
    hl_y1 = h_grille_bottom - max(2, int(size * 0.05))

    for hx0, hx1 in [(hl_left_x0, hl_left_x1), (hl_right_x0, hl_right_x1)]:
        arr[hl_y0:hl_y1, hx0:hx1, :3] = [172, 182, 196]
        arr[hl_y0 + 1 : hl_y1 - 1, hx0 + 1 : hx1 - 1, :3] = [255, 248, 176]
        sig_w = max(1, (hx1 - hx0) // 3)
        if hx0 == hl_left_x0:
            arr[hl_y0 + 1 : hl_y1 - 1, hx0 + 1 : hx0 + 1 + sig_w, :3] = [255, 142, 16]
        else:
            arr[hl_y0 + 1 : hl_y1 - 1, hx1 - 1 - sig_w : hx1 - 1, :3] = [255, 142, 16]

    # 4. Bumper
    arr[h_grille_bottom:, :, 0] = 42
    arr[h_grille_bottom:, :, 1] = 46
    arr[h_grille_bottom:, :, 2] = 52
    arr[h_grille_bottom:, :, 3] = 255
    arr[h_grille_bottom, :, :3] = [162, 172, 186]

    return Image.fromarray(arr)


def create_vehicle_image(size: int = 64, seed: int = 321) -> Image.Image:
    """Alias for create_car_grille_image."""
    return create_car_grille_image(size=size, seed=seed)


def create_duck_image(size: int = 64, seed: int = 4242) -> Image.Image:
    """Generate authentic stylized voxel duck plumage/feather texture.

    Creates a warm, radiant golden-yellow down feather pattern with soft
    quilted micro-voxel scallops, subtle sunlight highlights, and depth shading.
    Face elements (eyes, bill) are modeled as discrete 3D voxel geometry
    to ensure 100% distortion-free rendering across all 6 faces of 3D boxes.
    """
    rng = np.random.RandomState(seed)
    arr = np.zeros((size, size, 4), dtype=np.uint8)

    # 1. Base vibrant duck plumage yellow (#fbc02d / #f59e0b)
    arr[..., 0] = 252  # R
    arr[..., 1] = 208  # G
    arr[..., 2] = 24   # B
    arr[..., 3] = 255  # A

    # 2. Procedural feather scallop down pattern
    y, x = np.mgrid[:size, :size]
    freq_x = 2.0 * np.pi * 4.0 / size
    freq_y = 2.0 * np.pi * 6.0 / size
    # Subtle scalloped feather waves
    scallop = np.sin(x * freq_x + np.cos(y * freq_y * 0.5) * 0.8) * np.cos(y * freq_y)

    # 3. Soft highlights on crown of feathers (#fff176 / #fef08a)
    high_mask = scallop > 0.40
    arr[high_mask, 0] = 255
    arr[high_mask, 1] = 236
    arr[high_mask, 2] = 92

    # 4. Rich warm shadow between feather rows (#d97706 / #e69500)
    shade_mask = scallop < -0.40
    arr[shade_mask, 0] = 230
    arr[shade_mask, 1] = 165
    arr[shade_mask, 2] = 10

    # 5. Micro-grain voxel texture variation for authentic arcade feel
    grain = rng.uniform(-4.0, 4.0, (size, size))
    for c in range(3):
        arr[..., c] = np.clip(arr[..., c].astype(float) + grain, 0, 255).astype(np.uint8)

    return Image.fromarray(arr)


def create_tree_leaves_image(size: int = 64, seed: int = 555) -> Image.Image:
    """Generate lush stylized voxel tree foliage canopy texture."""
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[:size, :size]

    fx = 2.0 * np.pi * 3.0 / size
    fy = 2.0 * np.pi * 3.0 / size
    harmonic = np.sin(x * fx) * np.cos(y * fy)

    base_r = 45.0 + harmonic * 20.0 + rng.uniform(-6, 6, (size, size))
    base_g = 155.0 + harmonic * 35.0 + rng.uniform(-8, 8, (size, size))
    base_b = 35.0 + harmonic * 18.0 + rng.uniform(-5, 5, (size, size))

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = np.clip(base_r, 0, 255).astype(np.uint8)
    arr[..., 1] = np.clip(base_g, 0, 255).astype(np.uint8)
    arr[..., 2] = np.clip(base_b, 0, 255).astype(np.uint8)
    arr[..., 3] = 255

    return Image.fromarray(arr)


def create_lilypad_image(size: int = 64) -> Image.Image:
    """Generate floating tropical lily pad texture with notch and water drop."""
    cy, cx = (size - 1.0) / 2.0, (size - 1.0) / 2.0
    y, x = np.mgrid[:size, :size]
    dx = x - cx
    dy = y - cy
    r = np.hypot(dx, dy)
    r_norm = r / (size / 2.0)
    theta = np.arctan2(dy, dx)

    # Base turquoise water background
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = 24
    arr[..., 1] = 152
    arr[..., 2] = 188
    arr[..., 3] = 255

    is_pad = r_norm < 0.88
    # V-shaped notch on right
    is_notch = (np.abs(theta) < 0.35) & (r_norm > 0.12)
    is_leaf = is_pad & (~is_notch)

    # Leaf body
    arr[is_leaf, 0] = 52
    arr[is_leaf, 1] = 168
    arr[is_leaf, 2] = 58
    arr[is_leaf, 3] = 255

    # Lighter rim edge
    is_rim = is_leaf & (r_norm > 0.80)
    arr[is_rim, 0] = 95
    arr[is_rim, 1] = 208
    arr[is_rim, 2] = 88

    # Dew drop
    drop_x = int(cx - size * 0.18)
    drop_y = int(cy - size * 0.18)
    drop_r = max(1, size // 32)
    arr[drop_y - drop_r : drop_y + drop_r + 1, drop_x - drop_r : drop_x + drop_r + 1, :3] = [235, 250, 255]

    return Image.fromarray(arr)


# -----------------------------------------------------------------------------
# Module-level raw RGBA bytes generators conforming to TextureGeneratorContract
# -----------------------------------------------------------------------------

def generate_grass_texture(size: int = 64) -> bytes:
    """Generate lush multi-tone voxel grass texture RGBA bytes."""
    return create_grass_image(size=size).tobytes("raw", "RGBA")


def generate_asphalt_texture(size: int = 64) -> bytes:
    """Generate gritty asphalt pavement texture RGBA bytes with aggregate flecks."""
    return create_asphalt_image(size=size).tobytes("raw", "RGBA")


def generate_water_texture(size: int = 64, phase: float = 0.0) -> bytes:
    """Generate crystal water texture RGBA bytes with wave caustics & ripples."""
    return create_water_image(size=size, phase=phase).tobytes("raw", "RGBA")


def generate_wood_bark_texture(size: int = 64) -> bytes:
    """Generate vertical timber grain texture RGBA bytes for trunks and logs."""
    return create_wood_bark_image(size=size).tobytes("raw", "RGBA")


def generate_wood_rings_texture(size: int = 64) -> bytes:
    """Generate concentric tree growth rings RGBA bytes for cut log ends."""
    return create_wood_rings_image(size=size).tobytes("raw", "RGBA")


def generate_gravel_texture(size: int = 64) -> bytes:
    """Generate railroad stone ballast gravel texture RGBA bytes."""
    return create_rail_gravel_image(size=size).tobytes("raw", "RGBA")


def generate_rail_gravel_texture(size: int = 64) -> bytes:
    """Generate railroad stone ballast gravel texture RGBA bytes."""
    return create_rail_gravel_image(size=size).tobytes("raw", "RGBA")


def generate_rail_tie_texture(size: int = 64) -> bytes:
    """Generate rustic treated railroad timber tie texture RGBA bytes."""
    return create_rail_tie_image(size=size).tobytes("raw", "RGBA")


def generate_car_grille_texture(size: int = 64) -> bytes:
    """Generate vehicle radiator grille and window tinting RGBA bytes."""
    return create_car_grille_image(size=size).tobytes("raw", "RGBA")


def generate_vehicle_texture(size: int = 64) -> bytes:
    """Generate vehicle radiator grille and window tinting RGBA bytes."""
    return create_car_grille_image(size=size).tobytes("raw", "RGBA")


def generate_duck_texture(size: int = 64) -> bytes:
    """Generate adorable voxel duck feather pattern RGBA bytes."""
    return create_duck_image(size=size).tobytes("raw", "RGBA")


def generate_tree_leaves_texture(size: int = 64) -> bytes:
    """Generate stylized tree foliage RGBA bytes."""
    return create_tree_leaves_image(size=size).tobytes("raw", "RGBA")


def generate_lilypad_texture(size: int = 64) -> bytes:
    """Generate floating tropical lily pad RGBA bytes."""
    return create_lilypad_image(size=size).tobytes("raw", "RGBA")


# -----------------------------------------------------------------------------
# CrossyTextureGenerator Class (adheres to TextureGeneratorContract)
# -----------------------------------------------------------------------------

class CrossyTextureGenerator(TextureGeneratorContract):
    """Procedural stylized texture generator implementing TextureGeneratorContract."""

    @staticmethod
    def generate_grass_texture(size: int = 64) -> bytes:
        return generate_grass_texture(size=size)

    @staticmethod
    def generate_asphalt_texture(size: int = 64) -> bytes:
        return generate_asphalt_texture(size=size)

    @staticmethod
    def generate_water_texture(size: int = 64, phase: float = 0.0) -> bytes:
        return generate_water_texture(size=size, phase=phase)

    @staticmethod
    def generate_wood_bark_texture(size: int = 64) -> bytes:
        return generate_wood_bark_texture(size=size)

    @staticmethod
    def generate_wood_rings_texture(size: int = 64) -> bytes:
        return generate_wood_rings_texture(size=size)

    @staticmethod
    def generate_gravel_texture(size: int = 64) -> bytes:
        return generate_gravel_texture(size=size)

    @staticmethod
    def generate_rail_tie_texture(size: int = 64) -> bytes:
        return generate_rail_tie_texture(size=size)

    # Extended generators for vehicles, duck, and foliage
    @staticmethod
    def generate_rail_gravel_texture(size: int = 64) -> bytes:
        return generate_rail_gravel_texture(size=size)

    @staticmethod
    def generate_car_grille_texture(size: int = 64) -> bytes:
        return generate_car_grille_texture(size=size)

    @staticmethod
    def generate_vehicle_texture(size: int = 64) -> bytes:
        return generate_vehicle_texture(size=size)

    @staticmethod
    def generate_duck_texture(size: int = 64) -> bytes:
        return generate_duck_texture(size=size)

    @staticmethod
    def generate_tree_leaves_texture(size: int = 64) -> bytes:
        return generate_tree_leaves_texture(size=size)

    @staticmethod
    def generate_lilypad_texture(size: int = 64) -> bytes:
        return generate_lilypad_texture(size=size)

    @classmethod
    def create_image(cls, name: str, size: int = 64, phase: float = 0.0) -> Image.Image:
        """Create a PIL RGBA Image by identifier name."""
        clean = name.lower().strip()
        if clean in ("grass", "lawn", "meadow"):
            return create_grass_image(size=size)
        elif clean in ("asphalt", "road", "pavement"):
            return create_asphalt_image(size=size)
        elif clean in ("water", "river", "ocean"):
            return create_water_image(size=size, phase=phase)
        elif clean in ("wood_bark", "bark", "log_side", "trunk"):
            return create_wood_bark_image(size=size)
        elif clean in ("wood_rings", "rings", "log_end", "stump"):
            return create_wood_rings_image(size=size)
        elif clean in ("rail_gravel", "gravel", "ballast", "stone"):
            return create_rail_gravel_image(size=size)
        elif clean in ("rail_tie", "tie", "sleeper"):
            return create_rail_tie_image(size=size)
        elif clean in ("car_grille", "vehicle", "car", "truck"):
            return create_car_grille_image(size=size)
        elif clean in ("duck", "feathers", "player"):
            return create_duck_image(size=size)
        elif clean in ("tree_leaves", "leaves", "foliage"):
            return create_tree_leaves_image(size=size)
        elif clean in ("lilypad", "pad"):
            return create_lilypad_image(size=size)
        else:
            raise ValueError(f"Unknown texture name '{name}'")


TextureGenerator = CrossyTextureGenerator  # Ergonomic alias


# -----------------------------------------------------------------------------
# Asset Generation & Export Function
# -----------------------------------------------------------------------------

def ensure_textures_generated(assets_dir: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """Export all stylized procedural textures to assets/textures/*.png and raw RGBA files.

    Generates textures in both 64x64 and 128x128 resolutions, saves PNG files,
    exports raw .rgba byte buffers, and returns a comprehensive dictionary of filepaths.
    """
    if assets_dir is None:
        # Default to repo root assets/textures
        repo_root = Path(__file__).resolve().parent.parent.parent
        out_dir = repo_root / "assets" / "textures"
    else:
        out_dir = Path(assets_dir)

    out_dir.mkdir(parents=True, exist_ok=True)

    texture_names = [
        "grass",
        "asphalt",
        "water",
        "wood_bark",
        "wood_rings",
        "rail_gravel",
        "rail_tie",
        "car_grille",
        "duck",
        "tree_leaves",
        "lilypad",
    ]

    filepaths: Dict[str, str] = {}

    for name in texture_names:
        for size in (64, 128):
            img = CrossyTextureGenerator.create_image(name, size=size)
            png_name = f"{name}_{size}.png"
            png_path = out_dir / png_name
            img.save(png_path, format="PNG")

            # Export raw RGBA bytes file
            rgba_bytes = img.tobytes("raw", "RGBA")
            rgba_name = f"{name}_{size}.rgba"
            rgba_path = out_dir / rgba_name
            with open(rgba_path, "wb") as f:
                f.write(rgba_bytes)

            filepaths[f"{name}_{size}"] = str(png_path)
            filepaths[f"{name}_{size}_rgba"] = str(rgba_path)

            # Default canonical entry points to 64x64 voxel resolution
            if size == 64:
                canonical_png = out_dir / f"{name}.png"
                img.save(canonical_png, format="PNG")
                canonical_rgba = out_dir / f"{name}.rgba"
                with open(canonical_rgba, "wb") as f:
                    f.write(rgba_bytes)
                filepaths[name] = str(canonical_png)
                filepaths[f"{name}_rgba"] = str(canonical_rgba)

    # Register convenient aliases
    filepaths["gravel"] = filepaths["rail_gravel"]
    filepaths["gravel_64"] = filepaths["rail_gravel_64"]
    filepaths["gravel_128"] = filepaths["rail_gravel_128"]
    filepaths["vehicle"] = filepaths["car_grille"]
    filepaths["vehicle_64"] = filepaths["car_grille_64"]
    filepaths["vehicle_128"] = filepaths["car_grille_128"]

    return filepaths


# -----------------------------------------------------------------------------
# Texture & Material Registry (adheres to MaterialPaletteContract)
# -----------------------------------------------------------------------------

class TextureRegistry(MaterialPaletteContract):
    """Central registry caching VelocityEngine Texture and StylizedMaterial instances.

    Adheres strictly to MaterialPaletteContract:
      - provides cached Material access via get_material(name)
      - advances time-based texture coordinates via update_animated_materials(dt)
      - supports pixel-art voxel nearest filtering and PBR roughness/metallic tuning
    """

    def __init__(self, assets_dir: Optional[Union[str, Path]] = None, is_pixel_art: bool = True) -> None:
        if assets_dir is None:
            repo_root = Path(__file__).resolve().parent.parent.parent
            self.assets_dir = repo_root / "assets" / "textures"
        else:
            self.assets_dir = Path(assets_dir)

        self.is_pixel_art = is_pixel_art
        self.materials: Dict[str, Any] = {}
        self.textures: Dict[str, Any] = {}
        self.raw_buffers: Dict[str, bytes] = {}
        self.images: Dict[str, Image.Image] = {}
        self.water_phase: float = 0.0

        # Ensure directory and core textures exist
        self.texture_paths = ensure_textures_generated(self.assets_dir)

    def get_texture_path(self, name: str, size: int = 64) -> str:
        """Fetch absolute path of the generated PNG texture."""
        canonical = self._normalize_name(name)
        key = f"{canonical}_{size}" if f"{canonical}_{size}" in self.texture_paths else canonical
        if key in self.texture_paths:
            return self.texture_paths[key]
        png_path = self.assets_dir / f"{canonical}_{size}.png"
        return str(png_path)

    def get_image(self, name: str, size: int = 64, phase: float = 0.0) -> Image.Image:
        """Get or dynamically generate a PIL RGBA Image."""
        canonical = self._normalize_name(name)
        cache_key = f"{canonical}_{size}"
        if canonical == "water":
            # Dynamic wave phase
            return create_water_image(size=size, phase=phase)
        if cache_key in self.images:
            return self.images[cache_key]
        img = CrossyTextureGenerator.create_image(canonical, size=size, phase=phase)
        self.images[cache_key] = img
        return img

    def get_raw_bytes(self, name: str, size: int = 64, phase: float = 0.0) -> bytes:
        """Get or dynamically generate 4-channel RGBA byte buffer."""
        canonical = self._normalize_name(name)
        cache_key = f"{canonical}_{size}"
        if canonical == "water":
            return generate_water_texture(size=size, phase=phase)
        if cache_key in self.raw_buffers:
            return self.raw_buffers[cache_key]
        img = self.get_image(canonical, size=size, phase=phase)
        b = img.tobytes("raw", "RGBA")
        self.raw_buffers[cache_key] = b
        return b

    def get_texture(self, name: str, size: int = 64, phase: float = 0.0) -> Any:
        """Fetch or load a cached VelocityEngine Texture object."""
        canonical = self._normalize_name(name)
        cache_key = f"{canonical}_{size}"

        if canonical != "water" and cache_key in self.textures:
            return self.textures[cache_key]

        path = self.get_texture_path(canonical, size=size)
        if not os.path.isfile(path):
            ensure_textures_generated(self.assets_dir)

        if Texture is not None and hasattr(Texture, "load_from_file"):
            try:
                tex = Texture.load_from_file(str(path))
            except Exception:
                tex = None
        else:
            tex = None

        if tex is not None:
            self.textures[cache_key] = tex
            return tex

        # Fallback dummy texture holder if native engine is absent or headless
        class FallbackTexture:
            def __init__(self, w: int, h: int, p: str) -> None:
                self.width = w
                self.height = h
                self.channels = 4
                self.filepath = p
                self.is_pixel_art = True

            def is_valid(self) -> bool:
                return True

        fb_tex = FallbackTexture(size, size, str(path))
        self.textures[cache_key] = fb_tex
        return fb_tex

    def get_material(self, name: str, uv_scale: Optional[Tuple[float, float]] = None) -> Any:
        """Fetch or instantiate a cached stylized Material object with tuned PBR properties."""
        canonical = self._normalize_name(name)
        cache_key = canonical if uv_scale is None else f"{canonical}_{uv_scale[0]}_{uv_scale[1]}"
        if cache_key in self.materials:
            return self.materials[cache_key]

        config = MATERIAL_PRESETS.get(canonical, MaterialConfig(name=canonical))
        tex = self.get_texture(canonical, size=64)

        effective_uv = uv_scale if uv_scale is not None else config.uv_scale
        mat = StylizedMaterial(
            texture=tex,
            roughness=config.roughness,
            metallic=config.metallic,
            is_pixel_art=self.is_pixel_art,
            uv_scale=effective_uv,
            name=canonical,
        )

        if hasattr(mat, "set_color"):
            mat.set_color(*config.base_color)

        self.materials[cache_key] = mat
        if uv_scale is None and canonical not in self.materials:
            self.materials[canonical] = mat
        return mat

    def update_animated_materials(self, dt: float) -> None:
        """Advance time-based texture coordinates (e.g. flowing water ripples)."""
        self.water_phase = (self.water_phase + dt * 2.5) % (2.0 * math.pi)
        u_scroll = (self.water_phase / (2.0 * math.pi))

        # Update water materials
        for key, water_mat in list(self.materials.items()):
            if "water" in key:
                if hasattr(water_mat, "set_uv_offset"):
                    water_mat.set_uv_offset(u_scroll, 0.0)
                elif hasattr(water_mat, "set_uv_scale"):
                    u_scroll_subtle = u_scroll * 0.2
                    water_mat.set_uv_scale(water_mat.uv_scale[0] + u_scroll_subtle, water_mat.uv_scale[1])

    @staticmethod
    def _normalize_name(name: str) -> str:
        clean = name.lower().strip()
        alias_map = {
            "gravel": "rail_gravel",
            "vehicle": "car_grille",
            "car": "car_grille",
            "truck": "car_grille",
            "lawn": "grass",
            "meadow": "grass",
            "road": "asphalt",
            "pavement": "asphalt",
            "river": "water",
            "ocean": "water",
            "bark": "wood_bark",
            "log_side": "wood_bark",
            "trunk": "wood_bark",
            "rings": "wood_rings",
            "log_end": "wood_rings",
            "stump": "wood_rings",
            "sleeper": "rail_tie",
            "tie": "rail_tie",
            "feathers": "duck",
            "player": "duck",
            "leaves": "tree_leaves",
            "pad": "lilypad",
        }
        return alias_map.get(clean, clean)


# Unified alias for MaterialRegistry
MaterialRegistry = TextureRegistry

__all__ = [
    "MaterialConfig",
    "MATERIAL_PRESETS",
    "StylizedMaterial",
    "create_grass_image",
    "create_asphalt_image",
    "create_water_image",
    "create_wood_bark_image",
    "create_wood_rings_image",
    "create_rail_gravel_image",
    "create_gravel_image",
    "create_rail_tie_image",
    "create_car_grille_image",
    "create_vehicle_image",
    "create_duck_image",
    "create_tree_leaves_image",
    "create_lilypad_image",
    "generate_grass_texture",
    "generate_asphalt_texture",
    "generate_water_texture",
    "generate_wood_bark_texture",
    "generate_wood_rings_texture",
    "generate_gravel_texture",
    "generate_rail_gravel_texture",
    "generate_rail_tie_texture",
    "generate_car_grille_texture",
    "generate_vehicle_texture",
    "generate_duck_texture",
    "generate_tree_leaves_texture",
    "generate_lilypad_texture",
    "CrossyTextureGenerator",
    "TextureGenerator",
    "ensure_textures_generated",
    "TextureRegistry",
    "MaterialRegistry",
]
