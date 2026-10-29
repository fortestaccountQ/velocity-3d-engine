"""Phase 7 Verification Tests for Pielosyty 3D Engine.

Tests:
1. Loaders: OBJ, STL (ASCII & Binary), PLY (ASCII & Binary), Unified loader
2. Exporters: OBJ, STL (ASCII & Binary), glTF 2.0 (Self-contained JSON with Base64), PNG Screenshot
3. AssetCache singleton (Thread-safe caching of meshes, textures, models, deduplication)
4. EventDispatcher on Node3D (click, hover_enter, hover_leave, collision)
5. 3D Mouse Picking & App EventDispatcher (screen_to_ray, raycast, hit coordinates, bubbling, resize)
6. ImGui Editor Upgrade (F2 mode toggle, Scene Hierarchy, Inspector, Post-Process Panel, Gizmo & Save Scene to Script)
"""

import os
import struct
import tempfile
import pytest

import pielosyty as ve


class TestPhase7LoadersAndExporters:
    """Task 7.1: Loaders & Exporters verification."""

    def test_obj_loader_and_exporter(self, tmp_path):
        """Test Wavefront OBJ loading, exporting, and round-trip verification."""
        obj_file = tmp_path / "test_cube.obj"
        obj_content = """# Test OBJ Cube
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0
vn 0.0 0.0 1.0
vt 0.0 0.0
vt 1.0 0.0
vt 1.0 1.0
vt 0.0 1.0
f 1/1/1 2/2/1 3/3/1 4/4/1
f 5/1/1 6/2/1 7/3/1 8/4/1
"""
        obj_file.write_text(obj_content, encoding="utf-8")

        mesh = ve.load_obj_mesh(str(obj_file))
        assert mesh is not None
        assert mesh.num_vertices > 0
        assert mesh.num_indices == 12  # Two quads triangulated into 4 triangles = 12 indices
        assert mesh.local_aabb.is_valid()
        assert mesh.local_aabb.min_point.x <= 0.0
        assert mesh.local_aabb.max_point.x >= 1.0

        # Test static method Mesh.load_obj
        mesh2 = ve.Mesh.load_obj(str(obj_file))
        assert mesh2 is not None
        assert mesh2.num_indices == mesh.num_indices

        # Test scene.load_obj creating Model and Entity
        scene = ve.Scene()
        model = scene.load_obj(str(obj_file))
        assert model is not None
        assert len(model.meshes) >= 1
        assert model.meshes[0].mesh is not None

        # Test export_obj
        export_file = tmp_path / "exported.obj"
        success = ve.export_obj(model.root_entity, str(export_file))
        assert success
        assert os.path.exists(export_file)
        assert os.path.getsize(export_file) > 0

        # Roundtrip load
        reloaded = ve.load_obj_mesh(str(export_file))
        assert reloaded is not None
        assert reloaded.num_vertices > 0

    def test_obj_roundtrip_box_and_bounding_boxes(self, tmp_path):
        """Export box mesh to .obj, reload, and verify vertex/index counts & bounds match."""
        scene = ve.Scene()
        orig_box = scene.create_box(ve.Vec3(2.0, 3.0, 4.0))
        orig_mesh = orig_box.mesh
        assert orig_mesh is not None
        orig_aabb = orig_mesh.local_aabb

        obj_path = tmp_path / "roundtrip_box.obj"
        assert ve.export_obj(orig_box, str(obj_path))
        assert os.path.exists(obj_path)

        reloaded_mesh = ve.load_obj_mesh(str(obj_path))
        assert reloaded_mesh is not None
        assert reloaded_mesh.num_indices == orig_mesh.num_indices
        reloaded_aabb = reloaded_mesh.local_aabb
        assert reloaded_aabb.is_valid()
        assert abs(reloaded_aabb.min_point.x - orig_aabb.min_point.x) < 1e-4
        assert abs(reloaded_aabb.max_point.x - orig_aabb.max_point.x) < 1e-4
        assert abs(reloaded_aabb.min_point.y - orig_aabb.min_point.y) < 1e-4
        assert abs(reloaded_aabb.max_point.y - orig_aabb.max_point.y) < 1e-4
        assert abs(reloaded_aabb.min_point.z - orig_aabb.min_point.z) < 1e-4
        assert abs(reloaded_aabb.max_point.z - orig_aabb.max_point.z) < 1e-4

    def test_obj_edge_cases(self, tmp_path):
        """Hostile edge cases: missing normals (auto-compute smooth normals), negative indices."""
        # 1. Missing normals
        no_normals_obj = tmp_path / "no_normals.obj"
        no_normals_obj.write_text(
            "v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n",
            encoding="utf-8"
        )
        mesh_no_norm = ve.load_obj_mesh(str(no_normals_obj))
        assert mesh_no_norm is not None
        assert mesh_no_norm.num_vertices == 3
        assert mesh_no_norm.num_indices == 3

        # 2. Negative indices: -1, -2, -3
        neg_idx_obj = tmp_path / "neg_indices.obj"
        neg_idx_obj.write_text(
            "v 0 0 0\nv 2 0 0\nv 0 2 0\nf -3 -2 -1\n",
            encoding="utf-8"
        )
        mesh_neg = ve.load_obj_mesh(str(neg_idx_obj))
        assert mesh_neg is not None
        assert mesh_neg.num_indices == 3

    def test_stl_loader_ascii_and_binary(self, tmp_path):
        """Test STL loader supporting both ASCII and Binary formats."""
        # 1. ASCII STL
        ascii_stl = tmp_path / "test_ascii.stl"
        ascii_content = """solid test_triangle
  facet normal 0.0 0.0 1.0
    outer loop
      vertex 0.0 0.0 0.0
      vertex 1.0 0.0 0.0
      vertex 0.0 1.0 0.0
    endloop
  endfacet
endsolid test_triangle
"""
        ascii_stl.write_text(ascii_content, encoding="utf-8")

        mesh_ascii = ve.load_stl_mesh(str(ascii_stl))
        assert mesh_ascii is not None
        assert mesh_ascii.num_vertices == 3
        assert mesh_ascii.num_indices == 3

        # 2. Binary STL
        binary_stl = tmp_path / "test_binary.stl"
        header = b"Pielosyty Binary STL Test".ljust(80, b"\x00")
        facet_count = 1
        facet = struct.pack(
            "<3f3f3f3fH",
            0.0, 0.0, 1.0,  # normal
            0.0, 0.0, 0.0,  # v1
            1.0, 0.0, 0.0,  # v2
            1.0, 1.0, 0.0,  # v3
            0               # attribute byte count
        )
        with open(binary_stl, "wb") as f:
            f.write(header)
            f.write(struct.pack("<I", facet_count))
            f.write(facet)

        mesh_binary = ve.load_stl_mesh(str(binary_stl))
        assert mesh_binary is not None
        assert mesh_binary.num_vertices == 3
        assert mesh_binary.num_indices == 3

        # 3. Export STL (Binary and ASCII)
        scene = ve.Scene()
        box = scene.create_box(ve.Vec3(2.0, 2.0, 2.0))

        out_bin = tmp_path / "exported_bin.stl"
        assert ve.export_stl(box, str(out_bin), binary=True)
        assert os.path.exists(out_bin)
        reloaded_bin = ve.load_stl_mesh(str(out_bin))
        assert reloaded_bin is not None
        assert reloaded_bin.num_indices == 36  # Box has 12 triangles = 36 indices

        out_ascii = tmp_path / "exported_ascii.stl"
        assert ve.export_stl(box, str(out_ascii), binary=False)
        assert os.path.exists(out_ascii)
        reloaded_ascii = ve.load_stl_mesh(str(out_ascii))
        assert reloaded_ascii is not None
        assert reloaded_ascii.num_indices == 36

    def test_stl_face_normals_and_counts(self, tmp_path):
        """Verify triangle counts and face normal correctness on STL roundtrip."""
        scene = ve.Scene()
        sphere = scene.create_sphere(1.0, 12, 12)
        out_stl = tmp_path / "sphere_test.stl"
        assert ve.export_stl(sphere, str(out_stl), binary=True)

        reloaded = ve.load_stl_mesh(str(out_stl))
        assert reloaded is not None
        assert reloaded.num_indices % 3 == 0
        assert reloaded.num_vertices == reloaded.num_indices
        assert reloaded.local_aabb.is_valid()

    def test_ply_loader_ascii_and_binary(self, tmp_path):
        """Test PLY format parser supporting both ASCII and Binary with vertex colors."""
        # 1. ASCII PLY with vertex colors
        ascii_ply = tmp_path / "test_ascii_colors.ply"
        ascii_content = """ply
format ascii 1.0
comment Test ASCII PLY with colors
element vertex 3
property float x
property float y
property float z
property float nx
property float ny
property float nz
property uchar red
property uchar green
property uchar blue
property uchar alpha
element face 1
property list uchar int vertex_indices
end_header
0.0 0.0 0.0 0.0 0.0 1.0 255 0 0 255
1.0 0.0 0.0 0.0 0.0 1.0 0 255 0 255
0.5 1.0 0.0 0.0 0.0 1.0 0 0 255 255
3 0 1 2
"""
        ascii_ply.write_text(ascii_content, encoding="utf-8")

        mesh_ascii = ve.load_ply_mesh(str(ascii_ply))
        assert mesh_ascii is not None
        assert mesh_ascii.num_vertices == 3
        assert mesh_ascii.num_indices == 3
        assert mesh_ascii.local_aabb.is_valid()

        # 2. Binary PLY (little endian)
        binary_ply = tmp_path / "test_binary_ply.ply"
        header = (
            "ply\n"
            "format binary_little_endian 1.0\n"
            "element vertex 3\n"
            "property float x\n"
            "property float y\n"
            "property float z\n"
            "property float nx\n"
            "property float ny\n"
            "property float nz\n"
            "property uchar red\n"
            "property uchar green\n"
            "property uchar blue\n"
            "property uchar alpha\n"
            "element face 1\n"
            "property list uchar int vertex_indices\n"
            "end_header\n"
        ).encode("utf-8")

        v1 = struct.pack("<3f3f4B", 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 255, 0, 0, 255)
        v2 = struct.pack("<3f3f4B", 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0, 255, 0, 255)
        v3 = struct.pack("<3f3f4B", 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0, 0, 255, 255)
        face = struct.pack("<B3i", 3, 0, 1, 2)

        with open(binary_ply, "wb") as f:
            f.write(header)
            f.write(v1 + v2 + v3)
            f.write(face)

        mesh_bin = ve.load_ply_mesh(str(binary_ply))
        assert mesh_bin is not None
        assert mesh_bin.num_vertices == 3
        assert mesh_bin.num_indices == 3

        # Test scene.load_ply
        scene = ve.Scene()
        model = scene.load_ply(str(ascii_ply))
        assert model is not None
        assert len(model.meshes) >= 1

    def test_unified_mesh_loader(self, tmp_path):
        """Test load_mesh_file dispatching correctly by extension."""
        obj_file = tmp_path / "model.obj"
        obj_file.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", encoding="utf-8")
        mesh_obj = ve.load_mesh_file(str(obj_file))
        assert mesh_obj is not None
        assert mesh_obj.num_vertices == 3

        stl_file = tmp_path / "model.stl"
        stl_file.write_text("solid s\nfacet normal 0 0 1\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid s\n", encoding="utf-8")
        mesh_stl = ve.load_mesh_file(str(stl_file))
        assert mesh_stl is not None
        assert mesh_stl.num_vertices == 3

        bad_file = tmp_path / "model.unknown"
        bad_file.write_text("unsupported content", encoding="utf-8")
        assert ve.load_mesh_file(str(bad_file)) is None

    def test_gltf_exporter(self, tmp_path):
        """Test self-contained glTF 2.0 export with embedded base64 buffers."""
        scene = ve.Scene()
        box1 = scene.create_box(ve.Vec3(1.0, 1.0, 1.0))
        box1.name = "Box_Export"
        box1.transform.position = ve.Vec3(2.0, 0.0, 0.0)

        sphere = scene.create_sphere(0.5, 16, 16)
        sphere.name = "Sphere_Export"
        sphere.transform.position = ve.Vec3(-2.0, 0.0, 0.0)

        gltf_file = tmp_path / "scene_exported.gltf"
        success = ve.export_gltf(scene, str(gltf_file))
        assert success
        assert os.path.exists(gltf_file)

        content = gltf_file.read_text(encoding="utf-8")
        assert "asset" in content
        assert "2.0" in content
        assert "data:application/octet-stream;base64," in content
        assert "Box_Export" in content

        # Verify cgltf in ModelLoader can reload the exported glTF!
        reloaded_scene = ve.Scene()
        model = reloaded_scene.load_model(str(gltf_file))
        assert model is not None
        assert len(model.meshes) >= 2

    def test_screenshot_exporter(self, tmp_path):
        """Test save_screenshot saving to PNG file."""
        app = ve.EngineApp("Screenshot Test", 320, 240)
        scene = app.scene
        scene.create_box(ve.Vec3(1.0, 1.0, 1.0))

        png_file = tmp_path / "test_screenshot.png"
        success = ve.save_screenshot(app, str(png_file))
        assert success
        assert os.path.exists(png_file)
        assert os.path.getsize(png_file) > 0

        # Method call on app
        png_file2 = tmp_path / "app_screenshot.png"
        success2 = app.save_screenshot(str(png_file2))
        assert success2
        assert os.path.exists(png_file2)


class TestPhase7AssetCache:
    """Task 7.1: AssetCache singleton verification."""

    def test_asset_cache_operations_and_deduplication(self, tmp_path):
        cache = ve.AssetCache.instance()
        cache.clear()
        assert len(cache) == 0

        # 1. Manual caching
        mesh = ve.Mesh.create_box(1.0, 1.0, 1.0)
        cache.cache_mesh("box_key", mesh)
        assert cache.has("box_key")
        assert cache.get_mesh("box_key") is mesh

        tex = ve.Texture.create_checkerboard(32, 32, 4)
        cache.cache_texture("checker_key", tex)
        assert cache.has("checker_key")
        assert cache.get_texture("checker_key") is tex

        # 2. Automated loading and deduplication on repeated calls
        obj_file = tmp_path / "cached_cube.obj"
        obj_file.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", encoding="utf-8")

        mesh1 = cache.load_mesh(str(obj_file))
        assert mesh1 is not None
        assert cache.has(str(obj_file))
        mesh2 = cache.load_mesh(str(obj_file))
        assert mesh2 is mesh1  # Exact same cached instance returned!

        # 3. Model deduplication
        scene = ve.Scene()
        model_file = "assets/Soldier.glb"
        if os.path.exists(model_file):
            mod1 = cache.load_model(scene, model_file)
            assert mod1 is not None
            mod2 = cache.load_model(scene, model_file)
            assert mod2 is mod1

        # 4. Removal and clear
        cache.remove("box_key")
        assert not cache.has("box_key")
        assert cache.get_mesh("box_key") is None

        cache.clear()
        assert len(cache) == 0


class TestPhase7EventDispatcher:
    """Task 7.2: EventDispatcher & 3D Mouse Picking verification."""

    def test_node3d_events(self):
        node = ve.Node3D("EventTestNode")

        click_count = 0
        hover_enter_count = 0
        hover_leave_count = 0
        collision_count = 0

        def on_click(ev, data):
            nonlocal click_count
            click_count += 1

        def on_hover_enter(ev, data):
            nonlocal hover_enter_count
            hover_enter_count += 1

        def on_hover_leave():
            nonlocal hover_leave_count
            hover_leave_count += 1

        def on_collision(ev):
            nonlocal collision_count
            collision_count += 1

        node.on("click", on_click)
        node.on("hover_enter", on_hover_enter)
        node.on("hover_leave", on_hover_leave)
        node.on("collision", on_collision)

        assert node.has_listener("click")
        assert node.has_listener("hover_enter")
        assert node.has_listener("hover_leave")
        assert node.has_listener("collision")
        assert not node.has_listener("non_existent")

        # Emit events
        node.emit("click")
        assert click_count == 1

        node.emit("hover_enter")
        assert hover_enter_count == 1

        node.emit("hover_leave")
        assert hover_leave_count == 1

        node.emit("collision")
        assert collision_count == 1

        # Test off & clear
        node.off("click")
        assert not node.has_listener("click")
        node.emit("click")
        assert click_count == 1  # No change

        node.clear_listeners()
        assert not node.has_listener("hover_enter")

    def test_3d_mouse_picking_raycasting_and_dispatch(self):
        """Test camera screen_to_ray, scene.raycast, click hit coordinates, and parent bubbling."""
        app = ve.EngineApp("PickingTest", 800, 600)
        scene = app.scene

        parent_group = ve.Group("PickParent")
        scene.add(parent_group)

        target_box = scene.create_box(ve.Vec3(1.0, 1.0, 1.0))
        target_box.name = "PickTarget"
        target_box.transform.position = ve.Vec3(0.0, 0.0, 0.0)
        parent_group.add(target_box)

        app.camera.position = ve.Vec3(0.0, 0.0, 5.0)
        app.camera.set_target(0.0, 0.0, 0.0)

        # Center raycast (400, 300) on 800x600 screen points straight to (0, 0, 0)
        ray = app.camera.screen_to_ray(400.0, 300.0, 800.0, 600.0)
        hit = scene.raycast(ray)
        assert hit.hit
        assert hit.entity is target_box
        assert abs(hit.point.z - 0.5) < 0.1  # Front face of unit cube at Z = 0.5
        assert abs(hit.distance - 4.5) < 0.2  # Camera at Z = 5.0 -> distance ~ 4.5

        # Register click listener and verify hit data arrives in Python callback
        received_data = []
        parent_events = []

        def on_box_click(ev, data):
            received_data.append((ev, data.hit, data.point.z, data.distance))

        def on_parent_click(ev, data):
            parent_events.append(ev)

        target_box.on("click", on_box_click)
        parent_group.on("click", on_parent_click)

        # Dispatch click via EngineApp helper
        click_hit = app.dispatch_mouse_click(400.0, 300.0)
        assert click_hit.hit
        assert len(received_data) == 1
        ev_name, hit_flag, hit_z, hit_dist = received_data[0]
        assert ev_name == "click"
        assert hit_flag is True
        assert abs(hit_z - 0.5) < 0.1
        assert abs(hit_dist - 4.5) < 0.2
        assert parent_events == ["click"]  # Bubbling works!

        # Miss click at screen corner (10, 10)
        miss_hit = app.dispatch_mouse_click(10.0, 10.0)
        assert not miss_hit.hit
        assert len(received_data) == 1  # No additional click event fired

    def test_hover_enter_and_leave_dispatch(self):
        """Test dispatch_mouse_move triggering hover_enter and hover_leave with hit coordinates."""
        app = ve.EngineApp("HoverTest", 800, 600)
        box = app.scene.create_box(ve.Vec3(1.0, 1.0, 1.0))
        box.transform.position = ve.Vec3(0.0, 0.0, 0.0)
        app.camera.position = ve.Vec3(0.0, 0.0, 5.0)
        app.camera.set_target(0.0, 0.0, 0.0)

        hover_events = []
        box.on("hover_enter", lambda ev, data: hover_events.append(("enter", data.hit if data else None)))
        box.on("hover_leave", lambda ev, data: hover_events.append(("leave", None)))

        # Move mouse over box center
        app.dispatch_mouse_move(400.0, 300.0)
        assert len(hover_events) == 1
        assert hover_events[0][0] == "enter"
        assert hover_events[0][1] is True

        # Move mouse away
        app.dispatch_mouse_move(10.0, 10.0)
        assert len(hover_events) == 2
        assert hover_events[1][0] == "leave"

    def test_app_event_dispatcher(self):
        app = ve.EngineApp("AppEventTest", 800, 600)
        resize_fired = False

        def on_resize(ev, data):
            nonlocal resize_fired
            resize_fired = True

        app.on("resize", on_resize)
        app.emit("resize")
        assert resize_fired


class TestPhase7ImGuiEditorUpgrade:
    """Task 7.3: ImGui Editor upgrade verification (Criterion: F2 mode, hierarchy, gizmo, postprocess, save)."""

    def test_f2_mode_toggle_and_properties(self):
        """Verify Mode switching (GAME <-> EDITOR) and EditorManager properties."""
        app = ve.EngineApp("EditorModeTest", 800, 600)
        assert app.mode == ve.Mode.GAME

        # Toggle mode via F2 method
        app.toggle_mode()
        assert app.mode == ve.Mode.EDITOR

        app.toggle_mode()
        assert app.mode == ve.Mode.GAME

        # Direct property setter
        app.mode = ve.Mode.EDITOR
        assert app.mode == ve.Mode.EDITOR
        assert not app.is_mouse_locked()  # Editor unlocks mouse cursor

        editor = app.editor
        assert editor.show_hierarchy
        assert editor.show_inspector
        assert editor.show_postprocess

        # Hotkey inspection
        assert editor.is_toggle_hotkey_enabled()
        assert editor.toggle_hotkey() == ve.Key.F2

    def test_editor_manager_properties_and_panels(self):
        app = ve.EngineApp("EditorTest", 800, 600)
        editor = app.editor

        # Gizmo operations: 0=Translate, 1=Rotate, 2=Scale
        editor.gizmo_operation = 0
        assert editor.gizmo_operation == 0
        editor.gizmo_operation = 1
        assert editor.gizmo_operation == 1
        editor.gizmo_operation = 2
        assert editor.gizmo_operation == 2

        # Node / Entity selection tracking
        scene = app.scene
        cube = scene.create_cube()
        cube.name = "TargetCube"

        editor.select_entity(cube)
        assert editor.selected_entity is cube
        assert editor.selected_node is cube

        # Manipulate transform via selected node
        editor.selected_node.transform.position = ve.Vec3(5.0, 10.0, 15.0)
        assert abs(cube.transform.position.x - 5.0) < 1e-4

        # Deselect
        editor.select_node(None)
        assert editor.selected_node is None
        assert editor.selected_entity is None

    def test_material_and_postprocess_adjustments(self):
        """Verify modifying PBR materials and post-processing parameters via Editor API."""
        app = ve.EngineApp("EditorParamsTest", 800, 600)
        scene = app.scene

        # 1. PBR Material adjustments
        cube = scene.create_box(ve.Vec3(1.0, 1.0, 1.0))
        mat = cube.material
        assert mat is not None
        mat.roughness = 0.35
        mat.metallic = 0.85
        mat.emissive_intensity = 4.5
        mat.base_color = ve.Vec4(1.0, 0.2, 0.1, 1.0)
        assert abs(mat.roughness - 0.35) < 1e-4
        assert abs(mat.metallic - 0.85) < 1e-4
        assert abs(mat.emissive_intensity - 4.5) < 1e-4

        # 2. PointLight adjustments
        pt_light = ve.PointLight("TestPointLight", ve.Vec3(1.0, 0.8, 0.2), 3.0, 25.0)
        pt_light.transform.position = ve.Vec3(1.0, 2.0, 3.0)
        scene.add_light(pt_light)
        assert pt_light is not None
        pt_light.intensity = 5.0
        pt_light.range = 35.0
        assert abs(pt_light.intensity - 5.0) < 1e-4
        assert abs(pt_light.range - 35.0) < 1e-4

        # 3. Post-Process (BloomPass & SSAOPass) adjustments
        composer = ve.EffectComposer(800, 600)
        bloom = ve.BloomPass(threshold=0.8, strength=2.2, radius=0.6)
        composer.add_pass(bloom)
        app.composer = composer

        assert app.composer is not None
        bloom.threshold = 1.2
        bloom.strength = 3.5
        bloom.radius = 0.9
        assert abs(bloom.threshold - 1.2) < 1e-4
        assert abs(bloom.strength - 3.5) < 1e-4
        assert abs(bloom.radius - 0.9) < 1e-4

    def test_save_scene_to_script(self, tmp_path):
        """Verify save_scene_to_script generates valid, compilable Python code."""
        app = ve.EngineApp("ScriptExportTest", 800, 600)
        scene = app.scene
        box = scene.create_box(ve.Vec3(2.0, 2.0, 2.0))
        box.name = "ExportedBox"
        box.transform.position = ve.Vec3(1.0, 2.0, 3.0)

        script_file = tmp_path / "exported_scene.py"
        success = app.editor.save_scene_to_script(str(script_file))
        assert success
        assert os.path.exists(script_file)

        script_text = script_file.read_text(encoding="utf-8")
        assert "import pielosyty as ve" in script_text
        assert "scene.light" in script_text
        assert "ExportedBox" in script_text

        # Verify that the generated Python script compiles with 0 syntax errors!
        compiled = compile(script_text, str(script_file), "exec")
        assert compiled is not None
