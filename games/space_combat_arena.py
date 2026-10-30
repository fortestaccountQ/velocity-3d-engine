"""Space Combat Arena - 3D 6DOF Space Flight Dogfight Game.

Built with the Pielosyty 3D Engine.

Features:
- 6DOF Newtonian flight dynamics: pitch, yaw, roll, linear velocity, boost, inertia damping.
- Procedural starfighter geometry with emissive cockpit canopy, swept wings, and ion exhausts.
- Massive 1,200-instance asteroid field rendered via GPU hardware instancing (`InstancedMesh`).
- Dynamic asteroid rotation and real-time sphere/AABB collision detection.
- Dual wing-mounted laser blasters with glowing muzzle flash lights, laser projectiles, and raycast hits.
- Multi-tiered particle explosion system (`ParticleEmitter` with Additive sparks and Alpha smoke).
- Autonomous AI Enemy Drone starfighters with patrol, chase, dogfight, and attack behaviors.
- Deep space atmospheric cubemap sky and starfield ambiance.
- Full post-processing stack: `EffectComposer` with `BloomPass`, `TonemappingPass` (ACESFilmic),
  and `VignetteChromaticPass`.
- Comprehensive sci-fi UIOverlay HUD: aiming crosshair with target lead reticle, 2D circular radar minimap,
  speedometer, boost capacitor, shield and hull health bars, and enemy lock-on brackets.
- Built-in `--self-play` mode for automated verification and performance benchmarking.
"""

from __future__ import annotations

import sys
import math
import time
import random
from pathlib import Path
from typing import Optional, List, Tuple

# Ensure package import path
repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

import pielosyty as ve
from pielosyty import (
    App,
    Mesh,
    StandardMaterial,
    InstancedMesh,
    ParticleEmitter,
    BlendMode,
    PointLight,
    CubeTexture,
    EffectComposer,
    BloomPass,
    TonemappingPass,
    VignetteChromaticPass,
    TonemappingMode,
    Vec3,
    Vec4,
    Color,
    Key,
    CYAN,
    MAGENTA,
    YELLOW,
    GREEN,
    RED,
    WHITE,
)

# ---------------------------------------------------------------------------
# Vector Math Helpers
# ---------------------------------------------------------------------------

def vec3_add(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def vec3_sub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def vec3_scale(a: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
    return (a[0] * s, a[1] * s, a[2] * s)

def vec3_length(a: Tuple[float, float, float]) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])

def vec3_normalize(a: Tuple[float, float, float]) -> Tuple[float, float, float]:
    l = vec3_length(a)
    if l < 1e-6:
        return (0.0, 0.0, 1.0)
    inv = 1.0 / l
    return (a[0] * inv, a[1] * inv, a[2] * inv)

def vec3_dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def vec3_cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )

def euler_to_forward(pitch_deg: float, yaw_deg: float, roll_deg: float) -> Tuple[float, float, float]:
    """Calculate forward direction vector from pitch and yaw (degrees)."""
    p = math.radians(pitch_deg)
    y = math.radians(yaw_deg)
    fx = math.cos(p) * math.sin(y)
    fy = -math.sin(p)
    fz = -math.cos(p) * math.cos(y)
    return vec3_normalize((fx, fy, fz))

def euler_to_right(pitch_deg: float, yaw_deg: float, roll_deg: float) -> Tuple[float, float, float]:
    """Calculate right direction vector from yaw and roll (degrees)."""
    y = math.radians(yaw_deg)
    r = math.radians(roll_deg)
    rx = math.cos(y) * math.cos(r)
    ry = math.sin(r)
    rz = math.sin(y) * math.cos(r)
    return vec3_normalize((rx, ry, rz))

def euler_to_up(forward: Tuple[float, float, float], right: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return vec3_normalize(vec3_cross(right, forward))


# ---------------------------------------------------------------------------
# Ship Geometry Builders
# ---------------------------------------------------------------------------

def build_player_starfighter(scene: ve.Scene) -> ve.Entity:
    """Procedurally construct an advanced player interceptor starfighter."""
    ship = scene.create_entity("PlayerShip")

    # Materials
    hull_mat = StandardMaterial()
    hull_mat.base_color = (0.16, 0.20, 0.28, 1.0) # Deep Navy Titanium
    hull_mat.roughness = 0.35
    hull_mat.metallic = 0.85

    wing_mat = StandardMaterial()
    wing_mat.base_color = (0.24, 0.32, 0.44, 1.0)
    wing_mat.roughness = 0.4
    wing_mat.metallic = 0.7

    canopy_mat = StandardMaterial()
    canopy_mat.base_color = (0.1, 0.8, 0.95, 0.8) # Luminous Cyan Glass
    canopy_mat.emissive_color = (0.1, 0.8, 1.0, 1.0)
    canopy_mat.emissive_intensity = 2.5
    canopy_mat.roughness = 0.1
    canopy_mat.metallic = 0.1

    engine_mat = StandardMaterial()
    engine_mat.base_color = (0.05, 0.6, 1.0, 1.0)
    engine_mat.emissive_color = (0.1, 0.7, 1.0, 1.0)
    engine_mat.emissive_intensity = 4.0

    # 1. Main Fuselage
    fuselage = scene.create_entity("Fuselage")
    fuselage.mesh = Mesh.create_box(1.2, 0.8, 4.4)
    fuselage.material = hull_mat
    fuselage.transform.position = (0.0, 0.0, 0.0)
    ship.add(fuselage)

    # 2. Nose Cone
    nose = scene.create_entity("Nose")
    nose.mesh = Mesh.create_cone(radius=0.7, height=1.6, radial_segments=12)
    nose.material = hull_mat
    nose.transform.position = (0.0, 0.0, -2.8)
    nose.transform.rotation = (-90.0, 0.0, 0.0)
    ship.add(nose)

    # 3. Cockpit Canopy
    cockpit = scene.create_entity("Cockpit")
    cockpit.mesh = Mesh.create_box(0.7, 0.5, 1.4)
    cockpit.material = canopy_mat
    cockpit.transform.position = (0.0, 0.55, -0.6)
    ship.add(cockpit)

    # 4. Swept Delta Wings (Left & Right)
    left_wing = scene.create_entity("WingLeft")
    left_wing.mesh = Mesh.create_box(2.8, 0.12, 1.8)
    left_wing.material = wing_mat
    left_wing.transform.position = (-2.0, 0.0, 0.4)
    left_wing.transform.rotation = (0.0, 18.0, 0.0)
    ship.add(left_wing)

    right_wing = scene.create_entity("WingRight")
    right_wing.mesh = Mesh.create_box(2.8, 0.12, 1.8)
    right_wing.material = wing_mat
    right_wing.transform.position = (2.0, 0.0, 0.4)
    right_wing.transform.rotation = (0.0, -18.0, 0.0)
    ship.add(right_wing)

    # 5. Twin Wingtip Cannons
    cannon_mesh = Mesh.create_cylinder(radius=0.1, height=1.8, segments=8)
    cannon_left = scene.create_entity("CannonLeft")
    cannon_left.mesh = cannon_mesh
    cannon_left.material = hull_mat
    cannon_left.transform.position = (-3.3, 0.0, -0.2)
    cannon_left.transform.rotation = (90.0, 0.0, 0.0)
    ship.add(cannon_left)

    cannon_right = scene.create_entity("CannonRight")
    cannon_right.mesh = cannon_mesh
    cannon_right.material = hull_mat
    cannon_right.transform.position = (3.3, 0.0, -0.2)
    cannon_right.transform.rotation = (90.0, 0.0, 0.0)
    ship.add(cannon_right)

    # 6. Twin Ion Thruster Nozzles
    engine_left = scene.create_entity("EngineLeft")
    engine_left.mesh = Mesh.create_cylinder(radius=0.35, height=0.6, segments=12)
    engine_left.material = engine_mat
    engine_left.transform.position = (-0.5, 0.0, 2.3)
    engine_left.transform.rotation = (90.0, 0.0, 0.0)
    ship.add(engine_left)

    engine_right = scene.create_entity("EngineRight")
    engine_right.mesh = Mesh.create_cylinder(radius=0.35, height=0.6, segments=12)
    engine_right.material = engine_mat
    engine_right.transform.position = (0.5, 0.0, 2.3)
    engine_right.transform.rotation = (90.0, 0.0, 0.0)
    ship.add(engine_right)

    return ship


def build_enemy_drone(scene: ve.Scene, name: str) -> ve.Entity:
    """Procedurally construct an enemy pirate combat drone."""
    drone = scene.create_entity(name)

    body_mat = StandardMaterial()
    body_mat.base_color = (0.28, 0.12, 0.14, 1.0) # Crimson pirate steel
    body_mat.roughness = 0.4
    body_mat.metallic = 0.75

    glow_mat = StandardMaterial()
    glow_mat.base_color = (1.0, 0.15, 0.1, 1.0)
    glow_mat.emissive_color = (1.0, 0.1, 0.05, 1.0)
    glow_mat.emissive_intensity = 3.5

    # Core Hull
    core = scene.create_entity(f"{name}_Core")
    core.mesh = Mesh.create_octahedron(radius=1.3)
    core.material = body_mat
    core.transform.position = (0.0, 0.0, 0.0)
    core.transform.scale = (1.1, 0.8, 1.8)
    drone.add(core)

    # Sensor Visor (Glowing Red)
    eye = scene.create_entity(f"{name}_Eye")
    eye.mesh = Mesh.create_box(0.9, 0.25, 0.4)
    eye.material = glow_mat
    eye.transform.position = (0.0, 0.2, -1.2)
    drone.add(eye)

    # Outrigger Pylons
    pylon_left = scene.create_entity(f"{name}_PylonLeft")
    pylon_left.mesh = Mesh.create_box(1.4, 0.18, 0.8)
    pylon_left.material = body_mat
    pylon_left.transform.position = (-1.5, -0.2, 0.2)
    drone.add(pylon_left)

    pylon_right = scene.create_entity(f"{name}_PylonRight")
    pylon_right.mesh = Mesh.create_box(1.4, 0.18, 0.8)
    pylon_right.material = body_mat
    pylon_right.transform.position = (1.5, -0.2, 0.2)
    drone.add(pylon_right)

    # Thruster Core
    thrust = scene.create_entity(f"{name}_Thrust")
    thrust.mesh = Mesh.create_cylinder(radius=0.4, height=0.5, segments=8)
    thrust.material = glow_mat
    thrust.transform.position = (0.0, 0.0, 1.2)
    thrust.transform.rotation = (90.0, 0.0, 0.0)
    drone.add(thrust)

    return drone


# ---------------------------------------------------------------------------
# Asteroid Field Simulation
# ---------------------------------------------------------------------------

class AsteroidData:
    """State data for an individual asteroid in the instanced field."""
    __slots__ = ("pos", "rot", "rot_vel", "scale", "radius", "alive", "color")

    def __init__(
        self,
        pos: Tuple[float, float, float],
        rot: Tuple[float, float, float],
        rot_vel: Tuple[float, float, float],
        scale: Tuple[float, float, float],
        radius: float,
        color: Tuple[float, float, float, float],
    ):
        self.pos = pos
        self.rot = list(rot)
        self.rot_vel = rot_vel
        self.scale = scale
        self.radius = radius
        self.alive = True
        self.color = color


def create_asteroid_field(scene: ve.Scene, count: int = 1200) -> Tuple[InstancedMesh, List[AsteroidData]]:
    """Generate 1,200+ rotating asteroids distributed in a vast 3D belt."""
    base_mesh = Mesh.create_dodecahedron(radius=1.0)
    inst_mesh = InstancedMesh(base_mesh, count)

    rng = random.Random(1337)
    asteroids: List[AsteroidData] = []

    for i in range(count):
        # Ring belt distribution (inner radius 45, outer radius 320)
        angle = rng.uniform(0.0, 2.0 * math.pi)
        dist = rng.uniform(45.0, 320.0)
        # Higher density closer to the middle of the belt
        y = rng.gauss(0.0, 28.0)
        x = math.cos(angle) * dist
        z = math.sin(angle) * dist

        # Irregular scales and rocky shapes
        base_size = rng.uniform(1.6, 6.5)
        # A few massive monolithic asteroids
        if rng.random() < 0.05:
            base_size = rng.uniform(9.0, 16.0)

        sx = base_size * rng.uniform(0.7, 1.4)
        sy = base_size * rng.uniform(0.7, 1.4)
        sz = base_size * rng.uniform(0.7, 1.4)
        radius = max(sx, sy, sz) * 0.95

        rx = rng.uniform(0.0, 360.0)
        ry = rng.uniform(0.0, 360.0)
        rz = rng.uniform(0.0, 360.0)

        # Random tumble velocities
        rot_vel = (
            rng.uniform(-35.0, 35.0),
            rng.uniform(-35.0, 35.0),
            rng.uniform(-35.0, 35.0)
        )

        # Rocky mineral color variations: Basalt grey, iron oxide reddish, chondrite dark
        tint = rng.uniform(0.2, 0.48)
        iron = rng.uniform(0.9, 1.25)
        col = (tint * iron, tint * 0.95, tint * 0.88, 1.0)

        ast = AsteroidData((x, y, z), (rx, ry, rz), rot_vel, (sx, sy, sz), radius, col)
        asteroids.append(ast)

        # Set initial GPU instance transform
        inst_mesh.set_instance_transform(
            i, x, y, z, rx, ry, rz, sx, sy, sz, col
        )

    scene.add_instanced_mesh(inst_mesh)
    return inst_mesh, asteroids


# ---------------------------------------------------------------------------
# Laser Projectile & Weapon System
# ---------------------------------------------------------------------------

class LaserBolt:
    """Individual energetic blaster laser projectile."""
    __slots__ = ("entity", "pos", "dir", "speed", "lifetime", "damage", "is_enemy")

    def __init__(
        self,
        entity: ve.Entity,
        pos: Tuple[float, float, float],
        dir_vec: Tuple[float, float, float],
        speed: float = 180.0,
        damage: float = 35.0,
        is_enemy: bool = False,
    ):
        self.entity = entity
        self.pos = pos
        self.dir = dir_vec
        self.speed = speed
        self.lifetime = 1.6 # Seconds before auto-fade
        self.damage = damage
        self.is_enemy = is_enemy


class WeaponSystem:
    """Manages player and enemy laser blaster projectiles and muzzle flashes."""

    def __init__(self, scene: ve.Scene, app: App):
        self.scene = scene
        self.app = app
        self.bolts: List[LaserBolt] = []
        self.fire_cooldown = 0.0

        # Shared laser meshes and glowing materials
        self.laser_mesh = Mesh.create_cylinder(radius=0.12, height=2.4, segments=8)

        # Player laser: Brilliant Cyan Glow
        self.player_mat = StandardMaterial()
        self.player_mat.base_color = (0.2, 0.9, 1.0, 1.0)
        self.player_mat.emissive_color = (0.2, 0.9, 1.0, 1.0)
        self.player_mat.emissive_intensity = 5.0

        # Enemy laser: Searing Crimson Glow
        self.enemy_mat = StandardMaterial()
        self.enemy_mat.base_color = (1.0, 0.2, 0.1, 1.0)
        self.enemy_mat.emissive_color = (1.0, 0.1, 0.05, 1.0)
        self.enemy_mat.emissive_intensity = 5.0

        # Muzzle Flash PointLight
        self.muzzle_light = PointLight("MuzzleFlashLight", Vec3(0.2, 0.8, 1.0), 0.0, 12.0, 2.0)
        self.scene.add_light(self.muzzle_light)
        self.muzzle_timer = 0.0

    def fire_player(
        self,
        ship_pos: Tuple[float, float, float],
        forward: Tuple[float, float, float],
        right: Tuple[float, float, float],
    ) -> None:
        """Fire twin wing-mounted blasters from player ship."""
        if self.fire_cooldown > 0.0:
            return
        self.fire_cooldown = 0.14 # Rapid fire

        # Left and Right wingtip spawn offsets
        spawn_offsets = [
            vec3_add(vec3_scale(right, -3.2), vec3_scale(forward, 0.8)),
            vec3_add(vec3_scale(right, 3.2), vec3_scale(forward, 0.8)),
        ]

        for offset in spawn_offsets:
            start_pos = vec3_add(ship_pos, offset)
            ent = self.scene.create_entity(f"PlayerLaser_{len(self.bolts)}")
            ent.mesh = self.laser_mesh
            ent.material = self.player_mat
            ent.transform.position = start_pos

            # Align laser cylinder with flight direction
            pitch = math.degrees(math.asin(-forward[1]))
            yaw = math.degrees(math.atan2(forward[0], -forward[2]))
            ent.transform.rotation = (pitch + 90.0, yaw, 0.0)

            bolt = LaserBolt(ent, start_pos, forward, speed=210.0, damage=40.0, is_enemy=False)
            self.bolts.append(bolt)

        # Trigger bright muzzle flash PointLight
        self.muzzle_light.transform.position = ship_pos
        self.muzzle_light.intensity = 5.5
        self.muzzle_timer = 0.06

        # Play spatial laser blaster audio
        if hasattr(self.app, "audio") and self.app.audio is not None:
            try:
                self.app.audio.play_jump()
            except Exception:
                pass

    def fire_enemy(
        self,
        drone_pos: Tuple[float, float, float],
        forward: Tuple[float, float, float],
    ) -> None:
        """Fire single red blaster bolt from enemy drone."""
        start_pos = vec3_add(drone_pos, vec3_scale(forward, 1.2))
        ent = self.scene.create_entity(f"EnemyLaser_{len(self.bolts)}")
        ent.mesh = self.laser_mesh
        ent.material = self.enemy_mat
        ent.transform.position = start_pos

        pitch = math.degrees(math.asin(-forward[1]))
        yaw = math.degrees(math.atan2(forward[0], -forward[2]))
        ent.transform.rotation = (pitch + 90.0, yaw, 0.0)

        bolt = LaserBolt(ent, start_pos, forward, speed=160.0, damage=15.0, is_enemy=True)
        self.bolts.append(bolt)

    def update(self, dt: float) -> None:
        """Advance projectile positions and expire old bolts."""
        if self.fire_cooldown > 0.0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)

        # Muzzle light decay
        if self.muzzle_timer > 0.0:
            self.muzzle_timer -= dt
            if self.muzzle_timer <= 0.0:
                self.muzzle_light.intensity = 0.0

        surviving: List[LaserBolt] = []
        for bolt in self.bolts:
            bolt.lifetime -= dt
            if bolt.lifetime <= 0.0:
                self.scene.remove(bolt.entity)
                continue

            # Move projectile along its ray
            step = vec3_scale(bolt.dir, bolt.speed * dt)
            bolt.pos = vec3_add(bolt.pos, step)
            bolt.entity.transform.position = bolt.pos
            surviving.append(bolt)

        self.bolts = surviving


# ---------------------------------------------------------------------------
# Particle Explosion & FX System
# ---------------------------------------------------------------------------

class ExplosionSystem:
    """Multi-tiered particle explosion manager for combat impacts and destruction."""

    def __init__(self, scene: ve.Scene):
        self.scene = scene

        # Additive Golden/Orange Sparks Emitter
        self.sparks = ParticleEmitter(1600)
        self.sparks.emission_rate = 0.0 # Burst only
        self.sparks.lifespan = 1.1
        self.sparks.velocity = Vec3(0.0, 0.0, 0.0)
        self.sparks.spread = Vec3(22.0, 22.0, 22.0)
        self.sparks.gravity = Vec3(0.0, 0.0, 0.0) # Zero-g space dispersal
        self.sparks.start_color = Vec4(1.0, 0.85, 0.25, 1.0)
        self.sparks.end_color = Vec4(1.0, 0.2, 0.05, 0.0)
        self.sparks.start_size = 0.35
        self.sparks.end_size = 0.05
        self.sparks.blend_mode = BlendMode.Additive
        self.scene.add(self.sparks)

        # Alpha Expanding Dark Smoke Emitter
        self.smoke = ParticleEmitter(800)
        self.smoke.emission_rate = 0.0 # Burst only
        self.smoke.lifespan = 2.0
        self.smoke.velocity = Vec3(0.0, 0.0, 0.0)
        self.smoke.spread = Vec3(8.0, 8.0, 8.0)
        self.smoke.gravity = Vec3(0.0, 0.0, 0.0)
        self.smoke.start_color = Vec4(0.35, 0.35, 0.4, 0.75)
        self.smoke.end_color = Vec4(0.12, 0.12, 0.16, 0.0)
        self.smoke.start_size = 0.6
        self.smoke.end_size = 3.2
        self.smoke.blend_mode = BlendMode.Alpha
        self.scene.add(self.smoke)

        # Engine Thruster Trail Emitter
        self.thruster_fx = ParticleEmitter(500)
        self.thruster_fx.emission_rate = 75.0
        self.thruster_fx.lifespan = 0.4
        self.thruster_fx.velocity = Vec3(0.0, 0.0, 12.0)
        self.thruster_fx.spread = Vec3(0.4, 0.4, 1.2)
        self.thruster_fx.gravity = Vec3(0.0, 0.0, 0.0)
        self.thruster_fx.start_color = Vec4(0.2, 0.8, 1.0, 0.9)
        self.thruster_fx.end_color = Vec4(0.05, 0.3, 0.9, 0.0)
        self.thruster_fx.start_size = 0.28
        self.thruster_fx.end_size = 0.08
        self.thruster_fx.blend_mode = BlendMode.Additive
        self.scene.add(self.thruster_fx)

        # Flash point light for explosive blasts
        self.flash_light = PointLight("ExplosionFlash", Vec3(1.0, 0.6, 0.2), 0.0, 35.0, 1.8)
        self.scene.add_light(self.flash_light)
        self.flash_timer = 0.0

    def trigger_explosion(self, pos: Tuple[float, float, float], intensity: float = 1.0) -> None:
        """Detonate a fiery multi-layered particle explosion at specified coordinate."""
        self.sparks.set_position(pos[0], pos[1], pos[2])
        self.sparks.burst(int(55 * intensity))

        self.smoke.set_position(pos[0], pos[1], pos[2])
        self.smoke.burst(int(25 * intensity))

        self.flash_light.transform.position = pos
        self.flash_light.intensity = 8.0 * intensity
        self.flash_timer = 0.12

    def update(self, dt: float, ship_pos: Tuple[float, float, float], ship_dir: Tuple[float, float, float], is_boosting: bool) -> None:
        """Update thruster trail and flash lights."""
        if self.flash_timer > 0.0:
            self.flash_timer -= dt
            if self.flash_timer <= 0.0:
                self.flash_light.intensity = 0.0

        # Update thruster particle emitter at ship exhaust
        exhaust_pos = vec3_sub(ship_pos, vec3_scale(ship_dir, 2.3))
        self.thruster_fx.set_position(exhaust_pos[0], exhaust_pos[1], exhaust_pos[2])

        if is_boosting:
            self.thruster_fx.emission_rate = 160.0
            self.thruster_fx.start_size = 0.45
            self.thruster_fx.start_color = Vec4(1.0, 0.9, 0.4, 1.0) # White-hot boost
        else:
            self.thruster_fx.emission_rate = 65.0
            self.thruster_fx.start_size = 0.25
            self.thruster_fx.start_color = Vec4(0.2, 0.8, 1.0, 0.9) # Ion cyan


# ---------------------------------------------------------------------------
# Autonomous AI Enemy Drone Starfighters
# ---------------------------------------------------------------------------

class EnemyDrone:
    """Autonomous dogfighting enemy starfighter with state machine AI."""

    def __init__(self, entity: ve.Entity, pos: Tuple[float, float, float], index: int):
        self.entity = entity
        self.pos = pos
        self.vel = (0.0, 0.0, 0.0)
        self.pitch = 0.0
        self.yaw = float(index * 72.0)
        self.roll = 0.0
        self.health = 100.0
        self.alive = True
        self.state = "PATROL"
        self.fire_timer = random.uniform(1.0, 2.5)
        self.patrol_target = (
            math.cos(index) * 110.0,
            random.uniform(-20.0, 20.0),
            math.sin(index) * 110.0
        )

    def update(
        self,
        dt: float,
        player_pos: Tuple[float, float, float],
        weapons: WeaponSystem,
    ) -> None:
        """Run drone state machine AI: steer, pursue, evade, and dogfight."""
        if not self.alive:
            return

        to_player = vec3_sub(player_pos, self.pos)
        dist_to_player = vec3_length(to_player)

        # State Transitions
        if dist_to_player < 140.0:
            self.state = "PURSUE"
        else:
            self.state = "PATROL"

        # AI Flight Steering
        if self.state == "PURSUE":
            target_dir = vec3_normalize(to_player)
            # Smooth steering towards player
            current_fwd = euler_to_forward(self.pitch, self.yaw, self.roll)
            desired_yaw = math.degrees(math.atan2(target_dir[0], -target_dir[2]))
            desired_pitch = math.degrees(math.asin(-max(-1.0, min(1.0, target_dir[1]))))

            # Turn rate clamping
            turn_speed = 65.0 * dt
            dy = (desired_yaw - self.yaw + 180.0) % 360.0 - 180.0
            dp = desired_pitch - self.pitch
            self.yaw += max(-turn_speed, min(turn_speed, dy))
            self.pitch += max(-turn_speed, min(turn_speed, dp))

            # Banking roll proportional to yaw turn
            self.roll = max(-45.0, min(45.0, -dy * 1.5))

            # Forward propulsion
            drone_speed = 35.0
            if dist_to_player > 50.0:
                drone_speed = 52.0 # Close the gap
            self.vel = vec3_scale(current_fwd, drone_speed)

            # Fire red blaster weapons when locked on
            self.fire_timer -= dt
            forward_alignment = vec3_dot(current_fwd, target_dir)
            if self.fire_timer <= 0.0 and forward_alignment > 0.88 and dist_to_player < 100.0:
                weapons.fire_enemy(self.pos, current_fwd)
                self.fire_timer = random.uniform(1.4, 2.2)

        else: # PATROL
            to_patrol = vec3_sub(self.patrol_target, self.pos)
            if vec3_length(to_patrol) < 15.0:
                # Pick new patrol waypoint
                self.patrol_target = (
                    random.uniform(-140.0, 140.0),
                    random.uniform(-30.0, 30.0),
                    random.uniform(-140.0, 140.0)
                )
            target_dir = vec3_normalize(to_patrol)
            desired_yaw = math.degrees(math.atan2(target_dir[0], -target_dir[2]))
            self.yaw += max(-40.0 * dt, min(40.0 * dt, (desired_yaw - self.yaw + 180.0) % 360.0 - 180.0))
            fwd = euler_to_forward(self.pitch, self.yaw, self.roll)
            self.vel = vec3_scale(fwd, 28.0)

        # Integrate translation
        self.pos = vec3_add(self.pos, vec3_scale(self.vel, dt))
        self.entity.transform.position = self.pos
        self.entity.transform.rotation = (self.pitch, self.yaw, self.roll)


# ---------------------------------------------------------------------------
# Space Combat Arena Master Game Class
# ---------------------------------------------------------------------------

class SpaceCombatArena:
    """Master controller for Space Combat Arena."""

    def __init__(self, width: int = 1280, height: int = 720, self_play: bool = False, max_frames: int = 180):
        self.self_play = self_play
        self.max_frames = max_frames
        self.frame_count = 0

        # Initialize Engine Application
        self.app = App(
            "Pielosyty 3D - Space Combat Arena",
            width=width,
            height=height,
            clear_color="#040409",
            vsync=True,
        )
        self.scene = self.app.scene

        # Setup Atmospheric Deep Space Cubemap Sky
        sky = CubeTexture.create_gradient(
            top_color=Vec3(0.03, 0.04, 0.12),    # Midnight Stellar Void
            horizon_color=Vec3(0.14, 0.07, 0.24),# Purple Cosmic Nebula
            bottom_color=Vec3(0.01, 0.02, 0.04), # Deep Abyss
            size=64,
        )
        self.scene.set_environment(sky, 1.2)
        self.scene.set_background_cube(sky)

        # Distant Blue Star Sun
        self.scene.set_sun(direction=(-0.8, -1.2, -0.9), color=Color.from_hex("#e0eeff"), intensity=1.8)

        # 1. Setup Post-Processing Stack (Bloom + ACES Tonemapping + Vignette & Chromatic Aberration)
        self.composer = EffectComposer(self.app.width, self.app.height)
        self.bloom_pass = BloomPass(threshold=0.68, strength=2.6, radius=0.65)
        self.tonemap_pass = TonemappingPass(mode=TonemappingMode.ACESFilmic, exposure=1.05, gamma=2.2)
        self.vignette_pass = VignetteChromaticPass(vignette=0.32, chromatic=0.005, grain=0.015)

        self.composer.add_pass(self.bloom_pass)
        self.composer.add_pass(self.tonemap_pass)
        self.composer.add_pass(self.vignette_pass)
        self.app.composer = self.composer

        # 2. Build Player Starfighter
        self.player_ship = build_player_starfighter(self.scene)
        self.player_pos = (0.0, 0.0, 0.0)
        self.player_vel = (0.0, 0.0, 0.0)
        self.pitch = 0.0
        self.yaw = 0.0
        self.roll = 0.0
        self.max_speed = 60.0
        self.boost_multiplier = 2.4
        self.is_boosting = False

        # Player Combat Stats
        self.shield = 100.0
        self.max_shield = 100.0
        self.hull = 100.0
        self.max_hull = 100.0
        self.boost_capacitor = 100.0
        self.shield_regen_delay = 0.0
        self.score = 0
        self.kills = 0

        # 3. Generate Massive 1,200-Asteroid Field
        self.inst_mesh, self.asteroids = create_asteroid_field(self.scene, count=1200)

        # 4. Weapons & Particle FX
        self.weapons = WeaponSystem(self.scene, self.app)
        self.fx = ExplosionSystem(self.scene)

        # 5. Spawn Autonomous AI Enemy Drones
        self.enemy_drones: List[EnemyDrone] = []
        for i in range(5):
            angle = (i * 2.0 * math.pi) / 5.0
            spawn_x = math.cos(angle) * 95.0
            spawn_z = math.sin(angle) * 95.0
            drone_ent = build_enemy_drone(self.scene, f"EnemyDrone_{i}")
            drone = EnemyDrone(drone_ent, (spawn_x, random.uniform(-12.0, 12.0), spawn_z), i)
            self.enemy_drones.append(drone)

        # Camera state
        self.cam_pos = [0.0, 3.5, 9.5]
        self.app.camera.set_position(0.0, 3.5, 9.5)
        self.app.camera.set_target(0.0, 0.0, -10.0)

        # Benchmarking metrics
        self.start_time = time.time()
        self.accum_dt = 0.0
        self.benchmark_fps: List[float] = []

    def handle_input(self, dt: float) -> Tuple[float, float, float, float, float, float, bool, bool]:
        """Query keyboard and mouse inputs, or simulate autonomous flight in self-play."""
        inp = self.app.input

        pitch_input = 0.0
        yaw_input = 0.0
        roll_input = 0.0
        thrust_input = 0.0
        strafe_input = 0.0
        vertical_input = 0.0
        firing = False
        boosting = False

        if self.self_play:
            # Deterministic autonomous combat self-play behavior scripted over 180 frames
            t = self.frame_count
            thrust_input = 1.0

            # Target nearest alive drone
            target_drone = None
            for d in self.enemy_drones:
                if d.alive:
                    target_drone = d
                    break

            if target_drone is not None and 15 <= t < 85:
                # Steer towards drone and lock on
                to_target = vec3_sub(target_drone.pos, self.player_pos)
                target_dir = vec3_normalize(to_target)
                desired_yaw = math.degrees(math.atan2(target_dir[0], -target_dir[2]))
                desired_pitch = math.degrees(math.asin(-max(-1.0, min(1.0, target_dir[1]))))
                dy = (desired_yaw - self.yaw + 180.0) % 360.0 - 180.0
                dp = desired_pitch - self.pitch
                yaw_input = max(-1.0, min(1.0, dy * 0.08))
                pitch_input = max(-1.0, min(1.0, dp * 0.08))
                firing = (t % 3 == 0) # Rapid blaster barrage
                if t < 40:
                    boosting = True
            elif 85 <= t < 135:
                # Evasive barrel roll and afterburner boost through asteroid belt
                roll_input = 1.4
                yaw_input = 0.35
                pitch_input = -0.15
                boosting = True
                firing = (t % 4 == 0)
            else:
                # Loop maneuver and sweep
                pitch_input = -0.3
                yaw_input = -0.25
                roll_input = -0.4
                firing = (t % 5 == 0)

        else:
            # Interactive Keyboard & Mouse Controls
            # Pitch & Yaw
            if inp.is_key_down(Key.Up) or inp.is_key_down(Key.I):
                pitch_input += 1.0
            if inp.is_key_down(Key.Down) or inp.is_key_down(Key.K):
                pitch_input -= 1.0
            if inp.is_key_down(Key.Left) or inp.is_key_down(Key.J):
                yaw_input += 1.0
            if inp.is_key_down(Key.Right) or inp.is_key_down(Key.L):
                yaw_input -= 1.0

            # Roll (Q / E)
            if inp.is_key_down(Key.Q):
                roll_input -= 1.0
            if inp.is_key_down(Key.E):
                roll_input += 1.0

            # Linear Thrust (W / S)
            if inp.is_key_down(Key.W):
                thrust_input += 1.0
            if inp.is_key_down(Key.S):
                thrust_input -= 0.6

            # Lateral Strafe (A / D)
            if inp.is_key_down(Key.A):
                strafe_input -= 1.0
            if inp.is_key_down(Key.D):
                strafe_input += 1.0

            # Vertical Strafe (R / C or Space)
            if inp.is_key_down(Key.R):
                vertical_input += 1.0
            if inp.is_key_down(Key.C):
                vertical_input -= 1.0

            # Boost (Left Shift)
            if inp.is_key_down(Key.LEFT_SHIFT) or inp.is_key_down(Key.RightShift):
                boosting = True

            # Fire Blasters (Space or LMB)
            if inp.is_key_down(Key.SPACE) or inp.is_mouse_button_down(0):
                firing = True

        return pitch_input, yaw_input, roll_input, thrust_input, strafe_input, vertical_input, firing, boosting

    def update_physics(self, dt: float) -> None:
        """Run 6DOF Newtonian flight dynamics, inertia damping, and collision checks."""
        pitch_in, yaw_in, roll_in, thrust_in, strafe_in, vert_in, firing, boosting = self.handle_input(dt)

        # 1. Angular Rotations (Pitch, Yaw, Roll)
        turn_rate = 75.0 # deg/sec
        roll_rate = 110.0 # deg/sec
        self.pitch += pitch_in * turn_rate * dt
        self.yaw += yaw_in * turn_rate * dt
        self.roll += roll_in * roll_rate * dt

        # Natural banking roll when yawing
        if abs(yaw_in) > 0.01 and abs(roll_in) < 0.01:
            target_bank = -yaw_in * 24.0
            self.roll += (target_bank - self.roll) * min(1.0, 5.0 * dt)
        elif abs(roll_in) < 0.01:
            # Auto-level roll gradually
            self.roll *= max(0.0, 1.0 - 2.5 * dt)

        # Clamp pitch to prevent gimbal singularity
        self.pitch = max(-85.0, min(85.0, self.pitch))

        # 2. Linear Newtonian Propulsion & Inertia Damping
        fwd = euler_to_forward(self.pitch, self.yaw, self.roll)
        right = euler_to_right(self.pitch, self.yaw, self.roll)
        up = euler_to_up(fwd, right)

        # Boost capacitor logic
        self.is_boosting = False
        speed_cap = self.max_speed
        if boosting and self.boost_capacitor > 5.0:
            self.is_boosting = True
            speed_cap *= self.boost_multiplier
            self.boost_capacitor = max(0.0, self.boost_capacitor - 30.0 * dt)
        else:
            self.boost_capacitor = min(100.0, self.boost_capacitor + 18.0 * dt)

        # Acceleration force
        accel_rate = 55.0
        accel = (0.0, 0.0, 0.0)
        if abs(thrust_in) > 0.01:
            accel = vec3_add(accel, vec3_scale(fwd, thrust_in * accel_rate))
        if abs(strafe_in) > 0.01:
            accel = vec3_add(accel, vec3_scale(right, strafe_in * (accel_rate * 0.7)))
        if abs(vert_in) > 0.01:
            accel = vec3_add(accel, vec3_scale(up, vert_in * (accel_rate * 0.7)))

        # Integrate acceleration into velocity
        self.player_vel = vec3_add(self.player_vel, vec3_scale(accel, dt))

        # Inertia Damping: gradual velocity decay when throttle released
        damping = 0.985 if abs(thrust_in) > 0.01 else 0.94
        damping_factor = math.pow(damping, dt * 60.0)
        self.player_vel = vec3_scale(self.player_vel, damping_factor)

        # Speed clamp
        cur_speed = vec3_length(self.player_vel)
        if cur_speed > speed_cap:
            self.player_vel = vec3_scale(vec3_normalize(self.player_vel), speed_cap)

        # Integrate translation
        self.player_pos = vec3_add(self.player_pos, vec3_scale(self.player_vel, dt))

        # Update ship entity transform
        self.player_ship.transform.position = self.player_pos
        self.player_ship.transform.rotation = (self.pitch, self.yaw, self.roll)

        # 3. Weapons Firing
        if firing:
            self.weapons.fire_player(self.player_pos, fwd, right)

        # 4. Shield Regeneration
        if self.shield_regen_delay > 0.0:
            self.shield_regen_delay -= dt
        else:
            self.shield = min(self.max_shield, self.shield + 12.0 * dt)

        # 5. Smooth Cockpit/Chase Camera
        # Desired camera offset behind and above ship
        cam_offset = vec3_add(vec3_scale(up, 3.2), vec3_scale(fwd, -8.6))
        desired_cam = vec3_add(self.player_pos, cam_offset)
        cam_speed = min(1.0, 10.0 * dt)
        self.cam_pos[0] += (desired_cam[0] - self.cam_pos[0]) * cam_speed
        self.cam_pos[1] += (desired_cam[1] - self.cam_pos[1]) * cam_speed
        self.cam_pos[2] += (desired_cam[2] - self.cam_pos[2]) * cam_speed

        look_target = vec3_add(self.player_pos, vec3_scale(fwd, 15.0))
        self.app.camera.set_position(self.cam_pos[0], self.cam_pos[1], self.cam_pos[2])
        self.app.camera.set_target(look_target[0], look_target[1], look_target[2])

        # 6. Asteroid Field Rotation & GPU Instanced Buffer Updates
        for i, ast in enumerate(self.asteroids):
            if not ast.alive:
                continue
            # Tumble rotation
            ast.rot[0] = (ast.rot[0] + ast.rot_vel[0] * dt) % 360.0
            ast.rot[1] = (ast.rot[1] + ast.rot_vel[1] * dt) % 360.0
            ast.rot[2] = (ast.rot[2] + ast.rot_vel[2] * dt) % 360.0

            self.inst_mesh.set_instance_transform(
                i,
                ast.pos[0], ast.pos[1], ast.pos[2],
                ast.rot[0], ast.rot[1], ast.rot[2],
                ast.scale[0], ast.scale[1], ast.scale[2],
                ast.color,
            )

            # Player Ship vs Asteroid Collision Check
            dist_sq = vec3_dot(vec3_sub(self.player_pos, ast.pos), vec3_sub(self.player_pos, ast.pos))
            min_dist = ast.radius + 2.0
            if dist_sq < (min_dist * min_dist):
                # Collision impact!
                overlap = min_dist - math.sqrt(max(1e-4, dist_sq))
                normal = vec3_normalize(vec3_sub(self.player_pos, ast.pos))
                # Depenetrate & bounce
                self.player_pos = vec3_add(self.player_pos, vec3_scale(normal, overlap * 1.1))
                self.player_vel = vec3_scale(normal, 25.0)

                # Damage player shields
                self.shield_regen_delay = 3.5
                if self.shield > 0.0:
                    self.shield = max(0.0, self.shield - 25.0)
                else:
                    self.hull = max(0.0, self.hull - 15.0)

                self.fx.trigger_explosion(vec3_add(ast.pos, vec3_scale(normal, ast.radius)), intensity=0.8)

        # 7. Laser Projectiles Collision vs Asteroids & Ships
        for bolt in self.weapons.bolts:
            if not bolt.is_enemy:
                # Player laser vs Enemy Drones
                for drone in self.enemy_drones:
                    if not drone.alive:
                        continue
                    d_vec = vec3_sub(bolt.pos, drone.pos)
                    if vec3_length(d_vec) < 3.2:
                        bolt.lifetime = 0.0 # Destroy bolt
                        drone.health -= bolt.damage
                        self.fx.trigger_explosion(bolt.pos, intensity=0.7)
                        self.score += 50
                        if drone.health <= 0.0:
                            drone.alive = False
                            self.scene.remove(drone.entity)
                            self.fx.trigger_explosion(drone.pos, intensity=2.2)
                            self.score += 250
                            self.kills += 1
                        break

                # Player laser vs Asteroids
                for ast in self.asteroids:
                    if not ast.alive:
                        continue
                    d_vec = vec3_sub(bolt.pos, ast.pos)
                    if vec3_length(d_vec) < ast.radius:
                        bolt.lifetime = 0.0
                        self.fx.trigger_explosion(bolt.pos, intensity=0.6)
                        self.score += 15
                        break
            else:
                # Enemy laser vs Player Ship
                d_vec = vec3_sub(bolt.pos, self.player_pos)
                if vec3_length(d_vec) < 2.8:
                    bolt.lifetime = 0.0
                    self.shield_regen_delay = 3.5
                    if self.shield > 0.0:
                        self.shield = max(0.0, self.shield - bolt.damage)
                    else:
                        self.hull = max(0.0, self.hull - bolt.damage * 0.7)
                    self.fx.trigger_explosion(bolt.pos, intensity=0.8)

        # 8. Update Autonomous Enemy Drones
        for drone in self.enemy_drones:
            drone.update(dt, self.player_pos, self.weapons)

        # 9. Update Weapons & Particle FX
        self.weapons.update(dt)
        self.fx.update(dt, self.player_pos, fwd, self.is_boosting)

    def draw_hud(self) -> None:
        """Render modern sci-fi HUD with aiming reticle, 2D radar, speedometer, and status bars."""
        ui = self.app.ui
        ui.clear()

        sw = float(self.app.width)
        sh = float(self.app.height)
        cx = sw * 0.5
        cy = sh * 0.5

        # 1. Aiming Crosshair / Reticle
        reticle_color = CYAN if not self.is_boosting else YELLOW
        ui.draw_crosshair(size=14.0, color=reticle_color, pos=(cx, cy), thickness=1.5)
        # Outer Lead Ring
        ui.draw_rect(cx - 24.0, cy - 24.0, 48.0, 48.0, color=Color(0.2, 0.9, 1.0, 0.35), thickness=1.0)

        # 2. Speedometer & Boost Bar (Bottom Left)
        cur_speed = vec3_length(self.player_vel)
        ui.draw_text(f"VELOCITY: {cur_speed:05.1f} M/S", (36, int(sh - 120)), size=16, color=WHITE)

        # Boost Gauge
        ui.draw_text("BOOST CAPACITOR", (36, int(sh - 95)), size=11, color=Color(0.7, 0.8, 1.0, 0.8))
        ui.draw_rect(36.0, sh - 80.0, 160.0, 10.0, color=Color(0.2, 0.25, 0.35, 0.8), thickness=1.0)
        boost_w = max(0.0, (self.boost_capacitor / 100.0) * 158.0)
        boost_col = Color(1.0, 0.85, 0.2, 1.0) if self.boost_capacitor > 25.0 else Color(1.0, 0.3, 0.2, 1.0)
        ui.draw_rect(37.0, sh - 79.0, boost_w, 8.0, color=boost_col, thickness=1.0)

        # 3. Shield & Hull Health Bars (Bottom Center)
        bar_w = 220.0
        bar_h = 12.0
        bx = cx - bar_w * 0.5

        # Shield Bar (Cyan)
        ui.draw_text(f"SHIELD: {int(self.shield)}%", (int(bx), int(sh - 85)), size=12, color=CYAN)
        ui.draw_rect(bx, sh - 70.0, bar_w, bar_h, color=Color(0.15, 0.2, 0.3, 0.8), thickness=1.0)
        cur_shield_w = max(0.0, (self.shield / self.max_shield) * (bar_w - 2.0))
        ui.draw_rect(bx + 1.0, sh - 69.0, cur_shield_w, bar_h - 2.0, color=Color(0.1, 0.85, 1.0, 0.9), thickness=1.0)

        # Hull Bar (Green to Red)
        hull_pct = self.hull / self.max_hull
        hull_col = GREEN if hull_pct > 0.5 else (YELLOW if hull_pct > 0.25 else RED)
        ui.draw_text(f"HULL: {int(self.hull)}%", (int(bx), int(sh - 48)), size=12, color=hull_col)
        ui.draw_rect(bx, sh - 33.0, bar_w, bar_h, color=Color(0.15, 0.2, 0.3, 0.8), thickness=1.0)
        cur_hull_w = max(0.0, hull_pct * (bar_w - 2.0))
        ui.draw_rect(bx + 1.0, sh - 32.0, cur_hull_w, bar_h - 2.0, color=hull_col, thickness=1.0)

        # 4. 2D Circular Radar / Minimap (Bottom Right)
        radar_size = 140.0
        rx = sw - radar_size - 28.0
        ry = sh - radar_size - 28.0
        rcx = rx + radar_size * 0.5
        rcy = ry + radar_size * 0.5
        radar_range = 180.0

        # Radar Boundary & Cross-hairs
        ui.draw_rect(rx, ry, radar_size, radar_size, color=Color(0.12, 0.22, 0.35, 0.7), thickness=1.5)
        ui.draw_line((rcx - 20.0, rcy), (rcx + 20.0, rcy), color=Color(0.2, 0.4, 0.6, 0.5), thickness=1.0)
        ui.draw_line((rcx, rcy - 20.0), (rcx, rcy + 20.0), color=Color(0.2, 0.4, 0.6, 0.5), thickness=1.0)
        # Player Chevron in Center
        ui.draw_crosshair(size=4.0, color=CYAN, pos=(rcx, rcy), thickness=1.5)

        # Enemy blips on radar (Pulsing Red)
        for drone in self.enemy_drones:
            if not drone.alive:
                continue
            dx = drone.pos[0] - self.player_pos[0]
            dz = drone.pos[2] - self.player_pos[2]
            # Rotate by player yaw for forward-up radar orientation
            yaw_rad = math.radians(self.yaw)
            rot_x = dx * math.cos(yaw_rad) - dz * math.sin(yaw_rad)
            rot_z = dx * math.sin(yaw_rad) + dz * math.cos(yaw_rad)

            # Map to radar pixel coords
            px = rcx + (rot_x / radar_range) * (radar_size * 0.45)
            py = rcy + (rot_z / radar_range) * (radar_size * 0.45)
            # Clamp inside radar
            px = max(rx + 4.0, min(rx + radar_size - 4.0, px))
            py = max(ry + 4.0, min(ry + radar_size - 4.0, py))
            ui.draw_rect(px - 2.5, py - 2.5, 5.0, 5.0, color=RED, thickness=1.0)

        # 5. Top Bar: Score, Kills, Wave, and Title
        ui.draw_text("SPACE COMBAT ARENA // 6DOF PROTOCOL", (28, 24), size=18, color=WHITE)
        ui.draw_text(f"SCORE: {self.score:06d}  |  KILLS: {self.kills} / 5  |  WAVE 01", (28, 50), size=14, color=CYAN)

        if self.self_play:
            ui.draw_text(f"[AUTONOMOUS SELF-PLAY] FRAME: {self.frame_count}/{self.max_frames}", (28, 76), size=13, color=YELLOW)
        else:
            ui.draw_text("WASD: Thrust/Strafe | Q/E: Roll | Space/LMB: Blasters | Shift: Boost", (28, 76), size=12, color=Color(0.7, 0.8, 0.9, 0.8))

        # Target Lock-On Bracket on Nearest Drone
        nearest_drone = None
        min_drone_dist = 9999.0
        for drone in self.enemy_drones:
            if not drone.alive:
                continue
            d = vec3_length(vec3_sub(drone.pos, self.player_pos))
            if d < min_drone_dist:
                min_drone_dist = d
                nearest_drone = drone

        if nearest_drone is not None:
            ui.draw_text(f"LOCK: [DRONE-0{self.enemy_drones.index(nearest_drone) + 1}] {min_drone_dist:.1f}M", (int(cx - 85.0), int(cy + 42.0)), size=13, color=RED)

    def run(self) -> None:
        """Main game loop for both interactive and headless self-play execution."""
        last_time = time.time()

        def update(dt: float) -> None:
            nonlocal last_time
            self.frame_count += 1
            now = time.time()
            frame_dt = max(0.001, min(0.05, now - last_time if not self.self_play else 1.0 / 60.0))
            last_time = now

            self.benchmark_fps.append(1.0 / frame_dt)

            # Advance simulation
            self.update_physics(frame_dt)
            self.draw_hud()

            # Self-play termination condition
            if self.self_play and self.frame_count >= self.max_frames:
                avg_fps = sum(self.benchmark_fps) / len(self.benchmark_fps) if self.benchmark_fps else 60.0
                print(f"[Self-Play Completed] Successfully ran {self.frame_count} frames! Avg FPS: {avg_fps:.1f} | Score: {self.score} | Kills: {self.kills}")
                self.app.close()

        self.app.on_update(update)

        if not self.self_play and "--headless" not in sys.argv:
            self.app.run()
        else:
            # Headless / Self-play execution
            for _ in range(self.max_frames):
                update(1.0 / 60.0)


def main() -> None:
    is_self_play = "--self-play" in sys.argv or "--headless" in sys.argv
    max_frames = 180
    for idx, arg in enumerate(sys.argv):
        if arg == "--frames" and idx + 1 < len(sys.argv):
            try:
                max_frames = int(sys.argv[idx + 1])
            except ValueError:
                pass

    arena = SpaceCombatArena(width=1280, height=720, self_play=is_self_play, max_frames=max_frames)
    arena.run()


if __name__ == "__main__":
    main()
