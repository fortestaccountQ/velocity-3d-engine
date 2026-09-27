"""First-person character controller with mouse look, gravity, jump, and AABB collision resolution."""

import math
from typing import Optional, List
from engine import Key, Camera, InputManager, Scene, Entity, AABB, Vec3


class FirstPersonController:
    """First-Person Controller for walking, jumping, mouse-look, and AABB physics collisions."""

    def __init__(
        self,
        camera: Camera,
        input_manager: InputManager,
        scene: Optional[Scene] = None,
        move_speed: float = 5.0,
        mouse_sensitivity: float = 0.14,
        gravity: float = 16.0,
        jump_speed: float = 6.0,
        player_height: float = 1.7,
        player_radius: float = 0.35,
    ):
        self.camera = camera
        self.input = input_manager
        self.scene = scene

        self.move_speed = move_speed
        self.mouse_sensitivity = mouse_sensitivity
        self.gravity = gravity
        self.jump_speed = jump_speed
        self.player_height = player_height
        self.player_radius = player_radius

        self.velocity_y = 0.0
        self.is_grounded = True
        self.enabled = True

        # Custom obstacle AABBs that player cannot walk through
        self.custom_colliders: List[AABB] = []

    def add_collider(self, aabb: AABB):
        """Add a static obstacle AABB box to collision checks."""
        self.custom_colliders.append(aabb)

    def get_player_aabb(self, px: float, py: float, pz: float) -> AABB:
        """Calculate player bounding box for a given eye position (px, py, pz)."""
        r = self.player_radius
        # Eye is at py, feet at py - player_height
        min_p = Vec3(px - r, py - self.player_height, pz - r)
        max_p = Vec3(px + r, py + 0.1, pz + r)
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
                # delta_yaw, delta_pitch
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
        if m_len > 1e-5:
            speed = self.move_speed * dt
            # Optional sprint with Shift
            if self.input.is_key_down(Key.LEFT_SHIFT):
                speed *= 1.6
            dx = (move_x / m_len) * speed
            dz = (move_z / m_len) * speed
        else:
            dx = 0.0
            dz = 0.0

        # -------------------------------------------------------------------
        # 3. Jump & Vertical Gravity
        # -------------------------------------------------------------------
        if self.input.is_key_pressed(Key.SPACE) and self.is_grounded:
            self.velocity_y = self.jump_speed
            self.is_grounded = False

        self.velocity_y -= self.gravity * dt
        dy = self.velocity_y * dt

        # -------------------------------------------------------------------
        # 4. AABB Collision & Sliding (Independent Axis Testing)
        # -------------------------------------------------------------------
        curr_pos = self.camera.position
        px, py, pz = curr_pos.x, curr_pos.y, curr_pos.z

        # [Axis Y: Vertical step]
        new_py = py + dy
        box_y = self.get_player_aabb(px, new_py, pz)
        hit_y = self._check_collision(box_y)

        if hit_y is not None:
            if self.velocity_y < 0:
                # Landed on top of obstacle
                new_py = hit_y.max_point.y + self.player_height
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

        # [Axis X: Horizontal sliding]
        if abs(dx) > 1e-6:
            new_px = px + dx
            box_x = self.get_player_aabb(new_px, py, pz)
            if self._check_collision(box_x) is None:
                px = new_px

        # [Axis Z: Horizontal sliding]
        if abs(dz) > 1e-6:
            new_pz = pz + dz
            box_z = self.get_player_aabb(px, py, new_pz)
            if self._check_collision(box_z) is None:
                pz = new_pz

        # Apply resolved position to camera
        self.camera.set_position(px, py, pz)
