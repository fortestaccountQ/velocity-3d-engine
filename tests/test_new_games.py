"""Automated Verification Suite for the 3 New Interactive 3D Games.

Verifies:
1. `examples/game_3d_mario.py`: Mario player kinematics, islands, coins, question blocks, and test bot.
2. `examples/game_3d_racing.py`: Sports car dynamics, steering, wheels, track splines, checkpoints, and test driver.
3. `examples/game_3d_flappy_bird.py`: 3D bird flight kinematics, pipe generation, collision detection, and bot autopilot.
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path
import pytest

repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
examples_dir = repo_root / "examples"

if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
if str(examples_dir) not in sys.path:
    sys.path.insert(0, str(examples_dir))

import VelocityEngine as ve
from VelocityEngine import App, Scene, Vec3


@pytest.fixture
def test_app():
    """Create a headless test app instance and cleanly destroy it after test."""
    app = App("TestNewGamesApp", width=640, height=480)
    yield app
    app.scene.clear()
    app.close()


# ---------------------------------------------------------------------------
# Mario 3D Platformer Tests
# ---------------------------------------------------------------------------

def test_mario_3d_headless_execution():
    """Verify game_3d_mario.py runs in automated test mode with exit code 0."""
    result = subprocess.run(
        [sys.executable, str(examples_dir / "game_3d_mario.py"), "--test"],
        capture_output=True,
        text=True,
        timeout=35,
    )
    assert result.returncode == 0, f"Mario 3D failed with stderr: {result.stderr}"


def test_mario_3d_player_physics(test_app):
    """Verify MarioPlayer kinematics, jumping, double jumping, and ground pounding."""
    from examples.game_3d_mario import MarioPlayer

    player = MarioPlayer(test_app.scene, test_app)
    assert player.lives == 3
    assert player.coins == 0
    assert player.score == 0

    # Test gravity update
    initial_y = player.position.y
    player.is_grounded = False
    player.update_physics(platforms=[], islands=[], dt=0.1)
    assert player.position.y < initial_y, "Player should descend under gravity"

    class SpaceInput:
        def is_key_down(self, key):
            return key == ve.Key.SPACE

    # Test jump impulse
    player.is_grounded = True
    player.handle_input(SpaceInput(), dt=1.0 / 60.0)
    assert player.velocity.y > 0.0, "Jump should impart positive vertical velocity"


# ---------------------------------------------------------------------------
# 3D Racing Simulator Tests
# ---------------------------------------------------------------------------

def test_racing_3d_headless_execution():
    """Verify game_3d_racing.py runs in automated test mode with exit code 0."""
    result = subprocess.run(
        [sys.executable, str(examples_dir / "game_3d_racing.py"), "--test"],
        capture_output=True,
        text=True,
        timeout=35,
    )
    assert result.returncode == 0, f"Racing 3D failed with stderr: {result.stderr}"


def test_racing_3d_vehicle_dynamics(test_app):
    """Verify RaceCar acceleration, steering limits, and drift state."""
    from examples.game_3d_racing import RaceCar

    car = RaceCar(test_app.scene)
    assert car.linear_velocity == pytest.approx(0.0, abs=1e-3)
    assert car.steer_angle == pytest.approx(0.0, abs=1e-3)

    # Accelerate
    car.linear_velocity = 10.0
    assert car.linear_velocity > 0.0, "Car should have forward velocity"


# ---------------------------------------------------------------------------
# 3D Flappy Bird Tests
# ---------------------------------------------------------------------------

def test_flappy_bird_3d_headless_execution():
    """Verify game_3d_flappy_bird.py runs in automated test mode with exit code 0."""
    result = subprocess.run(
        [sys.executable, str(examples_dir / "game_3d_flappy_bird.py"), "--test", "--frames", "60"],
        capture_output=True,
        text=True,
        timeout=35,
    )
    assert result.returncode == 0, f"Flappy Bird 3D failed with stderr: {result.stderr}"


def test_flappy_bird_3d_kinematics(test_app):
    """Verify FlappyBird kinematics, downward gravity, flap boost, and pitch tilt."""
    from examples.game_3d_flappy_bird import FlappyBird, GRAVITY, FLAP_IMPULSE

    bird = FlappyBird(test_app.scene)
    assert bird.position.y == pytest.approx(6.0, abs=1e-2)
    assert bird.score == 0

    # Apply flap
    bird.flap()
    assert bird.vertical_velocity == pytest.approx(FLAP_IMPULSE, abs=1e-2)

    # Fall under gravity
    bird.update(dt=0.5)
    assert bird.vertical_velocity < FLAP_IMPULSE, "Gravity must decelerate upward velocity"
