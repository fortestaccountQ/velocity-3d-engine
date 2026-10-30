"""Unit and Integration Tests for Pielosyty 3D Games Suite.

Tests:
- `games.space_combat_arena`: 6DOF Space Flight Dogfight Arena, 1,200 instanced asteroids,
  laser blaster projectiles, particle explosions, autonomous AI drones, radar HUD.
- `games.dungeon_crawler`: Third-person Action RPG / Dungeon Crawler, Mixamo skeletal Soldier hero,
  animation state machine (Idle/Walk/Run/Attack), interactive raycast chest/lever/portcullis,
  flickering torch PointLights, SSAO + Bloom post-processing.
"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

repo_root = Path(__file__).resolve().parent.parent
python_dir = repo_root / "python"
if str(python_dir) not in sys.path:
    sys.path.insert(0, str(python_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from games.space_combat_arena import SpaceCombatArena, build_player_starfighter, build_enemy_drone, create_asteroid_field
from games.dungeon_crawler import DungeonCrawler, build_modular_dungeon, DungeonLighting, InteractiveChest, InteractiveLever, PortcullisDoor


def test_space_combat_arena_components():
    """Verify starfighter geometry, 1,200-instance asteroid field, weapons, and HUD."""
    arena = SpaceCombatArena(width=640, height=480, self_play=True, max_frames=30)

    # 1. Player ship and hierarchy
    assert arena.player_ship is not None
    assert len(arena.player_ship.children) >= 6 # Fuselage, Nose, Cockpit, Wings, Cannons, Engines

    # 2. Asteroid Field
    assert arena.inst_mesh is not None
    assert arena.inst_mesh.instance_count() == 1200
    assert len(arena.asteroids) == 1200

    # 3. AI Enemy Drones
    assert len(arena.enemy_drones) == 5
    for drone in arena.enemy_drones:
        assert drone.alive
        assert drone.health == 100.0

    # 4. Weapons & FX
    assert arena.weapons is not None
    assert arena.fx is not None
    assert arena.fx.sparks is not None
    assert arena.fx.smoke is not None
    assert arena.fx.thruster_fx is not None

    # 5. Post-Processing Stack
    assert arena.composer is not None
    assert arena.bloom_pass is not None
    assert arena.tonemap_pass is not None
    assert arena.vignette_pass is not None

    # 6. Run simulation steps
    for _ in range(30):
        arena.update_physics(1.0 / 60.0)
    arena.draw_hud()

    assert arena.score >= 0
    assert arena.shield <= arena.max_shield
    assert arena.hull <= arena.max_hull


def test_space_combat_arena_self_play():
    """Run Space Combat Arena automated self-play for 60 frames."""
    arena = SpaceCombatArena(width=640, height=480, self_play=True, max_frames=60)
    arena.run()
    assert arena.frame_count >= 60


def test_dungeon_crawler_components():
    """Verify dungeon architecture, skeletal hero, interactables, torch lights, and SSAO."""
    crawler = DungeonCrawler(width=640, height=480, self_play=True, max_frames=30)

    # 1. Skeletal Hero & Mixer
    assert crawler.hero_node is not None
    if crawler.mixer is not None:
        actions = crawler.mixer.actions
        assert "Idle" in actions
        assert "Walk" in actions
        assert "Run" in actions
        assert "Attack" in actions

    # 2. Interactables
    assert crawler.chest is not None
    assert not crawler.chest.is_opened
    assert crawler.lever is not None
    assert not crawler.lever.is_pulled
    assert crawler.portcullis is not None
    assert not crawler.portcullis.is_open

    # 3. Torch Lighting & Particles
    assert len(crawler.lighting.lights) >= 7 # Central brazier + 6 sconces
    assert crawler.lighting.fire_emitter is not None
    assert crawler.lighting.smoke_emitter is not None
    assert crawler.lighting.loot_emitter is not None

    # 4. Post-Processing
    assert crawler.composer is not None
    assert crawler.ssao_pass is not None
    assert crawler.bloom_pass is not None
    assert crawler.tonemap_pass is not None

    # 5. Obstacles
    assert len(crawler.obstacles) > 10

    # 6. Interactable trigger
    opened = crawler.chest.open()
    assert opened
    assert crawler.chest.is_opened

    pulled = crawler.lever.pull()
    assert pulled
    assert crawler.lever.is_pulled

    crawler.portcullis.trigger_open()
    assert crawler.portcullis.is_opening


def test_dungeon_crawler_self_play():
    """Run Dungeon Crawler automated self-play for 60 frames."""
    crawler = DungeonCrawler(width=640, height=480, self_play=True, max_frames=60)
    crawler.run()
    assert crawler.frame_count >= 60
