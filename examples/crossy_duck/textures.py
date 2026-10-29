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
        name="car_paint",
        roughness=0.22,
        metallic=0.20,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "car_cabin": MaterialConfig(
        name="car_cabin",
        roughness=0.12,
        metallic=0.10,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "car_wheel": MaterialConfig(
        name="car_wheel",
        roughness=0.55,
        metallic=0.45,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "truck_cargo": MaterialConfig(
        name="truck_cargo",
        roughness=0.60,
        metallic=0.20,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "train_body": MaterialConfig(
        name="train_body",
        roughness=0.20,
        metallic=0.35,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "train_window": MaterialConfig(
        name="train_window",
        roughness=0.15,
        metallic=0.10,
        base_color=(1.0, 1.0, 1.0, 1.0),
        uv_scale=(1.0, 1.0),
        is_pixel_art=True,
    ),
    "train_front": MaterialConfig(
        name="train_front",
        roughness=0.25,
        metallic=0.40,
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


CORE_TEXTURE_NAMES = [
    "grass",
    "asphalt",
    "water",
    "wood_bark",
    "wood_rings",
    "rail_gravel",
    "rail_tie",
    "car_grille",
    "duck",
    "car_paint",
    "car_cabin",
    "car_wheel",
    "truck_cargo",
    "train_body",
    "train_window",
    "train_front",
]

EXTENDED_TEXTURE_NAMES = CORE_TEXTURE_NAMES + ["tree_leaves", "lilypad"]


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


def create_car_paint_image(size: int = 64, seed: int = 101) -> Image.Image:
    """Generate glossy automotive car paint with clearcoat sheen, micro-flakes, and panel bevel."""
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[:size, :size]

    # Neutral high-key pearl/metallic silver-white base for universal tintability
    vert_grad = 1.0 - (y / float(size)) * 0.12
    base_luma = 232.0 * vert_grad

    # Metallic micro-flakes (+/- 4.5)
    flakes = rng.uniform(-4.5, 4.5, (size, size))

    # Subtle diagonal clear-coat highlight streak across body
    diag = (x * 0.7 + y * 0.3) / float(size)
    clearcoat = 14.0 * np.exp(-((diag - 0.45) ** 2) / 0.04)

    luma = np.clip(base_luma + flakes + clearcoat, 0, 255)

    arr = np.zeros((size, size, 4), dtype=np.uint8)
    arr[..., 0] = np.clip(luma - 1.0, 0, 255).astype(np.uint8)  # slight cool pearl undertone
    arr[..., 1] = np.clip(luma, 0, 255).astype(np.uint8)
    arr[..., 2] = np.clip(luma + 3.0, 0, 255).astype(np.uint8)
    arr[..., 3] = 255

    # Top & Left bevel specular highlight (car panel edge reflection)
    bevel_w = max(1, size // 32)
    arr[:bevel_w, :, :3] = [255, 255, 255]
    arr[:, :bevel_w, :3] = [255, 255, 255]

    # Bottom & Right subtle ambient occlusion shadow
    arr[-bevel_w:, :, :3] = np.clip(arr[-bevel_w:, :, :3].astype(int) - 38, 0, 255).astype(np.uint8)
    arr[:, -bevel_w:, :3] = np.clip(arr[:, -bevel_w:, :3].astype(int) - 38, 0, 255).astype(np.uint8)

    # Stylized panel seam / shutline near lower quarter
    seam_y = int(size * 0.78)
    if 0 <= seam_y < size:
        arr[seam_y, :, :3] = [170, 175, 185]
        if seam_y + 1 < size:
            arr[seam_y + 1, :, :3] = [252, 252, 255]

    return Image.fromarray(arr)


def create_car_cabin_image(size: int = 64, seed: int = 202) -> Image.Image:
    """Generate tinted cyan/charcoal automotive glass with diagonal glare streaks and seals."""
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    y, x = np.mgrid[:size, :size]

    # Base tinted charcoal glass with cyan depth undertone
    y_norm = y / float(size)
    r_base = 22.0 + y_norm * 14.0
    g_base = 38.0 + y_norm * 22.0
    b_base = 56.0 + y_norm * 28.0

    arr[..., 0] = np.clip(r_base, 0, 255).astype(np.uint8)
    arr[..., 1] = np.clip(g_base, 0, 255).astype(np.uint8)
    arr[..., 2] = np.clip(b_base, 0, 255).astype(np.uint8)
    arr[..., 3] = 255

    # Diagonal glare streaks across the glass
    dist1 = np.abs((x - y * 1.2) - int(size * 0.25))
    glare1_core = dist1 < max(1, size // 32)
    glare1_glow = (dist1 < max(2, size // 16)) & (~glare1_core)
    arr[glare1_glow, 0] = 85
    arr[glare1_glow, 1] = 160
    arr[glare1_glow, 2] = 210
    arr[glare1_core, 0] = 215
    arr[glare1_core, 1] = 245
    arr[glare1_core, 2] = 255

    dist2 = np.abs((x - y * 1.2) - int(size * 0.65))
    glare2_core = dist2 < max(1, size // 32)
    glare2_glow = (dist2 < max(2, size // 18)) & (~glare2_core)
    arr[glare2_glow, 0] = 70
    arr[glare2_glow, 1] = 140
    arr[glare2_glow, 2] = 185
    arr[glare2_core, 0] = 180
    arr[glare2_core, 1] = 225
    arr[glare2_core, 2] = 248

    # A/B Pillar: vertical structural window divider
    pillar_x = int(size * 0.44)
    pillar_w = max(2, size // 24)
    arr[:, pillar_x : pillar_x + pillar_w, :3] = [28, 32, 40]
    arr[:, pillar_x, :3] = [58, 64, 76]

    # Dark perimeter rubber weatherstrip / window seal
    seal_w = max(1, size // 32)
    arr[:seal_w, :, :3] = [18, 20, 26]
    arr[-seal_w:, :, :3] = [18, 20, 26]
    arr[:, :seal_w, :3] = [18, 20, 26]
    arr[:, -seal_w:, :3] = [18, 20, 26]

    return Image.fromarray(arr)


def create_car_wheel_image(size: int = 64, seed: int = 303) -> Image.Image:
    """Generate dark rubber tire tread with metallic alloy rim/hubcap in center."""
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    cy, cx = (size - 1.0) / 2.0, (size - 1.0) / 2.0
    y, x = np.mgrid[:size, :size]
    dx = x - cx
    dy = y - cy
    r = np.hypot(dx, dy)
    r_norm = r / (size / 2.0)
    theta = np.arctan2(dy, dx)

    # Base rubber tire background (dark charcoal)
    arr[..., 0] = 30
    arr[..., 1] = 32
    arr[..., 2] = 36
    arr[..., 3] = 255

    # Outer tire tread pattern (16-lug radial tread blocks)
    tread_mask = (r_norm >= 0.72) & (r_norm <= 0.98)
    tread_groove = (np.sin(theta * 16.0) > 0.65) & tread_mask
    arr[tread_mask, :3] = [40, 43, 48]
    arr[tread_groove, :3] = [16, 18, 22]

    # Tire sidewall
    sidewall = (r_norm >= 0.56) & (r_norm < 0.72)
    arr[sidewall, :3] = [34, 36, 42]

    # Metallic rim outer lip (r_norm 0.46 to 0.56)
    rim_lip = (r_norm >= 0.46) & (r_norm < 0.56)
    arr[rim_lip, :3] = [170, 178, 192]
    highlight_lip = rim_lip & (theta > -2.4) & (theta < -0.7)
    arr[highlight_lip, :3] = [230, 238, 248]
    shadow_lip = rim_lip & (theta > 0.7) & (theta < 2.4)
    arr[shadow_lip, :3] = [105, 112, 122]

    # Inner wheel well / brake cavity (r_norm 0.22 to 0.46)
    cavity = (r_norm >= 0.22) & (r_norm < 0.46)
    arr[cavity, :3] = [38, 42, 50]

    # 5-spoke stylized alloy star
    spoke_angle = (theta + np.pi) % (2.0 * np.pi / 5.0) - (np.pi / 5.0)
    is_spoke = cavity & (np.abs(spoke_angle) < 0.22)
    arr[is_spoke, :3] = [205, 215, 228]
    spoke_bevel = is_spoke & (spoke_angle < -0.08)
    arr[spoke_bevel, :3] = [240, 246, 255]

    # Metallic Center Hubcap (r_norm < 0.22)
    hubcap = r_norm < 0.22
    arr[hubcap, :3] = [185, 195, 210]
    hubcap_rim = (r_norm >= 0.18) & (r_norm < 0.22)
    arr[hubcap_rim, :3] = [140, 148, 160]

    # Central axle nut
    axle_nut = r_norm < 0.08
    arr[axle_nut, :3] = [45, 50, 60]

    # 5 Lug nuts around hubcap center
    for i in range(5):
        angle = i * (2.0 * np.pi / 5.0)
        bx = int(cx + np.cos(angle) * (size * 0.13))
        by = int(cy + np.sin(angle) * (size * 0.13))
        rad = max(1, size // 48)
        arr[max(0, by - rad) : min(size, by + rad + 1), max(0, bx - rad) : min(size, bx + rad + 1), :3] = [245, 250, 255]

    return Image.fromarray(arr)


def create_truck_cargo_image(size: int = 64, seed: int = 404) -> Image.Image:
    """Generate industrial corrugated shipping container siding with crisp vertical shadows."""
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[:size, :size]
    arr = np.zeros((size, size, 4), dtype=np.uint8)

    base_r = 222.0
    base_g = 228.0
    base_b = 236.0

    # Vertical corrugated ribs
    flute_width = max(4, size // 8)
    flute_pos = (x % flute_width).astype(float) / flute_width

    is_crevice = flute_pos < 0.22
    is_highlight = flute_pos > 0.78

    shade = np.zeros((size, size), dtype=float)
    shade[is_crevice] = -68.0
    shade[is_highlight] = 26.0

    # Subtle horizontal crease across mid-height
    mid_y = size // 2
    crease_mask = np.abs(y - mid_y) <= max(1, size // 48)
    shade[crease_mask] -= 18.0

    # Industrial steel grain noise
    grain = rng.uniform(-3.5, 3.5, (size, size))

    r = np.clip(base_r + shade + grain, 0, 255)
    g = np.clip(base_g + shade + grain, 0, 255)
    b = np.clip(base_b + shade * 0.9 + grain, 0, 255)

    arr[..., 0] = r.astype(np.uint8)
    arr[..., 1] = g.astype(np.uint8)
    arr[..., 2] = b.astype(np.uint8)
    arr[..., 3] = 255

    # Top & bottom heavy industrial perimeter rails
    rail_h = max(2, int(size * 0.08))
    arr[:rail_h, :, 0] = 188
    arr[:rail_h, :, 1] = 196
    arr[:rail_h, :, 2] = 206
    arr[rail_h - 1, :, :3] = [135, 145, 158]

    arr[-rail_h:, :, 0] = 165
    arr[-rail_h:, :, 1] = 175
    arr[-rail_h:, :, 2] = 186
    arr[-rail_h, :, :3] = [245, 250, 255]

    # Left & right structural corner posts
    post_w = max(2, int(size * 0.06))
    arr[:, :post_w, :3] = [178, 186, 198]
    arr[:, post_w - 1, :3] = [120, 130, 145]
    arr[:, -post_w:, :3] = [178, 186, 198]
    arr[:, -post_w, :3] = [245, 250, 255]

    # Stencil hazard/ISO label plate on right panel
    tag_w = max(4, int(size * 0.16))
    tag_h = max(3, int(size * 0.10))
    tag_x0 = size - post_w - tag_w - max(1, size // 32)
    tag_y0 = rail_h + max(2, size // 24)
    arr[tag_y0 : tag_y0 + tag_h, tag_x0 : tag_x0 + tag_w, :3] = [238, 142, 28]
    arr[tag_y0 + 1 : tag_y0 + tag_h - 1, tag_x0 + 1 : tag_x0 + tag_w - 1, :3] = [255, 255, 255]

    return Image.fromarray(arr)


def create_train_body_image(size: int = 64, seed: int = 505) -> Image.Image:
    """Generate high-speed bullet train metallic white/silver body with racing speed stripes."""
    rng = np.random.RandomState(seed)
    y, x = np.mgrid[:size, :size]
    arr = np.zeros((size, size, 4), dtype=np.uint8)

    # 1. Main aerodynamic body: metallic pearl-white / brushed silver
    brushed = rng.uniform(-3.0, 3.0, (size, size))
    vert_sheen = 244.0 - (y / float(size)) * 14.0

    r = np.clip(vert_sheen + brushed, 0, 255)
    g = np.clip(vert_sheen + brushed + 2.0, 0, 255)
    b = np.clip(vert_sheen + brushed + 5.0, 0, 255)

    arr[..., 0] = r.astype(np.uint8)
    arr[..., 1] = g.astype(np.uint8)
    arr[..., 2] = b.astype(np.uint8)
    arr[..., 3] = 255

    # Top edge aerodynamic specular highlight
    arr[0, :, :3] = [255, 255, 255]

    # 2. Racing Speed Stripes
    red_y0 = int(size * 0.58)
    red_h = max(2, int(size * 0.08))
    red_y1 = red_y0 + red_h
    arr[red_y0:red_y1, :, 0] = 228
    arr[red_y0:red_y1, :, 1] = 34
    arr[red_y0:red_y1, :, 2] = 42

    white_h = max(1, size // 48)
    white_y0 = red_y1
    white_y1 = white_y0 + white_h
    arr[white_y0:white_y1, :, :3] = [255, 255, 255]

    blue_y0 = white_y1
    blue_h = max(3, int(size * 0.12))
    blue_y1 = min(size - 1, blue_y0 + blue_h)
    arr[blue_y0:blue_y1, :, 0] = 16
    arr[blue_y0:blue_y1, :, 1] = 42
    arr[blue_y0:blue_y1, :, 2] = 104

    arr[blue_y1, :, :3] = [210, 222, 235]

    # 3. Lower aerodynamic undercarriage skirt
    skirt_y0 = int(size * 0.84)
    arr[skirt_y0:, :, 0] = 42
    arr[skirt_y0:, :, 1] = 46
    arr[skirt_y0:, :, 2] = 56
    arr[skirt_y0, :, :3] = [28, 32, 40]

    louver_spacing = max(4, size // 8)
    for lx in range(max(2, size // 16), size - max(2, size // 16), louver_spacing):
        arr[skirt_y0 + 2 : size - 2, lx, :3] = [22, 24, 30]

    return Image.fromarray(arr)


def create_train_window_image(size: int = 64, seed: int = 606) -> Image.Image:
    """Generate aerodynamic passenger windows band with interior glow and pillar dividers."""
    arr = np.zeros((size, size, 4), dtype=np.uint8)

    top_band_h = int(size * 0.18)
    bot_band_y = int(size * 0.82)

    arr[:top_band_h, :, 0] = 236
    arr[:top_band_h, :, 1] = 240
    arr[:top_band_h, :, 2] = 246
    arr[bot_band_y:, :, 0] = 236
    arr[bot_band_y:, :, 1] = 240
    arr[bot_band_y:, :, 2] = 246
    arr[..., 3] = 255

    arr[0, :, :3] = [255, 255, 255]
    arr[top_band_h - 1, :, :3] = [32, 36, 44]
    arr[bot_band_y, :, :3] = [32, 36, 44]

    win_y0 = top_band_h
    win_y1 = bot_band_y
    arr[win_y0:win_y1, :, 0] = 24
    arr[win_y0:win_y1, :, 1] = 34
    arr[win_y0:win_y1, :, 2] = 48

    num_bays = 3
    bay_w = size // num_bays
    pillar_w = max(2, size // 24)

    for i in range(num_bays):
        bay_x0 = i * bay_w
        bay_x1 = (i + 1) * bay_w if i < num_bays - 1 else size

        if i < num_bays - 1:
            px0 = bay_x1 - pillar_w
            px1 = bay_x1
            arr[win_y0:win_y1, px0:px1, 0] = 220
            arr[win_y0:win_y1, px0:px1, 1] = 226
            arr[win_y0:win_y1, px0:px1, 2] = 234
            arr[win_y0:win_y1, px0, :3] = [255, 255, 255]
            arr[win_y0:win_y1, px1 - 1, :3] = [170, 178, 190]

        pane_x0 = bay_x0 + max(1, size // 32)
        pane_x1 = (bay_x1 - pillar_w if i < num_bays - 1 else bay_x1) - max(1, size // 32)
        pane_cx = (pane_x0 + pane_x1) // 2
        pane_cy = (win_y0 + win_y1) // 2

        glow_rad_x = max(2, (pane_x1 - pane_x0) // 3)
        glow_rad_y = max(2, (win_y1 - win_y0) // 3)

        if pane_x1 > pane_x0 + 2 and win_y1 > win_y0 + 4:
            bay_ys, bay_xs = np.mgrid[win_y0 + 2 : win_y1 - 2, pane_x0 + 1 : pane_x1 - 1]
            dx = (bay_xs - pane_cx) / float(glow_rad_x)
            dy = (bay_ys - pane_cy) / float(glow_rad_y)
            dist2 = dx * dx + dy * dy
            glow_mask = dist2 < 1.0
            glow = np.clip(1.0 - dist2, 0.0, 1.0)

            sub_r = arr[win_y0 + 2 : win_y1 - 2, pane_x0 + 1 : pane_x1 - 1, 0].astype(float)
            sub_g = arr[win_y0 + 2 : win_y1 - 2, pane_x0 + 1 : pane_x1 - 1, 1].astype(float)
            sub_b = arr[win_y0 + 2 : win_y1 - 2, pane_x0 + 1 : pane_x1 - 1, 2].astype(float)

            sub_r[glow_mask] = 24.0 + glow[glow_mask] * 215.0
            sub_g[glow_mask] = 34.0 + glow[glow_mask] * 165.0
            sub_b[glow_mask] = 48.0 + glow[glow_mask] * 65.0

            arr[win_y0 + 2 : win_y1 - 2, pane_x0 + 1 : pane_x1 - 1, 0] = sub_r.astype(np.uint8)
            arr[win_y0 + 2 : win_y1 - 2, pane_x0 + 1 : pane_x1 - 1, 1] = sub_g.astype(np.uint8)
            arr[win_y0 + 2 : win_y1 - 2, pane_x0 + 1 : pane_x1 - 1, 2] = sub_b.astype(np.uint8)

        hr_w = max(1, size // 32)
        hr_h = max(2, size // 20)
        arr[pane_cy - hr_h : pane_cy, pane_cx - hr_w : pane_cx + hr_w + 1, :3] = [45, 42, 48]

    y_win, x_win = np.mgrid[win_y0:win_y1, :size]
    glare_mask = np.abs((x_win - (y_win - win_y0) * 1.5) - int(size * 0.4)) < max(1, size // 32)
    arr[win_y0:win_y1, :][glare_mask, 0] = np.clip(arr[win_y0:win_y1, :][glare_mask, 0].astype(int) + 110, 0, 255).astype(np.uint8)
    arr[win_y0:win_y1, :][glare_mask, 1] = np.clip(arr[win_y0:win_y1, :][glare_mask, 1].astype(int) + 160, 0, 255).astype(np.uint8)
    arr[win_y0:win_y1, :][glare_mask, 2] = np.clip(arr[win_y0:win_y1, :][glare_mask, 2].astype(int) + 200, 0, 255).astype(np.uint8)

    return Image.fromarray(arr)


def create_train_front_image(size: int = 64, seed: int = 707) -> Image.Image:
    """Generate bullet train front nose decal with aerodynamic raked windshield and warm radiant headlights."""
    arr = np.zeros((size, size, 4), dtype=np.uint8)
    cx = (size - 1.0) / 2.0

    # 1. Upper Section: Aerodynamic Raked Cockpit Windshield (top 42%)
    h_windshield = int(size * 0.42)
    y_ws, x_ws = np.mgrid[:h_windshield, :size]

    arr[:h_windshield, :, 0] = 22
    arr[:h_windshield, :, 1] = 38
    arr[:h_windshield, :, 2] = 58
    arr[..., 3] = 255

    side_frame_w = max(2, int(size * 0.10))
    arr[:h_windshield, :side_frame_w, 0] = 236
    arr[:h_windshield, :side_frame_w, 1] = 240
    arr[:h_windshield, :side_frame_w, 2] = 246
    arr[:h_windshield, -side_frame_w:, 0] = 236
    arr[:h_windshield, -side_frame_w:, 1] = 240
    arr[:h_windshield, -side_frame_w:, 2] = 246

    glare = np.abs((x_ws - y_ws * 1.4) - int(size * 0.28)) < max(1, size // 32)
    arr[:h_windshield, :][glare, 0] = 175
    arr[:h_windshield, :][glare, 1] = 225
    arr[:h_windshield, :][glare, 2] = 255

    arr[0, :, :3] = [238, 242, 248]
    arr[h_windshield - 1, :, :3] = [20, 24, 30]

    # 2. Middle Section: Aerodynamic Bullet Nose Cone (42% to 68%)
    h_nose_end = int(size * 0.68)
    arr[h_windshield:h_nose_end, :, 0] = 238
    arr[h_windshield:h_nose_end, :, 1] = 242
    arr[h_windshield:h_nose_end, :, 2] = 248

    emb_y0 = h_windshield + max(2, size // 24)
    emb_h = max(3, size // 16)
    emb_w = max(4, int(size * 0.22))
    emb_x0 = int(cx - emb_w / 2.0)
    emb_x1 = emb_x0 + emb_w
    arr[emb_y0 : emb_y0 + emb_h, emb_x0:emb_x1, :3] = [18, 48, 110]
    arr[emb_y0 + 1 : emb_y0 + emb_h - 1, emb_x0 : emb_x0 + 2, :3] = [245, 210, 50]
    arr[emb_y0 + 1 : emb_y0 + emb_h - 1, emb_x1 - 2 : emb_x1, :3] = [245, 210, 50]

    band_y = emb_y0 + emb_h + max(1, size // 32)
    arr[band_y : band_y + max(1, size // 32), :, 0] = 228
    arr[band_y : band_y + max(1, size // 32), :, 1] = 34
    arr[band_y : band_y + max(1, size // 32), :, 2] = 42

    # 3. Lower Section: High-Intensity Dual Radiant Headlights (68% to 86%)
    h_hl_end = int(size * 0.86)
    arr[h_nose_end:h_hl_end, :, 0] = 228
    arr[h_nose_end:h_hl_end, :, 1] = 232
    arr[h_nose_end:h_hl_end, :, 2] = 238

    hl_w = max(6, int(size * 0.22))
    hl_h = max(4, int(size * 0.14))
    hl_y0 = h_nose_end + max(1, (h_hl_end - h_nose_end - hl_h) // 2)
    hl_y1 = hl_y0 + hl_h

    hl_left_x0 = max(2, int(size * 0.10))
    hl_left_x1 = hl_left_x0 + hl_w
    hl_right_x1 = size - max(2, int(size * 0.10))
    hl_right_x0 = hl_right_x1 - hl_w

    for hx0, hx1 in [(hl_left_x0, hl_left_x1), (hl_right_x0, hl_right_x1)]:
        arr[hl_y0:hl_y1, hx0:hx1, :3] = [170, 180, 195]
        arr[hl_y0, hx0:hx1, :3] = [40, 44, 52]
        arr[hl_y1 - 1, hx0:hx1, :3] = [40, 44, 52]
        arr[hl_y0:hl_y1, hx0, :3] = [40, 44, 52]
        arr[hl_y0:hl_y1, hx1 - 1, :3] = [40, 44, 52]

        arr[hl_y0 + 1 : hl_y1 - 1, hx0 + 1 : hx1 - 1, 0] = 255
        arr[hl_y0 + 1 : hl_y1 - 1, hx0 + 1 : hx1 - 1, 1] = 246
        arr[hl_y0 + 1 : hl_y1 - 1, hx0 + 1 : hx1 - 1, 2] = 165
        arr[hl_y0 + 2 : hl_y1 - 2, hx0 + 2 : hx1 - 2, :3] = [255, 255, 245]

    center_hl_w = max(2, size // 16)
    arr[hl_y0 + 1 : hl_y1 - 1, int(cx - center_hl_w / 2) : int(cx + center_hl_w / 2) + 1, :3] = [255, 252, 215]

    # 4. Bottom Cowcatcher / Aerodynamic Air Dam Skirt (86% to 100%)
    arr[h_hl_end:, :, 0] = 36
    arr[h_hl_end:, :, 1] = 40
    arr[h_hl_end:, :, 2] = 48
    arr[h_hl_end, :, :3] = [185, 195, 210]

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


def generate_car_paint_texture(size: int = 64) -> bytes:
    """Generate glossy automotive car paint texture RGBA bytes."""
    return create_car_paint_image(size=size).tobytes("raw", "RGBA")


def generate_car_cabin_texture(size: int = 64) -> bytes:
    """Generate tinted automotive cabin glass texture RGBA bytes with glare streaks."""
    return create_car_cabin_image(size=size).tobytes("raw", "RGBA")


def generate_car_wheel_texture(size: int = 64) -> bytes:
    """Generate dark rubber tire with metallic rim hubcap texture RGBA bytes."""
    return create_car_wheel_image(size=size).tobytes("raw", "RGBA")


def generate_truck_cargo_texture(size: int = 64) -> bytes:
    """Generate corrugated shipping container siding texture RGBA bytes."""
    return create_truck_cargo_image(size=size).tobytes("raw", "RGBA")


def generate_train_body_texture(size: int = 64) -> bytes:
    """Generate metallic bullet train body with racing speed stripes RGBA bytes."""
    return create_train_body_image(size=size).tobytes("raw", "RGBA")


def generate_train_window_texture(size: int = 64) -> bytes:
    """Generate passenger train windows band with interior glow RGBA bytes."""
    return create_train_window_image(size=size).tobytes("raw", "RGBA")


def generate_train_front_texture(size: int = 64) -> bytes:
    """Generate bullet train nose decal with raked windshield and headlights RGBA bytes."""
    return create_train_front_image(size=size).tobytes("raw", "RGBA")


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

    @staticmethod
    def generate_car_paint_texture(size: int = 64) -> bytes:
        return generate_car_paint_texture(size=size)

    @staticmethod
    def generate_car_cabin_texture(size: int = 64) -> bytes:
        return generate_car_cabin_texture(size=size)

    @staticmethod
    def generate_car_wheel_texture(size: int = 64) -> bytes:
        return generate_car_wheel_texture(size=size)

    @staticmethod
    def generate_truck_cargo_texture(size: int = 64) -> bytes:
        return generate_truck_cargo_texture(size=size)

    @staticmethod
    def generate_train_body_texture(size: int = 64) -> bytes:
        return generate_train_body_texture(size=size)

    @staticmethod
    def generate_train_window_texture(size: int = 64) -> bytes:
        return generate_train_window_texture(size=size)

    @staticmethod
    def generate_train_front_texture(size: int = 64) -> bytes:
        return generate_train_front_texture(size=size)

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
        elif clean in ("car_paint", "paint", "car_chassis", "chassis", "car_body"):
            return create_car_paint_image(size=size)
        elif clean in ("car_cabin", "cabin", "car_window", "windshield"):
            return create_car_cabin_image(size=size)
        elif clean in ("car_wheel", "wheel", "tire", "truck_wheel"):
            return create_car_wheel_image(size=size)
        elif clean in ("truck_cargo", "cargo", "container", "shipping_container"):
            return create_truck_cargo_image(size=size)
        elif clean in ("train_body", "train", "locomotive"):
            return create_train_body_image(size=size)
        elif clean in ("train_window", "train_windows", "passenger_window"):
            return create_train_window_image(size=size)
        elif clean in ("train_front", "bullet_train_front", "train_nose", "train_headlight"):
            return create_train_front_image(size=size)
        elif clean in ("car_grille", "grille"):
            return create_car_grille_image(size=size)
        elif clean in ("vehicle", "car", "truck"):
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
        "car_paint",
        "car_cabin",
        "car_wheel",
        "truck_cargo",
        "train_body",
        "train_window",
        "train_front",
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
    filepaths["paint"] = filepaths["car_paint"]
    filepaths["paint_64"] = filepaths["car_paint_64"]
    filepaths["paint_128"] = filepaths["car_paint_128"]
    filepaths["cabin"] = filepaths["car_cabin"]
    filepaths["cabin_64"] = filepaths["car_cabin_64"]
    filepaths["cabin_128"] = filepaths["car_cabin_128"]
    filepaths["wheel"] = filepaths["car_wheel"]
    filepaths["wheel_64"] = filepaths["car_wheel_64"]
    filepaths["wheel_128"] = filepaths["car_wheel_128"]
    filepaths["cargo"] = filepaths["truck_cargo"]
    filepaths["cargo_64"] = filepaths["truck_cargo_64"]
    filepaths["cargo_128"] = filepaths["truck_cargo_128"]
    filepaths["train"] = filepaths["train_body"]
    filepaths["train_64"] = filepaths["train_body_64"]
    filepaths["train_128"] = filepaths["train_body_128"]

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
            "paint": "car_paint",
            "car_chassis": "car_paint",
            "chassis": "car_paint",
            "car_body": "car_paint",
            "cabin": "car_cabin",
            "car_window": "car_cabin",
            "windshield": "car_cabin",
            "wheel": "car_wheel",
            "tire": "car_wheel",
            "truck_wheel": "car_wheel",
            "cargo": "truck_cargo",
            "container": "truck_cargo",
            "shipping_container": "truck_cargo",
            "train": "train_body",
            "locomotive": "train_body",
            "train_windows": "train_window",
            "passenger_window": "train_window",
            "bullet_train_front": "train_front",
            "train_nose": "train_front",
            "train_headlight": "train_front",
            "grille": "car_grille",
        }
        return alias_map.get(clean, clean)


# Unified alias for MaterialRegistry
MaterialRegistry = TextureRegistry

__all__ = [
    "CORE_TEXTURE_NAMES",
    "EXTENDED_TEXTURE_NAMES",
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
    "create_car_paint_image",
    "create_car_cabin_image",
    "create_car_wheel_image",
    "create_truck_cargo_image",
    "create_train_body_image",
    "create_train_window_image",
    "create_train_front_image",
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
    "generate_car_paint_texture",
    "generate_car_cabin_texture",
    "generate_car_wheel_texture",
    "generate_truck_cargo_texture",
    "generate_train_body_texture",
    "generate_train_window_texture",
    "generate_train_front_texture",
    "CrossyTextureGenerator",
    "TextureGenerator",
    "ensure_textures_generated",
    "TextureRegistry",
    "MaterialRegistry",
]
