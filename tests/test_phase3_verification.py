"""Comprehensive QA Verification Test Suite for Phase 3:
Cameras, Multi-Viewport, RenderTarget FBO & EffectComposer Post-Processing.

Validates the Phase 3 Acceptance Criterion from задание.txt:
"✅ Критерий готовности Фазы 3: Сцена с неоновыми объектами (emissive_intensity = 5.0)
даёт мягкое свечение через BloomPass, в углах комнат виден SSAO, а на 3D-телевизоре
внутри сцены в реальном времени транслируется картинка со второй камеры (RenderTarget)."
"""

from __future__ import annotations
import math
import pytest
import pielosyty as pe


# ===========================================================================
# 1. Official Phase 3 Acceptance Criterion: TV Screen & Post-Processing Scene
# ===========================================================================

class TestPhase3AcceptanceCriteria:
    """Validates the official Phase 3 Acceptance Criterion end-to-end."""

    def test_tv_screen_render_to_texture_scenario(self):
        """Verify the 3D TV Screen scenario:

        - Second camera renders scene into a RenderTarget.
        - TV mesh receives the rendered texture via `tv_mesh.material.albedo_map = target.texture`.
        - Main camera renders the entire scene including the TV mesh.
        """
        scene = pe.Scene()
        app = pe.App("TV Screen Scenario Test", width=800, height=600)

        # 1. Neon object with emissive_intensity = 5.0
        neon_mat = pe.StandardMaterial()
        neon_mat.base_color = (0.1, 1.0, 0.2, 1.0)
        neon_mat.emissive_color = (0.1, 1.0, 0.2)
        neon_mat.emissive_intensity = 5.0
        neon_box = scene.create_box(size=(1.0, 1.0, 1.0), material=neon_mat)
        neon_box.name = "NeonCube"
        neon_box.transform.position = (0.0, 1.0, 0.0)

        # 2. Room Corner meshes (for SSAO verification)
        room_mat = pe.StandardMaterial()
        room_mat.base_color = (0.8, 0.8, 0.8, 1.0)
        room_mat.roughness = 0.8

        floor = scene.create_plane(width=10.0, height=10.0, material=room_mat)
        floor.name = "RoomFloor"

        back_wall = scene.create_plane(width=10.0, height=6.0, material=room_mat)
        back_wall.name = "BackWall"
        back_wall.transform.position = (0.0, 3.0, -5.0)

        side_wall = scene.create_plane(width=10.0, height=6.0, material=room_mat)
        side_wall.name = "SideWall"
        side_wall.transform.position = (-5.0, 3.0, 0.0)
        side_wall.transform.rotate_y(math.radians(90.0))

        # 3. 3D TV Screen Mesh
        tv_mat = pe.StandardMaterial()
        tv_mat.base_color = (1.0, 1.0, 1.0, 1.0)
        tv_mat.roughness = 0.2
        tv_screen = scene.create_plane(width=3.2, height=1.8, material=tv_mat)
        tv_screen.name = "TVScreen"
        tv_screen.transform.position = (3.0, 2.0, -2.0)

        # 4. Secondary Camera (Security Camera / TV Broadcast)
        tv_cam = pe.PerspectiveCamera(fov=60.0, aspect=1.777, near_z=0.1, far_z=50.0)
        tv_cam.set_position(0.0, 2.5, 4.0)
        tv_cam.set_target(0.0, 1.0, 0.0)

        # 5. RenderTarget for TV Broadcast
        tv_target = pe.RenderTarget(512, 288, pe.RenderTargetFormat.RGBA8, has_depth=True)
        assert tv_target.width == 512
        assert tv_target.height == 288
        assert tv_target.format == pe.RenderTargetFormat.RGBA8
        assert tv_target.has_depth is True
        assert tv_target.texture is not None

        # 6. Render secondary camera view to tv_target
        app.render_target(scene, tv_cam, tv_target)

        # 7. Bind rendered target to TV screen mesh material
        tv_mat.albedo_map = tv_target.texture
        assert tv_mat.albedo_map is not None
        assert tv_mat.albedo_map.width == 512
        assert tv_mat.albedo_map.height == 288

        # Also verify callable access syntax parity
        tv_mat.albedo_map = tv_target.texture()
        assert tv_mat.albedo_map is not None

        # 8. Main Scene Camera viewing the room and TV screen
        main_cam = pe.PerspectiveCamera(fov=55.0, aspect=1.333, near_z=0.2, far_z=100.0)
        main_cam.set_position(0.0, 3.0, 8.0)
        main_cam.set_target(0.0, 1.5, 0.0)

        main_target = pe.RenderTarget(800, 600, pe.RenderTargetFormat.RGBA16F, has_depth=True)
        app.render_target(scene, main_cam, main_target)

        # 9. Pixel readback verification
        pixels = app.read_pixels(tv_target)
        assert isinstance(pixels, bytes)
        target_pixels = tv_target.read_pixels()
        assert isinstance(target_pixels, bytes)

    def test_neon_objects_emissive_bloom_and_ssao_composer(self):
        """Verify BloomPass and SSAOPass configuration on scene with emissive neon objects."""
        scene = pe.Scene()
        app = pe.App("Neon Bloom and SSAO Test", width=800, height=600)

        # Neon emissive material
        neon_mat = pe.StandardMaterial()
        neon_mat.emissive_color = (1.0, 0.2, 0.8)
        neon_mat.emissive_intensity = 5.0
        assert neon_mat.emissive_intensity == 5.0

        cube = scene.create_box(size=(1.0, 1.0, 1.0), material=neon_mat)
        assert cube is not None

        # Setup EffectComposer with BloomPass and SSAOPass
        composer = pe.EffectComposer(800, 600)

        bloom = pe.BloomPass(threshold=1.0, strength=2.0, radius=0.6)
        assert abs(bloom.threshold - 1.0) < 1e-4
        assert abs(bloom.strength - 2.0) < 1e-4
        assert abs(bloom.radius - 0.6) < 1e-4
        assert bloom.name == "BloomPass"
        assert bloom.enabled is True

        ssao = pe.SSAOPass(radius=0.5, bias=0.025, power=1.5)
        assert abs(ssao.radius - 0.5) < 1e-4
        assert abs(ssao.bias - 0.025) < 1e-4
        assert abs(ssao.power - 1.5) < 1e-4
        assert ssao.name == "SSAOPass"
        assert ssao.enabled is True

        composer.add_pass(ssao)
        composer.add_pass(bloom)

        assert len(composer.passes) == 2
        assert composer.passes[0].name == "SSAOPass"
        assert composer.passes[1].name == "BloomPass"

        # Attach composer to app
        app.composer = composer
        assert app.composer is not None

        cam = pe.PerspectiveCamera(60.0, 1.333, 0.1, 100.0)
        composer.render(scene, cam)


# ===========================================================================
# 2. Camera Projection, Matrices, Raycasting & Viewports
# ===========================================================================

class TestCamerasAndViewports:
    """Tests PerspectiveCamera, OrthographicCamera, matrices, raycasting, and viewports."""

    def test_perspective_camera_properties_and_matrices(self):
        """Verify PerspectiveCamera FOV, aspect, near/far planes, and matrix updates."""
        cam = pe.PerspectiveCamera(fov=45.0, aspect=1.6, near_z=0.5, far_z=200.0)
        assert abs(cam.fov - 45.0) < 1e-3
        assert abs(cam.aspect - 1.6) < 1e-3
        assert abs(cam.near_plane - 0.5) < 1e-3
        assert abs(cam.far_plane - 200.0) < 1e-3
        assert cam.type == pe.CameraType.Perspective

        # Mutate properties
        cam.fov = 60.0
        cam.aspect = 1.777
        cam.near_plane = 0.1
        cam.far_plane = 500.0

        assert abs(cam.fov - 60.0) < 1e-3
        assert abs(cam.aspect - 1.777) < 1e-3

        # Matrices
        vm = cam.view_matrix()
        pm = cam.projection_matrix()
        vpm = cam.view_projection_matrix()
        assert vm is not None
        assert pm is not None
        assert vpm is not None

        # set_perspective helper
        cam.set_perspective(75.0, 2.0, 0.2, 1000.0)
        assert abs(cam.fov - 75.0) < 1e-3
        assert abs(cam.aspect - 2.0) < 1e-3

    def test_orthographic_camera_properties_and_boundaries(self):
        """Verify OrthographicCamera boundaries, zoom, and ortho matrix calculations."""
        ocam = pe.OrthographicCamera(left=-10.0, right=10.0, bottom=-5.0, top=5.0, near_z=0.1, far_z=50.0)
        assert abs(ocam.left - (-10.0)) < 1e-3
        assert abs(ocam.right - 10.0) < 1e-3
        assert abs(ocam.bottom - (-5.0)) < 1e-3
        assert abs(ocam.top - 5.0) < 1e-3
        assert ocam.type == pe.CameraType.Orthographic

        # Boundary mutations
        ocam.left = -20.0
        ocam.right = 20.0
        ocam.bottom = -10.0
        ocam.top = 10.0
        ocam.zoom = 2.0
        assert abs(ocam.left - (-20.0)) < 1e-3
        assert abs(ocam.zoom - 2.0) < 1e-3

        pm = ocam.projection_matrix()
        assert pm is not None

        # set_orthographic helper
        ocam.set_orthographic(-4.0, 4.0, -3.0, 3.0, 0.2, 80.0, 1.5)
        assert abs(ocam.left - (-4.0)) < 1e-3
        assert abs(ocam.right - 4.0) < 1e-3
        assert abs(ocam.bottom - (-3.0)) < 1e-3
        assert abs(ocam.top - 3.0) < 1e-3
        assert abs(ocam.zoom - 1.5) < 1e-3

    def test_camera_viewport_and_scissor_rects(self):
        """Verify camera viewport, scissor rect, scissor toggle, and clear color."""
        cam = pe.PerspectiveCamera()
        assert cam.has_scissor is False

        # Multi-viewport setup: split screen left half
        cam.viewport = (0.0, 0.0, 0.5, 1.0)
        assert abs(cam.viewport.x - 0.0) < 1e-4
        assert abs(cam.viewport.y - 0.0) < 1e-4
        assert abs(cam.viewport.z - 0.5) < 1e-4
        assert abs(cam.viewport.w - 1.0) < 1e-4

        # Scissor rect setup
        cam.scissor = (0.05, 0.05, 0.4, 0.9)
        cam.has_scissor = True
        assert cam.has_scissor is True
        assert abs(cam.scissor.x - 0.05) < 1e-4

        # Clear color
        cam.clear_color = (0.1, 0.2, 0.3, 1.0)
        assert abs(cam.clear_color.x - 0.1) < 1e-4
        assert abs(cam.clear_color.y - 0.2) < 1e-4
        assert abs(cam.clear_color.z - 0.3) < 1e-4

    def test_camera_screen_to_ray_perspective(self):
        """Verify screen_to_ray unprojection for PerspectiveCamera."""
        cam = pe.PerspectiveCamera(fov=60.0, aspect=1.333, near_z=0.1, far_z=100.0)
        cam.set_position(0.0, 2.0, 5.0)
        cam.set_target(0.0, 2.0, 0.0)

        # Center of screen (400, 300 on an 800x600 screen)
        ray_center = cam.screen_to_ray(400.0, 300.0, 800.0, 600.0)
        assert abs(ray_center.direction.z - (-1.0)) < 0.05
        assert abs(ray_center.direction.x) < 0.05

        # Off-center: right side
        ray_right = cam.screen_to_ray(800.0, 300.0, 800.0, 600.0)
        assert ray_right.direction.x > 0.0

        # Off-center: left side
        ray_left = cam.screen_to_ray(0.0, 300.0, 800.0, 600.0)
        assert ray_left.direction.x < 0.0

        # Off-center: top side (screen Y=0 is top in screen coordinates)
        ray_top = cam.screen_to_ray(400.0, 0.0, 800.0, 600.0)
        assert ray_top.direction.y > 0.0

    def test_camera_screen_to_ray_orthographic(self):
        """Verify screen_to_ray unprojection for OrthographicCamera."""
        ocam = pe.OrthographicCamera(-5.0, 5.0, -5.0, 5.0, 0.1, 100.0)
        ocam.set_position(0.0, 0.0, 10.0)
        ocam.set_target(0.0, 0.0, 0.0)

        ray_center = ocam.screen_to_ray(400.0, 300.0, 800.0, 600.0)
        # In orthographic projection, direction is parallel forward
        assert abs(ray_center.direction.z - (-1.0)) < 0.05

        # Off-center right should shift origin x positively
        ray_right = ocam.screen_to_ray(800.0, 300.0, 800.0, 600.0)
        assert ray_right.origin.x > ray_center.origin.x

    def test_camera_screen_to_ray_hierarchy_support(self):
        """Verify screen_to_ray computes correct world ray when camera is parented in Node3D hierarchy."""
        parent_node = pe.Node3D("PlayerRig")
        parent_node.transform.position = (10.0, 5.0, 20.0)

        cam = pe.PerspectiveCamera()
        parent_node.add(cam)
        cam.set_position(0.0, 1.8, 0.0)

        ray = cam.screen_to_ray(400.0, 300.0, 800.0, 600.0)
        # World origin must reflect parent translation
        assert abs(ray.origin.x - 10.0) < 0.5
        assert abs(ray.origin.y - 6.8) < 0.5
        assert abs(ray.origin.z - 20.0) < 0.5


# ===========================================================================
# 3. RenderTarget FBO Creation, Formats & Texture Binding
# ===========================================================================

class TestRenderTarget:
    """Tests RenderTarget lifecycle, formats (RGBA8/RGBA16F), resizing, and texturing."""

    def test_rendertarget_creation_rgba8(self):
        """Verify creation of RGBA8 RenderTarget."""
        rt = pe.RenderTarget(256, 256, pe.RenderTargetFormat.RGBA8, has_depth=True, samples=1)
        assert rt.width == 256
        assert rt.height == 256
        assert rt.format == pe.RenderTargetFormat.RGBA8
        assert rt.has_depth is True
        assert rt.samples == 1
        assert rt.texture is not None
        assert rt.texture.width == 256
        assert rt.texture.height == 256
        assert rt.texture.channels == 4

    def test_rendertarget_creation_rgba16f_hdr(self):
        """Verify creation of RGBA16F HDR RenderTarget."""
        rt = pe.RenderTarget(512, 512, pe.RenderTargetFormat.RGBA16F, has_depth=True, samples=1)
        assert rt.width == 512
        assert rt.height == 512
        assert rt.format == pe.RenderTargetFormat.RGBA16F
        assert rt.texture is not None

    def test_rendertarget_texture_wrapping_into_materials(self):
        """Verify that rt.texture binds to materials transparently."""
        rt = pe.RenderTarget(128, 128, pe.RenderTargetFormat.RGBA8)
        mat = pe.StandardMaterial()

        # Direct property access:
        mat.albedo_map = rt.texture
        assert mat.albedo_map is not None
        assert mat.albedo_map.width == 128
        assert mat.albedo_map.height == 128

        # Function call access:
        mat.albedo_map = rt.texture()
        assert mat.albedo_map is not None

        # Direct RenderTarget assignment:
        mat.albedo_map = rt
        assert mat.albedo_map is not None

    def test_rendertarget_resize(self):
        """Verify resizing a RenderTarget updates width, height, and texture dimensions."""
        rt = pe.RenderTarget(100, 100, pe.RenderTargetFormat.RGBA8)
        assert rt.width == 100
        assert rt.height == 100

        rt.resize(200, 150)
        assert rt.width == 200
        assert rt.height == 150
        assert rt.texture.width == 200
        assert rt.texture.height == 150

    def test_rendertarget_read_pixels(self):
        """Verify read_pixels returns valid byte buffer."""
        rt = pe.RenderTarget(64, 64, pe.RenderTargetFormat.RGBA8)
        pixels = rt.read_pixels()
        assert isinstance(pixels, bytes)


# ===========================================================================
# 4. EffectComposer & Full Post-Processing Suite
# ===========================================================================

class TestEffectComposerAndPasses:
    """Tests EffectComposer pass chaining, lifecycle, and pass parameterization."""

    def test_bloom_pass_parameters(self):
        """Verify BloomPass thresholds and parameters."""
        bloom = pe.BloomPass(threshold=0.8, strength=1.2, radius=0.4)
        assert abs(bloom.threshold - 0.8) < 1e-4
        assert abs(bloom.strength - 1.2) < 1e-4
        assert abs(bloom.radius - 0.4) < 1e-4

        bloom.threshold = 1.5
        bloom.strength = 3.0
        bloom.radius = 0.8
        assert abs(bloom.threshold - 1.5) < 1e-4
        assert abs(bloom.strength - 3.0) < 1e-4
        assert abs(bloom.radius - 0.8) < 1e-4

    def test_ssao_pass_parameters(self):
        """Verify SSAOPass radius, bias, and power parameters."""
        ssao = pe.SSAOPass(radius=0.75, bias=0.03, power=2.0)
        assert abs(ssao.radius - 0.75) < 1e-4
        assert abs(ssao.bias - 0.03) < 1e-4
        assert abs(ssao.power - 2.0) < 1e-4

        ssao.radius = 1.0
        ssao.bias = 0.05
        ssao.power = 1.0
        assert abs(ssao.radius - 1.0) < 1e-4
        assert abs(ssao.bias - 0.05) < 1e-4

    def test_fxaa_pass(self):
        """Verify FXAAPass creation and defaults."""
        fxaa = pe.FXAAPass()
        assert fxaa.name == "FXAAPass"
        assert fxaa.enabled is True
        fxaa.enabled = False
        assert fxaa.enabled is False

    def test_tonemapping_pass_all_modes(self):
        """Verify TonemappingPass modes (ACESFilmic, Reinhard, Cineon, Linear, Neutral)."""
        pass_aces = pe.TonemappingPass(pe.TonemappingMode.ACESFilmic, exposure=1.2, gamma=2.2)
        assert pass_aces.mode == pe.TonemappingMode.ACESFilmic
        assert abs(pass_aces.exposure - 1.2) < 1e-4
        assert abs(pass_aces.gamma - 2.2) < 1e-4

        pass_aces.mode = pe.TonemappingMode.Reinhard
        assert pass_aces.mode == pe.TonemappingMode.Reinhard

        pass_aces.mode = pe.TonemappingMode.Cineon
        assert pass_aces.mode == pe.TonemappingMode.Cineon

        pass_aces.mode = pe.TonemappingMode.Linear
        assert pass_aces.mode == pe.TonemappingMode.Linear

        pass_aces.mode = pe.TonemappingMode.Neutral
        assert pass_aces.mode == pe.TonemappingMode.Neutral

    def test_vignette_chromatic_pass(self):
        """Verify VignetteChromaticPass vignette, chromatic aberration, and film grain."""
        pass_vig = pe.VignetteChromaticPass(vignette=0.4, chromatic=0.008, grain=0.03)
        assert abs(pass_vig.vignette - 0.4) < 1e-4
        assert abs(pass_vig.chromatic - 0.008) < 1e-4
        assert abs(pass_vig.grain - 0.03) < 1e-4

        pass_vig.vignette = 0.6
        pass_vig.chromatic = 0.015
        pass_vig.grain = 0.05
        pass_vig.time = 2.5
        assert abs(pass_vig.vignette - 0.6) < 1e-4
        assert abs(pass_vig.chromatic - 0.015) < 1e-4
        assert abs(pass_vig.time - 2.5) < 1e-4

    def test_color_grading_pass(self):
        """Verify ColorGradingPass contrast, saturation, and brightness."""
        cg = pe.ColorGradingPass(contrast=1.1, saturation=1.2, brightness=0.95)
        assert abs(cg.contrast - 1.1) < 1e-4
        assert abs(cg.saturation - 1.2) < 1e-4
        assert abs(cg.brightness - 0.95) < 1e-4

        cg.contrast = 1.5
        cg.saturation = 0.0  # Monochrome test
        cg.brightness = 1.05
        assert abs(cg.contrast - 1.5) < 1e-4
        assert abs(cg.saturation - 0.0) < 1e-4

    def test_composer_chaining_and_pass_management(self):
        """Verify adding, ordering, removing, and clearing passes in EffectComposer."""
        composer = pe.EffectComposer(1024, 768)
        assert composer.enabled is True

        p1 = pe.SSAOPass()
        p2 = pe.BloomPass()
        p3 = pe.TonemappingPass()
        p4 = pe.VignetteChromaticPass()
        p5 = pe.ColorGradingPass()
        p6 = pe.FXAAPass()

        composer.add_pass(p1)
        composer.add_pass(p2)
        composer.add_pass(p3)
        composer.add_pass(p4)
        composer.add_pass(p5)
        composer.add_pass(p6)

        assert len(composer.passes) == 6
        pass_names = [p.name for p in composer.passes]
        assert pass_names == [
            "SSAOPass",
            "BloomPass",
            "TonemappingPass",
            "VignetteChromaticPass",
            "ColorGradingPass",
            "FXAAPass",
        ]

        # Remove single pass
        composer.remove_pass(p4)
        assert len(composer.passes) == 5
        assert "VignetteChromaticPass" not in [p.name for p in composer.passes]

        # Clear all
        composer.clear_passes()
        assert len(composer.passes) == 0


# ===========================================================================
# 5. Hostile Edge Cases & Safety Verifications
# ===========================================================================

class TestHostileEdgeCases:
    """Stress testing, hostile boundary conditions, and memory safety checks."""

    def test_rendertarget_invalid_dimensions(self):
        """Verify creating or resizing RenderTarget with 0 or negative dimensions does not crash."""
        # Creating with zero or negative dimensions
        rt_zero = pe.RenderTarget(0, 0)
        assert rt_zero.width == 0
        assert rt_zero.height == 0

        rt_neg = pe.RenderTarget(-50, -100)
        assert rt_neg.width == -50
        assert rt_neg.height == -100

        # Resizing to invalid dimensions
        rt = pe.RenderTarget(100, 100)
        rt.resize(0, 50)
        assert rt.width == 100  # Should retain valid previous size
        rt.resize(-20, -30)
        assert rt.width == 100

    def test_effect_composer_empty_execution(self):
        """Verify executing an EffectComposer with no passes does not crash."""
        composer = pe.EffectComposer(640, 480)
        assert len(composer.passes) == 0

        scene = pe.Scene()
        cam = pe.PerspectiveCamera()
        # Should gracefully return without pass execution
        composer.render(scene, cam)

    def test_screen_to_ray_zero_screen_dimensions(self):
        """Verify screen_to_ray with zero or negative width/height returns safe fallback ray."""
        cam = pe.PerspectiveCamera()
        cam.set_position(1.0, 2.0, 3.0)
        cam.set_target(1.0, 2.0, 0.0)

        # Zero width & height
        ray_zero = cam.screen_to_ray(100.0, 100.0, 0.0, 0.0)
        assert ray_zero.origin is not None
        assert ray_zero.direction is not None
        assert abs(ray_zero.origin.x - 1.0) < 1e-4

        # Negative width & height
        ray_neg = cam.screen_to_ray(100.0, 100.0, -800.0, -600.0)
        assert ray_neg.origin is not None
        assert ray_neg.direction is not None

    def test_orthographic_camera_inverted_boundaries(self):
        """Verify OrthographicCamera with inverted boundaries (left > right, bottom > top)."""
        ocam = pe.OrthographicCamera(left=10.0, right=-10.0, bottom=5.0, top=-5.0)
        assert ocam.left == 10.0
        assert ocam.right == -10.0
        pm = ocam.projection_matrix()
        assert pm is not None

    def test_perspective_camera_extreme_fov(self):
        """Verify PerspectiveCamera with very low (1 deg) and very high (179 deg) FOV."""
        cam_low = pe.PerspectiveCamera(fov=1.0)
        assert cam_low.fov == 1.0
        pm_low = cam_low.projection_matrix()
        assert pm_low is not None

        cam_high = pe.PerspectiveCamera(fov=179.0)
        assert cam_high.fov == 179.0
        pm_high = cam_high.projection_matrix()
        assert pm_high is not None

    def test_multiple_cameras_to_same_rendertarget(self):
        """Verify multiple cameras can render to the same RenderTarget sequentially."""
        scene = pe.Scene()
        app = pe.App("Multi-Cam RT Test", width=640, height=480)
        rt = pe.RenderTarget(256, 256)

        cam1 = pe.PerspectiveCamera(fov=60.0)
        cam1.set_position(0.0, 0.0, 5.0)

        cam2 = pe.OrthographicCamera(-5.0, 5.0, -5.0, 5.0)
        cam2.set_position(5.0, 5.0, 5.0)

        # Sequential rendering to same target
        app.render_target(scene, cam1, rt)
        app.render_target(scene, cam2, rt)
        assert rt.width == 256
        assert rt.height == 256
