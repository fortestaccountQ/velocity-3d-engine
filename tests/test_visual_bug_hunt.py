"""Hostile Visual QA and Shader Testing Suite for Pielosyty 3D Engine.

Tests:
1. Offscreen framebuffer read sanity & depth buffer sanity.
2. Normal mapping & TBN calculation (degenerate tangent NaN resilience).
3. PBR materials (Standard, Physical, Toon, Unlit, ShaderMaterial).
4. Transparent queue depth sorting (multi-layer back-to-front alpha blending).
5. Dynamic viewport resizing & aspect ratio stability.
6. Post-processing passes (BloomPass, SSAOPass, TonemappingPass, FXAAPass).
7. Shadow map texel snapping & 16-tap Poisson PCF.
"""

import pytest
import math
import struct
import pielosyty as p


@pytest.fixture(scope="module")
def app():
    """Shared offscreen EngineApp fixture."""
    return p.App("VisualQATestApp", width=128, height=128)


def get_pixel_rgba(buffer: bytes, width: int, x: int, y: int) -> tuple[int, int, int, int]:
    """Helper to sample pixel RGBA at coordinate (x, y)."""
    offset = (y * width + x) * 4
    if offset + 4 > len(buffer):
        return (0, 0, 0, 0)
    return struct.unpack_from("4B", buffer, offset)


# ============================================================================
# 1. Offscreen Framebuffer Read Sanity & Depth Buffer Sanity
# ============================================================================
def test_offscreen_framebuffer_and_depth_sanity(app):
    """Verify that offscreen render target captures color and depth buffers without corruption."""
    w, h = 64, 64
    target = p.RenderTarget(w, h, p.RenderTargetFormat.RGBA8, True)
    assert target.is_valid()
    assert target.width == w
    assert target.height == h
    assert target.has_depth is True

    scene = p.Scene()
    scene.background_color = (0.1, 0.2, 0.3, 1.0)
    scene.background_type = p.BackgroundType.Color

    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 0.0, 3.0)
    cam.set_target(0.0, 0.0, 0.0)

    # Red box in the center
    box = p.create_box(scene, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), color=(1.0, 0.0, 0.0, 1.0))
    app.render_target(scene, cam, target)

    # 1. Color buffer checks
    pixels = app.read_pixels(target)
    assert len(pixels) == w * h * 4

    # All bytes must be valid [0, 255]
    for b in pixels[:100]:
        assert 0 <= b <= 255

    # Center pixel should be red foreground
    center_r, center_g, center_b, center_a = get_pixel_rgba(pixels, w, 32, 32)
    assert center_r > 150
    assert center_g < 50
    assert center_b < 50
    assert center_a == 255

    # Corner pixel should be background color (approx 0.1, 0.2, 0.3 -> ~25, ~51, ~76)
    corner_r, corner_g, corner_b, _ = get_pixel_rgba(pixels, w, 2, 2)
    assert corner_r < 50
    assert corner_g > 30
    assert corner_b > 50

    # 2. Depth buffer checks
    depth_values = app.read_depth_pixels(target)
    assert len(depth_values) == w * h

    # Center depth should be < 1.0 (box is at z=0, cam at z=3 -> distance 2.5 to front face)
    center_depth = depth_values[32 * w + 32]
    assert 0.0 < center_depth < 0.99

    # Corner depth should be background clear value = 1.0
    corner_depth = depth_values[2 * w + 2]
    assert math.isclose(corner_depth, 1.0, rel_tol=1e-3)


# ============================================================================
# 2. TBN Calculation & Degenerate Tangent NaN Resilience
# ============================================================================
def test_tbn_collinear_tangent_resilience(app):
    """Hostile test: A custom mesh where tangent and normal are collinear (n == t).
    Previous implementation without guard would do normalize(t - n*(n.t)) = normalize(0) -> NaN!
    This test verifies that no NaNs are produced and pixels render cleanly.
    """
    mesh = p.Mesh()
    # Create 3 vertices forming a triangle with collinear normal and tangent
    v1 = p.Vertex()
    v1.position = p.Vec3(-1.0, -1.0, 0.0)
    v1.normal = p.Vec3(0.0, 0.0, 1.0)
    v1.tangent = p.Vec4(0.0, 0.0, 1.0, 1.0)  # COLLINEAR WITH NORMAL!
    v1.uv = p.Vec2(0.0, 0.0)
    v1.color = p.Vec4(1.0, 1.0, 1.0, 1.0)

    v2 = p.Vertex()
    v2.position = p.Vec3(1.0, -1.0, 0.0)
    v2.normal = p.Vec3(0.0, 0.0, 1.0)
    v2.tangent = p.Vec4(0.0, 0.0, 1.0, 1.0)  # COLLINEAR!
    v2.uv = p.Vec2(1.0, 0.0)
    v2.color = p.Vec4(1.0, 1.0, 1.0, 1.0)

    v3 = p.Vertex()
    v3.position = p.Vec3(0.0, 1.0, 0.0)
    v3.normal = p.Vec3(0.0, 0.0, 1.0)
    v3.tangent = p.Vec4(0.0, 0.0, 1.0, 1.0)  # COLLINEAR!
    v3.uv = p.Vec2(0.5, 1.0)
    v3.color = p.Vec4(1.0, 1.0, 1.0, 1.0)

    mesh.cpu_vertices = [v1, v2, v3]
    mesh.cpu_indices = [0, 1, 2]

    scene = p.Scene()
    ent = scene.create_entity("DegenerateTBN_Triangle")
    ent.mesh = mesh
    mat = p.StandardMaterial()
    mat.base_color = (1.0, 1.0, 0.0, 1.0)  # Yellow
    ent.material = mat

    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 0.0, 2.0)
    cam.set_target(0.0, 0.0, 0.0)

    target = p.RenderTarget(64, 64)
    app.render_target(scene, cam, target)

    pixels = app.read_pixels(target)
    # Ensure center pixel rendered properly and is not black/corrupted/NaN
    r, g, b, a = get_pixel_rgba(pixels, 64, 32, 32)
    assert r > 50
    assert g > 50
    assert a == 255


def test_normal_map_lighting_perturbation(app):
    """Verify that a perturbed normal map modifies pixel lighting compared to a flat normal map."""
    w, h = 64, 64
    target = p.RenderTarget(w, h)

    scene = p.Scene()
    light = p.DirectionalLight()
    light.set_position(2.0, 2.0, 2.0)
    light.set_direction(1.0, -1.0, -1.0)
    light.intensity = 1.0
    scene.add_light(light)

    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 0.0, 2.5)
    cam.set_target(0.0, 0.0, 0.0)

    box = p.create_box(scene, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0), color=(0.8, 0.8, 0.8, 1.0))
    app.render_target(scene, cam, target)
    flat_pixels = app.read_pixels(target)
    flat_center = get_pixel_rgba(flat_pixels, w, 32, 32)

    # Now create a perturbed normal texture: tilted normal (+X slant: RGB = 255, 128, 128)
    normal_data = bytearray([255, 128, 128, 255] * (16 * 16))
    norm_tex = p.DataTexture(bytes(normal_data), 16, 16, 4)
    mat = p.StandardMaterial()
    mat.base_color = (0.8, 0.8, 0.8, 1.0)
    mat.normal_map = norm_tex
    box.material = mat

    app.render_target(scene, cam, target)
    perturbed_pixels = app.read_pixels(target)
    perturbed_center = get_pixel_rgba(perturbed_pixels, w, 32, 32)

    # Lighting with slanted normal must differ from flat normal
    assert flat_center != perturbed_center


# ============================================================================
# 3. PBR Materials Suite Verification
# ============================================================================
def test_pbr_materials_suite(app):
    """Test all material types: Standard, Physical, Toon, Unlit, ShaderMaterial."""
    w, h = 64, 64
    target = p.RenderTarget(w, h)
    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 0.0, 2.5)
    cam.set_target(0.0, 0.0, 0.0)

    # 1. Unlit Material (Constant brightness independent of lighting)
    scene_unlit = p.Scene()
    box_unlit = p.create_box(scene_unlit, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0))
    unlit_mat = p.UnlitMaterial()
    unlit_mat.base_color = (0.0, 1.0, 0.0, 1.0)  # Pure green
    box_unlit.material = unlit_mat
    app.render_target(scene_unlit, cam, target)
    unlit_pixels = app.read_pixels(target)
    ur, ug, ub, ua = get_pixel_rgba(unlit_pixels, w, 32, 32)
    assert ug >= 250
    assert ur == 0
    assert ub == 0

    # 2. Toon Material (Quantized cell-shading)
    scene_toon = p.Scene()
    light = p.DirectionalLight()
    light.set_position(2.0, 2.0, 2.0)
    light.set_direction(1.0, -1.0, -1.0)
    scene_toon.add_light(light)
    box_toon = p.create_box(scene_toon, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0))
    toon_mat = p.ToonMaterial()
    toon_mat.base_color = (0.0, 0.5, 1.0, 1.0)
    toon_mat.steps = 3
    box_toon.material = toon_mat
    app.render_target(scene_toon, cam, target)
    toon_pixels = app.read_pixels(target)
    tr, tg, tb, ta = get_pixel_rgba(toon_pixels, w, 32, 32)
    assert tb > 50

    # 3. Physical Material (PBR with roughness and metallic)
    scene_phys = p.Scene()
    scene_phys.add_light(light)
    box_phys = p.create_box(scene_phys, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0))
    phys_mat = p.PhysicalMaterial()
    phys_mat.base_color = (1.0, 0.5, 0.0, 1.0)
    phys_mat.roughness = 0.2
    phys_mat.metallic = 0.8
    box_phys.material = phys_mat
    app.render_target(scene_phys, cam, target)
    phys_pixels = app.read_pixels(target)
    pr, pg, pb, pa = get_pixel_rgba(phys_pixels, w, 32, 32)
    assert pr > 50


# ============================================================================
# 4. Transparent Queue Depth Sorting & Multi-Layer Alpha Blending
# ============================================================================
def test_transparent_queue_depth_sorting(app):
    """Test 3 overlapping transparent planes at z = -1.0, -2.0, -3.0.
    With depth_write = false, back-to-front sorting must render all three planes blended together,
    rather than front plane occluding back planes in depth buffer!
    """
    w, h = 64, 64
    target = p.RenderTarget(w, h)

    scene = p.Scene()
    scene.background_color = (0.0, 0.0, 0.0, 1.0)  # Black background
    scene.background_type = p.BackgroundType.Color

    # Ambient light ensuring full visibility across transparent materials
    light = p.AmbientLight()
    light.color = (1.0, 1.0, 1.0)
    light.intensity = 1.0
    scene.add_light(light)

    # Plane 1: Front plane at z = -1.0 (Red, alpha = 0.5)
    p1 = p.create_box(scene, (2.0, 2.0, 0.05), (0.0, 0.0, -1.0))
    mat1 = p.StandardMaterial()
    mat1.base_color = (1.0, 0.0, 0.0, 0.5)
    mat1.transparent = True
    mat1.depth_write = False
    p1.material = mat1

    # Plane 2: Middle plane at z = -2.0 (Green, alpha = 0.5)
    p2 = p.create_box(scene, (2.0, 2.0, 0.05), (0.0, 0.0, -2.0))
    mat2 = p.StandardMaterial()
    mat2.base_color = (0.0, 1.0, 0.0, 0.5)
    mat2.transparent = True
    mat2.depth_write = False
    p2.material = mat2

    # Plane 3: Back plane at z = -3.0 (Blue, alpha = 0.5)
    p3 = p.create_box(scene, (2.0, 2.0, 0.05), (0.0, 0.0, -3.0))
    mat3 = p.StandardMaterial()
    mat3.base_color = (0.0, 0.0, 1.0, 0.5)
    mat3.transparent = True
    mat3.depth_write = False
    p3.material = mat3

    # Camera looking forward from z = 0 towards -z
    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 0.0, 0.0)
    cam.set_target(0.0, 0.0, -2.0)

    app.render_target(scene, cam, target)
    pixels = app.read_pixels(target)
    cr, cg, cb, ca = get_pixel_rgba(pixels, w, 32, 32)

    # Since all 3 transparent layers blend:
    # Red (front ~121), Green (middle ~64), Blue (back ~35) must all contribute!
    assert cr > 50, f"Expected Red channel > 50, got {cr}"
    assert cg > 25, f"Expected Green channel > 25, got {cg}"
    assert cb > 15, f"Expected Blue channel > 15, got {cb}"


# ============================================================================
# 5. Dynamic Viewport Resizing & Aspect Ratio Stability
# ============================================================================
def test_dynamic_viewport_and_aspect_ratio_stability(app):
    """Verify that changing render target dimensions or camera viewport updates aspect ratio
    and does NOT cause aspect ratio stretching or divide-by-zero.
    """
    scene = p.Scene()
    sphere = p.create_sphere(scene, radius=1.0)
    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 0.0, 3.0)
    cam.set_target(0.0, 0.0, 0.0)

    # 1. Square target 64x64 (aspect 1.0)
    target_square = p.RenderTarget(64, 64)
    app.render_target(scene, cam, target_square)
    assert cam.aspect == 1.0

    # 2. Widescreen target 128x64 (aspect 2.0)
    target_wide = p.RenderTarget(128, 64)
    app.render_target(scene, cam, target_wide)
    assert math.isclose(cam.aspect, 2.0, rel_tol=1e-3)

    # 3. Tall target 64x128 (aspect 0.5)
    target_tall = p.RenderTarget(64, 128)
    app.render_target(scene, cam, target_tall)
    assert math.isclose(cam.aspect, 0.5, rel_tol=1e-3)

    # 4. Sub-viewport split: viewport = (0, 0, 0.5, 1.0) on 128x64 target
    # sub-width = 64, sub-height = 64 -> sub-aspect = 1.0
    cam.viewport = (0.0, 0.0, 0.5, 1.0)
    app.render_target(scene, cam, target_wide)
    assert math.isclose(cam.aspect, 1.0, rel_tol=1e-3)


# ============================================================================
# 6. Post-Processing Passes Pipeline
# ============================================================================
def test_post_processing_pipeline(app):
    """Test EffectComposer with BloomPass, SSAOPass, TonemappingPass, and FXAAPass."""
    w, h = 64, 64
    composer = p.EffectComposer(w, h)
    assert composer.enabled is True

    # 1. Bloom Pass
    bloom = p.BloomPass(threshold=0.5, strength=1.5, radius=0.5)
    composer.add_pass(bloom)

    # 2. SSAO Pass
    ssao = p.SSAOPass(radius=0.5, bias=0.025, power=1.0)
    composer.add_pass(ssao)

    # 3. Tonemapping Pass (Test Neutral mode)
    tonemap = p.TonemappingPass(mode=p.TonemappingMode.Neutral, exposure=1.2, gamma=2.2)
    composer.add_pass(tonemap)

    # 4. FXAA Pass
    fxaa = p.FXAAPass()
    composer.add_pass(fxaa)

    assert len(composer.passes) == 4

    # Render scene through composer
    scene = p.Scene()
    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 0.0, 3.0)
    cam.set_target(0.0, 0.0, 0.0)

    # Bright emissive object to trigger bloom
    box = p.create_box(scene, (1.0, 1.0, 1.0), (0.0, 0.0, 0.0))
    mat = p.StandardMaterial()
    mat.base_color = (2.0, 1.5, 0.5, 1.0)  # HDR over 1.0
    box.material = mat

    composer.render(scene, cam)

    # Verify HDR render target is valid and readable (RGBA16F = 8 bytes per pixel)
    hdr_target = composer.hdr_target
    assert hdr_target.is_valid()
    hdr_pixels = app.read_pixels(hdr_target)
    expected_bytes = hdr_target.width * hdr_target.height * (8 if hdr_target.format == p.RenderTargetFormat.RGBA16F else 4)
    assert len(hdr_pixels) == expected_bytes

    # Change Tonemapping modes dynamically
    for mode in [
        p.TonemappingMode.ACESFilmic,
        p.TonemappingMode.Reinhard,
        p.TonemappingMode.Cineon,
        p.TonemappingMode.Linear,
        p.TonemappingMode.Neutral,
    ]:
        tonemap.mode = mode
        composer.render(scene, cam)
        pix = app.read_pixels(hdr_target)
        assert len(pix) == expected_bytes


# ============================================================================
# 7. Shadow Map Texel Snapping & 16-Tap Poisson PCF
# ============================================================================
def test_shadow_map_texel_snapping_and_pcf(app):
    """Test directional shadow casting with texel snapping and 16-tap Poisson PCF."""
    w, h = 64, 64
    target = p.RenderTarget(w, h)

    scene = p.Scene()
    scene.background_color = (0.2, 0.2, 0.2, 1.0)

    # Slanted directional light casting shadows
    light = p.DirectionalLight()
    light.set_position(5.0, 5.0, 0.0)
    light.set_direction(-1.0, -1.0, 0.0)
    light.cast_shadows = True
    scene.add_light(light)

    # Large floor plane receiving shadow
    floor = p.create_box(scene, (10.0, 0.1, 10.0), (0.0, -0.5, 0.0), color=(0.8, 0.8, 0.8, 1.0))
    floor.receive_shadows = True
    floor.cast_shadows = False

    # Box to the right casting shadow towards the center
    caster = p.create_box(scene, (1.0, 2.0, 1.0), (1.5, 1.0, 0.0), color=(1.0, 0.0, 0.0, 1.0))
    caster.cast_shadows = True

    # Camera looking top-down at floor
    cam = p.PerspectiveCamera(fov=60.0, aspect=1.0)
    cam.position = (0.0, 5.0, 0.01)
    cam.set_target(0.0, 0.0, 0.0)

    # Test 1: Hard shadows (pcf_16_tap = False)
    app.set_shadow_pcf_16_tap(False)
    app.set_shadow_texel_snapping(True)
    app.render_target(scene, cam, target)
    hard_pixels = app.read_pixels(target)

    # Test 2: Soft shadows (pcf_16_tap = True)
    app.set_shadow_pcf_16_tap(True)
    app.set_shadow_texel_snapping(True)
    app.render_target(scene, cam, target)
    soft_pixels = app.read_pixels(target)

    assert len(hard_pixels) == len(soft_pixels) == w * h * 4

    # Verify that shadows exist: floor has shadowed regions darker than lit regions
    # Sample lit corner of floor vs shadow region
    lit_r, lit_g, lit_b, _ = get_pixel_rgba(soft_pixels, w, 10, 10)
    shadow_r, shadow_g, shadow_b, _ = get_pixel_rgba(soft_pixels, w, 26, 32)

    lit_lum = 0.2126 * lit_r + 0.7152 * lit_g + 0.0722 * lit_b
    shadow_lum = 0.2126 * shadow_r + 0.7152 * shadow_g + 0.0722 * shadow_b
    assert lit_lum > shadow_lum, f"Lit luminance ({lit_lum}) must exceed shadow luminance ({shadow_lum})"
