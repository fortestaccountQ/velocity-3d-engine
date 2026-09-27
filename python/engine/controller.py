"""First-person character controller with mouse look, gravity, jump, AABB collision, depenetration, and audio."""

import math
from typing import Optional, List, Tuple
from engine import Key, Camera, InputManager, Scene, Entity, AABB, Cylinder, Vec3


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
