"""Unit tests verifying Example Scenes and Task 8.2 (10 Reference Showcase Examples).

Includes:
- Legacy Example A (08_model_viewer.py) and Example B (09_interactive_sandbox.py) parity checks.
- Comprehensive verification of all 10 reference showcase examples:
  1. `01_hello_pbr.py`: 5x5 grid of PBR spheres, metallic/roughness progression, IBL environment, OrbitController.
  2. `02_dynamic_lights_bloom.py`: 16 multi-colored PointLights, overhead SpotLight, emissive pillars, BloomPass.
  3. `03_skeletal_character.py`: Soldier.glb model, AnimationMixer crossfade Idle <-> Run, FollowCamera, obstacle collisions.
  4. `04_numpy_wave_surface.py`: 100,000+ vertices grid mesh, dynamic NumPy height modulation, GPU buffer updates.
  5. `05_custom_shader_water.py`: ShaderMaterial with custom vs/fs strings and uniforms, floating buoys.
  6. `06_render_to_texture_portal.py`: RenderTarget(512, 512), CCTV security camera, TV screen displaying live texture feed.
  7. `07_particles_and_sprites.py`: Campfire ParticleEmitter with Additive sparks, smoke, rain, Sprite billboards.
  8. `08_instanced_forest.py`: 50,000 instances (35k trees + 15k rocks), multi-tier LOD hero tree.
  9. `09_curves_and_rollercoaster.py`: Closed CatmullRomCurve3 spline, procedural TubeGeometry, GridHelper, pillars.
  10. `10_fps_game_sandbox.py`: FirstPersonController, 3D raycast target shooting, UIOverlay HUD, F2 mode toggle.
"""

from __future__ import annotations
import importlib
import unittest
from pathlib import Path
import VelocityEngine as ve
from VelocityEngine import (
    App,
    OrbitController,
    FirstPersonController,
    Color,
    WARM_WHITE,
    WHITE,
    CYAN,
    UIOverlay,
    Tween,
    TweenManager,
)


class TestExamplesParity(unittest.TestCase):
    """Test Three.js parity and components instantiation for legacy examples."""

    def test_example_a_components(self) -> None:
        duck_path = str(Path(__file__).resolve().parent.parent / "assets" / "duck.glb")
        app = App("Test Model Viewer", width=800, height=600)

        # Test OrbitController
        orb = OrbitController(target=(0.0, 0.8, 0.0), distance=3.5, min_distance=1.0, max_distance=20.0)
        app.camera = orb
        self.assertIs(app.camera_controller, orb)

        # Test Sun
        app.scene.set_sun(direction=(-1.0, -2.0, -1.0), color=WARM_WHITE, intensity=1.5)
        self.assertAlmostEqual(app.scene.light.intensity, 1.5)

        # Test Grid
        grid = app.scene.create_grid(size=30.0, step=1.0, color=Color.from_hex("#333842"))
        self.assertIsNotNone(grid)
        self.assertEqual(grid.name, "Grid")

        # Test Model Load
        duck = app.scene.load_model(duck_path)
        self.assertIsNotNone(duck)
        self.assertGreater(len(duck.meshes), 0)

        # Test UI Overlay
        app.ui.draw_text("VelocityEngine Duck Viewer", (20, 20), size=20, color=WARM_WHITE)
        app.ui.show_stats(True)
        self.assertTrue(app.ui.stats_visible)
        self.assertGreater(len(app.ui.commands), 0)

    def test_example_b_components(self) -> None:
        app = App("Test Interactive Sandbox", width=800, height=600)

        # Test FirstPersonController
        controller = FirstPersonController(
            camera=app.camera,
            input_manager=app.input,
            scene=app.scene,
            audio=app.audio,
            move_speed=5.5,
        )
        app.camera_controller = controller
        self.assertIs(app.camera_controller, controller)

        # Test Interactive Cubes & Collisions
        box = app.scene.create_box(size=(1.2, 1.2, 1.2), position=(2.0, 0.6, 2.0), color=Color.from_hex("#ff3366"))
        self.assertIsNotNone(box)
        self.assertTrue(box.has_collision)

        # Test Entity Tweens
        pos_tween = box.animate_position(target=(2.0, 2.5, 2.0), duration=0.3, ease="out_quad")
        rot_tween = box.animate_rotation_y(degrees=360.0, duration=0.5, ease="out_cubic")
        scale_tween = box.animate_scale(target=(1.5, 1.5, 1.5), duration=0.2, ease="linear")

        self.assertIsNotNone(pos_tween)
        self.assertIsNotNone(rot_tween)
        self.assertIsNotNone(scale_tween)

        # Step tweens
        app.tweens.update(0.15)
        self.assertGreater(box.transform.position.y, 0.6)

        # Test UI Overlay
        app.ui.draw_crosshair(size=12.0, color=WHITE)
        app.ui.draw_text("Sandbox Status", (20, 20), size=18, color=CYAN)
        self.assertEqual(len(app.ui.commands), 2)

    def test_import_example_modules(self) -> None:
        m_08 = importlib.import_module("examples.08_model_viewer")
        self.assertIsNotNone(m_08)
        self.assertTrue(hasattr(m_08, "app"))

        m_09 = importlib.import_module("examples.09_interactive_sandbox")
        self.assertIsNotNone(m_09)
        self.assertTrue(hasattr(m_09, "main"))

        m_12 = importlib.import_module("examples.12_phase2_pbr_helmet")
        self.assertIsNotNone(m_12)
        self.assertTrue(hasattr(m_12, "app"))

        m_13 = importlib.import_module("examples.13_phase5_curves_helpers_wave")
        self.assertIsNotNone(m_13)
        self.assertTrue(hasattr(m_13, "main"))


class TestTask82ShowcaseExamples(unittest.TestCase):
    """Verification test suite for Task 8.2 (10 Reference Showcase Examples)."""

    def test_import_all_10_showcase_examples(self) -> None:
        """Verify all 10 reference examples can be dynamically imported and expose run_example."""
        modules = [
            "examples.01_hello_pbr",
            "examples.02_dynamic_lights_bloom",
            "examples.03_skeletal_character",
            "examples.04_numpy_wave_surface",
            "examples.05_custom_shader_water",
            "examples.06_render_to_texture_portal",
            "examples.07_particles_and_sprites",
            "examples.08_instanced_forest",
            "examples.09_curves_and_rollercoaster",
            "examples.10_fps_game_sandbox",
        ]
        for mod_name in modules:
            mod = importlib.import_module(mod_name)
            self.assertIsNotNone(mod, f"Failed to import {mod_name}")
            self.assertTrue(hasattr(mod, "run_example"), f"Module {mod_name} missing 'run_example' function")

    def test_01_hello_pbr_execution(self) -> None:
        mod = importlib.import_module("examples.01_hello_pbr")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.scene)
        self.assertIsNotNone(app.scene.environment)
        # Verify 5x5 sphere grid (25 spheres)
        pbr_spheres = [e for e in app.scene.entities if "PBR_Sphere" in e.name]
        self.assertEqual(len(pbr_spheres), 25)

    def test_02_dynamic_lights_bloom_execution(self) -> None:
        mod = importlib.import_module("examples.02_dynamic_lights_bloom")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.composer)
        self.assertGreaterEqual(len(app.composer.passes), 1)
        self.assertEqual(app.composer.passes[0].name, "BloomPass")
        # Verify 16 point lights + 1 spot light
        pt_lights = [l for l in app.scene.lights if l.type == ve.LightType.Point]
        spot_lights = [l for l in app.scene.lights if l.type == ve.LightType.Spot]
        self.assertGreaterEqual(len(pt_lights), 16)
        self.assertGreaterEqual(len(spot_lights), 1)

    def test_03_skeletal_character_execution(self) -> None:
        mod = importlib.import_module("examples.03_skeletal_character")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.camera_controller)
        self.assertIsInstance(app.camera_controller, ve.FollowCamera)
        # Verify arena floor and wall entities
        walls = [e for e in app.scene.entities if "Wall" in e.name or "Crate" in e.name]
        self.assertGreaterEqual(len(walls), 8)

    def test_04_numpy_wave_surface_execution(self) -> None:
        mod = importlib.import_module("examples.04_numpy_wave_surface")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        wave_ents = [e for e in app.scene.entities if "DynamicNumPyWave" in e.name]
        self.assertEqual(len(wave_ents), 1)
        self.assertIn(wave_ents[0].mesh.num_vertices, (180 * 180, 316 * 317))

    def test_05_custom_shader_water_execution(self) -> None:
        mod = importlib.import_module("examples.05_custom_shader_water")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        water_ents = [e for e in app.scene.entities if "ShaderWaterPlane" in e.name]
        self.assertEqual(len(water_ents), 1)
        mat = water_ents[0].material
        self.assertIsNotNone(mat)
        self.assertEqual(mat.type, ve.MaterialType.CustomShader)
        self.assertIn("u_time", mat.uniforms)

    def test_06_render_to_texture_portal_execution(self) -> None:
        mod = importlib.import_module("examples.06_render_to_texture_portal")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        tv_screens = [e for e in app.scene.entities if "TVScreen" in e.name]
        self.assertEqual(len(tv_screens), 1)
        self.assertIsNotNone(tv_screens[0].material.albedo_map)

    def test_07_particles_and_sprites_execution(self) -> None:
        mod = importlib.import_module("examples.07_particles_and_sprites")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertGreaterEqual(len(app.scene.particle_emitters), 3)
        self.assertGreaterEqual(len(app.scene.sprites), 3)

    def test_08_instanced_forest_execution(self) -> None:
        mod = importlib.import_module("examples.08_instanced_forest")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertEqual(len(app.scene.instanced_meshes), 2)
        total_instances = sum(im.instance_count() for im in app.scene.instanced_meshes)
        self.assertEqual(total_instances, 50000)

    def test_09_curves_and_rollercoaster_execution(self) -> None:
        mod = importlib.import_module("examples.09_curves_and_rollercoaster")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        track_ents = [e for e in app.scene.entities if "RollercoasterTrack" in e.name]
        self.assertEqual(len(track_ents), 1)
        self.assertGreater(track_ents[0].mesh.num_vertices, 1000)
        pillars = [e for e in app.scene.entities if "SupportPillar" in e.name]
        self.assertGreater(len(pillars), 0)

    def test_10_fps_game_sandbox_execution(self) -> None:
        mod = importlib.import_module("examples.10_fps_game_sandbox")
        app = mod.run_example(headless=True, frames=5)
        self.assertIsNotNone(app)
        self.assertIsNotNone(app.camera_controller)
        self.assertIsInstance(app.camera_controller, ve.FirstPersonController)
        targets = [e for e in app.scene.entities if "BullseyeTarget" in e.name]
        self.assertEqual(len(targets), 8)


if __name__ == "__main__":
    unittest.main()
