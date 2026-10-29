"""VelocityEngine backwards-compatibility alias layer for Pielosyty 3D Engine.

VelocityEngine has been rebranded to pielosyty. This package re-exports
all symbols from pielosyty for complete backwards compatibility.
"""

from __future__ import annotations

try:
    import pielosyty as _pe
    from pielosyty import *
    from pielosyty import __version__, __all__
    _core = getattr(_pe, "_core", None)
except ImportError:
    from typing import Any

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

    InstancedMesh = getattr(_core, "InstancedMesh", None)
    InstanceData = getattr(_core, "InstanceData", None)

    UICommandType = getattr(_core, "UICommandType", None)
    UICommand = getattr(_core, "UICommand", None)

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
        UICommand,
        UICommandType,
        UITextCommand,
        UIRectCommand,
        UICrosshairCommand,
        UILineCommand,
    )
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

    patch_camera()
    patch_entity_and_model()
    patch_scene()
    patch_audio()
    patch_instanced_mesh()

    __version__ = "0.2.0-beta"
    __all__ = [
        "App",
        "EngineApp",
        "Mode",
        "Key",
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
        "Scene",
        "InputManager",
        "AudioManager",
        "EditorManager",
        "AABB",
        "BoundingSphere",
        "Cylinder",
        "Ray",
        "RaycastHit",
        "UIOverlay",
        "UICommand",
        "UICommandType",
        "UITextCommand",
        "UIRectCommand",
        "UICrosshairCommand",
        "UILineCommand",
        "FirstPersonController",
        "FlyCameraController",
        "FreeCameraController",
        "OrbitController",
        "FollowCamera",
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
        "screen_to_ray",
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
        "gold",
        "metal",
        "plastic",
        "rubber",
    ]
