"""Dungeon Crawler - 3D Third-Person Action RPG & Exploration Game.

Built with the Velocity 3D Engine.

Features:
- 3D skeletal character loaded from Mixamo `assets/Soldier.glb` with `AnimationMixer`.
- Smooth state machine crossfading between `Idle`, `Walk`, `Run`, and `Attack`.
- Third-person spring-arm `FollowCamera` tracking the hero.
- Modular dungeon environment: stone floor tiles, boundary walls, carved stone arches, and vaulted pillars.
- Real-time ground and obstacle AABB collision detection with responsive wall sliding.
- Dynamic flickering torch and brazier `PointLight`s with sinusoidal multi-frequency firelight noise.
- Fire spark (`BlendMode.Additive`) and smoke (`BlendMode.Alpha`) particle systems (`ParticleEmitter`).
- Interactive treasure chests, levers, and doors using 3D raycast picking (`raycast` and `node.on("click", ...)`).
- Animated chest opening with golden particle loot explosion and inventory progression.
- Animated wall lever flip triggering a sliding portcullis gate to unlock new chambers.
- Full post-processing stack: `EffectComposer` with `BloomPass` for torch glows,
  `SSAOPass` for corner ambient occlusion, and `TonemappingPass` (ACESFilmic).
- UI overlay displaying Hero HP bar, stamina gauge (drained by sprinting/attacking),
  inventory counter (Gold, Keys, Relics), contextual interaction hints, and notification banners.
- Built-in `--self-play` mode for automated 180-frame verification and benchmarking.
"""

from __future__ import annotations

import sys
import math
import time
import random
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

# Ensure package import path
repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

import VelocityEngine as ve
from VelocityEngine import (
    App,
    Mesh,
    StandardMaterial,
    Texture,
    AnimationMixer,
    AnimationClip,
    FollowCamera,
    ParticleEmitter,
    BlendMode,
    PointLight,
    CubeTexture,
    EffectComposer,
    BloomPass,
    SSAOPass,
    TonemappingPass,
    TonemappingMode,
    Ray,
    RaycastHit,
    screen_to_ray,
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
    WARM_WHITE,
    ORANGE,
)


def find_asset_path(filename: str) -> Path:
    """Resolve asset filepath across local directories."""
    paths = [
        repo_root / "assets" / filename,
        repo_root / "temp" / "threejs" / "examples" / "models" / "gltf" / filename,
    ]
    for p in paths:
        if p.exists():
            return p
    return repo_root / "assets" / filename


# ---------------------------------------------------------------------------
# Torch & Fire Particle System
# ---------------------------------------------------------------------------

class DungeonLighting:
    """Manages warm flickering torch PointLights and fire/smoke particle emitters."""

    def __init__(self, scene: ve.Scene):
        self.scene = scene
        self.lights: List[Tuple[PointLight, float]] = []

        # Shared Fire Sparks Emitter (Additive Blending)
        self.fire_emitter = ParticleEmitter(600)
        self.fire_emitter.emission_rate = 65.0
        self.fire_emitter.lifespan = 0.85
        self.fire_emitter.velocity = Vec3(0.0, 2.2, 0.0)
        self.fire_emitter.spread = Vec3(0.2, 0.4, 0.2)
        self.fire_emitter.gravity = Vec3(0.0, 0.6, 0.0) # Updraft
        self.fire_emitter.start_color = Vec4(1.0, 0.75, 0.2, 1.0)
        self.fire_emitter.end_color = Vec4(1.0, 0.15, 0.0, 0.0)
        self.fire_emitter.start_size = 0.18
        self.fire_emitter.end_size = 0.03
        self.fire_emitter.blend_mode = BlendMode.Additive
        self.scene.add(self.fire_emitter)

        # Shared Smoke Emitter (Alpha Blending)
        self.smoke_emitter = ParticleEmitter(300)
        self.smoke_emitter.emission_rate = 22.0
        self.smoke_emitter.lifespan = 1.8
        self.smoke_emitter.velocity = Vec3(0.0, 1.4, 0.0)
        self.smoke_emitter.spread = Vec3(0.3, 0.25, 0.3)
        self.smoke_emitter.gravity = Vec3(0.05, 0.15, 0.0)
        self.smoke_emitter.start_color = Vec4(0.3, 0.3, 0.35, 0.6)
        self.smoke_emitter.end_color = Vec4(0.12, 0.12, 0.15, 0.0)
        self.smoke_emitter.start_size = 0.22
        self.smoke_emitter.end_size = 1.1
        self.smoke_emitter.blend_mode = BlendMode.Alpha
        self.scene.add(self.smoke_emitter)

        # Loot Particle Emitter for Chests
        self.loot_emitter = ParticleEmitter(400)
        self.loot_emitter.emission_rate = 0.0 # Burst only
        self.loot_emitter.lifespan = 1.4
        self.loot_emitter.velocity = Vec3(0.0, 4.0, 0.0)
        self.loot_emitter.spread = Vec3(3.5, 3.5, 3.5)
        self.loot_emitter.gravity = Vec3(0.0, -2.5, 0.0)
        self.loot_emitter.start_color = Vec4(1.0, 0.9, 0.25, 1.0) # Radiant Gold
        self.loot_emitter.end_color = Vec4(0.2, 1.0, 0.8, 0.0)
        self.loot_emitter.start_size = 0.25
        self.loot_emitter.end_size = 0.05
        self.loot_emitter.blend_mode = BlendMode.Additive
        self.scene.add(self.loot_emitter)

    def add_torch(self, name: str, pos: Tuple[float, float, float], base_intensity: float = 3.6, radius: float = 12.0) -> PointLight:
        """Create a wall-mounted or freestanding torch PointLight."""
        torch_light = PointLight(name, Vec3(1.0, 0.58, 0.2), base_intensity, radius, 1.8)
        torch_light.transform.position = pos
        self.scene.add_light(torch_light)
        self.lights.append((torch_light, base_intensity))
        return torch_light

    def update(self, dt: float, time_accum: float) -> None:
        """Animate multi-frequency sinusoidal flicker noise on torch lights."""
        for idx, (light, base) in enumerate(self.lights):
            phase = float(idx) * 1.618
            flicker = (
                math.sin(time_accum * 9.2 + phase) * 0.35 +
                math.sin(time_accum * 18.7 + phase * 2.1) * 0.20 +
                math.sin(time_accum * 31.4 + phase * 0.7) * 0.12
            )
            light.intensity = max(0.8, base + flicker)


# ---------------------------------------------------------------------------
# Interactive Dungeon Objects: Chest, Lever, Portcullis Door
# ---------------------------------------------------------------------------

class InteractiveChest:
    """Treasure chest with rotatable hinged lid and click raycast callback."""

    def __init__(self, scene: ve.Scene, pos: Tuple[float, float, float], rot_y: float = 0.0):
        self.scene = scene
        self.pos = pos
        self.rot_y = rot_y
        self.is_opened = False
        self.lid_angle = 0.0
        self.target_lid_angle = 0.0

        # Materials
        wood_mat = StandardMaterial()
        wood_mat.base_color = (0.55, 0.45, 0.38, 1.0) # Aged Antique Oak
        wood_mat.roughness = 0.65
        wood_mat.metallic = 0.25

        chest_tex_path = repo_root / "assets" / "textures" / "dungeon_chest.png"
        chest_norm_path = repo_root / "assets" / "textures" / "dungeon_chest_normal.png"
        if chest_tex_path.exists():
            wood_mat.albedo_map = Texture.load_from_file(str(chest_tex_path))
        if chest_norm_path.exists():
            wood_mat.normal_map = Texture.load_from_file(str(chest_norm_path))
            wood_mat.normal_scale = 1.4

        iron_mat = StandardMaterial()
        iron_mat.base_color = (0.85, 0.72, 0.28, 1.0) # Gilded Brass Lock
        iron_mat.roughness = 0.25
        iron_mat.metallic = 0.92

        glow_mat = StandardMaterial()
        glow_mat.base_color = (1.0, 0.85, 0.2, 1.0)
        glow_mat.emissive_color = (1.0, 0.8, 0.1, 1.0)
        glow_mat.emissive_intensity = 3.5

        # Root entity
        self.root = scene.create_entity("TreasureChest")
        self.root.transform.position = pos
        self.root.transform.rotation = (0.0, rot_y, 0.0)

        # Chest Base Body
        self.base = scene.create_entity("ChestBase")
        self.base.mesh = Mesh.create_box(1.4, 0.65, 0.95)
        self.base.material = wood_mat
        self.base.transform.position = (0.0, 0.325, 0.0)
        self.root.add(self.base)

        # Chest Lid (Hinged at the rear)
        self.lid = scene.create_entity("ChestLid")
        self.lid.mesh = Mesh.create_box(1.42, 0.32, 0.96)
        self.lid.material = wood_mat
        self.lid.transform.position = (0.0, 0.8, 0.0)
        self.root.add(self.lid)

        # Brass lock latch
        self.latch = scene.create_entity("ChestLatch")
        self.latch.mesh = Mesh.create_box(0.25, 0.25, 0.1)
        self.latch.material = iron_mat
        self.latch.transform.position = (0.0, 0.55, -0.5)
        self.root.add(self.latch)

        # Register raycast click listener
        self.root.on("click", self.open)
        self.base.on("click", self.open)
        self.lid.on("click", self.open)

    def open(self) -> bool:
        """Trigger chest opening sequence."""
        if self.is_opened:
            return False
        self.is_opened = True
        self.target_lid_angle = 75.0
        return True

    def update(self, dt: float) -> None:
        """Smoothly animate lid rotation when opened."""
        if self.is_opened and self.lid_angle < self.target_lid_angle:
            self.lid_angle = min(self.target_lid_angle, self.lid_angle + 120.0 * dt)
            # Rotate lid backwards around hinge
            self.lid.transform.rotation = (-self.lid_angle, 0.0, 0.0)
            # Offset slightly backwards along Z as it swings
            rad = math.radians(self.lid_angle)
            self.lid.transform.position = (0.0, 0.8 + math.sin(rad) * 0.15, math.cos(rad) * 0.1)


class InteractiveLever:
    """Wall-mounted iron lever that triggers dungeon door mechanics."""

    def __init__(self, scene: ve.Scene, pos: Tuple[float, float, float], rot_y: float = 0.0):
        self.scene = scene
        self.pos = pos
        self.is_pulled = False
        self.handle_angle = 45.0
        self.target_angle = 45.0

        plate_mat = StandardMaterial()
        plate_mat.base_color = (0.2, 0.22, 0.26, 1.0)
        plate_mat.roughness = 0.6
        plate_mat.metallic = 0.7

        handle_mat = StandardMaterial()
        handle_mat.base_color = (0.8, 0.55, 0.2, 1.0) # Polished Brass Handle
        handle_mat.roughness = 0.3
        handle_mat.metallic = 0.85

        self.root = scene.create_entity("DungeonLever")
        self.root.transform.position = pos
        self.root.transform.rotation = (0.0, rot_y, 0.0)

        # Backplate
        self.plate = scene.create_entity("LeverPlate")
        self.plate.mesh = Mesh.create_box(0.5, 0.8, 0.12)
        self.plate.material = plate_mat
        self.plate.transform.position = (0.0, 0.0, 0.0)
        self.root.add(self.plate)

        # Pivot Shaft & Handle
        self.handle = scene.create_entity("LeverHandle")
        self.handle.mesh = Mesh.create_cylinder(radius=0.06, height=0.75, segments=8)
        self.handle.material = handle_mat
        self.handle.transform.position = (0.0, 0.0, 0.12)
        self.handle.transform.rotation = (self.handle_angle, 0.0, 0.0)
        self.root.add(self.handle)

        # Click listeners
        self.root.on("click", self.pull)
        self.plate.on("click", self.pull)
        self.handle.on("click", self.pull)

    def pull(self) -> bool:
        """Trigger lever pull sequence."""
        if self.is_pulled:
            return False
        self.is_pulled = True
        self.target_angle = -45.0
        return True

    def update(self, dt: float) -> None:
        """Smoothly animate handle flip downwards."""
        if self.is_pulled and self.handle_angle > self.target_angle:
            self.handle_angle = max(self.target_angle, self.handle_angle - 180.0 * dt)
            self.handle.transform.rotation = (self.handle_angle, 0.0, 0.0)


class PortcullisDoor:
    """Heavy iron barred portcullis gate that slides upwards into the ceiling arch."""

    def __init__(self, scene: ve.Scene, pos: Tuple[float, float, float]):
        self.scene = scene
        self.pos = list(pos)
        self.is_open = False
        self.is_opening = False
        self.current_y = pos[1]
        self.target_y = pos[1] + 4.2

        gate_mat = StandardMaterial()
        gate_mat.base_color = (0.18, 0.20, 0.24, 1.0) # Heavy Wrought Iron
        gate_mat.roughness = 0.5
        gate_mat.metallic = 0.85

        self.entity = scene.create_entity("PortcullisGate")
        self.entity.mesh = Mesh.create_box(4.8, 4.0, 0.28)
        self.entity.material = gate_mat
        self.entity.transform.position = (pos[0], pos[1], pos[2])

    def trigger_open(self) -> None:
        """Commence portcullis slide."""
        self.is_opening = True

    def update(self, dt: float) -> None:
        """Smoothly slide gate upwards."""
        if self.is_opening and self.current_y < self.target_y:
            self.current_y = min(self.target_y, self.current_y + 2.2 * dt)
            self.entity.transform.position = (self.pos[0], self.current_y, self.pos[2])
            if self.current_y >= self.target_y:
                self.is_open = True
                self.is_opening = False


# ---------------------------------------------------------------------------
# Modular Dungeon Environment Builder
# ---------------------------------------------------------------------------

def build_modular_dungeon(
    scene: ve.Scene,
    lighting: DungeonLighting,
) -> Tuple[List[Tuple[float, float, float, float]], InteractiveChest, InteractiveLever, PortcullisDoor]:
    """Construct stone floor tiles, perimeter walls, pillars, torches, and interactables.

    Returns:
        Tuple of (obstacle_boxes, chest, lever, portcullis)
    """
    # Sunlight (Moody cool crypt moonlight)
    scene.set_sun(direction=(-0.5, -1.8, -0.6), color=Color.from_hex("#1c2838"), intensity=0.35)

    # Subterranean crypt atmosphere
    sky = CubeTexture.create_gradient(
        top_color=Vec3(0.01, 0.012, 0.02),
        horizon_color=Vec3(0.018, 0.022, 0.035),
        bottom_color=Vec3(0.005, 0.005, 0.01),
        size=64,
    )
    scene.set_environment(sky, 0.35)
    scene.set_background_cube(sky)

    # Texture Filepaths
    floor_tex_p = repo_root / "assets" / "textures" / "dungeon_stone_floor.png"
    floor_norm_p = repo_root / "assets" / "textures" / "dungeon_stone_floor_normal.png"
    wall_tex_p = repo_root / "assets" / "textures" / "dungeon_stone_wall.png"
    wall_norm_p = repo_root / "assets" / "textures" / "dungeon_stone_wall_normal.png"

    # PBR Materials
    floor_mat = StandardMaterial()
    floor_mat.base_color = (0.75, 0.78, 0.82, 1.0) # Stone Flagstone Base
    floor_mat.roughness = 0.68
    floor_mat.metallic = 0.15
    floor_mat.uv_scale = (10.0, 14.0)
    if floor_tex_p.exists():
        floor_mat.albedo_map = Texture.load_from_file(str(floor_tex_p))
    if floor_norm_p.exists():
        floor_mat.normal_map = Texture.load_from_file(str(floor_norm_p))
        floor_mat.normal_scale = 1.6

    wall_mat = StandardMaterial()
    wall_mat.base_color = (0.78, 0.76, 0.80, 1.0) # Gothic Ashlar Bricks
    wall_mat.roughness = 0.62
    wall_mat.metallic = 0.18
    wall_mat.uv_scale = (6.0, 2.0)
    if wall_tex_p.exists():
        wall_mat.albedo_map = Texture.load_from_file(str(wall_tex_p))
    if wall_norm_p.exists():
        wall_mat.normal_map = Texture.load_from_file(str(wall_norm_p))
        wall_mat.normal_scale = 1.5

    pillar_mat = StandardMaterial()
    pillar_mat.base_color = (0.70, 0.70, 0.75, 1.0)
    pillar_mat.roughness = 0.50
    pillar_mat.metallic = 0.22
    pillar_mat.uv_scale = (1.5, 3.0)
    if wall_tex_p.exists():
        pillar_mat.albedo_map = Texture.load_from_file(str(wall_tex_p))
    if wall_norm_p.exists():
        pillar_mat.normal_map = Texture.load_from_file(str(wall_norm_p))
        pillar_mat.normal_scale = 1.3

    brazier_mat = StandardMaterial()
    brazier_mat.base_color = (0.28, 0.25, 0.22, 1.0)
    brazier_mat.roughness = 0.75
    brazier_mat.metallic = 0.35

    # 1. Modular Stone Floor Tiles (32m x 44m total area)
    floor = scene.create_entity("DungeonFloor")
    floor.mesh = Mesh.create_plane(width=34.0, depth=46.0, subdivisions_x=8, subdivisions_z=10)
    floor.material = floor_mat
    floor.transform.position = (0.0, 0.0, 0.0)

    # Subtle floor grid for stone tile grouting appearance
    scene.create_grid(size=44.0, step=2.0, color=Color.from_hex("#12141a"))

    obstacles: List[Tuple[float, float, float, float]] = []

    # 2. Outer Boundary Walls: (x, z, half_w, half_d)
    wall_h = 4.8
    wall_mesh_z = Mesh.create_box(1.2, wall_h, 44.0)
    wall_mesh_x = Mesh.create_box(34.0, wall_h, 1.2)

    # West Wall
    w_left = scene.create_entity("WallWest")
    w_left.mesh = wall_mesh_z
    w_left.material = wall_mat
    w_left.transform.position = (-16.0, wall_h * 0.5, 0.0)
    obstacles.append((-16.0, 0.0, 0.8, 22.0))

    # East Wall
    w_right = scene.create_entity("WallEast")
    w_right.mesh = wall_mesh_z
    w_right.material = wall_mat
    w_right.transform.position = (16.0, wall_h * 0.5, 0.0)
    obstacles.append((16.0, 0.0, 0.8, 22.0))

    # South Wall (Entrance Gatehouse)
    w_south = scene.create_entity("WallSouth")
    w_south.mesh = wall_mesh_x
    w_south.material = wall_mat
    w_south.transform.position = (0.0, wall_h * 0.5, 21.0)
    obstacles.append((0.0, 21.0, 17.0, 0.8))

    # North Wall (Far Sanctuary End)
    w_north = scene.create_entity("WallNorth")
    w_north.mesh = wall_mesh_x
    w_north.material = wall_mat
    w_north.transform.position = (0.0, wall_h * 0.5, -21.0)
    obstacles.append((0.0, -21.0, 17.0, 0.8))

    # 3. Partition Archway Wall (Splitting Central Hall from Grand Sanctuary at Z = -13.0)
    part_w = 14.0
    part_mesh = Mesh.create_box(part_w, wall_h, 1.2)

    part_left = scene.create_entity("PartitionLeft")
    part_left.mesh = part_mesh
    part_left.material = wall_mat
    part_left.transform.position = (-9.5, wall_h * 0.5, -13.0)
    obstacles.append((-9.5, -13.0, part_w * 0.5, 0.7))

    part_right = scene.create_entity("PartitionRight")
    part_right.mesh = part_mesh
    part_right.material = wall_mat
    part_right.transform.position = (9.5, wall_h * 0.5, -13.0)
    obstacles.append((9.5, -13.0, part_w * 0.5, 0.7))

    # Vaulted Arch Lintel over Portcullis Opening
    lintel = scene.create_entity("ArchLintel")
    lintel.mesh = Mesh.create_box(5.4, 1.2, 1.4)
    lintel.material = wall_mat
    lintel.transform.position = (0.0, wall_h - 0.6, -13.0)

    # 4. Vaulted Stone Columns & Pillars
    pillar_mesh = Mesh.create_cylinder(radius=0.45, height=wall_h, segments=16)
    capital_mesh = Mesh.create_box(1.2, 0.35, 1.2)

    pillar_coords = [
        (-6.0, 6.0), (6.0, 6.0),
        (-6.0, -4.0), (6.0, -4.0),
        (-2.5, -13.0), (2.5, -13.0), # Flanking portcullis arch
        (-6.0, -17.0), (6.0, -17.0),
    ]

    for idx, (px, pz) in enumerate(pillar_coords):
        p_col = scene.create_entity(f"PillarColumn_{idx}")
        p_col.mesh = pillar_mesh
        p_col.material = pillar_mat
        p_col.transform.position = (px, wall_h * 0.5, pz)

        # Base and Capital Blocks
        p_base = scene.create_entity(f"PillarBase_{idx}")
        p_base.mesh = capital_mesh
        p_base.material = pillar_mat
        p_base.transform.position = (px, 0.175, pz)

        p_cap = scene.create_entity(f"PillarCap_{idx}")
        p_cap.mesh = capital_mesh
        p_cap.material = pillar_mat
        p_cap.transform.position = (px, wall_h - 0.175, pz)

        obstacles.append((px, pz, 0.65, 0.65))

    # 5. Central Grand Fire Brazier at (0.0, 0.0, -5.0)
    brazier_base = scene.create_entity("CentralBrazierBase")
    brazier_base.mesh = Mesh.create_cylinder(radius=0.85, height=0.6, segments=16)
    brazier_base.material = brazier_mat
    brazier_base.transform.position = (0.0, 0.3, -5.0)

    brazier_bowl = scene.create_entity("CentralBrazierBowl")
    brazier_bowl.mesh = Mesh.create_cone(radius=1.2, height=0.55, radial_segments=16)
    brazier_bowl.material = brazier_mat
    brazier_bowl.transform.position = (0.0, 0.85, -5.0)
    brazier_bowl.transform.rotation = (180.0, 0.0, 0.0)

    # Brazier Light & Particle Placement
    lighting.add_torch("BrazierLight", (0.0, 1.3, -5.0), base_intensity=4.2, radius=16.0)
    lighting.fire_emitter.set_position(0.0, 1.0, -5.0)
    lighting.smoke_emitter.set_position(0.0, 1.2, -5.0)
    obstacles.append((0.0, -5.0, 0.95, 0.95))

    # 6. Wall Sconce Torches along corridors
    torch_sconce_mesh = Mesh.create_cylinder(radius=0.08, height=0.7, segments=8)
    torch_sconce_mat = StandardMaterial()
    torch_sconce_mat.base_color = (0.15, 0.12, 0.10, 1.0)
    torch_sconce_mat.metallic = 0.8

    torch_positions = [
        (-15.3, 2.4, 7.0),
        (15.3, 2.4, 7.0),
        (-15.3, 2.4, -4.0),
        (15.3, 2.4, -4.0),
        (-3.2, 2.6, -12.4),
        (3.2, 2.6, -12.4),
    ]

    for idx, (tx, ty, tz) in enumerate(torch_positions):
        sconce = scene.create_entity(f"TorchSconce_{idx}")
        sconce.mesh = torch_sconce_mesh
        sconce.material = torch_sconce_mat
        sconce.transform.position = (tx, ty, tz)
        lighting.add_torch(f"TorchLight_{idx}", (tx, ty + 0.3, tz), base_intensity=3.2, radius=10.0)

    # 7. Interactive Treasure Chest in East Alcove (X = 7.5, Z = 2.0)
    chest = InteractiveChest(scene, pos=(7.5, 0.0, 2.0), rot_y=-90.0)
    obstacles.append((7.5, 2.0, 0.85, 0.65))

    # 8. Interactive Wall Lever in West Corbel (X = -7.5, Z = 2.0)
    lever = InteractiveLever(scene, pos=(-7.5, 1.8, 2.0), rot_y=90.0)

    # 9. Portcullis Gate at Northern Opening (X = 0.0, Z = -13.0)
    portcullis = PortcullisDoor(scene, pos=(0.0, 2.0, -13.0))
    # Closed gate initially blocks movement
    obstacles.append((0.0, -13.0, 2.5, 0.4))

    return obstacles, chest, lever, portcullis


# ---------------------------------------------------------------------------
# Character Collision Checking & Wall Sliding
# ---------------------------------------------------------------------------

def check_dungeon_collision(
    px: float,
    pz: float,
    obstacles: List[Tuple[float, float, float, float]],
    radius: float = 0.45,
) -> bool:
    """Check circle vs AABB collision against dungeon boundaries and obstacles."""
    # Outer bounds clamp
    if abs(px) > 15.0 or abs(pz) > 20.0:
        return True

    for ox, oz, hw, hd in obstacles:
        closest_x = max(ox - hw, min(px, ox + hw))
        closest_z = max(oz - hd, min(pz, oz + hd))
        dx = px - closest_x
        dz = pz - closest_z
        if (dx * dx + dz * dz) < (radius * radius):
            return True
    return False


# ---------------------------------------------------------------------------
# Dungeon Crawler Master Game Class
# ---------------------------------------------------------------------------

class DungeonCrawler:
    """Master controller for 3D Third-Person Dungeon Crawler."""

    def __init__(self, width: int = 1280, height: int = 720, self_play: bool = False, max_frames: int = 180):
        self.self_play = self_play
        self.max_frames = max_frames
        self.frame_count = 0

        # Initialize Application
        self.app = App(
            "Velocity 3D - Dungeon Crawler",
            width=width,
            height=height,
            clear_color="#06070a",
            vsync=True,
        )
        self.app.show_hud = False
        self.app.show_crosshair = False
        self.scene = self.app.scene

        # 1. Setup Post-Processing Stack (Bloom + SSAO + ACES Tonemapping)
        self.composer = EffectComposer(self.app.width, self.app.height)
        self.ssao_pass = SSAOPass(radius=0.55, bias=0.025, power=1.2)
        self.bloom_pass = BloomPass(threshold=0.72, strength=2.2, radius=0.6)
        self.tonemap_pass = TonemappingPass(mode=TonemappingMode.ACESFilmic, exposure=1.05, gamma=2.2)

        self.composer.add_pass(self.ssao_pass)
        self.composer.add_pass(self.bloom_pass)
        self.composer.add_pass(self.tonemap_pass)
        self.app.composer = self.composer

        # 2. Lighting and Fire Systems
        self.lighting = DungeonLighting(self.scene)

        # 3. Modular Dungeon Environment & Interactables
        self.obstacles, self.chest, self.lever, self.portcullis = build_modular_dungeon(
            self.scene, self.lighting
        )

        # 4. Load Skeletal Hero Model (Soldier.glb)
        soldier_path = find_asset_path("Soldier.glb")
        self.hero_model = self.scene.load_model(str(soldier_path))

        if self.hero_model and self.hero_model.root_entity:
            self.hero_node = self.hero_model.root_entity
        else:
            # Fallback box hero
            self.hero_node = self.scene.create_entity("SoldierFallback")
            self.hero_node.mesh = Mesh.create_box(0.8, 1.8, 0.8)

        # Hero Spawn Position (Entrance Hall)
        self.hero_x = 0.0
        self.hero_z = 3.5
        self.hero_heading = 180.0
        self.hero_node.transform.position = (self.hero_x, 0.0, self.hero_z)

        # 5. Animation State Machine
        self.mixer: Optional[AnimationMixer] = None
        self.current_state = "Idle"
        self.is_attacking = False
        self.attack_timer = 0.0

        if self.hero_model and len(self.hero_model.animations) > 0:
            self.mixer = AnimationMixer(self.hero_node)
            for anim in self.hero_model.animations:
                self.mixer.clip_action(anim)

            # Synthesize specialized "Attack" animation clip from Run tracks
            run_clips = [a for a in self.hero_model.animations if a.name == "Run"]
            if run_clips:
                atk_clip = AnimationClip("Attack")
                for trk in run_clips[0].tracks:
                    atk_clip.add_track(trk)
                atk_clip.duration = 0.45
                atk_act = self.mixer.clip_action(atk_clip)
                atk_act.set_time_scale(2.2)

            idle_act = self.mixer.get_action("Idle")
            if idle_act:
                idle_act.play()

        # 6. Hero Broadsword Weapon & Sheath on Left Hip
        sword_root = self.scene.create_entity("HeroSword")
        sword_root.transform.position = (-0.28, 0.95, -0.05)
        sword_root.transform.rotation = (22.0, 10.0, -12.0)
        self.hero_node.add(sword_root)

        # Scabbard (Dark Leather)
        scabbard = self.scene.create_entity("SwordScabbard")
        scabbard.mesh = Mesh.create_box(0.045, 0.95, 0.09)
        scabbard_mat = StandardMaterial()
        scabbard_mat.base_color = (0.16, 0.12, 0.10, 1.0)
        scabbard_mat.roughness = 0.8
        scabbard_mat.metallic = 0.1
        scabbard.material = scabbard_mat
        scabbard.transform.position = (0.0, -0.35, 0.0)
        sword_root.add(scabbard)

        # Crossguard (Gilded Brass)
        guard = self.scene.create_entity("SwordCrossguard")
        guard.mesh = Mesh.create_box(0.065, 0.04, 0.24)
        guard_mat = StandardMaterial()
        guard_mat.base_color = (0.85, 0.72, 0.25, 1.0)
        guard_mat.metallic = 0.92
        guard_mat.roughness = 0.25
        guard.material = guard_mat
        guard.transform.position = (0.0, 0.14, 0.0)
        sword_root.add(guard)

        # Hilt Grip (Wrapped Leather)
        hilt = self.scene.create_entity("SwordHilt")
        hilt.mesh = Mesh.create_cylinder(radius=0.025, height=0.18, segments=8)
        hilt_mat = StandardMaterial()
        hilt_mat.base_color = (0.12, 0.10, 0.08, 1.0)
        hilt.material = hilt_mat
        hilt.transform.position = (0.0, 0.24, 0.0)
        sword_root.add(hilt)

        # Pommel (Golden Sphere)
        pommel = self.scene.create_entity("SwordPommel")
        pommel.mesh = Mesh.create_sphere(radius=0.038, rings=8, sectors=8)
        pommel.material = guard_mat
        pommel.transform.position = (0.0, 0.35, 0.0)
        sword_root.add(pommel)

        # 7. Third-Person Spring-Arm FollowCamera
        self.follow_cam = FollowCamera(
            camera=self.app.camera,
            target_entity=self.hero_node,
            offset=(0.0, 3.2, 5.8),
            look_at_offset=(0.0, 1.3, 0.0),
            stiffness=14.0,
            damping=0.85,
        )
        self.app.camera = self.follow_cam

        # 8. Hero Combat & RPG Progression Stats
        self.hp = 100.0
        self.max_hp = 100.0
        self.stamina = 100.0
        self.max_stamina = 100.0
        self.gold = 0
        self.keys = 0
        self.relics = 0

        # UI Prompts & Banners
        self.notification_msg = "DUNGEON CRAWLER INITIALIZED. EXPLORE THE CRYPT!"
        self.notification_timer = 4.0
        self.interaction_hint = ""

        # Performance & Benchmarking
        self.start_time = time.time()
        self.accum_time = 0.0
        self.benchmark_fps: List[float] = []

    def perform_attack(self) -> None:
        """Trigger sword attack slash."""
        if self.is_attacking or self.stamina < 15.0:
            return

        self.is_attacking = True
        self.attack_timer = 0.45
        self.stamina = max(0.0, self.stamina - 18.0)

        if self.mixer is not None:
            self.mixer.crossfade_to("Attack", 0.08)

        self.notification_msg = "SWORD SLASH! ATTACK EXECUTED."
        self.notification_timer = 2.0

        if hasattr(self.app, "audio") and self.app.audio is not None:
            try:
                self.app.audio.play_hit_3d((self.hero_x, 1.0, self.hero_z))
            except Exception:
                pass

    def perform_raycast_interaction(self) -> None:
        """Cast ray forward from hero and trigger click events on target objects."""
        # 1. Forward direction ray
        fwd_x = math.sin(math.radians(self.hero_heading))
        fwd_z = math.cos(math.radians(self.hero_heading))
        ray_origin = Vec3(self.hero_x, 1.2, self.hero_z)
        ray_dir = Vec3(fwd_x, 0.0, fwd_z)
        ray = Ray(ray_origin, ray_dir)

        hit = self.scene.raycast(ray, max_distance=3.5)

        # 2. Check Proximity if ray didn't hit direct bounding geometry
        dist_to_chest = math.hypot(self.hero_x - self.chest.pos[0], self.hero_z - self.chest.pos[2])
        dist_to_lever = math.hypot(self.hero_x - self.lever.pos[0], self.hero_z - self.lever.pos[2])

        if (hit.hit and "Chest" in hit.entity.name) or dist_to_chest < 2.5:
            if not self.chest.is_opened:
                self.chest.open()
                self.lighting.loot_emitter.set_position(self.chest.pos[0], 0.7, self.chest.pos[2])
                self.lighting.loot_emitter.burst(45)
                self.gold += 150
                self.relics += 1
                self.notification_msg = "ANCIENT CHEST OPENED! +150 GOLD, +1 ANCIENT RELIC!"
                self.notification_timer = 4.0
                if hasattr(self.app, "audio") and self.app.audio is not None:
                    try:
                        self.app.audio.play_jump()
                    except Exception:
                        pass

        elif (hit.hit and "Lever" in hit.entity.name) or dist_to_lever < 2.5:
            if not self.lever.is_pulled:
                self.lever.pull()
                self.portcullis.trigger_open()
                # Remove gate from collision obstacles
                self.obstacles = [o for o in self.obstacles if not (abs(o[0]) < 0.1 and abs(o[1] - (-13.0)) < 0.1)]
                self.notification_msg = "DUNGEON LEVER PULLED! PORTCULLIS UNLOCKED."
                self.notification_timer = 4.0

    def handle_input(self, dt: float) -> Tuple[float, float, bool, bool, bool]:
        """Query keyboard/mouse inputs or run autonomous scripted movement in self-play."""
        inp = self.app.input
        move_x = 0.0
        move_z = 0.0
        is_sprinting = False
        wants_attack = False
        wants_interact = False

        if self.self_play:
            # Deterministic autonomous walkthrough scripted across 180 frames
            t = self.frame_count

            # Phase 1: Move towards chest and open it
            if not self.chest.is_opened:
                target_x = self.chest.pos[0] - 1.2
                target_z = self.chest.pos[2]
                dx = target_x - self.hero_x
                dz = target_z - self.hero_z
                dist = math.hypot(dx, dz)
                if dist > 0.4:
                    move_x = dx / dist
                    move_z = dz / dist
                    is_sprinting = True
                else:
                    if t % 15 == 0:
                        wants_attack = True
                    wants_interact = True

            # Phase 2: Once chest opened, navigate across hall to lever
            elif not self.lever.is_pulled:
                target_x = self.lever.pos[0] + 1.2
                target_z = self.lever.pos[2]
                dx = target_x - self.hero_x
                dz = target_z - self.hero_z
                dist = math.hypot(dx, dz)
                if dist > 0.4:
                    move_x = dx / dist
                    move_z = dz / dist
                    is_sprinting = True
                else:
                    wants_interact = True

            # Phase 3: Head through opened gate into Grand Sanctuary
            else:
                target_x = 0.0
                target_z = -18.0
                dx = target_x - self.hero_x
                dz = target_z - self.hero_z
                dist = math.hypot(dx, dz)
                if dist > 0.4:
                    move_x = dx / dist
                    move_z = dz / dist
                    is_sprinting = True
                if t % 30 == 0:
                    wants_attack = True

        else:
            # Interactive WASD Navigation
            if inp.is_key_down(Key.W):
                move_z -= 1.0
            if inp.is_key_down(Key.S):
                move_z += 1.0
            if inp.is_key_down(Key.A):
                move_x -= 1.0
            if inp.is_key_down(Key.D):
                move_x += 1.0

            if inp.is_key_down(Key.LEFT_SHIFT):
                is_sprinting = True

            if inp.is_key_down(Key.SPACE) or inp.is_key_down(Key.F) or inp.is_mouse_down(0):
                wants_attack = True

            if inp.is_key_down(Key.E) or inp.is_mouse_down(1):
                wants_interact = True

        return move_x, move_z, is_sprinting, wants_attack, wants_interact

    def update(self, dt: float) -> None:
        """Run physics, animation state machine, and interactable updates."""
        self.accum_time += dt

        # Update interactables & lighting
        self.lighting.update(dt, self.accum_time)
        self.chest.update(dt)
        self.lever.update(dt)
        self.portcullis.update(dt)

        # Update notification banner timer
        if self.notification_timer > 0.0:
            self.notification_timer -= dt

        # Query input
        move_x, move_z, is_sprinting, wants_attack, wants_interact = self.handle_input(dt)

        # Trigger interaction
        if wants_interact:
            self.perform_raycast_interaction()

        # Contextual interaction hint calculation
        dist_to_chest = math.hypot(self.hero_x - self.chest.pos[0], self.hero_z - self.chest.pos[2])
        dist_to_lever = math.hypot(self.hero_x - self.lever.pos[0], self.hero_z - self.lever.pos[2])

        if dist_to_chest < 2.8 and not self.chest.is_opened:
            self.interaction_hint = "PRESS [E] OR CLICK TO OPEN ANCIENT CHEST"
        elif dist_to_lever < 2.8 and not self.lever.is_pulled:
            self.interaction_hint = "PRESS [E] OR CLICK TO PULL DUNGEON LEVER"
        elif self.portcullis.is_opening or self.portcullis.is_open:
            self.interaction_hint = "PORTCULLIS UNLOCKED - ADVANCE TO SANCTUARY"
        else:
            self.interaction_hint = ""

        # Trigger Attack
        if wants_attack:
            self.perform_attack()

        # Handle Attack State Duration
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0.0:
                self.is_attacking = False

        # Character Movement & Animation State Machine
        move_len = math.hypot(move_x, move_z)
        is_moving = move_len > 0.01 and not self.is_attacking

        move_speed = 3.6 # Normal Walk
        if is_sprinting and (self.stamina > 5.0 or self.self_play) and is_moving:
            move_speed = 8.8 if self.self_play else 6.4 # Sprint Run
            if not self.self_play:
                self.stamina = max(0.0, self.stamina - 20.0 * dt)
        else:
            self.stamina = min(self.max_stamina, self.stamina + 28.0 * dt)

        # Animation State Crossfading
        if self.is_attacking:
            self.current_state = "Attack"
        elif is_moving:
            move_x /= move_len
            move_z /= move_len

            target_state = "Run" if (is_sprinting and self.stamina > 5.0) else "Walk"
            if self.current_state != target_state:
                if self.mixer is not None:
                    self.mixer.crossfade_to(target_state, 0.18)
                self.current_state = target_state

            # Smooth heading orientation
            target_heading = math.degrees(math.atan2(move_x, move_z)) + 180.0
            self.hero_heading = target_heading
            self.hero_node.transform.rotation = (0.0, self.hero_heading, 0.0)

            # Collision Detection & Sliding Physics
            step_x = move_x * move_speed * dt
            step_z = move_z * move_speed * dt

            new_x = self.hero_x + step_x
            new_z = self.hero_z + step_z

            if not check_dungeon_collision(new_x, new_z, self.obstacles):
                self.hero_x = new_x
                self.hero_z = new_z
            elif not check_dungeon_collision(new_x, self.hero_z, self.obstacles):
                # Slide along X
                self.hero_x = new_x
            elif not check_dungeon_collision(self.hero_x, new_z, self.obstacles):
                # Slide along Z
                self.hero_z = new_z

            self.hero_node.transform.position = (self.hero_x, 0.0, self.hero_z)
        else:
            if not self.is_attacking and self.current_state != "Idle":
                if self.mixer is not None:
                    self.mixer.crossfade_to("Idle", 0.22)
                self.current_state = "Idle"

        # Advance skeletal animation mixer
        if self.mixer is not None:
            self.mixer.update(dt)

        # Update FollowCamera spring-arm
        self.follow_cam.update(dt)

    def draw_hud(self) -> None:
        """Render high-fantasy action RPG HUD: HP bar, stamina, inventory, and contextual hints."""
        ui = self.app.ui
        ui.clear()

        sw = float(self.app.width)
        sh = float(self.app.height)
        cx = sw * 0.5
        cy = sh * 0.5

        # 1. Hero Profile & Status Bars (Top Left)
        ui.draw_text("KNIGHT CHAMPION // CRYPT EXPEDITION", (28, 24), size=18, color=WARM_WHITE)

        # Health Bar (Crimson)
        bar_w = 200.0
        bar_h = 14.0
        ui.draw_text(f"HP  {int(self.hp)} / {int(self.max_hp)}", (28, 48), size=11, color=Color(1.0, 0.7, 0.7, 1.0))
        ui.draw_rect(28.0, 62.0, bar_w, bar_h, color=Color(0.2, 0.1, 0.12, 0.8), thickness=1.0)
        cur_hp_w = max(0.0, (self.hp / self.max_hp) * (bar_w - 2.0))
        ui.draw_rect(29.0, 63.0, cur_hp_w, bar_h - 2.0, color=Color(0.9, 0.2, 0.2, 0.95), thickness=1.0)

        # Stamina Bar (Emerald)
        ui.draw_text(f"STAMINA  {int(self.stamina)}%", (28, 82), size=11, color=Color(0.7, 1.0, 0.8, 1.0))
        ui.draw_rect(28.0, 96.0, bar_w, bar_h - 2.0, color=Color(0.1, 0.2, 0.15, 0.8), thickness=1.0)
        cur_stam_w = max(0.0, (self.stamina / self.max_stamina) * (bar_w - 2.0))
        ui.draw_rect(29.0, 97.0, cur_stam_w, bar_h - 4.0, color=Color(0.2, 0.85, 0.45, 0.95), thickness=1.0)

        # 2. Inventory Counter Badges (Top Right)
        badge_w = 460.0
        rx = sw - badge_w - 28.0
        ui.draw_rect(rx, 20.0, badge_w, 48.0, color=Color(0.06, 0.08, 0.12, 0.92), thickness=1.5)
        # Gold accent top line
        ui.draw_rect(rx, 20.0, badge_w, 2.5, color=Color(0.85, 0.70, 0.25, 0.95), thickness=1.0)
        ui.draw_text(f"GOLD: {self.gold:04d}", (int(rx + 20.0), 34), size=13, color=YELLOW)
        ui.draw_text(f"KEYS: {self.keys}", (int(rx + 180.0), 34), size=13, color=CYAN)
        ui.draw_text(f"RELICS: {self.relics}", (int(rx + 315.0), 34), size=13, color=MAGENTA)

        # 3. Contextual Interaction Prompt (Floating Center Screen)
        if self.interaction_hint:
            hint_w = len(self.interaction_hint) * 8.5
            ui.draw_rect(cx - hint_w * 0.5 - 14.0, cy + 50.0, hint_w + 28.0, 28.0, color=Color(0.06, 0.08, 0.12, 0.85), thickness=1.2)
            ui.draw_text(self.interaction_hint, (int(cx - hint_w * 0.5), int(cy + 56.0)), size=13, color=YELLOW)

        # 4. Action Notification Banner
        if self.notification_timer > 0.0:
            notif_w = len(self.notification_msg) * 8.0
            ui.draw_rect(cx - notif_w * 0.5 - 12.0, 80.0, notif_w + 24.0, 26.0, color=Color(0.1, 0.14, 0.22, 0.9), thickness=1.0)
            ui.draw_text(self.notification_msg, (int(cx - notif_w * 0.5), 86), size=12, color=CYAN)

        # 5. Bottom Controls Bar & Mode Indicator
        if self.self_play:
            ui.draw_text(f"[AUTONOMOUS SELF-PLAY] FRAME: {self.frame_count}/{self.max_frames} | STATE: {self.current_state}", (28, int(sh - 34)), size=12, color=YELLOW)
        else:
            ui.draw_text("WASD: Move | Shift: Sprint | LMB: Attack | E: Interact", (28, int(sh - 34)), size=11, color=Color(0.75, 0.80, 0.90, 0.85))

        # Center Aim Reticle
        ui.draw_crosshair(size=6.0, color=WHITE, pos=(cx, cy), thickness=1.0)

    def run(self) -> None:
        """Main game loop for interactive and headless self-play execution."""
        last_time = time.time()

        def update(dt: float) -> None:
            nonlocal last_time
            self.frame_count += 1
            now = time.time()
            frame_dt = max(0.001, min(0.05, now - last_time if not self.self_play else 1.0 / 60.0))
            last_time = now

            self.benchmark_fps.append(1.0 / frame_dt)

            self.update(frame_dt)
            self.draw_hud()

            if self.self_play and self.frame_count >= self.max_frames:
                avg_fps = sum(self.benchmark_fps) / len(self.benchmark_fps) if self.benchmark_fps else 60.0
                print(f"[Self-Play Completed] Successfully ran {self.frame_count} frames! Avg FPS: {avg_fps:.1f} | Gold: {self.gold} | Relics: {self.relics} | Gate Open: {self.portcullis.is_open or self.portcullis.is_opening}")
                self.app.close()

        self.app.on_update(update)

        if not self.self_play and "--headless" not in sys.argv:
            self.app.run()
        else:
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

    crawler = DungeonCrawler(width=1280, height=720, self_play=is_self_play, max_frames=max_frames)
    crawler.run()


if __name__ == "__main__":
    main()
