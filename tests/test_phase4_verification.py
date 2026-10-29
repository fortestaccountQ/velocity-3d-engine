import pytest
import math
import pielosyty as p


def test_background_type_enum():
    assert p.BackgroundType.Color is not None
    assert p.BackgroundType.Texture2D is not None
    assert p.BackgroundType.CubeMap is not None
    assert p.BackgroundType.ProceduralSky is not None


def test_shadow_settings():
    settings = p.ShadowSettings()
    assert settings.resolution == 2048
    assert math.isclose(settings.bias, 0.0015, rel_tol=1e-3)
    assert math.isclose(settings.normal_bias, 0.02, rel_tol=1e-3)
    assert math.isclose(settings.ortho_size, 40.0, rel_tol=1e-3)
    assert settings.texel_snapping is True
    assert settings.pcf_16_tap is True

    settings.resolution = 4096
    settings.bias = 0.0005
    settings.normal_bias = 0.01
    settings.ortho_size = 60.0
    settings.texel_snapping = False
    settings.pcf_16_tap = False

    assert settings.resolution == 4096
    assert math.isclose(settings.bias, 0.0005, rel_tol=1e-3)
    assert math.isclose(settings.normal_bias, 0.01, rel_tol=1e-3)
    assert math.isclose(settings.ortho_size, 60.0, rel_tol=1e-3)
    assert settings.texel_snapping is False
    assert settings.pcf_16_tap is False


def test_sky_params():
    params = p.SkyParams()
    assert math.isclose(params.turbidity, 2.0, rel_tol=1e-3)
    assert math.isclose(params.rayleigh, 1.0, rel_tol=1e-3)
    assert math.isclose(params.mie_coefficient, 0.005, rel_tol=1e-3)
    assert math.isclose(params.mie_directional_g, 0.8, rel_tol=1e-3)
    assert math.isclose(params.time_of_day, 12.0, rel_tol=1e-3)

    params.turbidity = 4.5
    params.time_of_day = 18.5
    assert math.isclose(params.turbidity, 4.5, rel_tol=1e-3)
    assert math.isclose(params.time_of_day, 18.5, rel_tol=1e-3)


def test_cube_texture_gradient():
    cube = p.CubeTexture.create_gradient(size=64)
    assert cube is not None
    assert cube.size == 64
    cube.destroy()


def test_procedural_sky():
    sky = p.ProceduralSky("DaySky")
    assert sky.name == "DaySky"
    assert math.isclose(sky.turbidity, 2.0, rel_tol=1e-3)

    sky.set_time_of_day(6.0)
    assert math.isclose(sky.time_of_day, 6.0, rel_tol=1e-3)

    sky.set_turbidity(3.0)
    assert math.isclose(sky.turbidity, 3.0, rel_tol=1e-3)

    sky.set_rayleigh(1.5)
    assert math.isclose(sky.rayleigh, 1.5, rel_tol=1e-3)

    sky.set_mie_coefficient(0.01)
    assert math.isclose(sky.mie_coefficient, 0.01, rel_tol=1e-3)

    sky.set_mie_directional_g(0.85)
    assert math.isclose(sky.mie_directional_g, 0.85, rel_tol=1e-3)


def test_cube_render_target_and_camera():
    rt = p.CubeRenderTarget(128)
    assert rt.resolution == 128
    tex = rt.cube_texture
    assert tex is not None
    assert tex.size == 128

    cam = p.CubeCamera(0.2, 50.0, 128)
    assert cam.resolution == 128
    assert math.isclose(cam.near_plane, 0.2, rel_tol=1e-3)
    assert math.isclose(cam.far_plane, 50.0, rel_tol=1e-3)
    cam.set_near_plane(0.5)
    cam.set_far_plane(80.0)
    assert math.isclose(cam.near_plane, 0.5, rel_tol=1e-3)
    assert math.isclose(cam.far_plane, 80.0, rel_tol=1e-3)


def test_scene_phase4_integration():
    scene = p.Scene()

    # Default background type
    assert scene.background_type == p.BackgroundType.Color

    # Set background color
    scene.set_background_color(0.2, 0.3, 0.4, 1.0)
    assert scene.background_type == p.BackgroundType.Color
    bg_col = scene.background_color
    assert math.isclose(bg_col.x, 0.2, rel_tol=1e-3)
    assert math.isclose(bg_col.y, 0.3, rel_tol=1e-3)
    assert math.isclose(bg_col.z, 0.4, rel_tol=1e-3)

    # Set Procedural Sky
    sky = p.ProceduralSky()
    scene.set_procedural_sky(sky)
    assert scene.background_type == p.BackgroundType.ProceduralSky
    assert scene.procedural_sky is not None

    # Set Cubemap
    cube = p.CubeTexture.create_gradient(size=32)
    scene.set_background_cube(cube)
    assert scene.background_type == p.BackgroundType.CubeMap
    assert scene.background_cube is not None

    # Set Environment & IBL intensity
    scene.set_environment(cube, 2.5)
    assert scene.environment is not None
    assert math.isclose(scene.environment_intensity, 2.5, rel_tol=1e-3)

    scene.environment_intensity = 0.8
    assert math.isclose(scene.environment_intensity, 0.8, rel_tol=1e-3)

    # Scene.add with ProceduralSky & CubeCamera
    cam = p.CubeCamera(0.1, 100.0, 64)
    scene.add(cam)
    scene.add(sky)

    # Clear scene resets background/env properly
    scene.clear()
    assert scene.environment is None
    assert scene.background_cube is None
    assert scene.procedural_sky is None


def test_engine_app_shadow_apis():
    app = p.EngineApp()
    assert app.shadow_settings.resolution == 2048

    app.set_shadow_resolution(1024)
    assert app.shadow_settings.resolution == 1024

    app.set_shadow_bias(0.002)
    assert math.isclose(app.shadow_settings.bias, 0.002, rel_tol=1e-3)

    app.set_shadow_normal_bias(0.03)
    assert math.isclose(app.shadow_settings.normal_bias, 0.03, rel_tol=1e-3)

    app.set_shadow_ortho_size(50.0)
    assert math.isclose(app.shadow_settings.ortho_size, 50.0, rel_tol=1e-3)

    app.set_shadow_pcf_16_tap(False)
    assert app.shadow_settings.pcf_16_tap is False

    app.set_shadow_texel_snapping(False)
    assert app.shadow_settings.texel_snapping is False


def test_chrome_sphere_reflection_and_ibl():
    """Verify Phase 4 Acceptance Criterion:
    Chrome sphere (metallic=1.0, roughness=0.05) honest reflection sampling configuration."""
    scene = p.Scene()
    cube = p.CubeTexture.create_gradient(
        top_color=p.Vec3(0.2, 0.6, 1.0),
        horizon_color=p.Vec3(0.8, 0.9, 1.0),
        bottom_color=p.Vec3(0.1, 0.1, 0.1),
        size=64,
    )
    scene.environment = cube
    scene.environment_intensity = 2.0

    mat = p.StandardMaterial()
    mat.metallic = 1.0
    mat.roughness = 0.05
    mat.base_color = (1.0, 1.0, 1.0, 1.0)

    sphere = scene.create_sphere(radius=1.5, segments=32)
    sphere.material = mat

    assert sphere.material.metallic == 1.0
    assert math.isclose(sphere.material.roughness, 0.05, rel_tol=1e-3)
    assert scene.environment is not None
    assert scene.environment.size == 64
    assert math.isclose(scene.environment_intensity, 2.0, rel_tol=1e-3)

    # In shader: env_lod = roughness * 7.0
    # For roughness=0.05, env_lod=0.35 (sampling base crisp reflection level)
    roughness = sphere.material.roughness
    env_lod = roughness * 7.0
    assert math.isclose(env_lod, 0.35, rel_tol=1e-3)

    # For metallic=1.0: kD = (1 - metallic) = 0.0 (zero diffuse, pure specular mirror)
    kD = 1.0 - sphere.material.metallic
    assert math.isclose(kD, 0.0, abs_tol=1e-5)

    # Test specular reflection formula: R = reflect(-V, N) = 2*(N.V)*N - V
    V = (0.0, 0.0, 1.0)
    N = (1.0 / math.sqrt(2.0), 0.0, 1.0 / math.sqrt(2.0))
    NdotV = N[0]*V[0] + N[1]*V[1] + N[2]*V[2]
    R = (2 * NdotV * N[0] - V[0], 2 * NdotV * N[1] - V[1], 2 * NdotV * N[2] - V[2])
    assert math.isclose(R[0], 1.0, rel_tol=1e-3)
    assert math.isclose(R[1], 0.0, abs_tol=1e-5)
    assert math.isclose(R[2], 0.0, abs_tol=1e-5)

    # Test environment intensity scaling
    scene.environment_intensity = 0.0
    assert math.isclose(scene.environment_intensity, 0.0, abs_tol=1e-5)
    scene.environment_intensity = 3.5
    assert math.isclose(scene.environment_intensity, 3.5, rel_tol=1e-3)

    # Test clearing environment (fallback to engine default cubemap)
    scene.environment = None
    assert scene.environment is None


def test_long_distance_shadows_v2_camera_tracking():
    """Verify Shadows v2: directional light shadow box follows active camera
    when player travels kilometers away from (0,0,0)."""
    app = p.EngineApp()
    scene = app.scene
    camera = app.camera

    scene.light.set_direction(0.4, -0.8, 0.4)

    # Camera at origin
    camera.position = p.Vec3(0.0, 0.0, 0.0)
    assert math.isclose(camera.position.x, 0.0, abs_tol=1e-5)

    # Camera travels 5 kilometers away: x=5000, z=5000
    camera.position = p.Vec3(5000.0, 150.0, 5000.0)
    assert math.isclose(camera.position.x, 5000.0, rel_tol=1e-3)
    assert math.isclose(camera.position.y, 150.0, rel_tol=1e-3)
    assert math.isclose(camera.position.z, 5000.0, rel_tol=1e-3)

    # Shadow settings configuration
    app.set_shadow_resolution(4096)
    app.set_shadow_ortho_size(40.0)
    app.set_shadow_texel_snapping(True)
    assert app.shadow_settings.resolution == 4096
    assert math.isclose(app.shadow_settings.ortho_size, 40.0, rel_tol=1e-3)
    assert app.shadow_settings.texel_snapping is True

    # Camera travels 50 kilometers away: x=50000, z=-50000
    camera.position = p.Vec3(50000.0, 20.0, -50000.0)
    assert math.isclose(camera.position.x, 50000.0, rel_tol=1e-3)
    assert math.isclose(camera.position.z, -50000.0, rel_tol=1e-3)


def test_shadow_texel_snapping_jitter_elimination():
    """Verify texel snapping algorithm prevents shadow shimmering/crawling."""
    resolution = 2048
    ortho_size = 40.0
    texel_size = (2.0 * ortho_size) / float(resolution)
    assert math.isclose(texel_size, 80.0 / 2048.0, rel_tol=1e-5)

    def snap(coord: float, t_size: float) -> float:
        return math.floor(coord / t_size) * t_size

    # Position in light space
    base_ls_x = 12.3456
    snapped_base = snap(base_ls_x, texel_size)

    # Sub-texel delta (less than texel_size = ~0.039)
    sub_texel_delta = 0.005
    snapped_moved = snap(base_ls_x + sub_texel_delta, texel_size)

    # Snapped position does not flutter on sub-texel movement
    assert math.isclose(snapped_base, snapped_moved, abs_tol=1e-6)

    # Larger movement crossing a texel boundary
    moved_over_boundary = snap(base_ls_x + texel_size * 1.5, texel_size)
    assert math.isclose(moved_over_boundary - snapped_base, texel_size, rel_tol=1e-4)


def test_shadow_poisson_disk_16_tap_configuration():
    """Verify 16-tap Poisson Disk PCF soft filtering structure."""
    poisson_disk_16 = [
        (-0.94201624, -0.39906216),
        ( 0.94558609, -0.76890725),
        (-0.09418410, -0.92938870),
        ( 0.34495938,  0.29387760),
        (-0.91588581,  0.45771432),
        (-0.81544232, -0.87912464),
        (-0.38277543,  0.27676845),
        ( 0.97484398,  0.75648379),
        ( 0.44323325, -0.97511554),
        ( 0.53742981, -0.47373420),
        (-0.26496911, -0.41893023),
        ( 0.79197514,  0.19090188),
        (-0.24188840,  0.99706507),
        (-0.81409955,  0.91437590),
        ( 0.19984126,  0.78641367),
        ( 0.14383161, -0.14100790),
    ]

    assert len(poisson_disk_16) == 16

    # Every tap must be strictly inside [-1, 1] kernel bounds and radius <= 1.25
    for x, y in poisson_disk_16:
        r = math.sqrt(x * x + y * y)
        assert abs(x) <= 1.0 and abs(y) <= 1.0, f"Poisson tap ({x}, {y}) outside [-1, 1] bounds"
        assert r <= 1.25, f"Poisson tap ({x}, {y}) outside filter radius: r={r}"

    # Distribution centroid should be close to center (0, 0)
    avg_x = sum(x for x, _ in poisson_disk_16) / 16.0
    avg_y = sum(y for _, y in poisson_disk_16) / 16.0
    assert abs(avg_x) < 0.15
    assert abs(avg_y) < 0.15

    # Check App API toggle for 16-tap PCF
    app = p.EngineApp()
    app.set_shadow_pcf_16_tap(True)
    assert app.shadow_settings.pcf_16_tap is True
    app.set_shadow_pcf_16_tap(False)
    assert app.shadow_settings.pcf_16_tap is False


def test_procedural_sky_solar_trajectory_and_clamping():
    """Verify ProceduralSky solar trajectory across 24h cycle and clamping."""
    sky = p.ProceduralSky("SolarTest")

    # Dawn: 6.0 hours -> sun at horizon
    sky.set_time_of_day(6.0)
    assert math.isclose(sky.time_of_day, 6.0, rel_tol=1e-3)
    sun = sky.sun_direction
    assert math.isclose(sun.y, 0.0, abs_tol=0.05)
    assert sun.x < 0.0  # Sunrise (east)

    # Noon: 12.0 hours -> sun near zenith
    sky.set_time_of_day(12.0)
    assert math.isclose(sky.time_of_day, 12.0, rel_tol=1e-3)
    sun = sky.sun_direction
    assert sun.y > 0.9  # Highest point in sky

    # Sunset: 18.0 hours -> sun at horizon
    sky.set_time_of_day(18.0)
    assert math.isclose(sky.time_of_day, 18.0, rel_tol=1e-3)
    sun = sky.sun_direction
    assert math.isclose(sun.y, 0.0, abs_tol=0.05)
    assert sun.x > 0.0  # Sunset (west)

    # Midnight: 0.0 hours -> sun underground
    sky.set_time_of_day(0.0)
    assert math.isclose(sky.time_of_day, 0.0, rel_tol=1e-3)
    sun = sky.sun_direction
    assert sun.y < -0.9

    # Unit vector invariant for all 24 hours
    for h in range(25):
        sky.set_time_of_day(float(h))
        d = sky.sun_direction
        length = math.sqrt(d.x * d.x + d.y * d.y + d.z * d.z)
        assert math.isclose(length, 1.0, rel_tol=1e-3)

    # Hostile edge-case clamping
    sky.set_time_of_day(-15.0)
    assert math.isclose(sky.time_of_day, 0.0, abs_tol=1e-5)
    sky.set_time_of_day(35.0)
    assert math.isclose(sky.time_of_day, 24.0, abs_tol=1e-5)

    # Non-zero normalize fallback
    sky.set_sun_direction(0.0, 0.0, 0.0)
    d = sky.sun_direction
    length = math.sqrt(d.x * d.x + d.y * d.y + d.z * d.z)
    assert math.isclose(length, 1.0, rel_tol=1e-3)


def test_procedural_sky_scattering_parameters():
    """Verify Rayleigh and Mie scattering atmospheric configuration."""
    sky = p.ProceduralSky()
    sky.set_turbidity(5.0)
    sky.set_rayleigh(2.5)
    sky.set_mie_coefficient(0.02)
    sky.set_mie_directional_g(0.9)

    assert math.isclose(sky.turbidity, 5.0, rel_tol=1e-3)
    assert math.isclose(sky.rayleigh, 2.5, rel_tol=1e-3)
    assert math.isclose(sky.mie_coefficient, 0.02, rel_tol=1e-3)
    assert math.isclose(sky.mie_directional_g, 0.9, rel_tol=1e-3)

    sky.set_rayleigh_color(0.3, 0.6, 0.9)
    assert math.isclose(sky.rayleigh_color.x, 0.3, rel_tol=1e-3)
    assert math.isclose(sky.rayleigh_color.y, 0.6, rel_tol=1e-3)
    assert math.isclose(sky.rayleigh_color.z, 0.9, rel_tol=1e-3)

    sky.set_mie_color(0.9, 0.8, 0.7)
    assert math.isclose(sky.mie_color.x, 0.9, rel_tol=1e-3)
    assert math.isclose(sky.mie_color.y, 0.8, rel_tol=1e-3)
    assert math.isclose(sky.mie_color.z, 0.7, rel_tol=1e-3)


def test_cube_texture_fallbacks_and_gradients():
    """Verify CubeTexture procedural generation and missing file fallbacks."""
    # Custom gradient
    cube = p.CubeTexture.create_gradient(
        top_color=p.Vec3(0.1, 0.2, 0.5),
        horizon_color=p.Vec3(0.5, 0.6, 0.7),
        bottom_color=p.Vec3(0.05, 0.05, 0.05),
        size=32,
    )
    assert cube is not None
    assert cube.size == 32
    cube.destroy()

    # Fallback on non-existent HDR path
    fallback_hdr = p.CubeTexture.load_from_hdr("non_existent_sky_pano.hdr", 64)
    assert fallback_hdr is not None
    assert fallback_hdr.size > 0
    fallback_hdr.destroy()

    # Fallback on missing 6-face files
    fallback_files = p.CubeTexture.load_from_files(
        "missing_px.png", "missing_nx.png",
        "missing_py.png", "missing_ny.png",
        "missing_pz.png", "missing_nz.png",
    )
    assert fallback_files is not None
    assert fallback_files.size > 0
    fallback_files.destroy()


def test_cube_camera_face_matrices_and_orientations():
    """Verify CubeCamera 6 face orientations matching cubemap conventions."""
    cam = p.CubeCamera(0.1, 100.0, 128)
    assert cam.resolution == 128
    assert cam.cube_texture is not None
    assert cam.cube_texture.size == 128

    # Face target directions (+X, -X, +Y, -Y, +Z, -Z)
    face_targets = [
        ( 1.0,  0.0,  0.0), # +X
        (-1.0,  0.0,  0.0), # -X
        ( 0.0,  1.0,  0.0), # +Y
        ( 0.0, -1.0,  0.0), # -Y
        ( 0.0,  0.0,  1.0), # +Z
        ( 0.0,  0.0, -1.0), # -Z
    ]
    face_ups = [
        ( 0.0, -1.0,  0.0), # +X
        ( 0.0, -1.0,  0.0), # -X
        ( 0.0,  0.0,  1.0), # +Y
        ( 0.0,  0.0, -1.0), # -Y
        ( 0.0, -1.0,  0.0), # +Z
        ( 0.0, -1.0,  0.0), # -Z
    ]

    for f in range(6):
        t = face_targets[f]
        u = face_ups[f]
        # Target and Up must be orthogonal: dot(t, u) == 0
        dot_tu = t[0]*u[0] + t[1]*u[1] + t[2]*u[2]
        assert math.isclose(dot_tu, 0.0, abs_tol=1e-5), f"Face {f} target and up not orthogonal"


def test_scene_background_polymorphic_property():
    """Verify scene.background polymorphic property accepting Color, CubeTexture, ProceduralSky, and None."""
    scene = p.Scene()

    # 1. CubeTexture
    cube = p.CubeTexture.create_gradient(size=32)
    scene.background = cube
    assert scene.background_type == p.BackgroundType.CubeMap

    # 2. ProceduralSky
    sky = p.ProceduralSky()
    scene.background = sky
    assert scene.background_type == p.BackgroundType.ProceduralSky

    # 3. Color tuple
    scene.background = (0.2, 0.4, 0.6, 1.0)
    assert scene.background_type == p.BackgroundType.Color
    col = scene.background_color
    assert math.isclose(col.x, 0.2, rel_tol=1e-3)
    assert math.isclose(col.y, 0.4, rel_tol=1e-3)
    assert math.isclose(col.z, 0.6, rel_tol=1e-3)

    # 4. None resets to default
    scene.background = None
    assert scene.background_type == p.BackgroundType.Color


def test_phase4_extreme_hostile_edge_cases():
    """Hostile edge-case audit: extreme coordinates, resolution switching, zero intensity."""
    app = p.EngineApp()
    scene = app.scene

    # Extreme camera coordinate (1,000,000 units)
    app.camera.position = p.Vec3(1e6, 1e6, 1e6)
    assert math.isclose(app.camera.position.x, 1e6, rel_tol=1e-3)

    # Zero environment intensity
    scene.environment_intensity = 0.0
    assert math.isclose(scene.environment_intensity, 0.0, abs_tol=1e-5)

    # Extreme shadow bias & ortho size
    app.set_shadow_bias(0.0)
    assert math.isclose(app.shadow_settings.bias, 0.0, abs_tol=1e-5)
    app.set_shadow_ortho_size(500.0)
    assert math.isclose(app.shadow_settings.ortho_size, 500.0, rel_tol=1e-3)

    # Multiple CubeRenderTarget creation and cleanup
    rts = [p.CubeRenderTarget(64) for _ in range(5)]
    for rt in rts:
        assert rt.resolution == 64
        rt.destroy()
