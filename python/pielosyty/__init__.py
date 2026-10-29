"""Pielosyty 3D Engine: High-performance C++20 3D Game & Editor Engine with Sokol GFX, PBR Shading, and Dear ImGui."""

from __future__ import annotations

from typing import Any

# Core native bindings import
try:
    from . import _pielosyty_core as _core
except ImportError:
    try:
        from . import _VelocityEngine_core as _core
    except ImportError:
        try:
            import _pielosyty_core as _core
        except ImportError:
            import _VelocityEngine_core as _core

Mode = _core.Mode
Key = _core.Key

class MouseButton:
    """Standard mouse buttons."""
    LEFT: int = 0
    RIGHT: int = 1
    MIDDLE: int = 2
Vec2 = getattr(_core, "Vec2", None)
Vec3 = _core.Vec3
Vec4 = _core.Vec4
Transform = _core.Transform
Camera = _core.Camera
DirectionalLight = _core.DirectionalLight
Mesh = _core.Mesh
Texture = _core.Texture
Entity = _core.Entity
Model = _core.Model
Scene = _core.Scene
InputManager = _core.InputManager
AudioManager = _core.AudioManager
EditorManager = _core.EditorManager
EngineApp = _core.EngineApp
AABB = _core.AABB
BoundingSphere = getattr(_core, "BoundingSphere", None)
Cylinder = _core.Cylinder
Ray = _core.Ray
RaycastHit = _core.RaycastHit

# Optional native extensions
InstancedMesh = getattr(_core, "InstancedMesh", None)
InstanceData = getattr(_core, "InstanceData", None)

# Phase 1: Math & Scene Graph types
Node3D = getattr(_core, "Node3D", None)
Mat4 = getattr(_core, "Mat4", None)
Quat = getattr(_core, "Quat", None)
Plane = getattr(_core, "Plane", None)
Frustum = getattr(_core, "Frustum", None)
RenderStats = getattr(_core, "RenderStats", None)
Light = getattr(_core, "Light", None)
LightType = getattr(_core, "LightType", None)
quat_from_euler = getattr(_core, "quat_from_euler", None)
quat_to_euler = getattr(_core, "quat_to_euler", None)
quat_from_axis_angle = getattr(_core, "quat_from_axis_angle", None)
quat_look_rotation = getattr(_core, "quat_look_rotation", None)
quat_slerp = getattr(_core, "quat_slerp", None)

class Euler:
    """Euler angles representation (in radians) with rotation order."""
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0, order: str = "XYZ") -> None:
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.order = str(order)

    def to_quat(self) -> Any:
        if quat_from_euler is not None:
            return quat_from_euler(self.x, self.y, self.z, self.order)
        return Quat() if Quat is not None else None

    @classmethod
    def from_quat(cls, q: Any, order: str = "XYZ") -> Euler:
        if quat_to_euler is not None:
            v = quat_to_euler(q, order)
            return cls(v.x, v.y, v.z, order)
        return cls(0.0, 0.0, 0.0, order)

    def to_vec3(self) -> Any:
        return Vec3(self.x, self.y, self.z)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def __getitem__(self, idx: int) -> float:
        return (self.x, self.y, self.z)[idx]

    def __len__(self) -> int:
        return 3

    def __repr__(self) -> str:
        return f"Euler(x={self.x}, y={self.y}, z={self.z}, order='{self.order}')"

# Phase 2: Materials, Textures, Geometry & Lights
Vertex = getattr(_core, "Vertex", None)
StandardMaterial = getattr(_core, "StandardMaterial", None)
PhysicalMaterial = getattr(_core, "PhysicalMaterial", None)
UnlitMaterial = getattr(_core, "UnlitMaterial", None)
LambertMaterial = getattr(_core, "LambertMaterial", None)
PhongMaterial = getattr(_core, "PhongMaterial", None)
ToonMaterial = getattr(_core, "ToonMaterial", None)
ShaderMaterial = getattr(_core, "ShaderMaterial", None)
MaterialType = getattr(_core, "MaterialType", None)
SideMode = getattr(_core, "SideMode", None)
BlendMode = getattr(_core, "BlendMode", None)
TextureFilter = getattr(_core, "TextureFilter", None)
TextureWrap = getattr(_core, "TextureWrap", None)
PipelineManager = getattr(_core, "PipelineManager", None)

def DataTexture(data: Any, width: int, height: int, channels: int = 4) -> Any:
    """Create a Texture from raw bytes, bytearray, memoryview, or numpy array."""
    if hasattr(data, "tobytes"):
        raw_bytes = data.tobytes()
    elif isinstance(data, (bytearray, memoryview)):
        raw_bytes = bytes(data)
    elif isinstance(data, bytes):
        raw_bytes = data
    else:
        raw_bytes = bytes(data)
    return Texture.create_data_texture(width, height, raw_bytes, channels)

setattr(Texture, "DataTexture", staticmethod(DataTexture))

PointLight = getattr(_core, "PointLight", None)
SpotLight = getattr(_core, "SpotLight", None)
HemisphereLight = getattr(_core, "HemisphereLight", None)
AmbientLight = getattr(_core, "AmbientLight", None)

# Phase 3: Cameras, Viewports, RenderTargets & Post-Processing
CameraType = getattr(_core, "CameraType", None)
PerspectiveCamera = getattr(_core, "PerspectiveCamera", None)
OrthographicCamera = getattr(_core, "OrthographicCamera", None)
RenderTargetFormat = getattr(_core, "RenderTargetFormat", None)
RenderTarget = getattr(_core, "RenderTarget", None)
TonemappingMode = getattr(_core, "TonemappingMode", None)
PostProcessPass = getattr(_core, "PostProcessPass", None)
BloomPass = getattr(_core, "BloomPass", None)
SSAOPass = getattr(_core, "SSAOPass", None)
FXAAPass = getattr(_core, "FXAAPass", None)
TonemappingPass = getattr(_core, "TonemappingPass", None)
VignetteChromaticPass = getattr(_core, "VignetteChromaticPass", None)
ColorGradingPass = getattr(_core, "ColorGradingPass", None)
EffectComposer = getattr(_core, "EffectComposer", None)

# Phase 4: Environment, Skybox, HDR/IBL & Advanced Shadows v2
BackgroundType = getattr(_core, "BackgroundType", None)
ShadowSettings = getattr(_core, "ShadowSettings", None)
SkyParams = getattr(_core, "SkyParams", None)
CubeTexture = getattr(_core, "CubeTexture", None)
ProceduralSky = getattr(_core, "ProceduralSky", None)
CubeRenderTarget = getattr(_core, "CubeRenderTarget", None)
CubeCamera = getattr(_core, "CubeCamera", None)

# Phase 5: Geometry, Curves, Helpers & Level of Detail
Curve3 = getattr(_core, "Curve3", None)
CatmullRomCurve3 = getattr(_core, "CatmullRomCurve3", None)
CubicBezierCurve3 = getattr(_core, "CubicBezierCurve3", None)
QuadraticBezierCurve3 = getattr(_core, "QuadraticBezierCurve3", None)
LineCurve3 = getattr(_core, "LineCurve3", None)
create_tube = getattr(_core, "create_tube", None)
create_lathe = getattr(_core, "create_lathe", None)
create_extrude = getattr(_core, "create_extrude", None)

LODLevel = getattr(_core, "LODLevel", None)
LOD = getattr(_core, "LOD", None)

Helper = getattr(_core, "Helper", None)
GridHelper = getattr(_core, "GridHelper", None)
AxesHelper = getattr(_core, "AxesHelper", None)
BoxHelper = getattr(_core, "BoxHelper", None)
ArrowHelper = getattr(_core, "ArrowHelper", None)
DirectionalLightHelper = getattr(_core, "DirectionalLightHelper", None)
SpotLightHelper = getattr(_core, "SpotLightHelper", None)
PointLightHelper = getattr(_core, "PointLightHelper", None)
CameraHelper = getattr(_core, "CameraHelper", None)

# Phase 6: Skeletal Animation, SkinnedMesh, Morph Targets, Sprites & ParticleEmitter
Bone = getattr(_core, "Bone", None)
Skeleton = getattr(_core, "Skeleton", None)
Interpolation = getattr(_core, "Interpolation", None)
PropertyType = getattr(_core, "PropertyType", None)
KeyframeTrack = getattr(_core, "KeyframeTrack", None)
AnimationClip = getattr(_core, "AnimationClip", None)
AnimationAction = getattr(_core, "AnimationAction", None)
AnimationMixer = getattr(_core, "AnimationMixer", None)
SkeletonHelper = getattr(_core, "SkeletonHelper", None)
SkinnedMesh = getattr(_core, "SkinnedMesh", None)

SpriteMaterial = getattr(_core, "SpriteMaterial", None)
Sprite = getattr(_core, "Sprite", None)
PointsMaterial = getattr(_core, "PointsMaterial", None)
Points = getattr(_core, "Points", None)
Particle = getattr(_core, "Particle", None)
ParticleEmitter = getattr(_core, "ParticleEmitter", None)

# Phase 7: Loaders, Exporters & AssetCache
load_obj_mesh = getattr(_core, "load_obj_mesh", None)
load_stl_mesh = getattr(_core, "load_stl_mesh", None)
load_ply_mesh = getattr(_core, "load_ply_mesh", None)
load_mesh_file = getattr(_core, "load_mesh_file", None)
load_obj = getattr(_core, "load_obj", None)
load_stl = getattr(_core, "load_stl", None)
load_ply = getattr(_core, "load_ply", None)
export_obj = getattr(_core, "export_obj", None)
export_stl = getattr(_core, "export_stl", None)
export_gltf = getattr(_core, "export_gltf", None)
save_screenshot = getattr(_core, "save_screenshot", None)
AssetCache = getattr(_core, "AssetCache", None)

class ModelLoader:
    """Utility class for loading 3D meshes and models."""
    @staticmethod
    def load(filepath: str) -> Any:
        if load_mesh_file is not None:
            return load_mesh_file(filepath)
        return None

    @staticmethod
    def load_obj(filepath: str) -> Any:
        if load_obj_mesh is not None:
            return load_obj_mesh(filepath)
        return None

    @staticmethod
    def load_stl(filepath: str) -> Any:
        if load_stl_mesh is not None:
            return load_stl_mesh(filepath)
        return None

    @staticmethod
    def load_ply(filepath: str) -> Any:
        if load_ply_mesh is not None:
            return load_ply_mesh(filepath)
        return None

# UI Commands contract (Phase 0.1)
UICommandType = getattr(_core, "UICommandType", None)
UICommand = getattr(_core, "UICommand", None)

# High-level ergonomics & Pythonic API modules
from .color import (
    Color,
    as_color,
    WHITE,
    BLACK,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    GRAY,
    DARK_GRAY,
    LIGHT_GRAY,
    WARM_WHITE,
    ORANGE,
    PURPLE,
)

from .tween import (
    Tween,
    TweenManager,
    linear,
    in_quad,
    out_quad,
    in_out_quad,
    in_cubic,
    out_cubic,
    in_out_cubic,
    in_bounce,
    out_bounce,
    in_out_bounce,
    in_elastic,
    out_elastic,
    in_out_elastic,
    patch_entity_and_model,
)

from .camera_utils import screen_to_ray, patch_camera
from .orbit_controller import OrbitController, FollowCamera
from .ui import (
    UIOverlay,
    UITextCommand,
    UIRectCommand,
    UICrosshairCommand,
    UILineCommand,
)
if UICommandType is None:
    from .ui import UICommandType  # type: ignore
if UICommand is None:
    from .ui import UICommand  # type: ignore

from .fog import Fog, FogExp2
NativeGroup = getattr(_core, "Group", None)
if NativeGroup is not None:
    Group = NativeGroup
else:
    from .group import Group
from .scene_factory import (
    SceneFactory,
    create_box,
    create_sphere,
    create_plane,
    create_cylinder,
    create_grid,
    set_sun,
    patch_scene,
)
from .material import Material, gold, metal, plastic, rubber
from .controller import FirstPersonController, FlyCameraController, FreeCameraController
from .app import App


def patch_audio() -> None:
    """Attach Pythonic helper methods directly onto the native AudioManager class."""
    def play_sound(self: Any, name: str, *args: Any, **kwargs: Any) -> Any:
        name_lower = str(name).lower()
        if "jump" in name_lower:
            return self.play_jump()
        elif "footstep" in name_lower or "step" in name_lower:
            return self.play_footstep()
        elif "hit" in name_lower:
            if args or kwargs:
                return self.play_hit_3d(*args, **kwargs)
            return self.play_hit_3d((0.0, 0.0, 0.0))
        elif hasattr(self, "play_sound_file"):
            return self.play_sound_file(name, *args, **kwargs)
        return None

    if not hasattr(_core.AudioManager, "play_sound"):
        _core.AudioManager.play_sound = play_sound


def patch_instanced_mesh() -> None:
    """Attach Pythonic ergonomic properties and helpers to InstancedMesh."""
    if InstancedMesh is None:
        return

    if not hasattr(InstancedMesh, "count"):
        InstancedMesh.count = property(
            lambda self: self.instance_count(),
            lambda self, val: self.set_instance_count(int(val)),
        )

    if not hasattr(InstancedMesh, "set_color_at"):
        def set_color_at(self: Any, index: int, color: Any) -> None:
            self.set_instance(index, color)
        InstancedMesh.set_color_at = set_color_at

    if not hasattr(InstancedMesh, "set_matrix_at"):
        def set_matrix_at(self: Any, index: int, matrix: Any) -> None:
            self.set_instance(index, (1.0, 1.0, 1.0, 1.0))
        InstancedMesh.set_matrix_at = set_matrix_at


# Automatically apply Pythonic patches to native core classes
patch_camera()
patch_entity_and_model()
patch_scene()
patch_audio()
patch_instanced_mesh()

__version__ = "0.2.0-beta"

__all__ = [
    # Engine & App
    "App",
    "EngineApp",
    "Mode",
    "Key",
    "MouseButton",
    "Vec2",
    "Vec3",
    "Vec4",
    "Transform",
    "Camera",
    "DirectionalLight",
    "Mesh",
    "InstancedMesh",
    "InstanceData",
    "Texture",
    "Material",
    "Entity",
    "Model",
    "ModelLoader",
    "Scene",
    "InputManager",
    "AudioManager",
    "EditorManager",
    "AABB",
    "BoundingSphere",
    "Cylinder",
    "Ray",
    "RaycastHit",
    # UI Commands & Overlay (Phase 0.1)
    "UIOverlay",
    "UICommand",
    "UICommandType",
    "UITextCommand",
    "UIRectCommand",
    "UICrosshairCommand",
    "UILineCommand",
    # Controllers
    "FirstPersonController",
    "FlyCameraController",
    "FreeCameraController",
    "OrbitController",
    "FollowCamera",
    # Pythonic Color
    "Color",
    "as_color",
    "WHITE",
    "BLACK",
    "RED",
    "GREEN",
    "BLUE",
    "YELLOW",
    "CYAN",
    "MAGENTA",
    "GRAY",
    "DARK_GRAY",
    "LIGHT_GRAY",
    "WARM_WHITE",
    "ORANGE",
    "PURPLE",
    # Tween & Animation
    "Tween",
    "TweenManager",
    "linear",
    "in_quad",
    "out_quad",
    "in_out_quad",
    "in_cubic",
    "out_cubic",
    "in_out_cubic",
    "in_bounce",
    "out_bounce",
    "in_out_bounce",
    "in_elastic",
    "out_elastic",
    "in_out_elastic",
    # UI & Raycasting
    "screen_to_ray",
    # Scene Factory & Hierarchy
    "Group",
    "Fog",
    "FogExp2",
    "SceneFactory",
    "create_box",
    "create_sphere",
    "create_plane",
    "create_cylinder",
    "create_grid",
    "set_sun",
    # Materials
    "gold",
    "metal",
    "plastic",
    "rubber",
    # Phase 1: Math & Scene Graph
    "Node3D",
    "Mat4",
    "Quat",
    "Euler",
    "Plane",
    "Frustum",
    "RenderStats",
    "Light",
    "LightType",
    "quat_from_euler",
    "quat_to_euler",
    "quat_from_axis_angle",
    "quat_look_rotation",
    "quat_slerp",
    # Phase 2: Materials, Textures, Geometry & Lights
    "Vertex",
    "StandardMaterial",
    "PhysicalMaterial",
    "UnlitMaterial",
    "LambertMaterial",
    "PhongMaterial",
    "ToonMaterial",
    "ShaderMaterial",
    "MaterialType",
    "SideMode",
    "BlendMode",
    "TextureFilter",
    "TextureWrap",
    "DataTexture",
    "PipelineManager",
    "PointLight",
    "SpotLight",
    "HemisphereLight",
    "AmbientLight",
    # Phase 3: Cameras, Viewports, RenderTargets & Post-Processing
    "CameraType",
    "PerspectiveCamera",
    "OrthographicCamera",
    "RenderTargetFormat",
    "RenderTarget",
    "TonemappingMode",
    "PostProcessPass",
    "BloomPass",
    "SSAOPass",
    "FXAAPass",
    "TonemappingPass",
    "VignetteChromaticPass",
    "ColorGradingPass",
    "EffectComposer",
    # Phase 4: Environment, Skybox, HDR/IBL & Advanced Shadows v2
    "BackgroundType",
    "ShadowSettings",
    "SkyParams",
    "CubeTexture",
    "ProceduralSky",
    "CubeRenderTarget",
    "CubeCamera",
    # Phase 5: Geometry, Curves, Helpers & Level of Detail
    "Curve3",
    "CatmullRomCurve3",
    "CubicBezierCurve3",
    "QuadraticBezierCurve3",
    "LineCurve3",
    "create_tube",
    "create_lathe",
    "create_extrude",
    "LODLevel",
    "LOD",
    "Helper",
    "GridHelper",
    "AxesHelper",
    "BoxHelper",
    "ArrowHelper",
    "DirectionalLightHelper",
    "SpotLightHelper",
    "PointLightHelper",
    "CameraHelper",
    # Phase 6: Skeletal Animation, Morph Targets, Sprites & Particle Systems
    "Bone",
    "Skeleton",
    "Interpolation",
    "PropertyType",
    "KeyframeTrack",
    "AnimationClip",
    "AnimationAction",
    "AnimationMixer",
    "SkeletonHelper",
    "SkinnedMesh",
    "SpriteMaterial",
    "Sprite",
    "PointsMaterial",
    "Points",
    "Particle",
    "ParticleEmitter",
    # Phase 7: Loaders, Exporters & AssetCache
    "load_obj_mesh",
    "load_stl_mesh",
    "load_ply_mesh",
    "load_mesh_file",
    "load_obj",
    "load_stl",
    "load_ply",
    "export_obj",
    "export_stl",
    "export_gltf",
    "save_screenshot",
    "AssetCache",
]
