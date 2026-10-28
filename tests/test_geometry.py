import math
import pytest
import VelocityEngine as ve


def test_create_box():
    w, h, d = 2.0, 4.0, 6.0
    box = ve.Mesh.create_box(w, h, d)
    assert box.num_indices == 36
    assert abs(box.local_aabb.min_point.x - (-1.0)) < 1e-5
    assert abs(box.local_aabb.max_point.x - (1.0)) < 1e-5
    assert abs(box.local_aabb.min_point.y - (-2.0)) < 1e-5
    assert abs(box.local_aabb.max_point.y - (2.0)) < 1e-5
    assert abs(box.local_aabb.min_point.z - (-3.0)) < 1e-5
    assert abs(box.local_aabb.max_point.z - (3.0)) < 1e-5
    assert box.local_aabb.is_valid()


def test_create_sphere():
    radius = 1.5
    rings, sectors = 16, 16
    sphere = ve.Mesh.create_sphere(radius, rings, sectors)
    # (rings - 1) * sectors * 6 indices
    assert sphere.num_indices == (rings - 1) * sectors * 6
    assert abs(sphere.local_aabb.min_point.y - (-radius)) < 1e-4
    assert abs(sphere.local_aabb.max_point.y - radius) < 1e-4
    assert sphere.local_aabb.is_valid()


def test_create_cylinder():
    r, h, segs = 0.5, 2.0, 16
    cyl_capped = ve.Mesh.create_cylinder(r, h, segs, True)
    # Side: 16 * 6 = 96, top: 16 * 3 = 48, bot: 16 * 3 = 48 -> 192
    assert cyl_capped.num_indices == 192
    assert abs(cyl_capped.local_aabb.min_point.y - (-1.0)) < 1e-5
    assert abs(cyl_capped.local_aabb.max_point.y - 1.0) < 1e-5

    cyl_uncapped = ve.Mesh.create_cylinder(r, h, segs, False)
    assert cyl_uncapped.num_indices == 96


def test_create_plane():
    p1 = ve.Mesh.create_plane(10.0, 10.0, 1, 1)
    assert p1.num_indices == 6

    p5 = ve.Mesh.create_plane(10.0, 10.0, 5, 5)
    assert p5.num_indices == 5 * 5 * 6  # 150
    assert abs(p5.local_aabb.min_point.x - (-5.0)) < 1e-5
    assert abs(p5.local_aabb.max_point.x - 5.0) < 1e-5
    assert abs(p5.local_aabb.min_point.z - (-5.0)) < 1e-5
    assert abs(p5.local_aabb.max_point.z - 5.0) < 1e-5
    assert p5.local_aabb.is_valid()


def test_create_custom():
    verts = [
        0.0, 0.0, 0.0,  0.0, 1.0, 0.0,  0.0, 0.0,  1.0, 1.0, 1.0, 1.0,
        2.0, 0.0, 0.0,  0.0, 1.0, 0.0,  1.0, 0.0,  1.0, 1.0, 1.0, 1.0,
        0.0, 3.0, 0.0,  0.0, 1.0, 0.0,  0.0, 1.0,  1.0, 1.0, 1.0, 1.0
    ]
    indices = [0, 1, 2]
    custom = ve.Mesh.create_custom(verts, indices, 12)
    assert custom.num_indices == 3
    assert abs(custom.local_aabb.max_point.x - 2.0) < 1e-5
    assert abs(custom.local_aabb.max_point.y - 3.0) < 1e-5


def test_camera_screen_to_ray():
    cam = ve.Camera()
    cam.set_position(0, 0, 10)
    cam.set_target(0, 0, 0)
    ray = cam.screen_to_ray(640, 360, 1280, 720)
    # Ray through center should point directly in -Z
    assert abs(ray.direction.x) < 1e-4
    assert abs(ray.direction.y) < 1e-4
    assert abs(ray.direction.z - (-1.0)) < 1e-4


def test_scene_factory_and_raycast():
    scene = ve.Scene()
    box_ent = scene.create_box((2, 2, 2), (1, 0, 0, 1))
    sphere_ent = scene.create_sphere(1.0, 16, 16, (0, 1, 0, 1))
    cyl_ent = scene.create_cylinder(0.5, 2.0, 16, True, (0, 0, 1, 1))
    plane_ent = scene.create_plane(10, 5)

    assert box_ent is not None
    assert sphere_ent is not None
    assert cyl_ent is not None
    assert plane_ent is not None

    # Test raycast against isolated target
    raycast_scene = ve.Scene()
    target = raycast_scene.create_box((2, 2, 2), (1, 0, 0, 1))
    target.has_collision = True

    cam = ve.Camera()
    cam.set_position(0, 0, 5)
    cam.set_target(0, 0, 0)
    ray = cam.screen_to_ray(400, 300, 800, 600)

    hit = raycast_scene.raycast(ray, 50.0)
    assert hit.hit
    assert hit.entity.id == target.id


def test_instanced_mesh():
    box = ve.Mesh.create_box(1, 1, 1)
    inst = ve.InstancedMesh(box, 4)
    assert inst.instance_count() == 4
    inst.set_instance_count(8)
    assert inst.instance_count() == 8
    inst.set_instance(0, (1, 1, 0, 1))
