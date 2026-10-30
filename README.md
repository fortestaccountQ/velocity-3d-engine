# Velocity 3D Engine

[ **English** | [Русский](docs/translations/README_ru.md) | [中文](docs/translations/README_zh.md) | [Español](docs/translations/README_es.md) | [Français](docs/translations/README_fr.md) | [العربية](docs/translations/README_ar.md) | [Deutsch](docs/translations/README_de.md) | [日本語](docs/translations/README_ja.md) | [Português](docs/translations/README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)](#project-status)

<a id="project-status"></a>
> [!WARNING]
> ### ⚠️ Project Status: Early Alpha / Work-in-Progress
> This engine is currently in an **early experimental alpha** stage. It is an active architectural proof-of-concept and technical foundation. Many subsystems are undergoing heavy iteration, APIs are subject to breaking changes, and significant modernization, refactoring, and optimizations are planned. **It is not yet production-ready.** However, a solid core foundation (C++20, Sokol GFX, nanobind, PBR, skeletal animation, and full test suite) is established and functional.

---

## 🌐 Documentation & Translations

The documentation for Velocity 3D Engine is available in the official UN languages and major global languages:

| Language | Document | Language | Document |
|:---|:---|:---|:---|
| 🇬🇧 **English** | [README.md](README.md) *(Original)* | 🇸🇦 **العربية** | [README_ar.md](docs/translations/README_ar.md) |
| 🇷🇺 **Русский** | [README_ru.md](docs/translations/README_ru.md) | 🇩🇪 **Deutsch** | [README_de.md](docs/translations/README_de.md) |
| 🇨🇳 **简体中文** | [README_zh.md](docs/translations/README_zh.md) | 🇯🇵 **日本語** | [README_ja.md](docs/translations/README_ja.md) |
| 🇪🇸 **Español** | [README_es.md](docs/translations/README_es.md) | 🇧🇷 **Português** | [README_pt.md](docs/translations/README_pt.md) |
| 🇫🇷 **Français** | [README_fr.md](docs/translations/README_fr.md) | | |

---

## 🌟 Highlights

**Velocity 3D Engine** combines the raw rendering performance of modern C++20 and [Sokol GFX](https://github.com/floooh/sokol) with the ergonomic expressiveness of Python via [nanobind](https://github.com/wjakob/nanobind).

- **High-Performance Core**: Written in modern C++20 with lightweight zero-overhead abstractions, GLM mathematics, and Sokol GFX (Direct3D 11, Metal, OpenGL).
- **Pythonic Ergonomics**: Complete Python bindings with PEP-484 / PEP-561 `.pyi` type stubs for IDE auto-completion. Supports operator overloading, context managers, and vector unpackings.
- **Physically Based Rendering (PBR)**: Metallic-roughness workflow (Cook-Torrance GGX microfacet specular, Lambertian diffuse, Sobel normal mapping, ambient occlusion, and emissive maps).
- **Skeletal Animation System**: glTF 2.0 skeletal loader with joint hierarchy propagation, inverse bind matrices, CPU linear blend skinning, and multi-clip animation blending.
- **Post-Processing Pipeline**: Modular `EffectComposer` supporting multi-pass post-processing: HDR Gaussian Bloom, ACES/Reinhard tonemapping, vignette, and custom GLSL/HLSL fullscreen shader passes.
- **Instanced Rendering**: High-throughput `InstancedMesh` pipeline capable of rendering tens of thousands of dynamic instances (e.g. asteroid fields, forests) with individual 4x4 transform matrices and instance tint colors.
- **2D HUD & Overlay Queue**: Integrated orthographic 2D rendering queue with built-in bitmap font atlas for on-screen debug stats, health gauges, and crosshairs.
- **Spatial Audio**: Integrated audio engine powered by `miniaudio` for sound effects, spatial 3D attenuation, and background ambience.
- **100% Automated Test Coverage**: Comprehensive suite of 420+ automated unit, integration, and stress tests verifying memory safety, handle lifecycles, and rendering math.

---

## 🎮 Included Playable Games & Demos

The repository includes five complete, standalone games demonstrating the engine's rendering, physics, audio, and gameplay capabilities:

### 1. 3D Mario Platformer (`examples/game_3d_mario.py`)
A vibrant third-person 3D obstacle course inspired by *Super Mario 64*:
- **Character Physics**: Responsive ground acceleration, variable-height jumping, double-jump somersault at peak, and airborne ground pound plunging.
- **Dynamic Level Architecture**: Floating grassy islands, sinusoidal moving platforms transferring velocity, spinning gold coins with scale-punch tweens, and breakable `?` blocks.
- **Summit Goal**: Radiant 5-pointed Power Star with emissive bloom, celebratory fanfare, and particle bursts.
- **Camera & HUD**: Third-person spring-arm `FollowCamera`, 2D HUD tracking Lives (`❤️ x 3`), Coins (`🪙`), Timer, and Score.

```powershell
python examples/game_3d_mario.py
```

### 2. 3D Racing Simulator (`examples/game_3d_racing.py`)
A high-speed arcade circuit racing and vehicle showcase simulator:
- **Sports Car Hierarchy**: Aerodynamic chassis, carbon splitter, GT rear wing, glowing headlights, and reactive taillights.
- **Steerable Axle & Drift Dynamics**: Front wheels yaw with steering (±28°), all 4 wheels spin proportional to road speed, handbrake drift mechanics, and twin tire-smoke particle emitters.
- **Circuit Track**: Closed 3D Catmull-Rom spline asphalt track with red-and-white rumble curbs, 4 checkpoint gates with sector split timing, and outer safety guardrails.
- **Avionics HUD**: Digital speedometer (km/h), 6-speed dual-clutch transmission indicator, RPM tachometer bar with redline warning, lap timer, and drift score counter.

```powershell
python examples/game_3d_racing.py
```

### 3. 3D Flappy Bird (`examples/game_3d_flappy_bird.py`)
The viral arcade classic reimagined in full 3D:
- **Flight Kinematics**: Instant flap impulse (`+8.5 m/s`), downward gravity ($g = 22.0$ m/s²), dynamic pitch tilt (diving down to -65°, climbing up to +25°), and articulated wing flap tweens.
- **Procedural Infinite Obstacles**: Streaming green cylindrical pipes with lip collars, randomized traversal gap (3.8 m), and infinite zero-leak buffer recycling.
- **Arcade Scoring & Audio**: Exact BoundingSphere 3D collision detection, crystal scoring chimes, impact screen shake, death tumble, and instant restart on Space.

```powershell
python examples/game_3d_flappy_bird.py
```

### 4. Dungeon Crawler (`games/dungeon_crawler.py`)
A third-person action RPG set in a dark subterranean crypt:
- **Animated Player Character**: Full glTF animated knight model with bone hierarchy and locomotion animations.
- **Modular Weaponry**: Custom 3D modeled broadsword with gilded crossguard, pommel, and leather scabbard attached to the hip.
- **Procedural PBR Materials**: High-resolution ashlar masonry walls, normal-mapped flagstone floors, and dark-oak iron-banded treasure chests.
- **RPG HUD**: Real-time health and stamina bars, collected gold, keys, relics counters, and minimap card.
- **Audio & Ambience**: Atmospheric dungeon soundtrack, footstep cues, chest interaction sounds, and torch flame lighting.

```powershell
python games/dungeon_crawler.py
```

### 5. Space Combat Arena (`games/space_combat_arena.py`)
A high-speed 6DOF space flight combat simulation:
- **Starfighter Flight Model**: 6-degrees-of-freedom inertial physics with pitch, yaw, roll, and booster acceleration.
- **Asteroid Belt**: Procedurally generated instanced asteroid field with 1,200 diverse asteroids rendered via `InstancedMesh`.
- **Cosmic Environment**: Deep space nebula skybox, volumetric particle thrusters, and laser projectile physics.
- **Cockpit Avionics**: Sci-fi flight HUD with velocity meter, boost capacitor gauge, hull and shield monitors, and 2D radar tracking.

```powershell
python games/space_combat_arena.py
```

---

## 📂 Repository Structure

```text
velocity-3d-engine/
├── assets/                     # 3D glTF/GLB models, textures, and normal maps
│   ├── textures/               # PBR diffuse, normal, and RGBA texture maps
│   ├── Soldier.glb             # Animated rigged character model
│   └── DamagedHelmet.glb       # Reference glTF PBR test model
├── bindings/                   # nanobind C++ -> Python bindings
│   ├── bindings.cpp            # Primary module entrypoint
│   ├── bind_app.cpp            # Application lifecycle and windowing
│   ├── bind_geometry.cpp       # Meshes, curves, points, instanced geometry
│   ├── bind_materials.cpp      # PBR, unlit, and custom shader materials
│   ├── bind_math.cpp           # Vec2/3/4, Quat, Euler, Mat3/4, Ray, Frustum
│   ├── bind_postprocess.cpp    # EffectComposer and post-processing passes
│   └── bind_scene.cpp          # Scene, Entity, Node3D, lights, cameras
├── core/                       # Core C++20 engine engine implementation
│   ├── include/engine/         # Public header files
│   └── src/                    # Engine source files
├── docs/                       # Comprehensive documentation suite (MkDocs Material)
│   ├── getting-started/        # Installation, Quickstart, Troubleshooting
│   ├── architecture/           # C++20 core, Sokol GFX pipeline, Scene Graph
│   ├── guides/                 # 10 deep developer guides (PBR, Skeletal, Audio, HUD, etc.)
│   ├── api-reference/          # Exhaustive Python & C++ API reference
│   ├── examples/               # Showcase curriculum index
│   ├── contributing/           # Contribution guidelines & code style
│   └── translations/           # Localized landing READMEs across 9 global languages
├── examples/                   # 16-example standardized curriculum + 3 standalone 3D games
│   ├── game_3d_mario.py        # 3D Mario Platformer (islands, coins, double-jump, star)
│   ├── game_3d_racing.py       # 3D Racing Simulator (sports car, steerable wheels, drift)
│   ├── game_3d_flappy_bird.py  # 3D Flappy Bird (kinematics, infinite pipes, scoring)
│   ├── 01_hello_window.py      # Window creation & background
│   ├── 02_rotating_cube.py     # PBR rotating cube
│   ├── 03_hello_pbr.py         # 5x5 metallic-roughness PBR sphere grid
│   ├── 04_dynamic_lights_bloom.py # Dynamic point lights & Bloom pass
│   ├── 05_skeletal_character.py # glTF rigged Soldier with dynamic skinning
│   ├── 06_interactive_sandbox.py # FPS controller & raycast picking
│   ├── 07_particles_and_sprites.py # Campfire particles & billboards
│   ├── 08_curves_rollercoaster.py # Spline tube track & banking camera
│   ├── 09_render_to_texture_portal.py # CCTV RenderTarget monitor
│   ├── 10_instanced_forest.py  # 50,000 scattered trees & rocks with LOD
│   ├── 11_water_surface.py     # Displaced wave water surface
│   ├── 12_numpy_wave.py        # 180x180 indexed grid running at 1300+ FPS
│   ├── 13_pbr_damaged_helmet.py # DamagedHelmet PBR test with lighting
│   ├── 14_fps_minigame.py      # FPS minigame with targets & audio
│   ├── 15_viral_cube_cannon.py # Bouncy cube cannon & duck reactions
│   ├── 16_visual_editor.py     # Dear ImGui editor, hierarchy & gizmos
│   └── legacy/                 # Archived historical PoC files
├── games/                      # Playable standalone games (Dungeon & Space)
├── python/                     # Python package implementations & type stubs
│   ├── VelocityEngine/         # Primary engine package
│   ├── velocity/               # Pythonic lowercase alias
│   └── pielosyty/              # Backwards-compatibility alias layer
├── scripts/                    # Utility and procedural texture generation tools
├── tests/                      # 420+ automated pytest test suites
├── third_party/                # Vendored dependencies (Sokol, GLM, ImGui, miniaudio)
├── CMakeLists.txt              # Primary CMake build system
└── pyproject.toml              # Scikit-build-core Python packaging configuration
```

---

## 🛠️ Building & Installation

### Prerequisites

- **CMake**: `>= 3.24`
- **C++20 Compiler**:
  - Windows: MSVC 2022 (v143) or Clang-CL
  - Linux: GCC `>= 12` or Clang `>= 15`
  - macOS: Apple Clang `>= 14`
- **Python**: `>= 3.10`
- **Build Tool**: Ninja (recommended) or MSBuild

### 1. Build and Install via Python (Editable Mode)

```powershell
# Clone the repository
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# Install build dependencies
pip install scikit-build-core nanobind ninja pytest numpy

# Compile the C++ core and install Python bindings
pip install -e . --no-build-isolation
```

### 2. Build via CMake Directly

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. Run Automated Tests

```powershell
pytest tests -q
```

---

## 💡 Quick Start Example

```python
import VelocityEngine as ve

# 1. Initialize application
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. Setup Camera
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. Add Directional & Ambient Lighting
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. Create PBR Material & Mesh
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. Run Application Loop
app.run()
```

---

## 🗺️ Roadmap & Known Limitations

As an early alpha, several key architectural improvements are planned:

- [ ] **GPU Compute Skinning**: Migrate from the current CPU linear blend skinning to GPU vertex shader / compute shader evaluation for high skeletal mesh counts.
- [ ] **Cascaded Shadow Maps (CSM)**: Support multi-frustum directional cascades for open-world outdoor scenes.
- [ ] **Shader Cross-Compilation**: Formalize automated offline GLSL/HLSL/MSL translation via `sokol-shdc`.
- [ ] **Physics Engine Integration**: Integrate Jolt Physics or PhysX for rigid-body simulation and collision response.
- [ ] **Vulkan & WebGPU Backends**: Add Vulkan and WebAssembly/WebGPU targets using Sokol GFX.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
Third-party libraries in [`third_party/`](third_party/) are subject to their respective open-source licenses (Sokol: zlib/libpng, GLM: Happy Bunny / MIT, ImGui: MIT, miniaudio: Public Domain / MIT-0).
