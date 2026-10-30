"""PBR Material presets and utility functions for VelocityEngine."""

from __future__ import annotations
from typing import Sequence
try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core


def gold(roughness: float = 0.25) -> _core.Material:
    """Preset: polished gold metal."""
    mat = _core.Material(roughness=roughness, metallic=1.0)
    mat.base_color = (1.0, 0.782, 0.344, 1.0)
    return mat


def metal(roughness: float = 0.2, color: Sequence[float] = (0.9, 0.9, 0.9, 1.0)) -> _core.Material:
    """Preset: metallic surface."""
    mat = _core.Material(roughness=roughness, metallic=1.0)
    mat.base_color = tuple(color) if len(color) == 4 else (*color, 1.0)
    return mat


def plastic(roughness: float = 0.4, color: Sequence[float] = (0.8, 0.2, 0.2, 1.0)) -> _core.Material:
    """Preset: dielectric plastic surface."""
    mat = _core.Material(roughness=roughness, metallic=0.0)
    mat.base_color = tuple(color) if len(color) == 4 else (*color, 1.0)
    return mat


def rubber(roughness: float = 0.9, color: Sequence[float] = (0.1, 0.1, 0.1, 1.0)) -> _core.Material:
    """Preset: rough rubber surface."""
    mat = _core.Material(roughness=roughness, metallic=0.0)
    mat.base_color = tuple(color) if len(color) == 4 else (*color, 1.0)
    return mat


# Attach presets directly onto the core Material class
_core.Material.gold = staticmethod(gold)
_core.Material.metal = staticmethod(metal)
_core.Material.plastic = staticmethod(plastic)
_core.Material.rubber = staticmethod(rubber)

Material = _core.Material
StandardMaterial = getattr(_core, "StandardMaterial", Material)
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

__all__ = [
    "Material",
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
    "PipelineManager",
    "gold",
    "metal",
    "plastic",
    "rubber",
]
