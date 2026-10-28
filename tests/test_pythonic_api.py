"""Comprehensive Unit Tests for VelocityEngine Pythonic API (Three.js Parity)."""

from __future__ import annotations

import math
import unittest
from typing import Tuple, Any

import VelocityEngine as ve
from VelocityEngine import (
    App,
    Color,
    WHITE,
    BLACK,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    GRAY,
    DARK_GRAY,
    LIGHT_GRAY,
    WARM_WHITE,
    ORANGE,
    PURPLE,
    Tween,
    TweenManager,
    OrbitController,
    FollowCamera,
    FlyCameraController,
    FreeCameraController,
    UIOverlay,
    SceneFactory,
    create_box,
    create_sphere,
    create_plane,
    create_cylinder,
    create_grid,
    set_sun,
    screen_to_ray,
    linear,
    in_quad,
    out_quad,
    in_out_quad,
    in_cubic,
    out_cubic,
    in_out_cubic,
    in_bounce,
    out_bounce,
    in_out_bounce,
    in_elastic,
    out_elastic,
    in_out_elastic,
)


class MockInputManager:
    """Mock InputManager for testing camera controllers without a window."""

    def __init__(self) -> None:
        self.mouse_x = 400.0
        self.mouse_y = 300.0
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0
        self.mouse_buttons = [False] * 8
        self.mouse_wheel = 0.0
        self.keys_down: set = set()
        self.keys_pressed: set = set()
        self._mouse_locked: bool = False

    def is_mouse_down(self, button: int) -> bool:
        if 0 <= button < len(self.mouse_buttons):
            return self.mouse_buttons[button]
        return False

    def is_key_down(self, key: Any) -> bool:
        return key in self.keys_down

    def is_key_pressed(self, key: Any) -> bool:
        return key in self.keys_pressed

    def is_mouse_locked(self) -> bool:
        return self._mouse_locked

    def set_mouse_locked(self, locked: bool) -> None:
        self._mouse_locked = bool(locked)


class TestColor(unittest.TestCase):
    """Unit tests for the Color class and presets."""

    def test_initialization(self) -> None:
        c1 = Color(0.2, 0.4, 0.6, 0.8)
        self.assertAlmostEqual(c1.r, 0.2)
        self.assertAlmostEqual(c1.g, 0.4)
        self.assertAlmostEqual(c1.b, 0.6)
        self.assertAlmostEqual(c1.a, 0.8)

        # Default alpha = 1.0
        c2 = Color(0.5, 0.5, 0.5)
        self.assertAlmostEqual(c2.a, 1.0)

        # From sequence
        c3 = Color((0.1, 0.2, 0.3, 0.4))
        self.assertAlmostEqual(c3.r, 0.1)
        self.assertAlmostEqual(c3.a, 0.4)

    def test_tuple_unpacking_and_indexing(self) -> None:
        c = Color(0.1, 0.2, 0.3, 0.4)
        r, g, b, a = c
        self.assertAlmostEqual(r, 0.1)
        self.assertAlmostEqual(g, 0.2)
        self.assertAlmostEqual(b, 0.3)
        self.assertAlmostEqual(a, 0.4)
        self.assertEqual(len(c), 4)
        self.assertAlmostEqual(c[0], 0.1)
        self.assertAlmostEqual(c[1], 0.2)

    def test_from_hex(self) -> None:
        # Standard 6-character
        c = Color.from_hex("#FF0000")
        self.assertAlmostEqual(c.r, 1.0)
        self.assertAlmostEqual(c.g, 0.0)
        self.assertAlmostEqual(c.b, 0.0)
        self.assertAlmostEqual(c.a, 1.0)

        # Without '#'
        c2 = Color.from_hex("00FF00")
        self.assertAlmostEqual(c2.g, 1.0)

        # 3-character #RGB
        c3 = Color.from_hex("#00F")
        self.assertAlmostEqual(c3.b, 1.0)

        # 8-character #RRGGBBAA
        c4 = Color.from_hex("#FFFFFF80")
        self.assertAlmostEqual(c4.r, 1.0)
        self.assertAlmostEqual(c4.a, 128 / 255.0, places=2)

        # 4-character #RGBA
        c5 = Color.from_hex("#F008")
        self.assertAlmostEqual(c5.r, 1.0)

    def test_from_rgb(self) -> None:
        # 0.0 to 1.0 range
        c1 = Color.from_rgb(0.5, 0.5, 0.5, 0.5)
        self.assertAlmostEqual(c1.r, 0.5)
        self.assertAlmostEqual(c1.a, 0.5)

        # 0 to 255 range normalization
        c2 = Color.from_rgb(255, 128, 0, 255)
        self.assertAlmostEqual(c2.r, 1.0)
        self.assertAlmostEqual(c2.g, 128 / 255.0, places=2)
        self.assertAlmostEqual(c2.b, 0.0)
        self.assertAlmostEqual(c2.a, 1.0)

    def test_from_hsv(self) -> None:
        # Pure red: h=0, s=1, v=1
        c_red = Color.from_hsv(0, 1.0, 1.0)
        self.assertAlmostEqual(c_red.r, 1.0)
        self.assertAlmostEqual(c_red.g, 0.0)
        self.assertAlmostEqual(c_red.b, 0.0)

        # Pure green: h=120 deg
        c_green = Color.from_hsv(120, 1.0, 1.0)
        self.assertAlmostEqual(c_green.r, 0.0)
        self.assertAlmostEqual(c_green.g, 1.0)
        self.assertAlmostEqual(c_green.b, 0.0)

        # Pure blue: h=240 deg
        c_blue = Color.from_hsv(240, 100, 100)
        self.assertAlmostEqual(c_blue.r, 0.0)
        self.assertAlmostEqual(c_blue.g, 0.0)
        self.assertAlmostEqual(c_blue.b, 1.0)

    def test_lerp(self) -> None:
        c1 = Color(0.0, 0.0, 0.0, 0.0)
        c2 = Color(1.0, 1.0, 1.0, 1.0)
        mid = c1.lerp(c2, 0.5)
        self.assertAlmostEqual(mid.r, 0.5)
        self.assertAlmostEqual(mid.g, 0.5)
        self.assertAlmostEqual(mid.b, 0.5)
        self.assertAlmostEqual(mid.a, 0.5)

    def test_presets(self) -> None:
        presets = [
            WHITE, BLACK, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA,
            GRAY, DARK_GRAY, LIGHT_GRAY, WARM_WHITE, ORANGE, PURPLE,
        ]
        for p in presets:
            self.assertIsInstance(p, Color)
            self.assertEqual(len(p), 4)

        # Check accessible as Color attributes
        self.assertEqual(Color.WHITE, WHITE)
        self.assertEqual(Color.RED, RED)
        self.assertEqual(Color.WARM_WHITE, WARM_WHITE)

    def test_conversion_helpers(self) -> None:
        c = Color(1.0, 0.0, 0.0, 1.0)
        self.assertEqual(c.to_hex(), "#FF0000")
        self.assertEqual(c.to_hex(include_alpha=True), "#FF0000FF")
        self.assertEqual(c.to_tuple(), (1.0, 0.0, 0.0, 1.0))
        vec4 = c.to_vec4()
        self.assertAlmostEqual(vec4.x, 1.0)
        vec3 = c.to_vec3()
        self.assertAlmostEqual(vec3.x, 1.0)

    def test_c_interop(self) -> None:
        s = ve.Scene()
        cube = s.create_cube()
        cube.color = Color.RED
        self.assertAlmostEqual(cube.color.x, 1.0)
        self.assertAlmostEqual(cube.color.y, 0.0)


class TestTweenAndEasings(unittest.TestCase):
    """Unit tests for tweening curves and TweenManager."""

    def test_easing_boundaries(self) -> None:
        easings = [
            linear, in_quad, out_quad, in_out_quad,
            in_cubic, out_cubic, in_out_cubic,
            in_bounce, out_bounce, in_out_bounce,
            in_elastic, out_elastic, in_out_elastic,
        ]
        for fn in easings:
            self.assertAlmostEqual(fn(0.0), 0.0, places=3, msg=f"{fn.__name__}(0) failed")
            self.assertAlmostEqual(fn(1.0), 1.0, places=3, msg=f"{fn.__name__}(1) failed")

    def test_tween_scalar(self) -> None:
        values = []
        tw = Tween(0.0, 10.0, duration=1.0, ease="linear", on_update=lambda v: values.append(v))
        done1 = tw.update(0.5)
        self.assertFalse(done1)
        self.assertAlmostEqual(values[-1], 5.0)

        done2 = tw.update(0.5)
        self.assertTrue(done2)
        self.assertAlmostEqual(values[-1], 10.0)

    def test_tween_vector(self) -> None:
        values = []
        tw = Tween((0.0, 0.0, 0.0), (10.0, 20.0, 30.0), duration=2.0, ease="linear", on_update=lambda v: values.append(v))
        tw.update(1.0)
        self.assertAlmostEqual(values[-1][0], 5.0)
        self.assertAlmostEqual(values[-1][1], 10.0)
        self.assertAlmostEqual(values[-1][2], 15.0)

    def test_tween_completion_callback_and_chaining(self) -> None:
        completed = []
        tw = Tween(0, 10, duration=1.0)
        ret = tw.on_complete(lambda: completed.append(True))
        self.assertIs(ret, tw)

        tw.update(1.0)
        self.assertTrue(completed)

    def test_tween_cancellation(self) -> None:
        tw = Tween(0, 10, duration=1.0)
        tw.cancel()
        done = tw.update(0.5)
        self.assertTrue(done)
        self.assertTrue(tw.cancelled)

    def test_tween_loop(self) -> None:
        tw = Tween(0, 10, duration=1.0, loop=True)
        done1 = tw.update(1.0)
        self.assertFalse(done1)
        self.assertAlmostEqual(tw.elapsed, 0.0)

    def test_tween_manager(self) -> None:
        mgr = TweenManager()
        val = [0.0]
        tw = Tween(0.0, 100.0, duration=1.0, on_update=lambda v: val.__setitem__(0, v))
        mgr.add(tw)
        self.assertEqual(mgr.count, 1)

        mgr.update(0.5)
        self.assertAlmostEqual(val[0], 50.0)
        self.assertEqual(mgr.count, 1)

        mgr.update(0.6)
        self.assertAlmostEqual(val[0], 100.0)
        self.assertEqual(mgr.count, 0)

    def test_entity_animation_methods(self) -> None:
        s = ve.Scene()
        e = s.create_cube()
        e.transform.set_position(0, 0, 0)
        e.transform.set_rotation(0, 0, 0)
        e.transform.set_scale(1, 1, 1)

        # Animate position
        tw_pos = e.animate_position((10.0, 20.0, 30.0), duration=1.0, ease="linear")
        self.assertIsInstance(tw_pos, Tween)

        # Animate rotation
        tw_rot = e.animate_rotation((45.0, 90.0, 180.0), duration=1.0, ease="linear")
        self.assertIsInstance(tw_rot, Tween)

        # Animate rotation_y
        tw_roty = e.animate_rotation_y(90.0, duration=1.0)
        self.assertIsInstance(tw_roty, Tween)

        # Animate scale
        tw_scale = e.animate_scale((2.0, 2.0, 2.0), duration=1.0)
        self.assertIsInstance(tw_scale, Tween)

        # Advance global TweenManager
        TweenManager.default().update(1.0)
        self.assertAlmostEqual(e.transform.position.x, 10.0)
        self.assertAlmostEqual(e.transform.position.y, 20.0)
        self.assertAlmostEqual(e.transform.position.z, 30.0)


class TestOrbitController(unittest.TestCase):
    """Unit tests for the OrbitController and FollowCamera."""

    def test_orbit_initialization_and_properties(self) -> None:
        cam = ve.Camera()
        orb = OrbitController(
            cam,
            target=(1.0, 2.0, 3.0),
            distance=10.0,
            min_distance=2.0,
            max_distance=100.0,
            yaw=0.0,
            pitch=0.0,
            damping=0.0,
        )
        self.assertEqual(orb.target, (1.0, 2.0, 3.0))
        self.assertAlmostEqual(orb.distance, 10.0)
        self.assertAlmostEqual(orb.min_distance, 2.0)
        self.assertAlmostEqual(orb.max_distance, 100.0)
        self.assertAlmostEqual(orb.yaw, 0.0)
        self.assertAlmostEqual(orb.pitch, 0.0)

    def test_orbit_camera_update_instant(self) -> None:
        cam = ve.Camera()
        orb = OrbitController(cam, target=(0.0, 0.0, 0.0), distance=5.0, yaw=0.0, pitch=0.0, damping=0.0)
        orb.update(1.0 / 60.0)

        # With yaw=0, pitch=0, target=(0,0,0), distance=5.0:
        # px = 5 * cos(0) * cos(0) = 5.0
        # py = 5 * sin(0) = 0.0
        # pz = 5 * cos(0) * sin(0) = 0.0
        self.assertAlmostEqual(cam.position.x, 5.0)
        self.assertAlmostEqual(cam.position.y, 0.0)
        self.assertAlmostEqual(cam.position.z, 0.0)
        self.assertAlmostEqual(cam.target.x, 0.0)

    def test_orbit_damping(self) -> None:
        cam = ve.Camera()
        orb = OrbitController(cam, target=(0.0, 0.0, 0.0), distance=10.0, yaw=0.0, pitch=0.0, damping=0.2)
        orb.target = (10.0, 10.0, 10.0)
        orb.update(1.0 / 60.0)
        # Should not instantly jump to target due to damping
        self.assertNotEqual(orb._current_target, [10.0, 10.0, 10.0])

    def test_orbit_input_handling(self) -> None:
        cam = ve.Camera()
        orb = OrbitController(cam, damping=0.0, rotate_speed=1.0)
        mock_input = MockInputManager()
        mock_input.mouse_buttons[0] = True
        mock_input.mouse_dx = 10.0
        mock_input.mouse_dy = 5.0

        orb.update(cam, mock_input, 1.0 / 60.0, 800, 600)
        # Mouse dx should decrease yaw, dy increase pitch
        self.assertAlmostEqual(orb.yaw, -100.0)
        self.assertAlmostEqual(orb.pitch, 25.0)

    def test_orbit_zoom(self) -> None:
        cam = ve.Camera()
        orb = OrbitController(cam, distance=10.0, zoom_speed=2.0, damping=0.0)
        orb.zoom(1.0)
        self.assertAlmostEqual(orb.distance, 8.0)

    def test_screen_to_ray_delegation(self) -> None:
        cam = ve.Camera()
        orb = OrbitController(cam)
        ray = orb.screen_to_ray(400, 300, 800, 600)
        self.assertIsNotNone(ray)
        self.assertAlmostEqual(ray.origin.x, cam.position.x)

    def test_follow_camera(self) -> None:
        cam = ve.Camera()
        s = ve.Scene()
        target = s.create_cube()
        target.transform.set_position(5.0, 0.0, 5.0)

        follow = FollowCamera(cam, target_entity=target, offset=(0.0, 2.0, -5.0))
        follow.update(1.0 / 60.0)
        self.assertIsNotNone(cam.position)


class TestFlyCameraController(unittest.TestCase):
    """Unit tests for the FlyCameraController (Free-Fly / Spectator 3D Camera)."""

    def test_fly_camera_initialization_and_alias(self) -> None:
        self.assertIs(FreeCameraController, FlyCameraController)
        cam = ve.Camera()
        fly = FlyCameraController(camera=cam, move_speed=10.0, mouse_sensitivity=0.15)
        self.assertAlmostEqual(fly.move_speed, 10.0)
        self.assertAlmostEqual(fly.mouse_sensitivity, 0.15)
        self.assertTrue(fly.auto_lock_on_click)
        self.assertFalse(fly.is_mouse_locked())

    def test_fly_camera_set_position_and_look_at(self) -> None:
        cam = ve.Camera()
        fly = FlyCameraController(camera=cam)
        fly.set_position(0.0, 2.5, 9.0)
        fly.look_at(0.0, 1.2, 0.0)

        # Position
        self.assertAlmostEqual(fly.position.x, 0.0)
        self.assertAlmostEqual(fly.position.y, 2.5)
        self.assertAlmostEqual(fly.position.z, 9.0)

        # Yaw and Pitch
        self.assertAlmostEqual(fly.yaw, -90.0, delta=0.5)
        self.assertAlmostEqual(fly.pitch, -8.219, delta=0.5)

        # Forward and Right vectors
        fwd = fly.forward()
        self.assertAlmostEqual(fwd.x, 0.0, delta=0.01)
        self.assertTrue(fwd.y < 0.0)
        self.assertTrue(fwd.z < -0.9)

        r = fly.right()
        self.assertAlmostEqual(r.x, 1.0, delta=0.01)
        self.assertAlmostEqual(r.y, 0.0, delta=0.01)
        self.assertAlmostEqual(r.z, 0.0, delta=0.01)

        # Camera sync
        self.assertAlmostEqual(cam.position.x, 0.0)
        self.assertAlmostEqual(cam.position.y, 2.5)
        self.assertAlmostEqual(cam.position.z, 9.0)

    def test_fly_camera_mouse_look_and_clamping(self) -> None:
        cam = ve.Camera()
        mock_input = MockInputManager()
        fly = FlyCameraController(camera=cam, input_manager=mock_input, mouse_sensitivity=0.2)
        fly.set_mouse_locked(True)

        # Mouse look: mouse_dx = 15, mouse_dy = 10
        mock_input.mouse_dx = 15.0
        mock_input.mouse_dy = 10.0
        fly.update(cam, mock_input, 1.0 / 60.0)

        # yaw = -90 + 15 * 0.2 = -87.0
        self.assertAlmostEqual(fly.yaw, -87.0, delta=0.01)
        # pitch = 0 - 10 * 0.2 = -2.0
        self.assertAlmostEqual(fly.pitch, -2.0, delta=0.01)

        # Extreme look up to test clamping at 89.0
        mock_input.mouse_dx = 0.0
        mock_input.mouse_dy = -1000.0
        fly.update(cam, mock_input, 1.0 / 60.0)
        self.assertAlmostEqual(fly.pitch, 89.0, delta=0.01)

        # Extreme look down to test clamping at -89.0
        mock_input.mouse_dy = 2000.0
        fly.update(cam, mock_input, 1.0 / 60.0)
        self.assertAlmostEqual(fly.pitch, -89.0, delta=0.01)

    def test_fly_camera_wasd_and_flight_movement(self) -> None:
        cam = ve.Camera()
        mock_input = MockInputManager()
        fly = FlyCameraController(camera=cam, input_manager=mock_input, move_speed=12.0)
        fly.set_mouse_locked(True)
        fly.set_position(0.0, 5.0, 0.0)
        fly.set_yaw_pitch(-90.0, 0.0)  # Looking towards -Z, right is +X

        dt = 0.1  # speed * dt = 1.2 units per step

        # Test W: move forward (into -Z)
        mock_input.keys_down = {ve.Key.W}
        fly.update(dt=dt, input_mgr=mock_input)
        self.assertAlmostEqual(fly.position.z, -1.2, delta=0.01)

        # Test S: move backward (towards +Z)
        mock_input.keys_down = {ve.Key.S}
        fly.update(dt=dt, input_mgr=mock_input)
        self.assertAlmostEqual(fly.position.z, 0.0, delta=0.01)

        # Test D: strafe right (towards +X)
        mock_input.keys_down = {ve.Key.D}
        fly.update(dt=dt, input_mgr=mock_input)
        self.assertAlmostEqual(fly.position.x, 1.2, delta=0.01)

        # Test A: strafe left (towards -X)
        mock_input.keys_down = {ve.Key.A}
        fly.update(dt=dt, input_mgr=mock_input)
        self.assertAlmostEqual(fly.position.x, 0.0, delta=0.01)

        # Test Space: fly straight up (+Y)
        mock_input.keys_down = {ve.Key.SPACE}
        fly.update(dt=dt, input_mgr=mock_input)
        self.assertAlmostEqual(fly.position.y, 6.2, delta=0.01)

        # Test LeftShift: fly straight down (-Y)
        mock_input.keys_down = {ve.Key.LEFT_SHIFT}
        fly.update(dt=dt, input_mgr=mock_input)
        self.assertAlmostEqual(fly.position.y, 5.0, delta=0.01)

    def test_fly_camera_mouse_lock_transitions(self) -> None:
        cam = ve.Camera()
        mock_input = MockInputManager()
        fly = FlyCameraController(camera=cam, input_manager=mock_input, auto_lock_on_click=True)
        self.assertFalse(fly.is_mouse_locked())

        # 1. Click button 0 -> locks mouse
        mock_input.mouse_buttons[0] = True
        fly.update(dt=1.0 / 60.0, input_mgr=mock_input)
        self.assertTrue(fly.is_mouse_locked())

        # 2. ESC key -> unlocks mouse
        mock_input.mouse_buttons[0] = False
        mock_input.keys_down = {ve.Key.ESCAPE}
        fly.update(dt=1.0 / 60.0, input_mgr=mock_input)
        self.assertFalse(fly.is_mouse_locked())

        # 3. TAB key -> toggles mouse lock (unlock -> lock)
        mock_input.keys_down = set()
        mock_input.keys_pressed = {ve.Key.TAB}
        fly.update(dt=1.0 / 60.0, input_mgr=mock_input)
        self.assertTrue(fly.is_mouse_locked())

        # 4. TAB key -> toggles mouse lock (lock -> unlock)
        mock_input.keys_pressed = {ve.Key.TAB}
        fly.update(dt=1.0 / 60.0, input_mgr=mock_input)
        self.assertFalse(fly.is_mouse_locked())

    def test_fly_camera_screen_to_ray_and_app_integration(self) -> None:
        app = App("FlyCamTest", width=1280, height=720)
        fly = FlyCameraController(camera=app.camera, input_manager=app.input, app=app)
        fly.set_position(0.0, 2.5, 9.0)
        fly.look_at(0.0, 1.2, 0.0)
        app.camera = fly

        self.assertIs(app.camera, fly)
        ray = fly.screen_to_ray(640, 360, 1280, 720)
        self.assertIsNotNone(ray)
        self.assertAlmostEqual(ray.origin.x, 0.0, delta=0.1)
        self.assertAlmostEqual(ray.origin.y, 2.5, delta=0.25)
        self.assertAlmostEqual(ray.origin.z, 9.0, delta=0.25)



class TestUIOverlay(unittest.TestCase):
    """Unit tests for 2D UIOverlay commands."""

    def test_draw_commands(self) -> None:
        ui = UIOverlay()
        ui.draw_text("VelocityEngine", (20, 20), size=24.0, color=WHITE)
        ui.draw_rect(10, 10, 200, 100, color=RED)
        ui.draw_crosshair(12.0, color=CYAN)

        self.assertEqual(len(ui.commands), 3)
        self.assertEqual(ui.commands[0].text, "VelocityEngine")
        self.assertEqual(ui.commands[1].w, 200.0)
        self.assertEqual(ui.commands[2].size, 12.0)

        ui.clear()
        self.assertEqual(len(ui.commands), 0)

    def test_show_stats(self) -> None:
        ui = UIOverlay()
        ui.show_stats(True)
        self.assertTrue(ui.stats_visible)
        ui.show_stats(False)
        self.assertFalse(ui.stats_visible)


class TestSceneFactory(unittest.TestCase):
    """Unit tests for Scene helper factory methods."""

    def setUp(self) -> None:
        self.scene = ve.Scene()
        self.factory = SceneFactory(self.scene)

    def test_create_box(self) -> None:
        box = self.factory.create_box(size=(2, 3, 4), position=(1, 2, 3), color=RED)
        self.assertEqual(box.name, "Box")
        self.assertAlmostEqual(box.transform.position.x, 1.0)
        self.assertAlmostEqual(box.transform.position.y, 2.0)
        self.assertAlmostEqual(box.transform.position.z, 3.0)
        self.assertTrue(box.has_collision)

    def test_create_sphere(self) -> None:
        sphere = self.factory.create_sphere(radius=2.5, segments=16, position=(0, 5, 0), color=BLUE)
        self.assertEqual(sphere.name, "Sphere")
        self.assertAlmostEqual(sphere.transform.position.y, 5.0)
        self.assertTrue(sphere.has_collision)

    def test_create_plane(self) -> None:
        plane = self.factory.create_plane(width=50.0, height=40.0, subdivisions=8, position=(0, -1, 0), color=GREEN)
        self.assertEqual(plane.name, "Plane")
        self.assertAlmostEqual(plane.transform.position.y, -1.0)
        self.assertTrue(plane.has_collision)

    def test_create_cylinder(self) -> None:
        cyl = self.factory.create_cylinder(radius=1.0, height=4.0, segments=24, color=YELLOW)
        self.assertEqual(cyl.name, "Cylinder")
        self.assertTrue(cyl.has_collision)

    def test_create_grid(self) -> None:
        grid = self.factory.create_grid(size=60.0, step=2.0, color=GRAY)
        self.assertEqual(grid.name, "Grid")
        self.assertFalse(grid.has_collision)

    def test_set_sun(self) -> None:
        self.factory.set_sun(direction=(-1, -2, -1), color=WARM_WHITE, intensity=2.5)
        self.assertAlmostEqual(self.scene.light.intensity, 2.5)
        self.assertAlmostEqual(self.scene.light.color.x, WARM_WHITE.r)

    def test_scene_patched_methods(self) -> None:
        # Directly on Scene instance
        box = self.scene.create_box((1, 1, 1), (0, 0, 0))
        self.assertEqual(box.name, "Box")
        sphere = self.scene.create_sphere(1.0)
        self.assertEqual(sphere.name, "Sphere")


class TestCameraRaycast(unittest.TestCase):
    """Unit tests for camera screen-to-ray and scene raycasting."""

    def test_screen_to_ray_center(self) -> None:
        cam = ve.Camera()
        cam.set_position(0.0, 0.0, 5.0)
        cam.set_target(0.0, 0.0, 0.0)

        ray = cam.screen_to_ray(400.0, 300.0, 800.0, 600.0)
        self.assertAlmostEqual(ray.origin.x, 0.0, places=3)
        self.assertAlmostEqual(ray.origin.y, 0.0, places=3)
        # Ray origin unprojects from near plane (z = position.z - near_plane)
        expected_z = cam.position.z - cam.near_plane
        self.assertAlmostEqual(ray.origin.z, expected_z, places=2)

        # Center ray should point directly along camera forward vector (0, 0, -1)
        self.assertAlmostEqual(ray.direction.x, 0.0, places=3)
        self.assertAlmostEqual(ray.direction.y, 0.0, places=3)
        self.assertAlmostEqual(ray.direction.z, -1.0, places=3)

    def test_raycast_hit_detection(self) -> None:
        scene = ve.Scene()
        box = scene.create_box(size=(2, 2, 2), position=(0, 0, 0))
        cam = ve.Camera()
        cam.set_position(0.0, 0.0, 5.0)
        cam.set_target(0.0, 0.0, 0.0)

        ray = cam.screen_to_ray(400.0, 300.0, 800.0, 600.0)
        hit = scene.raycast(ray)
        self.assertTrue(hit.hit)
        # Front face of 2x2x2 cube centered at origin is at z = 1.0
        self.assertAlmostEqual(hit.point.z, 1.0, places=2)
        # Distance from near plane (4.95) to front face (1.0) is 3.95
        expected_dist = cam.position.z - cam.near_plane - 1.0
        self.assertAlmostEqual(hit.distance, expected_dist, places=2)


class TestAppIntegration(unittest.TestCase):
    """Unit tests for the integrated App class."""

    def test_app_initialization_and_ui(self) -> None:
        app = App(title="Test Window", width=1024, height=768, clear_color=WARM_WHITE)
        self.assertEqual(app.width, 1024)
        self.assertEqual(app.height, 768)
        self.assertIsInstance(app.ui, UIOverlay)
        self.assertIsInstance(app.tweens, TweenManager)

    def test_app_camera_controller(self) -> None:
        app = App()
        orb = OrbitController(target=(0, 0, 0), distance=15.0)
        app.camera = orb
        self.assertIs(app.camera, orb)
        self.assertIs(app.camera_controller, orb)

    def test_app_raycast_decorators(self) -> None:
        app = App()
        clicked = []
        hovered = []

        @app.on_click
        def handle_click(hit: Any) -> None:
            clicked.append(hit)

        @app.on_hover
        def handle_hover(hit: Any) -> None:
            hovered.append(hit)

        # Simulate frame
        app._on_internal_frame(0.016)
        # Hover fires each frame
        self.assertEqual(len(hovered), 1)

    def test_app_target_fps_and_crosshair(self) -> None:
        app = App()
        self.assertEqual(app.target_fps, 0)
        self.assertTrue(app.show_crosshair)

        app.target_fps = 144
        self.assertEqual(app.target_fps, 144)
        self.assertEqual(app._core.target_fps, 144)

        app.set_target_fps(30)
        self.assertEqual(app.target_fps, 30)

        app.show_crosshair = False
        self.assertFalse(app.show_crosshair)
        self.assertFalse(app._core.show_crosshair)

        app.set_show_crosshair(True)
        self.assertTrue(app.show_crosshair)

        # App initialization with custom parameters
        app2 = App(target_fps=120, show_crosshair=False)
        self.assertEqual(app2.target_fps, 120)
        self.assertFalse(app2.show_crosshair)


class TestContractConformance(unittest.TestCase):
    """Verify structural compliance with contracts/pythonic_api_contract.py protocols."""

    def test_color_contract(self) -> None:
        c = Color(1.0, 0.5, 0.2, 1.0)
        self.assertTrue(hasattr(c, "r") and isinstance(c.r, float))
        self.assertTrue(hasattr(c, "g") and isinstance(c.g, float))
        self.assertTrue(hasattr(c, "b") and isinstance(c.b, float))
        self.assertTrue(hasattr(c, "a") and isinstance(c.a, float))
        self.assertTrue(callable(getattr(Color, "from_hex", None)))
        self.assertTrue(callable(getattr(Color, "from_rgb", None)))
        self.assertTrue(callable(getattr(c, "lerp", None)))

    def test_tween_contract(self) -> None:
        tw = Tween(0.0, 1.0, 1.0)
        self.assertTrue(callable(getattr(tw, "update", None)))
        self.assertTrue(callable(getattr(tw, "cancel", None)))
        self.assertTrue(callable(getattr(tw, "on_complete", None)))

    def test_orbit_controller_contract(self) -> None:
        cam = ve.Camera()
        orb = OrbitController(cam)
        self.assertTrue(hasattr(orb, "target"))
        self.assertTrue(hasattr(orb, "distance"))
        self.assertTrue(hasattr(orb, "min_distance"))
        self.assertTrue(hasattr(orb, "max_distance"))
        self.assertTrue(hasattr(orb, "damping"))
        self.assertTrue(callable(getattr(orb, "update", None)))
        # Verify update(dt, input_mgr, width, height) signature works
        orb.update(0.016, None, 1280, 720)

    def test_ui_overlay_contract(self) -> None:
        ui = UIOverlay()
        self.assertTrue(callable(getattr(ui, "draw_text", None)))
        self.assertTrue(callable(getattr(ui, "draw_rect", None)))
        self.assertTrue(callable(getattr(ui, "draw_crosshair", None)))
        self.assertTrue(callable(getattr(ui, "show_stats", None)))

    def test_scene_factory_contract(self) -> None:
        s = ve.Scene()
        sf = SceneFactory(s)
        self.assertTrue(callable(getattr(sf, "create_box", None)))
        self.assertTrue(callable(getattr(sf, "create_sphere", None)))
        self.assertTrue(callable(getattr(sf, "create_plane", None)))
        self.assertTrue(callable(getattr(sf, "create_cylinder", None)))
        self.assertTrue(callable(getattr(sf, "create_grid", None)))
        self.assertTrue(callable(getattr(sf, "set_sun", None)))


    def test_fly_camera_controller_contract(self) -> None:
        cam = ve.Camera()
        fly = FlyCameraController(cam)
        self.assertTrue(hasattr(fly, "move_speed"))
        self.assertTrue(hasattr(fly, "mouse_sensitivity"))
        self.assertTrue(hasattr(fly, "auto_lock_on_click"))
        self.assertTrue(callable(getattr(fly, "set_position", None)))
        self.assertTrue(callable(getattr(fly, "look_at", None)))
        self.assertTrue(callable(getattr(fly, "is_mouse_locked", None)))
        self.assertTrue(callable(getattr(fly, "set_mouse_locked", None)))
        self.assertTrue(callable(getattr(fly, "update", None)))
        # Verify update signatures
        fly.update(0.016, None, 1280, 720)
        fly.update(cam, None, 0.016, 1280, 720)


if __name__ == "__main__":
    unittest.main()
