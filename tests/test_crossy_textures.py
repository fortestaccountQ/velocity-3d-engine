"""Unit tests for Crossy Duck procedural voxel / pixel-art textures and registry.

Verifies:
  1. TextureGeneratorContract & MaterialPaletteContract protocol adherence.
  2. All procedural generators produce valid 4-channel RGBA images and exact byte lengths.
  3. Dynamic animation parameter (phase) for water waves and caustics.
  4. Determinism and reproducibility across seed parameters.
  5. ensure_textures_generated writes valid PNG and raw RGBA files to disk.
  6. TextureRegistry and MaterialRegistry caching, PBR property assignments, and UV scaling.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
import pytest
from PIL import Image
import numpy as np

from contracts.texture_contracts import (
    MaterialPaletteContract,
    TextureGeneratorContract,
)
from examples.crossy_duck.textures import (
    CrossyTextureGenerator,
    TextureGenerator,
    TextureRegistry,
    MaterialRegistry,
    StylizedMaterial,
    MaterialConfig,
    MATERIAL_PRESETS,
    CORE_TEXTURE_NAMES,
    EXTENDED_TEXTURE_NAMES,
    ensure_textures_generated,
    create_grass_image,
    create_asphalt_image,
    create_water_image,
    create_wood_bark_image,
    create_wood_rings_image,
    create_rail_gravel_image,
    create_gravel_image,
    create_rail_tie_image,
    create_car_grille_image,
    create_vehicle_image,
    create_duck_image,
    create_tree_leaves_image,
    create_lilypad_image,
    create_car_paint_image,
    create_car_cabin_image,
    create_car_wheel_image,
    create_truck_cargo_image,
    create_train_body_image,
    create_train_window_image,
    create_train_front_image,
    generate_grass_texture,
    generate_asphalt_texture,
    generate_water_texture,
    generate_wood_bark_texture,
    generate_wood_rings_texture,
    generate_gravel_texture,
    generate_rail_gravel_texture,
    generate_rail_tie_texture,
    generate_car_grille_texture,
    generate_vehicle_texture,
    generate_duck_texture,
    generate_tree_leaves_texture,
    generate_lilypad_texture,
    generate_car_paint_texture,
    generate_car_cabin_texture,
    generate_car_wheel_texture,
    generate_truck_cargo_texture,
    generate_train_body_texture,
    generate_train_window_texture,
    generate_train_front_texture,
)


# -----------------------------------------------------------------------------
# 1. Contract Adherence Tests
# -----------------------------------------------------------------------------

def test_texture_generator_contract_conformance() -> None:
    """Verify CrossyTextureGenerator implements all TextureGeneratorContract static methods."""
    required_methods = [
        "generate_grass_texture",
        "generate_asphalt_texture",
        "generate_water_texture",
        "generate_wood_bark_texture",
        "generate_wood_rings_texture",
        "generate_gravel_texture",
        "generate_rail_tie_texture",
        "generate_car_paint_texture",
        "generate_car_cabin_texture",
        "generate_car_wheel_texture",
        "generate_truck_cargo_texture",
        "generate_train_body_texture",
        "generate_train_window_texture",
        "generate_train_front_texture",
    ]
    for method_name in required_methods:
        assert hasattr(CrossyTextureGenerator, method_name), f"Missing method {method_name}"
        fn = getattr(CrossyTextureGenerator, method_name)
        assert callable(fn), f"{method_name} is not callable"

    # Also verify TextureGenerator alias
    assert TextureGenerator is CrossyTextureGenerator


def test_material_palette_contract_conformance(tmp_path: Path) -> None:
    """Verify TextureRegistry / MaterialRegistry implements MaterialPaletteContract."""
    reg = TextureRegistry(assets_dir=tmp_path)
    assert hasattr(reg, "materials")
    assert isinstance(reg.materials, dict)
    assert hasattr(reg, "get_material")
    assert callable(reg.get_material)
    assert hasattr(reg, "update_animated_materials")
    assert callable(reg.update_animated_materials)

    # MaterialRegistry is an alias for TextureRegistry
    assert MaterialRegistry is TextureRegistry


# -----------------------------------------------------------------------------
# 2. Procedural Image Generator Dimensions and Channels
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("size", [64, 128])
@pytest.mark.parametrize("tex_name", EXTENDED_TEXTURE_NAMES)
def test_image_generators_rgba_and_dimensions(tex_name: str, size: int) -> None:
    """Verify every procedural image generator returns a valid 4-channel RGBA Image."""
    img = CrossyTextureGenerator.create_image(tex_name, size=size)
    assert isinstance(img, Image.Image)
    assert img.mode == "RGBA", f"Expected RGBA mode for {tex_name}, got {img.mode}"
    assert img.size == (size, size), f"Expected {(size, size)}, got {img.size}"

    # Verify alpha channel is fully opaque or valid
    alpha = img.getchannel("A")
    extrema = alpha.getextrema()
    assert extrema[0] > 0, f"Alpha channel should not be completely transparent for {tex_name}"
    assert extrema[1] == 255, f"Alpha channel should reach 255 for {tex_name}"


# -----------------------------------------------------------------------------
# 3. Raw RGBA Byte Buffers Length & Correctness
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("size", [64, 128])
def test_raw_byte_buffer_lengths_and_matching(size: int) -> None:
    """Verify all raw byte generator functions return exact 4-channel buffer sizes."""
    expected_bytes = size * size * 4

    generators = {
        "grass": generate_grass_texture(size=size),
        "asphalt": generate_asphalt_texture(size=size),
        "water": generate_water_texture(size=size, phase=0.0),
        "wood_bark": generate_wood_bark_texture(size=size),
        "wood_rings": generate_wood_rings_texture(size=size),
        "gravel": generate_gravel_texture(size=size),
        "rail_gravel": generate_rail_gravel_texture(size=size),
        "rail_tie": generate_rail_tie_texture(size=size),
        "car_grille": generate_car_grille_texture(size=size),
        "vehicle": generate_vehicle_texture(size=size),
        "duck": generate_duck_texture(size=size),
        "tree_leaves": generate_tree_leaves_texture(size=size),
        "lilypad": generate_lilypad_texture(size=size),
        "car_paint": generate_car_paint_texture(size=size),
        "car_cabin": generate_car_cabin_texture(size=size),
        "car_wheel": generate_car_wheel_texture(size=size),
        "truck_cargo": generate_truck_cargo_texture(size=size),
        "train_body": generate_train_body_texture(size=size),
        "train_window": generate_train_window_texture(size=size),
        "train_front": generate_train_front_texture(size=size),
    }

    for name, raw_bytes in generators.items():
        assert isinstance(raw_bytes, bytes), f"{name} should return bytes"
        assert len(raw_bytes) == expected_bytes, (
            f"{name} byte count {len(raw_bytes)} != expected {expected_bytes}"
        )


def test_alias_equivalence() -> None:
    """Verify aliases return identical bytes for the same seed."""
    assert generate_gravel_texture(64) == generate_rail_gravel_texture(64)
    assert generate_vehicle_texture(64) == generate_car_grille_texture(64)


# -----------------------------------------------------------------------------
# 4. Animated Water Wave Dynamics
# -----------------------------------------------------------------------------

def test_water_texture_phase_animation() -> None:
    """Verify water texture generator responds continuously to phase parameter."""
    b0 = generate_water_texture(size=64, phase=0.0)
    b1 = generate_water_texture(size=64, phase=1.0)
    b2 = generate_water_texture(size=64, phase=2.0)
    b_cycle = generate_water_texture(size=64, phase=2.0 * math.pi)

    # Different phases must produce distinct wave crests and caustics
    assert b0 != b1, "Water texture at phase 0.0 and 1.0 should differ"
    assert b1 != b2, "Water texture at phase 1.0 and 2.0 should differ"

    # Non-empty buffers
    assert len(b0) == 64 * 64 * 4
    assert len(b1) == 64 * 64 * 4


# -----------------------------------------------------------------------------
# 5. Determinism and Seeding
# -----------------------------------------------------------------------------

def test_procedural_determinism() -> None:
    """Verify procedural generators produce deterministic identical buffers when called repeatedly."""
    for _ in range(3):
        assert generate_grass_texture(64) == generate_grass_texture(64)
        assert generate_asphalt_texture(64) == generate_asphalt_texture(64)
        assert generate_wood_bark_texture(64) == generate_wood_bark_texture(64)
        assert generate_wood_rings_texture(64) == generate_wood_rings_texture(64)
        assert generate_duck_texture(64) == generate_duck_texture(64)
        assert generate_car_paint_texture(64) == generate_car_paint_texture(64)
        assert generate_car_cabin_texture(64) == generate_car_cabin_texture(64)
        assert generate_car_wheel_texture(64) == generate_car_wheel_texture(64)
        assert generate_truck_cargo_texture(64) == generate_truck_cargo_texture(64)
        assert generate_train_body_texture(64) == generate_train_body_texture(64)
        assert generate_train_window_texture(64) == generate_train_window_texture(64)
        assert generate_train_front_texture(64) == generate_train_front_texture(64)


# -----------------------------------------------------------------------------
# 6. Disk Export and ensure_textures_generated
# -----------------------------------------------------------------------------

def test_ensure_textures_generated_creates_all_files(tmp_path: Path) -> None:
    """Verify ensure_textures_generated creates PNGs and .rgba byte files for all resolutions."""
    result = ensure_textures_generated(assets_dir=tmp_path)
    assert isinstance(result, dict)

    for name in CORE_TEXTURE_NAMES:
        # Check canonical
        assert name in result
        png_path = Path(result[name])
        assert png_path.is_file(), f"Missing PNG file {png_path}"
        assert png_path.stat().st_size > 0

        # Check raw rgba file
        rgba_key = f"{name}_rgba"
        assert rgba_key in result
        rgba_path = Path(result[rgba_key])
        assert rgba_path.is_file(), f"Missing RGBA file {rgba_path}"
        assert rgba_path.stat().st_size == 64 * 64 * 4

        # Check 128x128
        p128 = Path(result[f"{name}_128"])
        assert p128.is_file()
        rgba128 = Path(result[f"{name}_128_rgba"])
        assert rgba128.stat().st_size == 128 * 128 * 4

        # Verify PNG is readable by PIL
        with Image.open(png_path) as opened_img:
            assert opened_img.size == (64, 64)
            assert opened_img.mode == "RGBA"

        # Verify raw RGBA file contents match the PNG raw bytes
        with open(rgba_path, "rb") as f:
            read_bytes = f.read()
        with Image.open(png_path) as opened_img:
            assert read_bytes == opened_img.tobytes("raw", "RGBA")


# -----------------------------------------------------------------------------
# 7. TextureRegistry & MaterialRegistry Functionality
# -----------------------------------------------------------------------------

def test_texture_registry_caching_and_properties(tmp_path: Path) -> None:
    """Verify TextureRegistry caches textures and materials properly."""
    reg = TextureRegistry(assets_dir=tmp_path, is_pixel_art=True)
    assert reg.is_pixel_art is True

    # 1. Textures retrieval
    grass_tex = reg.get_texture("grass", size=64)
    assert grass_tex is not None
    assert grass_tex.width == 64
    assert grass_tex.height == 64

    # Second call should return the exact same cached instance
    grass_tex_cached = reg.get_texture("grass", size=64)
    assert grass_tex_cached is grass_tex

    # 2. Materials retrieval
    grass_mat = reg.get_material("grass")
    assert grass_mat is not None
    assert hasattr(grass_mat, "roughness")
    assert hasattr(grass_mat, "metallic")
    assert hasattr(grass_mat, "is_pixel_art")
    assert grass_mat.is_pixel_art is True
    assert pytest.approx(grass_mat.roughness, 0.01) == 0.85
    assert pytest.approx(grass_mat.metallic, 0.01) == 0.00
    assert grass_mat.uv_scale == (1.0, 1.0)

    # Cached material retrieval
    assert reg.get_material("grass") is grass_mat

    # Check asphalt material
    asphalt_mat = reg.get_material("asphalt")
    assert pytest.approx(asphalt_mat.roughness, 0.01) == 0.90
    assert pytest.approx(asphalt_mat.metallic, 0.01) == 0.02

    # Check water material
    water_mat = reg.get_material("water")
    assert pytest.approx(water_mat.roughness, 0.01) == 0.15
    assert pytest.approx(water_mat.metallic, 0.01) == 0.05

    # Check car_grille material
    car_mat = reg.get_material("car_grille")
    assert pytest.approx(car_mat.roughness, 0.01) == 0.30
    assert pytest.approx(car_mat.metallic, 0.01) == 0.60

    # Check duck material
    duck_mat = reg.get_material("duck")
    assert pytest.approx(duck_mat.roughness, 0.01) == 0.45
    assert pytest.approx(duck_mat.metallic, 0.01) == 0.00

    # Check vehicle and train materials
    paint_mat = reg.get_material("car_paint")
    assert pytest.approx(paint_mat.roughness, 0.01) == 0.22
    assert pytest.approx(paint_mat.metallic, 0.01) == 0.20

    cabin_mat = reg.get_material("car_cabin")
    assert pytest.approx(cabin_mat.roughness, 0.01) == 0.12
    assert pytest.approx(cabin_mat.metallic, 0.01) == 0.10

    wheel_mat = reg.get_material("car_wheel")
    assert pytest.approx(wheel_mat.roughness, 0.01) == 0.55
    assert pytest.approx(wheel_mat.metallic, 0.01) == 0.45

    cargo_mat = reg.get_material("truck_cargo")
    assert pytest.approx(cargo_mat.roughness, 0.01) == 0.60
    assert pytest.approx(cargo_mat.metallic, 0.01) == 0.20

    train_body_mat = reg.get_material("train_body")
    assert pytest.approx(train_body_mat.roughness, 0.01) == 0.20
    assert pytest.approx(train_body_mat.metallic, 0.01) == 0.35

    train_win_mat = reg.get_material("train_window")
    assert pytest.approx(train_win_mat.roughness, 0.01) == 0.15
    assert pytest.approx(train_win_mat.metallic, 0.01) == 0.10

    train_front_mat = reg.get_material("train_front")
    assert pytest.approx(train_front_mat.roughness, 0.01) == 0.25
    assert pytest.approx(train_front_mat.metallic, 0.01) == 0.40


def test_registry_update_animated_materials(tmp_path: Path) -> None:
    """Verify registry advances animated time coordinates."""
    reg = TextureRegistry(assets_dir=tmp_path)
    mat = reg.get_material("water")

    initial_phase = reg.water_phase
    reg.update_animated_materials(0.1)
    assert reg.water_phase > initial_phase


def test_registry_unknown_texture_error() -> None:
    """Verify requesting an unknown texture raises ValueError."""
    with pytest.raises(ValueError, match="Unknown texture name"):
        CrossyTextureGenerator.create_image("invalid_name_xyz")


def test_stylized_material_uv_scale_setter_getter() -> None:
    """Verify StylizedMaterial uv_scale property setter and getter works without nanobind error."""
    mat = StylizedMaterial(roughness=0.5, metallic=0.1, is_pixel_art=True, uv_scale=(2.0, 3.0))
    assert mat.uv_scale == (2.0, 3.0)

    # Mutate uv_scale
    mat.uv_scale = (4.0, 5.0)
    assert mat.uv_scale == (4.0, 5.0)
    assert mat.is_pixel_art is True


def test_car_paint_clean_voxel_finish_without_noisy_stripes() -> None:
    """Verify car paint is clean high-key solid automotive finish without chaotic diagonal streaks."""
    im = create_car_paint_image(size=64)
    arr = np.array(im)
    assert arr.shape == (64, 64, 4)

    # Core paint area should have high, uniform luma suitable for multiplication by car color
    core = arr[10:50, 10:50, :3]
    # Luma must be high-key (> 210)
    assert np.all(core > 200)
    # Variance in core should be low (subtle metallic luster, not noisy stripes)
    assert np.std(core) < 15.0


def test_car_cabin_clean_tinted_glass_without_diagonal_glare() -> None:
    """Verify car cabin is sleek tinted glass with clean vertical gradient and no diagonal glare lines."""
    im = create_car_cabin_image(size=64)
    arr = np.array(im)
    assert arr.shape == (64, 64, 4)

    # Glass should be dark tinted with cyan undertone (B > R)
    center = arr[32, 20, :3]
    assert center[2] >= center[0]
    # Window weatherstrip border around perimeter should be dark
    border_px = arr[0, 32, :3]
    assert np.all(border_px < 40)

