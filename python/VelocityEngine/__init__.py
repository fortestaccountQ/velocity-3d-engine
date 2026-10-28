"""VelocityEngine: High-performance C++20 3D Game & Editor Engine with Sokol GFX, PBR Shading, and Dear ImGui."""

from __future__ import annotations

from .app import App
from .material import Material, gold, metal, plastic, rubber

try:
    from ._VelocityEngine_core import (
        Mode,
        Key,
        Vec3,
        Vec4,
        Transform,
        Camera,
        DirectionalLight,
        Mesh,
        Texture,
        Entity,
        Model,
        Scene,
        InputManager,
        AudioManager,
        EditorManager,
        AABB,
        Cylinder,
        Ray,
        RaycastHit,
    )
except ImportError:
    from _VelocityEngine_core import (
        Mode,
        Key,
        Vec3,
        Vec4,
        Transform,
        Camera,
        DirectionalLight,
        Mesh,
        Texture,
        Entity,
        Model,
        Scene,
        InputManager,
        AudioManager,
        EditorManager,
        AABB,
        Cylinder,
        Ray,
        RaycastHit,
    )

from .controller import FirstPersonController

__version__ = "0.2.0-beta"

__all__ = [
    "App",
    "Mode",
    "Key",
    "Vec3",
    "Vec4",
    "Transform",
    "Camera",
    "DirectionalLight",
    "Mesh",
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
    "FirstPersonController",
    "gold",
    "metal",
    "plastic",
    "rubber",
]
