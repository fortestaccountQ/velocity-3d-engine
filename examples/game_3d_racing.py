"""game_3d_racing.py - 3D Arcade Circuit Racing Simulator.

Part of Velocity 3D Engine Showcase Games.

Features:
- Physics-based sports car dynamics: acceleration (0 to 180 km/h), progressive braking,
  reverse gear, speed-sensitive front wheel steering (+-28 deg), and centrifugal handbrake drift.
- Sleek aerodynamic sports car hierarchy:
  * Glossy PBR metallic racing paint (metallic = 0.85, roughness = 0.15).
  * Glowing emissive headlights (intensity = 3.0) and dynamic taillights (turn bright red on brake).
  * 4 separate wheel meshes (FL, FR, RL, RR) with alloy rims and rubber tires:
    - Front wheels yaw with steering angle (+-28 deg).
    - All 4 wheels spin around pitch/spin axis proportional to linear road speed (v / r).
  * Twin tire-smoke particle emitters (`ParticleEmitter`) spawning white/grey smoke puffs during
    hard braking or centrifugal drifting.
- Closed asphalt race circuit:
  * Closed 3D CatmullRomCurve3 spline with curved corners and banked turns.
  * Procedural asphalt road ribbon and alternating red-and-white rumble curbs along corners.
  * 4 Checkpoint gates distributed around the track to register sector splits and lap completion.
  * Guardrails with collision detection preventing the car from driving off-world.
- Telemetry HUD (`UIOverlay`):
  * Digital and analog speedometer (0 to 180 km/h).
  * Tachometer (RPM) and 6-speed dual-clutch gear indicator ('R', 'N', '1'..'6').
  * Live lap timer, Current lap, and Best lap record.
  * Drift score indicator rewarding sustained powerslides.
  * Checkpoint sector indicators.
- Camera modes (toggle with 'C'):
  * Mode 1: Dynamic Chase Camera with FOV speed-zoom (55 deg to 71 deg at 180 km/h) and spring damping.
  * Mode 2: Showroom Turntable OrbitController with mouse orbit and auto-rotation.
- Full automated self-play mode triggered via `--test` running for 120 frames and exiting cleanly with code 0.
"""

from __future__ import annotations

import sys
import math
import time
from pathlib import Path
from typing import Optional, List, Tuple, Any

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
    Mesh,
    StandardMaterial,
    ParticleEmitter,
    BlendMode,
    CubeTexture,
    EffectComposer,
    BloomPass,
    TonemappingPass,
    TonemappingMode,
    Vec3,
    Vec4,
    Color,
    Key,
    OrbitController,
    WARM_WHITE,
    CYAN,
    YELLOW,
    WHITE,
    RED,
    GREEN,
    MAGENTA,
)

# ---------------------------------------------------------------------------
# Constants & Physics Tuning
# ---------------------------------------------------------------------------

MAX_SPEED_MS: float = 50.0       # 180 km/h in m/s
MAX_REVERSE_MS: float = -9.72     # -35 km/h in m/s
ACCELERATION: float = 14.5        # Base engine acceleration m/s^2
BRAKING_DECEL: float = 24.0       # Brake deceleration m/s^2
REVERSE_ACCEL: float = 8.5        # Reverse acceleration m/s^2
ROLLING_RESISTANCE: float = 1.2   # Passive drag deceleration m/s^2
MAX_STEER_DEG: float = 28.0       # Maximum front wheel steer angle
WHEEL_RADIUS: float = 0.35        # Wheel radius in meters (for spin v / r)
WHEEL_WIDTH: float = 0.28         # Wheel width in meters
TRACK_WIDTH: float = 12.0         # Track road width in meters
CURB_WIDTH: float = 1.2           # Rumble curb width in meters
GUARDRAIL_OFFSET: float = 7.4     # Distance from centerline to guardrail

# Closed 3D Circuit Control Points
TRACK_CONTROL_POINTS: List[Tuple[float, float, float]] = [
    (0.0, 0.0, 60.0),
    (0.0, 0.0, 0.0),       # Checkpoint 0: Start / Finish Line
    (0.0, 0.0, -60.0),
    (30.0, 1.5, -110.0),   # Turn 1: Sweeping right turn with banking
    (80.0, 2.5, -130.0),
    (140.0, 1.2, -110.0),
    (170.0, 0.6, -50.0),   # Checkpoint 1: Sector 1 Exit
    (180.0, 0.0, 10.0),
    (160.0, 0.0, 70.0),    # Turn 2: Chicane S-curve entry
    (130.0, 0.8, 90.0),    # Checkpoint 2: Chicane apex
    (110.0, 0.0, 120.0),
    (70.0, 3.0, 160.0),    # Turn 3: Hairpin / Banked Carousel
    (10.0, 3.5, 170.0),
    (-40.0, 2.0, 150.0),   # Checkpoint 3: Hairpin Exit / Sector 3
    (-60.0, 0.8, 110.0),   # Turn 4: Final sweep back onto main straight
    (-40.0, 0.0, 75.0),
]


# ---------------------------------------------------------------------------
# Geometry Builders (Procedural Wheels, Car, Track & Gantries)
# ---------------------------------------------------------------------------

def create_wheel_mesh(radius: float = WHEEL_RADIUS, width: float = WHEEL_WIDTH, segments: int = 24) -> ve.Mesh:
    """Generate a procedural cylindrical wheel mesh oriented along the X axle.

    Includes alloy rim caps and dark tire tread with outward normals.
    Stride: 12 floats (px, py, pz, nx, ny, nz, u, v, r, g, b, a).
    """
    verts: List[float] = []
    indices: List[int] = []
    hw = width * 0.5

    # Center vertices for wheel hub caps
    # 0: Left wheel hub center
    verts.extend([-hw, 0.0, 0.0, -1.0, 0.0, 0.0, 0.5, 0.5, 0.75, 0.78, 0.82, 1.0])
    # 1: Right wheel hub center
    verts.extend([hw, 0.0, 0.0, 1.0, 0.0, 0.0, 0.5, 0.5, 0.75, 0.78, 0.82, 1.0])

    for i in range(segments):
        theta = 2.0 * math.pi * i / segments
        y = radius * math.cos(theta)
        z = radius * math.sin(theta)

        # Left rim vertex
        verts.extend([-hw, y, z, -1.0, 0.0, 0.0, 0.5 + 0.5 * math.cos(theta), 0.5 + 0.5 * math.sin(theta), 0.7, 0.72, 0.75, 1.0])
        # Right rim vertex
        verts.extend([hw, y, z, 1.0, 0.0, 0.0, 0.5 + 0.5 * math.cos(theta), 0.5 + 0.5 * math.sin(theta), 0.7, 0.72, 0.75, 1.0])
        # Left tread vertex
        verts.extend([-hw, y, z, 0.0, math.cos(theta), math.sin(theta), 0.0, float(i) / segments, 0.12, 0.12, 0.13, 1.0])
        # Right tread vertex
        verts.extend([hw, y, z, 0.0, math.cos(theta), math.sin(theta), 1.0, float(i) / segments, 0.12, 0.12, 0.13, 1.0])

    for i in range(segments):
        i_next = (i + 1) % segments
        # Left wheel cap triangle
        indices.extend([0, 2 + i_next * 4, 2 + i * 4])
        # Right wheel cap triangle
        indices.extend([1, 2 + i * 4 + 1, 2 + i_next * 4 + 1])
        # Tread quad (two triangles)
        tl0 = 2 + i * 4 + 2
        tr0 = 2 + i * 4 + 3
        tl1 = 2 + i_next * 4 + 2
        tr1 = 2 + i_next * 4 + 3
        indices.extend([tl0, tr0, tr1])
        indices.extend([tl0, tr1, tl1])

    return ve.Mesh.create_custom(verts, indices, 12)


def build_sports_car_hierarchy(scene: ve.Scene) -> Tuple[ve.Entity, ve.Entity, List[ve.Entity], ve.StandardMaterial]:
    """Construct the sleek procedural 3D sports car hierarchy with glossy PBR metallic paint,

    glowing headlights, dynamic brake taillights, and 4 wheel meshes.
    Returns: (car_root, chassis, wheels_list, taillight_mat)
    """
    car_root = scene.create_entity("CarRoot")
    chassis = scene.create_entity("Chassis")
    car_root.add(chassis)

    # 1. Main aerodynamic lower body shell (glossy metallic paint)
    body_mat = StandardMaterial()
    body_mat.base_color = (0.92, 0.08, 0.12, 1.0) # Vibrant Italian racing red
    body_mat.metallic = 0.85
    body_mat.roughness = 0.15

    body = scene.create_entity("CarBody")
    body.mesh = Mesh.create_box(1.9, 0.44, 4.3)
    body.material = body_mat
    body.transform.position = (0.0, 0.38, 0.0)
    chassis.add(body)

    # 2. Sloped front hood / nose
    hood = scene.create_entity("CarHood")
    hood.mesh = Mesh.create_box(1.82, 0.28, 1.5)
    hood.material = body_mat
    hood.transform.position = (0.0, 0.42, -1.25)
    chassis.add(hood)

    # 3. Aerodynamic tapered greenhouse / cockpit cabin (tinted glass)
    glass_mat = StandardMaterial()
    glass_mat.base_color = (0.08, 0.12, 0.18, 0.85)
    glass_mat.metallic = 0.92
    glass_mat.roughness = 0.08

    cockpit = scene.create_entity("CarCockpit")
    cockpit.mesh = Mesh.create_box(1.42, 0.42, 1.95)
    cockpit.material = glass_mat
    cockpit.transform.position = (0.0, 0.74, 0.22)
    chassis.add(cockpit)

    # 4. Front carbon-fiber splitter lip
    carbon_mat = StandardMaterial()
    carbon_mat.base_color = (0.1, 0.1, 0.12, 1.0)
    carbon_mat.metallic = 0.3
    carbon_mat.roughness = 0.65

    splitter = scene.create_entity("FrontSplitter")
    splitter.mesh = Mesh.create_box(2.0, 0.08, 0.5)
    splitter.material = carbon_mat
    splitter.transform.position = (0.0, 0.18, -2.15)
    chassis.add(splitter)

    # 5. Rear carbon-fiber aerodynamic diffuser
    diffuser = scene.create_entity("RearDiffuser")
    diffuser.mesh = Mesh.create_box(1.88, 0.14, 0.6)
    diffuser.material = carbon_mat
    diffuser.transform.position = (0.0, 0.22, 2.05)
    chassis.add(diffuser)

    # 6. High-downforce GT rear racing wing
    wing_strut_mesh = Mesh.create_box(0.08, 0.32, 0.22)
    strut_l = scene.create_entity("WingStrut_L")
    strut_l.mesh = wing_strut_mesh
    strut_l.material = carbon_mat
    strut_l.transform.position = (-0.62, 0.74, 2.0)
    chassis.add(strut_l)

    strut_r = scene.create_entity("WingStrut_R")
    strut_r.mesh = wing_strut_mesh
    strut_r.material = carbon_mat
    strut_r.transform.position = (0.62, 0.74, 2.0)
    chassis.add(strut_r)

    wing_foil = scene.create_entity("WingFoil")
    wing_foil.mesh = Mesh.create_box(1.95, 0.06, 0.38)
    wing_foil.material = carbon_mat
    wing_foil.transform.position = (0.0, 0.92, 2.0)
    chassis.add(wing_foil)

    # 7. Glowing emissive front headlights (intensity = 3.0)
    headlight_mat = StandardMaterial()
    headlight_mat.base_color = (0.95, 0.98, 1.0, 1.0)
    headlight_mat.emissive_color = (1.0, 1.0, 0.95, 1.0)
    headlight_mat.emissive_intensity = 3.0

    hl_mesh = Mesh.create_box(0.35, 0.12, 0.15)
    hl_l = scene.create_entity("Headlight_L")
    hl_l.mesh = hl_mesh
    hl_l.material = headlight_mat
    hl_l.transform.position = (-0.66, 0.42, -2.15)
    chassis.add(hl_l)

    hl_r = scene.create_entity("Headlight_R")
    hl_r.mesh = hl_mesh
    hl_r.material = headlight_mat
    hl_r.transform.position = (0.66, 0.42, -2.15)
    chassis.add(hl_r)

    # 8. Dynamic emissive taillights (turns bright red on braking)
    taillight_mat = StandardMaterial()
    taillight_mat.base_color = (0.65, 0.06, 0.06, 1.0)
    taillight_mat.emissive_color = (0.6, 0.04, 0.04, 1.0)
    taillight_mat.emissive_intensity = 1.0

    tl_mesh = Mesh.create_box(0.48, 0.10, 0.12)
    tl_l = scene.create_entity("Taillight_L")
    tl_l.mesh = tl_mesh
    tl_l.material = taillight_mat
    tl_l.transform.position = (-0.65, 0.44, 2.15)
    chassis.add(tl_l)

    tl_r = scene.create_entity("Taillight_R")
    tl_r.mesh = tl_mesh
    tl_r.material = taillight_mat
    tl_r.transform.position = (0.65, 0.44, 2.15)
    chassis.add(tl_r)

    # 9. Four separate wheel entities (0: FL, 1: FR, 2: RL, 3: RR)
    wheel_mesh = create_wheel_mesh(radius=WHEEL_RADIUS, width=WHEEL_WIDTH, segments=24)
    wheel_mat = StandardMaterial()
    wheel_mat.base_color = (0.8, 0.82, 0.86, 1.0)
    wheel_mat.metallic = 0.85
    wheel_mat.roughness = 0.25

    wheel_fl = scene.create_entity("Wheel_FL")
    wheel_fl.mesh = wheel_mesh
    wheel_fl.material = wheel_mat
    wheel_fl.transform.position = (-0.95, WHEEL_RADIUS, -1.35)
    car_root.add(wheel_fl)

    wheel_fr = scene.create_entity("Wheel_FR")
    wheel_fr.mesh = wheel_mesh
    wheel_fr.material = wheel_mat
    wheel_fr.transform.position = (0.95, WHEEL_RADIUS, -1.35)
    car_root.add(wheel_fr)

    wheel_rl = scene.create_entity("Wheel_RL")
    wheel_rl.mesh = wheel_mesh
    wheel_rl.material = wheel_mat
    wheel_rl.transform.position = (-0.95, WHEEL_RADIUS, 1.35)
    car_root.add(wheel_rl)

    wheel_rr = scene.create_entity("Wheel_RR")
    wheel_rr.mesh = wheel_mesh
    wheel_rr.material = wheel_mat
    wheel_rr.transform.position = (0.95, WHEEL_RADIUS, 1.35)
    car_root.add(wheel_rr)

    wheels: List[ve.Entity] = [wheel_fl, wheel_fr, wheel_rl, wheel_rr]
    car_root.update_world_matrix()

    return car_root, chassis, wheels, taillight_mat


# ---------------------------------------------------------------------------
# Track Spline, Ribbon & Checkpoint Architecture
# ---------------------------------------------------------------------------

class TrackSegment:
    """Precomputed road segment along the CatmullRom spline."""

    def __init__(self, index: int, center: ve.Vec3, tangent: ve.Vec3, normal: ve.Vec3, width: float = TRACK_WIDTH) -> None:
        self.index: int = index
        self.center: ve.Vec3 = center
        self.tangent: ve.Vec3 = tangent
        self.normal: ve.Vec3 = normal # Perpendicular right vector in X-Z
        self.width: float = width
        half_w = width * 0.5
        self.left_boundary: ve.Vec3 = ve.Vec3(center.x - normal.x * half_w, center.y, center.z - normal.z * half_w)
        self.right_boundary: ve.Vec3 = ve.Vec3(center.x + normal.x * half_w, center.y, center.z + normal.z * half_w)


def build_track_geometry(curve: ve.CatmullRomCurve3, num_samples: int = 240) -> Tuple[ve.Mesh, ve.Mesh, ve.Mesh, List[TrackSegment]]:
    """Generate the closed asphalt track ribbon, rumble curbs, guardrails, and segment math."""
    asphalt_verts: List[float] = []
    asphalt_indices: List[int] = []

    curb_verts: List[float] = []
    curb_indices: List[int] = []

    rail_verts: List[float] = []
    rail_indices: List[int] = []

    segments: List[TrackSegment] = []

    half_w = TRACK_WIDTH * 0.5
    curb_w = CURB_WIDTH

    for i in range(num_samples):
        t = float(i) / float(num_samples)
        p = curve.get_point(t)
        tang = curve.get_tangent(t)

        # Right normal vector: Tangent x (0, 1, 0)
        rx = tang.z
        ry = 0.0
        rz = -tang.x
        l = math.hypot(rx, rz)
        if l > 1e-6:
            rx /= l
            rz /= l

        norm = ve.Vec3(rx, ry, rz)
        seg = TrackSegment(i, p, tang, norm, TRACK_WIDTH)
        segments.append(seg)

        # Asphalt boundary positions
        lx, ly, lz = p.x - rx * half_w, p.y, p.z - rz * half_w
        rrx, rry, rrz = p.x + rx * half_w, p.y, p.z + rz * half_w

        # 1. Asphalt road quad vertices
        v_offset = float(i) * 0.35
        asphalt_verts.extend([lx, ly, lz, 0.0, 1.0, 0.0, 0.0, v_offset, 0.2, 0.21, 0.24, 1.0])
        asphalt_verts.extend([rrx, rry, rrz, 0.0, 1.0, 0.0, 1.0, v_offset, 0.2, 0.21, 0.24, 1.0])

        # 2. Alternating rumble curbs (red and white)
        is_red = ((i // 3) % 2) == 0
        cr, cg, cb = (0.88, 0.12, 0.12) if is_red else (0.95, 0.95, 0.95)
        curb_elev = ly + 0.08

        # Left curb (from lx - curb_w to lx)
        clx = lx - rx * curb_w
        clz = lz - rz * curb_w
        curb_verts.extend([clx, curb_elev, clz, 0.0, 1.0, 0.0, 0.0, 0.0, cr, cg, cb, 1.0])
        curb_verts.extend([lx, curb_elev, lz, 0.0, 1.0, 0.0, 1.0, 0.0, cr, cg, cb, 1.0])

        # Right curb (from rrx to rrx + curb_w)
        crx = rrx + rx * curb_w
        crz = rrz + rz * curb_w
        curb_verts.extend([rrx, curb_elev, rrz, 0.0, 1.0, 0.0, 0.0, 0.0, cr, cg, cb, 1.0])
        curb_verts.extend([crx, curb_elev, crz, 0.0, 1.0, 0.0, 1.0, 0.0, cr, cg, cb, 1.0])

        # 3. Outer guardrails
        glx = lx - rx * (curb_w + 0.2)
        glz = lz - rz * (curb_w + 0.2)
        grx = rrx + rx * (curb_w + 0.2)
        grz = rrz + rz * (curb_w + 0.2)

        rail_verts.extend([glx, ly + 0.2, glz, rx, 0.0, rz, 0.0, 0.0, 0.75, 0.78, 0.82, 1.0])
        rail_verts.extend([glx, ly + 0.75, glz, rx, 0.0, rz, 0.0, 1.0, 0.85, 0.88, 0.92, 1.0])
        rail_verts.extend([grx, rry + 0.2, grz, -rx, 0.0, -rz, 0.0, 0.0, 0.75, 0.78, 0.82, 1.0])
        rail_verts.extend([grx, rry + 0.75, grz, -rx, 0.0, -rz, 0.0, 1.0, 0.85, 0.88, 0.92, 1.0])

    for i in range(num_samples):
        i_next = (i + 1) % num_samples

        # Asphalt indices
        a0 = i * 2
        a1 = i * 2 + 1
        a2 = i_next * 2
        a3 = i_next * 2 + 1
        asphalt_indices.extend([a0, a1, a2, a1, a3, a2])

        # Curb indices (4 verts per slice: 2 for left curb, 2 for right curb)
        c_base = i * 4
        c_next = i_next * 4
        # Left curb quad
        curb_indices.extend([c_base, c_base + 1, c_next, c_base + 1, c_next + 1, c_next])
        # Right curb quad
        curb_indices.extend([c_base + 2, c_base + 3, c_next + 2, c_base + 3, c_next + 3, c_next + 2])

        # Guardrail indices (4 verts per slice: 2 left rail, 2 right rail)
        r_base = i * 4
        r_next = i_next * 4
        rail_indices.extend([r_base, r_next, r_base + 1, r_next, r_next + 1, r_base + 1])
        rail_indices.extend([r_base + 2, r_base + 3, r_next + 2, r_base + 3, r_next + 3, r_next + 2])

    asphalt_mesh = ve.Mesh.create_custom(asphalt_verts, asphalt_indices, 12)
    curbs_mesh = ve.Mesh.create_custom(curb_verts, curb_indices, 12)
    rails_mesh = ve.Mesh.create_custom(rail_verts, rail_indices, 12)

    return asphalt_mesh, curbs_mesh, rails_mesh, segments


def build_checkpoint_gantry(
    scene: ve.Scene,
    center_pos: Tuple[float, float, float],
    tangent: Tuple[float, float, float],
    title: str,
    color_rgb: Tuple[float, float, float],
) -> Tuple[ve.Entity, ve.AABB]:
    """Construct an overhead structural race gantry with glowing neon checkpoint banners."""
    gantry_root = scene.create_entity(f"Gantry_{title}")
    gantry_root.transform.position = center_pos

    # Heading from tangent
    yaw_deg = math.degrees(math.atan2(-tangent[0], -tangent[2]))
    gantry_root.transform.rotation = (0.0, yaw_deg, 0.0)

    # Steel pillar material
    steel_mat = StandardMaterial()
    steel_mat.base_color = (0.35, 0.38, 0.42, 1.0)
    steel_mat.metallic = 0.9
    steel_mat.roughness = 0.25

    # Neon emissive banner material
    neon_mat = StandardMaterial()
    neon_mat.base_color = (color_rgb[0], color_rgb[1], color_rgb[2], 1.0)
    neon_mat.emissive_color = (color_rgb[0], color_rgb[1], color_rgb[2], 1.0)
    neon_mat.emissive_intensity = 3.2

    # Left & Right structural columns
    col_mesh = Mesh.create_box(0.5, 5.8, 0.5)
    col_l = scene.create_entity("GantryCol_L")
    col_l.mesh = col_mesh
    col_l.material = steel_mat
    col_l.transform.position = (-7.5, 2.9, 0.0)
    gantry_root.add(col_l)

    col_r = scene.create_entity("GantryCol_R")
    col_r.mesh = col_mesh
    col_r.material = steel_mat
    col_r.transform.position = (7.5, 2.9, 0.0)
    gantry_root.add(col_r)

    # Horizontal overhead truss
    truss_mesh = Mesh.create_box(15.5, 0.45, 0.45)
    truss = scene.create_entity("GantryTruss")
    truss.mesh = truss_mesh
    truss.material = steel_mat
    truss.transform.position = (0.0, 5.5, 0.0)
    gantry_root.add(truss)

    # Illuminated checkpoint banner
    banner_mesh = Mesh.create_box(10.5, 1.1, 0.25)
    banner = scene.create_entity("GantryBanner")
    banner.mesh = banner_mesh
    banner.material = neon_mat
    banner.transform.position = (0.0, 4.8, 0.0)
    gantry_root.add(banner)

    gantry_root.update_world_matrix()

    # Trigger AABB around gate
    cx, cy, cz = center_pos
    aabb = ve.AABB(
        ve.Vec3(cx - 10.0, cy - 1.0, cz - 10.0),
        ve.Vec3(cx + 10.0, cy + 8.0, cz + 10.0),
    )
    return gantry_root, aabb


class RaceTrack:
    """Closed asphalt race track circuit with curbs, guardrails, checkpoints, and lap records."""

    def __init__(self, scene: ve.Scene) -> None:
        self.scene: ve.Scene = scene
        self.spline: ve.CatmullRomCurve3 = ve.CatmullRomCurve3(TRACK_CONTROL_POINTS, closed=True)

        asphalt_m, curbs_m, rails_m, self.segments = build_track_geometry(self.spline, num_samples=240)

        # 1. Asphalt road entity
        self.asphalt_entity: ve.Entity = scene.create_entity("AsphaltCircuit")
        self.asphalt_entity.mesh = asphalt_m
        mat_asphalt = StandardMaterial()
        mat_asphalt.base_color = (0.22, 0.23, 0.26, 1.0)
        mat_asphalt.metallic = 0.1
        mat_asphalt.roughness = 0.85
        self.asphalt_entity.material = mat_asphalt

        # 2. Rumble curbs entity
        self.curbs_entity: ve.Entity = scene.create_entity("RumbleCurbs")
        self.curbs_entity.mesh = curbs_m
        mat_curbs = StandardMaterial()
        mat_curbs.metallic = 0.2
        mat_curbs.roughness = 0.5
        self.curbs_entity.material = mat_curbs
        self.curbs: List[ve.Entity] = [self.curbs_entity]

        # 3. Guardrails entity
        self.guardrails_entity: ve.Entity = scene.create_entity("Guardrails")
        self.guardrails_entity.mesh = rails_m
        mat_rails = StandardMaterial()
        mat_rails.base_color = (0.8, 0.82, 0.86, 1.0)
        mat_rails.metallic = 0.88
        mat_rails.roughness = 0.25
        self.guardrails_entity.material = mat_rails

        # 4. Checkpoints & Gantries (4 distributed around circuit)
        self.checkpoints: List[ve.AABB] = []
        self.gantry_entities: List[ve.Entity] = []

        cp_specs = [
            (0.0625, "START / FINISH", (1.0, 0.85, 0.2)), # Checkpoint 0: Yellow/Gold
            (0.3750, "SECTOR 1",       (0.1, 0.85, 1.0)), # Checkpoint 1: Cyan
            (0.5625, "SECTOR 2",       (1.0, 0.65, 0.1)), # Checkpoint 2: Orange/Amber
            (0.8125, "SECTOR 3",       (1.0, 0.15, 0.6)), # Checkpoint 3: Magenta
        ]

        for t_val, title, color_rgb in cp_specs:
            pt = self.spline.get_point(t_val)
            tang = self.spline.get_tangent(t_val)
            gantry_ent, aabb = build_checkpoint_gantry(
                scene,
                (pt.x, pt.y, pt.z),
                (tang.x, tang.y, tang.z),
                title,
                color_rgb,
            )
            self.gantry_entities.append(gantry_ent)
            self.checkpoints.append(aabb)

        # Lap and split records
        self.next_checkpoint_idx: int = 0
        self.lap_started: bool = False
        self.current_lap: int = 1
        self.current_lap_time: float = 0.0
        self.lap_times: List[float] = []
        self.best_lap: float = float("inf")
        self.last_checkpoint_name: str = "START LINE"

    def check_checkpoint(self, car_pos: ve.Vec3) -> Optional[int]:
        """Verify if car enters the expected next checkpoint volume and advance lap state."""
        target_aabb = self.checkpoints[self.next_checkpoint_idx]
        if target_aabb.contains(car_pos):
            triggered_idx = self.next_checkpoint_idx
            if triggered_idx == 0:
                if self.lap_started:
                    self.lap_times.append(self.current_lap_time)
                    if self.current_lap_time < self.best_lap:
                        self.best_lap = self.current_lap_time
                    self.current_lap += 1
                self.lap_started = True
                self.current_lap_time = 0.0
                self.last_checkpoint_name = "START / FINISH"
            elif triggered_idx == 1:
                self.last_checkpoint_name = "SECTOR 1"
            elif triggered_idx == 2:
                self.last_checkpoint_name = "SECTOR 2"
            elif triggered_idx == 3:
                self.last_checkpoint_name = "SECTOR 3"

            self.next_checkpoint_idx = (self.next_checkpoint_idx + 1) % len(self.checkpoints)
            return triggered_idx
        return None

    def get_closest_segment(self, pos: ve.Vec3) -> TrackSegment:
        """Find the closest precomputed track segment for collision and elevation."""
        best_seg = self.segments[0]
        min_dist_sq = float("inf")
        px, pz = pos.x, pos.z

        for seg in self.segments:
            dx = px - seg.center.x
            dz = pz - seg.center.z
            d2 = dx * dx + dz * dz
            if d2 < min_dist_sq:
                min_dist_sq = d2
                best_seg = seg
        return best_seg


# ---------------------------------------------------------------------------
# RaceCar Dynamic Vehicle Implementation
# ---------------------------------------------------------------------------

class RaceCar:
    """High-performance 3D Sports Car with interactive controls, tire smoke,

    wheel rotation, and centrifugal drift physics.
    """

    def __init__(self, scene: ve.Scene, start_pos: Tuple[float, float, float] = (0.0, 0.35, 45.0), start_heading: float = 0.0) -> None:
        self.scene: ve.Scene = scene
        self.root, self.chassis, self.wheels, self.taillight_mat = build_sports_car_hierarchy(scene)

        self.position: ve.Vec3 = ve.Vec3(start_pos[0], start_pos[1], start_pos[2])
        self.heading: float = float(start_heading) # Yaw angle in degrees (0 = facing -Z forward)
        self.linear_velocity: float = 0.0          # Forward speed in m/s (speed_kmh = linear_velocity * 3.6)
        self.lateral_velocity: float = 0.0         # Sideways slip velocity in m/s
        self.angular_velocity: float = 0.0         # Yaw rate in rad/s
        self.steer_angle: float = 0.0              # Front wheel steer angle in degrees (+-28 deg)
        self.is_drifting: bool = False             # Powerslide drift active
        self.wheel_spin: float = 0.0               # Wheel pitch spin angle in degrees

        # Drift scoring & telemetry
        self.drift_score: int = 0
        self.current_drift_points: float = 0.0
        self.slip_angle_deg: float = 0.0
        self.rpm: float = 1200.0
        self.gear: str = "1"
        self.is_braking: bool = False

        # Twin tire-smoke particle emitters
        self.tire_smoke_left: ve.ParticleEmitter = ve.ParticleEmitter(160)
        self.tire_smoke_right: ve.ParticleEmitter = ve.ParticleEmitter(160)

        for emitter in (self.tire_smoke_left, self.tire_smoke_right):
            emitter.emission_rate = 0.0
            emitter.lifespan = 0.85
            emitter.start_size = 0.22
            emitter.end_size = 1.35
            emitter.start_color = Vec4(0.85, 0.88, 0.92, 0.55)
            emitter.end_color = Vec4(0.95, 0.95, 0.95, 0.0)
            emitter.velocity = Vec3(0.0, 0.75, 0.0)
            emitter.spread = Vec3(0.35, 0.25, 0.35)
            emitter.blend_mode = BlendMode.Alpha
            scene.add(emitter)

        # Primary alias matching MASTER_PLAN.md contract
        self.tire_smoke: ve.ParticleEmitter = self.tire_smoke_left

        self._sync_transforms()

    @property
    def speed_kmh(self) -> float:
        """Linear road speed in km/h."""
        return self.linear_velocity * 3.6

    def handle_controls(self, input_mgr: ve.InputManager, dt: float) -> None:
        """Process keyboard inputs (WASD, Arrow Keys, Space Handbrake)."""
        gas: float = 0.0
        brake: float = 0.0
        steer_input: float = 0.0
        handbrake: bool = False

        # Gas (W / Up)
        if input_mgr.is_key_down(Key.W) or input_mgr.is_key_down(Key.UP):
            gas = 1.0

        # Brake / Reverse (S / Down)
        if input_mgr.is_key_down(Key.S) or input_mgr.is_key_down(Key.DOWN):
            brake = 1.0

        # Steer (A / Left = Turn Left; D / Right = Turn Right)
        if input_mgr.is_key_down(Key.A) or input_mgr.is_key_down(Key.LEFT):
            steer_input += 1.0
        if input_mgr.is_key_down(Key.D) or input_mgr.is_key_down(Key.RIGHT):
            steer_input -= 1.0

        # Handbrake Drift (Space)
        if input_mgr.is_key_down(Key.SPACE):
            handbrake = True

        self._apply_inputs(gas, brake, steer_input, handbrake, dt)

    def _apply_inputs(self, gas: float, brake: float, steer_input: float, handbrake: bool, dt: float) -> None:
        """Core vehicle dynamics integration."""
        dt_safe = max(0.0001, min(0.05, dt))
        v = self.linear_velocity

        # 1. Front Wheel Steering Math (+-28 deg with speed-sensitive stability)
        speed_ratio = min(1.0, max(0.0, abs(v) / MAX_SPEED_MS))
        speed_steer_scale = max(0.38, 1.0 - speed_ratio * 0.62)
        target_steer = steer_input * MAX_STEER_DEG * speed_steer_scale

        steer_rate = 14.0 if steer_input != 0.0 else 18.0
        self.steer_angle += (target_steer - self.steer_angle) * min(1.0, steer_rate * dt_safe)

        # 2. Longitudinal Acceleration & Braking
        self.is_braking = False
        if gas > 0.0:
            if v >= -0.5:
                # Forward drive power curve
                torque_factor = max(0.0, 1.0 - (v / MAX_SPEED_MS) ** 1.35)
                self.linear_velocity += ACCELERATION * torque_factor * gas * dt_safe
            else:
                # Decelerate reverse motion
                self.linear_velocity += BRAKING_DECEL * gas * dt_safe

        if brake > 0.0:
            if v > 0.4:
                # Progressive forward braking
                self.linear_velocity = max(0.0, self.linear_velocity - BRAKING_DECEL * brake * dt_safe)
                self.is_braking = True
            else:
                # Reverse drive
                rev_torque = max(0.0, 1.0 - (abs(v) / abs(MAX_REVERSE_MS)))
                self.linear_velocity = max(MAX_REVERSE_MS, self.linear_velocity - REVERSE_ACCEL * rev_torque * brake * dt_safe)

        # Passive rolling resistance & drag
        if gas == 0.0 and brake == 0.0:
            if abs(self.linear_velocity) > 0.05:
                drag = ROLLING_RESISTANCE * dt_safe
                if self.linear_velocity > 0.0:
                    self.linear_velocity = max(0.0, self.linear_velocity - drag)
                else:
                    self.linear_velocity = min(0.0, self.linear_velocity + drag)
            else:
                self.linear_velocity = 0.0

        # Dynamic Taillight Glow
        if self.is_braking or (brake > 0.0 and self.linear_velocity > 0.0):
            self.taillight_mat.base_color = (1.0, 0.08, 0.08, 1.0)
            self.taillight_mat.emissive_color = (1.0, 0.05, 0.05, 1.0)
            self.taillight_mat.emissive_intensity = 4.2
        else:
            self.taillight_mat.base_color = (0.65, 0.06, 0.06, 1.0)
            self.taillight_mat.emissive_color = (0.55, 0.03, 0.03, 1.0)
            self.taillight_mat.emissive_intensity = 1.0

        # 3. Cornering, Lateral Friction & Centrifugal Handbrake Drift
        wheelbase = 2.65
        steer_rad = math.radians(self.steer_angle)

        if not handbrake:
            # High-grip road traction
            target_ang_vel = (self.linear_velocity / wheelbase) * math.tan(steer_rad)
            self.angular_velocity += (target_ang_vel - self.angular_velocity) * min(1.0, 12.0 * dt_safe)
            # Rapid damping of sideways drift
            self.lateral_velocity *= max(0.0, 1.0 - 15.0 * dt_safe)
            self.is_drifting = False
        else:
            # Drop lateral tire friction, initiate powerslide drift!
            turn_dir = 1.0 if self.steer_angle > 0.5 else (-1.0 if self.steer_angle < -0.5 else (1.0 if self.angular_velocity >= 0 else -1.0))
            centrifugal_kick = 2.8 * turn_dir * (abs(self.linear_velocity) / 25.0)
            self.angular_velocity += centrifugal_kick * dt_safe
            # Accumulate lateral drift velocity
            self.lateral_velocity += self.angular_velocity * self.linear_velocity * 0.45 * dt_safe
            self.lateral_velocity *= max(0.0, 1.0 - 1.6 * dt_safe)

            self.slip_angle_deg = math.degrees(math.atan2(self.lateral_velocity, max(1.0, abs(self.linear_velocity))))
            if abs(self.slip_angle_deg) > 10.0 and abs(self.speed_kmh) > 22.0:
                self.is_drifting = True
                drift_mult = 1.0 + min(2.5, abs(self.slip_angle_deg) / 20.0)
                earned = abs(self.slip_angle_deg) * (abs(self.speed_kmh) / 20.0) * drift_mult * 10.0 * dt_safe
                self.current_drift_points += earned
                self.drift_score += int(earned)
            else:
                self.is_drifting = False

        # Integrate heading angle
        self.heading += math.degrees(self.angular_velocity * dt_safe)
        self.heading %= 360.0

        # 4. Integrate World Position
        rad = math.radians(self.heading)
        # Forward vector (-sin, 0, -cos)
        fx, fz = -math.sin(rad), -math.cos(rad)
        # Right vector (cos, 0, -sin)
        rx, rz = math.cos(rad), -math.sin(rad)

        vx = fx * self.linear_velocity + rx * self.lateral_velocity
        vz = fz * self.linear_velocity + rz * self.lateral_velocity

        self.position.x += vx * dt_safe
        self.position.z += vz * dt_safe

        # 5. Wheel Spin & Steering Angles
        spin_delta_deg = (self.linear_velocity / WHEEL_RADIUS) * dt_safe * (180.0 / math.pi)
        self.wheel_spin = (self.wheel_spin + spin_delta_deg) % 360.0

        # Front wheels (0: FL, 1: FR) turn with steer_angle and spin
        self.wheels[0].transform.rotation = (self.wheel_spin, self.steer_angle, 0.0)
        self.wheels[1].transform.rotation = (self.wheel_spin, self.steer_angle, 0.0)
        # Rear wheels (2: RL, 3: RR) spin only
        self.wheels[2].transform.rotation = (self.wheel_spin, 0.0, 0.0)
        self.wheels[3].transform.rotation = (self.wheel_spin, 0.0, 0.0)

        # 6. Twin Tire Smoke Particle Emitters
        # Compute world positions of rear wheels for smoke spawn
        rear_offset_z = 1.4
        rear_offset_x = 0.95
        smoke_lx = self.position.x - fx * rear_offset_z - rx * rear_offset_x
        smoke_lz = self.position.z - fz * rear_offset_z - rz * rear_offset_x
        smoke_rx = self.position.x - fx * rear_offset_z + rx * rear_offset_x
        smoke_rz = self.position.z - fz * rear_offset_z + rz * rear_offset_x

        self.tire_smoke_left.set_position(smoke_lx, self.position.y + 0.08, smoke_lz)
        self.tire_smoke_right.set_position(smoke_rx, self.position.y + 0.08, smoke_rz)

        should_smoke = self.is_drifting or (self.is_braking and abs(self.speed_kmh) > 35.0)
        if should_smoke:
            smoke_rate = 85.0 if self.is_drifting else 50.0
            self.tire_smoke_left.emission_rate = smoke_rate
            self.tire_smoke_right.emission_rate = smoke_rate
        else:
            self.tire_smoke_left.emission_rate = 0.0
            self.tire_smoke_right.emission_rate = 0.0

        self.tire_smoke_left.update(dt_safe)
        self.tire_smoke_right.update(dt_safe)

        # 7. Tachometer & Dual-Clutch Gear Calculation
        self._update_telemetry(gas)
        self._sync_transforms()

    def update_dynamics(self, track_bounds: List[TrackSegment], dt: float) -> None:
        """Resolve collisions with track guardrails and align elevation with the road surface."""
        if not track_bounds:
            return

        # Find closest track segment
        best_seg = track_bounds[0]
        min_dist_sq = float("inf")
        px, pz = self.position.x, self.position.z

        for seg in track_bounds:
            dx = px - seg.center.x
            dz = pz - seg.center.z
            d2 = dx * dx + dz * dz
            if d2 < min_dist_sq:
                min_dist_sq = d2
                best_seg = seg

        # Track centerline elevation matching
        target_y = best_seg.center.y + WHEEL_RADIUS
        self.position.y += (target_y - self.position.y) * min(1.0, 15.0 * dt)

        # Guardrail collision check
        dx = self.position.x - best_seg.center.x
        dz = self.position.z - best_seg.center.z
        lat_dist = dx * best_seg.normal.x + dz * best_seg.normal.z

        max_lat = GUARDRAIL_OFFSET
        if abs(lat_dist) > max_lat:
            # Prevent driving off-world: bounce off guardrail
            sign = 1.0 if lat_dist > 0.0 else -1.0
            corrected_lat = sign * max_lat

            self.position.x = best_seg.center.x + best_seg.normal.x * corrected_lat
            self.position.z = best_seg.center.z + best_seg.normal.z * corrected_lat

            # Invert lateral momentum with restitution
            restitution = 0.35
            self.lateral_velocity = -self.lateral_velocity * restitution
            self.linear_velocity *= 0.82 # Kinetic impact energy loss

            # Align heading slightly parallel to track tangent
            tang_yaw = math.degrees(math.atan2(-best_seg.tangent.x, -best_seg.tangent.z))
            self.heading += (tang_yaw - self.heading) * min(1.0, 6.0 * dt)

        self._sync_transforms()

    def _update_telemetry(self, gas: float) -> None:
        """Compute realistic transmission gears and engine RPM."""
        spd = self.speed_kmh
        if spd < -0.5:
            self.gear = "R"
            self.rpm = 1200.0 + (abs(spd) / 35.0) * 5500.0
        elif abs(spd) < 1.0 and gas == 0.0:
            self.gear = "N"
            self.rpm = 950.0 + 100.0 * math.sin(time.time() * 8.0)
        elif spd < 38.0:
            self.gear = "1"
            self.rpm = 1200.0 + (max(0.0, spd) / 38.0) * 6200.0
        elif spd < 72.0:
            self.gear = "2"
            self.rpm = 3800.0 + ((spd - 38.0) / 34.0) * 3600.0
        elif spd < 108.0:
            self.gear = "3"
            self.rpm = 4200.0 + ((spd - 72.0) / 36.0) * 3300.0
        elif spd < 142.0:
            self.gear = "4"
            self.rpm = 4500.0 + ((spd - 108.0) / 34.0) * 3100.0
        elif spd < 168.0:
            self.gear = "5"
            self.rpm = 4800.0 + ((spd - 142.0) / 26.0) * 2800.0
        else:
            self.gear = "6"
            self.rpm = 5200.0 + ((min(180.0, spd) - 168.0) / 12.0) * 2300.0

        if gas > 0.0 and self.rpm > 7400.0:
            # Rev limiter bounce
            self.rpm += math.sin(time.time() * 45.0) * 180.0

    def _sync_transforms(self) -> None:
        """Propagate position and heading yaw to root entity hierarchy."""
        self.root.transform.position = (self.position.x, self.position.y, self.position.z)
        self.root.transform.rotation = (0.0, self.heading, 0.0)
        self.root.update_world_matrix()


# ---------------------------------------------------------------------------
# Dynamic Cameras (Chase Camera with Speed FOV-Zoom & Showroom Turntable)
# ---------------------------------------------------------------------------

class ChaseCamera:
    """Mode 1: Dynamic Third-Person Chase Camera with smooth spring damping

    and high-speed FOV speed-zoom (55 deg to 71 deg at 180 km/h).
    """

    def __init__(self, camera: ve.Camera) -> None:
        self.camera: ve.Camera = camera
        self.current_pos: List[float] = [0.0, 3.0, 55.0]
        self.current_target: List[float] = [0.0, 1.2, 45.0]
        self.current_fov: float = 55.0

        self.distance: float = 7.0
        self.height: float = 2.6
        self.look_height: float = 1.15
        self.look_ahead: float = 4.2
        self.stiffness: float = 12.0
        self.base_fov: float = 55.0
        self.max_fov: float = 71.0

    def update(self, car: RaceCar, dt: float) -> None:
        rad = math.radians(car.heading)
        fx = -math.sin(rad)
        fz = -math.cos(rad)

        # Ideal camera trailing position
        ideal_x = car.position.x - fx * self.distance
        ideal_y = car.position.y + self.height
        ideal_z = car.position.z - fz * self.distance

        # Ideal look-at target ahead of car
        target_x = car.position.x + fx * self.look_ahead
        target_y = car.position.y + self.look_height
        target_z = car.position.z + fz * self.look_ahead

        # Smooth exponential spring interpolation
        factor = 1.0 - math.exp(-max(0.001, dt) * self.stiffness)
        self.current_pos[0] += (ideal_x - self.current_pos[0]) * factor
        self.current_pos[1] += (ideal_y - self.current_pos[1]) * factor
        self.current_pos[2] += (ideal_z - self.current_pos[2]) * factor

        self.current_target[0] += (target_x - self.current_target[0]) * factor
        self.current_target[1] += (target_y - self.current_target[1]) * factor
        self.current_target[2] += (target_z - self.current_target[2]) * factor

        # FOV Speed-Zoom (stretching peripheral vision for blazing speed sensation)
        speed_factor = min(1.0, max(0.0, abs(car.speed_kmh) / 180.0))
        target_fov = self.base_fov + speed_factor * (self.max_fov - self.base_fov)
        fov_factor = 1.0 - math.exp(-max(0.001, dt) * 6.0)
        self.current_fov += (target_fov - self.current_fov) * fov_factor

        self.camera.set_position(self.current_pos[0], self.current_pos[1], self.current_pos[2])
        self.camera.set_target(self.current_target[0], self.current_target[1], self.current_target[2])
        self.camera.fov = self.current_fov


# ---------------------------------------------------------------------------
# Main Racing Simulator Application Facade
# ---------------------------------------------------------------------------

class RacingSimulatorApp:
    """Master controller managing Game Loop, Telemetry HUD, Post-Processing,

    Audio Cues, and Automated Self-Play verification.
    """

    def __init__(self, width: int = 1280, height: int = 720, self_play: bool = False, max_test_frames: int = 120) -> None:
        self.width: int = width
        self.height: int = height
        self.self_play: bool = self_play
        self.max_test_frames: int = max_test_frames
        self.frame_counter: int = 0

        # 1. Initialize Engine App
        self.app: App = App(
            title="Velocity 3D Engine | Racing Simulator",
            width=width,
            height=height,
            clear_color="#0e131d",
            show_crosshair=False,
            vsync=True,
        )
        self.scene: ve.Scene = self.app.scene

        # 2. Lighting & Environment Cubemap for Glossy PBR Reflections
        self.scene.set_sun(direction=(-0.85, -1.9, -1.1), color=WARM_WHITE, intensity=1.65)
        sky_cube = CubeTexture.create_gradient(
            top_color=Vec3(0.12, 0.42, 0.88),       # Azure sky
            horizon_color=Vec3(0.78, 0.86, 0.96),   # Bright horizon
            bottom_color=Vec3(0.14, 0.22, 0.16),    # Grass ambiance
            size=128,
        )
        self.scene.set_environment(sky_cube, 1.35)
        self.scene.set_background_cube(sky_cube)

        # 3. Ground Infield & Outfield Grass
        ground = self.scene.create_entity("OutfieldGrass")
        ground.mesh = Mesh.create_plane(width=650.0, depth=650.0, subdivisions_x=2, subdivisions_z=2)
        mat_ground = StandardMaterial()
        mat_ground.base_color = (0.16, 0.32, 0.18, 1.0) # Lush grass green
        mat_ground.roughness = 0.92
        mat_ground.metallic = 0.02
        ground.material = mat_ground
        ground.transform.position = (60.0, -0.05, 20.0)

        # 4. Construct Closed Circuit Track & Checkpoint Gantries
        self.track: RaceTrack = RaceTrack(self.scene)

        # 5. Build 3D Sports Car
        self.car: RaceCar = RaceCar(self.scene, start_pos=(0.0, 0.35, 45.0), start_heading=0.0)

        # 6. Post-Processing Stack (Bloom + ACESFilmic Tonemapping)
        self.composer: EffectComposer = EffectComposer(self.app.width, self.app.height)
        self.bloom_pass: BloomPass = BloomPass(threshold=0.72, strength=1.45, radius=0.6)
        self.tonemap_pass: TonemappingPass = TonemappingPass(mode=TonemappingMode.ACESFilmic, exposure=1.05)
        self.composer.add_pass(self.bloom_pass)
        self.composer.add_pass(self.tonemap_pass)
        self.app.composer = self.composer

        # 7. Camera Systems (Mode 1: Dynamic Chase; Mode 2: Showroom Turntable)
        self.camera_mode: int = 1 # 1 = Chase, 2 = Orbit
        self.chase_cam: ChaseCamera = ChaseCamera(self.app._core.camera)
        self.orbit_ctrl: OrbitController = OrbitController(
            target=(self.car.position.x, self.car.position.y + 0.8, self.car.position.z),
            distance=7.5,
            min_distance=3.0,
            max_distance=25.0,
            pitch=18.0,
        )
        self.prev_c_down: bool = False

        # Hook Frame Update Loop
        self.app.on_update(self.update)

    def toggle_camera_mode(self) -> None:
        """Toggle between Mode 1 (Dynamic Chase) and Mode 2 (Showroom Turntable)."""
        if self.camera_mode == 1:
            self.camera_mode = 2
            self.orbit_ctrl.target = (self.car.position.x, self.car.position.y + 0.8, self.car.position.z)
            self.app.camera = self.orbit_ctrl
        else:
            self.camera_mode = 1
            self.app.camera = None # Revert to direct camera control

    def update(self, dt: float) -> None:
        """Main game frame update callback."""
        self.frame_counter += 1
        dt_safe = max(0.0001, min(0.05, dt))

        # Checkpoint lap timing
        if self.track.lap_started:
            self.track.current_lap_time += dt_safe

        # Input handling
        if self.self_play:
            self._update_self_play(dt_safe)
        else:
            self.car.handle_controls(self.app.input, dt_safe)

            # Camera toggle key 'C'
            c_down = self.app.input.is_key_down(Key.C)
            if c_down and not self.prev_c_down:
                self.toggle_camera_mode()
            self.prev_c_down = c_down

        # Physics collision with track bounds
        self.car.update_dynamics(self.track.segments, dt_safe)

        # Checkpoint detection
        cp_triggered = self.track.check_checkpoint(self.car.position)
        if cp_triggered is not None:
            try:
                self.app.audio.play_jump() # Audio confirmation
            except Exception:
                pass

        # Camera updates
        if self.camera_mode == 1:
            self.chase_cam.update(self.car, dt_safe)
        else:
            self.orbit_ctrl.target = (self.car.position.x, self.car.position.y + 0.8, self.car.position.z)
            # Subtle turntable auto-rotation
            if not self.app.input.is_mouse_down(0):
                self.orbit_ctrl.yaw += 18.0 * dt_safe

        # Render 2D Telemetry HUD
        self.draw_hud()

        # Headless automated testing limit
        if (self.self_play or "--test" in sys.argv or "--headless" in sys.argv) and self.frame_counter >= self.max_test_frames:
            self.app.close()

    def _update_self_play(self, dt: float) -> None:
        """Automated AI pilot guiding the car along the spline for CI testing."""
        # Lookahead along spline
        lookahead_t = ((self.frame_counter * 0.004) + 0.02) % 1.0
        target_pt = self.track.spline.get_point(lookahead_t)

        dx = target_pt.x - self.car.position.x
        dz = target_pt.z - self.car.position.z
        desired_yaw = math.degrees(math.atan2(-dx, -dz))

        diff = desired_yaw - self.car.heading
        while diff > 180.0:
            diff -= 360.0
        while diff < -180.0:
            diff += 360.0

        steer_input = max(-1.0, min(1.0, diff / 25.0))
        gas = 1.0

        # Simulate drift powerslide between frames 45 and 75
        handbrake = (45 <= self.frame_counter <= 75)

        self.car._apply_inputs(gas=gas, brake=0.0, steer_input=steer_input, handbrake=handbrake, dt=dt)

    def draw_hud(self) -> None:
        """Render high-contrast 2D telemetry HUD overlay."""
        ui = self.app.ui
        ui.clear()
        w = max(640, self.app.width)
        h = max(480, self.app.height)

        # 1. Header & Controls
        ui.draw_text("VELOCITY RACING SIMULATOR", 24, 22, size=18, color=WARM_WHITE)
        ui.draw_text("[W/Up] Gas  [S/Down] Brake/Rev  [A/D] Steer  [Space] Drift  [C] Camera", 24, 46, size=12, color=Color(0.72, 0.78, 0.88, 1.0))

        # 2. Lap & Timing Card (Top-Right)
        card_w, card_h = 280, 80
        cx = w - card_w - 24
        ui.draw_rect(cx, 18, card_w, card_h, color=Color(0.06, 0.09, 0.14, 0.82))
        ui.draw_text(f"LAP: {self.track.current_lap} / 3", cx + 14, 26, size=15, color=YELLOW)

        cur_time_str = self._format_lap_time(self.track.current_lap_time)
        best_time_str = self._format_lap_time(self.track.best_lap) if self.track.best_lap < 999.0 else "--:--.--"
        ui.draw_text(f"TIME: {cur_time_str}", cx + 14, 46, size=14, color=WHITE)
        ui.draw_text(f"BEST: {best_time_str}", cx + 14, 66, size=13, color=CYAN if self.track.best_lap < 999.0 else Color(0.6, 0.6, 0.6, 1.0))

        # Sector indicators (4 dots)
        for s_idx in range(4):
            dot_x = cx + card_w - 65 + s_idx * 14
            dot_col = GREEN if s_idx < self.track.next_checkpoint_idx else Color(0.35, 0.38, 0.42, 1.0)
            ui.draw_rect(dot_x, 26, 9, 9, color=dot_col)

        # 3. Dynamic Drift Banner (Center)
        if self.car.is_drifting:
            ui.draw_text(">> DRIFT POWERSLIDE <<", w * 0.5 - 110, 110, size=24, color=MAGENTA)
            ui.draw_text(f"+{int(self.car.current_drift_points)} PTS  ({abs(self.car.slip_angle_deg):.0f} deg)", w * 0.5 - 75, 142, size=16, color=YELLOW)

        # Permanent Total Drift Score
        ui.draw_text(f"DRIFT SCORE: {self.car.drift_score:,}", 24, 68, size=14, color=MAGENTA)

        # 4. Speedometer, Tachometer & Gear Cluster (Bottom-Right)
        clus_w, clus_h = 260, 155
        bx = w - clus_w - 24
        by = h - clus_h - 24
        ui.draw_rect(bx, by, clus_w, clus_h, color=Color(0.05, 0.07, 0.12, 0.88))

        # Digital Speed Readout
        spd = int(abs(self.car.speed_kmh))
        ui.draw_text(f"{spd:3d}", bx + 22, by + 12, size=46, color=WHITE)
        ui.draw_text("KM/H", bx + 130, by + 34, size=15, color=CYAN)

        # Analog Speed Bar (0 to 180 km/h)
        speed_pct = min(1.0, max(0.0, spd / 180.0))
        bar_w = 216.0
        bar_fill = bar_w * speed_pct
        speed_col = GREEN if speed_pct < 0.5 else (YELLOW if speed_pct < 0.82 else RED)
        ui.draw_rect(bx + 22, by + 68, bar_w, 10, color=Color(0.18, 0.22, 0.28, 1.0))
        if bar_fill > 1.0:
            ui.draw_rect(bx + 22, by + 68, bar_fill, 10, color=speed_col)

        # Gear Box & Character
        ui.draw_rect(bx + 22, by + 90, 48, 52, color=Color(0.14, 0.18, 0.25, 1.0))
        gear_col = RED if self.car.gear == "R" else YELLOW
        ui.draw_text(self.car.gear, bx + 36, by + 98, size=30, color=gear_col)
        ui.draw_text("GEAR", bx + 30, by + 130, size=9, color=Color(0.7, 0.75, 0.8, 1.0))

        # Tachometer RPM Bar
        ui.draw_text(f"RPM: {int(self.car.rpm):,}", bx + 84, by + 94, size=13, color=WHITE)
        rpm_pct = min(1.0, max(0.0, self.car.rpm / 8000.0))
        rpm_fill = 154.0 * rpm_pct
        ui.draw_rect(bx + 84, by + 116, 154, 8, color=Color(0.18, 0.22, 0.28, 1.0))
        if rpm_fill > 1.0:
            rpm_col = Color(1.0, 0.2, 0.1, 1.0) if rpm_pct > 0.85 else Color(1.0, 0.65, 0.1, 1.0)
            ui.draw_rect(bx + 84, by + 116, rpm_fill, 8, color=rpm_col)

        # 5. Camera Mode Indicator (Bottom-Left)
        cam_mode_str = "CHASE (FOV Speed-Zoom)" if self.camera_mode == 1 else "SHOWROOM (Turntable Orbit)"
        ui.draw_text(f"CAM: {cam_mode_str}  [Press C to switch]", 24, h - 36, size=12, color=Color(0.65, 0.72, 0.82, 1.0))

    @staticmethod
    def _format_lap_time(seconds: float) -> str:
        """Format seconds into MM:SS.ss string."""
        if math.isinf(seconds) or seconds < 0.0:
            return "--:--.--"
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins:02d}:{secs:05.2f}"

    def run(self) -> None:
        """Execute the interactive or self-play simulation loop."""
        self.app.run()


def run_example(headless: bool = False, frames: int = 120) -> RacingSimulatorApp:
    """Entry point for standalone execution and automated test runners."""
    sim = RacingSimulatorApp(width=1280, height=720, self_play=headless, max_test_frames=frames)
    sim.run()
    return sim


if __name__ == "__main__":
    is_test = ("--test" in sys.argv) or ("--headless" in sys.argv)
    test_frames = 120
    for idx, arg in enumerate(sys.argv):
        if arg == "--frames" and idx + 1 < len(sys.argv):
            try:
                test_frames = int(sys.argv[idx + 1])
            except ValueError:
                pass

    run_example(headless=is_test, frames=test_frames)
