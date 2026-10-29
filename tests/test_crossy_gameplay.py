"""Unit tests for Crossy Duck gameplay mechanics, math, camera, and state machines."""

import pytest
from contracts.crossy_contracts import (
    CELL_MIN_X,
    CELL_MAX_X,
    PlayerStatus,
    RowType,
)
from examples.crossy_duck.player import (
    PlayerController,
    HOP_DURATION,
    JUMP_HEIGHT,
    IDLE_TIMEOUT,
    BASE_SCALE,
)
from examples.crossy_duck.camera_vfx import (
    IsometricCamera,
    CrossyHUD,
)


class MockWorldRow:
    """Mock WorldRow for deterministic hazard testing."""

    def __init__(self, is_hazardous=False, reason=None, carrier_vx=None):
        self.is_hazardous = is_hazardous
        self.reason = reason
        self.carrier_vx = carrier_vx
        self.z_index = 0
        self.row_type = RowType.ROAD
        self.entities = []
        self.obstacles = []

    def update(self, dt: float) -> None:
        pass

    def check_player_hazard(self, px: float, pz: float):
        return (self.is_hazardous, self.reason, self.carrier_vx)

    def cleanup(self, scene) -> None:
        pass


class MockCamera:
    """Mock engine camera capturing set_position and set_target calls."""

    def __init__(self):
        self.position = (0.0, 0.0, 0.0)
        self.target = (0.0, 0.0, 0.0)

    def set_position(self, x: float, y: float, z: float):
        self.position = (float(x), float(y), float(z))

    def set_target(self, x: float, y: float, z: float):
        self.target = (float(x), float(y), float(z))


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_player_initial_state():
    """Verify player initializes at origin with correct baseline metrics."""
    player = PlayerController(grid_x=0, grid_z=0)
    assert player.grid_x == 0
    assert player.grid_z == 0
    assert player.x == 0.0
    assert player.y == 0.0
    assert player.z == 0.0
    assert player.status == PlayerStatus.IDLE
    assert player.score == 0
    assert player.highest_z == 0
    assert player.coins == 0
    assert player.carrier_vx == 0.0
    assert player.rotation_y == 0.0
    assert player.idle_timer == 0.0


def test_player_hop_forward_math_and_parabola():
    """Verify snappy hop movement, parabolic arc height, and landing completion."""
    player = PlayerController(grid_x=0, grid_z=0)
    success = player.hop(0, 1)
    assert success is True
    assert player.status == PlayerStatus.HOPPING
    assert player.rotation_y == 0.0

    # Step to midpoint of hop duration
    half_time = HOP_DURATION * 0.5
    player.update(half_time)

    assert player.status == PlayerStatus.HOPPING
    # Parabolic arc at t=0.5 must be near peak jump height
    assert pytest.approx(player.y, abs=0.05) == JUMP_HEIGHT
    assert pytest.approx(player.z, abs=0.05) == 0.5
    assert pytest.approx(player.x, abs=0.01) == 0.0

    # Complete the hop
    player.update(half_time + 0.01)
    assert player.status == PlayerStatus.IDLE
    assert pytest.approx(player.y, abs=0.01) == 0.0
    assert pytest.approx(player.z, abs=0.01) == 1.0
    assert player.grid_z == 1
    assert player.highest_z == 1
    assert player.score == 1


def test_player_grid_boundary_clamping():
    """Verify player cannot hop outside world boundaries [-10, 10]."""
    # Max positive boundary
    player = PlayerController(grid_x=CELL_MAX_X, grid_z=0)
    blocked = player.hop(1, 0)
    assert blocked is False
    assert player.grid_x == CELL_MAX_X
    assert player.status == PlayerStatus.IDLE

    # Max negative boundary
    player = PlayerController(grid_x=CELL_MIN_X, grid_z=0)
    blocked = player.hop(-1, 0)
    assert blocked is False
    assert player.grid_x == CELL_MIN_X
    assert player.status == PlayerStatus.IDLE

    # Inward hop is permitted
    allowed = player.hop(1, 0)
    assert allowed is True
    assert player.status == PlayerStatus.HOPPING


def test_player_rotation_directions():
    """Verify duck turns to face direction of hop."""
    player = PlayerController(grid_x=0, grid_z=0)

    # Forward
    player.hop(0, 1)
    assert player.rotation_y == 0.0
    player.update(HOP_DURATION + 0.01)

    # Right
    player.hop(1, 0)
    assert player.rotation_y == 90.0
    player.update(HOP_DURATION + 0.01)

    # Left
    player.hop(-1, 0)
    assert player.rotation_y == -90.0
    player.update(HOP_DURATION + 0.01)

    # Backward
    player.hop(0, -1)
    assert player.rotation_y == 180.0


def test_player_backward_hop_limit():
    """Verify player can backtrack slightly but cannot walk indefinitely into pruned zones."""
    player = PlayerController(grid_x=0, grid_z=0)

    # Hop forward to z=7
    for _ in range(7):
        player.hop(0, 1)
        player.update(HOP_DURATION + 0.01)

    assert player.highest_z == 7
    assert player.grid_z == 7

    # Can hop backward
    assert player.hop(0, -1) is True
    player.update(HOP_DURATION + 0.01)
    assert player.grid_z == 6

    # Move player down to lower limit (highest_z - 6 = 1)
    while player.grid_z > 1:
        player.hop(0, -1)
        player.update(HOP_DURATION + 0.01)

    assert player.grid_z == 1
    # At z=1, trying to backtrack below 1 is blocked
    blocked = player.hop(0, -1)
    assert blocked is False
    assert player.grid_z == 1


def test_score_incrementing_and_high_score():
    """Verify score tracks highest forward Z reached, not decreasing on backward moves."""
    player = PlayerController(grid_x=0, grid_z=0)

    player.hop(0, 1)
    player.update(HOP_DURATION + 0.01)
    assert player.score == 1
    assert player.highest_z == 1

    player.hop(0, 1)
    player.update(HOP_DURATION + 0.01)
    assert player.score == 2
    assert player.highest_z == 2

    # Backward step does not decrease highest_z or score
    player.hop(0, -1)
    player.update(HOP_DURATION + 0.01)
    assert player.grid_z == 1
    assert player.score == 2
    assert player.highest_z == 2


def test_camera_target_tracking_math():
    """Verify isometric camera positioning and target look-at calculations."""
    mock_cam = MockCamera()
    iso_cam = IsometricCamera(camera=mock_cam, damping=10.0)

    # Player at (3.0, 0.0, 15.0)
    des_pos = iso_cam.get_desired_position(3.0, 0.0, 15.0)
    des_tgt = iso_cam.get_desired_target(3.0, 0.0, 15.0)

    # Expected: pos = (px - 7.0, 11.0, pz - 8.5)
    assert pytest.approx(des_pos[0]) == 3.0 - 7.0
    assert pytest.approx(des_pos[1]) == 11.0
    assert pytest.approx(des_pos[2]) == 15.0 - 8.5

    # Expected: target = (px, 0.5, pz + 1.5)
    assert pytest.approx(des_tgt[0]) == 3.0
    assert pytest.approx(des_tgt[1]) == 0.5
    assert pytest.approx(des_tgt[2]) == 16.5

    # Test snap_to
    class DummyPlayer:
        x = 3.0
        y = 0.0
        z = 15.0

    iso_cam.snap_to(DummyPlayer())
    assert pytest.approx(mock_cam.position[0]) == -4.0
    assert pytest.approx(mock_cam.position[1]) == 11.0
    assert pytest.approx(mock_cam.position[2]) == 6.5
    assert pytest.approx(mock_cam.target[0]) == 3.0
    assert pytest.approx(mock_cam.target[1]) == 0.5
    assert pytest.approx(mock_cam.target[2]) == 16.5

    # Test smooth damping update
    DummyPlayer.z = 16.0
    iso_cam.update(0.05, DummyPlayer())
    # pos_z should smoothly increase toward 16.0 - 8.5 = 7.5
    assert mock_cam.position[2] > 6.5
    assert mock_cam.position[2] < 7.5


def test_hud_high_score_persistence():
    """Verify CrossyHUD maintains high score through player resets."""
    hud = CrossyHUD(app=None)
    assert hud.high_score == 0

    hud.update_high_score(12)
    assert hud.high_score == 12

    # Lower score does not overwrite high score
    hud.update_high_score(5)
    assert hud.high_score == 12

    # Higher score updates high score
    hud.update_high_score(19)
    assert hud.high_score == 19


def test_water_riding_and_drowning():
    """Verify log riding velocity and drowning in hazardous water."""
    player = PlayerController(grid_x=0, grid_z=3)

    # 1. Safe log riding with carrier velocity
    safe_log_row = MockWorldRow(is_hazardous=False, reason=None, carrier_vx=2.5)
    player.update(0.1, safe_log_row)
    assert pytest.approx(player.carrier_vx) == 2.5
    assert pytest.approx(player.x) == 0.25
    assert player.status == PlayerStatus.IDLE

    # 2. Hazard: water drowning
    drown_row = MockWorldRow(is_hazardous=True, reason="DROWN", carrier_vx=None)
    player.update(0.05, drown_row)
    assert player.status == PlayerStatus.DROWNED
    assert player.death_reason == "DROWN"


def test_car_hazard_squashed():
    """Verify car collision triggers SQUASHED state and squashing scale."""
    player = PlayerController(grid_x=0, grid_z=2)
    car_row = MockWorldRow(is_hazardous=True, reason="CAR", carrier_vx=None)

    player.update(0.05, car_row)
    assert player.status == PlayerStatus.SQUASHED
    assert player.death_reason == "CAR"

    # Further updates animate squash flattening
    player.update(0.1)
    assert player.scale_y < BASE_SCALE
    assert player.scale_x > BASE_SCALE


def test_idle_timeout_death():
    """Verify staying idle for > idle_timeout seconds triggers EATEN game over."""
    player = PlayerController(grid_x=0, grid_z=0, idle_timeout=8.0)
    assert player.idle_timer == 0.0

    # Advance 4.0 seconds - still alive
    player.update(4.0)
    assert player.status == PlayerStatus.IDLE
    assert pytest.approx(player.idle_timer) == 4.0

    # Advance beyond 8.0s timeout
    player.update(4.5)
    assert player.status == PlayerStatus.EATEN
    assert player.death_reason == "IDLE_TIMEOUT"


def test_coin_collection():
    """Verify coin collection increments counter."""
    player = PlayerController(grid_x=0, grid_z=0)
    assert player.coins == 0
    player.collect_coin(1)
    assert player.coins == 1
    player.collect_coin(5)
    assert player.coins == 6


def test_player_reset():
    """Verify player reset restores original state."""
    player = PlayerController(grid_x=3, grid_z=5)
    player.hop(0, 1)
    player.update(HOP_DURATION + 0.01)
    player.collect_coin(3)
    player.die(PlayerStatus.SQUASHED, "CAR")

    assert player.status == PlayerStatus.SQUASHED
    assert player.score > 0

    player.reset()
    assert player.grid_x == 0
    assert player.grid_z == 0
    assert player.x == 0.0
    assert player.y == 0.0
    assert player.z == 0.0
    assert player.status == PlayerStatus.IDLE
    assert player.score == 0
    assert player.highest_z == 0
    assert player.death_reason is None


def test_voxel_duck_composite_character():
    """Verify procedural composite voxel duck contains all handcrafted anatomy parts."""
    class MockScene:
        def __init__(self):
            self.created_boxes = []

        def create_entity(self, name=""):
            class MockEntity:
                def __init__(self, name):
                    self.name = name
                    self.material = None
                    self.parent = None
                    class MockT:
                        def __init__(self):
                            self.position = (0, 0, 0)
                            self.rotation = (0, 0, 0)
                            self.scale = (1, 1, 1)
                    self.transform = MockT()
            return MockEntity(name)

        def create_box(self, size=(1, 1, 1), color=None, material=None, name=""):
            ent = self.create_entity(name)
            ent.size = size
            ent.color = color
            ent.material = material
            self.created_boxes.append(ent)
            return ent

    scene = MockScene()
    player = PlayerController(scene=scene)
    assert player.is_voxel_duck is True
    assert player.entity is not None
    assert player.entity.name == "VoxelDuck"

    # Verify all anatomical parts are created: body, head, beak, eyes, pupils, wings, tail, feet
    part_names = [p.name for p in player.voxel_parts]
    expected_parts = [
        "DuckBody", "DuckHead", "DuckBeak", "DuckEyeL", "DuckEyeR",
        "DuckPupilL", "DuckPupilR", "DuckWingL", "DuckWingR", "DuckTail",
        "DuckFootL", "DuckFootR"
    ]
    for exp in expected_parts:
        assert exp in part_names, f"Missing duck part {exp} in voxel duck"


def test_app_vsync_and_frame_timing_properties():
    """Verify VSync configuration and frame diagnostics on App."""
    try:
        import VelocityEngine as ve
        app = ve.App(title="VSyncTest", width=640, height=480, vsync=True)
        assert app.vsync is True
        app.vsync = False
        assert app.vsync is False
        assert isinstance(app.fps, (int, float))
        assert isinstance(app.frame_time_ms, (int, float))
    except ImportError:
        pass
