"""Pielosyty backwards-compatibility alias layer for VelocityEngine.

The engine has been unified under VelocityEngine. This package re-exports
all symbols from VelocityEngine for complete backwards compatibility.
"""

from __future__ import annotations

import VelocityEngine as _ve
from VelocityEngine import *
from VelocityEngine import __version__, __all__

_core = getattr(_ve, "_core", None)
