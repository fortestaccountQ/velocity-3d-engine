"""OrbitController and FollowCamera controllers for 3D camera navigation."""

from __future__ import annotations

import math
from typing import Tuple, Sequence, Optional, Any, Union

try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core


class OrbitController:
    """Three.js-style OrbitController with smooth spherical coordinate damping,

    target tracking, mouse dragging (LMB rotate, RMB/MMB pan), and zooming.
    """

    def __init__(
        self,
        camera: Optional[Any] = None,
        target: Sequence[float] = (0.0, 0.0, 0.0),
        distance: float = 5.0,
        min_distance: float = 0.5,
        max_distance: float = 500.0,
        yaw: float = -90.0,
        pitch: float = 20.0,
        min_pitch: float = -89.0,
        max_pitch: float = 89.0,
        damping: float = 0.1,
        rotate_speed: float = 0.3,
        zoom_speed: float = 1.0,
        pan_speed: float = 0.005,
    ):
        self.camera = camera

        # Target parameters
        self._target_target = [float(target[0]), float(target[1]), float(target[2])]
        self._current_target = list(self._target_target)

        # Distance
        self.min_distance = float(min_distance)
        self.max_distance = float(max_distance)
        self._target_distance = max(self.min_distance, min(self.max_distance, float(distance)))
        self._current_distance = self._target_distance

        # Spherical angles (in degrees)
        self.min_pitch = float(min_pitch)
        self.max_pitch = float(max_pitch)
        self._target_yaw = float(yaw)
        self._current_yaw = self._target_yaw
        self._target_pitch = max(self.min_pitch, min(self.max_pitch, float(pitch)))
        self._current_pitch = self._target_pitch

        # Tuning
        self.damping = max(0.0, float(damping))
        self.rotate_speed = float(rotate_speed)
        self.zoom_speed = float(zoom_speed)
        self.pan_speed = float(pan_speed)

        # Sync initial state if camera provided
        if self.camera is not None:
            self._apply_to_camera(self.camera)

    @property
    def target(self) -> Tuple[float, float, float]:
        """Look-at target coordinate (x, y, z)."""
        return (self._target_target[0], self._target_target[1], self._target_target[2])

    @target.setter
    def target(self, val: Sequence[float]) -> None:
        self._target_target = [float(val[0]), float(val[1]), float(val[2])]
        if self.damping <= 0.0:
            self._current_target = list(self._target_target)

    @property
    def distance(self) -> float:
        """Distance from target."""
        return self._target_distance

    @distance.setter
    def distance(self, val: float) -> None:
        self._target_distance = max(self.min_distance, min(self.max_distance, float(val)))
        if self.damping <= 0.0:
            self._current_distance = self._target_distance

    @property
    def yaw(self) -> float:
        """Azimuth angle in degrees."""
        return self._target_yaw

    @yaw.setter
    def yaw(self, val: float) -> None:
        self._target_yaw = float(val)
        if self.damping <= 0.0:
            self._current_yaw = self._target_yaw

    @property
    def pitch(self) -> float:
        """Elevation angle in degrees."""
        return self._target_pitch

    @pitch.setter
    def pitch(self, val: float) -> None:
        self._target_pitch = max(self.min_pitch, min(self.max_pitch, float(val)))
        if self.damping <= 0.0:
            self._current_pitch = self._target_pitch

    def zoom(self, delta: float) -> None:
        """Zoom in/out by adjusting target distance."""
        self._target_distance = max(
            self.min_distance,
            min(self.max_distance, self._target_distance - float(delta) * self.zoom_speed)
        )
        if self.damping <= 0.0:
            self._current_distance = self._target_distance

    def pan(self, dx: float, dy: float) -> None:
        """Pan target position along camera view plane."""
        rad_y = math.radians(self._current_yaw)
        # Camera right vector: (-sin(yaw), 0, cos(yaw))
        rx = -math.sin(rad_y)
        rz = math.cos(rad_y)

        # Pan offset
        scale = self.pan_speed * self._current_distance
        self._target_target[0] += rx * dx * scale
        self._target_target[1] += dy * scale
        self._target_target[2] += rz * dx * scale

        if self.damping <= 0.0:
            self._current_target = list(self._target_target)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Update controller state and apply to camera.

        Accepts:
            update(camera, input_mgr, dt, width, height)
            update(dt, input_mgr, width, height)
            update(camera, dt)
            update(dt)
        """
        # Parse arguments polymorphically
        cam = self.camera
        input_mgr = None
        dt = 1.0 / 60.0
        width = 1280
        height = 720

        if len(args) == 5:
            # update(camera, input_mgr, dt, width, height)
            cam = args[0]
            input_mgr = args[1]
            dt = float(args[2])
            width = int(args[3])
            height = int(args[4])
        elif len(args) == 4:
            # update(dt, input_mgr, width, height)
            dt = float(args[0])
            input_mgr = args[1]
            width = int(args[2])
            height = int(args[3])
        elif len(args) == 3:
            cam = args[0]
            input_mgr = args[1]
            dt = float(args[2])
        elif len(args) == 2:
            if hasattr(args[0], "forward") or hasattr(args[0], "position"):
                cam = args[0]
                dt = float(args[1])
            else:
                dt = float(args[0])
                input_mgr = args[1]
        elif len(args) == 1:
            dt = float(args[0])

        if "camera" in kwargs:
            cam = kwargs["camera"]
        if "input_mgr" in kwargs:
            input_mgr = kwargs["input_mgr"]
        if "dt" in kwargs:
            dt = float(kwargs["dt"])
        if "width" in kwargs:
            width = int(kwargs["width"])
        if "height" in kwargs:
            height = int(kwargs["height"])

        if cam is not None and self.camera is None:
            self.camera = cam

        # 1. Process user input
        if input_mgr is not None:
            mdx = getattr(input_mgr, "mouse_dx", 0.0)
            mdy = getattr(input_mgr, "mouse_dy", 0.0)

            # Left mouse button -> Rotate
            lmb = False
            try:
                lmb = input_mgr.is_mouse_down(0)
            except Exception:
                pass

            # Right or middle mouse button -> Pan
            rmb = False
            mmb = False
            try:
                rmb = input_mgr.is_mouse_down(1)
            except Exception:
                pass
            try:
                mmb = input_mgr.is_mouse_down(2)
            except Exception:
                pass

            if lmb and not rmb:
                self._target_yaw -= mdx * self.rotate_speed
                self._target_pitch += mdy * self.rotate_speed
                self._target_pitch = max(self.min_pitch, min(self.max_pitch, self._target_pitch))

            if rmb or mmb:
                self.pan(-mdx, mdy)

            # Scroll wheel zoom
            wheel = 0.0
            if hasattr(input_mgr, "mouse_wheel"):
                wheel = float(getattr(input_mgr, "mouse_wheel", 0.0))
            elif hasattr(input_mgr, "scroll_y"):
                wheel = float(getattr(input_mgr, "scroll_y", 0.0))

            if abs(wheel) > 1e-4:
                self.zoom(wheel)

        # 2. Damping interpolation
        if self.damping <= 0.0:
            self._current_yaw = self._target_yaw
            self._current_pitch = self._target_pitch
            self._current_distance = self._target_distance
            self._current_target = list(self._target_target)
        else:
            factor = 1.0 - math.exp(-max(0.0001, dt) * (1.0 / max(0.01, self.damping * 0.5)))
            factor = max(0.0, min(1.0, factor))
            self._current_yaw += (self._target_yaw - self._current_yaw) * factor
            self._current_pitch += (self._target_pitch - self._current_pitch) * factor
            self._current_distance += (self._target_distance - self._current_distance) * factor
            self._current_target[0] += (self._target_target[0] - self._current_target[0]) * factor
            self._current_target[1] += (self._target_target[1] - self._current_target[1]) * factor
            self._current_target[2] += (self._target_target[2] - self._current_target[2]) * factor

        # 3. Apply to camera
        target_cam = cam or self.camera
        if target_cam is not None:
            self._apply_to_camera(target_cam)

    def _apply_to_camera(self, cam: Any) -> None:
        """Compute spherical position and apply to camera."""
        rad_y = math.radians(self._current_yaw)
        rad_p = math.radians(self._current_pitch)

        # Position on sphere relative to target
        px = self._current_target[0] + self._current_distance * math.cos(rad_p) * math.cos(rad_y)
        py = self._current_target[1] + self._current_distance * math.sin(rad_p)
        pz = self._current_target[2] + self._current_distance * math.cos(rad_p) * math.sin(rad_y)

        cam.set_position(px, py, pz)
        cam.set_target(self._current_target[0], self._current_target[1], self._current_target[2])

    def screen_to_ray(self, mouse_x: float, mouse_y: float, screen_w: float, screen_h: float) -> Any:
        """Forward screen_to_ray call to underlying camera."""
        if self.camera is not None and hasattr(self.camera, "screen_to_ray"):
            return self.camera.screen_to_ray(mouse_x, mouse_y, screen_w, screen_h)
        from .camera_utils import screen_to_ray
        if self.camera is not None:
            return screen_to_ray(self.camera, mouse_x, mouse_y, screen_w, screen_h)
        raise RuntimeError("OrbitController has no camera assigned to perform screen_to_ray")

    # Delegate camera properties for transparent drop-in usage
    def forward(self) -> Any:
        return self.camera.forward() if self.camera else _core.Vec3(0, 0, -1)

    def right(self) -> Any:
        return self.camera.right() if self.camera else _core.Vec3(1, 0, 0)

    @property
    def position(self) -> Any:
        return self.camera.position if self.camera else _core.Vec3(0, 0, 0)

    @property
    def fov(self) -> float:
        return getattr(self.camera, "fov", 55.0)


# ---------------------------------------------------------------------------
# FollowCamera with Spring-Arm Damping
# ---------------------------------------------------------------------------

class FollowCamera:
    """Third-person follow camera with spring-arm physics and obstacle collision damping."""

    def __init__(
        self,
        camera: Optional[Any] = None,
        target_entity: Optional[Any] = None,
        offset: Sequence[float] = (0.0, 3.0, 6.0),
        look_at_offset: Sequence[float] = (0.0, 1.2, 0.0),
        spring_arm_length: float = 6.0,
        stiffness: float = 12.0,
        damping: float = 0.85,
        min_arm_length: float = 0.5,
        max_arm_length: float = 50.0,
        scene: Optional[Any] = None,
    ):
        self.camera = camera
        self.target_entity = target_entity
        self.offset = (float(offset[0]), float(offset[1]), float(offset[2]))
        self.look_at_offset = (float(look_at_offset[0]), float(look_at_offset[1]), float(look_at_offset[2]))
        self.spring_arm_length = float(spring_arm_length)
        self.stiffness = float(stiffness)
        self.damping = float(damping)
        self.min_arm_length = float(min_arm_length)
        self.max_arm_length = float(max_arm_length)
        self.scene = scene

        # Spring dynamics state
        self._current_pos: Optional[list[float]] = None
        self._velocity = [0.0, 0.0, 0.0]

    def _get_target_world_pos(self) -> Tuple[float, float, float]:
        if self.target_entity is not None and hasattr(self.target_entity, "transform"):
            p = self.target_entity.transform.position
            return (float(p.x), float(p.y), float(p.z))
        return (0.0, 0.0, 0.0)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Advance spring-arm simulation and update camera position."""
        dt = 1.0 / 60.0
        cam = self.camera

        if len(args) == 1:
            dt = float(args[0])
        elif len(args) == 2:
            cam = args[0]
            dt = float(args[1])

        if "dt" in kwargs:
            dt = float(kwargs["dt"])
        if "camera" in kwargs:
            cam = kwargs["camera"]

        target_cam = cam or self.camera
        if target_cam is None:
            return

        tx, ty, tz = self._get_target_world_pos()

        # Desired look-at point
        look_x = tx + self.look_at_offset[0]
        look_y = ty + self.look_at_offset[1]
        look_z = tz + self.look_at_offset[2]

        # Ideal camera position
        ideal_x = tx + self.offset[0]
        ideal_y = ty + self.offset[1]
        ideal_z = tz + self.offset[2]

        if self._current_pos is None:
            self._current_pos = [ideal_x, ideal_y, ideal_z]

        # Spring-damper integration
        dt_safe = max(0.0001, min(0.1, dt))
        dx = ideal_x - self._current_pos[0]
        dy = ideal_y - self._current_pos[1]
        dz = ideal_z - self._current_pos[2]

        ax = dx * self.stiffness - self._velocity[0] * self.damping * self.stiffness
        ay = dy * self.stiffness - self._velocity[1] * self.damping * self.stiffness
        az = dz * self.stiffness - self._velocity[2] * self.damping * self.stiffness

        self._velocity[0] += ax * dt_safe
        self._velocity[1] += ay * dt_safe
        self._velocity[2] += az * dt_safe

        self._current_pos[0] += self._velocity[0] * dt_safe
        self._current_pos[1] += self._velocity[1] * dt_safe
        self._current_pos[2] += self._velocity[2] * dt_safe

        target_cam.set_position(self._current_pos[0], self._current_pos[1], self._current_pos[2])
        target_cam.set_target(look_x, look_y, look_z)

    def screen_to_ray(self, mouse_x: float, mouse_y: float, screen_w: float, screen_h: float) -> Any:
        if self.camera is not None and hasattr(self.camera, "screen_to_ray"):
            return self.camera.screen_to_ray(mouse_x, mouse_y, screen_w, screen_h)
        from .camera_utils import screen_to_ray
        if self.camera is not None:
            return screen_to_ray(self.camera, mouse_x, mouse_y, screen_w, screen_h)
        raise RuntimeError("FollowCamera has no camera assigned to perform screen_to_ray")
