"""Velocity 3D Engine: High-performance C++20 3D Game & Editor Engine with Sokol GFX, PBR Shading, and Dear ImGui."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import enum
from typing import Any, List, Optional, Tuple, Union, overload

# ---------------------------------------------------------------------------
# Native Core Types & Math
# ---------------------------------------------------------------------------
from ._VelocityEngine_core import (
    # Core Vectors & Matrices
    Vec2 as Vec2,
    Vec3 as Vec3,
    Vec4 as Vec4,
    Mat4 as Mat4,
    Quat as Quat,
    Euler as Euler,
    Transform as Transform,
    Plane as Plane,
    Frustum as Frustum,
    AABB as AABB,
    BoundingSphere as BoundingSphere,
    Cylinder as Cylinder,
    Ray as Ray,
    RaycastHit as RaycastHit,
    RenderStats as RenderStats,
    quat_from_euler as quat_from_euler,
    quat_to_euler as quat_to_euler,
    quat_from_axis_angle as quat_from_axis_angle,
    quat_look_rotation as quat_look_rotation,
    quat_slerp as quat_slerp,
    # Engine & Input
    Mode as Mode,
    Key as Key,
    MouseButton as MouseButton,
    EngineApp as EngineApp,
    InputManager as InputManager,
    AudioManager as AudioManager,
    EditorManager as EditorManager,
    UICommand as UICommand,
    UICommandType as UICommandType,
    # Geometry & Models
    Vertex as Vertex,
    Mesh as Mesh,
    InstanceData as InstanceData,
    InstancedMesh as InstancedMesh,
    Model as Model,
    ModelLoader as ModelLoader,
    Curve3 as Curve3,
    CatmullRomCurve3 as CatmullRomCurve3,
    CubicBezierCurve3 as CubicBezierCurve3,
    QuadraticBezierCurve3 as QuadraticBezierCurve3,
    LineCurve3 as LineCurve3,
    create_tube as create_tube,
    create_lathe as create_lathe,
    create_extrude as create_extrude,
    LODLevel as LODLevel,
    LOD as LOD,
    # Materials & Textures
    MaterialType as MaterialType,
    SideMode as SideMode,
    BlendMode as BlendMode,
    TextureFilter as TextureFilter,
    TextureWrap as TextureWrap,
    StandardMaterial as StandardMaterial,
    PhysicalMaterial as PhysicalMaterial,
    UnlitMaterial as UnlitMaterial,
    LambertMaterial as LambertMaterial,
    PhongMaterial as PhongMaterial,
    ToonMaterial as ToonMaterial,
    ShaderMaterial as ShaderMaterial,
    PipelineManager as PipelineManager,
    Texture as Texture,
    CubeTexture as CubeTexture,
    DataTexture as DataTexture,
    # Scene Graph & Lights
    Node3D as Node3D,
    Entity as Entity,
    Scene as Scene,
    Light as Light,
    LightType as LightType,
    DirectionalLight as DirectionalLight,
    PointLight as PointLight,
    SpotLight as SpotLight,
    HemisphereLight as HemisphereLight,
    AmbientLight as AmbientLight,
    # Cameras
    Camera as Camera,
    CameraType as CameraType,
    PerspectiveCamera as PerspectiveCamera,
    OrthographicCamera as OrthographicCamera,
    # Helpers
    Helper as Helper,
    GridHelper as GridHelper,
    AxesHelper as AxesHelper,
    BoxHelper as BoxHelper,
    ArrowHelper as ArrowHelper,
    CameraHelper as CameraHelper,
    DirectionalLightHelper as DirectionalLightHelper,
    PointLightHelper as PointLightHelper,
    SpotLightHelper as SpotLightHelper,
    SkeletonHelper as SkeletonHelper,
    # Animation & Particles
    Bone as Bone,
    Skeleton as Skeleton,
    Interpolation as Interpolation,
    PropertyType as PropertyType,
    KeyframeTrack as KeyframeTrack,
    AnimationClip as AnimationClip,
    AnimationAction as AnimationAction,
    AnimationMixer as AnimationMixer,
    SkinnedMesh as SkinnedMesh,
    SpriteMaterial as SpriteMaterial,
    Sprite as Sprite,
    PointsMaterial as PointsMaterial,
    Points as Points,
    Particle as Particle,
    ParticleEmitter as ParticleEmitter,
    # Post Processing & Render Targets
    RenderTargetFormat as RenderTargetFormat,
    RenderTarget as RenderTarget,
    TonemappingMode as TonemappingMode,
    PostProcessPass as PostProcessPass,
    BloomPass as BloomPass,
    SSAOPass as SSAOPass,
    FXAAPass as FXAAPass,
    TonemappingPass as TonemappingPass,
    VignetteChromaticPass as VignetteChromaticPass,
    ColorGradingPass as ColorGradingPass,
    EffectComposer as EffectComposer,
    CubeRenderTarget as CubeRenderTarget,
    CubeCamera as CubeCamera,
    # Environment
    BackgroundType as BackgroundType,
    ShadowSettings as ShadowSettings,
    SkyParams as SkyParams,
    ProceduralSky as ProceduralSky,
    # Asset IO
    AssetCache as AssetCache,
    load_obj_mesh as load_obj_mesh,
    load_stl_mesh as load_stl_mesh,
    load_ply_mesh as load_ply_mesh,
    load_mesh_file as load_mesh_file,
    load_obj as load_obj,
    load_stl as load_stl,
    load_ply as load_ply,
    export_obj as export_obj,
    export_stl as export_stl,
    export_gltf as export_gltf,
    save_screenshot as save_screenshot,
)

# ---------------------------------------------------------------------------
# Pythonic Facade & Helper Modules
# ---------------------------------------------------------------------------
from .app import App as App
from .color import (
    Color as Color,
    as_color as as_color,
    WHITE as WHITE,
    BLACK as BLACK,
    RED as RED,
    GREEN as GREEN,
    BLUE as BLUE,
    YELLOW as YELLOW,
    CYAN as CYAN,
    MAGENTA as MAGENTA,
    GRAY as GRAY,
    DARK_GRAY as DARK_GRAY,
    LIGHT_GRAY as LIGHT_GRAY,
    WARM_WHITE as WARM_WHITE,
    ORANGE as ORANGE,
    PURPLE as PURPLE,
)
from .controller import (
    FirstPersonController as FirstPersonController,
    FlyCameraController as FlyCameraController,
    FreeCameraController as FreeCameraController,
)
from .orbit_controller import (
    OrbitController as OrbitController,
    FollowCamera as FollowCamera,
)
from .fog import (
    Fog as Fog,
    FogExp2 as FogExp2,
)
from .group import Group as Group
from .tween import (
    Tween as Tween,
    TweenManager as TweenManager,
    linear as linear,
    in_quad as in_quad,
    out_quad as out_quad,
    in_out_quad as in_out_quad,
    in_cubic as in_cubic,
    out_cubic as out_cubic,
    in_out_cubic as in_out_cubic,
    in_bounce as in_bounce,
    out_bounce as out_bounce,
    in_out_bounce as in_out_bounce,
    in_elastic as in_elastic,
    out_elastic as out_elastic,
    in_out_elastic as in_out_elastic,
    patch_entity_and_model as patch_entity_and_model,
)
from .camera_utils import (
    screen_to_ray as screen_to_ray,
    patch_camera as patch_camera,
)
from .ui import (
    UIOverlay as UIOverlay,
    UITextCommand as UITextCommand,
    UIRectCommand as UIRectCommand,
    UICrosshairCommand as UICrosshairCommand,
    UILineCommand as UILineCommand,
)
from .scene_factory import (
    SceneFactory as SceneFactory,
    create_box as create_box,
    create_sphere as create_sphere,
    create_plane as create_plane,
    create_cylinder as create_cylinder,
    create_grid as create_grid,
    set_sun as set_sun,
    patch_scene as patch_scene,
)
from .material import (
    Material as Material,
    gold as gold,
    metal as metal,
    plastic as plastic,
    rubber as rubber,
)

# ---------------------------------------------------------------------------
# Monkey Patchers & Package Metadata
# ---------------------------------------------------------------------------
def patch_audio() -> None: ...
def patch_instanced_mesh() -> None: ...

__version__: str
__all__: list[str]
