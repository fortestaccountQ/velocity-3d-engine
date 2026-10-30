"""Sanity test suite verifying all 16 standardized reference examples run cleanly.

Covers:
01_hello_window.py
02_rotating_cube.py
03_hello_pbr.py
04_dynamic_lights_bloom.py
05_skeletal_character.py
06_interactive_sandbox.py
07_particles_and_sprites.py
08_curves_rollercoaster.py
09_render_to_texture_portal.py
10_instanced_forest.py
11_water_surface.py
12_numpy_wave.py
13_pbr_damaged_helmet.py
14_fps_minigame.py
15_viral_cube_cannon.py
16_visual_editor.py
"""

from __future__ import annotations
import importlib
import subprocess
import sys
import unittest
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


class TestAll16ExamplesSanity(unittest.TestCase):
    """Smoke test suite verifying that all 16 curriculum examples run cleanly."""

    def _run_example_subprocess(self, script_name: str, timeout: float = 30.0) -> None:
        script_path = EXAMPLES_DIR / script_name
        self.assertTrue(script_path.exists(), f"Example script not found: {script_path}")

        cmd = [sys.executable, str(script_path), "--test", "--frames", "30"]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            cwd=str(EXAMPLES_DIR.parent),
        )
        self.assertEqual(
            result.returncode,
            0,
            f"{script_name} failed with code {result.returncode}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}",
        )

    def test_01_hello_window(self) -> None:
        self._run_example_subprocess("01_hello_window.py")

    def test_02_rotating_cube(self) -> None:
        self._run_example_subprocess("02_rotating_cube.py")

    def test_03_hello_pbr(self) -> None:
        self._run_example_subprocess("03_hello_pbr.py")

    def test_04_dynamic_lights_bloom(self) -> None:
        self._run_example_subprocess("04_dynamic_lights_bloom.py")

    def test_05_skeletal_character(self) -> None:
        self._run_example_subprocess("05_skeletal_character.py")

    def test_06_interactive_sandbox(self) -> None:
        self._run_example_subprocess("06_interactive_sandbox.py")

    def test_07_particles_and_sprites(self) -> None:
        self._run_example_subprocess("07_particles_and_sprites.py")

    def test_08_curves_rollercoaster(self) -> None:
        self._run_example_subprocess("08_curves_rollercoaster.py")

    def test_09_render_to_texture_portal(self) -> None:
        self._run_example_subprocess("09_render_to_texture_portal.py")

    def test_10_instanced_forest(self) -> None:
        self._run_example_subprocess("10_instanced_forest.py")

    def test_11_water_surface(self) -> None:
        self._run_example_subprocess("11_water_surface.py")

    def test_12_numpy_wave(self) -> None:
        self._run_example_subprocess("12_numpy_wave.py")

    def test_13_pbr_damaged_helmet(self) -> None:
        self._run_example_subprocess("13_pbr_damaged_helmet.py")

    def test_14_fps_minigame(self) -> None:
        self._run_example_subprocess("14_fps_minigame.py")

    def test_15_viral_cube_cannon(self) -> None:
        self._run_example_subprocess("15_viral_cube_cannon.py")

    def test_16_visual_editor(self) -> None:
        self._run_example_subprocess("16_visual_editor.py")


if __name__ == "__main__":
    unittest.main()
