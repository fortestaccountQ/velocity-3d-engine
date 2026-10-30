# C++ Header File Index (`core/include/engine/*.hpp`)

Comprehensive index of all public header files in the Velocity 3D Engine core C++20 library.

---

## Headers Overview Table

| Header File | Primary Classes / Structs | Subsystem |
|:---|:---|:---|
| [`animation.hpp`](#animationhpp) | `Bone`, `Skeleton`, `AnimationClip`, `AnimationAction`, `AnimationMixer` | Skeletal Animation |
| [`app.hpp`](#apphpp) | `EngineApp`, `WindowConfig`, `RenderStats`, `UICommand` | Application & Windowing |
| [`asset_io.hpp`](#asset_iohpp) | `AssetCache`, `load_obj`, `export_obj`, `save_screenshot` | Asset Import / Export |
| [`audio.hpp`](#audiohpp) | `AudioManager` | Spatial 3D Audio |
| [`camera.hpp`](#camerahpp) | `Camera`, `PerspectiveCamera`, `OrthographicCamera` | Camera & Projection |
| [`cube_camera.hpp`](#cube_camerahpp) | `CubeCamera` | Dynamic Reflection Probes |
| [`cube_texture.hpp`](#cube_texturehpp) | `CubeTexture` | Cubemaps & Skyboxes |
| [`curve.hpp`](#curvehpp) | `Curve3`, `CatmullRomCurve3`, `CubicBezierCurve3` | Parametric Splines |
| [`editor.hpp`](#editorhpp) | `EditorManager` | ImGui Visual Scene Editor |
| [`entity.hpp`](#entityhpp) | `Entity` | Renderable Game Objects |
| [`helpers.hpp`](#helpershpp) | `GridHelper`, `AxesHelper`, `BoxHelper`, `LightHelper` | Visual Debug Gizmos |
| [`input.hpp`](#inputhpp) | `InputManager`, `Key`, `MouseButton` | Input Handling |
| [`light.hpp`](#lighthpp) | `DirectionalLight`, `PointLight`, `SpotLight`, `AmbientLight` | Illumination |
| [`lod.hpp`](#lodhpp) | `LOD`, `LODLevel` | Distance-based LOD |
| [`material.hpp`](#materialhpp) | `StandardMaterial`, `PhysicalMaterial`, `PipelineManager` | Materials & Pipelines |
| [`math_types.hpp`](#math_typeshpp) | `AABB`, `BoundingSphere`, `Cylinder`, `Frustum`, `Ray` | Math & Collision Geometry |
| [`mesh.hpp`](#meshhpp) | `Mesh`, `Vertex`, `InstanceData` | Geometry & Buffers |
| [`model.hpp`](#modelhpp) | `Model` | glTF / OBJ Multi-mesh Container |
| [`model_loader.hpp`](#model_loaderhpp) | `ModelLoader` | Asset Loader Interface |
| [`node3d.hpp`](#node3dhpp) | `Node3D`, `Group` | Scene Graph Transform Hierarchy |
| [`particle.hpp`](#particlehpp) | `ParticleEmitter`, `Particle` | Particle FX System |
| [`physics.hpp`](#physicshpp) | Collision math, AABB depenetration, character controller physics | Physics Primitives |
| [`points.hpp`](#pointshpp) | `Points`, `PointsMaterial` | Point Cloud Rendering |
| [`post_process.hpp`](#post_processhpp) | `EffectComposer`, `BloomPass`, `SSAOPass`, `TonemappingPass` | Post-Processing |
| [`render_target.hpp`](#render_targethpp) | `RenderTarget`, `CubeRenderTarget` | Framebuffers & Render Targets |
| [`scene.hpp`](#scenehpp) | `Scene` | Root Scene Graph & Raycasting |
| [`skinned_mesh.hpp`](#skinned_meshhpp) | `SkinnedMesh` | Rigged Characters |
| [`sky.hpp`](#skyhpp) | `ProceduralSky`, `SkyParams` | Atmosphere & Sky |
| [`sprite.hpp`](#spritehpp) | `Sprite`, `SpriteMaterial` | 3D Billboard Sprites |
| [`texture.hpp`](#texturehpp) | `Texture`, `DataTexture` | 2D GPU Textures |
| [`transform.hpp`](#transformhpp) | `Transform` | Local & World Matrix Transform |

---

## Detailed Header Index

### `animation.hpp`
- **Location**: `core/include/engine/animation.hpp`
- **Dependencies**: `<glm/glm.hpp>`, `<glm/gtc/quaternion.hpp>`, `<string>`, `<vector>`, `<memory>`, `engine/node3d.hpp`
- **Description**: Defines keyframe animation structures, linear/cubic spline interpolation, bone hierarchy propagation, and crossfading mixers.

### `app.hpp`
- **Location**: `core/include/engine/app.hpp`
- **Dependencies**: `sokol_app.h`, `sokol_gfx.h`, `engine/scene.hpp`, `engine/camera.hpp`, `engine/input.hpp`, `engine/audio.hpp`
- **Description**: Primary application orchestrator. Configures window settings, event loop callbacks, shadow passes, scene rendering, and 2D HUD command buffers.

### `asset_io.hpp`
- **Location**: `core/include/engine/asset_io.hpp`
- **Dependencies**: `engine/mesh.hpp`, `engine/model.hpp`, `<string>`
- **Description**: Asset import and export routines for Wavefront `.obj`, binary/ASCII `.stl`, Stanford `.ply`, and glTF 2.0 files, plus PNG screenshot capture.

### `audio.hpp`
- **Location**: `core/include/engine/audio.hpp`
- **Dependencies**: `<glm/glm.hpp>`, `<string>`, `<memory>`
- **Description**: Lightweight audio interface wrapping `miniaudio`. Implements 3D spatial listener positioning, procedural footstep/jump synthesis, and audio file decoding.

### `camera.hpp`
- **Location**: `core/include/engine/camera.hpp`
- **Dependencies**: `engine/node3d.hpp`, `engine/math_types.hpp`
- **Description**: Camera base class, `PerspectiveCamera`, and `OrthographicCamera`. Computes view, projection, and combined view-projection matrices ($\mathbf{M}_{\text{VP}}$). Provides `screen_to_ray` screen unprojection.

### `cube_camera.hpp`
- **Location**: `core/include/engine/cube_camera.hpp`
- **Dependencies**: `engine/camera.hpp`, `engine/render_target.hpp`
- **Description**: Six-sided environment probe that renders the scene into each of the 6 faces of a `CubeRenderTarget` for real-time metallic reflections.

### `cube_texture.hpp`
- **Location**: `core/include/engine/cube_texture.hpp`
- **Dependencies**: `sokol_gfx.h`, `<string>`, `<array>`
- **Description**: GPU cubemap texture resource. Supports loading six face images, equirectangular HDR sky textures, and procedural atmospheric gradients.

### `curve.hpp`
- **Location**: `core/include/engine/curve.hpp`
- **Dependencies**: `<glm/glm.hpp>`, `<vector>`
- **Description**: Parametric 3D curve base class with implementations for `CatmullRomCurve3`, `CubicBezierCurve3`, and `LineCurve3`. Implements arc-length parameterization and procedural tube generation.

### `editor.hpp`
- **Location**: `core/include/engine/editor.hpp`
- **Dependencies**: `imgui.h`, `ImGuizmo.h`, `engine/scene.hpp`
- **Description**: Visual scene inspection GUI. Renders the scene node tree hierarchy, entity material parameters, light properties, and 3D translation/rotation/scale gizmos.

### `entity.hpp`
- **Location**: `core/include/engine/entity.hpp`
- **Dependencies**: `engine/node3d.hpp`, `engine/mesh.hpp`, `engine/material.hpp`, `engine/math_types.hpp`
- **Description**: Core renderable scene entity. Combines a geometric `Mesh`, a shading `Material`, color tint, and local/world collision bounding boxes.

### `helpers.hpp`
- **Location**: `core/include/engine/helpers.hpp`
- **Dependencies**: `engine/node3d.hpp`, `engine/mesh.hpp`, `engine/material.hpp`
- **Description**: Visual debug wireframe renderers for ground grids, XYZ coordinate axes, bounding boxes, lights, cameras, and skeletons.

### `input.hpp`
- **Location**: `core/include/engine/input.hpp`
- **Dependencies**: `sokol_app.h`, `<unordered_set>`
- **Description**: Polled input state manager. Tracks keyboard key states (`is_key_down`, `is_key_pressed`, `is_key_released`), mouse position, and mouse delta offsets.

### `light.hpp`
- **Location**: `core/include/engine/light.hpp`
- **Dependencies**: `engine/node3d.hpp`, `<glm/glm.hpp>`
- **Description**: Dynamic light types (`DirectionalLight`, `PointLight`, `SpotLight`, `AmbientLight`, `HemisphereLight`) and shader uniform block packing.

### `lod.hpp`
- **Location**: `core/include/engine/lod.hpp`
- **Dependencies**: `engine/node3d.hpp`, `engine/mesh.hpp`
- **Description**: Level of Detail manager. Switches between discrete mesh detail representations based on distance from the active camera.

### `material.hpp`
- **Location**: `core/include/engine/material.hpp`
- **Dependencies**: `sokol_gfx.h`, `engine/texture.hpp`, `<glm/glm.hpp>`
- **Description**: Material shading definitions (`StandardMaterial`, `PhysicalMaterial`, `UnlitMaterial`, `ShaderMaterial`) and the global `PipelineManager` GPU pipeline cache.

### `math_types.hpp`
- **Location**: `core/include/engine/math_types.hpp`
- **Dependencies**: `<glm/glm.hpp>`, `<glm/gtc/quaternion.hpp>`
- **Description**: Fundamental geometric mathematics: `Ray`, `Plane`, `AABB`, `BoundingSphere`, `Cylinder`, and `Frustum` intersection routines.

### `mesh.hpp`
- **Location**: `core/include/engine/mesh.hpp`
- **Dependencies**: `sokol_gfx.h`, `engine/math_types.hpp`, `<vector>`
- **Description**: Polygon mesh buffer holding vertex and index buffers. Contains procedural generators for boxes, spheres, cylinders, capsules, and tori, along with morph targets and dynamic buffer updates.

### `model.hpp`
- **Location**: `core/include/engine/model.hpp`
- **Dependencies**: `engine/node3d.hpp`, `engine/mesh.hpp`, `engine/animation.hpp`
- **Description**: Hierarchical multi-mesh container representing imported 3D models with embedded materials, skeletons, and animation clips.

### `model_loader.hpp`
- **Location**: `core/include/engine/model_loader.hpp`
- **Dependencies**: `cgltf.h`, `engine/model.hpp`
- **Description**: glTF 2.0 / GLB binary file parser. Translates scene nodes, PBR materials, skinning joints, and animation samplers into native engine objects.

### `node3d.hpp`
- **Location**: `core/include/engine/node3d.hpp`
- **Dependencies**: `engine/transform.hpp`, `<vector>`, `<memory>`, `<string>`
- **Description**: Base hierarchical scene node. Implements parent-child relationships, world matrix caching, visibility flags, shadow flags, and event dispatch.

### `particle.hpp`
- **Location**: `core/include/engine/particle.hpp`
- **Dependencies**: `engine/node3d.hpp`, `sokol_gfx.h`
- **Description**: Procedural particle emitter. Simulates particles with position, velocity, acceleration, color over lifetime, and size over lifetime.

### `physics.hpp`
- **Location**: `core/include/engine/physics.hpp`
- **Dependencies**: `engine/math_types.hpp`
- **Description**: Collision detection and minimum translation vector (MTV) depenetration algorithms for characters colliding with arbitrary boxes.

### `points.hpp`
- **Location**: `core/include/engine/points.hpp`
- **Dependencies**: `engine/node3d.hpp`, `sokol_gfx.h`
- **Description**: Point cloud geometry container and shader pass for rendering unindexed vertex points.

### `post_process.hpp`
- **Location**: `core/include/engine/post_process.hpp`
- **Dependencies**: `engine/render_target.hpp`, `sokol_gfx.h`
- **Description**: Chained fullscreen post-processing pipeline (`EffectComposer`, `BloomPass`, `SSAOPass`, `TonemappingPass`, `FXAAPass`).

### `render_target.hpp`
- **Location**: `core/include/engine/render_target.hpp`
- **Dependencies**: `sokol_gfx.h`
- **Description**: Offscreen GPU color and depth-stencil texture attachments for offscreen rendering, portals, and post-processing buffers.

### `scene.hpp`
- **Location**: `core/include/engine/scene.hpp`
- **Dependencies**: `engine/node3d.hpp`, `engine/entity.hpp`, `engine/light.hpp`
- **Description**: Scene graph root manager. Manages entities, instanced meshes, lights, sky background, and spatial raycast queries.

### `skinned_mesh.hpp`
- **Location**: `core/include/engine/skinned_mesh.hpp`
- **Dependencies**: `engine/entity.hpp`, `engine/animation.hpp`
- **Description**: Rigged skeletal character entity. Applies bone transformations to vertex buffers using CPU linear blend skinning.

### `sky.hpp`
- **Location**: `core/include/engine/sky.hpp`
- **Dependencies**: `sokol_gfx.h`, `<glm/glm.hpp>`
- **Description**: Procedural Rayleigh and Mie atmospheric scattering sky simulation.

### `sprite.hpp`
- **Location**: `core/include/engine/sprite.hpp`
- **Dependencies**: `engine/node3d.hpp`, `engine/material.hpp`
- **Description**: Camera-facing 3D billboard sprite for foliage, UI markers, and glow auras.

### `texture.hpp`
- **Location**: `core/include/engine/texture.hpp`
- **Dependencies**: `sokol_gfx.h`, `<string>`
- **Description**: 2D GPU texture resource encapsulating image dimensions, channels, wrap modes, and filtering modes.

### `transform.hpp`
- **Location**: `core/include/engine/transform.hpp`
- **Dependencies**: `<glm/glm.hpp>`, `<glm/gtc/quaternion.hpp>`
- **Description**: Spatial transform component. Manages local position, quaternion orientation, and scale, with dirty-flag caching for local and world matrices.
