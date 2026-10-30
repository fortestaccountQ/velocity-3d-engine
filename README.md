# Velocity 3D Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)]()

> [!WARNING]
> ### ⚠️ Project Status: Early Alpha / Work-in-Progress
> This engine is currently in an **early experimental alpha** stage. It is an active architectural proof-of-concept and technical foundation. Many subsystems are undergoing heavy iteration, APIs are subject to breaking changes, and significant modernization, refactoring, and optimizations are planned. **It is not yet production-ready.** However, a solid core foundation (C++20, Sokol GFX, nanobind, PBR, skeletal animation, and full test suite) is established and functional.

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

## 🎮 Included Playable Demos

The repository includes two complete, standalone demo games in the [`games/`](games/) directory demonstrating the engine's capabilities:

### 1. Dungeon Crawler (`games/dungeon_crawler.py`)
A third-person action RPG set in a dark subterranean crypt:
- **Animated Player Character**: Full glTF animated knight model with bone hierarchy and locomotion animations.
- **Modular Weaponry**: Custom 3D modeled broadsword with gilded crossguard, pommel, and leather scabbard attached to the hip.
- **Procedural PBR Materials**: High-resolution ashlar masonry walls, normal-mapped flagstone floors, and dark-oak iron-banded treasure chests.
- **RPG HUD**: Real-time health and stamina bars, collected gold, keys, relics counters, and minimap card.
- **Audio & Ambience**: Atmospheric dungeon soundtrack, footstep cues, chest interaction sounds, and torch flame lighting.

```powershell
python games/dungeon_crawler.py
```

### 2. Space Combat Arena (`games/space_combat_arena.py`)
A high-speed 6DOF space flight combat simulation:
- **Starfighter Flight Model**: 6-degrees-of-freedom inertial physics with pitch, yaw, roll, and booster acceleration.
- **Asteroid Belt**: Procedurally generated instanced asteroid field with diverse scales and rotations rendered via `InstancedMesh`.
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
├── examples/                   # 13 feature-focused educational examples
│   ├── 01_hello_pbr.py         # Basic PBR sphere setup
│   ├── 02_dynamic_lights_bloom.py # Dynamic point lights and bloom pass
│   ├── 03_skeletal_character.py # glTF skeletal animation loading
│   ├── 04_numpy_wave_surface.py # Procedural mesh deformation via NumPy
│   ├── 05_custom_shader_water.py # Custom fullscreen shader pass
│   ├── 06_render_to_texture_portal.py # Render targets and portal rendering
│   ├── 07_particles_and_sprites.py # Particle systems and 3D billboard sprites
│   ├── 08_instanced_forest.py  # High-density instanced rendering
│   └── ...                     # Additional interactive showcases
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
