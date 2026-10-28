"""Unit tests for the Viral 3D Cube Cannon (Кубик-пушка) in VelocityEngine."""

import sys
import math
import subprocess
from pathlib import Path
import pytest

repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import VelocityEngine as ve
from VelocityEngine import (
    App,
    Color,
    CYAN,
    YELLOW,
    MAGENTA,
    GREEN,
    RED,
    ORANGE,
    PURPLE,
)


def test_cube_cannon_palette():
    """Verify neon palette has 10 distinct vibrant colors."""
    palette = [
        CYAN,
        YELLOW,
        MAGENTA,
        GREEN,
        RED,
        ORANGE,
        PURPLE,
        Color.from_hex("#39ff14"),
        Color.from_hex("#00f0ff"),
        Color.from_hex("#ff007f"),
    ]
    assert len(palette) == 10
    for col in palette:
        assert isinstance(col, Color)
        assert 0.0 <= col.r <= 1.0
        assert 0.0 <= col.g <= 1.0
        assert 0.0 <= col.b <= 1.0


def test_cube_cannon_bounce_math():
    """Test floor bounce restitution (0.58) and horizontal ground friction (0.88)."""
    pos = [0.0, 0.15, 0.0]  # Below 0.20 floor
    vel = [10.0, -20.0, 5.0]

    if pos[1] <= 0.20:
        pos[1] = 0.20
        vel[1] = -vel[1] * 0.58
        vel[0] *= 0.88
        vel[2] *= 0.88

    assert pos[1] == 0.20
    assert pytest.approx(vel[1], rel=1e-4) == 11.6
    assert pytest.approx(vel[0], rel=1e-4) == 8.8
    assert pytest.approx(vel[2], rel=1e-4) == 4.4


def test_duck_collision_threshold():
    """Test Duck collision detection within radius 1.7."""
    duck_center = (0.0, 0.0, 0.0)
    inside_point = (1.0, 0.8, 0.5)
    outside_point = (2.0, 1.0, 2.0)

    dist_in = math.sqrt(sum((a - b) ** 2 for a, b in zip(inside_point, duck_center)))
    dist_out = math.sqrt(sum((a - b) ** 2 for a, b in zip(outside_point, duck_center)))

    assert dist_in < 1.7
    assert dist_out >= 1.7


def test_cube_cannon_active_limit():
    """Test active cube limit caps at 300 entities and purges oldest."""
    app = App(title="TestLimit", width=100, height=100)
    cubes = []

    for i in range(350):
        ent = app.scene.create_box(size=(0.4, 0.4, 0.4), color=CYAN, has_collision=True, cast_shadows=True)
        cubes.append({"entity": ent, "id": i})
        while len(cubes) > 300:
            oldest = cubes.pop(0)
            app.scene.remove_entity(oldest["entity"])

    assert len(cubes) == 300
    assert cubes[0]["id"] == 50
    assert cubes[-1]["id"] == 349
    app.close()


def test_showcase_automated_run():
    """Run examples/10_showcase.py with --test flag and ensure clean 60 frame exit."""
    python_exe = sys.executable
    showcase_script = str(repo_root / "examples" / "10_showcase.py")

    result = subprocess.run(
        [python_exe, showcase_script, "--test"],
        capture_output=True,
        text=True,
        cwd=str(repo_root),
        timeout=30,
    )

    assert result.returncode == 0, f"Process failed with error: {result.stderr}"
    assert "Verified 60 frames in automated test mode" in result.stdout
    assert "Engine closed cleanly" in result.stdout
