# Examples & Games Catalog

Velocity 3D Engine includes a rich curriculum of educational code examples and two complete standalone production-grade games demonstrating the engine's subsystems.

---

## 🎮 Included Full Games

### 1. Dungeon Crawler (`games/dungeon_crawler.py`)
A third-person action RPG set in a dark subterranean crypt.

```powershell
python games/dungeon_crawler.py
```

- **Rigged Player Character**: Full glTF animated knight model with bone hierarchy, walk, run, and attack animations.
- **Modular Weaponry**: Custom 3D modeled broadsword with gilded crossguard, brass pommel, and leather scabbard attached to the hip joint.
- **Procedural PBR Materials**: High-resolution ashlar masonry walls, normal-mapped flagstone floors, and iron-banded treasure chests.
- **RPG HUD**: Real-time health and stamina bars, collected gold and key counters, and minimap card.
- **Spatial Audio & Ambience**: Atmospheric dungeon soundtrack, footstep cues, chest interaction sounds, and torch flame lighting.

---

### 2. Space Combat Arena (`games/space_combat_arena.py`)
A high-speed 6DOF space flight combat simulation.

```powershell
python games/space_combat_arena.py
```

- **Starfighter Flight Model**: 6-degrees-of-freedom inertial physics with pitch, yaw, roll, and booster acceleration.
- **Asteroid Belt**: Procedurally generated asteroid field with diverse scales and orientations rendered via `InstancedMesh`.
- **Cosmic Environment**: Deep space nebula skybox, volumetric particle thrusters, and laser projectile physics.
- **Cockpit Avionics**: Sci-fi flight HUD with velocity meter, boost capacitor gauge, hull/shield monitors, and 2D radar tracking.

---

## 📚 Curriculum Educational Examples

### Part 1: Core Foundation & Shading

#### `01_hello_pbr.py` — Physically Based Rendering Matrix
- **Path**: `examples/01_hello_pbr.py`
- **Command**: `python examples/01_hello_pbr.py`
- **Key Concepts**: 5x5 grid of PBR spheres demonstrating a smooth 2D gradient of `metallic` ($0.0 \to 1.0$) and `roughness` ($0.0 \to 1.0$), Image-Based Lighting (IBL) environment reflection, and `OrbitController`.

#### `02_dynamic_lights_bloom.py` — Multi-Light Arena & HDR Bloom
- **Path**: `examples/02_dynamic_lights_bloom.py`
- **Command**: `python examples/02_dynamic_lights_bloom.py`
- **Key Concepts**: 16 orbiting multi-colored `PointLight` emitters, overhead `SpotLight`, high-luminance emissive pillars, and `BloomPass` HDR glow post-processing.

#### `03_skeletal_character.py` — Rigged Character & Crossfading
- **Path**: `examples/03_skeletal_character.py`
- **Command**: `python examples/03_skeletal_character.py`
- **Key Concepts**: Rigged `Soldier.glb` glTF character, `AnimationMixer` crossfading between Idle and Run clips, `FollowCamera` spring-arm tracking, and obstacle collisions.

#### `04_numpy_wave_surface.py` — NumPy Dynamic Buffer Updates
- **Path**: `examples/04_numpy_wave_surface.py`
- **Command**: `python examples/04_numpy_wave_surface.py`
- **Key Concepts**: High-density 100,000+ vertex polygon grid, high-speed procedural sine wave deformation evaluated via NumPy SIMD, and `mesh.update_vertices_from_numpy()` GPU buffer streaming.

#### `05_custom_shader_water.py` — Custom ShaderMaterial & Uniforms
- **Path**: `examples/05_custom_shader_water.py`
- **Command**: `python examples/05_custom_shader_water.py`
- **Key Concepts**: Writing custom vertex and fragment shaders in GLSL, passing time and wave frequency uniforms, and simulating buoyant objects floating on procedural waves.

---

### Part 2: Advanced Rendering & Instancing

#### `06_render_to_texture_portal.py` — Offscreen RenderTarget & CCTV
- **Path**: `examples/06_render_to_texture_portal.py`
- **Command**: `python examples/06_render_to_texture_portal.py`
- **Key Concepts**: Offscreen `RenderTarget` (512x512), secondary security camera rendering an offscreen scene pass, and mapping the resulting texture onto an in-game TV monitor.

#### `07_particles_and_sprites.py` — Particle Systems & Billboards
- **Path**: `examples/07_particles_and_sprites.py`
- **Command**: `python examples/07_particles_and_sprites.py`
- **Key Concepts**: Campfire `ParticleEmitter` with additive flame sparks and rising alpha smoke, weather rain simulation, and 3D camera-facing `Sprite` billboards.

#### `08_instanced_forest.py` — 50,000 Instanced Meshes & LOD
- **Path**: `examples/08_instanced_forest.py`
- **Command**: `python examples/08_instanced_forest.py`
- **Key Concepts**: High-throughput rendering of 35,000 pine trees and 15,000 rocks in a single GPU draw call using `InstancedMesh`, combined with multi-tier `LOD` mesh switching.

#### `09_curves_and_rollercoaster.py` — Splines & Procedural Tube Extrusion
- **Path**: `examples/09_curves_and_rollercoaster.py`
- **Command**: `python examples/09_curves_and_rollercoaster.py`
- **Key Concepts**: Closed `CatmullRomCurve3` 3D spline, procedural `Mesh.create_tube()` geometry generation, rail pillars, and animating a coaster cart along curve tangents.

#### `10_fps_game_sandbox.py` — First-Person Shooting Gallery
- **Path**: `examples/10_fps_game_sandbox.py`
- **Command**: `python examples/10_fps_game_sandbox.py`
- **Key Concepts**: `FirstPersonController` navigation, mouse lock, 3D raycasting against moving targets, score tracking via `UIOverlay` HUD, and F2 toggle to `Mode.EDITOR`.

---

### Part 3: Foundational Curriculum

| Example File | Key Subsystems Demonstrated |
|:---|:---|
| `01_window.py` | Minimal window initialization, clear color, and clean shutdown. |
| `02_rotating_cube.py` | Polygon cube creation, per-frame delta time animation, and transform updates. |
| `03_scene_lighting.py` | Directional and ambient light setup with specular material response. |
| `04_textured_material.py` | Loading image files into GPU textures, UV scale, and wrap modes. |
| `05_load_model.py` | Loading glTF 2.0 models (`duck.glb`), hierarchy parsing, and auto-centering. |
| `06_playable_demo.py` | First-person controller with jumping, gravity, and obstacle collision boxes. |
| `07_editor_mode.py` | Toggling `Mode.EDITOR`, Dear ImGui scene graph tree, and 3D transform gizmos. |
| `08_model_viewer.py` | Inspection model viewer with `OrbitController`, floor grid, and sun direction. |
| `09_interactive_sandbox.py` | Physics raycasting, dynamic box spawning on click, and hover highlights. |
| `10_showcase.py` | Master showcase combining PBR materials, directional shadows, and bloom. |
| `11_crossy_duck.py` | Crossy Duck voxel minigame with procedural traffic lanes and water logs. |
| `12_phase2_pbr_helmet.py` | Verification scene for glTF DamagedHelmet reference asset with normal maps. |
| `13_phase5_curves_helpers_wave.py` | Spline curves, procedural tube geometry, and debug helpers. |
