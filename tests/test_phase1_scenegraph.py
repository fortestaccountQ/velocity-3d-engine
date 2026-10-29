"""Unit tests for Phase 1: Math Core, Quaternion Transforms, Node3D Unified Scene Graph, and Frustum Culling."""

import math
import pytest
import pielosyty as pe


def test_quaternion_math():
    q = pe.quat_from_euler(0.0, 90.0, 0.0)
    assert len(q) == 4
    assert abs(q.w - math.cos(math.radians(45.0))) < 1e-4
    assert abs(q.y - math.sin(math.radians(45.0))) < 1e-4

    e = pe.quat_to_euler(q)
    assert abs(e[1] - 90.0) < 1e-2

    q_axis = pe.quat_from_axis_angle(pe.Vec3(0, 1, 0), 90.0)
    assert abs(q_axis.y - q.y) < 1e-4

    q_look = pe.quat_look_rotation(pe.Vec3(0, 0, -1))
    assert abs(q_look.w - 1.0) < 1e-4

    q_slerp = pe.quat_slerp(pe.Quat(1, 0, 0, 0), q, 0.5)
    assert abs(q_slerp.y - math.sin(math.radians(22.5))) < 1e-3


def test_plane_and_frustum():
    plane = pe.Plane(pe.Vec3(0, 1, 0), -5.0)
    assert abs(plane.distance_to_point(pe.Vec3(0, 10, 0)) - 5.0) < 1e-4

    frustum = pe.Frustum()
    assert frustum.intersects_sphere(pe.Vec3(0, 0, 0), 1.0) is True
    aabb = pe.AABB(pe.Vec3(-1, -1, -1), pe.Vec3(1, 1, 1))
    assert frustum.intersects_aabb(aabb) is True
    assert frustum.intersects_aabb(pe.Vec3(-1, -1, -1), pe.Vec3(1, 1, 1)) is True


def test_transform_quaternion_sync():
    t = pe.Transform()
    t.position = pe.Vec3(1, 2, 3)
    t.rotation = (0, 45, 0)
    assert abs(t.rotation.y - 45.0) < 1e-3
    assert abs(t.orientation.y - math.sin(math.radians(22.5))) < 1e-3

    t.rotation.y += 45.0
    m = t.model_matrix()
    assert m is not None
    assert abs(t.rotation.y - 90.0) < 1e-3

    t.look_at(pe.Vec3(10, 2, 3))
    assert abs(t.rotation.y - (-90.0)) < 1e-2 or abs(t.rotation.y - 270.0) < 1e-2


def test_node3d_hierarchy_propagation():
    parent = pe.Node3D("ParentNode")
    parent.tag = "root_group"
    child = pe.Node3D("ChildNode")
    child.tag = "child_tag"
    grandchild = pe.Node3D("GrandChild")

    parent.add(child)
    child.add(grandchild)

    parent.transform.position = pe.Vec3(10, 0, 0)
    child.transform.position = pe.Vec3(0, 5, 0)
    grandchild.transform.position = pe.Vec3(0, 0, 2)

    assert abs(grandchild.world_position().x - 10.0) < 1e-4
    assert abs(grandchild.world_position().y - 5.0) < 1e-4
    assert abs(grandchild.world_position().z - 2.0) < 1e-4

    loc = grandchild.world_to_local(pe.Vec3(10, 5, 2))
    assert abs(loc.x) < 1e-4 and abs(loc.y) < 1e-4 and abs(loc.z) < 1e-4

    assert parent.get_by_name("GrandChild") == grandchild
    tagged = parent.find_all_by_tag("child_tag")
    assert len(tagged) == 1 and tagged[0] == child

    child.remove(grandchild)
    assert grandchild.parent is None
    assert len(child.children) == 0

    parent.clear()


def test_polymorphic_subclasses():
    parent = pe.Node3D("Parent")

    ent = pe.Entity(1, "Hero")
    assert isinstance(ent, pe.Node3D)
    parent.add(ent)
    ent.transform.position = pe.Vec3(3, 0, 0)
    assert abs(ent.world_position().x - 3.0) < 1e-4

    cam = pe.Camera()
    assert isinstance(cam, pe.Node3D)
    cam.set_perspective(60.0, 16.0 / 9.0, 0.1, 1000.0)
    parent.add(cam)
    cam.transform.position = pe.Vec3(0, 10, 20)
    assert abs(cam.world_position().y - 10.0) < 1e-4

    sun = pe.DirectionalLight("Sun")
    assert isinstance(sun, pe.Node3D)
    assert isinstance(sun, pe.Light)
    sun.set_direction(-1, -1, 0)
    parent.add(sun)

    mesh = pe.Mesh.create_cube()
    inst = pe.InstancedMesh(mesh, 10)
    assert isinstance(inst, pe.Node3D)
    parent.add(inst)
    assert inst.instance_count() == 10

    scene = pe.Scene()
    scene.add(parent)
    assert len(scene.entities) >= 1
    assert len(scene.instanced_meshes) >= 1

    parent.clear()
    scene.clear()


def test_render_stats():
    app = pe.EngineApp("StatsTest", 100, 100)
    stats = app.stats
    assert stats.draw_calls == 0
    assert stats.culled_objects == 0
    assert stats.total_triangles == 0
    assert stats.total_instances == 0
