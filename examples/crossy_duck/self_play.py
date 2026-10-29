"""self_play.py - Autonomous AI CrossyBot and Headless Performance Benchmarking.

Part of VelocityEngine Crossy Duck.
Provides:
  - CrossyBot: Predictive autonomous agent that analyzes upcoming traffic,
    railroad beacons, river logs, and obstacle hitboxes to safely hop forward.
  - BenchmarkReport: Precision performance metrics collector computing
    min/avg/max FPS, 95th and 99th percentile frame times, and ASCII summary tables.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any, Sequence

from contracts.crossy_contracts import (
    GRID_STEP,
    CELL_MIN_X,
    CELL_MAX_X,
    RowType,
    PlayerStatus,
)


@dataclass
class BenchmarkReport:
    """Benchmark performance report capturing frame times, FPS metrics, and percentiles."""

    frame_times: List[float] = field(default_factory=list)

    def record_frame(self, dt: float) -> None:
        """Record a single frame duration in seconds."""
        if dt > 0.0:
            self.frame_times.append(float(dt))

    def add_frame_time(self, dt: float) -> None:
        """Alias for record_frame."""
        self.record_frame(dt)

    @property
    def total_frames(self) -> int:
        """Total number of frames recorded."""
        return len(self.frame_times)

    @property
    def total_time_s(self) -> float:
        """Total elapsed benchmarking duration in seconds."""
        return sum(self.frame_times)

    @property
    def avg_fps(self) -> float:
        """Average frames per second across the benchmark."""
        if not self.frame_times or self.total_time_s <= 0.0:
            return 0.0
        return self.total_frames / self.total_time_s

    @property
    def min_fps(self) -> float:
        """Instantaneous minimum FPS (corresponding to maximum frame time)."""
        if not self.frame_times:
            return 0.0
        max_dt = max(self.frame_times)
        return (1.0 / max_dt) if max_dt > 0.0 else 0.0

    @property
    def max_fps(self) -> float:
        """Instantaneous maximum FPS (corresponding to minimum frame time)."""
        if not self.frame_times:
            return 0.0
        min_dt = min(self.frame_times)
        return (1.0 / min_dt) if min_dt > 0.0 else 0.0

    @property
    def avg_ms(self) -> float:
        """Average frame time in milliseconds."""
        if not self.frame_times:
            return 0.0
        return (self.total_time_s / self.total_frames) * 1000.0

    def percentile_ms(self, p: float) -> float:
        """Compute the p-th percentile of frame times in milliseconds."""
        if not self.frame_times:
            return 0.0
        sorted_ms = sorted(t * 1000.0 for t in self.frame_times)
        k = (len(sorted_ms) - 1) * (p / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_ms[int(k)]
        d0 = sorted_ms[int(f)] * (c - k)
        d1 = sorted_ms[int(c)] * (k - f)
        return d0 + d1

    @property
    def p50_ms(self) -> float:
        """Median (50th percentile) frame time in milliseconds."""
        return self.percentile_ms(50.0)

    @property
    def p95_ms(self) -> float:
        """95th percentile frame time in milliseconds."""
        return self.percentile_ms(95.0)

    @property
    def p99_ms(self) -> float:
        """99th percentile frame time in milliseconds."""
        return self.percentile_ms(99.0)

    def summary(self) -> str:
        """Generate a clean ASCII benchmark report table."""
        lines = [
            "+" + "-" * 50 + "+",
            f"|{'VELOCITY ENGINE BENCHMARK REPORT':^50}|",
            "+" + "-" * 50 + "+",
            f"| Frames Sampled      : {self.total_frames:<27} |",
            f"| Total Duration (s)  : {self.total_time_s:<27.3f} |",
            "+" + "-" * 50 + "+",
            f"| Average FPS         : {self.avg_fps:<27.1f} |",
            f"| Minimum FPS         : {self.min_fps:<27.1f} |",
            f"| Maximum FPS         : {self.max_fps:<27.1f} |",
            "+" + "-" * 50 + "+",
            f"| Avg Frame Time      : {self.avg_ms:<24.2f} ms |",
            f"| 50th %ile (Median)  : {self.p50_ms:<24.2f} ms |",
            f"| 95th %ile Frame Time: {self.p95_ms:<24.2f} ms |",
            f"| 99th %ile Frame Time: {self.p99_ms:<24.2f} ms |",
            "+" + "-" * 50 + "+",
        ]
        return "\n".join(lines)

    def print_summary(self) -> None:
        """Print formatted benchmark summary to stdout."""
        print(self.summary())


class CrossyBot:
    """Predictive autonomous AI agent for Crossy Duck self-play.

    Evaluates grid terrain, moving vehicles, rail warning beacons, and floating
    logs over a time horizon to select safe, optimal hops.
    """

    def __init__(
        self,
        lookahead: int = 4,
        hop_predict_time: float = 0.16,
        safety_margin: float = 0.45,
    ) -> None:
        self.lookahead: int = int(lookahead)
        self.hop_predict_time: float = float(hop_predict_time)
        self.safety_margin: float = float(safety_margin)
        self.enabled: bool = True
        self.step_cooldown: float = 0.0

    def decide_next_action(
        self,
        player: Any,
        world: Any,
    ) -> Optional[Tuple[int, int]]:
        """Examine player and world state, returning (dx, dz) hop or None (wait).

        Returns:
            (0, 1)   : Hop forward
            (-1, 0)  : Hop left
            (1, 0)   : Hop right
            (0, -1)  : Hop backward (emergency evacuation)
            None     : Wait / stay in position
        """
        # Bot only initiates hops when the duck is completely IDLE
        status = getattr(player, "status", PlayerStatus.IDLE)
        if status != PlayerStatus.IDLE:
            return None

        # Determine duck's current grid position
        cur_gx = int(getattr(player, "grid_x", 0))
        cur_gz = int(getattr(player, "grid_z", 0))
        real_x = float(getattr(player, "x", float(cur_gx)))
        real_z = float(getattr(player, "z", float(cur_gz)))

        cur_row = self._get_row(world, cur_gz)

        # -------------------------------------------------------------------
        # 1. EMERGENCY ESCAPE CHECK (River edge drift or Train coming)
        # -------------------------------------------------------------------
        emergency_action = self._check_emergency_escape(cur_row, real_x, real_z, cur_gx, cur_gz, world)
        if emergency_action is not None:
            return emergency_action

        # -------------------------------------------------------------------
        # 2. EVALUATE PRIMARY MOVE: HOP FORWARD (0, 1)
        # -------------------------------------------------------------------
        fwd_target_gx = cur_gx
        fwd_target_gz = cur_gz + 1
        if self._is_cell_safe(world, fwd_target_gx, fwd_target_gz, self.hop_predict_time):
            return (0, 1)

        # -------------------------------------------------------------------
        # 3. BFS PATHFINDING DETOUR AROUND OBSTACLES (Trees, Clusters, Gaps)
        # -------------------------------------------------------------------
        detour_action = self._find_path_bfs(world, cur_gx, cur_gz)
        if detour_action is not None:
            return detour_action

        # -------------------------------------------------------------------
        # 4. PATIENT WAITING: Timing gaps in road traffic or awaiting next train/log
        # -------------------------------------------------------------------
        return None

    def _find_path_bfs(
        self,
        world: Any,
        start_gx: int,
        start_gz: int,
        max_depth: int = 6,
    ) -> Optional[Tuple[int, int]]:
        """Breadth-First Search finding optimal detour around static obstacles and traffic."""
        from collections import deque

        # Queue elements: (gx, gz, first_move, depth)
        queue = deque()
        visited = set([(start_gx, start_gz)])

        # Ordered initial lateral moves: prefer centering toward lane 0
        initial_moves = []
        if start_gx > 0:
            initial_moves.extend([(-1, 0), (1, 0)])
        else:
            initial_moves.extend([(1, 0), (-1, 0)])

        for dx, dz in initial_moves:
            nx = start_gx + dx
            nz = start_gz + dz
            if CELL_MIN_X <= nx <= CELL_MAX_X and (nx, nz) not in visited:
                if self._is_cell_safe(world, nx, nz, self.hop_predict_time):
                    # Check if this lateral hop immediately allows jumping forward
                    if self._is_cell_safe(world, nx, nz + 1, self.hop_predict_time * 2.0):
                        return (dx, dz)
                    visited.add((nx, nz))
                    queue.append((nx, nz, (dx, dz), 1))

        # Search up to max_depth steps for a detour around wide tree clusters
        while queue:
            gx, gz, first_move, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for dx, dz in [(0, 1), (-1, 0), (1, 0)]:
                nx = gx + dx
                nz = gz + dz
                if CELL_MIN_X <= nx <= CELL_MAX_X and (nx, nz) not in visited:
                    t_est = self.hop_predict_time * (depth + 1)
                    if self._is_cell_safe(world, nx, nz, t_est):
                        if nz > start_gz:
                            # Reached an open route to the next row!
                            return first_move
                        visited.add((nx, nz))
                        queue.append((nx, nz, first_move, depth + 1))

        # Fallback: If directly facing a solid tree, actively navigate laterally toward nearest open column
        is_tree_ahead = hasattr(world, "is_cell_blocked") and world.is_cell_blocked(start_gx, start_gz + 1)
        if is_tree_ahead and hasattr(world, "is_cell_blocked"):
            open_cols = [x for x in range(CELL_MIN_X, CELL_MAX_X + 1) if not world.is_cell_blocked(x, start_gz + 1)]
            if open_cols:
                best_x = min(open_cols, key=lambda x: (abs(x - start_gx), abs(x)))
                dir_x = 1 if best_x > start_gx else -1
                if self._is_cell_safe(world, start_gx + dir_x, start_gz, self.hop_predict_time):
                    return (dir_x, 0)
                if self._is_cell_safe(world, start_gx - dir_x, start_gz, self.hop_predict_time):
                    return (-dir_x, 0)

        return None

    def _check_emergency_escape(
        self,
        cur_row: Optional[Any],
        real_x: float,
        real_z: float,
        cur_gx: int,
        cur_gz: int,
        world: Any,
    ) -> Optional[Tuple[int, int]]:
        """Evacuate if duck is about to drift off-screen on a log or get run over by a train."""
        if cur_row is None:
            return None

        row_type = getattr(cur_row, "row_type", None)

        # A. River carrier edge drift
        if row_type == RowType.RIVER:
            carrier_vx = getattr(cur_row, "carrier_vx", 0.0)
            # If duck is nearing screen boundaries, must jump!
            if (carrier_vx > 0 and real_x > CELL_MAX_X - 0.5) or (carrier_vx < 0 and real_x < CELL_MIN_X + 0.5):
                # Try forward first
                if self._is_cell_safe(world, cur_gx, cur_gz + 1, self.hop_predict_time):
                    return (0, 1)
                # Try opposite lateral hop against drift
                if carrier_vx > 0 and cur_gx > CELL_MIN_X and self._is_cell_safe(world, cur_gx - 1, cur_gz, self.hop_predict_time):
                    return (-1, 0)
                if carrier_vx < 0 and cur_gx < CELL_MAX_X and self._is_cell_safe(world, cur_gx + 1, cur_gz, self.hop_predict_time):
                    return (1, 0)
                # Fallback: jump backward to safe land
                if self._is_cell_safe(world, cur_gx, cur_gz - 1, self.hop_predict_time):
                    return (0, -1)

        # B. Rail beacon warning or passing train
        elif row_type == RowType.RAIL:
            is_warning = getattr(cur_row, "is_warning", False)
            is_passing = getattr(cur_row, "is_train_passing", False)
            if is_warning or is_passing:
                # Evacuate immediately! Forward is best
                if self._is_cell_safe(world, cur_gx, cur_gz + 1, self.hop_predict_time):
                    return (0, 1)
                if self._is_cell_safe(world, cur_gx, cur_gz - 1, self.hop_predict_time):
                    return (0, -1)
                if cur_gx > CELL_MIN_X and self._is_cell_safe(world, cur_gx - 1, cur_gz, self.hop_predict_time):
                    return (-1, 0)
                if cur_gx < CELL_MAX_X and self._is_cell_safe(world, cur_gx + 1, cur_gz, self.hop_predict_time):
                    return (1, 0)

        return None

    def _get_row(self, world: Any, z: int) -> Optional[Any]:
        """Safely fetch row from world generator or dict."""
        if hasattr(world, "get_row"):
            return world.get_row(z)
        if hasattr(world, "active_rows") and isinstance(world.active_rows, dict):
            return world.active_rows.get(z)
        return None

    def _is_cell_safe(self, world: Any, target_gx: int, target_gz: int, t_predict: float) -> bool:
        """Determine whether the target cell (gx, gz) will be safe to land on at t_predict."""
        if target_gx < CELL_MIN_X or target_gx > CELL_MAX_X:
            return False

        row = self._get_row(world, target_gz)
        if row is None:
            return False

        # Static collision check (e.g. Tree or Rock)
        if hasattr(row, "is_blocked") and row.is_blocked(float(target_gx), float(target_gz)):
            return False

        row_type = getattr(row, "row_type", None)

        # 1. Road Row: Predict vehicle positions over window [t_predict - 0.05, t_predict + 0.15]
        if row_type == RowType.ROAD:
            target_x = float(target_gx)
            target_z = float(target_gz)
            for obs in getattr(row, "obstacles", []):
                obs_speed = getattr(obs, "speed", 0.0)
                obs_w = getattr(obs, "width", 1.5)
                half_w = obs_w * 0.5 + self.safety_margin

                # Check multiple time samples during arrival and post-landing
                for sample_t in (0.0, t_predict * 0.5, t_predict, t_predict + 0.12):
                    future_obs_x = getattr(obs, "x", 0.0) + obs_speed * sample_t
                    # Screen wrap simulation
                    min_wrap = getattr(obs, "min_wrap_x", -48.0)
                    max_wrap = getattr(obs, "max_wrap_x", 48.0)
                    span = max_wrap - min_wrap
                    if span > 0.0:
                        while future_obs_x < min_wrap:
                            future_obs_x += span
                        while future_obs_x > max_wrap:
                            future_obs_x -= span

                    if abs(future_obs_x - target_x) < half_w:
                        return False
            return True

        # 2. River Row: Must land on top of a floating log
        elif row_type == RowType.RIVER:
            target_x = float(target_gx)
            has_carrier_log = False
            for obs in getattr(row, "obstacles", []):
                if not getattr(obs, "is_log", False):
                    continue
                obs_speed = getattr(obs, "speed", 0.0)
                obs_w = getattr(obs, "width", 3.0)
                half_w = max(0.2, (obs_w * 0.5) - 0.25)  # Stay safely on log body

                future_log_x = getattr(obs, "x", 0.0) + obs_speed * t_predict
                min_wrap = getattr(obs, "min_wrap_x", -38.0)
                max_wrap = getattr(obs, "max_wrap_x", 38.0)
                span = max_wrap - min_wrap
                if span > 0.0:
                    while future_log_x < min_wrap:
                        future_log_x += span
                    while future_log_x > max_wrap:
                        future_log_x -= span

                if abs(future_log_x - target_x) <= half_w:
                    has_carrier_log = True
                    break

            # If no log under target_x at landing time, duck drowns
            return has_carrier_log

        # 3. Rail Row: Check warning lights and incoming trains
        elif row_type == RowType.RAIL:
            if getattr(row, "is_warning", False) or getattr(row, "is_train_passing", False):
                return False
            # Check train proximity
            train = getattr(row, "train", None)
            if train is not None:
                train_spd = getattr(train, "speed", 0.0)
                if abs(train_spd) > 0.0:
                    future_train_x = getattr(train, "x", 0.0) + train_spd * t_predict
                    train_w = getattr(train, "width", 16.0)
                    if abs(future_train_x - float(target_gx)) < (train_w * 0.5 + 2.0):
                        return False
            return True

        # 4. Grass / Start Row: Safe if not blocked
        return True
