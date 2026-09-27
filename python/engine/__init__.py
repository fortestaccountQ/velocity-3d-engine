"""Modular 3D Engine package with C++20 core, Sokol GFX, GLM, Nanobind, and PBR-lite texturing."""

from .app import App

try:
    from ._engine_core import (
        Key,
        Vec3,
        Vec4,
        Transform,
        Camera,
        DirectionalLight,
        Texture,
        Material,
        Entity,
        Scene,
        InputManager,
    )
except ImportError:
    pass

__version__ = "0.3.0"
__all__ = [
    "App",
    "Key",
    "Vec3",
    "Vec4",
    "Transform",
    "Camera",
    "DirectionalLight",
    "Texture",
    "Material",
    "Entity",
    "Scene",
    "InputManager",
]
