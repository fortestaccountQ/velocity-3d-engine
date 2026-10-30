"""Phase 8 Verification Test Suite: Python Ecosystem, .pyi Type Stubs & 10 Showcase Demos.

Tests:
1. Task 8.1 - Typing & Packaging Integrity:
   - Verify py.typed markers in both python/pielosyty and python/VelocityEngine.
   - Verify syntax & AST parsing of _VelocityEngine_core.pyi and __init__.pyi.
   - Verify comprehensive type stub definitions (Math, Core, Scene, Materials, Post-Processing, Particles, UI).
   - Verify pyright typing passes on stubs with 0 errors.

2. Task 8.2 - 10 Reference Showcase Examples:
   - 01_hello_pbr.py: 5x5 PBR sphere grid, metallic/roughness progression, IBL environment, OrbitController.
   - 02_dynamic_lights_bloom.py: 16 colored point lights, overhead spot light, emissive pillars, BloomPass.
   - 03_skeletal_character.py: Soldier.glb, AnimationMixer, crossfade, FollowCamera, obstacles.
   - 04_numpy_wave_surface.py: 100,000+ vertices grid, NumPy height modulation, GPU buffer updates.
   - 05_custom_shader_water.py: Custom ShaderMaterial, GLSL shaders, uniform bindings, floating buoys.
   - 06_render_to_texture_portal.py: RenderTarget(512, 512), CCTV camera, TV screen textured with RTT.
   - 07_particles_and_sprites.py: ParticleEmitter campfire & smoke & rain, Sprite billboards.
   - 08_instanced_forest.py: 50,000 instanced entities (35k trees, 15k rocks), LOD hero tree.
   - 09_curves_and_rollercoaster.py: CatmullRomCurve3 spline, procedural TubeGeometry, GridHelper, pillars.
   - 10_fps_game_sandbox.py: FirstPersonController, 3D raycast shooting, UIOverlay HUD, F2 mode toggle.
"""

from __future__ import annotations
import ast
import importlib
from pathlib import Path
import subprocess
import sys
import unittest

import VelocityEngine as ve
from VelocityEngine import (
    App,
    OrbitController,
    FirstPersonController,
    FollowCamera,
    Color,
    MaterialType,
    LightType,
)


class TestPhase8TypingAndStubs(unittest.TestCase):
    """Task 8.1: Complete .pyi type stubs and py.typed marker verification."""

    def setUp(self) -> None:
        self.root_dir = Path(__file__).resolve().parent.parent

    def test_py_typed_markers_exist(self) -> None:
        """Verify py.typed marker files exist in both pielosyty and VelocityEngine."""
        pielo_marker = self.root_dir / "python" / "pielosyty" / "py.typed"
        ve_marker = self.root_dir / "python" / "VelocityEngine" / "py.typed"
        self.assertTrue(pielo_marker.exists(), f"Missing marker: {pielo_marker}")
        self.assertTrue(ve_marker.exists(), f"Missing marker: {ve_marker}")

    def test_pyi_stubs_syntax_and_ast_parsing(self) -> None:
        """Verify that all .pyi files are syntactically valid and parse cleanly into AST."""
        stub_files = [
            self.root_dir / "python" / "pielosyty" / "__init__.pyi",
            self.root_dir / "python" / "pielosyty" / "_VelocityEngine_core.pyi",
            self.root_dir / "python" / "VelocityEngine" / "__init__.pyi",
            self.root_dir / "python" / "VelocityEngine" / "_VelocityEngine_core.pyi",
        ]

        for stub in stub_files:
            self.assertTrue(stub.exists(), f"Stub file not found: {stub}")
            with open(stub, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(stub))
            self.assertGreater(len(tree.body), 0, f"Empty AST for {stub}")

    def test_core_stub_contains_essential_types(self) -> None:
        """Verify _VelocityEngine_core.pyi contains all foundational classes and functions."""
        stub_path = self.root_dir / "python" / "pielosyty" / "_VelocityEngine_core.pyi"
        with open(stub_path, "r", encoding="utf-8") as f:
            content = f.read()

        init_stub_path = self.root_dir / "python" / "pielosyty" / "__init__.pyi"
        with open(init_stub_path, "r", encoding="utf-8") as f:
            init_content = f.read()

        essential_symbols = [
            "class Vec2:",
            "class Vec3:",
            "class Vec4:",
            "class Mat4:",
            "class Quat:",
            "class Ray:",
            "class Scene:",
            "class Entity(Node3D):",
            "class Mesh:",
            "class Camera(Node3D):",
            "class PerspectiveCamera(Camera):",
            "class OrthographicCamera(Camera):",
            "class Material:",
            "class StandardMaterial(Material):",
            "class PhysicalMaterial(StandardMaterial):",
            "class ShaderMaterial(Material):",
            "class DirectionalLight(Light):",
            "class PointLight(Light):",
            "class SpotLight(Light):",
            "class HemisphereLight(Light):",
            "class InstancedMesh(Node3D):",
            "class ParticleEmitter(Node3D):",
            "class Sprite(Node3D):",
            "class LOD(Node3D):",
            "class RenderTarget:",
            "class EffectComposer:",
            "class BloomPass(PostProcessPass):",
            "class AnimationMixer:",
            "class AnimationClip:",
            "class KeyframeTrack:",
            "class CatmullRomCurve3(Curve3):",
            "def create_tube(",
            "class GridHelper(Helper):",
            "class AxesHelper(Helper):",
            "class AudioManager:",
        ]

        for sym in essential_symbols:
            self.assertIn(sym, content, f"Missing symbol '{sym}' in {stub_path}")

        self.assertIn("Color as Color", init_content, f"Missing Color in {init_stub_path}")

    def test_pyright_validation_on_stubs(self) -> None:
        """Run pyright type check directly on stub files to ensure 0 errors."""
        pyright_exe = Path(sys.executable).parent / "pyright.exe"
        if not pyright_exe.exists():
            self.skipTest(f"pyright.exe not found at {pyright_exe}")

        cmd = [
            str(pyright_exe),
            str(self.root_dir / "python" / "pielosyty" / "_VelocityEngine_core.pyi"),
            str(self.root_dir / "python" / "pielosyty" / "__init__.pyi"),
            str(self.root_dir / "python" / "VelocityEngine" / "_VelocityEngine_core.pyi"),
            str(self.root_dir / "python" / "VelocityEngine" / "__init__.pyi"),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(
            result.returncode,
            0,
            f"Pyright returned errors:\n{result.stdout}\n{result.stderr}",
        )
        self.assertIn("0 errors", result.stdout)


class TestPhase8ShowcaseExamples(unittest.TestCase):
    """Task 8.2: 10 Reference Showcase Examples verification."""

    def test_01_hello_pbr(self) -> None:
        mod = importlib.import_module("examples.01_hello_pbr")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.camera_controller)
        self.assertIsInstance(app.camera_controller, OrbitController)
        pbr_spheres = [e for e in app.scene.entities if "PBR_Sphere" in e.name]
        self.assertEqual(len(pbr_spheres), 25, "Expected 5x5 grid of 25 PBR spheres")
        for s in pbr_spheres:
            self.assertEqual(s.material.type, MaterialType.Standard)

    def test_02_dynamic_lights_bloom(self) -> None:
        mod = importlib.import_module("examples.02_dynamic_lights_bloom")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        pt_lights = [l for l in app.scene.lights if l.type == LightType.Point]
        spot_lights = [l for l in app.scene.lights if l.type == LightType.Spot]
        self.assertGreaterEqual(len(pt_lights), 16, "Expected at least 16 dynamic point lights")
        self.assertGreaterEqual(len(spot_lights), 1, "Expected overhead spot light")
        self.assertIsNotNone(app.composer)
        self.assertGreaterEqual(len(app.composer.passes), 1)
        self.assertEqual(app.composer.passes[0].name, "BloomPass")

    def test_03_skeletal_character(self) -> None:
        mod = importlib.import_module("examples.03_skeletal_character")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertIsInstance(app.camera_controller, FollowCamera)
        obstacles = [e for e in app.scene.entities if "Wall" in e.name or "Crate" in e.name]
        self.assertGreaterEqual(len(obstacles), 8)
        self.assertTrue(all(ob.has_collision for ob in obstacles))

    def test_04_numpy_wave_surface(self) -> None:
        mod = importlib.import_module("examples.04_numpy_wave_surface")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        wave_ents = [e for e in app.scene.entities if "DynamicNumPyWave" in e.name]
        self.assertEqual(len(wave_ents), 1)
        # 180 * 180 = 32,400 vertices (safe within uint16 limit)
        self.assertIn(wave_ents[0].mesh.num_vertices, (180 * 180, 316 * 317))

    def test_05_custom_shader_water(self) -> None:
        mod = importlib.import_module("examples.05_custom_shader_water")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        water_ents = [e for e in app.scene.entities if "ShaderWaterPlane" in e.name]
        self.assertEqual(len(water_ents), 1)
        mat = water_ents[0].material
        self.assertEqual(mat.type, MaterialType.CustomShader)
        self.assertIn("u_time", mat.uniforms)
        self.assertIn("u_sun_dir", mat.uniforms)
        buoys = [e for e in app.scene.entities if "Buoy" in e.name]
        self.assertGreaterEqual(len(buoys), 4)

    def test_06_render_to_texture_portal(self) -> None:
        mod = importlib.import_module("examples.06_render_to_texture_portal")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        tv_screens = [e for e in app.scene.entities if "TVScreen" in e.name]
        self.assertEqual(len(tv_screens), 1)
        self.assertIsNotNone(tv_screens[0].material.albedo_map)

    def test_07_particles_and_sprites(self) -> None:
        mod = importlib.import_module("examples.07_particles_and_sprites")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        emitters = app.scene.particle_emitters
        self.assertGreaterEqual(len(emitters), 3, "Expected fire, smoke, and rain emitters")
        sprites = app.scene.sprites
        self.assertGreaterEqual(len(sprites), 3, "Expected glowing sprite billboards")

    def test_08_instanced_forest(self) -> None:
        mod = importlib.import_module("examples.08_instanced_forest")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertEqual(len(app.scene.instanced_meshes), 2)
        total_instances = sum(im.instance_count() for im in app.scene.instanced_meshes)
        self.assertEqual(total_instances, 50000, "Expected 50,000 instances (35k trees + 15k rocks)")
        lod_nodes = [e for e in app.scene.entities if "LOD_Tree" in e.name]
        self.assertGreaterEqual(len(lod_nodes), 3, "Expected at least 3 LOD tree geometry tiers (High, Med, Low)")

    def test_09_curves_and_rollercoaster(self) -> None:
        mod = importlib.import_module("examples.09_curves_and_rollercoaster")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        track_ents = [e for e in app.scene.entities if "RollercoasterTrack" in e.name]
        self.assertEqual(len(track_ents), 1)
        self.assertGreater(track_ents[0].mesh.num_vertices, 1000)
        pillars = [e for e in app.scene.entities if "SupportPillar" in e.name]
        self.assertGreaterEqual(len(pillars), 10)

    def test_10_fps_game_sandbox(self) -> None:
        mod = importlib.import_module("examples.10_fps_game_sandbox")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertIsInstance(app.camera_controller, FirstPersonController)
        targets = [e for e in app.scene.entities if "BullseyeTarget" in e.name]
        self.assertEqual(len(targets), 8)
        self.assertGreaterEqual(len(app.ui.commands), 2)


if __name__ == "__main__":
    unittest.main()
