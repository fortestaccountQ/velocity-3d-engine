# Velocity 3D Engine: Master Engineering Specification & Swarm Blueprint (`MASTER_PLAN.md`)

**Document Version:** 1.0.0-RELEASE  
**Author:** Antigravity System Architect & Universal Tech Lead (GOF Mode 3)  
**Project:** Velocity 3D Engine (`d:\python\reverse_engineering\3d_render`)  
**Status:** APPROVED (Full Administrative Carte Blanche Granted by User)  
**Baseline Test Suite:** 424 / 424 Passing (`pytest tests/`)

---

## 1. Global Architectural Rules & System Contracts

### 1.1 Non-Negotiable Operational Laws
1. **Local Git Exclusivity:** All development, branches, commits, tags, and merges MUST remain strictly local (`git add`, `git commit`, `git merge`, `git tag`). Absolutely **zero** `git push` or remote publication.
2. **Zero Solo Feature Coding:** All module implementations, documentation pages, game codes, and test files are developed by specialized subagents operating on isolated tasks with strict ownership boundaries.
3. **Memory & Buffer Safety:**
   - Single-mesh vertex count must never exceed **65,535 vertices** (`uint16_t` Sokol index buffer limit). Grids and procedural surfaces must stay within 180x180 resolution and include explicit quad triangulation indices.
   - Dynamic buffers (e.g. CPU-skinned characters, dynamic water waves) must call `mesh->mark_dynamic()` before GPU buffer creation to allocate `SG_USAGE_DYNAMIC` or `SG_USAGE_STREAM`.
4. **Coordinate & Projection Conventions:**
   - Right-handed Cartesian: `+X` = Right, `+Y` = Up, `-Z` = Camera Forward.
   - Depth buffer range: `[0.0, 1.0]` (Direct3D 11, Metal, Vulkan standard via `GLM_FORCE_DEPTH_ZERO_TO_ONE`).
5. **Ergonomic Python API:**
   - Public imports must strictly use `import VelocityEngine as ve` (with `import velocity as ve` and legacy `import pielosyty as ve` preserved for backward compatibility).
   - All public methods, properties, and constructors must maintain PEP-484 typing signatures and match `_VelocityEngine_core.pyi` stubs.
6. **Documentation & i18n Parity:**
   - All documentation resides in `docs/` with standard GitHub Flavored Markdown and Material for MkDocs compatibility.
   - Root README and all 8 localized landing pages in `docs/translations/` must have 100% structural symmetry, valid badge destinations, and properly unlinked bold active language tags.
7. **Playable Games & Demos Quality Standard:**
   - Every example must support interactive play (human controls) and automated headless self-play (`--test` flag) executing 60–120 frames without error, memory leaks, or NaN transforms.
   - Zero black artifacts: all materials must have proper lighting or ambient fallbacks, instance transforms must never collapse to origin `(0, 0, 0)`, and textures must exist on disk.

---

## 2. Target File Tree & Exclusive Ownership Map

```text
velocity-3d-engine/
├── README.md                                   [Orchestrator]
├── LICENSE                                     [Orchestrator]
├── mkdocs.yml                                  [DocsArchitectDev]
├── MASTER_PLAN.md                              [Orchestrator]
│
├── core/                                       [CoreEngineDev]
│   ├── src/
│   │   ├── model_loader.cpp                    # Fix: Ensure SkinnedMesh vertex buffer is dynamic
│   │   ├── editor.cpp                          # Branding: Pielosyty -> VelocityEngine
│   │   └── asset_io.cpp                        # Branding: Pielosyty -> VelocityEngine
│
├── docs/                                       [DocsSwarm]
│   ├── index.md                                # Landing Page & Portal
│   ├── getting-started/
│   │   ├── index.md
│   │   ├── installation.md                     # Windows, Linux, macOS, Python 3.10-3.13
│   │   ├── quickstart.md                       # 5-Minute First 3D Scene
│   │   └── troubleshooting.md                  # Common build, shader, and buffer fixes
│   ├── architecture/
│   │   ├── overview.md                         # Hybrid C++20 + Sokol GFX + Nanobind
│   │   ├── render-pipeline.md                  # Forward+ passes, PBR, Ping-Pong HDR
│   │   └── scene-graph.md                      # Node3D, World Matrices, Transforms
│   ├── guides/
│   │   ├── materials-and-shaders.md            # Cook-Torrance GGX PBR, textures, IBL
│   │   ├── skeletal-animation.md               # glTF rigs, skinning, crossfades, sockets
│   │   ├── post-processing.md                  # EffectComposer, Bloom, SSAO, Tonemapping
│   │   ├── lighting-and-shadows.md             # Directional, Point, Spot, Shadows
│   │   ├── cameras-and-input.md                # Controllers (FPS, Orbit, Follow), picking
│   │   ├── audio.md                            # miniaudio 2D & 3D spatial sound
│   │   ├── instancing-and-lod.md               # InstancedMesh (50k objects), LOD, Culling
│   │   ├── ui-and-hud.md                       # UIOverlay, bitmap font, 2D gauges
│   │   ├── asset-pipeline.md                   # glTF, OBJ, STL, PLY loading & exporting
│   │   └── editor-and-tooling.md               # Dear ImGui, Gizmos, Scene serialization
│   ├── api-reference/
│   │   ├── python/
│   │   │   ├── app.md                          # App, WindowConfig, Mode
│   │   │   ├── scene.md                        # Scene, Entity, Node3D, Group
│   │   │   ├── geometry.md                     # Mesh, InstancedMesh, SkinnedMesh, Curves
│   │   │   ├── materials.md                    # StandardMaterial, Texture, ShaderMaterial
│   │   │   ├── lights.md                       # DirectionalLight, PointLight, SpotLight
│   │   │   ├── animation.md                    # AnimationMixer, AnimationClip, Skeleton
│   │   │   ├── postprocess.md                  # EffectComposer, BloomPass, SSAOPass
│   │   │   ├── controllers.md                  # FirstPerson, Orbit, Follow controllers
│   │   │   ├── math.md                         # Vec2/3/4, Quat, Euler, Mat4, Ray, AABB
│   │   │   └── audio.md                        # AudioManager
│   │   └── cpp/
│   │       ├── core-engine.md                  # EngineApp, WindowConfig, Renderer
│   │       └── headers.md                      # engine/*.hpp index
│   ├── examples/
│   │   ├── index.md                            # Showcase curriculum catalog (16 examples)
│   │   ├── mario-3d.md                         # 3D Mario Platformer Deep Dive
│   │   ├── racing-3d.md                        # 3D Racing Simulator Deep Dive
│   │   └── flappy-bird-3d.md                   # 3D Flappy Bird Deep Dive
│   ├── contributing/
│   │   ├── index.md
│   │   ├── code-style.md                       # C++20 formatting & Python PEP-561
│   │   └── testing-guide.md                    # pytest test suites & headless CI
│   └── translations/                           # Complete localized READMEs
│       ├── README_ar.md                        # Arabic
│       ├── README_de.md                        # German
│       ├── README_es.md                        # Spanish
│       ├── README_fr.md                        # French
│       ├── README_ja.md                        # Japanese
│       ├── README_pt.md                        # Portuguese
│       ├── README_ru.md                        # Russian
│       └── README_zh.md                        # Simplified Chinese
│
├── examples/                                   [ExamplesDev]
│   ├── legacy/                                 # Archived obsolete PoCs
│   │   ├── 01_window.py
│   │   ├── 02_rotating_cube.py
│   │   ├── 03_scene_lighting.py
│   │   ├── 04_textured_material.py
│   │   ├── 05_load_model.py
│   │   └── 06_playable_demo.py
│   ├── 01_hello_window.py                      # Modern clean window & background
│   ├── 02_rotating_cube.py                     # Textured PBR spinning cube
│   ├── 03_hello_pbr.py                         # 5x5 PBR metallic-roughness sphere grid
│   ├── 04_dynamic_lights_bloom.py              # Lissajous point lights + HDR BloomPass
│   ├── 05_skeletal_character.py                # Mixamo Soldier.glb with dynamic skinning
│   ├── 06_interactive_sandbox.py               # FirstPersonController + raycast bouncing
│   ├── 07_particles_and_sprites.py             # Atmospheric campfire, sparks, smoke, rain
│   ├── 08_curves_rollercoaster.py              # CatmullRom spline, tube track, banking camera
│   ├── 09_render_to_texture_portal.py          # CCTV camera feed on 3D TV monitor
│   ├── 10_instanced_forest.py                  # Fixed: 10,000 scattered pine trees & rocks
│   ├── 11_water_surface.py                     # Fixed: Procedural displaced wave surface
│   ├── 12_numpy_wave.py                        # Fixed: 180x180 indexed grid running at 60 FPS
│   ├── 13_pbr_damaged_helmet.py                # Fixed: DamagedHelmet PBR test with lighting
│   ├── 14_fps_minigame.py                      # Playable FPS shooter with audio & targets
│   ├── 15_viral_cube_cannon.py                 # Viral bouncy cube cannon & duck reactions
│   ├── 16_visual_editor.py                     # Dear ImGui editor, hierarchy, gizmos (F2)
│   ├── game_3d_mario.py                        # NEW: 3D Mario Platformer Game
│   ├── game_3d_racing.py                       # NEW: 3D Arcade Circuit Racing Game
│   └── game_3d_flappy_bird.py                  # NEW: 3D Flappy Bird Game
│
└── tests/                                      [QAVerifierDev]
    ├── test_new_games.py                       # Automated verification of 3 new games
    └── test_examples_sanity.py                 # Smoke tests verifying all 16 examples run
```

---

## 3. Concrete Data Structures, Schemas & Interface Blueprints

### 3.1 3D Mario Platformer (`examples/game_3d_mario.py`)
```python
class MarioPlayer:
    position: ve.Vec3
    velocity: ve.Vec3
    facing_angle: float
    is_grounded: bool
    is_double_jump_ready: bool
    is_ground_pounding: bool
    lives: int
    coins: int
    score: int
    
    def handle_input(self, input_mgr: ve.InputManager, dt: float) -> None: ...
    def update_physics(self, platforms: list["MovingPlatform"], islands: list["AABB"], dt: float) -> None: ...
    def collect_coin(self, coin: "Coin") -> None: ...
    def respawn(self) -> None: ...

class MovingPlatform:
    entity: ve.Entity
    start_pos: ve.Vec3
    end_pos: ve.Vec3
    velocity: ve.Vec3
    phase: float
    
    def update(self, dt: float) -> None: ...
```

### 3.2 3D Racing Simulator (`examples/game_3d_racing.py`)
```python
class RaceCar:
    chassis: ve.Entity
    wheels: list[ve.Entity]  # 0: FL, 1: FR, 2: RL, 3: RR
    position: ve.Vec3
    heading: float
    linear_velocity: float
    angular_velocity: float
    steer_angle: float
    is_drifting: bool
    tire_smoke: ve.ParticleEmitter
    
    def handle_controls(self, input_mgr: ve.InputManager, dt: float) -> None: ...
    def update_dynamics(self, track_bounds: list["TrackSegment"], dt: float) -> None: ...

class RaceTrack:
    spline: ve.CatmullRomCurve3
    curbs: list[ve.Entity]
    checkpoints: list[ve.AABB]
    lap_times: list[float]
    best_lap: float
    
    def check_checkpoint(self, car_pos: ve.Vec3) -> None: ...
```

### 3.3 3D Flappy Bird (`examples/game_3d_flappy_bird.py`)
```python
class FlappyBird:
    entity: ve.Entity
    position: ve.Vec3
    vertical_velocity: float
    pitch_angle: float
    bounding_sphere: ve.BoundingSphere
    is_alive: bool
    score: int
    best_score: int
    
    def flap(self) -> None: ...
    def update(self, dt: float) -> None: ...
    def die(self) -> None: ...
    def reset(self) -> None: ...

class PipePair:
    top_pipe: ve.Entity
    bottom_pipe: ve.Entity
    x_pos: float
    gap_y: float
    has_scored: bool
    
    def update(self, speed: float, dt: float) -> None: ...
```

---

## 4. Iterative Phased Roadmap with Intra-Phase Parallelism

### Phase 0: Baseline Savepoint, Bug Fixes & Legacy Cleanup
*Criteria: `model_loader.cpp` patched, legacy files safely moved, branding sanitized, build passes 100%.*

- **[x] Task 0.1 (Topology A - Parallel):** Git baseline savepoint commit and tag `v0.1-pre-swarm`.
- **[x] Task 0.2 (Topology A - Parallel):** Patch `core/src/model_loader.cpp` to ensure `mesh->mark_dynamic()` is set BEFORE `mesh->ensure_gpu_buffers()` for skinned character meshes.
- **[x] Task 0.3 (Topology A - Parallel):** Sanitize legacy branding in `LICENSE`, `core/src/editor.cpp`, and `core/src/asset_io.cpp`.
- **[x] Task 0.4 (Topology A - Parallel):** Archive the 6 broken PoC scripts (`01_window.py`..`06_playable_demo.py`) into `examples/legacy/`.
- **[x] Acceptance Gate Phase 0:** `pytest tests/` passes 424/424, git working tree clean.

---

### Phase 1: Comprehensive Documentation & Localization Factory
*Criteria: `docs/` tree fully authored with 12 complete guides, API references, MkDocs configuration, and 8 localized READMEs.*

- **[x] Task 1.1 (Topology A - Parallel):** Create `mkdocs.yml`, `docs/index.md`, and `docs/getting-started/` (`installation.md`, `quickstart.md`, `troubleshooting.md`).
- **[x] Task 1.2 (Topology A - Parallel):** Author `docs/architecture/` (`overview.md`, `render-pipeline.md`, `scene-graph.md`).
- **[x] Task 1.3 (Topology A - Parallel):** Author `docs/guides/` (Part 1: `materials-and-shaders.md`, `skeletal-animation.md`, `post-processing.md`, `lighting-and-shadows.md`, `cameras-and-input.md`).
- **[x] Task 1.4 (Topology A - Parallel):** Author `docs/guides/` (Part 2: `audio.md`, `instancing-and-lod.md`, `ui-and-hud.md`, `asset-pipeline.md`, `editor-and-tooling.md`).
- **[x] Task 1.5 (Topology A - Parallel):** Author `docs/api-reference/` (`python/` all 10 modules + `cpp/`).
- **[x] Task 1.6 (Topology A - Parallel):** Author `docs/contributing/` (`overview.md`, `code-style.md`, `testing-guide.md`) and `docs/examples/` showcase pages.
- **[x] Task 1.7 (Topology A - Parallel):** Migrate and harmonize all 8 translations to `docs/translations/README_*.md` with fixed badges, navigation links, and the languages matrix table.
- **[x] Acceptance Gate Phase 1:** All markdown files exist, have zero broken cross-links, and provide executable code snippets.

---

### Phase 2: Examples Overhaul & Visual Glitch Fixes
*Criteria: Clean 16-step curriculum in `examples/`, zero black clumps, zero black spiderweb shards, 60 FPS.*

- **[x] Task 2.1 (Topology A - Parallel):** Fix `08_instanced_forest.py` (re-indexed to `10_instanced_forest.py`): assign valid positions/matrices via `set_instance_transform` across the terrain.
- **[x] Task 2.2 (Topology A - Parallel):** Fix `04_numpy_wave_surface.py` (re-indexed to `12_numpy_wave.py`): 180x180 resolution with proper quad indices preventing `uint16_t` overflow.
- **[x] Task 2.3 (Topology A - Parallel):** Reorganize and clean up examples 01 through 16 to form the standardized educational curriculum.
- **[x] Acceptance Gate Phase 2:** Run all 16 examples with `--test` flag: 100% exit code 0, zero black artifacts, zero crashes.

---

### Phase 3: The 3 High-Profile Interactive 3D Games
*Criteria: Mario 3D, Racing 3D, and Flappy Bird 3D fully implemented with responsive controls, physics, HUD, audio, and automated self-play test modes.*

- **[x] Task 3.1 (Topology A - Parallel):** Implement **3D Mario Platformer** (`examples/game_3d_mario.py`).
- **[x] Task 3.2 (Topology A - Parallel):** Implement **3D Racing Simulator** (`examples/game_3d_racing.py`).
- **[x] Task 3.3 (Topology A - Parallel):** Implement **3D Flappy Bird** (`examples/game_3d_flappy_bird.py`).
- **[x] Acceptance Gate Phase 3:** All 3 games execute smoothly at 60 FPS in interactive mode and pass headless self-play verification.

---

### Phase 4: Universal 4-Tier Verification & Production Delivery
*Criteria: Automated pytest test suite for new games, visual inspection via window testing, clean git release tag.*

- **[x] Task 4.1 (Topology A - Parallel):** Author `tests/test_new_games.py` and `tests/test_examples_sanity.py` verifying frame stepping, bounding volumes, and collision math.
- **[x] Task 4.2 (Topology B - Sequential):** Execute full automated test suite (`pytest tests/`) ensuring 100% pass rate.
- **[x] Task 4.3 (Topology B - Sequential):** Perform visual smoke check of the 3 new games using headless rendering / window verification.
- **[x] Task 4.4 (Topology B - Sequential):** Final local git commit, tag `v1.0.0-alpha`, and deliver comprehensive development report.
