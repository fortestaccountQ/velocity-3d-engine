"""VelocityEngine: High-performance C++20 3D Game & Editor Engine with Sokol GFX, PBR Shading, and Dear ImGui."""

from __future__ import annotations

# Core native bindings import
try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core

Mode = _core.Mode
Key = _core.Key
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
from .ui import UIOverlay
from .fog import Fog, FogExp2
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


# Automatically apply Pythonic patches to native core classes
patch_camera()
patch_entity_and_model()
patch_scene()
patch_audio()

__version__ = "0.2.0-beta"

__all__ = [
    # Engine & App
    "App",
    "EngineApp",
    "Mode",
    "Key",
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
    "Scene",
    "InputManager",
    "AudioManager",
    "EditorManager",
    "AABB",
    "Cylinder",
    "Ray",
    "RaycastHit",
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
    "UIOverlay",
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
]
