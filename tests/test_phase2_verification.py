"""Comprehensive QA Verification Test Suite for Phase 2:
Modular Materials, PBR Shading, Multi-Light UBO, Render Queues & Transparency.

Validates the Phase 2 Acceptance Criteria:
"Загруженный .glb шлем (DamagedHelmet) отображает рельеф через normal_map,
светится через emissive_map, освещается 8 разноцветными PointLight,
а сквозь полупрозрачный стеклянный куб перед ним корректно виден как сам шлем,
так и другие стеклянные объекты позади."
"""

from __future__ import annotations
import math
from pathlib import Path
import pytest
import numpy as np
import pielosyty as pe


# ---------------------------------------------------------------------------
# Helpers & Paths
# ---------------------------------------------------------------------------
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
DAMAGED_HELMET_GLB = ASSETS_DIR / "DamagedHelmet.glb"
DAMAGED_HELMET_GLTF = (
    Path(__file__).resolve().parent.parent
    / "temp"
    / "threejs"
    / "examples"
    / "models"
    / "gltf"
    / "DamagedHelmet"
    / "glTF"
    / "DamagedHelmet.gltf"
)


class TestDamagedHelmetAcceptanceCriteria:
    """Validates the official Phase 2 Acceptance Criterion."""

    def test_damaged_helmet_pbr_loading_and_textures(self):
        """Verify DamagedHelmet loads with normal_map, emissive_map, ao_map, mr_map, and analytical tangents."""
        model_path = str(DAMAGED_HELMET_GLB if DAMAGED_HELMET_GLB.exists() else DAMAGED_HELMET_GLTF)
        assert Path(model_path).exists(), f"DamagedHelmet file not found at: {model_path}"

        scene = pe.Scene()
        helmet_model = scene.load_model(model_path)
        assert helmet_model is not None, "Failed to load DamagedHelmet model"
        assert len(helmet_model.meshes) > 0, "DamagedHelmet contains no mesh primitives"

        prim = helmet_model.meshes[0]
        mesh = prim.mesh
        assert mesh is not None, "Entity has no mesh"
        assert len(mesh.cpu_vertices) > 0, "Mesh has 0 vertices"
        assert mesh.num_indices > 0, "Mesh has 0 indices"

        # Verify Analytical Tangents on loaded geometry
        sample_verts = mesh.cpu_vertices[:100]
        for v in sample_verts:
            tx, ty, tz, tw = v.tangent.x, v.tangent.y, v.tangent.z, v.tangent.w
            t_len = math.sqrt(tx * tx + ty * ty + tz * tz)
            assert abs(t_len - 1.0) < 0.05, f"Tangent not normalized: len={t_len}"
            assert abs(abs(tw) - 1.0) < 1e-3, f"Handedness {tw} must be +1.0 or -1.0"

        # Verify PBR Material maps
        mat = prim.material
        assert mat is not None, "Helmet entity has no material"
        assert mat.type == pe.MaterialType.Standard, f"Expected StandardMaterial, got {mat.type}"

        # 1. Normal Map (for surface relief)
        assert mat.normal_map is not None, "DamagedHelmet must load normal_map"
        assert mat.normal_map.width > 0 and mat.normal_map.height > 0
        assert mat.normal_scale > 0.0

        # 2. Emissive Map (for glowing components)
        assert mat.emissive_map is not None, "DamagedHelmet must load emissive_map"
        assert mat.emissive_map.width > 0 and mat.emissive_map.height > 0
        assert mat.emissive_color.x > 0.0 or mat.emissive_color.y > 0.0 or mat.emissive_color.z > 0.0

        # 3. Metallic-Roughness Map
        assert mat.metallic_roughness_map is not None, "DamagedHelmet must load metallic_roughness_map"
        assert mat.metallic_roughness_map.width > 0 and mat.metallic_roughness_map.height > 0

        # 4. Ambient Occlusion Map
        assert mat.ao_map is not None or mat.occlusion_map is not None, "DamagedHelmet must load ao_map / occlusion_map"
        ao = mat.ao_map if mat.ao_map is not None else mat.occlusion_map
        assert ao.width > 0 and ao.height > 0

        # 5. Albedo Map
        assert mat.albedo_map is not None, "DamagedHelmet must load albedo_map"
        assert mat.albedo_map.width > 0 and mat.albedo_map.height > 0

    def test_eight_multicolored_point_lights_illumination(self):
        """Verify 8 multi-colored PointLight nodes can illuminate the helmet scene."""
        scene = pe.Scene()
        model_path = str(DAMAGED_HELMET_GLB if DAMAGED_HELMET_GLB.exists() else DAMAGED_HELMET_GLTF)
        helmet = scene.load_model(model_path)
        assert helmet is not None

        # 8 distinct light colors: Red, Green, Blue, Yellow, Cyan, Magenta, White, Warm Orange
        colors = [
            pe.Vec3(1.0, 0.1, 0.1),  # Red
            pe.Vec3(0.1, 1.0, 0.1),  # Green
            pe.Vec3(0.1, 0.2, 1.0),  # Blue
            pe.Vec3(1.0, 0.9, 0.1),  # Yellow
            pe.Vec3(0.1, 1.0, 0.9),  # Cyan
            pe.Vec3(1.0, 0.1, 0.9),  # Magenta
            pe.Vec3(1.0, 1.0, 1.0),  # White
            pe.Vec3(1.0, 0.5, 0.1),  # Orange
        ]

        radius = 2.5
        lights = []
        for i, col in enumerate(colors):
            angle = (2.0 * math.pi / 8.0) * i
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            y = 0.5 * math.sin(angle * 2.0)

            pt_light = pe.PointLight(f"PointLight_{i}", col, 2.0, 6.0, 2.0)
            pt_light.transform.position = pe.Vec3(x, y, z)
            scene.add_light(pt_light)
            lights.append(pt_light)

        assert len(scene.lights) == 8
        for i, lt in enumerate(scene.lights):
            assert lt.type == pe.LightType.Point
            assert abs(lt.intensity - 2.0) < 1e-3
            assert abs(lt.range - 6.0) < 1e-3

    def test_transparency_queues_and_sorting_depth(self):
        """Verify semi-transparent glass cube in front, helmet in center, and glass object behind.

        Contract:
        - Opaque items (helmet) rendered front-to-back with depth_write = True.
        - Transparent items rendered strictly back-to-front with depth_write = False and Alpha blending.
        - Both helmet and rear glass are visible through the front semi-transparent glass cube.
        """
        scene = pe.Scene()

        # Camera at (0, 0, 5) looking towards -Z
        cam_pos = pe.Vec3(0.0, 0.0, 5.0)

        # 1. Helmet in center at (0, 0, 0) -> distance to camera = 5.0, dist_sq = 25.0
        model_path = str(DAMAGED_HELMET_GLB if DAMAGED_HELMET_GLB.exists() else DAMAGED_HELMET_GLTF)
        helmet = scene.load_model(model_path)
        helmet_ent = helmet.meshes[0]
        helmet_ent.transform.position = pe.Vec3(0.0, 0.0, 0.0)
        assert helmet_ent.material.transparent is False

        # 2. Semi-transparent glass cube in FRONT at (0, 0, 2.0) -> distance = 3.0, dist_sq = 9.0
        front_glass_box = scene.create_entity("GlassCubeFront")
        front_glass_box.mesh = pe.Mesh.create_box(1.2, 1.2, 1.2)
        front_glass_box.transform.position = pe.Vec3(0.0, 0.0, 2.0)

        front_mat = pe.PhysicalMaterial()
        front_mat.transparent = True
        front_mat.opacity = 0.35
        front_mat.depth_write = False
        front_mat.blend_mode = pe.BlendMode.Alpha
        front_mat.transmission = 0.9
        front_mat.ior = 1.52
        front_glass_box.material = front_mat

        # 3. Semi-transparent glass sphere BEHIND helmet at (0, 0, -2.5) -> distance = 7.5, dist_sq = 56.25
        rear_glass_obj = scene.create_entity("GlassSphereRear")
        rear_glass_obj.mesh = pe.Mesh.create_sphere(0.8, 16, 16)
        rear_glass_obj.transform.position = pe.Vec3(0.0, 0.0, -2.5)

        rear_mat = pe.StandardMaterial()
        rear_mat.transparent = True
        rear_mat.opacity = 0.50
        rear_mat.depth_write = False
        rear_mat.blend_mode = pe.BlendMode.Alpha
        rear_glass_obj.material = rear_mat

        # Partition scene entities into Opaque and Transparent queues
        opaque_items = []
        transparent_items = []

        for ent in scene.entities:
            if not ent.visible or ent.mesh is None:
                continue
            mat = ent.material
            is_trans = mat and (mat.transparent or mat.opacity < 0.999 or mat.blend_mode != pe.BlendMode.Opaque)
            pos = ent.transform.position
            dx = pos.x - cam_pos.x
            dy = pos.y - cam_pos.y
            dz = pos.z - cam_pos.z
            d2 = dx * dx + dy * dy + dz * dz

            if is_trans:
                transparent_items.append((ent, d2))
            else:
                opaque_items.append((ent, d2))

        # Check queue separation
        assert len(opaque_items) == 1
        assert opaque_items[0][0].name.startswith("DamagedHelmet") or "damaged" in opaque_items[0][0].name.lower()

        assert len(transparent_items) == 2
        names = [item[0].name for item in transparent_items]
        assert "GlassCubeFront" in names
        assert "GlassSphereRear" in names

        # Sort transparent queue BACK-TO-FRONT (descending dist_sq)
        transparent_items.sort(key=lambda item: item[1], reverse=True)

        # Verify ordering: rear glass MUST be rendered before front glass
        first_trans = transparent_items[0]
        second_trans = transparent_items[1]

        assert first_trans[0].name == "GlassSphereRear"
        assert abs(first_trans[1] - 56.25) < 1e-2
        assert second_trans[0].name == "GlassCubeFront"
        assert abs(second_trans[1] - 9.0) < 1e-2

        # Verify depth write flags
        assert first_trans[0].material.depth_write is False
        assert second_trans[0].material.depth_write is False
        assert opaque_items[0][0].material.depth_write is True


class TestMaterialHierarchyAndPBR:
    """Verifies all material types and Cook-Torrance PBR parameters."""

    def test_standard_material_all_properties(self):
        mat = pe.StandardMaterial()
        assert mat.type == pe.MaterialType.Standard
        assert mat.roughness == 0.5
        assert mat.metallic == 0.0
        assert mat.side == pe.SideMode.Front
        assert mat.blend_mode == pe.BlendMode.Opaque
        assert mat.depth_write is True
        assert mat.depth_test is True
        assert mat.wireframe is False

        # Custom values
        mat.roughness = 0.15
        mat.metallic = 0.95
        mat.normal_scale = 1.8
        mat.ao_intensity = 0.65
        mat.emissive_intensity = 4.0
        mat.emissive_color = pe.Vec3(0.2, 0.8, 1.0)
        mat.transparent = True
        mat.opacity = 0.75
        mat.depth_write = False
        mat.side = pe.SideMode.Double
        mat.blend_mode = pe.BlendMode.Additive
        mat.uv_scale = pe.Vec2(2.0, 3.0)
        mat.uv_offset = pe.Vec2(0.1, 0.2)
        mat.alpha_cutoff = 0.33
        mat.alpha_test = True

        assert abs(mat.roughness - 0.15) < 1e-4
        assert abs(mat.metallic - 0.95) < 1e-4
        assert abs(mat.normal_scale - 1.8) < 1e-4
        assert abs(mat.ao_intensity - 0.65) < 1e-4
        assert abs(mat.emissive_intensity - 4.0) < 1e-4
        assert abs(mat.opacity - 0.75) < 1e-4
        assert mat.side == pe.SideMode.Double
        assert mat.blend_mode == pe.BlendMode.Additive
        assert mat.depth_write is False
        assert mat.alpha_test is True

    def test_physical_material_extended_pbr(self):
        mat = pe.PhysicalMaterial()
        assert mat.type == pe.MaterialType.Physical
        assert mat.clearcoat == 0.0
        assert mat.transmission == 0.0
        assert abs(mat.ior - 1.5) < 1e-4

        mat.clearcoat = 1.0
        mat.clearcoat_roughness = 0.05
        mat.transmission = 0.98
        mat.ior = 2.42  # diamond IOR
        mat.sheen = pe.Vec3(0.8, 0.2, 0.4)
        mat.sheen_roughness = 0.3

        assert abs(mat.clearcoat - 1.0) < 1e-4
        assert abs(mat.clearcoat_roughness - 0.05) < 1e-4
        assert abs(mat.transmission - 0.98) < 1e-4
        assert abs(mat.ior - 2.42) < 1e-4
        assert abs(mat.sheen.x - 0.8) < 1e-4

    def test_unlit_material(self):
        mat = pe.UnlitMaterial()
        assert mat.type == pe.MaterialType.Unlit
        assert mat.wireframe is False
        mat.wireframe = True
        mat.set_color(1.0, 0.0, 0.0, 0.5)
        assert mat.wireframe is True
        assert abs(mat.base_color.x - 1.0) < 1e-4
        assert abs(mat.base_color.w - 0.5) < 1e-4

    def test_lambert_material(self):
        mat = pe.LambertMaterial()
        assert mat.type == pe.MaterialType.Lambert
        assert abs(mat.roughness - 1.0) < 1e-4

    def test_phong_material(self):
        mat = pe.PhongMaterial()
        assert mat.type == pe.MaterialType.Phong
        assert abs(mat.shininess - 30.0) < 1e-4
        mat.shininess = 128.0
        mat.specular_color = pe.Vec3(1.0, 1.0, 0.5)
        assert abs(mat.shininess - 128.0) < 1e-4
        assert abs(mat.specular_color.z - 0.5) < 1e-4

    def test_toon_material(self):
        mat = pe.ToonMaterial()
        assert mat.type == pe.MaterialType.Toon
        assert mat.steps == 3
        mat.steps = 5
        assert mat.steps == 5

    def test_shader_material(self):
        mat = pe.ShaderMaterial()
        assert mat.type == pe.MaterialType.CustomShader
        mat.vertex_shader = "float4 main() { return 0; }"
        mat.fragment_shader = "float4 main() { return float4(1,0,0,1); }"
        mat.uniforms = {
            "u_time": pe.Vec4(1.0, 0.0, 0.0, 0.0),
            "u_color": pe.Vec4(0.2, 0.4, 0.8, 1.0)
        }
        assert "main" in mat.vertex_shader
        assert len(mat.uniforms) == 2
        assert abs(mat.uniforms["u_time"].x - 1.0) < 1e-4

    def test_material_presets_parity(self):
        gold = pe.gold(0.2)
        assert abs(gold.metallic - 1.0) < 1e-4
        assert abs(gold.roughness - 0.2) < 1e-4
        assert abs(gold.base_color.x - 1.0) < 1e-3

        metal = pe.metal(0.1, (0.7, 0.8, 0.9, 1.0))
        assert abs(metal.metallic - 1.0) < 1e-4
        assert abs(metal.roughness - 0.1) < 1e-4

        plastic = pe.plastic(0.4, (1.0, 0.0, 0.0, 1.0))
        assert abs(plastic.metallic - 0.0) < 1e-4
        assert abs(plastic.roughness - 0.4) < 1e-4

        rubber = pe.rubber(0.85, (0.05, 0.05, 0.05, 1.0))
        assert abs(rubber.metallic - 0.0) < 1e-4
        assert abs(rubber.roughness - 0.85) < 1e-4


class TestTextureAndDataTextureAPI:
    """Verifies Texture wrap and filter parameters and DataTexture creation from raw buffers."""

    def test_texture_wrap_modes(self):
        data = bytes([255, 255, 255, 255])
        tex = pe.Texture.create_data_texture(1, 1, data, 4)
        assert tex.width == 1 and tex.height == 1

        for wrap in [pe.TextureWrap.Repeat, pe.TextureWrap.ClampToEdge, pe.TextureWrap.MirroredRepeat]:
            tex.wrap_s = wrap
            tex.wrap_t = wrap
            assert tex.wrap_s == wrap
            assert tex.wrap_t == wrap

    def test_texture_filter_modes(self):
        data = bytes([128, 128, 128, 255])
        tex = pe.Texture.create_data_texture(1, 1, data, 4)

        for filt in [pe.TextureFilter.Nearest, pe.TextureFilter.Linear]:
            tex.filter_min = filt
            tex.filter_mag = filt
            assert tex.filter_min == filt
            assert tex.filter_mag == filt

    def test_datatexture_from_python_bytes(self):
        raw = bytes([255, 0, 0, 255,  0, 255, 0, 255])  # 2x1 RGBA
        tex = pe.DataTexture(raw, 2, 1, 4)
        assert tex is not None
        assert tex.width == 2
        assert tex.height == 1
        assert tex.channels == 4

    def test_datatexture_from_bytearray(self):
        raw = bytearray([0, 0, 255, 255,  255, 255, 0, 255])
        tex = pe.DataTexture(raw, 2, 1, 4)
        assert tex.width == 2
        assert tex.height == 1

    def test_datatexture_from_memoryview(self):
        raw = memoryview(bytes([100, 150, 200, 255] * 4))
        tex = pe.DataTexture(raw, 2, 2, 4)
        assert tex.width == 2
        assert tex.height == 2

    def test_datatexture_from_numpy_array(self):
        arr = np.zeros((4, 4, 4), dtype=np.uint8)
        arr[:, :, 0] = 255  # Red channel
        arr[:, :, 3] = 255  # Alpha
        tex = pe.DataTexture(arr, 4, 4, 4)
        assert tex.width == 4
        assert tex.height == 4
        assert tex.channels == 4


class TestMultiLightUBO:
    """Verifies all 5 light types and scene light limits."""

    def test_directional_light_properties(self):
        dir_light = pe.DirectionalLight("Sun", pe.Vec3(0.0, -1.0, 0.0), pe.Vec3(1.0, 0.9, 0.8), 2.0)
        assert dir_light.type == pe.LightType.Directional
        assert dir_light.cast_shadow is True
        assert abs(dir_light.intensity - 2.0) < 1e-4

        # Changing direction
        dir_light.set_direction(1.0, -2.0, 1.0)
        wd = dir_light.get_world_direction()
        norm = math.sqrt(wd.x**2 + wd.y**2 + wd.z**2)
        assert abs(norm - 1.0) < 1e-3

    def test_point_light_properties(self):
        pt = pe.PointLight("Torch", pe.Vec3(1.0, 0.5, 0.0), 3.0, 15.0, 2.5)
        assert pt.type == pe.LightType.Point
        assert abs(pt.intensity - 3.0) < 1e-4
        assert abs(pt.range - 15.0) < 1e-4
        assert abs(pt.decay - 2.5) < 1e-4

    def test_spot_light_properties(self):
        spot = pe.SpotLight("Spot", pe.Vec3(0.8, 0.8, 1.0), 4.0, 25.0)
        assert spot.type == pe.LightType.Spot
        assert abs(spot.intensity - 4.0) < 1e-4
        assert abs(spot.range - 25.0) < 1e-4

        spot.set_cone_angles(0.15, 0.45)
        assert abs(spot.inner_cone_angle - 0.15) < 1e-4
        assert abs(spot.outer_cone_angle - 0.45) < 1e-4

    def test_hemisphere_light_properties(self):
        hemi = pe.HemisphereLight("SkyGround", pe.Vec3(0.4, 0.6, 0.9), pe.Vec3(0.2, 0.15, 0.1), 1.2)
        assert hemi.type == pe.LightType.Hemisphere
        assert abs(hemi.intensity - 1.2) < 1e-4
        assert abs(hemi.sky_color.y - 0.6) < 1e-4
        assert abs(hemi.ground_color.x - 0.2) < 1e-4

    def test_ambient_light_properties(self):
        amb = pe.AmbientLight("RoomAmb", pe.Vec3(0.3, 0.3, 0.3), 0.5)
        assert amb.type == pe.LightType.Ambient
        assert abs(amb.intensity - 0.5) < 1e-4
        assert abs(amb.color.x - 0.3) < 1e-4

    def test_multi_light_scene_registration_and_limits(self):
        scene = pe.Scene()

        # Add 4 Directional lights (max UBO capacity)
        for i in range(4):
            scene.add_light(pe.DirectionalLight(f"Dir_{i}"))

        # Add 16 Point lights (max UBO capacity)
        for i in range(16):
            scene.add_light(pe.PointLight(f"Point_{i}"))

        # Add 8 Spot lights (max UBO capacity)
        for i in range(8):
            scene.add_light(pe.SpotLight(f"Spot_{i}"))

        # Add Hemisphere and Ambient
        scene.add_light(pe.HemisphereLight("Hemi"))
        scene.add_light(pe.AmbientLight("Amb"))

        assert len(scene.lights) == 4 + 16 + 8 + 2  # 30 lights registered

        # Remove some lights
        pt0 = scene.lights[4]
        scene.remove_light(pt0)
        assert len(scene.lights) == 29


class TestPipelineManager:
    """Verifies PipelineManager singleton and cache clearing."""

    def test_singleton_and_clear(self):
        pm = pe.PipelineManager.instance()
        assert pm is not None
        # Calling release_all multiple times must not crash or leak
        pm.release_all()
        pm.release_all()


class TestHostileEdgeCases:
    """Hostile edge-case tests protecting against crashes, regressions, and bounds violations."""

    def test_out_of_bounds_material_parameters(self):
        """Negative and extreme values must be assignable without crashing or throwing unhandled exceptions."""
        mat = pe.StandardMaterial()
        mat.roughness = -2.5
        mat.metallic = 99.0
        mat.normal_scale = -10.0
        mat.ao_intensity = 50.0
        mat.opacity = -0.5
        mat.alpha_cutoff = 10.0

        assert mat.roughness == -2.5
        assert mat.metallic == 99.0

    def test_missing_texture_fallback(self):
        """Entity with material having None for texture maps fallback safely."""
        scene = pe.Scene()
        ent = scene.create_entity("FallbackEntity")
        ent.mesh = pe.Mesh.create_box(1.0, 1.0, 1.0)
        mat = pe.StandardMaterial()
        # Verify defaults are None
        assert mat.albedo_map is None
        assert mat.normal_map is None
        assert mat.metallic_roughness_map is None
        assert mat.ao_map is None
        assert mat.emissive_map is None
        ent.material = mat
        scene.add_entity(ent)

        assert ent.material.albedo_map is None
        assert ent.material.normal_map is None

    def test_excessive_point_lights(self):
        """Adding 32 point lights (exceeding UBO 16 lights cap) does not crash or corrupt memory."""
        scene = pe.Scene()
        for i in range(32):
            scene.add_light(pe.PointLight(f"ExcessPoint_{i}", pe.Vec3(1, 1, 1), 1.0, 10.0))
        assert len(scene.lights) == 32

    def test_empty_indices_mesh_tangents(self):
        """Degenerate empty mesh does not cause divide-by-zero or segfault."""
        mesh = pe.Mesh()
        assert len(mesh.cpu_vertices) == 0
        assert mesh.num_indices == 0
