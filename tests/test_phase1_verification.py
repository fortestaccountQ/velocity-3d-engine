"""Comprehensive verification and hostile edge-case test suite for Phase 1:
Math Core, Quaternion Transforms, Unified Node3D Scene Graph, and Frustum Culling.

Verifies the Phase 1 Acceptance Criterion:
"Камера и источник света, добавленные как .add() к вращающемуся по кватерниону Group,
синхронно движутся в мире; объекты за спиной камеры отсекаются фрустумом."
"""

import math
import pytest
import pielosyty as pe


class TestQuaternionTransforms:
    """Verifies Quaternion-based Transform, orientation property, Euler sync, look_at, and gimbal-lock immunity."""

    def test_orientation_property_and_defaults(self):
        t = pe.Transform()
        q = t.orientation
        assert abs(q.w - 1.0) < 1e-5
        assert abs(q.x) < 1e-5
        assert abs(q.y) < 1e-5
        assert abs(q.z) < 1e-5

        # Setting orientation directly
        new_q = pe.quat_from_axis_angle(pe.Vec3(0, 1, 0), 90.0)
        t.orientation = new_q
        assert abs(t.orientation.y - math.sin(math.radians(45.0))) < 1e-4
        assert abs(t.orientation.w - math.cos(math.radians(45.0))) < 1e-4

    def test_euler_to_quaternion_sync(self):
        t = pe.Transform()
        t.rotation = (0, 45, 0)
        assert abs(t.rotation.y - 45.0) < 1e-3
        expected_y = math.sin(math.radians(22.5))
        assert abs(t.orientation.y - expected_y) < 1e-3

        # Modify rotation component directly
        t.rotation.y += 45.0
        m = t.model_matrix()
        assert m is not None
        assert abs(t.rotation.y - 90.0) < 1e-3
        assert abs(t.orientation.y - math.sin(math.radians(45.0))) < 1e-3

    def test_quaternion_to_euler_sync(self):
        t = pe.Transform()
        # Rotate 60 degrees around X
        t.orientation = pe.quat_from_axis_angle(pe.Vec3(1, 0, 0), 60.0)
        assert abs(t.rotation.x - 60.0) < 1e-2
        assert abs(t.rotation.y) < 1e-2
        assert abs(t.rotation.z) < 1e-2

    def test_look_at_directional_vectors(self):
        t = pe.Transform()
        t.position = pe.Vec3(0, 0, 0)

        # Look at +X (should rotate yaw to face right)
        t.look_at(pe.Vec3(10, 0, 0))
        m = t.model_matrix()
        # Forward (-Z in local) rotated to world should point towards +X
        fwd_world = t.orientation * pe.Vec3(0, 0, -1)
        assert abs(fwd_world.x - 1.0) < 1e-3
        assert abs(fwd_world.y) < 1e-3
        assert abs(fwd_world.z) < 1e-3

        # Look at +Z (facing backward)
        t.look_at(pe.Vec3(0, 0, 10))
        fwd_world = t.orientation * pe.Vec3(0, 0, -1)
        assert abs(fwd_world.z - 1.0) < 1e-3

    def test_rotate_on_axis_arbitrary(self):
        t = pe.Transform()
        axis = pe.Vec3(1, 1, 0)  # non-normalized
        len_axis = math.sqrt(2.0)
        norm_axis = pe.Vec3(1.0 / len_axis, 1.0 / len_axis, 0.0)

        t.rotate_on_axis(norm_axis, 90.0)
        q = t.orientation
        assert not math.isnan(q.w) and not math.isnan(q.x)
        assert abs(math.sqrt(q.w**2 + q.x**2 + q.y**2 + q.z**2) - 1.0) < 1e-4

    def test_non_gimbal_lock_rotation(self):
        """Euler rotations at pitch = 90 deg suffer gimbal lock; quaternion rotations must preserve all 3 DOF."""
        t = pe.Transform()
        # Rotate pitch 90 degrees
        t.rotate_x(90.0)
        # Rotate roll 90 degrees
        t.rotate_z(90.0)
        # Rotate yaw 90 degrees
        t.rotate_y(90.0)

        q = t.orientation
        # Ensure no singularity, no NaNs, and valid unit quaternion
        assert not math.isnan(q.w) and not math.isnan(q.x) and not math.isnan(q.y) and not math.isnan(q.z)
        norm = math.sqrt(q.w * q.w + q.x * q.x + q.y * q.y + q.z * q.z)
        assert abs(norm - 1.0) < 1e-4

        # Model matrix remains invertible
        m = t.model_matrix()
        det = (
            m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
            - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
            + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
        )
        assert abs(abs(det) - 1.0) < 1e-3


class TestNode3DHierarchy:
    """Verifies Node3D parenting, traversal, transform propagation, and hostile edge cases."""

    def test_parent_child_lifecycle(self):
        parent = pe.Node3D("Parent")
        child = pe.Node3D("Child")

        assert child.parent is None
        assert len(parent.children) == 0

        parent.add(child)
        assert child.parent == parent
        assert len(parent.children) == 1
        assert parent.children[0] == child

        # Adding same child twice is idempotent
        parent.add(child)
        assert len(parent.children) == 1

        # Reparenting to new parent
        parent2 = pe.Node3D("Parent2")
        parent2.add(child)
        assert child.parent == parent2
        assert len(parent.children) == 0
        assert len(parent2.children) == 1

        # Remove from parent
        child.remove_from_parent()
        assert child.parent is None
        assert len(parent2.children) == 0

        # Clear
        parent.add(child)
        parent.clear()
        assert len(parent.children) == 0
        assert child.parent is None

    def test_deep_hierarchy_transform_propagation(self):
        """15-level deep hierarchy propagating translation and quaternion rotation."""
        depth = 15
        nodes = [pe.Node3D(f"Node_{i}") for i in range(depth)]
        for i in range(depth - 1):
            nodes[i].add(nodes[i + 1])
            nodes[i + 1].transform.position = pe.Vec3(1, 0, 0)

        deepest = nodes[-1]
        assert abs(deepest.world_position().x - float(depth - 1)) < 1e-4
        assert abs(deepest.world_position().y) < 1e-4
        assert abs(deepest.world_position().z) < 1e-4

        # Rotate root 90 degrees around Y axis
        root = nodes[0]
        root.transform.orientation = pe.quat_from_axis_angle(pe.Vec3(0, 1, 0), 90.0)

        # In right-handed coords, +X rotated +90 around Y lands on -Z
        pos = deepest.world_position()
        assert abs(pos.x) < 1e-3
        assert abs(pos.y) < 1e-3
        assert abs(pos.z - (-float(depth - 1))) < 1e-3

        # Clean up
        for n in nodes:
            n.clear()

    def test_world_to_local_invertibility(self):
        parent = pe.Node3D("P")
        child = pe.Node3D("C")
        parent.add(child)

        parent.transform.position = pe.Vec3(10, 20, 30)
        parent.transform.orientation = pe.quat_from_axis_angle(pe.Vec3(0, 1, 0), 45.0)
        child.transform.position = pe.Vec3(1, 2, 3)

        world_p = child.world_position()
        local_p = child.world_to_local(world_p)

        assert abs(local_p.x) < 1e-4
        assert abs(local_p.y) < 1e-4
        assert abs(local_p.z) < 1e-4

        recon_world = child.local_to_world(local_p)
        assert abs(recon_world.x - world_p.x) < 1e-4
        assert abs(recon_world.y - world_p.y) < 1e-4
        assert abs(recon_world.z - world_p.z) < 1e-4

        parent.clear()

    def test_search_by_name_and_tag(self):
        root = pe.Node3D("Root")
        c1 = pe.Node3D("Child1")
        c1.tag = "enemy"
        c2 = pe.Node3D("Child2")
        c2.tag = "enemy"
        c3 = pe.Node3D("Child3")
        c3.tag = "ally"

        root.add(c1)
        c1.add(c2)
        root.add(c3)

        assert root.get_by_name("Child2") == c2
        assert root.get_by_name("NonExistent") is None

        enemies = root.find_all_by_tag("enemy")
        assert len(enemies) == 2
        assert c1 in enemies and c2 in enemies

        allies = root.find_all_by_tag("ally")
        assert len(allies) == 1 and allies[0] == c3

        root.clear()

    def test_hostile_cycle_prevention(self):
        """Hostile tests: attempts to construct cyclic parent-child links must be rejected."""
        a = pe.Node3D("A")
        b = pe.Node3D("B")
        c = pe.Node3D("C")

        # 1. Self-add
        a.add(a)
        assert len(a.children) == 0

        # 2. 2-node cycle: A -> B, then B.add(A)
        a.add(b)
        assert b.parent == a
        b.add(a)
        assert a.parent != b
        assert len(b.children) == 0

        # 3. 3-node cycle: A -> B -> C, then C.add(A)
        b.add(c)
        assert c.parent == b
        c.add(a)
        assert a.parent != c
        assert len(c.children) == 0

        # 4. Multi-level cycle attempt: A -> B -> C -> D -> E, then E.add(B)
        d = pe.Node3D("D")
        e = pe.Node3D("E")
        c.add(d)
        d.add(e)
        e.add(b)
        assert b.parent == a
        assert len(e.children) == 0

        a.clear()

    def test_empty_group_safety(self):
        g = pe.Group("EmptyGroup")
        assert len(g.children) == 0
        assert g.parent is None
        # World transforms on empty group must be valid
        assert g.world_position() is not None
        assert g.world_direction() is not None
        g.clear()


class TestPhase1AcceptanceCriterion:
    """Verifies the exact Phase 1 Acceptance Criterion from задание.txt:
    'Камера и источник света, добавленные как .add() к вращающемуся по кватерниону Group,
     синхронно движутся в мире; объекты за спиной камеры отсекаются фрустумом.'
    """

    def test_camera_and_light_synchronous_movement_with_rotating_group(self):
        rig = pe.Group("LightingAndCameraRig")
        rig.transform.position = pe.Vec3(0, 5, 0)

        # Attach Camera as child
        cam = pe.Camera()
        cam.set_perspective(60.0, 16.0 / 9.0, 0.1, 1000.0)
        cam.transform.position = pe.Vec3(0, 0, 10)  # local offset 10 along Z
        rig.add(cam)

        # Attach DirectionalLight as child
        sun = pe.DirectionalLight("Sun")
        sun.set_direction(0, 0, -1)  # pointing along -Z locally
        rig.add(sun)

        # 1. Initial State verification
        initial_cam_pos = cam.world_position()
        assert abs(initial_cam_pos.x) < 1e-4
        assert abs(initial_cam_pos.y - 5.0) < 1e-4
        assert abs(initial_cam_pos.z - 10.0) < 1e-4

        initial_sun_dir = sun.world_direction()
        assert abs(initial_sun_dir.x) < 1e-4
        assert abs(initial_sun_dir.y) < 1e-4
        assert abs(initial_sun_dir.z - (-1.0)) < 1e-4

        # 2. Rotate Group by 90 degrees around Y via quaternion
        q_90 = pe.quat_from_axis_angle(pe.Vec3(0, 1, 0), 90.0)
        rig.transform.orientation = q_90

        # In right-handed coords, (0, 0, 10) rotated +90 around Y lands on (+10, 0, 0)
        rot_cam_pos = cam.world_position()
        assert abs(rot_cam_pos.x - 10.0) < 1e-3
        assert abs(rot_cam_pos.y - 5.0) < 1e-3
        assert abs(rot_cam_pos.z) < 1e-3

        # Light direction (0, 0, -1) rotated +90 around Y lands on (-1, 0, 0)
        rot_sun_dir = sun.world_direction()
        assert abs(rot_sun_dir.x - (-1.0)) < 1e-3
        assert abs(rot_sun_dir.y) < 1e-3
        assert abs(rot_sun_dir.z) < 1e-3

        # Camera view matrix updates to reflect parent group world transform
        view_m = cam.view_matrix()
        assert view_m is not None

        # 3. Rotate Group by 180 degrees around Y via quaternion
        q_180 = pe.quat_from_axis_angle(pe.Vec3(0, 1, 0), 180.0)
        rig.transform.orientation = q_180

        pos_180 = cam.world_position()
        assert abs(pos_180.x) < 1e-3
        assert abs(pos_180.y - 5.0) < 1e-3
        assert abs(pos_180.z - (-10.0)) < 1e-3

        dir_180 = sun.world_direction()
        assert abs(dir_180.x) < 1e-3
        assert abs(dir_180.y) < 1e-3
        assert abs(dir_180.z - 1.0) < 1e-3

        rig.clear()

    def test_frustum_culling_behind_camera_acceptance(self):
        """Verifies that objects behind the camera are culled and increment stats.culled_objects,
        while objects inside the frustum increment stats.draw_calls."""
        app = pe.EngineApp("CullingVerification", 800, 600)
        scene = app.scene
        cam = app.camera

        # Camera at (0, 2, 5) looking forward towards (0, 2, 0) along -Z
        cam.set_position(0.0, 2.0, 5.0)
        cam.set_target(0.0, 2.0, 0.0)

        # 1. Object directly in front of camera (Z = 0.0) -> inside frustum
        cube_front = scene.create_cube()
        cube_front.transform.position = pe.Vec3(0, 2, 0)

        # 2. Object further ahead in front of camera (Z = -5.0) -> inside frustum
        cube_ahead = scene.create_cube()
        cube_ahead.transform.position = pe.Vec3(0, 2, -5)

        # 3. Object behind the camera (Z = 15.0) -> behind camera, MUST BE CULLED
        cube_behind = scene.create_cube()
        cube_behind.transform.position = pe.Vec3(0, 2, 15)

        # 4. Object far to the side (X = 100.0) -> outside frustum, MUST BE CULLED
        cube_lateral = scene.create_cube()
        cube_lateral.transform.position = pe.Vec3(100, 2, 0)

        # Evaluate frustum culling
        app.evaluate_frustum_culling()

        stats = app.stats
        assert stats.draw_calls == 2, f"Expected 2 draw calls, got {stats.draw_calls}"
        assert stats.culled_objects == 2, f"Expected 2 culled objects, got {stats.culled_objects}"
        assert stats.total_triangles == 24, f"Expected 24 triangles (2 cubes x 12 tris), got {stats.total_triangles}"

        # Now rotate camera 180 degrees to look toward +Z (facing the previously behind object)
        cam.set_target(0.0, 2.0, 20.0)
        app.evaluate_frustum_culling()

        # Now cube_behind (Z=15) is in front of camera, while cube_front (Z=0) and cube_ahead (Z=-5) are behind!
        stats2 = app.stats
        assert stats2.draw_calls == 1, f"Expected 1 draw call after 180 flip, got {stats2.draw_calls}"
        assert stats2.culled_objects == 3, f"Expected 3 culled objects after 180 flip, got {stats2.culled_objects}"

        scene.clear()

    def test_frustum_geometric_math_core(self):
        """Verifies Frustum and Plane extraction from camera View-Projection matrix."""
        cam = pe.Camera()
        cam.set_perspective(60.0, 1.0, 0.1, 100.0)
        cam.set_position(0.0, 0.0, 10.0)
        cam.set_target(0.0, 0.0, 0.0)

        vp = cam.view_projection_matrix()
        frustum = pe.Frustum()
        frustum.set_from_projection_matrix(vp)

        # Inside frustum at origin
        assert frustum.intersects_sphere(pe.Vec3(0, 0, 0), 1.0) is True
        assert frustum.intersects_aabb(pe.Vec3(-1, -1, -1), pe.Vec3(1, 1, 1)) is True

        # Behind camera (Z = 20)
        assert frustum.intersects_sphere(pe.Vec3(0, 0, 20), 1.0) is False
        assert frustum.intersects_aabb(pe.Vec3(-1, -1, 15), pe.Vec3(1, 1, 25)) is False

        # Beyond far plane (Z = -150)
        assert frustum.intersects_sphere(pe.Vec3(0, 0, -150), 1.0) is False
        assert frustum.intersects_aabb(pe.Vec3(-1, -1, -160), pe.Vec3(1, 1, -140)) is False
