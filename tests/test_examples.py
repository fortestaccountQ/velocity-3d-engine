"""Unit tests verifying Example A (08_model_viewer.py) and Example B (09_interactive_sandbox.py)."""

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
    """Test Three.js parity and components instantiation for Example A and Example B."""

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


if __name__ == "__main__":
    unittest.main()
