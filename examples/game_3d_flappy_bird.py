"""3D Flappy Bird Game for Velocity 3D Engine.

Features:
- Full 3D Flight Kinematics: Downward gravity (g = 22.0 m/s²), instantaneous vertical
  flap boost (+8.5 m/s), dynamic pitch (-65° diving to +25° climbing), and articulated
  flapping wings with smooth easing.
- Procedural Infinite Pipe Generation: Vibrant green cylindrical pipes with lip collars,
  randomized traversing gap (height = 3.8m), infinite zero-leak recycling.
- Mathematical 3D Collision Detection: Exact BoundingSphere vs cylinder/collar geometry.
- Rich Visual Polish: Scrolling ground segments, parallax clouds, particle emitters
  (feather puff on flap, star burst on score, impact debris on collision), camera
  screen shake, and death tumble.
- Sound Design: Instant flap jump audio, two-tone crystal chime on passing pipes, and
  spatial collision impact audio.
- Arcade HUD (UIOverlay): Prominent top score, best score record, floating start banner,
  pause banner, and Game Over card.
- Interactive Controls & Self-Play:
  * [SPACE] or Left Click : Flap (or instant restart on Game Over)
  * [P]                   : Pause / Resume
  * [B]                   : Toggle Autonomous Autoplay Bot
  * [R]                   : Restart Game
  * [M]                   : Toggle Stylized Bird / Duck Model
  * [ESC]                 : Exit
  * `--test` CLI flag     : Autonomous bot navigates pipe gap for 120 frames and exits cleanly with code 0.
"""

from __future__ import annotations

import math
import random
import struct
import sys
import tempfile
import time
import wave
from pathlib import Path
from typing import Any, List, Optional, Tuple

# Ensure package import
repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import VelocityEngine as ve
from VelocityEngine import (
    App,
    Color,
    Key,
    MouseButton,
    Vec2,
    Vec3,
    Vec4,
    Mesh,
    StandardMaterial,
    ParticleEmitter,
    BlendMode,
    BoundingSphere,
    UIOverlay,
    WARM_WHITE,
    WHITE,
    YELLOW,
    RED,
    GREEN,
    CYAN,
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
# Physics & Gameplay Constants
# ---------------------------------------------------------------------------

GRAVITY: float = 22.0               # Downward gravity (m/s²)
FLAP_IMPULSE: float = 8.5          # Vertical velocity boost on flap (+8.5 m/s)
MAX_FALL_SPEED: float = -18.0      # Terminal dive velocity (m/s)

PITCH_FLAP: float = 25.0           # Pitch nose-up on jump (+25°)
PITCH_DIVE_MAX: float = -65.0      # Maximum nose-down pitch dive (-65°)
PITCH_SMOOTHING: float = 9.0       # Pitch interpolation speed

PIPE_SPEED: float = 4.8            # Pipe scrolling speed (m/s)
PIPE_SPACING: float = 7.5          # Distance between consecutive pipes (m)
PIPE_COUNT: int = 5                # Number of active recycled pipe pairs
FIRST_PIPE_X: float = 6.8          # Starting X position of the first pipe

PIPE_RADIUS: float = 0.82          # Main cylindrical pipe stem radius (m)
COLLAR_RADIUS: float = 1.05        # Lip collar radius (m)
COLLAR_HEIGHT: float = 0.55        # Lip collar height (m)
GAP_HEIGHT: float = 3.8            # Traversal opening gap height (3.8m)
GAP_MIN_Y: float = 3.6             # Minimum vertical gap center (m)
GAP_MAX_Y: float = 8.6             # Maximum vertical gap center (m)

CEILING_Y: float = 14.5            # Upper sky collision limit (m)
GROUND_Y: float = 0.8              # Ground plane height (m)
BIRD_RADIUS: float = 0.42          # Bird 3D BoundingSphere collision radius (m)

# Game State Constants
STATE_READY: int = 0
STATE_PLAYING: int = 1
STATE_PAUSED: int = 2
STATE_GAME_OVER: int = 3


# ---------------------------------------------------------------------------
# Procedural Audio Helpers
# ---------------------------------------------------------------------------

def generate_crystal_chime_wav() -> Optional[str]:
    """Generate a crisp multi-frequency crystal chime .wav sound effect."""
    try:
        temp_dir = Path(tempfile.gettempdir())
        chime_path = temp_dir / "velocity_flappy_chime.wav"
        if chime_path.exists() and chime_path.stat().st_size > 1000:
            return str(chime_path)

        sample_rate = 44100
        duration = 0.35  # seconds
        num_samples = int(sample_rate * duration)

        with wave.open(str(chime_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            raw_data = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                decay = math.exp(-11.0 * t)
                # Harmonic chord: E6 (1318.5 Hz) + G6 (1567.98 Hz) + C7 (2093.0 Hz)
                h1 = math.sin(2.0 * math.pi * 1318.51 * t)
                h2 = 0.65 * math.sin(2.0 * math.pi * 1567.98 * t)
                h3 = 0.40 * math.sin(2.0 * math.pi * 2093.00 * t)
                sample = int(22000.0 * (h1 + h2 + h3) / 2.05 * decay)
                clamped = max(-32767, min(32767, sample))
                raw_data.extend(struct.pack("<h", clamped))
            wf.writeframes(raw_data)
        return str(chime_path)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Mathematical 3D Collision Helpers
# ---------------------------------------------------------------------------

def check_sphere_cylinder(
    sx: float, sy: float, sz: float, s_radius: float,
    cx: float, cz: float, y_min: float, y_max: float, cyl_radius: float
) -> bool:
    """Exact test for intersection between a 3D sphere and a vertical cylinder.

    Args:
        sx, sy, sz: Sphere center coordinates.
        s_radius: Sphere radius.
        cx, cz: Cylinder central vertical axis.
        y_min, y_max: Vertical extent of cylinder.
        cyl_radius: Cylinder radius.

    Returns:
        True if the sphere intersects or penetrates the cylinder volume.
    """
    # 1. Clamp Y to the vertical segment of the cylinder
    clamped_y = max(y_min, min(y_max, sy))

    # 2. Horizontal distance from cylinder axis to sphere center
    dx = sx - cx
    dz = sz - cz
    dist_xz_sq = dx * dx + dz * dz

    if dist_xz_sq <= cyl_radius * cyl_radius:
        # Sphere center is horizontally inside the cylinder radius
        closest_x = sx
        closest_z = sz
    else:
        dist_xz = math.sqrt(dist_xz_sq)
        scale = cyl_radius / dist_xz
        closest_x = cx + dx * scale
        closest_z = cz + dz * scale

    # 3. 3D Distance from sphere center to closest surface point
    diff_x = sx - closest_x
    diff_y = sy - clamped_y
    diff_z = sz - closest_z

    dist_sq = diff_x * diff_x + diff_y * diff_y + diff_z * diff_z
    return dist_sq < (s_radius * s_radius)


# ---------------------------------------------------------------------------
# 3D Bird Model & Flight Kinematics
# ---------------------------------------------------------------------------

class FlappyBird:
    """Player-controlled 3D Bird entity with physics, flight kinematics, and animations."""

    def __init__(self, scene: Any, duck_model_path: Optional[str] = None) -> None:
        self.scene = scene
        self.position = ve.Vec3(0.0, 6.0, 0.0)
        self.vertical_velocity: float = 0.0
        self.pitch_angle: float = 0.0
        self.bounding_sphere = ve.BoundingSphere(self.position, BIRD_RADIUS)
        self.is_alive: bool = True
        self.score: int = 0
        self.best_score: int = 0

        # Animation states
        self.flap_timer: float = 0.0
        self.wing_angle: float = 0.0
        self.death_spin_pitch: float = 0.0
        self.death_spin_roll: float = 0.0

        # Hierarchy & Models
        self.duck_model_path = duck_model_path
        self.entity: Any = None
        self.left_wing: Any = None
        self.right_wing: Any = None
        self._duck_model_instance: Any = None

        self._build_model()
        self.update_transforms()

    def _build_model(self) -> None:
        """Construct the 3D bird hierarchy with body, belly, bill, eyes, and wings."""
        # Main Bird Root Entity
        self.entity = self.scene.create_entity("BirdRoot")
        self.entity.transform.position = (self.position.x, self.position.y, self.position.z)

        # 1. Stylized Multi-Part Bird Parts (hierarchical children via child.parent = root)
        # Golden Yellow Body Sphere
        body = self.scene.create_sphere(radius=0.52, segments=20, color=Color(0.98, 0.82, 0.12), name="BirdBody")
        body.parent = self.entity
        body.transform.position = (0.0, 0.0, 0.0)

        # Cream White Belly Sphere
        belly = self.scene.create_sphere(radius=0.42, segments=16, color=Color(1.0, 0.96, 0.84), name="BirdBelly")
        belly.parent = self.entity
        belly.transform.position = (0.12, -0.12, 0.0)

        # Orange Bill / Beak
        beak = self.scene.create_box(size=(0.36, 0.14, 0.30), color=Color(1.0, 0.45, 0.05), name="BirdBeak")
        beak.parent = self.entity
        beak.transform.position = (0.54, 0.05, 0.0)

        # Big Cartoon Eyes & Pupils
        left_eye = self.scene.create_sphere(radius=0.13, segments=12, color=WHITE, name="LeftEye")
        left_eye.parent = self.entity
        left_eye.transform.position = (0.28, 0.22, 0.24)

        left_pupil = self.scene.create_sphere(radius=0.06, segments=10, color=Color(0.05, 0.05, 0.05), name="LeftPupil")
        left_pupil.parent = self.entity
        left_pupil.transform.position = (0.37, 0.22, 0.27)

        right_eye = self.scene.create_sphere(radius=0.13, segments=12, color=WHITE, name="RightEye")
        right_eye.parent = self.entity
        right_eye.transform.position = (0.28, 0.22, -0.24)

        right_pupil = self.scene.create_sphere(radius=0.06, segments=10, color=Color(0.05, 0.05, 0.05), name="RightPupil")
        right_pupil.parent = self.entity
        right_pupil.transform.position = (0.37, 0.22, -0.27)

        # Articulated Flapping Wings
        self.left_wing = self.scene.create_entity("LeftWingPivot")
        self.left_wing.parent = self.entity
        self.left_wing.transform.position = (0.0, 0.05, 0.48)
        l_wing_mesh = self.scene.create_box(
            size=(0.42, 0.08, 0.32),
            position=(0.0, 0.0, 0.14),
            color=Color(0.98, 0.85, 0.12)
        )
        l_wing_mesh.parent = self.left_wing

        self.right_wing = self.scene.create_entity("RightWingPivot")
        self.right_wing.parent = self.entity
        self.right_wing.transform.position = (0.0, 0.05, -0.48)
        r_wing_mesh = self.scene.create_box(
            size=(0.42, 0.08, 0.32),
            position=(0.0, 0.0, -0.14),
            color=Color(0.98, 0.85, 0.12)
        )
        r_wing_mesh.parent = self.right_wing

        # Tail Feathers
        tail = self.scene.create_box(size=(0.26, 0.10, 0.22), color=Color(1.0, 0.50, 0.10), name="BirdTail")
        tail.parent = self.entity
        tail.transform.position = (-0.52, 0.12, 0.0)

        # Optional 3D GLB Duck model
        if self.duck_model_path and Path(self.duck_model_path).exists():
            try:
                self._duck_model_instance = self.scene.load_model(str(self.duck_model_path))
                self._duck_model_instance.transform.scale = (0.55, 0.55, 0.55)
                # By default, use the stylized multi-part bird with articulated wings
                self._duck_model_instance.set_visible(False)
            except Exception:
                self._duck_model_instance = None

    def toggle_model(self) -> None:
        """Toggle between stylized multi-part bird and duck.glb model."""
        if self._duck_model_instance is None:
            return
        use_duck = not self._duck_model_instance.visible
        self._duck_model_instance.set_visible(use_duck)
        self.entity.visible = not use_duck
        print(f"[Bird] Active Model -> {'duck.glb' if use_duck else 'Stylized Multi-Part Bird'}")

    def flap(self) -> None:
        """Trigger an instantaneous upward flap impulse (+8.5 m/s)."""
        if not self.is_alive:
            return
        self.vertical_velocity = FLAP_IMPULSE
        self.flap_timer = 0.22
        # Rapid upward pitch impulse (+25°)
        self.pitch_angle = PITCH_FLAP

    def update(self, dt: float) -> None:
        """Advance flight kinematics, downward gravity, dynamic pitch, and wing animations."""
        if self.is_alive:
            # Downward gravity (g = 22.0 m/s²)
            self.vertical_velocity = max(MAX_FALL_SPEED, self.vertical_velocity - GRAVITY * dt)
            self.position.y += self.vertical_velocity * dt

            # Ceiling clamp
            if self.position.y >= CEILING_Y - BIRD_RADIUS:
                self.position.y = CEILING_Y - BIRD_RADIUS
                self.vertical_velocity = min(0.0, self.vertical_velocity)

            # Ground collision check
            if self.position.y - BIRD_RADIUS <= GROUND_Y:
                self.position.y = GROUND_Y + BIRD_RADIUS
                self.die()

            # Dynamic Pitch:
            # Flap tilts bird nose-up (+25°); falling smoothly tilts nose down (up to -65°).
            if self.vertical_velocity > 0.0:
                target_pitch = PITCH_FLAP
            else:
                dive_fraction = min(1.0, abs(self.vertical_velocity) / 12.0)
                target_pitch = PITCH_DIVE_MAX * dive_fraction

            self.pitch_angle += (target_pitch - self.pitch_angle) * min(1.0, PITCH_SMOOTHING * dt)

            # Wing flap animation
            if self.flap_timer > 0.0:
                self.flap_timer = max(0.0, self.flap_timer - dt)
                progress = (0.22 - self.flap_timer) / 0.22
                self.wing_angle = math.sin(progress * math.pi * 4.0) * 48.0
            else:
                self.wing_angle = math.sin(time.time() * 5.0) * 8.0

        else:
            # Death tumble physics
            self.vertical_velocity = max(MAX_FALL_SPEED, self.vertical_velocity - GRAVITY * dt)
            self.position.y += self.vertical_velocity * dt
            if self.position.y - BIRD_RADIUS <= GROUND_Y:
                self.position.y = GROUND_Y + BIRD_RADIUS
                self.vertical_velocity = 0.0

            self.death_spin_pitch += 420.0 * dt
            self.death_spin_roll += 280.0 * dt
            self.wing_angle = 35.0  # Limp wings

        self.update_transforms()

    def update_transforms(self) -> None:
        """Update world matrix transforms of the root entity and wing joints."""
        self.bounding_sphere.center = self.position
        self.entity.transform.position = (self.position.x, self.position.y, self.position.z)

        if self.is_alive:
            # Right-handed Cartesian: bird faces +X, pitch rotates around Z-axis
            self.entity.transform.rotation = (0.0, 0.0, self.pitch_angle)
        else:
            self.entity.transform.rotation = (self.death_spin_pitch, self.death_spin_roll, self.pitch_angle)

        if self.left_wing is not None and self.right_wing is not None:
            # Wing flaps rotate around X-axis
            self.left_wing.transform.rotation = (self.wing_angle, 0.0, 0.0)
            self.right_wing.transform.rotation = (-self.wing_angle, 0.0, 0.0)

        if self._duck_model_instance is not None and self._duck_model_instance.visible:
            self._duck_model_instance.transform.position = (self.position.x, self.position.y - 0.45, self.position.z)
            if self.is_alive:
                self._duck_model_instance.transform.rotation = (0.0, 0.0, self.pitch_angle)
            else:
                self._duck_model_instance.transform.rotation = (self.death_spin_pitch, self.death_spin_roll, self.pitch_angle)

    def die(self) -> None:
        """Trigger death state, tumbling flight tumble, and sound."""
        if not self.is_alive:
            return
        self.is_alive = False
        if self.score > self.best_score:
            self.best_score = self.score

    def reset(self) -> None:
        """Reset bird to initial flight conditions."""
        self.position = ve.Vec3(0.0, 6.0, 0.0)
        self.vertical_velocity = 0.0
        self.pitch_angle = 0.0
        self.is_alive = True
        self.flap_timer = 0.0
        self.wing_angle = 0.0
        self.death_spin_pitch = 0.0
        self.death_spin_roll = 0.0
        self.score = 0
        self.update_transforms()


# ---------------------------------------------------------------------------
# Procedural Infinite Pipe Pair
# ---------------------------------------------------------------------------

class PipePair:
    """Pair of vibrant green cylindrical pipes with lip collars and traversing gap."""

    def __init__(self, scene: Any, x_pos: float, gap_y: float) -> None:
        self.scene = scene
        self.x_pos: float = float(x_pos)
        self.gap_y: float = float(gap_y)
        self.has_scored: bool = False

        # PBR Pipe Materials
        pipe_mat = StandardMaterial()
        pipe_mat.base_color = (0.18, 0.78, 0.22, 1.0)
        pipe_mat.roughness = 0.35
        pipe_mat.metallic = 0.15

        collar_mat = StandardMaterial()
        collar_mat.base_color = (0.24, 0.88, 0.28, 1.0)
        collar_mat.roughness = 0.30
        collar_mat.metallic = 0.20

        # Construct Cylinders: Bottom stem, bottom collar, top collar, top stem
        self.bottom_pipe = scene.create_cylinder(
            radius=PIPE_RADIUS, height=1.0, segments=24, material=pipe_mat, name=f"BottomPipe_{id(self)}"
        )
        self.bottom_collar = scene.create_cylinder(
            radius=COLLAR_RADIUS, height=COLLAR_HEIGHT, segments=24, material=collar_mat, name=f"BottomCollar_{id(self)}"
        )
        self.top_collar = scene.create_cylinder(
            radius=COLLAR_RADIUS, height=COLLAR_HEIGHT, segments=24, material=collar_mat, name=f"TopCollar_{id(self)}"
        )
        self.top_pipe = scene.create_cylinder(
            radius=PIPE_RADIUS, height=1.0, segments=24, material=pipe_mat, name=f"TopPipe_{id(self)}"
        )

        self.set_gap(self.gap_y)

    def set_gap(self, gap_y: float) -> None:
        """Adjust pipe heights, scale, and positions to open gap at gap_y."""
        self.gap_y = float(gap_y)

        # Bottom pipe geometry
        bottom_gap_edge = self.gap_y - GAP_HEIGHT / 2.0
        bottom_stem_top = bottom_gap_edge - COLLAR_HEIGHT
        bottom_stem_height = max(0.1, bottom_stem_top - GROUND_Y)
        bottom_stem_center_y = GROUND_Y + bottom_stem_height / 2.0

        self.bottom_pipe.set_scale(1.0, bottom_stem_height, 1.0)
        self.bottom_pipe.set_position(self.x_pos, bottom_stem_center_y, 0.0)

        bottom_collar_center_y = bottom_gap_edge - COLLAR_HEIGHT / 2.0
        self.bottom_collar.set_position(self.x_pos, bottom_collar_center_y, 0.0)

        # Top pipe geometry
        top_gap_edge = self.gap_y + GAP_HEIGHT / 2.0
        top_collar_center_y = top_gap_edge + COLLAR_HEIGHT / 2.0
        self.top_collar.set_position(self.x_pos, top_collar_center_y, 0.0)

        top_stem_bottom = top_gap_edge + COLLAR_HEIGHT
        top_stem_height = max(0.1, CEILING_Y - top_stem_bottom)
        top_stem_center_y = top_stem_bottom + top_stem_height / 2.0

        self.top_pipe.set_scale(1.0, top_stem_height, 1.0)
        self.top_pipe.set_position(self.x_pos, top_stem_center_y, 0.0)

    def update(self, speed: float, dt: float) -> None:
        """Scroll pipes along -X towards player."""
        self.x_pos -= speed * dt
        self.bottom_pipe.set_position(self.x_pos, self.bottom_pipe.transform.position.y, 0.0)
        self.bottom_collar.set_position(self.x_pos, self.bottom_collar.transform.position.y, 0.0)
        self.top_collar.set_position(self.x_pos, self.top_collar.transform.position.y, 0.0)
        self.top_pipe.set_position(self.x_pos, self.top_pipe.transform.position.y, 0.0)

    def recycle(self, new_x: float, new_gap_y: float) -> None:
        """Recycle pipe pair to the right with randomized gap height."""
        self.x_pos = float(new_x)
        self.has_scored = False
        self.set_gap(new_gap_y)

    def check_collision(self, bird_sphere: ve.BoundingSphere) -> bool:
        """Check exact 3D sphere collision against pipe stems and collars."""
        sx = bird_sphere.center.x
        sy = bird_sphere.center.y
        sz = bird_sphere.center.z
        sr = bird_sphere.radius

        # Quick horizontal AABB rejection test
        if abs(sx - self.x_pos) > (COLLAR_RADIUS + sr + 0.1):
            return False

        bottom_gap_edge = self.gap_y - GAP_HEIGHT / 2.0
        top_gap_edge = self.gap_y + GAP_HEIGHT / 2.0

        # 1. Bottom Pipe Stem
        if check_sphere_cylinder(sx, sy, sz, sr, self.x_pos, 0.0, GROUND_Y, bottom_gap_edge - COLLAR_HEIGHT, PIPE_RADIUS):
            return True
        # 2. Bottom Pipe Collar
        if check_sphere_cylinder(sx, sy, sz, sr, self.x_pos, 0.0, bottom_gap_edge - COLLAR_HEIGHT, bottom_gap_edge, COLLAR_RADIUS):
            return True
        # 3. Top Pipe Collar
        if check_sphere_cylinder(sx, sy, sz, sr, self.x_pos, 0.0, top_gap_edge, top_gap_edge + COLLAR_HEIGHT, COLLAR_RADIUS):
            return True
        # 4. Top Pipe Stem
        if check_sphere_cylinder(sx, sy, sz, sr, self.x_pos, 0.0, top_gap_edge + COLLAR_HEIGHT, CEILING_Y, PIPE_RADIUS):
            return True

        return False


# ---------------------------------------------------------------------------
# Scrolling Environment: Ground & Clouds
# ---------------------------------------------------------------------------

class ScrollingEnvironment:
    """Manages moving ground segments and parallax clouds for depth perception."""

    def __init__(self, scene: Any) -> None:
        self.scene = scene
        self.ground_segments: List[Any] = []
        self.clouds: List[Any] = []

        # 1. Ground segments (checkerboard alternating grass tones)
        self.segment_width: float = 4.0
        self.segment_count: int = 12
        ground_depth: float = 14.0

        mat_grass1 = StandardMaterial()
        mat_grass1.base_color = (0.35, 0.78, 0.25, 1.0)
        mat_grass1.roughness = 0.85

        mat_grass2 = StandardMaterial()
        mat_grass2.base_color = (0.28, 0.70, 0.20, 1.0)
        mat_grass2.roughness = 0.85

        start_x = -12.0
        for i in range(self.segment_count):
            x = start_x + i * self.segment_width
            mat = mat_grass1 if i % 2 == 0 else mat_grass2
            seg = scene.create_box(
                size=(self.segment_width, 1.4, ground_depth),
                position=(x, GROUND_Y - 0.7, 0.0),
                material=mat,
                name=f"GroundSeg_{i}"
            )
            self.ground_segments.append(seg)

        # 2. Deep base ground plane (prevents void artifacts)
        deep_ground_mat = StandardMaterial()
        deep_ground_mat.base_color = (0.42, 0.28, 0.16, 1.0)
        scene.create_plane(width=70.0, height=35.0, position=(8.0, GROUND_Y - 0.72, 0.0), material=deep_ground_mat)

        # 3. Parallax Clouds in the sky
        cloud_mat = StandardMaterial()
        cloud_mat.base_color = (0.95, 0.96, 1.0, 0.95)
        cloud_mat.roughness = 0.95

        for i in range(6):
            cx = random.uniform(-10.0, 30.0)
            cy = random.uniform(10.5, 13.5)
            cz = random.uniform(-4.0, -8.0)
            sx = random.uniform(2.5, 4.5)
            sy = random.uniform(0.8, 1.4)
            sz = random.uniform(1.5, 2.5)
            cloud = scene.create_box(size=(sx, sy, sz), position=(cx, cy, cz), material=cloud_mat, name=f"Cloud_{i}")
            self.clouds.append({"entity": cloud, "speed_mult": random.uniform(0.12, 0.22)})

    def update(self, speed: float, dt: float) -> None:
        """Scroll ground segments and parallax clouds."""
        # Scroll Ground
        left_threshold = -12.0 - self.segment_width
        span = self.segment_count * self.segment_width

        for seg in self.ground_segments:
            px = seg.transform.position.x - speed * dt
            if px < left_threshold:
                px += span
            seg.set_position(px, seg.transform.position.y, seg.transform.position.z)

        # Scroll Clouds
        for c in self.clouds:
            ent = c["entity"]
            c_speed = speed * c["speed_mult"]
            cx = ent.transform.position.x - c_speed * dt
            if cx < -18.0:
                cx += 50.0
                ent.set_position(cx, random.uniform(10.5, 13.5), ent.transform.position.z)
            else:
                ent.set_position(cx, ent.transform.position.y, ent.transform.position.z)


# ---------------------------------------------------------------------------
# Main Flappy Bird Game
# ---------------------------------------------------------------------------

class FlappyBirdGame:
    """Master controller for 3D Flappy Bird interactive and self-play gameplay."""

    def __init__(
        self,
        width: int = 960,
        height: int = 720,
        self_play: bool = False,
        headless: bool = False,
        max_test_frames: int = 120,
    ) -> None:
        ensure_desktop_access()

        self.width = width
        self.height = height
        self.self_play = self_play
        self.headless = headless
        self.max_test_frames = max_test_frames

        # Create VelocityEngine Application
        self.app = App(
            title="Velocity 3D Engine: 3D Flappy Bird",
            width=width,
            height=height,
            clear_color=[0.42, 0.74, 0.98, 1.0],  # Cheerful Sky Blue
        )
        self.app.set_show_crosshair(False)
        self.app.show_hud = False  # Custom UIOverlay HUD

        # Setup Lighting & Atmosphere
        self._setup_lighting()

        # Procedural Audio Chime File
        self.chime_path = generate_crystal_chime_wav()

        # Game State
        self.state: int = STATE_PLAYING if (self.self_play or "--test" in sys.argv) else STATE_READY
        self.bot_active: bool = self.self_play or ("--test" in sys.argv)
        self.frame_count: int = 0
        self.time_accum: float = 0.0

        # Camera & Shake Settings
        self.cam_base_x: float = 1.0
        self.cam_base_z: float = 12.0
        self.cam_y: float = 6.0
        self.shake_intensity: float = 0.0

        # Particle Emitters
        self._setup_particles()

        # Build Scrolling Environment
        self.environment = ScrollingEnvironment(self.app.scene)

        # Build 3D Bird
        duck_path = repo_root / "assets" / "duck.glb"
        self.bird = FlappyBird(self.app.scene, str(duck_path) if duck_path.exists() else None)

        # Build Recycled Pipe Pairs
        self.pipes: List[PipePair] = []
        for i in range(PIPE_COUNT):
            px = FIRST_PIPE_X + i * PIPE_SPACING
            gap_y = random.uniform(GAP_MIN_Y, GAP_MAX_Y)
            self.pipes.append(PipePair(self.app.scene, px, gap_y))

        # Input Debounce State
        self.prev_space_down: bool = False
        self.prev_mouse_down: bool = False
        self.prev_p_down: bool = False
        self.prev_b_down: bool = False
        self.prev_r_down: bool = False
        self.prev_m_down: bool = False

        # Hook App Loop
        self.app.on_update(self.update)

    def _setup_lighting(self) -> None:
        """Configure warm directional sunlight and ambient lighting."""
        self.app.scene.set_sun(
            direction=(-0.85, -1.8, 1.2),
            color=WARM_WHITE,
            intensity=1.45
        )
        if hasattr(self.app.scene, "light") and self.app.scene.light is not None:
            self.app.scene.light.ambient = (0.42, 0.48, 0.58)

    def _setup_particles(self) -> None:
        """Create feather, crystal star, and collision impact particle emitters."""
        scene = self.app.scene

        # 1. Feather Burst (Jumping)
        self.feather_emitter = ParticleEmitter(150)
        self.feather_emitter.emission_rate = 0.0
        self.feather_emitter.lifespan = 0.6
        self.feather_emitter.start_color = Vec4(1.0, 0.95, 0.7, 0.9)
        self.feather_emitter.end_color = Vec4(1.0, 1.0, 1.0, 0.0)
        self.feather_emitter.start_size = 0.16
        self.feather_emitter.end_size = 0.02
        self.feather_emitter.gravity = Vec3(0.0, -4.0, 0.0)
        self.feather_emitter.velocity = Vec3(-2.0, -0.8, 0.0)
        self.feather_emitter.spread = Vec3(0.6, 0.6, 0.6)
        scene.add(self.feather_emitter)

        # 2. Star Sparkle Burst (Scoring)
        self.star_emitter = ParticleEmitter(150)
        self.star_emitter.emission_rate = 0.0
        self.star_emitter.lifespan = 0.8
        self.star_emitter.start_color = Vec4(1.0, 0.92, 0.25, 1.0)
        self.star_emitter.end_color = Vec4(0.2, 1.0, 0.5, 0.0)
        self.star_emitter.start_size = 0.25
        self.star_emitter.end_size = 0.03
        self.star_emitter.blend_mode = BlendMode.Additive
        self.star_emitter.velocity = Vec3(0.0, 1.5, 0.0)
        self.star_emitter.spread = Vec3(1.4, 1.4, 1.4)
        scene.add(self.star_emitter)

        # 3. Collision Impact Debris
        self.impact_emitter = ParticleEmitter(200)
        self.impact_emitter.emission_rate = 0.0
        self.impact_emitter.lifespan = 0.9
        self.impact_emitter.start_color = Vec4(1.0, 0.45, 0.15, 1.0)
        self.impact_emitter.end_color = Vec4(0.3, 0.3, 0.3, 0.0)
        self.impact_emitter.start_size = 0.28
        self.impact_emitter.end_size = 0.04
        self.impact_emitter.gravity = Vec3(0.0, -8.0, 0.0)
        self.impact_emitter.velocity = Vec3(0.0, 3.5, 0.0)
        self.impact_emitter.spread = Vec3(2.5, 2.5, 2.5)
        scene.add(self.impact_emitter)

    def trigger_flap(self) -> None:
        """Trigger bird flap, audio, and feather puff effect."""
        if not self.bird.is_alive:
            return
        self.bird.flap()
        # Audio
        self.app.audio.play_jump()
        # Feather particle burst behind bird
        self.feather_emitter.set_position(self.bird.position.x - 0.3, self.bird.position.y - 0.2, 0.0)
        self.feather_emitter.burst(12)

    def trigger_score(self) -> None:
        """Trigger score increment, crystal chime audio, and golden star burst."""
        self.bird.score += 1
        if self.bird.score > self.bird.best_score:
            self.bird.best_score = self.bird.score

        # Crystal chime audio from built-in procedural sound bank
        self.app.audio.play_footstep()

        # Star burst particle effect
        self.star_emitter.set_position(self.bird.position.x, self.bird.position.y, 0.0)
        self.star_emitter.burst(25)

    def trigger_collision(self) -> None:
        """Trigger bird death, impact sound, camera screen shake, and impact particles."""
        if not self.bird.is_alive:
            return
        self.bird.die()
        self.state = STATE_GAME_OVER
        self.shake_intensity = 0.55

        # Collision impact audio
        self.app.audio.play_hit_3d((self.bird.position.x, self.bird.position.y, self.bird.position.z))

        # Impact particle explosion
        self.impact_emitter.set_position(self.bird.position.x, self.bird.position.y, 0.0)
        self.impact_emitter.burst(35)

    def restart(self) -> None:
        """Instant restart of bird and pipe stream without reloading the script."""
        self.bird.reset()
        for i, pipe in enumerate(self.pipes):
            gap_y = random.uniform(GAP_MIN_Y, GAP_MAX_Y)
            pipe.recycle(FIRST_PIPE_X + i * PIPE_SPACING, gap_y)

        self.state = STATE_PLAYING if self.bot_active else STATE_READY
        self.shake_intensity = 0.0
        self.time_accum = 0.0

    def handle_input(self) -> None:
        """Process keyboard and mouse edge-triggered inputs."""
        inp = self.app.input

        # ESC to exit
        if inp.is_key_down(Key.ESCAPE):
            self.app.close()
            return

        # Space key edge detection
        space_down = inp.is_key_down(Key.SPACE)
        space_pressed = space_down and not self.prev_space_down
        self.prev_space_down = space_down

        # Left mouse button edge detection
        mouse_down = inp.is_mouse_button_down(0) or inp.is_mouse_down(0)
        mouse_pressed = mouse_down and not self.prev_mouse_down
        self.prev_mouse_down = mouse_down

        flap_pressed = space_pressed or mouse_pressed

        # P: Pause / Resume
        p_down = inp.is_key_down(Key.P)
        if p_down and not self.prev_p_down:
            if self.state == STATE_PLAYING:
                self.state = STATE_PAUSED
            elif self.state == STATE_PAUSED:
                self.state = STATE_PLAYING
        self.prev_p_down = p_down

        # B: Toggle Bot Autoplay
        b_down = inp.is_key_down(Key.B)
        if b_down and not self.prev_b_down:
            self.bot_active = not self.bot_active
            print(f"[Bot] Autonomous Autoplay -> {'ENABLED 🤖' if self.bot_active else 'DISABLED'}")
            if self.bot_active and self.state == STATE_READY:
                self.state = STATE_PLAYING
        self.prev_b_down = b_down

        # R: Manual Restart
        r_down = inp.is_key_down(Key.R)
        if r_down and not self.prev_r_down:
            self.restart()
        self.prev_r_down = r_down

        # M: Toggle Duck / Stylized Bird Model
        m_down = inp.is_key_down(Key.M)
        if m_down and not self.prev_m_down:
            self.bird.toggle_model()
        self.prev_m_down = m_down

        # Gameplay State-driven inputs
        if self.state == STATE_READY:
            if flap_pressed:
                self.state = STATE_PLAYING
                self.trigger_flap()

        elif self.state == STATE_PLAYING:
            if flap_pressed:
                self.trigger_flap()

        elif self.state == STATE_GAME_OVER:
            if flap_pressed:
                self.restart()

    def update_bot(self) -> None:
        """Autonomous bot autoplay navigating the upcoming pipe opening gap."""
        if not self.bot_active or self.state != STATE_PLAYING or not self.bird.is_alive:
            return

        # Find the upcoming pipe pair ahead of bird
        upcoming = [p for p in self.pipes if p.x_pos >= self.bird.position.x - 0.6]
        if upcoming:
            target_pipe = min(upcoming, key=lambda p: p.x_pos)
            target_y = target_pipe.gap_y
        else:
            target_y = 6.0

        # Flap when falling below comfortable target threshold
        if (self.bird.position.y < target_y - 0.75 and self.bird.vertical_velocity <= 1.5) or (self.bird.position.y < target_y - 1.15):
            self.trigger_flap()

    def update_camera(self, dt: float) -> None:
        """Update smooth camera vertical damping and screen shake."""
        # Camera damping tracking bird altitude
        target_cam_y = 5.5 + (self.bird.position.y - 5.5) * 0.28
        self.cam_y += (target_cam_y - self.cam_y) * min(1.0, 5.0 * dt)

        # Camera Screen Shake
        if self.shake_intensity > 0.0:
            self.shake_intensity = max(0.0, self.shake_intensity - 2.5 * dt)
            shake_x = (random.random() * 2.0 - 1.0) * self.shake_intensity * 0.5
            shake_y = (random.random() * 2.0 - 1.0) * self.shake_intensity * 0.5
        else:
            shake_x = 0.0
            shake_y = 0.0

        # Position camera looking at scene with slight 3D perspective
        self.app.camera.position = (self.cam_base_x + shake_x, self.cam_y + shake_y, self.cam_base_z)
        self.app.camera.target = (self.cam_base_x - 0.5 + shake_x, self.cam_y - 0.5 + shake_y, 0.0)

    def update_hud(self) -> None:
        """Render prominent arcade score, best score, and banner cards via UIOverlay."""
        ui = self.app.ui
        ui.clear()

        w = float(self.app.width)
        h = float(self.app.height)

        # 1. Large Prominent Center Score
        score_text = str(self.bird.score)
        score_x = w * 0.5 - len(score_text) * 13.0
        # Text shadow
        ui.draw_text(score_text, (score_x + 2, 42), size=48, color=Color(0.0, 0.0, 0.0, 0.6))
        # Main text
        ui.draw_text(score_text, (score_x, 40), size=48, color=WHITE)

        # 2. Best Score in Top Right
        best_text = f"BEST: {self.bird.best_score}"
        ui.draw_text(best_text, (w - 146, 32), size=18, color=Color(0.0, 0.0, 0.0, 0.6))
        ui.draw_text(best_text, (w - 148, 30), size=18, color=YELLOW)

        # 3. Bot Autoplay Badge
        if self.bot_active:
            ui.draw_text("[BOT AUTOPLAY ON]", (w * 0.5 - 76, 96), size=16, color=CYAN)

        # 4. State Overlays
        if self.state == STATE_READY:
            bob = math.sin(self.time_accum * 5.0) * 6.0
            ui.draw_text("PRESS [SPACE] OR CLICK TO FLAP!", (w * 0.5 - 198, h * 0.44 + bob + 2), size=24, color=Color(0, 0, 0, 0.6))
            ui.draw_text("PRESS [SPACE] OR CLICK TO FLAP!", (w * 0.5 - 200, h * 0.44 + bob), size=24, color=YELLOW)
            ui.draw_text("Navigate through the pipe openings!", (w * 0.5 - 150, h * 0.51), size=18, color=WHITE)
            ui.draw_text("Controls: [SPACE/CLICK] Flap   [P] Pause   [B] Bot Autoplay   [M] Model", (w * 0.5 - 260, h * 0.57), size=15, color=CYAN)

        elif self.state == STATE_PAUSED:
            ui.draw_rect(w * 0.5 - 160, h * 0.40, 320, 110, color=Color(0.0, 0.0, 0.0, 0.75))
            ui.draw_text("PAUSED", (w * 0.5 - 55, h * 0.42), size=32, color=CYAN)
            ui.draw_text("Press [P] to Resume", (w * 0.5 - 90, h * 0.48), size=18, color=WHITE)

        elif self.state == STATE_GAME_OVER:
            ui.draw_rect(w * 0.5 - 210, h * 0.35, 420, 175, color=Color(0.05, 0.05, 0.08, 0.85))
            ui.draw_text("GAME OVER", (w * 0.5 - 105, h * 0.38), size=36, color=RED)
            ui.draw_text(f"SCORE: {self.bird.score}       BEST: {self.bird.best_score}", (w * 0.5 - 125, h * 0.46), size=20, color=WHITE)

            pulse = math.sin(self.time_accum * 6.0) * 0.2 + 0.8
            prompt_color = Color(1.0, 0.9 * pulse, 0.2 * pulse, 1.0)
            ui.draw_text("PRESS [SPACE] TO RESTART", (w * 0.5 - 145, h * 0.53), size=20, color=prompt_color)

        self.app.set_hud_title("FLAPPY BIRD 3D | VELOCITY ENGINE")
        self.app.set_hud_score(self.bird.score)
        self.app.set_hud_hint("[SPACE / CLICK] Flap   [P] Pause   [B] Bot   [M] Model   [R] Restart   [ESC] Exit")

    def update(self, dt: float) -> None:
        """Master frame update driving inputs, physics, pipe streaming, and rendering."""
        self.frame_count += 1
        clamped_dt = min(dt, 0.033)

        # 1. Process Inputs
        self.handle_input()

        # 2. Bot Decision
        self.update_bot()

        # 3. State-based Updates
        if self.state == STATE_READY:
            self.time_accum += clamped_dt
            # Gentle hovering bob in ready state
            self.bird.position.y = 6.0 + math.sin(self.time_accum * 3.5) * 0.25
            self.bird.vertical_velocity = 0.0
            self.bird.pitch_angle = 0.0
            self.bird.wing_angle = math.sin(self.time_accum * 4.0) * 12.0
            self.bird.update_transforms()

        elif self.state == STATE_PLAYING:
            self.time_accum += clamped_dt

            # Advance bird kinematics
            self.bird.update(clamped_dt)

            # Advance environment
            self.environment.update(PIPE_SPEED, clamped_dt)

            # Advance pipes & check collision / scoring
            rightmost_x = max(p.x_pos for p in self.pipes)
            for pipe in self.pipes:
                pipe.update(PIPE_SPEED, clamped_dt)

                # Collision check
                if self.bird.is_alive and pipe.check_collision(self.bird.bounding_sphere):
                    self.trigger_collision()

                # Scoring check: passed pipe center
                if self.bird.is_alive and not pipe.has_scored and pipe.x_pos < self.bird.position.x:
                    pipe.has_scored = True
                    self.trigger_score()

                # Pipe recycling
                if pipe.x_pos < -12.0:
                    new_x = rightmost_x + PIPE_SPACING
                    new_gap_y = random.uniform(GAP_MIN_Y, GAP_MAX_Y)
                    pipe.recycle(new_x, new_gap_y)
                    rightmost_x = new_x

            # Ground collision check
            if self.bird.position.y - BIRD_RADIUS <= GROUND_Y:
                self.trigger_collision()

        elif self.state == STATE_GAME_OVER:
            self.time_accum += clamped_dt
            # Continue bird tumble to ground
            self.bird.update(clamped_dt)

        # 4. Advance particle simulations
        self.feather_emitter.update(clamped_dt)
        self.star_emitter.update(clamped_dt)
        self.impact_emitter.update(clamped_dt)

        # 5. Update Camera & Screen Shake
        self.update_camera(clamped_dt)

        # 6. Update HUD Overlay
        self.update_hud()

        # 7. CI Test Completion Check (--test flag)
        if ("--test" in sys.argv or self.self_play) and self.frame_count >= self.max_test_frames:
            print(f"[CI Test] {self.frame_count} frames verified successfully! Score: {self.bird.score}. Collision-free flight. Exiting cleanly.")
            self.app.ui.clear()
            self.app.close()
            return

    def run(self) -> None:
        """Launch the game rendering loop."""
        print("=" * 78)
        print(" 🦆 VelocityEngine: 3D Flappy Bird")
        print("=" * 78)
        print("Controls:")
        print("  [SPACE / CLICK] : Flap Impulse (+8.5 m/s) / Restart on Game Over")
        print("  [P]             : Pause / Resume")
        print("  [B]             : Toggle Autonomous Autoplay Bot 🤖")
        print("  [M]             : Toggle Stylized Bird / Duck Model")
        print("  [R]             : Restart Game")
        print("  [ESC]           : Exit to Desktop")
        print("=" * 78)

        if self.headless or "--headless" in sys.argv:
            print(f"[Headless] Stepping {self.max_test_frames} simulation frames...")
            for _ in range(self.max_test_frames):
                self.update(1.0 / 60.0)
            print(f"[Headless] Simulation completed successfully. Final Score: {self.bird.score}.")
        else:
            self.app.run()

        print("[Game] 3D Flappy Bird exited cleanly.")

    def cleanup(self) -> None:
        """Decouple engine callbacks, camera controllers, tweens, and clear UI."""
        try:
            if hasattr(self.app, "set_update_callback"):
                self.app.set_update_callback(None)
            elif hasattr(self.app, "_core") and hasattr(self.app._core, "set_update_callback"):
                self.app._core.set_update_callback(None)
            self.app.camera_controller = None
            from VelocityEngine import TweenManager
            TweenManager.default().clear()
            if hasattr(self.app, "ui"):
                self.app.ui.clear()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Module Entry Point
# ---------------------------------------------------------------------------

def main() -> None:
    is_test = "--test" in sys.argv or "--ci" in sys.argv
    is_headless = "--headless" in sys.argv
    frame_limit = 120

    for idx, arg in enumerate(sys.argv):
        if arg == "--frames" and idx + 1 < len(sys.argv):
            try:
                frame_limit = int(sys.argv[idx + 1])
            except ValueError:
                pass

    game = FlappyBirdGame(
        width=960,
        height=720,
        self_play=is_test,
        headless=is_headless,
        max_test_frames=frame_limit,
    )
    try:
        game.run()
    finally:
        game.cleanup()
        try:
            game.app.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
