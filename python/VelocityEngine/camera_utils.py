"""Camera raycasting and projection utilities for VelocityEngine."""

from __future__ import annotations

import math
from typing import Tuple, Any

try:
    from . import _VelocityEngine_core as _core
except ImportError:
    import _VelocityEngine_core as _core


def screen_to_ray(camera: Any, mouse_x: float, mouse_y: float, screen_w: float, screen_h: float) -> Any:
    """Convert screen coordinate (mouse_x, mouse_y) into a 3D world space Ray.

    Screen space origin (0, 0) is top-left, (screen_w, screen_h) is bottom-right.
    """
    w = max(1.0, float(screen_w))
    h = max(1.0, float(screen_h))

    # Normalized device coordinates: [-1, 1]
    ndc_x = (2.0 * float(mouse_x) / w) - 1.0
    ndc_y = 1.0 - (2.0 * float(mouse_y) / h)

    # Camera forward and right vectors
    fwd = camera.forward()
    f_len = math.sqrt(fwd.x * fwd.x + fwd.y * fwd.y + fwd.z * fwd.z)
    if f_len > 1e-6:
        fx, fy, fz = fwd.x / f_len, fwd.y / f_len, fwd.z / f_len
    else:
        fx, fy, fz = 0.0, 0.0, -1.0

    r = camera.right()
    rx, ry, rz = r.x, r.y, r.z

    # Reconstruct true camera up = normalize(cross(right, forward))
    ux = ry * fz - rz * fy
    uy = rz * fx - rx * fz
    uz = rx * fy - ry * fx
    u_len = math.sqrt(ux * ux + uy * uy + uz * uz)
    if u_len > 1e-6:
        ux, uy, uz = ux / u_len, uy / u_len, uz / u_len
    else:
        ux, uy, uz = 0.0, 1.0, 0.0

    aspect = w / h
    fov_deg = getattr(camera, "fov", 55.0)
    tan_half_fov = math.tan(math.radians(fov_deg * 0.5))

    # Unprojected direction vector in world coordinates
    dx = fx + rx * (ndc_x * aspect * tan_half_fov) + ux * (ndc_y * tan_half_fov)
    dy = fy + ry * (ndc_x * aspect * tan_half_fov) + uy * (ndc_y * tan_half_fov)
    dz = fz + rz * (ndc_x * aspect * tan_half_fov) + uz * (ndc_y * tan_half_fov)
    d_len = math.sqrt(dx * dx + dy * dy + dz * dz)
    if d_len > 1e-6:
        dx, dy, dz = dx / d_len, dy / d_len, dz / d_len

    pos = camera.position
    return _core.Ray(_core.Vec3(pos.x, pos.y, pos.z), _core.Vec3(dx, dy, dz))


def patch_camera():
    """Attach screen_to_ray method to native Camera class."""
    if not hasattr(_core.Camera, "screen_to_ray"):
        _core.Camera.screen_to_ray = screen_to_ray
