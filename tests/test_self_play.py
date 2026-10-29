"""Unit tests for VelocityEngine Crossy Duck self-play, CrossyBot AI, and BenchmarkReport."""

from __future__ import annotations
from typing import Optional, List, Dict, Set, Tuple
import pytest
from contracts.crossy_contracts import (
    CELL_MIN_X,
    CELL_MAX_X,
    RowType,
    PlayerStatus,
)
from examples.crossy_duck.self_play import CrossyBot, BenchmarkReport


# ---------------------------------------------------------------------------
# Mock Helper Classes for Deterministic Testing
# ---------------------------------------------------------------------------

class MockPlayer:
    """Mock PlayerController matching the interface expected by CrossyBot."""

    def __init__(self, gx: int = 0, gz: int = 0, status: PlayerStatus = PlayerStatus.IDLE):
        self.grid_x = int(gx)
        self.grid_z = int(gz)
        self.x = float(gx)
        self.y = 0.0
        self.z = float(gz)
        self.status = status
        self.score = gz
        self.idle_timer = 0.0
        self.carrier_vx = 0.0


class MockObstacle:
    """Mock vehicle or log obstacle."""

    def __init__(
        self,
        x: float,
        speed: float = 0.0,
        width: float = 1.5,
        is_log: bool = False,
        min_wrap_x: float = -20.0,
        max_wrap_x: float = 20.0,
    ):
        self.x = float(x)
        self.speed = float(speed)
        self.width = float(width)
        self.is_log = bool(is_log)
        self.min_wrap_x = float(min_wrap_x)
        self.max_wrap_x = float(max_wrap_x)


class MockRow:
    """Mock WorldRow for scenario-based bot decision testing."""

    def __init__(
        self,
        z_index: int,
        row_type: RowType,
        blocked_x: Optional[set] = None,
        obstacles: Optional[list] = None,
        is_warning: bool = False,
        is_train_passing: bool = False,
        carrier_vx: float = 0.0,
    ):
        self.z_index = int(z_index)
        self.row_type = row_type
        self.blocked_lanes = blocked_x or set()
        self.obstacles = obstacles or []
        self.is_warning = bool(is_warning)
        self.is_train_passing = bool(is_train_passing)
        self.carrier_vx = float(carrier_vx)

    def is_blocked(self, px: float, pz: float) -> bool:
        return int(round(px)) in self.blocked_lanes


class MockWorld:
    """Mock WorldGenerator storing rows by z index."""

    def __init__(self, rows: Optional[dict] = None):
        self.active_rows = rows or {}

    def get_row(self, z: int):
        return self.active_rows.get(z)


# ---------------------------------------------------------------------------
# BenchmarkReport Tests
# ---------------------------------------------------------------------------

def test_benchmark_report_empty():
    """Verify empty BenchmarkReport handles zero division gracefully."""
    rep = BenchmarkReport()
    assert rep.total_frames == 0
    assert rep.total_time_s == 0.0
    assert rep.avg_fps == 0.0
    assert rep.min_fps == 0.0
    assert rep.max_fps == 0.0
    assert rep.avg_ms == 0.0
    assert rep.p50_ms == 0.0
    assert rep.p95_ms == 0.0
    assert rep.p99_ms == 0.0


def test_benchmark_report_single_frame():
    """Verify metrics for a single 16.6667ms (60 FPS) frame."""
    rep = BenchmarkReport()
    dt = 1.0 / 60.0
    rep.record_frame(dt)

    assert rep.total_frames == 1
    assert pytest.approx(rep.total_time_s, abs=1e-5) == dt
    assert pytest.approx(rep.avg_fps, abs=0.1) == 60.0
    assert pytest.approx(rep.min_fps, abs=0.1) == 60.0
    assert pytest.approx(rep.max_fps, abs=0.1) == 60.0
    assert pytest.approx(rep.avg_ms, abs=0.01) == 16.67
    assert pytest.approx(rep.p95_ms, abs=0.01) == 16.67
    assert pytest.approx(rep.p99_ms, abs=0.01) == 16.67


def test_benchmark_report_multiple_frames_math():
    """Verify min/avg/max FPS and percentile calculations with known frame durations."""
    rep = BenchmarkReport()
    # 5 frames: 10ms, 20ms, 30ms, 40ms, 50ms
    dts = [0.010, 0.020, 0.030, 0.040, 0.050]
    for d in dts:
        rep.record_frame(d)

    assert rep.total_frames == 5
    assert pytest.approx(rep.total_time_s, abs=1e-5) == 0.150
    # Average FPS: 5 frames / 0.150s = 33.33 FPS
    assert pytest.approx(rep.avg_fps, abs=0.01) == (5.0 / 0.150)
    # Min FPS corresponds to max frame time 50ms -> 20 FPS
    assert pytest.approx(rep.min_fps, abs=0.01) == 20.0
    # Max FPS corresponds to min frame time 10ms -> 100 FPS
    assert pytest.approx(rep.max_fps, abs=0.01) == 100.0
    # Average ms: 150ms / 5 = 30.0 ms
    assert pytest.approx(rep.avg_ms, abs=0.01) == 30.0
    # Median ms: 30.0 ms
    assert pytest.approx(rep.p50_ms, abs=0.01) == 30.0
    # 95th percentile between 40ms and 50ms
    assert rep.p95_ms > 40.0
    assert rep.p99_ms <= 50.0


def test_benchmark_report_summary_formatting(capsys):
    """Verify ASCII table generation and summary printing."""
    rep = BenchmarkReport()
    for _ in range(100):
        rep.record_frame(0.0033)  # ~300 FPS

    summary_text = rep.summary()
    assert "VELOCITY ENGINE BENCHMARK REPORT" in summary_text
    assert "Frames Sampled" in summary_text
    assert "Average FPS" in summary_text
    assert "Minimum FPS" in summary_text
    assert "Maximum FPS" in summary_text
    assert "95th %ile Frame Time" in summary_text
    assert "99th %ile Frame Time" in summary_text

    rep.print_summary()
    captured = capsys.readouterr()
    assert "VELOCITY ENGINE BENCHMARK REPORT" in captured.out


# ---------------------------------------------------------------------------
# CrossyBot Decision Making Tests
# ---------------------------------------------------------------------------

def test_bot_idle_requirement():
    """Bot must return None when player is not in IDLE status (e.g. mid-hop or dead)."""
    bot = CrossyBot()
    world = MockWorld({0: MockRow(0, RowType.START), 1: MockRow(1, RowType.GRASS)})

    player_hopping = MockPlayer(gx=0, gz=0, status=PlayerStatus.HOPPING)
    assert bot.decide_next_action(player_hopping, world) is None

    player_dead = MockPlayer(gx=0, gz=0, status=PlayerStatus.SQUASHED)
    assert bot.decide_next_action(player_dead, world) is None


def test_bot_hops_forward_on_clear_grass():
    """When path ahead is clear, bot immediately decides forward hop (0, 1)."""
    bot = CrossyBot()
    world = MockWorld({
        0: MockRow(0, RowType.START),
        1: MockRow(1, RowType.GRASS, blocked_x=set()),
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    assert action == (0, 1)


def test_bot_maneuvers_around_tree():
    """When forward path is blocked by a tree, bot avoids collision and hops laterally."""
    bot = CrossyBot()
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.GRASS, blocked_x={0}),  # Tree directly ahead at x=0
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    assert action in ((-1, 0), (1, 0))


def test_bot_navigates_multi_tree_cluster_without_getting_stuck():
    """When blocked by a 3-tree cluster (lanes 0, 1, 2), BFS detours safely around it."""
    bot = CrossyBot()
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.GRASS, blocked_x={0, 1, 2}),  # 3 trees blocking forward and right
    })
    # Duck at x=1
    player = MockPlayer(gx=1, gz=0)
    action = bot.decide_next_action(player, world)
    # The open route is to the left (-1, 0)
    assert action == (-1, 0)


def test_bot_waits_for_speeding_car():
    """Bot waits (None) when a car on the road ahead would collide with the duck."""
    bot = CrossyBot()
    # Car at x=0.0 moving slowly across the lane
    danger_car = MockObstacle(x=0.0, speed=0.0, width=2.0)
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.ROAD, obstacles=[danger_car]),
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    # Forward is dangerous; waiting for car to clear
    assert action is None or action in ((-1, 0), (1, 0))
    assert action != (0, 1)


def test_bot_hops_forward_through_road_gap():
    """Bot hops forward into traffic gap when cars are safely away."""
    bot = CrossyBot()
    # Cars are far away on left and right
    safe_cars = [
        MockObstacle(x=-12.0, speed=4.0, width=1.5),
        MockObstacle(x=12.0, speed=-4.0, width=1.5),
    ]
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.ROAD, obstacles=safe_cars),
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    assert action == (0, 1)


def test_bot_refuses_to_jump_into_open_water():
    """In a river row with no log under duck's landing cell, bot will not hop into water."""
    bot = CrossyBot()
    # River with logs far away at x=-10 and x=+10
    distant_logs = [
        MockObstacle(x=-10.0, speed=2.0, width=3.0, is_log=True),
        MockObstacle(x=10.0, speed=2.0, width=3.0, is_log=True),
    ]
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.RIVER, obstacles=distant_logs),
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    # Duck must NOT jump forward into open water
    assert action != (0, 1)


def test_bot_hops_forward_onto_floating_log():
    """When a floating log is positioned ahead, bot safely hops forward onto it."""
    bot = CrossyBot()
    # Log centered right in front of duck
    centered_log = MockObstacle(x=0.0, speed=0.0, width=3.5, is_log=True)
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.RIVER, obstacles=[centered_log]),
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    assert action == (0, 1)


def test_bot_predicts_moving_log_arrival():
    """Bot calculates future log position at t_predict and hops when log arrives."""
    bot = CrossyBot(hop_predict_time=0.16)
    # Log at x = -0.4 with speed = +2.5 -> at t=0.16s, x = -0.4 + 0.4 = 0.0
    approaching_log = MockObstacle(x=-0.4, speed=2.5, width=3.0, is_log=True)
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.RIVER, obstacles=[approaching_log]),
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    assert action == (0, 1)


def test_bot_avoids_rail_during_warning_or_passing():
    """Bot stops and waits when railroad beacon is flashing warning or train is passing."""
    bot = CrossyBot()
    warning_rail = MockRow(1, RowType.RAIL, is_warning=True)
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: warning_rail,
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    assert action != (0, 1)

    # Passing train
    passing_rail = MockRow(1, RowType.RAIL, is_train_passing=True)
    world.active_rows[1] = passing_rail
    action2 = bot.decide_next_action(player, world)
    assert action2 != (0, 1)


def test_bot_crosses_idle_railroad():
    """Bot hops forward across railroad when beacon is unlit and tracks are clear."""
    bot = CrossyBot()
    idle_rail = MockRow(1, RowType.RAIL, is_warning=False, is_train_passing=False)
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: idle_rail,
    })
    player = MockPlayer(gx=0, gz=0)
    action = bot.decide_next_action(player, world)
    assert action == (0, 1)


def test_bot_emergency_evacuation_from_rail():
    """If duck is on tracks and train beacon starts flashing, bot evacuates immediately."""
    bot = CrossyBot()
    cur_rail = MockRow(1, RowType.RAIL, is_warning=True)
    safe_grass = MockRow(2, RowType.GRASS)
    world = MockWorld({
        1: cur_rail,
        2: safe_grass,
    })
    player_on_tracks = MockPlayer(gx=0, gz=1)
    action = bot.decide_next_action(player_on_tracks, world)
    # Evacuation: forward hop to grass
    assert action == (0, 1)


def test_bot_respects_world_boundaries():
    """Bot never decides a hop that leads outside the allowable grid bounds."""
    bot = CrossyBot()
    world = MockWorld({
        0: MockRow(0, RowType.GRASS),
        1: MockRow(1, RowType.GRASS, blocked_x={CELL_MIN_X}),
    })
    # Player at left boundary edge
    player_at_left = MockPlayer(gx=CELL_MIN_X, gz=0)
    action = bot.decide_next_action(player_at_left, world)
    # Must never hop left out of bounds
    assert action != (-1, 0)
