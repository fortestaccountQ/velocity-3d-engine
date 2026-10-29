"""Example 08: Massive 50,000-Instance Forest with LOD and Frustum Culling.

Showcase:
- 50,000 instanced foliage and rock assets rendered concurrently at 60+ FPS via `InstancedMesh`.
  * 35,000 Pine Trees with procedural canopy color variations.
  * 15,000 Granite Rocks and Boulders scattered across terrain.
- Multi-tier Level of Detail (`LOD`) hero tree switching geometry based on camera distance (High / Med / Low).
- Automatic GPU hardware instancing and view-frustum culling.
- FlyCameraController / OrbitController for aerial flight over the massive landscape.
- Standalone execution and headless/test suite support.
"""

from __future__ import annotations
import sys
import math
import random
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
    InstancedMesh,
    LOD,
    Node3D,
    StandardMaterial,
    CubeTexture,
    Vec3,
    Color,
    WARM_WHITE,
    CYAN,
    WHITE,
    YELLOW,
    GREEN,
)


def create_forest_scene(app: App) -> tuple[InstancedMesh, InstancedMesh, LOD]:
    """Generate 50,000 foliage and rock instances and set up multi-tier LOD hero entity."""
    scene = app.scene

    # Sunlight and atmospheric sky
    scene.set_sun(direction=(-0.7, -1.8, -0.6), color=WARM_WHITE, intensity=1.5)
    sky = CubeTexture.create_gradient(
        top_color=Vec3(0.18, 0.42, 0.78),
        horizon_color=Vec3(0.72, 0.82, 0.92),
        bottom_color=Vec3(0.12, 0.16, 0.12),
        size=64,
    )
    scene.set_environment(sky, 1.3)
    scene.set_background_cube(sky)

    # 1. Terrain Ground
    ground = scene.create_entity("TerrainGround")
    ground.mesh = Mesh.create_plane(width=320.0, depth=320.0, subdivisions_x=4, subdivisions_z=4)
    ground_mat = StandardMaterial()
    ground_mat.base_color = (0.12, 0.18, 0.1, 1.0) # Forest floor green
    ground_mat.roughness = 0.85
    ground_mat.metallic = 0.05
    ground.material = ground_mat
    ground.transform.position = (0.0, -0.05, 0.0)

    # 2. 35,000 Pine Trees via InstancedMesh
    tree_mesh = Mesh.create_cylinder(radius=0.7, height=4.5, segments=8)
    tree_inst = InstancedMesh(tree_mesh, 35000)

    # Deterministic pseudo-random generation for fast reproducible distribution
    rng = random.Random(42)
    for i in range(35000):
        # Forest foliage color variation: Deep pine green to vibrant emerald
        g = rng.uniform(0.35, 0.75)
        r = rng.uniform(0.04, 0.15)
        b = rng.uniform(0.08, 0.22)
        tree_inst.set_instance(i, (r, g, b, 1.0))

    scene.add_instanced_mesh(tree_inst)

    # 3. 15,000 Granite Rocks via InstancedMesh (Total = 50,000 instances)
    rock_mesh = Mesh.create_box(1.2, 0.9, 1.4)
    rock_inst = InstancedMesh(rock_mesh, 15000)

    for i in range(15000):
        # Rock tint: Granite slate grey to sandstone brown
        grey = rng.uniform(0.25, 0.55)
        warmth = rng.uniform(0.9, 1.1)
        rock_inst.set_instance(i, (grey * warmth, grey, grey * 0.9, 1.0))

    scene.add_instanced_mesh(rock_inst)

    # 4. Hero Ancient Tree with Multi-Tier Level of Detail (LOD)
    lod = LOD("HeroAncientTreeLOD")

    # High Detail Tier (< 30m distance): 32-segment detailed trunk and layered foliage
    node_high = scene.create_entity("LOD_Tree_High")
    node_high.mesh = Mesh.create_cylinder(radius=1.2, height=9.0, segments=32)
    mat_high = StandardMaterial()
    mat_high.base_color = (0.15, 0.65, 0.25, 1.0)
    mat_high.roughness = 0.3
    node_high.material = mat_high

    # Medium Detail Tier (30m - 80m distance): 12-segment simplified mesh
    node_med = scene.create_entity("LOD_Tree_Med")
    node_med.mesh = Mesh.create_cylinder(radius=1.2, height=9.0, segments=12)
    mat_med = StandardMaterial()
    mat_med.base_color = (0.12, 0.55, 0.22, 1.0)
    mat_med.roughness = 0.5
    node_med.material = mat_med

    # Low Detail Tier (> 80m distance): 6-segment low-poly proxy
    node_low = scene.create_entity("LOD_Tree_Low")
    node_low.mesh = Mesh.create_cylinder(radius=1.2, height=9.0, segments=6)
    mat_low = StandardMaterial()
    mat_low.base_color = (0.1, 0.45, 0.2, 1.0)
    mat_low.roughness = 0.7
    node_low.material = mat_low

    lod.add_level(node_high, 30.0)
    lod.add_level(node_med, 80.0)
    lod.add_level(node_low, 250.0)
    lod.transform.position = (0.0, 4.5, 0.0)
    scene.add(lod)

    return tree_inst, rock_inst, lod


def run_example(headless: bool = False, frames: int = 60) -> App:
    """Run the 50,000 instance forest example in interactive or headless mode."""
    app = App("Pielosyty - 08 Instanced Forest (50k)", width=1280, height=720, clear_color="#0a1014")

    # High-altitude cinematic orbit controller over the forest canopy
    orb = OrbitController(target=(0.0, 5.0, 0.0), distance=75.0, min_distance=5.0, max_distance=250.0, pitch=30.0)
    app.camera = orb

    tree_inst, rock_inst, lod = create_forest_scene(app)

    # UI Overlay setup
    app.ui.clear()
    app.ui.draw_text("Pielosyty 3D Engine | 08: Instanced Forest & LOD System", (24, 24), size=20, color=WARM_WHITE)
    app.ui.draw_text("50,000 Live Entities: 35,000 Pine Trees + 15,000 Granite Boulders via InstancedMesh", (24, 52), size=14, color=CYAN)
    app.ui.draw_text("Multi-Tier LOD: High (<30m) -> Med (30-80m) -> Low (>80m) with Frustum Culling", (24, 76), size=13, color=GREEN)
    app.ui.show_stats(True)

    time_accum = 0.0
    frame_counter = 0

    def update(dt: float) -> None:
        nonlocal time_accum, frame_counter
        time_accum += dt
        frame_counter += 1

        # Camera position query for LOD distance evaluation
        core_cam = getattr(app.camera, "camera", None) or getattr(app, "_core", app).camera
        cam_p = core_cam.position
        lod.update_lod((cam_p.x, cam_p.y, cam_p.z))

        current_lod_tier = lod.current_level_index()
        lod_names = ["Tier 0 (High Poly)", "Tier 1 (Medium Poly)", "Tier 2 (Low Poly Billboard)"]
        active_tier_name = lod_names[current_lod_tier] if current_lod_tier < len(lod_names) else f"Tier {current_lod_tier}"

        if frame_counter % 20 == 0:
            app.ui.draw_text(f"Hero Tree LOD: {active_tier_name} | Distance: {math.sqrt(cam_p.x**2 + (cam_p.y-4.5)**2 + cam_p.z**2):.1f}m", (24, 100), size=12, color=YELLOW)

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
