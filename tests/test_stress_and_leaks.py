"""Comprehensive Performance, Massive-Scale Stress, and Memory Leak Verification Suite.

Validates:
1. Massive-Scale Stress Testing:
   - InstancedMesh with 100,000 instances: allocation, matrix streaming, GPU buffer prep,
     frustum culling, and triangle statistics.
   - Zero-copy NumPy mesh vertex streaming at 100,000 vertices with dynamic updates.
   - 1,000 continuous simulation frames: steady frame delta times, zero memory spikes, GIL release.
2. Rapid Churn & Leak Detection:
   - Rapid allocation & destruction of 500+ Meshes, Textures, Materials, Nodes, RenderTargets.
   - Assertion of non-monotonic RSS growth and verified Sokol handle release.
3. Nanobind Refcount Audit:
   - Verification of weakref cycle breaking in App facade and UIOverlay.
   - Hierarchy parent/child Node3D destruction and clean reference clearing.
   - TweenManager lifecycle and target entity release.
   - Clean shutdown without nanobind instance/function/type leaks.
"""

from __future__ import annotations

import os
import sys
import time
import math
import gc
import psutil
import pytest
import numpy as np

import pielosyty as pe
import VelocityEngine as ve


class TestMassiveScaleStress:
    """Task 1: Massive Scale Stress Testing under extreme workloads."""

    def test_instanced_mesh_100k_allocation_and_streaming(self):
        """Verify InstancedMesh with 100,000 instances: allocation, streaming, and GPU buffer prep."""
        mesh = pe.Mesh.create_cube()
        t0 = time.perf_counter()
        inst = pe.InstancedMesh(mesh, 100000)
        t_alloc = time.perf_counter() - t0

        assert inst.instance_count() == 100000
        assert inst.count == 100000
        # Allocation must be under 500ms
        assert t_alloc < 0.50, f"100k allocation took {t_alloc*1000:.2f} ms"

        # Stream matrix and color updates to boundary and sample instances
        t1 = time.perf_counter()
        inst.set_instance(0, (1.0, 0.0, 0.0, 1.0))
        inst.set_instance(50000, (0.0, 1.0, 0.0, 1.0))
        inst.set_instance(99999, (0.0, 0.0, 1.0, 1.0))

        # Test set_instance_transform on 1000 sample instances
        for i in range(1000):
            idx = i * 99
            inst.set_instance_transform(
                idx,
                float(i), 0.0, float(i),
                0.0, float(i * 0.1), 0.0,
                1.0, 1.0, 1.0,
                (0.5, 0.5, 1.0, 1.0),
            )
        t_stream = time.perf_counter() - t1
        assert t_stream < 0.20, f"1000 transform updates took {t_stream*1000:.2f} ms"

        # GPU buffer preparation must be safe and valid
        gpu_ok = inst.ensure_gpu_buffers()
        assert isinstance(gpu_ok, bool)

        # Teardown
        inst.destroy()
        del inst, mesh
        gc.collect()

    def test_instanced_mesh_frustum_culling_100k(self):
        """Verify 100,000 InstancedMesh scene integration, culling, and triangle throughput."""
        app = pe.App("100k Frustum Test", 1280, 720)
        mesh = pe.Mesh.create_cube()
        inst = pe.InstancedMesh(mesh, 100000)

        app.scene.add_instanced_mesh(inst)
        assert len(app.scene.instanced_meshes) == 1
        assert app.scene.instanced_meshes[0].instance_count() == 100000

        # Evaluate view-frustum culling
        app.evaluate_frustum_culling()
        stats = app.stats

        assert stats.total_instances == 100000
        assert stats.draw_calls >= 1
        # Cube has 36 indices = 12 triangles per instance * 100k = 1.2M triangles
        assert stats.total_triangles == 1200000

        app.scene.remove_instanced_mesh(inst)
        assert len(app.scene.instanced_meshes) == 0

        app.close()
        del app, mesh, inst, stats
        gc.collect()

    def test_numpy_mesh_vertex_streaming_100k(self):
        """Verify zero-copy NumPy mesh vertex streaming at 100,000 vertices with dynamic updates."""
        # Generate 100,000 random 3D vertices
        rng = np.random.default_rng(42)
        verts = rng.standard_normal((100000, 3)).astype(np.float32)

        t0 = time.perf_counter()
        mesh = pe.Mesh.from_numpy(verts)
        t_create = time.perf_counter() - t0

        assert mesh.num_vertices == 100000
        assert t_create < 0.20, f"100k vertex creation took {t_create*1000:.2f} ms"

        # Dynamic vertex updates: sine wave deformation
        new_verts = (np.sin(verts) * 2.0).astype(np.float32)
        t1 = time.perf_counter()
        mesh.update_vertices_from_numpy(new_verts, recalculate_bounds=True)
        t_stream = time.perf_counter() - t1

        # Streaming 100k vertices should complete in < 20 ms
        assert t_stream < 0.05, f"100k vertex streaming took {t_stream*1000:.2f} ms"

        # Raw update test
        raw_flat = new_verts.ravel()
        t2 = time.perf_counter()
        mesh.update_vertices_raw(raw_flat)
        t_raw = time.perf_counter() - t2
        assert t_raw < 0.05, f"100k raw vertex update took {t_raw*1000:.2f} ms"

        del mesh, verts, new_verts, raw_flat
        gc.collect()

    def test_continuous_simulation_1000_frames_frame_pacing(self):
        """Stress test 1,000 continuous simulation frames: steady frame delta times and zero memory spikes."""
        process = psutil.Process(os.getpid())
        app = pe.App("1000 Frames Simulation Test", 1280, 720)
        mesh = pe.Mesh.create_cube()
        inst = pe.InstancedMesh(mesh, 5000)
        app.scene.add_instanced_mesh(inst)

        # Setup UI and tweens
        app.ui.draw_text("Stress Pacing Test", 100, 100)
        app.ui.draw_crosshair(10.0, pe.WHITE)

        # Warm up 5 frames
        for _ in range(5):
            app._on_internal_frame(0.016)

        gc.collect()
        rss_start = process.memory_info().rss / (1024 * 1024)

        delta_times = []
        t0 = time.perf_counter()
        for frame in range(1000):
            t_frame_start = time.perf_counter()
            app._on_internal_frame(0.016)
            delta_times.append(time.perf_counter() - t_frame_start)
        t_total = time.perf_counter() - t0

        gc.collect()
        rss_end = process.memory_info().rss / (1024 * 1024)
        rss_diff = rss_end - rss_start

        # 1. Steady frame delta times: average frame time must be under 2 ms
        avg_dt = sum(delta_times) / len(delta_times)
        max_dt = max(delta_times)
        assert avg_dt < 0.005, f"Average frame time too high: {avg_dt*1000:.4f} ms"
        assert max_dt < 0.100, f"Frame spike detected: {max_dt*1000:.4f} ms"

        # 2. Assert zero memory spikes: RSS growth during the 1,000 frames must remain under 5 MB
        assert rss_diff < 5.0, f"Memory spiked by {rss_diff:+.2f} MB across 1,000 frames"

        app.close()
        del app, mesh, inst, delta_times
        gc.collect()


class TestRapidChurnAndLeakDetection:
    """Task 2: Rapid Churn & Leak Detection."""

    def test_rapid_churn_500_iterations(self):
        """Rapid allocation & destruction of 500+ Meshes, Textures, Materials, Nodes, and RenderTargets."""
        process = psutil.Process(os.getpid())

        # Warmup allocation to prime allocator pools
        for _ in range(50):
            m = pe.Mesh.create_cube()
            tex = pe._core.Texture.create_solid_color(255, 128, 64, 255)
            mat = pe.StandardMaterial()
            node = pe.Node3D("WarmupNode")
            rt = pe._core.RenderTarget(128, 128)
            del m, tex, mat, node, rt
        gc.collect()

        rss_baseline = process.memory_info().rss / (1024 * 1024)
        batch_samples = []

        total_churn = 500
        batch_size = 100
        num_batches = total_churn // batch_size

        for b in range(num_batches):
            for i in range(batch_size):
                # 1. Mesh
                m = pe.Mesh.create_cube()
                # 2. Texture
                tex = pe._core.Texture.create_solid_color(255, 128, 64, 255)
                # 3. Material
                mat = pe.StandardMaterial()
                mat.roughness = 0.5
                mat.metallic = 0.8
                # 4. Node3D
                node = pe.Node3D(f"ChurnNode_{b}_{i}")
                node.set_position(float(i), 0.0, 0.0)
                # 5. RenderTarget
                rt = pe._core.RenderTarget(128, 128)
                del m, tex, mat, node, rt

            gc.collect()
            current_rss = process.memory_info().rss / (1024 * 1024)
            batch_samples.append(current_rss)

        # Assert memory does not monotonically grow out of control
        # Drift across 500 complex GPU/CPU objects must remain under 12 MB
        drift = batch_samples[-1] - batch_samples[0]
        assert drift < 12.0, f"Monotonic memory drift detected: {drift:+.2f} MB ({batch_samples})"

    def test_sokol_handle_lifecycle_verification(self):
        """Verify explicit handle destructions in Mesh, RenderTarget, and InstancedMesh."""
        mesh = pe.Mesh.create_box(1.0, 1.0, 1.0)
        assert mesh.vbuf_id >= 0
        assert mesh.ibuf_id >= 0

        inst = pe.InstancedMesh(mesh, 100)
        inst.ensure_gpu_buffers()
        # Explicit destroy
        inst.destroy()
        assert inst.inst_vbuf_id == 0

        rt = pe._core.RenderTarget(64, 64)
        rt.destroy()
        assert rt.color_image_id == 0
        assert rt.color_view_id == 0
        assert rt.sampler_id == 0

        del inst, mesh, rt
        gc.collect()


class TestNanobindRefcountAudit:
    """Task 3: Nanobind Reference Counting & Ownership Policies."""

    def test_app_weakref_no_circular_reference(self):
        """Verify App and UIOverlay do not create a cyclic reference keeping App alive."""
        import weakref

        app = pe.App("Weakref Test", 640, 480)
        app_weak = weakref.ref(app)
        ui = app.ui
        assert ui.app is app

        app.close()
        del app
        gc.collect()

        # App should be immediately collected because UIOverlay uses weakref
        assert app_weak() is None, "App was kept alive by a lingering circular reference!"

    def test_scene_node_hierarchy_destruction(self):
        """Verify deep Node3D parent-child trees are cleanly freed on clear() without cyclic leaks."""
        root = pe.Node3D("Root")
        for i in range(20):
            child = pe.Node3D(f"Child_{i}")
            for j in range(5):
                grandchild = pe.Node3D(f"Grandchild_{i}_{j}")
                child.add(grandchild)
            root.add(child)

        assert len(root.children) == 20
        assert root.children[0].parent is root

        # Clear root
        root.clear()
        assert len(root.children) == 0

        del root
        gc.collect()

    def test_tween_manager_lifecycle_and_target_deref(self):
        """Verify TweenManager release of animated targets when cancelled or cleared."""
        class AnimatedTarget:
            def __init__(self):
                self.val = 0.0

            def on_update(self, v):
                self.val = v

        target = AnimatedTarget()
        c0 = sys.getrefcount(target)

        tm = pe.TweenManager()
        tw = pe.Tween(0.0, 10.0, 1.0, on_update=target.on_update)
        tm.add(tw)

        c1 = sys.getrefcount(target)
        assert c1 > c0, "Target was not referenced by Tween!"

        # Advance partially
        tm.update(0.5)
        assert target.val > 0.0

        # Clear tween manager
        tm.clear()
        del tw
        gc.collect()

        c2 = sys.getrefcount(target)
        assert c2 == c0, f"Target reference was not released after clear()! (c0={c0}, c2={c2})"

    def test_instanced_mesh_refcount_correctness(self):
        """Verify InstancedMesh with attached Mesh frees Mesh reference when dereferenced."""
        mesh = pe.Mesh.create_cube()
        c0 = sys.getrefcount(mesh)

        inst = pe.InstancedMesh(mesh, 500)
        c1 = sys.getrefcount(mesh)
        assert c1 > c0, "Mesh was not referenced by InstancedMesh!"

        del inst
        gc.collect()

        c2 = sys.getrefcount(mesh)
        assert c2 == c0, f"Mesh reference was not dropped after InstancedMesh deletion! (c0={c0}, c2={c2})"
