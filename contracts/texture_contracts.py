"""Texture and Material Data Contracts for Crossy Duck and VelocityEngine.

Defines the rigid interface boundaries for:
  1. Texture generation and loading (Pixel-Art / Voxel vs PBR Linear)
  2. Material palettes and UV tiling contracts
  3. Dynamic animated textures (e.g. river water waves/scrolling)
"""

from __future__ import annotations
from typing import Protocol, Tuple, Optional, Any, Dict


class TextureGeneratorContract(Protocol):
    """Protocol for procedural generation and caching of stylized game textures."""

    @staticmethod
    def generate_grass_texture(size: int = 64) -> bytes:
        """Generate lush multi-tone voxel grass texture RGBA bytes."""
        ...

    @staticmethod
    def generate_asphalt_texture(size: int = 64) -> bytes:
        """Generate gritty asphalt pavement texture RGBA bytes with aggregate flecks."""
        ...

    @staticmethod
    def generate_water_texture(size: int = 64, phase: float = 0.0) -> bytes:
        """Generate crystal water texture RGBA bytes with wave caustics & ripples."""
        ...

    @staticmethod
    def generate_wood_bark_texture(size: int = 64) -> bytes:
        """Generate vertical timber grain texture RGBA bytes for trunks and logs."""
        ...

    @staticmethod
    def generate_wood_rings_texture(size: int = 64) -> bytes:
        """Generate concentric tree growth rings RGBA bytes for cut log ends."""
        ...

    @staticmethod
    def generate_gravel_texture(size: int = 64) -> bytes:
        """Generate railroad stone ballast gravel texture RGBA bytes."""
        ...

    @staticmethod
    def generate_rail_tie_texture(size: int = 64) -> bytes:
        """Generate rustic treated railroad timber tie texture RGBA bytes."""
        ...

    @staticmethod
    def generate_car_paint_texture(size: int = 64) -> bytes:
        """Generate glossy automotive car paint texture RGBA bytes."""
        ...

    @staticmethod
    def generate_car_cabin_texture(size: int = 64) -> bytes:
        """Generate tinted automotive cabin glass texture RGBA bytes with glare streaks."""
        ...

    @staticmethod
    def generate_car_wheel_texture(size: int = 64) -> bytes:
        """Generate dark rubber tire with metallic rim hubcap texture RGBA bytes."""
        ...

    @staticmethod
    def generate_truck_cargo_texture(size: int = 64) -> bytes:
        """Generate corrugated shipping container siding texture RGBA bytes."""
        ...

    @staticmethod
    def generate_train_body_texture(size: int = 64) -> bytes:
        """Generate metallic bullet train body with racing speed stripes RGBA bytes."""
        ...

    @staticmethod
    def generate_train_window_texture(size: int = 64) -> bytes:
        """Generate passenger train windows band with interior glow RGBA bytes."""
        ...

    @staticmethod
    def generate_train_front_texture(size: int = 64) -> bytes:
        """Generate bullet train nose decal with raked windshield and headlights RGBA bytes."""
        ...



class MaterialPaletteContract(Protocol):
    """Protocol for unified game material management."""
    materials: Dict[str, Any]

    def get_material(self, name: str) -> Any:
        """Fetch material by registered identifier."""
        ...

    def update_animated_materials(self, dt: float) -> None:
        """Advance time-based texture coordinates (e.g. flowing water)."""
        ...
