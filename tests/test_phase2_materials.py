"""Comprehensive Unit Tests for Phase 2:
- Task 2.1: Analytical Tangents & Handedness on all Primitive Meshes
- Task 2.2: Material Hierarchy, PBR Cook-Torrance & PipelineManager
- Task 2.3: Texture & DataTexture API with Wrap & Filter Modes
- Task 2.4: Multi-Light System (Directional, Point, Spot, Hemisphere, Ambient)
- Task 2.5: Render Queues & Transparency Blending Contracts
"""

import math
import pytest
import pielosyty as pe


def test_analytical_tangents_box():
    """Verify analytical tangents on box geometry have unit length and valid handedness."""
    mesh = pe.Mesh.create_box(1.0, 1.0, 1.0)
    verts = mesh.cpu_vertices
    assert len(verts) == 24  # 6 faces * 4 vertices
    
    for v in verts:
        tx, ty, tz, tw = v.tangent.x, v.tangent.y, v.tangent.z, v.tangent.w
        t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
        assert abs(t_len - 1.0) < 1e-3, f"Tangent {tx, ty, tz} not normalized"
        assert abs(abs(tw) - 1.0) < 1e-3, f"Handedness {tw} must be +1 or -1"
        
        # Tangent must be orthogonal to normal
        dot = tx * v.normal.x + ty * v.normal.y + tz * v.normal.z
        assert abs(dot) < 1e-3, f"Tangent and normal not orthogonal: dot={dot}"


def test_analytical_tangents_sphere():
    """Verify analytical tangents on sphere geometry."""
    mesh = pe.Mesh.create_sphere(1.0, 16, 16)
    verts = mesh.cpu_vertices
    assert len(verts) > 0
    
    for v in verts:
        tx, ty, tz, tw = v.tangent.x, v.tangent.y, v.tangent.z, v.tangent.w
        t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
        assert abs(t_len - 1.0) < 1e-3, f"Tangent {tx, ty, tz} not normalized"
        assert abs(abs(tw) - 1.0) < 1e-3, f"Handedness {tw} must be +1 or -1"


def test_analytical_tangents_plane():
    """Verify analytical tangents on plane geometry point along positive X axis."""
    mesh = pe.Mesh.create_plane(10.0, 10.0, 2, 2)
    verts = mesh.cpu_vertices
    assert len(verts) > 0
    
    for v in verts:
        # Plane normal is (0, 1, 0), tangent should be (1, 0, 0, 1)
        assert abs(v.tangent.x - 1.0) < 1e-3
        assert abs(v.tangent.y) < 1e-3
        assert abs(v.tangent.z) < 1e-3
        assert abs(v.tangent.w - 1.0) < 1e-3
        assert abs(v.normal.y - 1.0) < 1e-3


def test_analytical_tangents_cylinder():
    """Verify analytical tangents on cylinder geometry."""
    mesh = pe.Mesh.create_cylinder(0.5, 2.0, 16, True)
    verts = mesh.cpu_vertices
    assert len(verts) > 0
    
    for v in verts:
        tx, ty, tz, tw = v.tangent.x, v.tangent.y, v.tangent.z, v.tangent.w
        t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
        assert abs(t_len - 1.0) < 1e-3, f"Tangent {tx, ty, tz} not normalized"
        assert abs(abs(tw) - 1.0) < 1e-3, f"Handedness {tw} must be +1 or -1"


def test_texture_and_datatexture_api():
    """Verify DataTexture creation and texture wrap/filter parameters."""
    raw_data = bytes([
        255, 0, 0, 255,   0, 255, 0, 255,
        0, 0, 255, 255,   255, 255, 0, 255
    ])
    tex = pe.Texture.create_data_texture(2, 2, raw_data, 4)
    assert tex is not None
    assert tex.width == 2
    assert tex.height == 2
    assert tex.channels == 4

    # Wrap and filter configuration
    tex.wrap_s = pe.TextureWrap.Repeat
    tex.wrap_t = pe.TextureWrap.ClampToEdge
    tex.filter_min = pe.TextureFilter.Linear
    tex.filter_mag = pe.TextureFilter.Nearest

    assert tex.wrap_s == pe.TextureWrap.Repeat
    assert tex.wrap_t == pe.TextureWrap.ClampToEdge
    assert tex.filter_min == pe.TextureFilter.Linear
    assert tex.filter_mag == pe.TextureFilter.Nearest


def test_material_system_hierarchy():
    """Verify Material polymorphism, properties, and material types."""
    # StandardMaterial
    std_mat = pe.StandardMaterial()
    assert std_mat.type == pe.MaterialType.Standard
    std_mat.roughness = 0.35
    std_mat.metallic = 0.8
    std_mat.normal_scale = 1.2
    std_mat.ao_intensity = 0.75
    std_mat.emissive_intensity = 2.0
    std_mat.emissive_color = pe.Vec3(1.0, 0.5, 0.2)
    assert abs(std_mat.roughness - 0.35) < 1e-4
    assert abs(std_mat.metallic - 0.8) < 1e-4
    assert abs(std_mat.normal_scale - 1.2) < 1e-4

    # Blending and transparency
    std_mat.transparent = True
    std_mat.opacity = 0.5
    std_mat.side = pe.SideMode.Double
    std_mat.blend_mode = pe.BlendMode.Alpha
    assert std_mat.transparent is True
    assert abs(std_mat.opacity - 0.5) < 1e-4
    assert std_mat.side == pe.SideMode.Double
    assert std_mat.blend_mode == pe.BlendMode.Alpha

    # PhysicalMaterial
    phys_mat = pe.PhysicalMaterial()
    assert phys_mat.type == pe.MaterialType.Physical
    phys_mat.clearcoat = 0.9
    phys_mat.clearcoat_roughness = 0.1
    phys_mat.transmission = 0.85
    phys_mat.ior = 1.52
    phys_mat.sheen = pe.Vec3(0.5, 0.5, 0.5)
    phys_mat.sheen_roughness = 0.2
    assert abs(phys_mat.clearcoat - 0.9) < 1e-4
    assert abs(phys_mat.ior - 1.52) < 1e-4

    # UnlitMaterial
    unlit_mat = pe.UnlitMaterial()
    assert unlit_mat.type == pe.MaterialType.Unlit
    unlit_mat.wireframe = True
    assert unlit_mat.wireframe is True

    # LambertMaterial
    lambert_mat = pe.LambertMaterial()
    assert lambert_mat.type == pe.MaterialType.Lambert
    assert abs(lambert_mat.roughness - 1.0) < 1e-4

    # PhongMaterial
    phong_mat = pe.PhongMaterial()
    assert phong_mat.type == pe.MaterialType.Phong
    phong_mat.shininess = 64.0
    phong_mat.specular_color = pe.Vec3(0.8, 0.8, 0.8)
    assert abs(phong_mat.shininess - 64.0) < 1e-4

    # ToonMaterial
    toon_mat = pe.ToonMaterial()
    assert toon_mat.type == pe.MaterialType.Toon
    toon_mat.steps = 4
    assert toon_mat.steps == 4

    # ShaderMaterial
    shader_mat = pe.ShaderMaterial()
    assert shader_mat.type == pe.MaterialType.CustomShader
    shader_mat.vertex_shader = "// custom vs"
    shader_mat.fragment_shader = "// custom fs"
    shader_mat.uniforms = {"u_custom": pe.Vec4(1, 2, 3, 4)}
    assert shader_mat.vertex_shader == "// custom vs"
    assert "u_custom" in shader_mat.uniforms


def test_multi_light_system():
    """Verify all 5 light types and multi-light scene integration."""
    # DirectionalLight
    dir_light = pe.DirectionalLight("Sun", pe.Vec3(0.5, -1.0, 0.3), pe.Vec3(1.0, 0.95, 0.8), 1.5)
    assert dir_light.type == pe.LightType.Directional
    assert dir_light.cast_shadow is True
    assert abs(dir_light.intensity - 1.5) < 1e-4

    # PointLight
    pt_light = pe.PointLight("Torch", pe.Vec3(1.0, 0.6, 0.2), 2.0, 8.0, 1.5)
    assert pt_light.type == pe.LightType.Point
    assert abs(pt_light.range - 8.0) < 1e-4
    assert abs(pt_light.decay - 1.5) < 1e-4

    # SpotLight
    spot_light = pe.SpotLight("Flashlight", pe.Vec3(1.0, 1.0, 1.0), 3.0, 20.0)
    assert spot_light.type == pe.LightType.Spot
    spot_light.set_cone_angles(0.2, 0.5)
    assert abs(spot_light.inner_cone_angle - 0.2) < 1e-4
    assert abs(spot_light.outer_cone_angle - 0.5) < 1e-4

    # HemisphereLight
    hemi_light = pe.HemisphereLight("SkyGround", pe.Vec3(0.6, 0.7, 0.9), pe.Vec3(0.3, 0.2, 0.1), 0.8)
    assert hemi_light.type == pe.LightType.Hemisphere
    assert abs(hemi_light.sky_color.x - 0.6) < 1e-4
    assert abs(hemi_light.ground_color.x - 0.3) < 1e-4

    # AmbientLight
    amb_light = pe.AmbientLight("RoomAmbient", pe.Vec3(0.2, 0.2, 0.2), 0.3)
    assert amb_light.type == pe.LightType.Ambient
    assert abs(amb_light.intensity - 0.3) < 1e-4

    # Multi-Light scene registration
    scene = pe.Scene()
    scene.add_light(dir_light)
    scene.add_light(pt_light)
    scene.add_light(spot_light)
    scene.add_light(hemi_light)
    scene.add_light(amb_light)

    lights = scene.lights
    assert len(lights) == 5
    assert lights[0].name == "Sun"
    assert lights[1].name == "Torch"
    assert lights[2].name == "Flashlight"
    assert lights[3].name == "SkyGround"
    assert lights[4].name == "RoomAmbient"

    scene.remove_light(pt_light)
    assert len(scene.lights) == 4


def test_pipeline_manager():
    """Verify PipelineManager singleton and release_all method."""
    pm = pe.PipelineManager.instance()
    assert pm is not None
    pm.release_all()  # Should not raise exception


def test_gltf_pbr_model_loading():
    """Verify glTF loading populates analytical tangents and StandardMaterial."""
    from pathlib import Path
    duck_path = str(Path(__file__).resolve().parent.parent / "assets" / "duck.glb")
    scene = pe.Scene()
    duck = scene.load_model(duck_path)
    assert duck is not None
    assert len(duck.meshes) > 0

    ent = duck.meshes[0]
    assert ent.mesh is not None
    assert ent.material is not None
    assert ent.material.type == pe.MaterialType.Standard

    mesh = ent.mesh
    assert len(mesh.cpu_vertices) > 0
    for v in mesh.cpu_vertices[:50]:  # sample vertices
        tx, ty, tz, tw = v.tangent.x, v.tangent.y, v.tangent.z, v.tangent.w
        t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
        assert abs(t_len - 1.0) < 1e-2, f"Duck tangent not normalized: {t_len}"
        assert abs(abs(tw) - 1.0) < 1e-2, f"Duck handedness invalid: {tw}"
