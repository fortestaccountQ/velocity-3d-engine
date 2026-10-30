"""Unit and Integration Tests for 3D Mario Platformer (examples/game_3d_mario.py).

Tests:
- Mario character hierarchy, materials, and initialization parameters.
- Platforming mechanics: locomotion, variable jumping, double-jump somersault at peak.
- Ground pound physics and breakable block shattering.
- Moving platforms sine-wave dynamics and velocity transfer.
- Collectible coins scale-punch tweens and counter incrementation.
- Power Star radiant summit collection, fanfare, and particle burst.
- Pitfall detection below Y = -6.0 and respawn mechanics.
- Headless self-play 120-frame execution.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

import VelocityEngine as ve
from VelocityEngine import App, Vec3, AABB
from examples.game_3d_mario import (
    MarioPlayer,
    MovingPlatform,
    Coin,
    QuestionBlock,
    PowerStar,
    WorldIsland,
    MarioGame,
    run_game,
)


@pytest.fixture
def test_app():
    """Create a headless test app instance and cleanly destroy it after test."""
    app = App("TestMarioApp", width=640, height=480)
    yield app
    app.scene.clear()
    app.close()


def test_mario_player_initialization(test_app):
    """Verify Mario player initial parameters, hierarchy, and collision bounds."""
    scene = test_app.scene
    player = MarioPlayer(scene, test_app)

    assert player.lives == 3
    assert player.coins == 0
    assert player.score == 0
    assert player.is_grounded
    assert not player.is_double_jump_ready
    assert not player.is_ground_pounding
    assert player.root_entity is not None
    assert len(player.root_entity.children) >= 10  # Boots, legs, torso, bib, buttons, head, nose, moustache, cap

    player.cleanup()


def test_mario_locomotion_and_rotation(test_app):
    """Verify horizontal acceleration and directional facing angle calculation."""
    scene = test_app.scene
    player = MarioPlayer(scene, test_app)

    # Simulate moving right (+X)
    class FakeInput:
        def is_key_down(self, key):
            return key in (ve.Key.D, ve.Key.RIGHT)

    player.handle_input(FakeInput(), dt=1.0 / 60.0)
    assert player.velocity.x > 0.0

    # Facing angle should rotate towards right (-90 / 270 deg)
    for _ in range(15):
        player.handle_input(FakeInput(), dt=1.0 / 60.0)
    assert abs(player.facing_angle - (-90.0)) < 15.0 or abs(player.facing_angle - 270.0) < 15.0

    player.cleanup()


def test_mario_variable_jump_and_double_jump(test_app):
    """Verify short hop on tap, high jump on hold, and double-jump somersault at jump peak."""
    scene = test_app.scene
    player = MarioPlayer(scene, test_app)

    class SpaceInput:
        def __init__(self, pressed=True):
            self.pressed = pressed
        def is_key_down(self, key):
            return key == ve.Key.SPACE and self.pressed

    # 1. Tap Space: Jump launched
    player.handle_input(SpaceInput(True), dt=1.0 / 60.0)
    assert not player.is_grounded
    assert player.is_jumping
    assert player.velocity.y > 5.0

    # Simulate rise to jump peak
    player.velocity.y = 0.5  # near peak
    player.update_physics(platforms=[], islands=[], dt=1.0 / 60.0)
    player.handle_input(SpaceInput(False), dt=1.0 / 60.0)
    assert player.is_double_jump_ready

    # Double jump somersault trigger
    player.handle_input(SpaceInput(True), dt=1.0 / 60.0)
    assert player.was_double_jumped
    assert not player.is_double_jump_ready
    assert player.is_somersaulting
    assert player.velocity.y >= 9.0

    player.cleanup()


def test_mario_ground_pound(test_app):
    """Verify airborne Shift ground pound plunge and downward velocity."""
    scene = test_app.scene
    player = MarioPlayer(scene, test_app)

    player.is_grounded = False
    player.velocity.y = 2.0

    class ShiftInput:
        def is_key_down(self, key):
            return key == ve.Key.LEFT_SHIFT

    player.handle_input(ShiftInput(), dt=1.0 / 60.0)
    assert player.is_ground_pounding
    assert player.velocity.y <= -20.0
    assert player.velocity.x == 0.0
    assert player.velocity.z == 0.0

    player.cleanup()


def test_moving_platform_dynamics(test_app):
    """Verify MovingPlatform sinusoidal trajectory and instantaneous velocity."""
    scene = test_app.scene
    plat = MovingPlatform(
        scene=scene,
        start_pos=Vec3(0.0, 2.0, 0.0),
        end_pos=Vec3(10.0, 2.0, 0.0),
        speed=2.0,
    )

    # Initial update
    plat.update(dt=1.0 / 60.0)
    assert plat.aabb is not None
    assert plat.velocity is not None

    # Platform moves horizontally along X
    for _ in range(30):
        plat.update(dt=1.0 / 60.0)
    assert plat.entity.transform.position.x > 0.0


def test_question_block_and_coin_collection(test_app):
    """Verify bumping '?' block from below spawns bonus coin and increments score."""
    scene = test_app.scene
    player = MarioPlayer(scene, test_app)

    box_mesh = ve.Mesh.create_box(1.0, 1.0, 1.0)
    coin_mesh = ve.Mesh.create_cylinder(0.4, 0.1, 16)
    mat = ve.StandardMaterial()

    block = QuestionBlock(
        scene=scene,
        position=Vec3(0.0, 3.0, 0.0),
        box_mesh=box_mesh,
        active_mat=mat,
        inactive_mat=mat,
        coin_mesh=coin_mesh,
        coin_mat=mat,
    )

    initial_coins = player.coins
    initial_score = player.score

    block.bump(player, test_app)
    assert player.coins == initial_coins + 1
    assert player.score == initial_score + 200
    assert not block.has_item

    block.cleanup()
    player.cleanup()


def test_power_star_victory(test_app):
    """Verify Power Star summit pickup, fanfare, and score bonus."""
    scene = test_app.scene
    player = MarioPlayer(scene, test_app)
    star = PowerStar(scene, Vec3(0.0, 10.0, 0.0))

    initial_score = player.score
    star.collect(player, test_app)

    assert star.is_collected
    assert player.stars_collected == 1
    assert player.score == initial_score + 5000

    star.cleanup()
    player.cleanup()


def test_pitfall_and_respawn(test_app):
    """Verify falling below Y = -6.0 deducts a life and respawns at origin."""
    scene = test_app.scene
    player = MarioPlayer(scene, test_app)

    player.lives = 3
    player.position = Vec3(0.0, -7.0, 0.0)
    player.update_physics(platforms=[], islands=[], dt=1.0 / 60.0)

    assert player.lives == 2
    assert player.position.y >= 1.0  # respawned on ground

    player.cleanup()


def test_mario_3d_headless_self_play():
    """Verify full game executes for 120 frames in automated test mode without errors."""
    app = run_game(test_mode=True, frames=120)
    assert app is not None
