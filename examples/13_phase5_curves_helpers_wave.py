"""Example 13: Phase 5 Acceptance Criteria Showcase.

Demonstrates:
- 100,000 vertex wave dynamically computed in Python using NumPy and updated on GPU.
- CatmullRomCurve3 3D spline with procedural TubeGeometry.
- Visual Helpers: GridHelper, AxesHelper, BoxHelper, LightHelper, CameraHelper.
- Level of Detail (LOD) node switching based on camera distance.
- Smooth camera flight along CatmullRomCurve3 looking along the tangent.
"""

from __future__ import annotations
import math
import time
import numpy as np
import pielosyty as p

def create_wave_data(nx: int = 200, nz: int = 500, time_val: float = 0.0) -> np.ndarray:
    """Generate 100,000 vertex wave buffer with positions, normals, UVs, tints, and tangents."""
    n = nx * nz
    x = np.linspace(-30.0, 30.0, nx, dtype=np.float32)
    z = np.linspace(-30.0, 30.0, nz, dtype=np.float32)
    xx, zz = np.meshgrid(x, z)
    xx_flat = xx.ravel()
    zz_flat = zz.ravel()

    # Dynamic wave calculation via np.sin() and np.cos()
    r = np.sqrt(xx_flat * xx_flat + zz_flat * zz_flat)
    y_flat = np.sin(r * 0.4 - time_val * 3.0) * 1.5

    # 16-float stride vertex buffer layout:
    # pos(3), normal(3), uv(2), color(4), tangent(4) = 16 floats
    buffer = np.zeros((n, 16), dtype=np.float32)
    buffer[:, 0] = xx_flat
    buffer[:, 1] = y_flat
    buffer[:, 2] = zz_flat

    # Analytical or upward normals
    buffer[:, 4] = 1.0  # normal Y

    # UV coords
    buffer[:, 6] = (xx_flat + 30.0) / 60.0
    buffer[:, 7] = (zz_flat + 30.0) / 60.0

    # Gradient tint color based on wave height
    t_norm = (y_flat + 1.5) / 3.0
    buffer[:, 8] = 0.1 + 0.2 * t_norm    # R
    buffer[:, 9] = 0.5 + 0.4 * t_norm    # G
    buffer[:, 10] = 0.8 + 0.2 * t_norm   # B
    buffer[:, 11] = 1.0                  # A

    # Tangent
    buffer[:, 12] = 1.0  # tangent X
    buffer[:, 15] = 1.0  # tangent W (handedness)

    return buffer


def main() -> None:
    app = p.EngineApp()
    scene = app.scene

    # 1. Procedural 100,000 Vertex Dynamic Wave Mesh
    initial_wave = create_wave_data(200, 500, 0.0)
    wave_mesh = p.Mesh.from_numpy(initial_wave[:, :3])
    wave_mesh.update_vertices_from_numpy(initial_wave, recalculate_bounds=False)

    wave_entity = p.Entity("DynamicWave")
    wave_entity.mesh = wave_mesh
    wave_mat = p.StandardMaterial()
    wave_mat.roughness = 0.3
    wave_mat.metallic = 0.1
    wave_mat.base_color = (0.2, 0.7, 1.0, 1.0)
    wave_entity.material = wave_mat
    scene.add(wave_entity)

    # 2. CatmullRomCurve3 with TubeGeometry
    curve_points = [
        (0.0, 8.0, -25.0),
        (15.0, 12.0, -10.0),
        (20.0, 6.0, 15.0),
        (0.0, 10.0, 30.0),
        (-20.0, 14.0, 10.0),
        (-15.0, 8.0, -15.0),
    ]
    curve = p.CatmullRomCurve3(curve_points, closed=True, tension=0.5)
    tube_mesh = p.create_tube(curve, tubular_segments=100, radius=0.4, radial_segments=12, closed=True)

    tube_entity = p.Entity("RollercoasterTube")
    tube_entity.mesh = tube_mesh
    tube_mat = p.StandardMaterial()
    tube_mat.roughness = 0.2
    tube_mat.metallic = 0.7
    tube_mat.base_color = (1.0, 0.4, 0.1, 1.0)
    tube_entity.material = tube_mat
    scene.add(tube_entity)

    # 3. Visual Helpers
    grid = p.GridHelper(size=60.0, divisions=30, color_center=(0.9, 0.9, 0.2, 1.0), color_grid=(0.2, 0.2, 0.3, 1.0))
    axes = p.AxesHelper(size=5.0)
    box = p.BoxHelper(tube_entity, color=(0.0, 1.0, 0.5, 1.0))
    arrow = p.ArrowHelper(dir=(0.0, 1.0, 0.0), origin=(0.0, 0.0, 0.0), length=4.0, color=(1.0, 1.0, 0.0, 1.0))

    scene.add(grid)
    scene.add(axes)
    scene.add(box)
    scene.add(arrow)

    # 4. Level of Detail (LOD)
    lod = p.LOD("LODTree")
    lod_high = p.Entity("SphereHigh")
    lod_high.mesh = p.Mesh.create_sphere(radius=1.5, rings=32, sectors=32)
    lod_med = p.Entity("SphereMed")
    lod_med.mesh = p.Mesh.create_sphere(radius=1.5, rings=16, sectors=16)
    lod_low = p.Entity("SphereLow")
    lod_low.mesh = p.Mesh.create_sphere(radius=1.5, rings=8, sectors=8)

    lod.add_level(lod_high, 10.0)
    lod.add_level(lod_med, 50.0)
    lod.add_level(lod_low, 100.0)
    lod.transform.position = p.Vec3(0.0, 5.0, 0.0)
    scene.add(lod)

    # 5. Sun Light and Helper
    sun = p.DirectionalLight("Sun")
    sun.direction = p.Vec3(-0.5, -1.0, -0.3)
    sun.color = p.Vec3(1.0, 0.95, 0.85)
    scene.add(sun)
    sun_helper = p.DirectionalLightHelper(sun, size=3.0)
    scene.add(sun_helper)

    print("Phase 5 Showcase initialized successfully.")
    print("Simulating 60 FPS flight along CatmullRomCurve3 with dynamic wave updates...")

    # Benchmark 60-frame simulation loop
    start_time = time.perf_counter()
    total_frames = 60
    for frame in range(total_frames):
        t = (frame / float(total_frames)) % 1.0
        
        # Flight camera along spline
        cam_pos = curve.get_point(t)
        cam_tan = curve.get_tangent(t)
        app.camera.set_position(cam_pos.x, cam_pos.y, cam_pos.z)
        app.camera.set_target(cam_pos.x + cam_tan.x * 5.0, cam_pos.y + cam_tan.y * 5.0, cam_pos.z + cam_tan.z * 5.0)

        # Dynamic wave update
        wave_data = create_wave_data(200, 500, time_val=frame * 0.03)
        wave_mesh.update_vertices_from_numpy(wave_data, recalculate_bounds=False)

    elapsed = time.perf_counter() - start_time
    fps = total_frames / elapsed
    print(f"Simulation completed: {total_frames} frames in {elapsed:.3f} s ({fps:.1f} FPS, {elapsed/total_frames*1000:.2f} ms/frame).")


if __name__ == "__main__":
    main()
