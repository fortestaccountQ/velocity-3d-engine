"""Modular 3D Engine package with C++20 core, Sokol GFX, GLM, Nanobind, and glTF 2.0 / GLB loading."""

from .app import App

try:
    from ._engine_core import (
        Key,
        Vec3,
        Vec4,
        Transform,
        Camera,
        DirectionalLight,
        Mesh,
        Texture,
        Material,
        Entity,
        Model,
        Scene,
        InputManager,
        AudioManager,
        AABB,
        Cylinder,
        Ray,
        RaycastHit,
    )
except ImportError:
    pass

from .controller import FirstPersonController

__version__ = "0.8.0"
__all__ = [
    "App",
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
    "AABB",
    "Cylinder",
    "Ray",
    "RaycastHit",
    "FirstPersonController",
]
