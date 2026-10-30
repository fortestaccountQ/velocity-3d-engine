"""Velocity 3D Engine: Pythonic lowercase shortcut package for VelocityEngine."""

from __future__ import annotations

import VelocityEngine as _ve
from VelocityEngine import *
from VelocityEngine import __version__, __all__

_core = getattr(_ve, "_core", None)
