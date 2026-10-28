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


def test_bounding_sphere_and_ray_intersection():
    aabb = ve.AABB(ve.Vec3(-1, -1, -1), ve.Vec3(1, 1, 1))
    sphere = ve.BoundingSphere.from_aabb(aabb)
    assert sphere.is_valid()
    assert abs(sphere.center.x) < 1e-5
    assert abs(sphere.center.y) < 1e-5
    assert abs(sphere.center.z) < 1e-5
    # Radius of box with extents (1, 1, 1) is sqrt(3) ~= 1.732
    assert abs(sphere.radius - math.sqrt(3.0)) < 1e-4

    # Direct hit
    ray_hit = ve.Ray(ve.Vec3(0, 0, 5), ve.Vec3(0, 0, -1))
    hit, t = ray_hit.intersect_sphere(sphere)
    assert hit
    assert abs(t - (5.0 - sphere.radius)) < 1e-4

    # Miss
    ray_miss = ve.Ray(ve.Vec3(0, 5, 5), ve.Vec3(0, 0, -1))
    hit_miss, _ = ray_miss.intersect_sphere(sphere)
    assert not hit_miss

    # Inside sphere
    ray_inside = ve.Ray(ve.Vec3(0, 0, 0), ve.Vec3(0, 0, 1))
    hit_in, t_in = ray_inside.intersect_sphere(sphere)
    assert hit_in
    assert abs(t_in - sphere.radius) < 1e-4


def test_entity_world_bounding_sphere():
    scene = ve.Scene()
    ent = scene.create_box((2, 2, 2))
    ent.transform.position = (5, 0, 0)

    sphere = ent.world_bounding_sphere()
    assert sphere.is_valid()
    assert abs(sphere.center.x - 5.0) < 1e-4
    assert abs(sphere.radius - math.sqrt(3.0)) < 1e-4

    # Raycast pre-pass verification: ray through (5, 0, 10) pointing in -Z hits
    ray = ve.Ray(ve.Vec3(5, 0, 10), ve.Vec3(0, 0, -1))
    hit = scene.raycast(ray)
    assert hit.hit
    assert hit.entity.id == ent.id

    # Ray missing the bounding sphere at X=10 doesn't hit
    ray2 = ve.Ray(ve.Vec3(10, 0, 10), ve.Vec3(0, 0, -1))
    hit2 = scene.raycast(ray2)
    assert not hit2.hit


def test_fog_and_tone_mapping_integration():
    app = ve.App(title="FogTest", width=640, height=480)
    
    # 1. Linear Fog
    fog_lin = ve.Fog(color="#223344", near=5.0, far=50.0)
    app.fog = fog_lin
    assert app.fog is fog_lin
    assert app._core.fog_enabled
    assert app._core.fog_type == 1  # 1 = Linear
    assert abs(app._core.fog_near - 5.0) < 1e-4
    assert abs(app._core.fog_far - 50.0) < 1e-4

    # 2. Exp2 Fog
    fog_exp = ve.FogExp2(color="#112233", density=0.035)
    app.fog = fog_exp
    assert app.fog is fog_exp
    assert app._core.fog_enabled
    assert app._core.fog_type == 2  # 2 = Exp2
    assert abs(app._core.fog_density - 0.035) < 1e-4

    # 3. Clear Fog
    app.fog = None
    assert app.fog is None
    assert not app._core.fog_enabled

    # 4. Tone Mapping
    assert app.tone_mapping is True
    app.tone_mapping = False
    assert app.tone_mapping is False
    assert app._core.tone_mapping is False
    app.tone_mapping = True
    assert app.tone_mapping is True


def test_engine_target_fps_and_crosshair():
    app = ve._core.EngineApp()
    assert app.target_fps == 0
    assert app.show_crosshair is True

    app.set_target_fps(120)
    assert app.target_fps == 120

    app.target_fps = 0
    assert app.target_fps == 0

    app.set_show_crosshair(False)
    assert app.show_crosshair is False

    app.show_crosshair = True
    assert app.show_crosshair is True

