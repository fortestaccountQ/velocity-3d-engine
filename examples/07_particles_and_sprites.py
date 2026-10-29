"""Example 07: Campfire Particle Systems & 3D Sprite Billboards.

Showcase:
- Atmospheric nighttime campfire scene with multi-layered particle effects.
- `ParticleEmitter` producing rising fire embers/sparks with `BlendMode.Additive`.
- Rising smoke volume with alpha blending and expansion over lifespan.
- Surrounding rain weather particle system streaming down from the sky.
- Floating 3D overhead name tag and health bar using spherical `Sprite` billboards always facing the camera.
- Standalone execution and headless/test suite support.
"""

from __future__ import annotations
import sys
import math
from pathlib import Path
from typing import Optional

# Ensure package import
repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))

import pielosyty as ve
from pielosyty import (
    App,
    OrbitController,
    Mesh,
    StandardMaterial,
    SpriteMaterial,
    Sprite,
    ParticleEmitter,
    BlendMode,
    PointLight,
    Vec3,
    Vec4,
    Vec2,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
    GREEN,
    RED,
)


def create_campfire_scene(app: App) -> tuple[ParticleEmitter, ParticleEmitter, ParticleEmitter, list[Sprite], PointLight]:
    """Construct campfire logs, particle emitters, NPC character, and billboard sprites."""
    scene = app.scene

    # 1. Dark night atmosphere & ground
    scene.create_grid(size=50.0, step=1.0, color=Color.from_hex("#171c26"))

    ground = scene.create_entity("ForestGround")
    ground.mesh = Mesh.create_plane(width=45.0, depth=45.0, subdivisions_x=2, subdivisions_z=2)
    ground_mat = StandardMaterial()
    ground_mat.base_color = (0.1, 0.12, 0.14, 1.0)
    ground_mat.roughness = 0.8
    ground_mat.metallic = 0.1
    ground.material = ground_mat
    ground.transform.position = (0.0, 0.0, 0.0)

    # 2. Campfire logs arranged in circle around embers
    log_mesh = Mesh.create_cylinder(radius=0.18, height=1.6, segments=12)
    log_mat = StandardMaterial()
    log_mat.base_color = (0.35, 0.22, 0.12, 1.0)
    log_mat.roughness = 0.85
    log_mat.metallic = 0.05

    for i in range(6):
        angle = (2.0 * math.pi * i) / 6.0
        log = scene.create_entity(f"CampfireLog_{i}")
        log.mesh = log_mesh
        log.material = log_mat
        lx = math.cos(angle) * 0.7
        lz = math.sin(angle) * 0.7
        log.transform.position = (lx, 0.15, lz)
        log.transform.rotation = (25.0, math.degrees(-angle) + 90.0, 0.0)

    # Embers stone ring
    stone_mesh = Mesh.create_sphere(radius=0.25, rings=12, sectors=12)
    stone_mat = StandardMaterial()
    stone_mat.base_color = (0.2, 0.22, 0.25, 1.0)
    stone_mat.roughness = 0.9
    for i in range(10):
        angle = (2.0 * math.pi * i) / 10.0
        stone = scene.create_entity(f"RingStone_{i}")
        stone.mesh = stone_mesh
        stone.material = stone_mat
        stone.transform.position = (math.cos(angle) * 1.35, 0.12, math.sin(angle) * 1.35)

    # Flickering Campfire PointLight
    fire_light = PointLight("CampfireGlow", Vec3(1.0, 0.55, 0.15), 4.0, 14.0, 1.8)
    fire_light.transform.position = (0.0, 0.6, 0.0)
    scene.add_light(fire_light)

    # 3. ParticleEmitter: Rising Fire Sparks with Additive Blending
    sparks = ParticleEmitter(300)
    sparks.emission_rate = 75.0
    sparks.lifespan = 1.3
    sparks.velocity = Vec3(0.0, 3.2, 0.0)
    sparks.spread = Vec3(0.35, 0.8, 0.35)
    sparks.gravity = Vec3(0.0, 0.4, 0.0) # Thermal updraft
    sparks.start_color = Vec4(1.0, 0.85, 0.25, 1.0) # Bright golden spark
    sparks.end_color = Vec4(1.0, 0.1, 0.0, 0.0)     # Fading red-orange
    sparks.start_size = 0.22
    sparks.end_size = 0.04
    sparks.blend_mode = BlendMode.Additive
    sparks.set_position(0.0, 0.2, 0.0)
    scene.add(sparks)

    # 4. ParticleEmitter: Expanding Campfire Smoke
    smoke = ParticleEmitter(180)
    smoke.emission_rate = 28.0
    smoke.lifespan = 2.4
    smoke.velocity = Vec3(0.0, 2.0, 0.0)
    smoke.spread = Vec3(0.5, 0.4, 0.5)
    smoke.gravity = Vec3(0.1, 0.15, 0.0) # Slight drift
    smoke.start_color = Vec4(0.35, 0.35, 0.4, 0.65)
    smoke.end_color = Vec4(0.15, 0.16, 0.22, 0.0)
    smoke.start_size = 0.3
    smoke.end_size = 1.35
    smoke.blend_mode = BlendMode.Alpha
    smoke.set_position(0.0, 0.3, 0.0)
    scene.add(smoke)

    # 5. ParticleEmitter: Falling Rain
    rain = ParticleEmitter(1500)
    rain.emission_rate = 350.0
    rain.lifespan = 1.2
    rain.velocity = Vec3(0.0, -14.0, 0.0)
    rain.spread = Vec3(12.0, 1.0, 12.0)
    rain.gravity = Vec3(0.0, -9.8, 0.0)
    rain.start_color = Vec4(0.7, 0.82, 1.0, 0.45)
    rain.end_color = Vec4(0.4, 0.55, 0.85, 0.1)
    rain.start_size = 0.06
    rain.end_size = 0.06
    rain.blend_mode = BlendMode.Alpha
    rain.set_position(0.0, 15.0, 0.0)
    scene.add(rain)

    # 6. NPC Standing by the Fire
    npc = scene.create_entity("FireWatcherNPC")
    duck_path = repo_root / "assets" / "duck.glb"
    if duck_path.exists():
        duck_model = scene.load_model(str(duck_path))
        npc = duck_model.root_entity
        npc.transform.position = (2.4, 0.0, 0.0)
        npc.transform.scale = (1.4, 1.4, 1.4)
        npc.transform.rotation = (0.0, -90.0, 0.0)
    else:
        npc.mesh = Mesh.create_cylinder(radius=0.4, height=1.8, segments=16)
        npc_mat = StandardMaterial()
        npc_mat.base_color = (0.2, 0.7, 0.3, 1.0)
        npc.material = npc_mat
        npc.transform.position = (2.4, 0.9, 0.0)

    # 7. Overhead Billboard Sprites: Name Tag & Health Bar
    sprites: list[Sprite] = []

    # Name Tag Sprite
    name_mat = SpriteMaterial()
    name_mat.color = Vec4(1.0, 0.9, 0.2, 1.0) # Golden yellow nameplate
    name_sprite = Sprite(name_mat)
    name_sprite.set_position(2.4, 2.2, 0.0)
    name_sprite.scale = Vec2(1.2, 0.25)
    scene.add(name_sprite)
    sprites.append(name_sprite)

    # Health Bar Background (Dark Red)
    hp_bg_mat = SpriteMaterial()
    hp_bg_mat.color = Vec4(0.4, 0.05, 0.05, 0.8)
    hp_bg = Sprite(hp_bg_mat)
    hp_bg.set_position(2.4, 1.9, 0.0)
    hp_bg.scale = Vec2(1.0, 0.15)
    scene.add(hp_bg)
    sprites.append(hp_bg)

    # Health Bar Foreground (Vibrant Green)
    hp_mat = SpriteMaterial()
    hp_mat.color = Vec4(0.1, 0.9, 0.2, 1.0)
    hp_fg = Sprite(hp_mat)
    hp_fg.set_position(2.4, 1.9, 0.01)
    hp_fg.scale = Vec2(0.85, 0.13)
    scene.add(hp_fg)
    sprites.append(hp_fg)

    return sparks, smoke, rain, sprites, fire_light


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the particles & sprites campfire example in interactive or headless mode."""
    app = App("Pielosyty - 07 Particles & Sprites", width=1280, height=720, clear_color="#070a10")

    orb = OrbitController(target=(0.0, 1.0, 0.0), distance=9.5, min_distance=2.0, max_distance=25.0, pitch=20.0)
    app.camera = orb

    sparks, smoke, rain, sprites, fire_light = create_campfire_scene(app)

    # UI Overlay setup
    app.ui.clear()
    app.ui.draw_text("Pielosyty 3D Engine | 07: Particles & Sprites", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("Campfire Particles: Additive Sparks + Alpha Smoke + Falling Rain Emitter", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("Overhead Billboards: Spherical Camera-Facing Sprite Name Tag & Health Bar", (24, 76), size=13, color=YELLOW)
    app.ui.show_stats(True)

    time_accum = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        # Advance particle physics simulations
        sparks.update(dt)
        smoke.update(dt)
        rain.update(dt)

        # Dynamic flickering campfire lighting
        flicker = 3.6 + 0.9 * math.sin(time_accum * 16.0) * math.cos(time_accum * 11.0)
        fire_light.intensity = max(1.5, flicker)

        # Align billboard sprites facing active camera
        core_cam = getattr(app.camera, "camera", None) or getattr(app, "_core", app).camera
        for sp in sprites:
            sp.compute_billboard_matrix(core_cam)

        if (headless or "--test" in sys.argv or "--headless" in sys.argv) and frame_counter >= frames:
            app.close()

    app.on_update(update)

    if not headless and "--headless" not in sys.argv:
        app.run()
    else:
        for _ in range(frames):
            update(1.0 / 60.0)

    return app


if __name__ == "__main__":
    is_headless = "--headless" in sys.argv
    frame_limit = 60
    for idx, arg in enumerate(sys.argv):
        if arg == "--frames" and idx + 1 < len(sys.argv):
            try:
                frame_limit = int(sys.argv[idx + 1])
            except ValueError:
                pass

    run_example(headless=is_headless, frames=frame_limit)
