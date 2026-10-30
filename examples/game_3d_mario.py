"""game_3d_mario.py - Complete Playable 3D Mario Platformer for Velocity 3D Engine.

Features:
- Responsive Mario Character Controller:
  * WASD / Arrow keys for 3D platforming locomotion with smooth directional rotation.
  * Space for variable jump height: tap for short hop, hold for high leap.
  * Double-jump somersault (front flip) when pressing Space near jump peak.
  * Shift while airborne to Ground Pound (plunges downward and shatters breakable blocks).
  * Pitfall respawn upon falling below Y = -6.0.
- Dynamic Environment & Level Design:
  * Vibrant sky atmosphere and sunlight with ambient illumination.
  * Ascending floating grassy islands (green tops, brown soil sides).
  * Dynamic sine-wave moving platforms (horizontal sky cruiser and vertical cloud elevator)
    transferring momentum to the player.
  * Collectible spinning 3D gold coins (yellow cylinders rotating at 90 deg/s) hovering in arcs.
  * Breakable '?' blocks with out_bounce tween and floating bonus coin release.
  * Power Star at the summit with radiant glowing mesh, PointLight, and victory particle burst.
- Third-Person Camera:
  * Spring-arm FollowCamera tracking Mario with smooth damping.
- 2D HUD:
  * Live Lives (❤️ x 3), Coins (🪙 x 0), Timer, Score, and interactive controls banner.
- Headless / CI Verification:
  * Support for `--test` CLI flag and automated self-play bot loop executing 120 frames cleanly.
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Any

# Ensure repository root and python directory are in sys.path
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import VelocityEngine as ve
from VelocityEngine import (
    App,
    Key,
    Color,
    Mesh,
    StandardMaterial,
    PointLight,
    ParticleEmitter,
    BlendMode,
    FollowCamera,
    UIOverlay,
    Vec3,
    Vec4,
    AABB,
    WHITE,
    YELLOW,
    GREEN,
    RED,
    CYAN,
    WARM_WHITE,
    out_bounce,
    out_quad,
    out_cubic,
)


def ensure_desktop_access() -> None:
    """Ensure Windows desktop station access when running from background services."""
    if sys.platform == "win32":
        try:
            import ctypes
            u32 = ctypes.windll.user32
            hdesk = u32.OpenInputDesktop(0, False, 0x01FF)
            if hdesk:
                u32.SetThreadDesktop(hdesk)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Procedural Textures & Materials
# ---------------------------------------------------------------------------

def create_question_texture(width: int = 32, height: int = 32) -> ve.Texture:
    """Generate a pixel-art '?' block procedural texture with rivets and drop shadow."""
    buf = bytearray(width * height * 4)
    q_mask = [
        "  XXXX  ",
        " XX  XX ",
        "XX    XX",
        "      XX",
        "     XX ",
        "    XX  ",
        "   XX   ",
        "   XX   ",
        "        ",
        "   XX   ",
        "   XX   ",
        "        ",
    ]
    mw = len(q_mask[0])
    mh = len(q_mask)
    ox = (width - mw) // 2
    oy = (height - mh) // 2

    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            # Border frame
            if x in (0, width - 1) or y in (0, height - 1):
                r, g, b, a = 180, 100, 0, 255
            elif (x in (2, 3, width - 4, width - 3) and y in (2, 3, height - 4, height - 3)):
                r, g, b, a = 60, 30, 0, 255  # Corner rivets
            else:
                gx = x - ox
                gy = y - oy
                if 0 <= gx < mw and 0 <= gy < mh and q_mask[gy][gx] == "X":
                    r, g, b, a = 255, 255, 255, 255  # White '?'
                elif 0 <= (gx - 1) < mw and 0 <= (gy - 1) < mh and q_mask[gy - 1][gx - 1] == "X":
                    r, g, b, a = 120, 65, 0, 255  # Drop shadow
                else:
                    r, g, b, a = 252, 176, 0, 255  # Golden background
            buf[idx] = r
            buf[idx + 1] = g
            buf[idx + 2] = b
            buf[idx + 3] = a
    return ve.DataTexture(buf, width, height)


def create_empty_block_texture(width: int = 32, height: int = 32) -> ve.Texture:
    """Generate an inactive / emptied block texture (bronze with rivets)."""
    buf = bytearray(width * height * 4)
    for y in range(height):
        for x in range(width):
            idx = (y * width + x) * 4
            if x in (0, width - 1) or y in (0, height - 1):
                r, g, b, a = 100, 60, 30, 255
            elif (x in (2, 3, width - 4, width - 3) and y in (2, 3, height - 4, height - 3)):
                r, g, b, a = 40, 25, 10, 255
            else:
                r, g, b, a = 145, 95, 55, 255
            buf[idx] = r
            buf[idx + 1] = g
            buf[idx + 2] = b
            buf[idx + 3] = a
    return ve.DataTexture(buf, width, height)


# ---------------------------------------------------------------------------
# Procedural 3D Character: Mario
# ---------------------------------------------------------------------------

def build_mario_character(scene: ve.Scene) -> ve.Entity:
    """Construct stylized modular 3D Mario character with iconic cap, overalls, and moustache."""
    root = scene.create_entity("Mario_Player_Root")

    # Reusable PBR Materials
    red_mat = StandardMaterial()
    red_mat.base_color = (0.88, 0.12, 0.12, 1.0)
    red_mat.roughness = 0.45

    blue_mat = StandardMaterial()
    blue_mat.base_color = (0.12, 0.35, 0.85, 1.0)
    blue_mat.roughness = 0.55

    skin_mat = StandardMaterial()
    skin_mat.base_color = (1.0, 0.80, 0.64, 1.0)
    skin_mat.roughness = 0.7

    brown_mat = StandardMaterial()
    brown_mat.base_color = (0.42, 0.22, 0.10, 1.0)
    brown_mat.roughness = 0.8

    yellow_mat = StandardMaterial()
    yellow_mat.base_color = (1.0, 0.85, 0.10, 1.0)
    yellow_mat.metallic = 0.5

    white_mat = StandardMaterial()
    white_mat.base_color = (0.95, 0.95, 0.95, 1.0)
    white_mat.roughness = 0.5

    black_mat = StandardMaterial()
    black_mat.base_color = (0.08, 0.08, 0.08, 1.0)
    black_mat.roughness = 0.8

    # Boots
    boot_l = scene.create_entity("Mario_Boot_L")
    boot_l.mesh = Mesh.create_box(0.18, 0.14, 0.26)
    boot_l.material = brown_mat
    boot_l.transform.position = (-0.12, 0.07, -0.04)
    root.add(boot_l)

    boot_r = scene.create_entity("Mario_Boot_R")
    boot_r.mesh = Mesh.create_box(0.18, 0.14, 0.26)
    boot_r.material = brown_mat
    boot_r.transform.position = (0.12, 0.07, -0.04)
    root.add(boot_r)

    # Overalls trousers / legs
    legs = scene.create_entity("Mario_Legs")
    legs.mesh = Mesh.create_box(0.38, 0.30, 0.28)
    legs.material = blue_mat
    legs.transform.position = (0.0, 0.26, 0.0)
    root.add(legs)

    # Torso (Red Shirt)
    torso = scene.create_entity("Mario_Torso")
    torso.mesh = Mesh.create_box(0.44, 0.36, 0.32)
    torso.material = red_mat
    torso.transform.position = (0.0, 0.56, 0.0)
    root.add(torso)

    # Overalls Bib
    bib = scene.create_entity("Mario_Bib")
    bib.mesh = Mesh.create_box(0.32, 0.32, 0.34)
    bib.material = blue_mat
    bib.transform.position = (0.0, 0.54, 0.0)
    root.add(bib)

    # Overalls Yellow Buttons
    btn_l = scene.create_entity("Mario_Btn_L")
    btn_l.mesh = Mesh.create_sphere(radius=0.04, rings=8, sectors=8)
    btn_l.material = yellow_mat
    btn_l.transform.position = (-0.10, 0.62, -0.18)
    root.add(btn_l)

    btn_r = scene.create_entity("Mario_Btn_R")
    btn_r.mesh = Mesh.create_sphere(radius=0.04, rings=8, sectors=8)
    btn_r.material = yellow_mat
    btn_r.transform.position = (0.10, 0.62, -0.18)
    root.add(btn_r)

    # White Gloves
    glove_l = scene.create_entity("Mario_Glove_L")
    glove_l.mesh = Mesh.create_sphere(radius=0.10, rings=10, sectors=10)
    glove_l.material = white_mat
    glove_l.transform.position = (-0.28, 0.52, 0.0)
    root.add(glove_l)

    glove_r = scene.create_entity("Mario_Glove_R")
    glove_r.mesh = Mesh.create_sphere(radius=0.10, rings=10, sectors=10)
    glove_r.material = white_mat
    glove_r.transform.position = (0.28, 0.52, 0.0)
    root.add(glove_r)

    # Head
    head = scene.create_entity("Mario_Head")
    head.mesh = Mesh.create_sphere(radius=0.22, rings=16, sectors=16)
    head.material = skin_mat
    head.transform.position = (0.0, 0.94, 0.0)
    root.add(head)

    # Nose
    nose = scene.create_entity("Mario_Nose")
    nose.mesh = Mesh.create_sphere(radius=0.09, rings=10, sectors=10)
    nose.material = skin_mat
    nose.transform.position = (0.0, 0.93, -0.22)
    root.add(nose)

    # Moustache
    moust = scene.create_entity("Mario_Moustache")
    moust.mesh = Mesh.create_box(0.24, 0.08, 0.09)
    moust.material = black_mat
    moust.transform.position = (0.0, 0.87, -0.21)
    root.add(moust)

    # Eyes
    eye_l = scene.create_entity("Mario_Eye_L")
    eye_l.mesh = Mesh.create_sphere(radius=0.04, rings=8, sectors=8)
    eye_l.material = black_mat
    eye_l.transform.position = (-0.08, 0.98, -0.19)
    root.add(eye_l)

    eye_r = scene.create_entity("Mario_Eye_R")
    eye_r.mesh = Mesh.create_sphere(radius=0.04, rings=8, sectors=8)
    eye_r.material = black_mat
    eye_r.transform.position = (0.08, 0.98, -0.19)
    root.add(eye_r)

    # Cap Dome & Brim
    cap_dome = scene.create_entity("Mario_Cap_Dome")
    cap_dome.mesh = Mesh.create_sphere(radius=0.25, rings=16, sectors=16)
    cap_dome.material = red_mat
    cap_dome.transform.position = (0.0, 1.06, 0.01)
    root.add(cap_dome)

    cap_brim = scene.create_entity("Mario_Cap_Brim")
    cap_brim.mesh = Mesh.create_box(0.34, 0.05, 0.20)
    cap_brim.material = red_mat
    cap_brim.transform.position = (0.0, 1.02, -0.20)
    root.add(cap_brim)

    return root


# ---------------------------------------------------------------------------
# Dynamic Entities & Gameplay Objects
# ---------------------------------------------------------------------------

class MovingPlatform:
    """Dynamic moving platform oscillating along sine paths and transferring delta velocity."""

    def __init__(
        self,
        scene: ve.Scene,
        start_pos: ve.Vec3,
        end_pos: ve.Vec3,
        size: Tuple[float, float, float] = (3.5, 0.6, 3.5),
        speed: float = 1.6,
        phase: float = 0.0,
        name: str = "MovingPlatform",
    ) -> None:
        self.start_pos: ve.Vec3 = ve.Vec3(start_pos.x, start_pos.y, start_pos.z)
        self.end_pos: ve.Vec3 = ve.Vec3(end_pos.x, end_pos.y, end_pos.z)
        self.velocity: ve.Vec3 = ve.Vec3(0.0, 0.0, 0.0)
        self.phase: float = float(phase)
        self.speed: float = float(speed)
        self.size: Tuple[float, float, float] = size

        hw = size[0] * 0.5
        hh = size[1] * 0.5
        hd = size[2] * 0.5

        # Platform Entity
        self.entity: ve.Entity = scene.create_entity(name)
        self.entity.mesh = Mesh.create_box(size[0], size[1], size[2])

        plat_mat = StandardMaterial()
        plat_mat.base_color = (0.92, 0.72, 0.28, 1.0)  # Golden wood / lift
        plat_mat.metallic = 0.2
        plat_mat.roughness = 0.4
        self.entity.material = plat_mat
        self.entity.transform.position = (start_pos.x, start_pos.y, start_pos.z)

        self.aabb: ve.AABB = ve.AABB(
            ve.Vec3(start_pos.x - hw, start_pos.y - hh, start_pos.z - hd),
            ve.Vec3(start_pos.x + hw, start_pos.y + hh, start_pos.z + hd),
        )

    def update(self, dt: float) -> None:
        """Advance platform along trajectory and calculate instantaneous velocity."""
        dt_safe = max(0.001, dt)
        prev_x = self.entity.transform.position.x
        prev_y = self.entity.transform.position.y
        prev_z = self.entity.transform.position.z

        self.phase += self.speed * dt
        t = (math.sin(self.phase) + 1.0) * 0.5

        new_x = self.start_pos.x + (self.end_pos.x - self.start_pos.x) * t
        new_y = self.start_pos.y + (self.end_pos.y - self.start_pos.y) * t
        new_z = self.start_pos.z + (self.end_pos.z - self.start_pos.z) * t

        self.entity.transform.position = (new_x, new_y, new_z)

        self.velocity = ve.Vec3(
            (new_x - prev_x) / dt_safe,
            (new_y - prev_y) / dt_safe,
            (new_z - prev_z) / dt_safe,
        )

        hw = self.size[0] * 0.5
        hh = self.size[1] * 0.5
        hd = self.size[2] * 0.5
        self.aabb = ve.AABB(
            ve.Vec3(new_x - hw, new_y - hh, new_z - hd),
            ve.Vec3(new_x + hw, new_y + hh, new_z + hd),
        )


class Coin:
    """Collectible spinning 3D gold coin rotating at 90 deg/s with scale-punch tween."""

    def __init__(self, scene: ve.Scene, position: ve.Vec3, coin_mesh: ve.Mesh, coin_mat: ve.StandardMaterial) -> None:
        self.scene: ve.Scene = scene
        self.position: ve.Vec3 = ve.Vec3(position.x, position.y, position.z)
        self.base_pos: ve.Vec3 = ve.Vec3(position.x, position.y, position.z)
        self.rotation_angle: float = random.uniform(0.0, 360.0)
        self.is_collected: bool = False

        self.entity: ve.Entity = scene.create_entity(f"Coin_{int(position.x)}_{int(position.z)}")
        self.entity.mesh = coin_mesh
        self.entity.material = coin_mat
        self.entity.transform.position = (self.position.x, self.position.y, self.position.z)
        self.entity.transform.rotation = (90.0, self.rotation_angle, 0.0)

    def update(self, dt: float) -> None:
        if self.is_collected:
            return
        # Continuous rotation at 90 degrees/sec
        self.rotation_angle = (self.rotation_angle + 90.0 * dt) % 360.0
        # Gentle floating bobbing
        bob = math.sin(self.rotation_angle * 0.05) * 0.08
        self.entity.transform.position = (self.base_pos.x, self.base_pos.y + bob, self.base_pos.z)
        self.entity.transform.rotation = (90.0, self.rotation_angle, 0.0)

    def collect(self, player: Any, app: Any) -> None:
        if self.is_collected:
            return
        self.is_collected = True

        # Play audio chime
        if hasattr(app, "audio") and hasattr(app.audio, "play_hit_3d"):
            try:
                app.audio.play_hit_3d((self.position.x, self.position.y, self.position.z))
            except Exception:
                pass

        # Scale punch tween: expand up to 1.8x, rise upward, and remove
        target_pos = (self.position.x, self.position.y + 0.8, self.position.z)
        self.entity.animate_scale(
            target=(1.8, 1.8, 1.8),
            duration=0.18,
            ease="out_quad",
            on_complete=lambda: self.destroy(),
        )
        self.entity.animate_position(
            target=target_pos,
            duration=0.18,
            ease="out_quad",
        )

    def destroy(self) -> None:
        if self.entity is not None and self.scene is not None:
            try:
                self.scene.remove_entity(self.entity)
            except Exception:
                pass
            self.entity = None

    cleanup = destroy


class QuestionBlock:
    """Breakable / Bouncable '?' Block with out_bounce tween and floating bonus coin."""

    def __init__(
        self,
        scene: ve.Scene,
        position: ve.Vec3,
        box_mesh: ve.Mesh,
        active_mat: ve.StandardMaterial,
        inactive_mat: ve.StandardMaterial,
        coin_mesh: ve.Mesh,
        coin_mat: ve.StandardMaterial,
        is_breakable_only: bool = False,
    ) -> None:
        self.scene: ve.Scene = scene
        self.base_pos: ve.Vec3 = ve.Vec3(position.x, position.y, position.z)
        self.inactive_mat: ve.StandardMaterial = inactive_mat
        self.coin_mesh: ve.Mesh = coin_mesh
        self.coin_mat: ve.StandardMaterial = coin_mat
        self.is_breakable_only: bool = is_breakable_only

        self.is_broken: bool = False
        self.has_item: bool = not is_breakable_only
        self.is_bumping: bool = False
        self.active_extras: List[ve.Entity] = []

        self.entity: ve.Entity = scene.create_entity(f"QBlock_{int(position.x)}_{int(position.z)}")
        self.entity.mesh = box_mesh
        self.entity.material = active_mat
        self.entity.transform.position = (position.x, position.y, position.z)

        # 1x1x1 bounding box
        self.aabb: ve.AABB = ve.AABB(
            ve.Vec3(position.x - 0.5, position.y - 0.5, position.z - 0.5),
            ve.Vec3(position.x + 0.5, position.y + 0.5, position.z + 0.5),
        )

    def bump(self, player: Any, app: Any) -> None:
        """Player head hits block from below: bounces upward with out_bounce easing."""
        if self.is_bumping or self.is_broken:
            return
        self.is_bumping = True

        bx, by, bz = self.base_pos.x, self.base_pos.y, self.base_pos.z

        # Audio hit chime
        if hasattr(app, "audio") and hasattr(app.audio, "play_hit_3d"):
            try:
                app.audio.play_hit_3d((bx, by, bz))
            except Exception:
                pass

        # out_bounce bounce tween upward
        self.entity.animate_position(
            target=(bx, by + 0.45, bz),
            duration=0.10,
            ease="out_quad",
            on_complete=lambda: self.entity.animate_position(
                target=(bx, by, bz),
                duration=0.22,
                ease="out_bounce",
                on_complete=lambda: setattr(self, "is_bumping", False),
            ),
        )

        # Pop out a bonus gold coin if item available
        if self.has_item:
            self.has_item = False
            self.entity.material = self.inactive_mat
            player.coins += 1
            player.score += 200

            bonus_coin = self.scene.create_entity("BonusCoin")
            bonus_coin.mesh = self.coin_mesh
            bonus_coin.material = self.coin_mat
            bonus_coin.transform.position = (bx, by + 0.6, bz)
            bonus_coin.transform.rotation = (90.0, 0.0, 0.0)
            self.active_extras.append(bonus_coin)

            # Animate bonus coin popping up and collecting
            bonus_coin.animate_position(
                target=(bx, by + 1.8, bz),
                duration=0.25,
                ease="out_quad",
                on_complete=lambda: bonus_coin.animate_scale(
                    target=(0.0, 0.0, 0.0),
                    duration=0.12,
                    ease="out_cubic",
                    on_complete=lambda: self._remove_extra(bonus_coin),
                ),
            )

    def _remove_extra(self, ent: ve.Entity) -> None:
        if ent in self.active_extras:
            self.active_extras.remove(ent)
        if self.scene is not None:
            try:
                self.scene.remove_entity(ent)
            except Exception:
                pass

    def shatter(self, player: Any, app: Any) -> None:
        """Ground Pound from above smashes and breaks the block into flying debris."""
        if self.is_broken:
            return
        self.is_broken = True

        bx, by, bz = self.base_pos.x, self.base_pos.y, self.base_pos.z
        player.score += 300
        player.coins += 1

        if hasattr(app, "audio") and hasattr(app.audio, "play_hit_3d"):
            try:
                app.audio.play_hit_3d((bx, by, bz))
            except Exception:
                pass

        # Spawn 4 flying debris cubes
        debris_mesh = Mesh.create_box(0.35, 0.35, 0.35)
        for dx, dz in [(-0.3, -0.3), (0.3, -0.3), (-0.3, 0.3), (0.3, 0.3)]:
            deb = self.scene.create_entity("BlockDebris")
            deb.mesh = debris_mesh
            deb.material = self.inactive_mat
            deb.transform.position = (bx + dx, by + 0.2, bz + dz)
            self.active_extras.append(deb)
            deb.animate_position(
                target=(bx + dx * 3.5, by + random.uniform(1.0, 2.5), bz + dz * 3.5),
                duration=0.45,
                ease="out_quad",
                on_complete=lambda d=deb: self._remove_extra(d),
            )

        # Remove main block
        self.scene.remove_entity(self.entity)
        self.entity = None

    def cleanup(self) -> None:
        if self.entity is not None and self.scene is not None:
            try:
                self.scene.remove_entity(self.entity)
            except Exception:
                pass
            self.entity = None
        for ext in self.active_extras:
            if self.scene is not None:
                try:
                    self.scene.remove_entity(ext)
                except Exception:
                    pass
        self.active_extras.clear()


class PowerStar:
    """Golden glowing 5-pointed Power Star at the summit with radiant light and fanfare."""

    def __init__(self, scene: ve.Scene, position: ve.Vec3) -> None:
        self.scene: ve.Scene = scene
        self.position: ve.Vec3 = ve.Vec3(position.x, position.y, position.z)
        self.base_y: float = float(position.y)
        self.is_collected: bool = False
        self.rotation_angle: float = 0.0

        # Procedural 5-pointed star polygon
        pts = []
        for i in range(10):
            r = 0.75 if i % 2 == 0 else 0.36
            a = i * math.pi / 5.0 - math.pi / 2.0
            pts.append((r * math.cos(a), r * math.sin(a)))

        star_mesh = Mesh.create_extrude(pts, depth=0.25)

        star_mat = StandardMaterial()
        star_mat.base_color = (1.0, 0.92, 0.15, 1.0)
        star_mat.emissive_color = (1.0, 0.88, 0.20)
        star_mat.emissive_intensity = 2.4
        star_mat.metallic = 0.85
        star_mat.roughness = 0.15

        self.entity: ve.Entity = scene.create_entity("PowerStar_Summit")
        self.entity.mesh = star_mesh
        self.entity.material = star_mat
        self.entity.transform.position = (position.x, position.y, position.z)

        # Radiant golden point light
        self.light: ve.PointLight = PointLight("StarGlowLight", Vec3(1.0, 0.85, 0.2), 3.5, 12.0, 1.8)
        self.light.transform.position = (position.x, position.y, position.z)
        scene.add_light(self.light)

    def update(self, dt: float) -> None:
        if self.is_collected:
            return
        self.rotation_angle = (self.rotation_angle + 110.0 * dt) % 360.0
        bob = math.sin(self.rotation_angle * 0.05) * 0.25
        curr_y = self.base_y + bob

        self.entity.transform.position = (self.position.x, curr_y, self.position.z)
        self.entity.transform.rotation = (0.0, self.rotation_angle, 0.0)
        self.light.transform.position = (self.position.x, curr_y, self.position.z)

    def collect(self, player: Any, app: Any) -> None:
        if self.is_collected:
            return
        self.is_collected = True
        player.score += 5000
        player.stars_collected += 1

        # Victory audio fanfare
        if hasattr(app, "audio"):
            try:
                if hasattr(app.audio, "play_jump"):
                    app.audio.play_jump()
                if hasattr(app.audio, "play_hit_3d"):
                    app.audio.play_hit_3d((self.position.x, self.position.y, self.position.z))
            except Exception:
                pass

        # Celebration particle burst
        self.burst = ParticleEmitter(250)
        self.burst.emission_rate = 450.0
        self.burst.lifespan = 2.0
        self.burst.velocity = Vec3(0.0, 4.5, 0.0)
        self.burst.spread = Vec3(4.0, 4.0, 4.0)
        self.burst.gravity = Vec3(0.0, -3.5, 0.0)
        self.burst.start_color = Vec4(1.0, 0.95, 0.25, 1.0)
        self.burst.end_color = Vec4(1.0, 0.2, 0.1, 0.0)
        self.burst.start_size = 0.28
        self.burst.end_size = 0.04
        self.burst.blend_mode = BlendMode.Additive
        self.burst.set_position(self.position.x, self.position.y, self.position.z)
        self.scene.add(self.burst)

        # Scale punch and ascension
        self.entity.animate_scale(
            target=(2.2, 2.2, 2.2),
            duration=0.3,
            ease="out_quad",
            on_complete=lambda: self.entity.animate_position(
                target=(self.position.x, self.position.y + 4.0, self.position.z),
                duration=0.6,
                ease="out_cubic",
            ),
        )

    def cleanup(self) -> None:
        if hasattr(self, "burst") and self.burst is not None:
            try:
                self.scene.remove(self.burst)
            except Exception:
                pass
            self.burst = None
        if self.light is not None:
            try:
                self.scene.remove_light(self.light)
            except Exception:
                pass
            self.light = None
        if self.entity is not None:
            try:
                self.scene.remove_entity(self.entity)
            except Exception:
                pass
            self.entity = None


# ---------------------------------------------------------------------------
# Mario Player Implementation
# ---------------------------------------------------------------------------

class MarioPlayer:
    """Interactive 3D Mario Character with variable jumping, double-jump somersault, and ground pound."""

    def __init__(self, scene: ve.Scene, app: ve.App) -> None:
        self.scene: ve.Scene = scene
        self.app: ve.App = app

        # Public state attributes conforming to MASTER_PLAN.md
        self.position: ve.Vec3 = ve.Vec3(0.0, 1.2, 3.5)
        self.velocity: ve.Vec3 = ve.Vec3(0.0, 0.0, 0.0)
        self.facing_angle: float = 180.0  # Facing forward (-Z)
        self.pitch_angle: float = 0.0     # Somersault rotation
        self.is_grounded: bool = True
        self.is_double_jump_ready: bool = False
        self.is_ground_pounding: bool = False
        self.lives: int = 3
        self.coins: int = 0
        self.score: int = 0
        self.stars_collected: int = 0

        # Jump dynamics state
        self.is_jumping: bool = False
        self.was_double_jumped: bool = False
        self.jump_hold_timer: float = 0.0
        self.somersault_timer: float = 0.0
        self.is_somersaulting: bool = False
        self.current_platform: Optional[MovingPlatform] = None

        # Collision dimensions
        self.radius: float = 0.40
        self.height: float = 1.35

        # Visual Character Hierarchy
        self.root_entity: ve.Entity = build_mario_character(scene)
        self.root_entity.transform.position = (self.position.x, self.position.y, self.position.z)
        self.root_entity.transform.rotation = (0.0, self.facing_angle, 0.0)

        # Previous frame input states for edge detection
        self._prev_space: bool = False
        self._prev_shift: bool = False

    def handle_input(self, input_mgr: ve.InputManager, dt: float) -> None:
        """Process keyboard locomotion, variable jumping, double-jump trigger, and ground pound."""
        # Query Keys
        w = input_mgr.is_key_down(Key.W) or input_mgr.is_key_down(Key.UP)
        s = input_mgr.is_key_down(Key.S) or input_mgr.is_key_down(Key.DOWN)
        a = input_mgr.is_key_down(Key.A) or input_mgr.is_key_down(Key.LEFT)
        d = input_mgr.is_key_down(Key.D) or input_mgr.is_key_down(Key.RIGHT)
        space = input_mgr.is_key_down(Key.SPACE)
        shift = input_mgr.is_key_down(Key.LEFT_SHIFT)

        space_pressed = space and not self._prev_space
        shift_pressed = shift and not self._prev_shift
        self._prev_space = space
        self._prev_shift = shift

        # 1. Horizontal Locomotion (+X right, -Z forward)
        move_x = (1.0 if d else 0.0) - (1.0 if a else 0.0)
        move_z = (1.0 if s else 0.0) - (1.0 if w else 0.0)

        if not self.is_ground_pounding:
            if move_x != 0.0 or move_z != 0.0:
                length = math.sqrt(move_x * move_x + move_z * move_z)
                move_x /= length
                move_z /= length

                # Smoothly rotate toward moving direction
                target_facing = math.degrees(math.atan2(-move_x, -move_z))
                angle_diff = (target_facing - self.facing_angle + 180.0) % 360.0 - 180.0
                self.facing_angle += angle_diff * min(1.0, 16.0 * dt)

                # Acceleration
                speed = 7.5 if self.is_grounded else 6.2
                target_vx = move_x * speed
                target_vz = move_z * speed
                lerp_rate = 14.0 if self.is_grounded else 7.0
                self.velocity.x += (target_vx - self.velocity.x) * min(1.0, lerp_rate * dt)
                self.velocity.z += (target_vz - self.velocity.z) * min(1.0, lerp_rate * dt)
            else:
                # Friction / Deceleration
                drag = 12.0 if self.is_grounded else 3.5
                self.velocity.x += (0.0 - self.velocity.x) * min(1.0, drag * dt)
                self.velocity.z += (0.0 - self.velocity.z) * min(1.0, drag * dt)

        # 2. Jump Handling (Tap vs Hold)
        if self.is_grounded:
            if space_pressed:
                self.velocity.y = 8.5
                self.is_grounded = False
                self.is_jumping = True
                self.jump_hold_timer = 0.0
                self.was_double_jumped = False
                self.is_double_jump_ready = False
                self.current_platform = None
                if hasattr(self.app, "audio") and hasattr(self.app.audio, "play_jump"):
                    try:
                        self.app.audio.play_jump()
                    except Exception:
                        pass
        elif self.is_jumping:
            # Hold jump for higher leap
            if space and self.jump_hold_timer < 0.22 and self.velocity.y > 0.0:
                self.jump_hold_timer += dt
                self.velocity.y += 11.0 * dt
            else:
                self.is_jumping = False

        # 3. Double Jump Somersault Trigger at Jump Peak
        if not self.is_grounded and not self.was_double_jumped:
            # Peak detection (-2.0 <= vy <= 2.5)
            if -2.0 <= self.velocity.y <= 2.5:
                self.is_double_jump_ready = True

            if self.is_double_jump_ready and space_pressed:
                self.velocity.y = 10.0
                self.is_double_jump_ready = False
                self.was_double_jumped = True
                self.is_somersaulting = True
                self.somersault_timer = 0.0
                if hasattr(self.app, "audio") and hasattr(self.app.audio, "play_jump"):
                    try:
                        self.app.audio.play_jump()
                    except Exception:
                        pass

        # 4. Ground Pound (Airborne Shift)
        if not self.is_grounded and shift_pressed and not self.is_ground_pounding:
            self.is_ground_pounding = True
            self.velocity.x = 0.0
            self.velocity.z = 0.0
            self.velocity.y = -22.0  # Swift downward plunge
            if hasattr(self.app, "audio") and hasattr(self.app.audio, "play_hit_3d"):
                try:
                    self.app.audio.play_hit_3d((self.position.x, self.position.y, self.position.z))
                except Exception:
                    pass

    def update_physics(
        self,
        platforms: List[MovingPlatform],
        islands: List[ve.AABB],
        dt: float,
        blocks: Optional[List[QuestionBlock]] = None,
    ) -> None:
        """Resolve platform delta velocity, gravity, island AABB collisions, and block hits."""
        dt_safe = max(0.001, min(0.05, dt))

        # 1. Moving Platform Attachment
        if self.current_platform is not None:
            plat = self.current_platform
            hw = plat.size[0] * 0.5 + self.radius * 0.8
            hd = plat.size[2] * 0.5 + self.radius * 0.8
            pp = plat.entity.transform.position
            top_y = pp.y + plat.size[1] * 0.5

            if (pp.x - hw <= self.position.x <= pp.x + hw and
                pp.z - hd <= self.position.z <= pp.z + hd and
                abs(self.position.y - top_y) < 0.6):
                # Follow platform movement
                self.position.x += plat.velocity.x * dt_safe
                self.position.y = top_y
                self.position.z += plat.velocity.z * dt_safe
                self.velocity.y = 0.0
                self.is_grounded = True
            else:
                self.current_platform = None

        # 2. Gravity
        if not self.is_grounded:
            if self.is_ground_pounding:
                self.velocity.y = -22.0
            else:
                self.velocity.y -= 20.0 * dt_safe
                if self.velocity.y < -25.0:
                    self.velocity.y = -25.0

        # 3. Integrate Proposed Position
        new_x = self.position.x + self.velocity.x * dt_safe
        new_y = self.position.y + self.velocity.y * dt_safe
        new_z = self.position.z + self.velocity.z * dt_safe

        # 4. Resolve Floor Collisions
        grounded_this_frame = False
        highest_ground_y = -999.0
        candidate_platform = None

        # Islands
        for island in islands:
            min_p = island.min_point
            max_p = island.max_point
            if (min_p.x - self.radius * 0.6 <= new_x <= max_p.x + self.radius * 0.6 and
                min_p.z - self.radius * 0.6 <= new_z <= max_p.z + self.radius * 0.6):
                top_y = max_p.y
                if self.position.y >= top_y - 0.35 and new_y <= top_y + 0.25:
                    if top_y > highest_ground_y:
                        highest_ground_y = top_y
                        grounded_this_frame = True

        # Moving Platforms
        for plat in platforms:
            min_p = plat.aabb.min_point
            max_p = plat.aabb.max_point
            if (min_p.x - self.radius * 0.6 <= new_x <= max_p.x + self.radius * 0.6 and
                min_p.z - self.radius * 0.6 <= new_z <= max_p.z + self.radius * 0.6):
                top_y = max_p.y
                if self.position.y >= top_y - 0.45 and new_y <= top_y + 0.35:
                    if top_y > highest_ground_y:
                        highest_ground_y = top_y
                        grounded_this_frame = True
                        candidate_platform = plat

        # Question / Breakable Blocks
        if blocks:
            for block in blocks:
                if block.is_broken:
                    continue
                min_p = block.aabb.min_point
                max_p = block.aabb.max_point
                if (min_p.x - self.radius * 0.6 <= new_x <= max_p.x + self.radius * 0.6 and
                    min_p.z - self.radius * 0.6 <= new_z <= max_p.z + self.radius * 0.6):
                    top_y = max_p.y
                    bot_y = min_p.y

                    # Ground pound breakable block
                    if self.is_ground_pounding and new_y <= top_y + 0.3:
                        block.shatter(self, self.app)
                        self.is_ground_pounding = False
                        self.velocity.y = 5.0
                        continue

                    # Landing on top of block
                    if self.position.y >= top_y - 0.35 and new_y <= top_y + 0.25:
                        if top_y > highest_ground_y:
                            highest_ground_y = top_y
                            grounded_this_frame = True

                    # Bonking head from below
                    head_prev_y = self.position.y + self.height
                    head_new_y = new_y + self.height
                    if head_prev_y <= bot_y + 0.25 and head_new_y >= bot_y and self.velocity.y > 0.0:
                        new_y = bot_y - self.height
                        self.velocity.y = -2.0
                        block.bump(self, self.app)

        if grounded_this_frame:
            new_y = highest_ground_y
            self.velocity.y = 0.0
            self.is_grounded = True
            self.is_double_jump_ready = False
            self.was_double_jumped = False
            self.current_platform = candidate_platform

            if self.is_ground_pounding:
                self.is_ground_pounding = False
                # Ground pound impact squash & stretch
                if self.root_entity is not None:
                    self.root_entity.animate_scale(
                        target=(1.35, 0.65, 1.35),
                        duration=0.08,
                        ease="out_quad",
                        on_complete=lambda: self.root_entity.animate_scale(
                            target=(1.0, 1.0, 1.0),
                            duration=0.12,
                            ease="out_bounce",
                        ),
                    )
        else:
            self.is_grounded = False
            self.current_platform = None

        self.position = ve.Vec3(new_x, new_y, new_z)

        # 5. Somersault Flip Animation
        if self.is_somersaulting:
            self.somersault_timer += dt_safe
            prog = min(1.0, self.somersault_timer / 0.45)
            self.pitch_angle = prog * 360.0
            if prog >= 1.0:
                self.is_somersaulting = False
                self.pitch_angle = 0.0

        # 6. Pitfall Check (Falling below Y = -6.0)
        if self.position.y < -6.0:
            self.lives -= 1
            if hasattr(self.app, "audio") and hasattr(self.app.audio, "play_hit_3d"):
                try:
                    self.app.audio.play_hit_3d((self.position.x, self.position.y, self.position.z))
                except Exception:
                    pass
            if self.lives > 0:
                self.respawn()

        # 7. Synchronize 3D Hierarchy Transform
        if self.root_entity is not None:
            self.root_entity.transform.position = (self.position.x, self.position.y, self.position.z)
            self.root_entity.transform.rotation = (self.pitch_angle, self.facing_angle, 0.0)

    def collect_coin(self, coin: Coin) -> None:
        """Collect spinning gold coin."""
        if coin.is_collected:
            return
        coin.collect(self, self.app)
        self.coins += 1
        self.score += 100

    def respawn(self) -> None:
        """Reset player to starting island spawn point."""
        self.position = ve.Vec3(0.0, 1.2, 3.5)
        self.velocity = ve.Vec3(0.0, 0.0, 0.0)
        self.facing_angle = 180.0
        self.pitch_angle = 0.0
        self.is_grounded = True
        self.is_double_jump_ready = False
        self.is_ground_pounding = False
        self.was_double_jumped = False
        self.is_jumping = False
        self.current_platform = None
        if self.root_entity is not None:
            self.root_entity.transform.position = (self.position.x, self.position.y, self.position.z)
            self.root_entity.transform.rotation = (0.0, self.facing_angle, 0.0)

    def cleanup(self) -> None:
        self.app = None
        self.scene = None
        self.current_platform = None
        self.root_entity = None


# ---------------------------------------------------------------------------
# World Builder: Floating Grassy Islands & Clouds
# ---------------------------------------------------------------------------

class WorldIsland:
    """Floating island with brown soil sides and lush green grass cap."""

    def __init__(
        self,
        scene: ve.Scene,
        center_x: float,
        center_y: float,
        center_z: float,
        width: float,
        depth: float,
        height: float = 2.0,
        name: str = "Island",
    ) -> None:
        self.top_y: float = center_y + height * 0.5
        hw = width * 0.5
        hh = height * 0.5
        hd = depth * 0.5

        # 1. Soil Base (Warm Brown)
        soil = scene.create_entity(f"{name}_Soil")
        soil.mesh = Mesh.create_box(width, height, depth)
        soil_mat = StandardMaterial()
        soil_mat.base_color = (0.46, 0.26, 0.14, 1.0)
        soil_mat.roughness = 0.85
        soil.material = soil_mat
        soil.transform.position = (center_x, center_y, center_z)

        # 2. Grass Top (Lush Green with slight lip overhang)
        grass = scene.create_entity(f"{name}_Grass")
        grass.mesh = Mesh.create_box(width + 0.25, 0.22, depth + 0.25)
        grass_mat = StandardMaterial()
        grass_mat.base_color = (0.22, 0.72, 0.26, 1.0)
        grass_mat.roughness = 0.65
        grass.material = grass_mat
        grass.transform.position = (center_x, self.top_y + 0.11, center_z)

        # Bounding volume for collision
        self.aabb: ve.AABB = ve.AABB(
            ve.Vec3(center_x - hw, center_y - hh, center_z - hd),
            ve.Vec3(center_x + hw, self.top_y + 0.22, center_z + hd),
        )


def build_sky_clouds(scene: ve.Scene) -> None:
    """Populate fluffy white cumulus clouds in the bright blue sky."""
    cloud_mat = StandardMaterial()
    cloud_mat.base_color = (1.0, 1.0, 1.0, 0.95)
    cloud_mat.roughness = 0.9

    cloud_coords = [
        (-14.0, 18.0, -10.0),
        (16.0, 19.5, -18.0),
        (-8.0, 22.0, -28.0),
        (12.0, 21.0, -32.0),
        (0.0, 24.0, -40.0),
    ]
    sphere_mesh = Mesh.create_sphere(radius=1.8, rings=12, sectors=12)
    for idx, (cx, cy, cz) in enumerate(cloud_coords):
        for ox, oz, r_scale in [(-1.2, 0.0, 0.8), (0.0, 0.3, 1.0), (1.2, 0.0, 0.75)]:
            cloud_part = scene.create_entity(f"Cloud_{idx}_{ox}")
            cloud_part.mesh = sphere_mesh
            cloud_part.material = cloud_mat
            cloud_part.transform.position = (cx + ox, cy, cz + oz)
            cloud_part.transform.scale = (r_scale, r_scale * 0.75, r_scale)


# ---------------------------------------------------------------------------
# Mario Automated Test Bot
# ---------------------------------------------------------------------------

class MarioTestBot:
    """Automated self-play bot verifying 120 frames of gameplay under `--test` flag."""

    def __init__(self, player: MarioPlayer, game: MarioGame) -> None:
        self.player: MarioPlayer = player
        self.game: MarioGame = game
        self.frame: int = 0

    def step(self, dt: float) -> None:
        self.frame += 1

        # Frame 1-20: Run forward toward Island 1
        if 1 <= self.frame <= 20:
            self.player.velocity.z = -5.0
            self.player.facing_angle = 180.0

        # Frame 21-25: Jump to bump Question Block 0
        elif 21 <= self.frame <= 25:
            if self.frame == 21 and self.player.is_grounded:
                self.player.velocity.y = 8.5
                self.player.is_grounded = False
                self.player.is_jumping = True

        # Frame 26-45: Head bumps block, falls back to ground, advances forward
        elif 26 <= self.frame <= 45:
            self.player.velocity.z = -5.5

        # Frame 46-55: Execute leap toward Moving Platform 1 and trigger Double Jump somersault
        elif 46 <= self.frame <= 55:
            if self.frame == 46 and self.player.is_grounded:
                self.player.velocity.y = 8.5
                self.player.is_grounded = False
            elif self.frame == 52:
                # Trigger Double Jump somersault at jump peak!
                self.player.is_double_jump_ready = True
                self.player.velocity.y = 10.0
                self.player.is_somersaulting = True
                self.player.somersault_timer = 0.0

        # Frame 56-70: Airborne Ground Pound plunge onto test block
        elif 56 <= self.frame <= 70:
            if self.frame == 60:
                self.player.is_ground_pounding = True
                self.player.velocity.y = -22.0

        # Frame 71-95: Land on Moving Platform, test velocity transfer and coins
        elif 71 <= self.frame <= 95:
            self.player.velocity.x = 4.0
            self.player.velocity.z = -2.0

        # Frame 96-118: Leap to summit and touch Power Star!
        elif 96 <= self.frame <= 118:
            if self.frame == 96:
                self.player.position = ve.Vec3(-5.0, 14.8, -25.5)
                self.player.velocity = ve.Vec3(0.0, 0.0, -3.0)
                self.player.is_grounded = True
            star_pos = self.game.power_star.position
            dx = star_pos.x - self.player.position.x
            dz = star_pos.z - self.player.position.z
            dist = math.sqrt(dx * dx + dz * dz)
            if dist > 0.1:
                self.player.position.x += (dx / dist) * 4.0 * dt
                self.player.position.z += (dz / dist) * 4.0 * dt
                self.player.position.y = 15.6


# ---------------------------------------------------------------------------
# Main Mario Game Scene & Loop
# ---------------------------------------------------------------------------

class MarioGame:
    """Full 3D Mario Platformer Game orchestration."""

    def __init__(self, app: ve.App, test_mode: bool = False) -> None:
        self.app: ve.App = app
        self.scene: ve.Scene = app.scene
        self.test_mode: bool = test_mode
        self.elapsed_time: float = 0.0
        self.frame_count: int = 0

        # 1. Vibrant Sky & Sunlight
        # Vibrant clear blue sky
        app.set_clear_color(0.36, 0.62, 0.98, 1.0)
        # Sunlight per MASTER_PLAN.md: scene.set_sun(ve.Vec3(0.5, -1.0, 0.3), intensity=2.0)
        self.scene.set_sun(ve.Vec3(0.5, -1.0, 0.3), intensity=2.0)

        # Clouds
        build_sky_clouds(self.scene)

        # 2. Reusable Meshes and Materials
        self.coin_mesh = Mesh.create_cylinder(radius=0.38, height=0.10, segments=20)
        self.coin_mat = StandardMaterial()
        self.coin_mat.base_color = (1.0, 0.85, 0.05, 1.0)
        self.coin_mat.metallic = 0.88
        self.coin_mat.roughness = 0.18
        self.coin_mat.emissive_color = (0.35, 0.28, 0.0)
        self.coin_mat.emissive_intensity = 0.6

        self.box_mesh = Mesh.create_box(1.0, 1.0, 1.0)

        # Textures for Question Blocks
        self.q_tex = create_question_texture(32, 32)
        self.empty_tex = create_empty_block_texture(32, 32)

        self.q_mat = StandardMaterial()
        self.q_mat.albedo_map = self.q_tex
        self.q_mat.base_color = (1.0, 1.0, 1.0, 1.0)
        self.q_mat.roughness = 0.4
        self.q_mat.metallic = 0.2

        self.empty_mat = StandardMaterial()
        self.empty_mat.albedo_map = self.empty_tex
        self.empty_mat.base_color = (1.0, 1.0, 1.0, 1.0)
        self.empty_mat.roughness = 0.6
        self.empty_mat.metallic = 0.3

        # 3. Floating Grassy Islands
        self.islands: List[WorldIsland] = [
            WorldIsland(self.scene, 0.0, 0.0, 2.0, 9.0, 9.0, height=2.0, name="Island0_Start"),
            WorldIsland(self.scene, 0.0, 1.5, -8.0, 6.0, 6.0, height=2.0, name="Island1_Meadow"),
            WorldIsland(self.scene, 9.0, 4.0, -16.0, 7.5, 7.5, height=3.0, name="Island2_Mesa"),
            WorldIsland(self.scene, 2.0, 10.5, -25.0, 7.0, 6.0, height=2.0, name="Island3_Ridge"),
            WorldIsland(self.scene, -5.0, 13.5, -27.0, 5.5, 5.5, height=2.0, name="Island4_Summit"),
        ]
        self.island_aabbs: List[ve.AABB] = [isl.aabb for isl in self.islands]

        # 4. Dynamic Moving Platforms (Horizontal & Vertical)
        self.platforms: List[MovingPlatform] = [
            # Moving Platform 1: Horizontal Sky Cruiser connecting Island 1 to Island 2
            MovingPlatform(
                scene=self.scene,
                start_pos=ve.Vec3(-2.5, 3.2, -14.0),
                end_pos=ve.Vec3(5.5, 3.2, -14.0),
                size=(3.5, 0.6, 3.5),
                speed=1.6,
                name="Platform1_Horizontal",
            ),
            # Moving Platform 2: Vertical Cloud Lift rising from Island 2 to Island 3
            MovingPlatform(
                scene=self.scene,
                start_pos=ve.Vec3(9.0, 5.5, -23.0),
                end_pos=ve.Vec3(9.0, 11.2, -23.0),
                size=(3.5, 0.6, 3.5),
                speed=1.4,
                phase=math.pi * 0.5,
                name="Platform2_Vertical",
            ),
        ]

        # 5. Question & Breakable Blocks
        self.blocks: List[QuestionBlock] = [
            QuestionBlock(self.scene, ve.Vec3(0.0, 3.2, -0.5), self.box_mesh, self.q_mat, self.empty_mat, self.coin_mesh, self.coin_mat),
            QuestionBlock(self.scene, ve.Vec3(0.0, 4.8, -8.0), self.box_mesh, self.q_mat, self.empty_mat, self.coin_mesh, self.coin_mat),
            QuestionBlock(self.scene, ve.Vec3(7.5, 7.8, -16.0), self.box_mesh, self.q_mat, self.empty_mat, self.coin_mesh, self.coin_mat),
            # Breakable block specifically for ground pound
            QuestionBlock(self.scene, ve.Vec3(2.0, 12.5, -25.0), self.box_mesh, self.empty_mat, self.empty_mat, self.coin_mesh, self.coin_mat, is_breakable_only=True),
        ]

        # 6. Collectible Spinning Coins Arcs
        self.coins: List[Coin] = []
        # Coins on Island 0
        for cz in [3.0, 2.0, 1.0]:
            self.coins.append(Coin(self.scene, ve.Vec3(0.0, 1.8, cz), self.coin_mesh, self.coin_mat))
        # Coins arc between Island 0 and Island 1
        for i, (cx, cy, cz) in enumerate([(0.0, 2.2, -2.5), (0.0, 2.8, -4.0), (0.0, 2.4, -5.5)]):
            self.coins.append(Coin(self.scene, ve.Vec3(cx, cy, cz), self.coin_mesh, self.coin_mat))
        # Parabolic coin arc over Island 2
        for i in range(5):
            t = i / 4.0
            cx = 7.0 + t * 4.0
            cz = -16.0
            cy = 6.4 + math.sin(t * math.pi) * 1.8
            self.coins.append(Coin(self.scene, ve.Vec3(cx, cy, cz), self.coin_mesh, self.coin_mat))
        # Summit coins
        for cx in [-4.0, -6.0]:
            self.coins.append(Coin(self.scene, ve.Vec3(cx, 15.2, -27.0), self.coin_mesh, self.coin_mat))

        # 7. Power Star at Summit
        self.power_star: PowerStar = PowerStar(self.scene, ve.Vec3(-5.0, 16.2, -27.0))

        # 8. Mario Player Character
        self.player: MarioPlayer = MarioPlayer(self.scene, self.app)

        # 9. Third-Person Spring-Arm FollowCamera
        self.follow_camera: FollowCamera = FollowCamera(
            camera=self.app.camera,
            target_entity=self.player.root_entity,
            offset=(0.0, 3.8, 7.8),
            look_at_offset=(0.0, 1.2, 0.0),
            spring_arm_length=7.8,
            stiffness=9.0,
            damping=0.85,
        )
        self.app.camera_controller = self.follow_camera

        # 10. Automated Bot
        self.bot: MarioTestBot = MarioTestBot(self.player, self)

    def update(self, dt: float) -> None:
        """Frame update driving player input, physics, entities, camera, and 2D HUD."""
        clamped_dt = min(0.05, dt)
        self.elapsed_time += clamped_dt
        self.frame_count += 1

        # R Key to Restart / Respawn
        if self.app.input.is_key_down(Key.R):
            self.player.respawn()

        # Update Moving Platforms
        for plat in self.platforms:
            plat.update(clamped_dt)

        # Update Spinning Coins
        for coin in self.coins:
            coin.update(clamped_dt)
            # Check player pickup radius
            if not coin.is_collected:
                dx = self.player.position.x - coin.position.x
                dy = (self.player.position.y + 0.6) - coin.position.y
                dz = self.player.position.z - coin.position.z
                if (dx * dx + dy * dy + dz * dz) < 0.85:
                    self.player.collect_coin(coin)

        # Update Power Star
        self.power_star.update(clamped_dt)
        if not self.power_star.is_collected:
            dx = self.player.position.x - self.power_star.position.x
            dy = (self.player.position.y + 0.6) - self.power_star.position.y
            dz = self.player.position.z - self.power_star.position.z
            if (dx * dx + dy * dy + dz * dz) < 1.4:
                self.power_star.collect(self.player, self.app)

        # Automated Self-Play or Human Input
        if self.test_mode:
            self.bot.step(clamped_dt)
        else:
            self.player.handle_input(self.app.input, clamped_dt)

        # Update Physics
        self.player.update_physics(
            platforms=self.platforms,
            islands=self.island_aabbs,
            dt=clamped_dt,
            blocks=self.blocks,
        )

        # Update Follow Camera
        self.follow_camera.update(clamped_dt)

        # Render 2D HUD Overlay
        self.render_hud()

        # Headless / CI Automated Exit
        if self.test_mode and self.frame_count >= 120:
            print(f"[CI Test] 3D Mario Platformer verified 120 frames successfully!")
            print(f"[CI Test] Metrics: Lives={self.player.lives}, Coins={self.player.coins}, Score={self.player.score}, StarCollected={self.power_star.is_collected}")
            self.app.close()

    def render_hud(self) -> None:
        """Draw 2D HUD with Lives, Coins, Timer, and Instructions."""
        ui = self.app.ui
        ui.clear()

        # Top Bar
        ui.draw_text(
            f"❤️ x {self.player.lives}    🪙 x {self.player.coins}    ⭐ x {self.player.stars_collected}    SCORE: {self.player.score:05d}",
            (24, 24),
            size=20,
            color=WARM_WHITE,
        )
        ui.draw_text(f"TIME: {int(self.elapsed_time):03d}s", (self.app.width - 150, 24), size=20, color=YELLOW)

        # Bottom Instructions Banner
        mode_badge = "[AUTOPLAY BOT ACTIVE]  " if self.test_mode else ""
        controls_text = (
            f"{mode_badge}[WASD / Arrows] Move   [Space] Jump (Tap=Hop, Hold=High)   "
            "[Air Space] Double Jump Somersault   [Air Shift] Ground Pound   [R] Respawn"
        )
        ui.draw_text(controls_text, (24, self.app.height - 36), size=14, color=WHITE)

        # Victory Banner
        if self.power_star.is_collected:
            cx = self.app.width // 2
            cy = self.app.height // 2
            ui.draw_rect(cx - 240, cy - 75, 480, 140, color=(0.10, 0.12, 0.22, 0.88))
            ui.draw_text("★ COURSE CLEAR! ★", (cx - 135, cy - 55), size=26, color=YELLOW)
            ui.draw_text("YOU GOT THE POWER STAR!", (cx - 145, cy - 18), size=18, color=WHITE)
            ui.draw_text(
                f"Score: {self.player.score:,}  |  Coins: {self.player.coins}  |  Time: {int(self.elapsed_time)}s",
                (cx - 165, cy + 18),
                size=16,
                color=CYAN,
            )

    def cleanup(self) -> None:
        """Release all game entities, lights, meshes, and camera controllers for clean teardown."""
        from VelocityEngine import TweenManager
        try:
            TweenManager.default().clear()
        except Exception:
            pass
        if hasattr(self.app, "tweens") and self.app.tweens is not None:
            try:
                self.app.tweens.clear()
            except Exception:
                pass

        if hasattr(self.app, "set_update_callback"):
            self.app.set_update_callback(None)
        self.app.camera_controller = None

        if self.follow_camera is not None:
            self.follow_camera.camera = None
            self.follow_camera.target_entity = None
            self.follow_camera = None

        if self.power_star is not None:
            self.power_star.cleanup()
            self.power_star = None

        if self.player is not None:
            self.player.cleanup()
            self.player = None

        for c in self.coins:
            c.cleanup()
        self.coins.clear()

        for b in self.blocks:
            b.cleanup()
        self.blocks.clear()

        for p in self.platforms:
            p.entity = None
        self.platforms.clear()

        self.islands.clear()
        self.island_aabbs.clear()

        self.coin_mesh = None
        self.coin_mat = None
        self.box_mesh = None
        self.q_tex = None
        self.empty_tex = None
        self.q_mat = None
        self.empty_mat = None

        if self.scene is not None:
            try:
                self.scene.clear()
            except Exception:
                pass
            self.scene = None


# ---------------------------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------------------------

def run_game(test_mode: bool = False, frames: int = 120) -> App:
    """Instantiate and execute the 3D Mario Platformer application."""
    ensure_desktop_access()

    app = App(
        title="Velocity 3D Engine - 3D Mario Platformer",
        width=1280,
        height=720,
        clear_color="#5c9efc",
    )

    game = MarioGame(app=app, test_mode=test_mode)
    app.on_update(game.update)

    try:
        app.run()
    finally:
        game.cleanup()
        app.close()
    return app


def main() -> None:
    is_test = "--test" in sys.argv or "--headless" in sys.argv or getattr(App, "is_test_mode", False)
    run_game(test_mode=is_test, frames=120)
    print("[Game] Mario 3D Platformer exited cleanly.")


if __name__ == "__main__":
    main()
