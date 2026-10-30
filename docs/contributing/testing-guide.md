# Testing & Quality Assurance Guide

Velocity 3D Engine enforces an uncompromising testing discipline: **100% automated test coverage** across all math routines, scene graph hierarchies, shader pipelines, skeletal loaders, and game logic.

---

## Running Automated Tests

All tests are located in the `tests/` directory and run using `pytest`.

```bash
# Run entire test suite
pytest tests -q

# Run with detailed verbose output
pytest tests -v

# Run a specific test module
pytest tests/test_geometry.py -v

# Run a specific test case class or method
pytest tests/test_phase1_scenegraph.py::TestSceneGraph::test_parent_child_transforms -v
```

---

## Test Suite Architecture

```text
tests/
├── conftest.py                   # Global pytest fixtures and engine lifecycle hooks
├── test_phase0_foundation.py     # App initialization, window lifecycle, clear color
├── test_phase1_scenegraph.py     # Node3D, Entity, Group hierarchy, world matrix caching
├── test_phase2_materials.py      # StandardMaterial, PhysicalMaterial, PBR properties
├── test_phase3_verification.py   # DirectionalLight, PointLight, SpotLight, shadow settings
├── test_phase4_verification.py   # Cubemaps, IBL environment radiance, procedural sky
├── test_phase5_verification.py   # CatmullRom splines, tube extrusion, debug helpers
├── test_phase6_verification.py   # glTF character rigging, bone hierarchy, AnimationMixer
├── test_phase7_verification.py   # EffectComposer, BloomPass, SSAOPass, TonemappingPass
├── test_phase8_verification.py   # Asset loaders (OBJ, STL, PLY), GLTF exporter
├── test_geometry.py              # Procedural primitives, vertex formats, morph targets
├── test_pythonic_api.py          # Operator overloading, color conversion, tweening
├── test_examples.py              # Parity tests for all curriculum example scenes
├── test_games.py                 # Dungeon Crawler and Space Combat Arena game loops
├── test_stress_and_leaks.py      # Memory leaks, weakref destruction, 50k instances
└── test_visual_bug_hunt.py       # Offscreen frame buffer regression tests
```

---

## Headless Testing in CI

Continuous Integration environments (e.g. GitHub Actions runners) typically lack physical GPU monitors and Direct3D display adapters.

To run headless tests in CI:
1. Sokol GFX automatically operates with an offscreen dummy backend or software rasterizer when no physical monitor is attached.
2. In headless tests, avoid calling blocking `app.run()`. Instead, initialize `ve.App`, simulate frames directly by calling internal update hooks or `app.render_target()`, and verify outputs via `app.read_pixels()`:

```python
import unittest
import VelocityEngine as ve

class TestHeadlessRendering(unittest.TestCase):
    def test_offscreen_render(self) -> None:
        app = ve.App(title="Headless Test", width=320, height=240)
        target = ve.RenderTarget(320, 240)
        
        # Render offscreen frame
        app.render_target(app.scene, app.camera, target)
        
        # Inspect raw RGBA pixel bytes
        pixels = app.read_pixels(target)
        self.assertEqual(len(pixels), 320 * 240 * 4)
        app.close()
```

---

## Writing New Tests

### 1. Math & Collision Unit Tests
Test mathematical invariance, boundary edge cases, and numerical tolerances:

```python
import unittest
import VelocityEngine as ve

class TestPhysicsMTV(unittest.TestCase):
    def test_cylinder_box_collision(self) -> None:
        cyl = ve.Cylinder(base=ve.Vec3(0.0, 0.0, 0.0), radius=0.5, height=2.0)
        box = ve.AABB(min_point=ve.Vec3(-0.4, 0.0, -0.4), max_point=ve.Vec3(0.4, 2.0, 0.4))
        
        # Must detect overlap
        self.assertTrue(cyl.intersects_aabb(box))
        
        # Minimum Translation Vector must point outward
        mtv = cyl.get_penetration_aabb(box)
        self.assertGreater(mtv.length(), 0.0)
```

---

### 2. Memory Safety & Reference Leak Tests
Ensure that complex scene trees and callback closures do not retain circular references preventing garbage collection:

```python
import gc
import weakref
import unittest
import VelocityEngine as ve

class TestMemoryCleanup(unittest.TestCase):
    def test_entity_cleanup(self) -> None:
        entity = ve.Entity(mesh=ve.Mesh.create_cube(1.0))
        ref = weakref.ref(entity)
        
        del entity
        gc.collect()
        
        # Weakref must be dead after deletion
        self.assertIsNone(ref())
```
