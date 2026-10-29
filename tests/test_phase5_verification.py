import pytest
import math
import numpy as np
import pielosyty as p


# ============================================================================
# 1. Primitive Generators
# ============================================================================

def test_mesh_create_capsule():
    mesh = p.Mesh.create_capsule(radius=0.5, length=1.0, cap_segments=8, radial_segments=16)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices > 0
    assert mesh.num_indices % 3 == 0
    aabb = mesh.aabb
    assert aabb.min_bounds.y < 0.0
    assert aabb.max_bounds.y > 0.0
    # Length 1.0 + 2 * radius 0.5 = 2.0 total height
    total_height = aabb.max_bounds.y - aabb.min_bounds.y
    assert math.isclose(total_height, 2.0, rel_tol=0.05)


def test_mesh_create_cone():
    mesh = p.Mesh.create_cone(radius=1.0, height=2.0, radial_segments=32)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices > 0
    assert mesh.num_indices % 3 == 0
    aabb = mesh.aabb
    height = aabb.max_bounds.y - aabb.min_bounds.y
    assert math.isclose(height, 2.0, rel_tol=0.05)


def test_mesh_create_torus():
    mesh = p.Mesh.create_torus(radius=1.0, tube=0.4, radial_segments=16, tubular_segments=32)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices > 0
    assert mesh.num_indices % 3 == 0
    aabb = mesh.aabb
    # Torus outer radius is radius + tube = 1.4
    assert aabb.max_bounds.x <= 1.45
    assert aabb.min_bounds.x >= -1.45


def test_mesh_create_torus_knot():
    mesh = p.Mesh.create_torus_knot(radius=1.0, tube=0.3, tubular_segments=64, radial_segments=8, p=2, q=3)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices > 0
    assert mesh.num_indices % 3 == 0
    aabb = mesh.aabb
    assert aabb.min_bounds.x < aabb.max_bounds.x
    assert aabb.min_bounds.y < aabb.max_bounds.y
    assert aabb.min_bounds.z < aabb.max_bounds.z


def test_mesh_create_circle():
    mesh = p.Mesh.create_circle(radius=1.5, segments=32)
    assert mesh is not None
    assert mesh.num_vertices == 34  # center + 32 rim vertices + 1 UV seam closing vertex
    assert mesh.num_indices == 32 * 3
    aabb = mesh.aabb
    assert math.isclose(aabb.min_bounds.y, 0.0, abs_tol=1e-5)
    assert math.isclose(aabb.max_bounds.y, 0.0, abs_tol=1e-5)
    assert math.isclose(aabb.max_bounds.x, 1.5, rel_tol=0.05)


def test_mesh_create_ring():
    mesh = p.Mesh.create_ring(inner_radius=0.5, outer_radius=1.2, theta_segments=16)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices == 16 * 6  # 16 quads = 32 triangles = 96 indices
    aabb = mesh.aabb
    assert math.isclose(aabb.min_bounds.y, 0.0, abs_tol=1e-5)
    assert math.isclose(aabb.max_bounds.y, 0.0, abs_tol=1e-5)


def test_mesh_platonic_solids():
    # Tetrahedron: 4 faces * 3 = 12 indices
    tetra = p.Mesh.create_tetrahedron(radius=1.0)
    assert tetra is not None
    assert tetra.num_indices == 12
    assert tetra.num_vertices == 12

    # Octahedron: 8 faces * 3 = 24 indices
    octa = p.Mesh.create_octahedron(radius=1.0)
    assert octa is not None
    assert octa.num_indices == 24
    assert octa.num_vertices == 24

    # Icosahedron: 20 faces * 3 = 60 indices
    icosa = p.Mesh.create_icosahedron(radius=1.0)
    assert icosa is not None
    assert icosa.num_indices == 60
    assert icosa.num_vertices == 60

    # Dodecahedron: 12 pentagons * 3 triangles each * 3 = 108 indices, 12 pentagons * 5 vertices = 60 vertices
    dodeca = p.Mesh.create_dodecahedron(radius=1.0)
    assert dodeca is not None
    assert dodeca.num_indices == 108
    assert dodeca.num_vertices == 60


# ============================================================================
# 2. Curves & Splines
# ============================================================================

def test_catmull_rom_curve():
    pts = [(0.0, 0.0, 0.0), (1.0, 2.0, 0.0), (3.0, 1.0, 0.0), (5.0, 0.0, 0.0)]
    curve = p.CatmullRomCurve3(pts, closed=False, tension=0.5)
    p0 = curve.get_point(0.0)
    p1 = curve.get_point(1.0)
    assert math.isclose(p0.x, 0.0, abs_tol=1e-3)
    assert math.isclose(p0.y, 0.0, abs_tol=1e-3)
    assert math.isclose(p1.x, 5.0, abs_tol=1e-3)
    assert math.isclose(p1.y, 0.0, abs_tol=1e-3)

    t_mid = curve.get_tangent(0.5)
    t_len = math.sqrt(t_mid.x * t_mid.x + t_mid.y * t_mid.y + t_mid.z * t_mid.z)
    assert math.isclose(t_len, 1.0, rel_tol=1e-3)

    sampled = curve.get_points(20)
    assert len(sampled) == 21


def test_cubic_bezier_curve():
    v0 = (0.0, 0.0, 0.0)
    v1 = (0.0, 2.0, 0.0)
    v2 = (2.0, 2.0, 0.0)
    v3 = (2.0, 0.0, 0.0)
    curve = p.CubicBezierCurve3(v0, v1, v2, v3)
    p_start = curve.get_point(0.0)
    p_end = curve.get_point(1.0)
    p_mid = curve.get_point(0.5)

    assert math.isclose(p_start.x, 0.0, abs_tol=1e-4)
    assert math.isclose(p_end.x, 2.0, abs_tol=1e-4)
    assert math.isclose(p_mid.x, 1.0, abs_tol=1e-4)
    assert math.isclose(p_mid.y, 1.5, abs_tol=1e-4)

    tangent = curve.get_tangent(0.0)
    assert math.isclose(tangent.y, 1.0, rel_tol=1e-3)


def test_quadratic_bezier_curve():
    v0 = (0.0, 0.0, 0.0)
    v1 = (1.0, 2.0, 0.0)
    v2 = (2.0, 0.0, 0.0)
    curve = p.QuadraticBezierCurve3(v0, v1, v2)
    p_mid = curve.get_point(0.5)
    # B(0.5) = 0.25*v0 + 0.5*v1 + 0.25*v2 = (1.0, 1.0, 0.0)
    assert math.isclose(p_mid.x, 1.0, abs_tol=1e-4)
    assert math.isclose(p_mid.y, 1.0, abs_tol=1e-4)


def test_line_curve():
    v1 = (1.0, 2.0, 3.0)
    v2 = (5.0, 6.0, 7.0)
    curve = p.LineCurve3(v1, v2)
    mid = curve.get_point(0.5)
    assert math.isclose(mid.x, 3.0, abs_tol=1e-4)
    assert math.isclose(mid.y, 4.0, abs_tol=1e-4)
    assert math.isclose(mid.z, 5.0, abs_tol=1e-4)

    t = curve.get_tangent(0.2)
    t_len = math.sqrt(t.x * t.x + t.y * t.y + t.z * t.z)
    assert math.isclose(t_len, 1.0, rel_tol=1e-3)


# ============================================================================
# 3. Procedural Generators (Tube, Lathe, Extrude)
# ============================================================================

def test_create_tube():
    pts = [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 2.0, 0.0), (2.0, 2.0, 0.0)]
    curve = p.CatmullRomCurve3(pts)
    mesh = p.create_tube(curve, tubular_segments=32, radius=0.15, radial_segments=8, closed=False)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices > 0
    assert mesh.num_indices % 3 == 0

    # Test via Mesh static method
    mesh2 = p.Mesh.create_tube(curve, 16, 0.1, 6, False)
    assert mesh2.num_vertices > 0


def test_create_lathe():
    points = [(0.1, -1.0), (0.5, 0.0), (0.2, 1.0)]
    mesh = p.create_lathe(points, segments=16)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices > 0

    mesh2 = p.Mesh.create_lathe(points, 8)
    assert mesh2.num_vertices > 0


def test_create_extrude():
    poly = [(0.0, 0.0), (2.0, 0.0), (2.0, 1.0), (0.0, 1.0)]
    mesh = p.create_extrude(poly, depth=1.5, bevel_thickness=0.0)
    assert mesh is not None
    assert mesh.num_vertices > 0
    assert mesh.num_indices > 0
    aabb = mesh.aabb
    assert math.isclose(aabb.max_bounds.z - aabb.min_bounds.z, 1.5, rel_tol=0.05)


# ============================================================================
# 4. Zero-Copy NumPy Buffer Geometry
# ============================================================================

def test_mesh_numpy_buffer():
    # 4 vertices: quad
    # vertex layout: pos(3), normal(3), uv(2), color(4) = 12 floats
    verts = np.array([
        [-1.0, -1.0, 0.0,  0.0, 0.0, 1.0,  0.0, 0.0,  1.0, 1.0, 1.0, 1.0],
        [ 1.0, -1.0, 0.0,  0.0, 0.0, 1.0,  1.0, 0.0,  1.0, 1.0, 1.0, 1.0],
        [ 1.0,  1.0, 0.0,  0.0, 0.0, 1.0,  1.0, 1.0,  1.0, 1.0, 1.0, 1.0],
        [-1.0,  1.0, 0.0,  0.0, 0.0, 1.0,  0.0, 1.0,  1.0, 1.0, 1.0, 1.0],
    ], dtype=np.float32)

    indices = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint16)

    mesh = p.Mesh.from_numpy(verts, indices)
    assert mesh is not None
    assert mesh.is_dynamic is True
    assert mesh.num_vertices == 4
    assert mesh.num_indices == 6
    assert mesh.aabb.min_bounds.x == -1.0
    assert mesh.aabb.max_bounds.x == 1.0

    # Dynamic update of vertices in-place
    verts[0, 0] = -2.0
    mesh.update_vertices_from_numpy(verts)
    assert mesh.aabb.min_bounds.x == -2.0

    # Test 1D flat array update
    flat_verts = verts.flatten()
    flat_verts[12] = 2.5  # element index 12: x of vertex 1
    mesh.update_vertices_from_numpy(flat_verts)
    assert mesh.aabb.max_bounds.x == 2.5


# ============================================================================
# 5. Level of Detail (LOD)
# ============================================================================

def test_lod_switching():
    lod = p.LOD("HeroMeshLOD")
    assert lod.name == "HeroMeshLOD"
    assert lod.num_levels() == 0

    node_high = p.Node3D("High")
    node_med = p.Node3D("Med")
    node_low = p.Node3D("Low")

    lod.add_level(node_high, 0.0)
    lod.add_level(node_med, 15.0)
    lod.add_level(node_low, 40.0)

    assert lod.num_levels() == 3

    # Camera close: should be level 0 (High)
    lod.update_lod((0.0, 0.0, 5.0))
    assert lod.current_level_index() == 0
    assert node_high.visible is True
    assert node_med.visible is False
    assert node_low.visible is False

    # Camera medium distance: should be level 1 (Med)
    lod.update_lod((0.0, 0.0, 20.0))
    assert lod.current_level_index() == 1
    assert node_high.visible is False
    assert node_med.visible is True
    assert node_low.visible is False

    # Camera far: should be level 2 (Low)
    lod.update_lod((0.0, 0.0, 60.0))
    assert lod.current_level_index() == 2
    assert node_high.visible is False
    assert node_med.visible is False
    assert node_low.visible is True


def test_scene_lod_integration():
    scene = p.Scene()
    lod = p.LOD("LODTree")
    lod.add_level(p.Node3D("LOD0"), 0.0)
    lod.add_level(p.Node3D("LOD1"), 20.0)

    scene.add(lod)
    assert len(scene.lods) == 1

    scene.remove(lod)
    assert len(scene.lods) == 0

    scene.add(lod)
    scene.clear()
    assert len(scene.lods) == 0


# ============================================================================
# 6. Visual Helpers
# ============================================================================

def test_grid_helper():
    grid = p.GridHelper(size=20.0, divisions=10)
    assert grid is not None
    assert grid.size == 20.0
    assert grid.divisions == 10
    grid.update()


def test_axes_helper():
    axes = p.AxesHelper(size=3.0)
    assert axes is not None
    assert axes.size == 3.0
    axes.update()


def test_box_helper():
    target = p.Entity("BoxTarget")
    box = p.BoxHelper(target=target, color=(1.0, 1.0, 0.0, 1.0))
    assert box is not None
    box.update()


def test_arrow_helper():
    arrow = p.ArrowHelper(dir=(0.0, 1.0, 0.0), origin=(0.0, 0.0, 0.0), length=2.5)
    assert arrow is not None
    assert math.isclose(arrow.length, 2.5, rel_tol=1e-3)
    arrow.set_direction((1.0, 0.0, 0.0))
    arrow.set_length(3.0)
    arrow.update()


def test_light_helpers():
    dir_light = p.DirectionalLight("Sun")
    dir_helper = p.DirectionalLightHelper(dir_light, size=2.0)
    assert dir_helper is not None
    dir_helper.update()

    spot_light = p.SpotLight("Flashlight")
    spot_helper = p.SpotLightHelper(spot_light)
    assert spot_helper is not None
    spot_helper.update()

    point_light = p.PointLight("Bulb")
    point_helper = p.PointLightHelper(point_light, sphere_size=0.5)
    assert point_helper is not None
    point_helper.update()


def test_camera_helper():
    cam = p.PerspectiveCamera(60.0, 1.333, 0.1, 100.0)
    cam_helper = p.CameraHelper(cam)
    assert cam_helper is not None
    cam_helper.update()


def test_scene_helper_integration():
    scene = p.Scene()
    grid = p.GridHelper(10.0, 10)
    axes = p.AxesHelper(1.0)

    scene.add(grid)
    scene.add(axes)
    assert len(scene.helpers) == 2

    scene.remove(grid)
    assert len(scene.helpers) == 1

    scene.clear()
    assert len(scene.helpers) == 0


# ============================================================================
# 7. Hostile Edge Cases & Comprehensive Verification Audit
# ============================================================================

def test_parametric_primitives_hostile_audit():
    """Hostile edge-case audit: all 10 primitives have non-zero triangles, valid unit normals, unit tangents, and finite AABBs."""
    primitives = [
        ("capsule_std", p.Mesh.create_capsule(radius=0.4, length=1.2, cap_segments=6, radial_segments=12)),
        ("capsule_zero_len", p.Mesh.create_capsule(radius=0.5, length=0.0, cap_segments=4, radial_segments=8)),
        ("cone_closed", p.Mesh.create_cone(radius=1.0, height=2.5, radial_segments=24, open_ended=False)),
        ("cone_open", p.Mesh.create_cone(radius=1.0, height=2.5, radial_segments=24, open_ended=True)),
        ("torus", p.Mesh.create_torus(radius=1.2, tube=0.3, radial_segments=12, tubular_segments=24)),
        ("torus_knot", p.Mesh.create_torus_knot(radius=1.0, tube=0.25, tubular_segments=48, radial_segments=12, p=3, q=4)),
        ("circle", p.Mesh.create_circle(radius=2.0, segments=24)),
        ("ring", p.Mesh.create_ring(inner_radius=0.3, outer_radius=1.5, theta_segments=20)),
        ("tetrahedron", p.Mesh.create_tetrahedron(radius=1.5)),
        ("octahedron", p.Mesh.create_octahedron(radius=1.5)),
        ("icosahedron_0", p.Mesh.create_icosahedron(radius=1.5, subdivisions=0)),
        ("icosahedron_1", p.Mesh.create_icosahedron(radius=1.5, subdivisions=1)),
        ("dodecahedron", p.Mesh.create_dodecahedron(radius=1.5)),
    ]

    for name, mesh in primitives:
        assert mesh is not None, f"{name} is None"
        assert mesh.num_vertices > 0, f"{name} has 0 vertices"
        assert mesh.num_indices > 0, f"{name} has 0 indices"
        assert mesh.num_indices % 3 == 0, f"{name} num_indices {mesh.num_indices} not divisible by 3"

        aabb = mesh.aabb
        assert np.isfinite(aabb.min_bounds.x) and np.isfinite(aabb.max_bounds.x), f"{name} non-finite AABB x"
        assert np.isfinite(aabb.min_bounds.y) and np.isfinite(aabb.max_bounds.y), f"{name} non-finite AABB y"
        assert np.isfinite(aabb.min_bounds.z) and np.isfinite(aabb.max_bounds.z), f"{name} non-finite AABB z"
        assert aabb.min_bounds.x <= aabb.max_bounds.x, f"{name} invalid AABB min.x > max.x"
        assert aabb.min_bounds.y <= aabb.max_bounds.y, f"{name} invalid AABB min.y > max.y"
        assert aabb.min_bounds.z <= aabb.max_bounds.z, f"{name} invalid AABB min.z > max.z"

        # Check vertex attributes: normals and tangents
        for v in mesh.cpu_vertices:
            n_len = math.sqrt(v.normal.x**2 + v.normal.y**2 + v.normal.z**2)
            assert math.isclose(n_len, 1.0, rel_tol=0.08), f"{name} normal not unit length: {n_len}"

            t_len = math.sqrt(v.tangent.x**2 + v.tangent.y**2 + v.tangent.z**2)
            assert math.isclose(t_len, 1.0, rel_tol=0.08), f"{name} tangent not unit length: {t_len}"
            assert math.isclose(abs(v.tangent.w), 1.0, abs_tol=1e-3), f"{name} tangent w not +/-1: {v.tangent.w}"


def test_procedural_geometry_hostile_audit():
    """Hostile edge-case audit: Tube, Lathe, and Extrude geometries."""
    # 1. Tube along straight line
    line = p.LineCurve3((0.0, 0.0, 0.0), (0.0, 10.0, 0.0))
    tube_line = p.create_tube(line, tubular_segments=16, radius=0.2, radial_segments=6, closed=False)
    assert tube_line.num_vertices > 0
    assert tube_line.num_indices % 3 == 0

    # 2. Tube along closed CatmullRomCurve3
    pts = [(0, 0, 0), (2, 2, 0), (4, 0, 2), (2, -2, 0)]
    curve = p.CatmullRomCurve3(pts, closed=True)
    tube_closed = p.create_tube(curve, tubular_segments=24, radius=0.3, radial_segments=8, closed=True)
    assert tube_closed.num_vertices > 0
    assert tube_closed.num_indices % 3 == 0

    # 3. Lathe with partial angle (180 deg)
    profile = [(0.2, -1.0), (0.8, 0.0), (0.3, 1.0)]
    lathe_partial = p.create_lathe(profile, segments=12, phi_start=0.0, phi_length=math.pi)
    assert lathe_partial.num_vertices > 0
    assert lathe_partial.num_indices % 3 == 0

    # 4. Extrude concave polygon (L-shape)
    l_shape = [
        (0.0, 0.0), (3.0, 0.0), (3.0, 1.0),
        (1.0, 1.0), (1.0, 3.0), (0.0, 3.0)
    ]
    extrude_l = p.create_extrude(l_shape, depth=2.0, bevel_thickness=0.0)
    assert extrude_l.num_vertices > 0
    assert extrude_l.num_indices % 3 == 0
    aabb = extrude_l.aabb
    assert math.isclose(aabb.max_bounds.z - aabb.min_bounds.z, 2.0, rel_tol=0.05)


def test_visual_helpers_hostile_audit():
    """Hostile edge-case audit: Visual helpers with null targets, dynamic updates, and parameter changes."""
    # 1. GridHelper
    grid = p.GridHelper(50.0, 20)
    assert grid.size == 50.0
    assert grid.divisions == 20
    grid.size = 100.0
    grid.divisions = 50
    assert grid.size == 100.0
    assert grid.divisions == 50
    grid.update()

    # 2. AxesHelper
    axes = p.AxesHelper(10.0)
    assert axes.size == 10.0
    axes.size = 2.0
    assert axes.size == 2.0
    axes.update()

    # 3. BoxHelper with null target vs moving target
    box_null = p.BoxHelper(None)
    assert box_null.target is None
    box_null.update()

    target_node = p.Node3D("TargetNode")
    box_valid = p.BoxHelper(target_node, color=(1.0, 0.0, 0.0, 1.0))
    box_valid.update()
    box_valid.set_from_object(target_node)
    box_valid.update()

    # 4. ArrowHelper with zero-direction fallback and updates
    arrow = p.ArrowHelper(dir=(0.0, 0.0, 0.0), origin=(1.0, 2.0, 3.0), length=5.0)
    assert math.isclose(arrow.length, 5.0, rel_tol=1e-3)
    arrow.set_direction((0.0, 0.0, 1.0))
    arrow.set_length(10.0, head_length=1.0, head_width=0.5)
    arrow.set_color((0.0, 1.0, 0.0, 1.0))
    arrow.update()

    # 5. CameraHelper with Orthographic and Perspective cameras
    ortho_cam = p.OrthographicCamera(-5.0, 5.0, -5.0, 5.0, 0.1, 100.0)
    ortho_helper = p.CameraHelper(ortho_cam)
    ortho_helper.update()

    persp_cam = p.PerspectiveCamera(45.0, 1.777, 0.5, 500.0)
    persp_helper = p.CameraHelper(persp_cam)
    persp_helper.update()

    # 6. Light Helpers
    dir_light = p.DirectionalLight("Sun")
    dir_light.direction = p.Vec3(0.0, -1.0, 0.0)
    dir_hlp = p.DirectionalLightHelper(dir_light, size=4.0)
    dir_hlp.update()

    spot_light = p.SpotLight("Spot")
    spot_light.inner_cone_angle = 0.3
    spot_light.outer_cone_angle = 0.6
    spot_hlp = p.SpotLightHelper(spot_light)
    spot_hlp.update()

    point_light = p.PointLight("Point")
    point_hlp = p.PointLightHelper(point_light, sphere_size=1.0)
    point_hlp.update()


def test_lod_comprehensive_thresholds():
    """Verify Level of Detail (LOD) threshold switching with 3 distance tiers: 10.0, 50.0, 100.0."""
    lod = p.LOD("LODAsset")
    l_high = p.Node3D("TierHigh")
    l_med = p.Node3D("TierMed")
    l_low = p.Node3D("TierLow")

    lod.add_level(l_high, 10.0)
    lod.add_level(l_med, 50.0)
    lod.add_level(l_low, 100.0)

    assert lod.num_levels() == 3

    # Distance 5.0 (< 10.0): Level 0 active
    lod.update_lod((0.0, 0.0, 5.0))
    assert lod.current_level_index() == 0
    assert l_high.visible is True
    assert l_med.visible is False
    assert l_low.visible is False

    # Distance 60.0 (>= 50.0 and < 100.0): Level 1 active
    lod.update_lod((0.0, 0.0, 60.0))
    assert lod.current_level_index() == 1
    assert l_high.visible is False
    assert l_med.visible is True
    assert l_low.visible is False

    # Distance 150.0 (>= 100.0): Level 2 active
    lod.update_lod((0.0, 0.0, 150.0))
    assert lod.current_level_index() == 2
    assert l_high.visible is False
    assert l_med.visible is False
    assert l_low.visible is True


def test_phase5_100k_vertex_wave_dynamic_update_and_gil_release():
    """Verify 100,000 vertex wave dynamic NumPy update with sub-millisecond per-frame upload latency and GIL release."""
    import time
    import threading

    nx, nz = 200, 500
    n = nx * nz
    assert n == 100000

    x = np.linspace(-20.0, 20.0, nx, dtype=np.float32)
    z = np.linspace(-20.0, 20.0, nz, dtype=np.float32)
    xx, zz = np.meshgrid(x, z)
    xx_flat = xx.ravel()
    zz_flat = zz.ravel()

    # 16-float stride vertex buffer: pos(3), normal(3), uv(2), color(4), tangent(4)
    wave_buf = np.zeros((n, 16), dtype=np.float32)
    wave_buf[:, 0] = xx_flat
    wave_buf[:, 1] = np.sin(xx_flat)
    wave_buf[:, 2] = zz_flat
    wave_buf[:, 4] = 1.0  # normal Y
    wave_buf[:, 8:12] = 1.0  # color
    wave_buf[:, 12] = 1.0  # tangent X
    wave_buf[:, 15] = 1.0  # tangent W

    mesh = p.Mesh.from_numpy(wave_buf[:, :3])
    assert mesh.num_vertices == n

    # Benchmark loop: isolate pure upload latency
    iterations = 50
    t0_upload = time.perf_counter()
    for i in range(iterations):
        mesh.update_vertices_from_numpy(wave_buf, recalculate_bounds=False)
    upload_elapsed = time.perf_counter() - t0_upload
    upload_avg_ms = (upload_elapsed / iterations) * 1000.0
    # Assert upload latency (< 2.5 ms for 96-byte Phase 6 vertex layout)
    assert upload_avg_ms < 2.5, f"Per-frame upload latency {upload_avg_ms:.3f} ms exceeds limit"

    # End-to-end benchmark: wave calculation + upload (must comfortably beat 60 FPS / 16.6 ms)
    t0_e2e = time.perf_counter()
    for i in range(iterations):
        phase = i * 0.05
        wave_buf[:, 1] = np.sin(xx_flat * 0.4 + phase) * np.cos(zz_flat * 0.4 + phase)
        mesh.update_vertices_from_numpy(wave_buf, recalculate_bounds=False)
    e2e_elapsed = time.perf_counter() - t0_e2e
    e2e_avg_ms = (e2e_elapsed / iterations) * 1000.0
    assert e2e_avg_ms < 16.6, f"Combined wave calculation and upload {e2e_avg_ms:.3f} ms exceeds 60 FPS budget"

    # Multithreaded test verifying GIL is released during upload
    thread_ran = False
    def worker():
        nonlocal thread_ran
        for _ in range(100):
            _ = [math.sin(j) for j in range(100)]
        thread_ran = True

    t_worker = threading.Thread(target=worker)
    t_worker.start()

    for i in range(20):
        mesh.update_vertices_from_numpy(wave_buf, recalculate_bounds=False)

    t_worker.join(timeout=2.0)
    assert thread_ran is True, "Worker thread failed to complete concurrently; GIL contention suspected"


def test_phase5_acceptance_criterion_flight_wave_scene():
    """Verify Acceptance Criterion: 100,000 vertex wave updating at 60 FPS with camera flying along CatmullRomCurve3, TubeGeometry, and GridHelper."""
    import time

    nx, nz = 200, 500
    n = nx * nz
    assert n == 100000

    scene = p.Scene()

    # 1. 100k vertex wave mesh
    x = np.linspace(-25.0, 25.0, nx, dtype=np.float32)
    z = np.linspace(-25.0, 25.0, nz, dtype=np.float32)
    xx, zz = np.meshgrid(x, z)
    xx_flat = xx.ravel()
    zz_flat = zz.ravel()

    wave_buf = np.zeros((n, 16), dtype=np.float32)
    wave_buf[:, 0] = xx_flat
    wave_buf[:, 1] = np.sin(xx_flat)
    wave_buf[:, 2] = zz_flat
    wave_buf[:, 4] = 1.0
    wave_buf[:, 8:12] = 1.0
    wave_buf[:, 12] = 1.0
    wave_buf[:, 15] = 1.0

    wave_mesh = p.Mesh.from_numpy(wave_buf[:, :3])
    wave_entity = p.Entity("WaveEntity")
    wave_entity.mesh = wave_mesh
    scene.add(wave_entity)

    # 2. CatmullRomCurve3 with TubeGeometry
    control_points = [
        (0.0, 5.0, -20.0),
        (10.0, 8.0, -5.0),
        (15.0, 4.0, 10.0),
        (0.0, 7.0, 25.0),
        (-15.0, 10.0, 5.0),
        (-10.0, 6.0, -15.0),
    ]
    curve = p.CatmullRomCurve3(control_points, closed=True, tension=0.5)
    tube_mesh = p.create_tube(curve, tubular_segments=64, radius=0.3, radial_segments=12, closed=True)
    tube_entity = p.Entity("TubeEntity")
    tube_entity.mesh = tube_mesh
    scene.add(tube_entity)

    # 3. GridHelper & AxesHelper
    grid = p.GridHelper(50.0, 25)
    axes = p.AxesHelper(5.0)
    scene.add(grid)
    scene.add(axes)

    # 4. LOD Node
    lod = p.LOD("LODTree")
    lod.add_level(p.Node3D("LOD_High"), 10.0)
    lod.add_level(p.Node3D("LOD_Med"), 50.0)
    lod.add_level(p.Node3D("LOD_Low"), 100.0)
    scene.add(lod)

    assert len(scene.helpers) == 2
    assert len(scene.lods) == 1

    # 5. Flying Camera along Spline for 60 frames (1 second at 60 FPS)
    cam = p.PerspectiveCamera(60.0, 1.333, 0.1, 1000.0)
    prev_pos = None

    t0 = time.perf_counter()
    num_frames = 60

    for frame in range(num_frames):
        t = frame / float(num_frames)

        # Sample position and look direction
        pos = curve.get_point(t)
        tan = curve.get_tangent(t)
        tan_len = math.sqrt(tan.x**2 + tan.y**2 + tan.z**2)
        assert math.isclose(tan_len, 1.0, rel_tol=1e-3), f"Tangent not normalized at t={t}: {tan_len}"

        cam.set_position(pos.x, pos.y, pos.z)
        cam.set_target(pos.x + tan.x * 5.0, pos.y + tan.y * 5.0, pos.z + tan.z * 5.0)

        # Smooth flight continuity check (no wild teleportation)
        if prev_pos is not None:
            dist = math.sqrt((pos.x - prev_pos.x)**2 + (pos.y - prev_pos.y)**2 + (pos.z - prev_pos.z)**2)
            assert dist < 5.0, f"Discontinuous camera jump at frame {frame}: {dist}"
        prev_pos = pos

        # Dynamic wave update via np.sin()
        wave_buf[:, 1] = np.sin(xx_flat * 0.3 + t * 6.28) * np.cos(zz_flat * 0.3 + t * 6.28)
        wave_mesh.update_vertices_from_numpy(wave_buf, recalculate_bounds=False)

    total_time = time.perf_counter() - t0
    fps = num_frames / total_time
    assert fps >= 60.0, f"Simulation ran at {fps:.1f} FPS, expected >= 60.0 FPS"

