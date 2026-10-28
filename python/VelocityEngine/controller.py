"""First-person character controller with mouse look, gravity, jump, AABB collision, depenetration, and audio."""

import math
from typing import Optional, List, Tuple, Any, Sequence, Union
from . import Key, Camera, InputManager, Scene, Entity, AABB, Cylinder, Vec3

# Setup common case aliases on Key enum if present
for _orig, _alias in [
    ("ESCAPE", "Escape"),
    ("TAB", "Tab"),
    ("SPACE", "Space"),
    ("LEFT_SHIFT", "LeftShift"),
    ("LEFT_CONTROL", "LeftControl"),
    ("LEFT_ALT", "LeftAlt"),
]:
    if hasattr(Key, _orig) and not hasattr(Key, _alias):
        try:
            setattr(Key, _alias, getattr(Key, _orig))
        except Exception:
            pass



class FirstPersonController:
    """First-Person Controller with sub-stepping, minimum translation vector depenetration, and spatial audio."""

    def __init__(
        self,
        camera: Camera,
        input_manager: InputManager,
        scene: Optional[Scene] = None,
        audio: Optional[object] = None,
        move_speed: float = 5.0,
        mouse_sensitivity: float = 0.14,
        gravity: float = 16.0,
        jump_speed: float = 6.0,
        player_height: float = 1.7,
        player_radius: float = 0.35,
        step_height: float = 0.20,
    ):
        self.camera = camera
        self.input = input_manager
        self.scene = scene
        self.audio = audio

        self.move_speed = move_speed
        self.mouse_sensitivity = mouse_sensitivity
        self.gravity = gravity
        self.jump_speed = jump_speed
        self.player_height = player_height
        self.player_radius = player_radius
        self.step_height = step_height

        self.velocity_y = 0.0
        self.is_grounded = True
        self.enabled = True
        self.step_timer = 0.0

        # Custom obstacle AABBs that player cannot walk through
        self.custom_colliders: List[AABB] = []

    def add_collider(self, aabb: AABB):
        """Add a static obstacle AABB box to collision checks."""
        self.custom_colliders.append(aabb)

    def get_player_cylinder(self, px: float, py: float, pz: float, elevated: bool = True) -> Cylinder:
        """Create player collision cylinder. If elevated=True, elevates base by step_height so feet slide over low thresholds."""
        step = self.step_height if elevated else 0.0
        base_y = py - self.player_height + step
        h = max(0.2, self.player_height - step + 0.15)
        return Cylinder(Vec3(px, base_y, pz), radius=self.player_radius, height=h)

    def _check_cylinder_collision(self, cyl: Cylinder, ignore_entities: Optional[List[Entity]] = None) -> Optional[Tuple[bool, Vec3]]:
        """Check if player cylinder intersects any obstacles and return MTV if penetrating."""
        # 1. Custom colliders
        for box in self.custom_colliders:
            if box.is_valid() and cyl.intersects_aabb(box):
                hit, mtv = cyl.get_penetration_aabb(box)
                if hit:
                    return hit, mtv

        # 2. Scene entities
        if self.scene:
            for entity in self.scene.entities:
                if not entity.visible or not entity.has_collision or entity.mesh is None:
                    continue
                if ignore_entities and entity in ignore_entities:
                    continue
                if "Plane" in entity.name or "floor" in entity.name.lower():
                    continue

                world_box = entity.world_aabb()
                if world_box.is_valid() and cyl.intersects_aabb(world_box):
                    hit, mtv = cyl.get_penetration_aabb(world_box)
                    if hit:
                        return hit, mtv

        return None

    def get_player_aabb(self, px: float, py: float, pz: float) -> AABB:
        """Calculate player full bounding box for vertical/ground tests."""
        r = self.player_radius
        min_p = Vec3(px - r, py - self.player_height, pz - r)
        max_p = Vec3(px + r, py + 0.15, pz + r)
        return AABB(min_p, max_p)

    def get_player_horizontal_aabb(self, px: float, py: float, pz: float) -> AABB:
        """Calculate player horizontal collision AABB, elevated by step_height so feet don't collide with the floor/platform."""
        r = self.player_radius
        min_p = Vec3(px - r, py - self.player_height + self.step_height, pz - r)
        max_p = Vec3(px + r, py + 0.15, pz + r)
        return AABB(min_p, max_p)

    def _check_collision(self, test_box: AABB, ignore_entities: Optional[List[Entity]] = None) -> Optional[AABB]:
        """Check if test_box intersects any colliders in the scene or custom colliders."""
        # 1. Custom colliders
        for box in self.custom_colliders:
            if box.is_valid() and test_box.intersects(box):
                return box

        # 2. Scene entities
        if self.scene:
            for entity in self.scene.entities:
                if not entity.visible or not entity.has_collision or entity.mesh is None:
                    continue
                if ignore_entities and entity in ignore_entities:
                    continue
                # Skip flat floor planes (floor is handled by ground collision)
                if "Plane" in entity.name or "floor" in entity.name.lower():
                    continue

                world_box = entity.world_aabb()
                if world_box.is_valid() and test_box.intersects(world_box):
                    return world_box

        return None

    def update(self, dt: float):
        if not self.enabled or dt <= 0.0:
            return

        dt = min(dt, 0.1)

        # -------------------------------------------------------------------
        # 1. Mouse Look (Pitch & Yaw)
        # -------------------------------------------------------------------
        if self.input.is_mouse_locked():
            mdx = self.input.mouse_dx
            mdy = self.input.mouse_dy
            if abs(mdx) > 0.001 or abs(mdy) > 0.001:
                self.camera.rotate(mdx * self.mouse_sensitivity, -mdy * self.mouse_sensitivity)

        # -------------------------------------------------------------------
        # 2. WASD Horizontal Movement Vector (projected on XZ plane)
        # -------------------------------------------------------------------
        fwd = self.camera.forward()
        fwd_len = math.hypot(fwd.x, fwd.z)
        if fwd_len > 1e-5:
            fx, fz = fwd.x / fwd_len, fwd.z / fwd_len
        else:
            fx, fz = 0.0, -1.0

        rx = -fz
        rz = fx

        move_x = 0.0
        move_z = 0.0

        if self.input.is_key_down(Key.W):
            move_x += fx
            move_z += fz
        if self.input.is_key_down(Key.S):
            move_x -= fx
            move_z -= fz
        if self.input.is_key_down(Key.A):
            move_x -= rx
            move_z -= rz
        if self.input.is_key_down(Key.D):
            move_x += rx
            move_z += rz

        m_len = math.hypot(move_x, move_z)
        is_sprinting = self.input.is_key_down(Key.LEFT_SHIFT)
        if m_len > 1e-5:
            speed = self.move_speed * dt
            if is_sprinting:
                speed *= 1.6
            dx = (move_x / m_len) * speed
            dz = (move_z / m_len) * speed
        else:
            dx = 0.0
            dz = 0.0

        # -------------------------------------------------------------------
        # 3. Footstep Audio Rhythm
        # -------------------------------------------------------------------
        if m_len > 1e-5 and self.is_grounded:
            step_interval = 0.28 if is_sprinting else 0.40
            self.step_timer += dt
            if self.step_timer >= step_interval:
                self.step_timer = 0.0
                if self.audio and hasattr(self.audio, "play_footstep"):
                    self.audio.play_footstep()
        else:
            self.step_timer = 0.25

        # -------------------------------------------------------------------
        # 4. Jump & Vertical Gravity
        # -------------------------------------------------------------------
        if self.input.is_key_pressed(Key.SPACE) and self.is_grounded:
            self.velocity_y = self.jump_speed
            self.is_grounded = False
            if self.audio and hasattr(self.audio, "play_jump"):
                self.audio.play_jump()

        self.velocity_y -= self.gravity * dt
        dy = self.velocity_y * dt

        # -------------------------------------------------------------------
        # 5. AABB Collision & Sliding (Sub-stepping + Depenetration)
        # -------------------------------------------------------------------
        curr_pos = self.camera.position
        px, py, pz = curr_pos.x, curr_pos.y, curr_pos.z

        # [Axis Y: Vertical step]
        new_py = py + dy
        box_y = self.get_player_aabb(px, new_py, pz)
        hit_y = self._check_collision(box_y)

        if hit_y is not None:
            if self.velocity_y < 0:
                # Landed on top of obstacle (add small epsilon so feet sit cleanly above surface)
                new_py = hit_y.max_point.y + self.player_height + 0.002
                self.velocity_y = 0.0
                self.is_grounded = True
            elif self.velocity_y > 0:
                # Hit ceiling
                new_py = hit_y.min_point.y - 0.15
                self.velocity_y = 0.0
        else:
            # Check default ground level (Y = 0)
            if new_py - self.player_height <= 0.0:
                new_py = self.player_height
                self.velocity_y = 0.0
                self.is_grounded = True
            else:
                self.is_grounded = False

        py = new_py

        # [Sub-stepping for Horizontal Movement with Cylinder]
        dist_xz = math.hypot(dx, dz)
        max_substep = self.player_radius * 0.45
        substeps = max(1, math.ceil(dist_xz / max_substep))
        step_dx = dx / substeps
        step_dz = dz / substeps

        for _ in range(substeps):
            # Check combined movement (step_dx, step_dz)
            cand_cyl = self.get_player_cylinder(px + step_dx, py, pz + step_dz, elevated=True)
            col = self._check_cylinder_collision(cand_cyl)
            if col is None:
                px += step_dx
                pz += step_dz
            else:
                # Direct movement collided with obstacle: try sliding along obstacle face/corner
                hit, mtv = col
                slide_px = px + step_dx + mtv.x
                slide_pz = pz + step_dz + mtv.z
                slide_cyl = self.get_player_cylinder(slide_px, py, slide_pz, elevated=True)
                if self._check_cylinder_collision(slide_cyl) is None:
                    px = slide_px
                    pz = slide_pz
                else:
                    # Separate single-axis slides
                    if abs(step_dx) > 1e-6:
                        x_cyl = self.get_player_cylinder(px + step_dx, py, pz, elevated=True)
                        if self._check_cylinder_collision(x_cyl) is None:
                            px += step_dx
                    if abs(step_dz) > 1e-6:
                        z_cyl = self.get_player_cylinder(px, py, pz + step_dz, elevated=True)
                        if self._check_cylinder_collision(z_cyl) is None:
                            pz += step_dz

        # [Depenetration: Minimum Translation Vector Check via Cylinder]
        current_cyl = self.get_player_cylinder(px, py, pz, elevated=False)
        for custom_box in self.custom_colliders:
            if custom_box.is_valid():
                hit, mtv = current_cyl.get_penetration_aabb(custom_box)
                if hit:
                    px += mtv.x
                    py += mtv.y
                    pz += mtv.z
                    current_cyl = self.get_player_cylinder(px, py, pz, elevated=False)

        if self.scene:
            for entity in self.scene.entities:
                if not entity.visible or not entity.has_collision or entity.mesh is None:
                    continue
                if "Plane" in entity.name or "floor" in entity.name.lower():
                    continue
                wbox = entity.world_aabb()
                if wbox.is_valid():
                    hit, mtv = current_cyl.get_penetration_aabb(wbox)
                    if hit:
                        px += mtv.x
                        py += mtv.y
                        pz += mtv.z
                        if mtv.y > 0.001:
                            self.is_grounded = True
                            self.velocity_y = 0.0
                        current_cyl = self.get_player_cylinder(px, py, pz, elevated=False)

        # Apply resolved position to camera
        self.camera.set_position(px, py, pz)


class FlyCameraController:
    """Free-Fly / Spectator 3D Camera Controller.

    Allows 6DOF flying camera movement with mouse look, keyboard translation (WASD, Space, Shift),
    and mouse cursor auto-locking on click with ESC / TAB release.
    """

    def __init__(
        self,
        camera: Optional[Any] = None,
        input_manager: Optional[Any] = None,
        app: Optional[Any] = None,
        move_speed: float = 8.0,
        mouse_sensitivity: float = 0.12,
        auto_lock_on_click: bool = True,
    ):
        self.app = app
        self.camera = camera or (getattr(app, "camera", None) if app else None)
        self.input = input_manager or (getattr(app, "input", None) if app else None)

        self.move_speed = float(move_speed)
        self.mouse_sensitivity = float(mouse_sensitivity)
        self.auto_lock_on_click = bool(auto_lock_on_click)

        # Position and spherical orientation angles (in degrees)
        self.pos = [0.0, 2.0, 6.0]
        self.yaw = -90.0
        self.pitch = 0.0

        if self.camera is not None:
            if hasattr(self.camera, "position"):
                p = self.camera.position
                if hasattr(p, "x"):
                    self.pos = [float(p.x), float(p.y), float(p.z)]
                elif isinstance(p, (list, tuple)) and len(p) >= 3:
                    self.pos = [float(p[0]), float(p[1]), float(p[2])]
            if hasattr(self.camera, "yaw"):
                self.yaw = float(self.camera.yaw)
            if hasattr(self.camera, "pitch"):
                self.pitch = float(self.camera.pitch)

        self._mouse_locked = False
        self._prev_lmb_down = False
        self._prev_esc_down = False
        self._prev_tab_down = False

        if self.camera is not None:
            self._sync_camera()

    @property
    def position(self) -> Vec3:
        return Vec3(self.pos[0], self.pos[1], self.pos[2])

    @position.setter
    def position(self, val: Any) -> None:
        if hasattr(val, "x"):
            self.pos = [float(val.x), float(val.y), float(val.z)]
        else:
            self.pos = [float(val[0]), float(val[1]), float(val[2])]
        self._sync_camera()

    @property
    def target(self) -> Vec3:
        rad_y = math.radians(self.yaw)
        rad_p = math.radians(self.pitch)
        fx = math.cos(rad_y) * math.cos(rad_p)
        fy = math.sin(rad_p)
        fz = math.sin(rad_y) * math.cos(rad_p)
        return Vec3(self.pos[0] + fx, self.pos[1] + fy, self.pos[2] + fz)

    @target.setter
    def target(self, val: Any) -> None:
        if hasattr(val, "x"):
            self.look_at(val.x, val.y, val.z)
        else:
            self.look_at(val[0], val[1], val[2])

    @property
    def up(self) -> Vec3:
        rad_y = math.radians(self.yaw)
        rad_p = math.radians(self.pitch)
        fx = math.cos(rad_y) * math.cos(rad_p)
        fy = math.sin(rad_p)
        fz = math.sin(rad_y) * math.cos(rad_p)
        rx = -math.sin(rad_y)
        ry = 0.0
        rz = math.cos(rad_y)
        ux = ry * fz - rz * fy
        uy = rz * fx - rx * fz
        uz = rx * fy - ry * fx
        return Vec3(ux, uy, uz)

    def forward(self) -> Vec3:
        rad_y = math.radians(self.yaw)
        rad_p = math.radians(self.pitch)
        fx = math.cos(rad_y) * math.cos(rad_p)
        fy = math.sin(rad_p)
        fz = math.sin(rad_y) * math.cos(rad_p)
        return Vec3(fx, fy, fz)

    def right(self) -> Vec3:
        rad_y = math.radians(self.yaw)
        rx = -math.sin(rad_y)
        ry = 0.0
        rz = math.cos(rad_y)
        return Vec3(rx, ry, rz)

    @property
    def fov(self) -> float:
        return getattr(self.camera, "fov", 55.0)

    def set_position(self, x: float, y: float, z: float) -> None:
        """Set camera position in world space."""
        self.pos = [float(x), float(y), float(z)]
        self._sync_camera()

    def look_at(self, x: float, y: float, z: float) -> None:
        """Orient camera towards target coordinates (x, y, z)."""
        dx = float(x) - self.pos[0]
        dy = float(y) - self.pos[1]
        dz = float(z) - self.pos[2]
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)
        if dist > 1e-6:
            dx /= dist
            dy /= dist
            dz /= dist
            self.pitch = math.degrees(math.asin(max(-1.0, min(1.0, dy))))
            self.yaw = math.degrees(math.atan2(dz, dx))
            self.pitch = max(-89.0, min(89.0, self.pitch))
            self._sync_camera()

    def set_target(self, x: float, y: float, z: float) -> None:
        """Alias for look_at."""
        self.look_at(x, y, z)

    def set_yaw_pitch(self, new_yaw: float, new_pitch: float) -> None:
        """Directly set camera yaw and pitch in degrees."""
        self.yaw = float(new_yaw)
        self.pitch = max(-89.0, min(89.0, float(new_pitch)))
        self._sync_camera()

    def rotate(self, delta_yaw: float, delta_pitch: float) -> None:
        """Rotate camera by relative delta yaw and delta pitch in degrees."""
        self.yaw += float(delta_yaw)
        self.pitch = max(-89.0, min(89.0, self.pitch + float(delta_pitch)))
        self._sync_camera()

    def is_mouse_locked(self) -> bool:
        """Check if mouse cursor is currently locked and captured."""
        if self.app is not None and hasattr(self.app, "is_mouse_locked"):
            try:
                native_locked = self.app.is_mouse_locked()
                if native_locked != self._mouse_locked and hasattr(self.app, "is_running") and self.app.is_running:
                    self._mouse_locked = native_locked
            except Exception:
                pass
        return self._mouse_locked

    def set_mouse_locked(self, locked: bool) -> None:
        """Lock or release mouse cursor."""
        self._mouse_locked = bool(locked)
        if self.app is not None and hasattr(self.app, "set_mouse_locked"):
            try:
                self.app.set_mouse_locked(locked)
            except Exception:
                pass
        elif self.input is not None and hasattr(self.input, "set_mouse_locked"):
            try:
                self.input.set_mouse_locked(locked)
            except Exception:
                pass

    def _is_key_down(self, input_mgr: Any, key_name: str) -> bool:
        if input_mgr is None:
            return False
        k = getattr(Key, key_name, None)
        if k is None:
            k = getattr(Key, key_name.upper(), None)
        if k is None and key_name.upper() == "SHIFT":
            k = getattr(Key, "LEFT_SHIFT", None)
        if k is not None and hasattr(input_mgr, "is_key_down"):
            try:
                return bool(input_mgr.is_key_down(k))
            except Exception:
                pass
        return False

    def _is_key_pressed(self, input_mgr: Any, key_name: str) -> bool:
        if input_mgr is None:
            return False
        k = getattr(Key, key_name, None)
        if k is None:
            k = getattr(Key, key_name.upper(), None)
        if k is not None and hasattr(input_mgr, "is_key_pressed"):
            try:
                return bool(input_mgr.is_key_pressed(k))
            except Exception:
                pass
        return False

    def _sync_camera(self, target_cam: Optional[Any] = None) -> None:
        cam = target_cam or self.camera
        if cam is None:
            return
        rad_y = math.radians(self.yaw)
        rad_p = math.radians(self.pitch)
        fx = math.cos(rad_y) * math.cos(rad_p)
        fy = math.sin(rad_p)
        fz = math.sin(rad_y) * math.cos(rad_p)

        px, py, pz = self.pos[0], self.pos[1], self.pos[2]
        tx, ty, tz = px + fx, py + fy, pz + fz

        if hasattr(cam, "set_position"):
            try:
                cam.set_position(px, py, pz)
            except Exception:
                pass
        if hasattr(cam, "set_target"):
            try:
                cam.set_target(tx, ty, tz)
            except Exception:
                pass
        try:
            cam.position = Vec3(px, py, pz)
            cam.target = Vec3(tx, ty, tz)
        except Exception:
            try:
                cam.position = (px, py, pz)
                cam.target = (tx, ty, tz)
            except Exception:
                pass

    def screen_to_ray(self, mouse_x: float, mouse_y: float, screen_w: float, screen_h: float) -> Any:
        """Forward screen_to_ray call to underlying camera."""
        if self.camera is not None and hasattr(self.camera, "screen_to_ray"):
            return self.camera.screen_to_ray(mouse_x, mouse_y, screen_w, screen_h)
        from .camera_utils import screen_to_ray
        if self.camera is not None:
            return screen_to_ray(self.camera, mouse_x, mouse_y, screen_w, screen_h)
        raise RuntimeError("FlyCameraController has no camera assigned to perform screen_to_ray")

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Update controller, handle mouse locking, look rotation, and 3D translation.

        Compatible signatures:
            update(camera, input_mgr, dt, width=1280, height=720)
            update(dt, input_mgr=None, width=None, height=None)
            update(camera, dt)
            update(dt)
        """
        cam = self.camera
        input_mgr = self.input
        dt = 1.0 / 60.0
        width = 1280
        height = 720

        if len(args) == 5:
            cam, input_mgr, dt, width, height = args[0], args[1], float(args[2]), int(args[3]), int(args[4])
        elif len(args) == 4:
            if hasattr(args[0], "forward") or hasattr(args[0], "position") or hasattr(args[0], "set_position"):
                cam, input_mgr, dt, width = args[0], args[1], float(args[2]), int(args[3])
            else:
                dt, input_mgr, width, height = float(args[0]), args[1], int(args[2]), int(args[3])
        elif len(args) == 3:
            cam, input_mgr, dt = args[0], args[1], float(args[2])
        elif len(args) == 2:
            if hasattr(args[0], "forward") or hasattr(args[0], "position") or hasattr(args[0], "set_position"):
                cam, dt = args[0], float(args[1])
            else:
                dt, input_mgr = float(args[0]), args[1]
        elif len(args) == 1:
            dt = float(args[0])

        if "camera" in kwargs:
            cam = kwargs["camera"]
        if "input_mgr" in kwargs:
            input_mgr = kwargs["input_mgr"]
        elif "input_manager" in kwargs:
            input_mgr = kwargs["input_manager"]
        if "dt" in kwargs:
            dt = float(kwargs["dt"])
        if "width" in kwargs:
            width = int(kwargs["width"])
        if "height" in kwargs:
            height = int(kwargs["height"])

        if cam is not None and self.camera is None:
            self.camera = cam
        if input_mgr is not None and self.input is None:
            self.input = input_mgr

        cam = cam or self.camera
        input_mgr = input_mgr or self.input
        if input_mgr is None and self.app is not None:
            input_mgr = getattr(self.app, "input", None)

        dt = max(0.0, min(dt, 0.2))

        # 1. Mouse Button 0 (Click / Press) Auto-Lock
        lmb_down = False
        if input_mgr is not None and hasattr(input_mgr, "is_mouse_down"):
            try:
                lmb_down = bool(input_mgr.is_mouse_down(0))
            except Exception:
                pass
        lmb_pressed = lmb_down and not self._prev_lmb_down
        self._prev_lmb_down = lmb_down

        if self.auto_lock_on_click and (lmb_pressed or (lmb_down and not self.is_mouse_locked())):
            self.set_mouse_locked(True)

        # 2. ESC / TAB unlocking
        esc_down = self._is_key_down(input_mgr, "ESCAPE") or self._is_key_down(input_mgr, "Escape")
        esc_pressed = self._is_key_pressed(input_mgr, "ESCAPE") or (esc_down and not self._prev_esc_down)
        self._prev_esc_down = esc_down

        tab_down = self._is_key_down(input_mgr, "TAB") or self._is_key_down(input_mgr, "Tab")
        tab_pressed = self._is_key_pressed(input_mgr, "TAB") or (tab_down and not self._prev_tab_down)
        self._prev_tab_down = tab_down

        if esc_pressed:
            self.set_mouse_locked(False)

        if tab_pressed:
            self.set_mouse_locked(not self.is_mouse_locked())

        # 3. Look & Movement when mouse is locked
        if self.is_mouse_locked():
            mdx = getattr(input_mgr, "mouse_dx", 0.0) if input_mgr else 0.0
            mdy = getattr(input_mgr, "mouse_dy", 0.0) if input_mgr else 0.0

            if abs(mdx) > 1e-4 or abs(mdy) > 1e-4:
                self.yaw += mdx * self.mouse_sensitivity
                self.pitch -= mdy * self.mouse_sensitivity
                self.pitch = max(-89.0, min(89.0, self.pitch))

            rad_y = math.radians(self.yaw)
            rad_p = math.radians(self.pitch)

            fx = math.cos(rad_y) * math.cos(rad_p)
            fy = math.sin(rad_p)
            fz = math.sin(rad_y) * math.cos(rad_p)

            rx = -math.sin(rad_y)
            ry = 0.0
            rz = math.cos(rad_y)

            speed = self.move_speed * dt

            # W / S: move forward / backward along look vector (W zooms in, S zooms out)
            if self._is_key_down(input_mgr, "W"):
                self.pos[0] += fx * speed
                self.pos[1] += fy * speed
                self.pos[2] += fz * speed
            if self._is_key_down(input_mgr, "S"):
                self.pos[0] -= fx * speed
                self.pos[1] -= fy * speed
                self.pos[2] -= fz * speed

            # A / D: strafe left / right
            if self._is_key_down(input_mgr, "D"):
                self.pos[0] += rx * speed
                self.pos[1] += ry * speed
                self.pos[2] += rz * speed
            if self._is_key_down(input_mgr, "A"):
                self.pos[0] -= rx * speed
                self.pos[1] -= ry * speed
                self.pos[2] -= rz * speed

            # Space: fly straight up: pos.y += move_speed * dt
            if self._is_key_down(input_mgr, "SPACE") or self._is_key_down(input_mgr, "Space"):
                self.pos[1] += speed

            # LeftShift: fly straight down: pos.y -= move_speed * dt
            if (
                self._is_key_down(input_mgr, "LEFT_SHIFT")
                or self._is_key_down(input_mgr, "LeftShift")
                or self._is_key_down(input_mgr, "SHIFT")
            ):
                self.pos[1] -= speed

        # 4. Sync camera
        self._sync_camera(cam)


# Alias
FreeCameraController = FlyCameraController

__all__ = [
    "FirstPersonController",
    "FlyCameraController",
    "FreeCameraController",
]

