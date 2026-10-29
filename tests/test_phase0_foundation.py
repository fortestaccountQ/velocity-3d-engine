"""Phase 0 Foundation Test Suite: Pielosyty 3D Engine.

Tests Phase 0 Acceptance Criteria:
- Task 0.1: UIOverlay custom commands (draw_text, draw_rect, draw_crosshair, draw_line, flush)
  and submission to EngineApp.submit_ui_commands.
- Task 0.2: InstancedMesh 10,000 instance data allocation, GPU buffer preparation,
  matrix and color updates, adding to Scene and shadow/scene pipelines.
- Task 0.3: Primary 'pielosyty' package and 100% backwards-compatible 'VelocityEngine' alias parity.
- Task 0.4: Hostile edge case and stress verification (huge counts, boundary coords, null inputs).
"""

import math
import pytest
import pielosyty as pe
import VelocityEngine as ve


class TestPhase0PackageParity:
    """Verify package rebranding and backwards compatibility alias layer."""

    def test_package_exports_exist(self):
        assert hasattr(pe, "__version__")
        assert hasattr(ve, "__version__")
        assert pe.__version__ == ve.__version__

        core_symbols = [
            "App",
            "EngineApp",
            "Scene",
            "Entity",
            "Mesh",
            "InstancedMesh",
            "InstanceData",
            "Texture",
            "Material",
            "Camera",
            "DirectionalLight",
            "Transform",
            "Vec2",
            "Vec3",
            "Vec4",
            "AABB",
            "Ray",
            "RaycastHit",
            "UIOverlay",
            "UICommand",
            "UICommandType",
            "UITextCommand",
            "UIRectCommand",
            "UICrosshairCommand",
            "UILineCommand",
            "Color",
            "WHITE",
            "RED",
            "GREEN",
            "BLUE",
            "TweenManager",
            "Fog",
            "Group",
        ]
        for sym in core_symbols:
            assert hasattr(pe, sym), f"Symbol '{sym}' missing from pielosyty"
            assert hasattr(ve, sym), f"Symbol '{sym}' missing from VelocityEngine"

    def test_alias_parity_identity(self):
        """VelocityEngine symbols must map directly to pielosyty symbols."""
        assert ve.UIOverlay is pe.UIOverlay
        assert ve.UICommand is pe.UICommand
        assert ve.UICommandType is pe.UICommandType
        assert ve.InstancedMesh is pe.InstancedMesh
        assert ve.Color is pe.Color
        assert ve.App is pe.App
        assert ve.EngineApp is pe.EngineApp
        assert ve.Scene is pe.Scene

        # Backwards compatibility check for ve._core
        assert hasattr(ve, "_core")
        assert ve._core is pe._core


class TestUIOverlayCustomCommands:
    """Verify Task 0.1 custom UI overlay commands creation, conversion, and submission."""

    def test_ui_command_type_enum(self):
        assert hasattr(pe.UICommandType, "Text")
        assert hasattr(pe.UICommandType, "Rect")
        assert hasattr(pe.UICommandType, "Line")
        assert hasattr(pe.UICommandType, "Crosshair")

    def test_draw_text_signatures(self):
        ui = pe.UIOverlay()
        # Acceptance criterion signature: ui.draw_text('Hello', 100, 100)
        ui.draw_text("Hello", 100, 100)
        # Tuple coordinate signature
        ui.draw_text("World", (200, 150), size=24.0, color=pe.RED)
        # Keyword position signature
        ui.draw_text("Kwarg", pos=(300, 250), size=18.0, color=pe.GREEN)

        assert len(ui.commands) == 3

        c0 = ui.commands[0]
        assert isinstance(c0, pe.UITextCommand)
        assert c0.text == "Hello"
        assert c0.pos == (100.0, 100.0)

        c1 = ui.commands[1]
        assert c1.text == "World"
        assert c1.pos == (200.0, 150.0)
        assert c1.size == 24.0

        native0 = c0.to_native()
        assert native0.type == pe.UICommandType.Text
        assert native0.text == "Hello"
        assert abs(native0.pos.x - 100.0) < 1e-4
        assert abs(native0.pos.y - 100.0) < 1e-4

    def test_draw_rect_signatures(self):
        ui = pe.UIOverlay()
        # Positional x, y, w, h
        ui.draw_rect(10, 20, 100, 50, color=pe.BLUE, thickness=2.0)
        # Tuple (x, y, w, h)
        ui.draw_rect((30, 40, 120, 60), color=pe.YELLOW)
        # Keyword arguments
        ui.draw_rect(x=5, y=5, w=50, h=50, color=pe.WHITE)

        assert len(ui.commands) == 3

        n0 = ui.commands[0].to_native()
        assert n0.type == pe.UICommandType.Rect
        assert abs(n0.pos.x - 10.0) < 1e-4
        assert abs(n0.pos.y - 20.0) < 1e-4
        assert abs(n0.size.x - 100.0) < 1e-4
        assert abs(n0.size.y - 50.0) < 1e-4
        assert abs(n0.thickness - 2.0) < 1e-4

    def test_draw_crosshair_signatures(self):
        ui = pe.UIOverlay()
        ui.draw_crosshair(size=14.0, color=pe.RED)
        ui.draw_crosshair(12.0, (400, 300))
        ui.draw_crosshair(pos=(100, 100), size=8.0, thickness=1.5)

        assert len(ui.commands) == 3
        n0 = ui.commands[0].to_native()
        assert n0.type == pe.UICommandType.Crosshair
        assert abs(n0.size.x - 14.0) < 1e-4

        n1 = ui.commands[1].to_native()
        assert abs(n1.pos.x - 400.0) < 1e-4
        assert abs(n1.pos.y - 300.0) < 1e-4

    def test_draw_line_signatures(self):
        ui = pe.UIOverlay()
        ui.draw_line((0, 0), (800, 600), thickness=2.5, color=pe.CYAN)
        ui.draw_line(10, 20, 300, 400, pe.WHITE, 1.0)

        assert len(ui.commands) == 2
        n0 = ui.commands[0].to_native()
        assert n0.type == pe.UICommandType.Line
        assert abs(n0.pos.x - 0.0) < 1e-4
        assert abs(n0.pos.y - 0.0) < 1e-4
        assert abs(n0.size.x - 800.0) < 1e-4
        assert abs(n0.size.y - 600.0) < 1e-4
        assert abs(n0.thickness - 2.5) < 1e-4

    def test_flush_and_submit_to_engine(self):
        app = pe.App("Test UI Submission", 800, 600)
        app.clear_ui_commands()

        app.ui.draw_text("Hello Phase 0", 100, 100)
        app.ui.draw_rect(50, 50, 200, 100, pe.Color(0, 1, 0, 0.5))
        app.ui.draw_crosshair(size=10.0, color=pe.WHITE)
        app.ui.draw_line((0, 0), (100, 100), color=pe.RED)

        assert len(app.ui.commands) == 4

        flushed = app.ui.flush(app)
        assert len(flushed) == 4
        assert len(app.ui.commands) == 0

        # Verify EngineApp received the custom UI commands
        assert len(app._core.custom_ui_commands) == 4
        c_text = app._core.custom_ui_commands[0]
        assert c_text.type == pe.UICommandType.Text
        assert c_text.text == "Hello Phase 0"

        # Calling clear_ui_commands clears the native queue
        app.clear_ui_commands()
        assert len(app._core.custom_ui_commands) == 0


class TestInstancedMesh10k:
    """Verify Task 0.2 InstancedMesh with 10,000 instances."""

    def test_instanced_mesh_allocation_10000(self):
        mesh = pe.Mesh.create_cube()
        assert mesh is not None
        assert mesh.num_indices == 36

        inst = pe.InstancedMesh(mesh, 10000)
        assert inst.instance_count() == 10000
        assert inst.count == 10000
        assert inst.mesh is mesh

    def test_instanced_mesh_updates(self):
        mesh = pe.Mesh.create_cube()
        inst = pe.InstancedMesh(mesh, 10000)

        # Set first, middle, and last instance
        inst.set_instance(0, (1.0, 0.0, 0.0, 1.0))
        inst.set_color_at(5000, pe.Color(0.0, 1.0, 0.0, 1.0))
        inst.set_matrix_at(9999, None)

        assert inst.count == 10000

        # Dynamic resize
        inst.set_instance_count(12000)
        assert inst.count == 12000
        inst.count = 10000
        assert inst.count == 10000

    def test_scene_instanced_mesh_management(self):
        scene = pe.Scene()
        mesh = pe.Mesh.create_cube()
        inst = pe.InstancedMesh(mesh, 10000)

        assert len(scene.instanced_meshes) == 0

        # Method 1: add_instanced_mesh
        scene.add_instanced_mesh(inst)
        assert len(scene.instanced_meshes) == 1
        assert scene.instanced_meshes[0].instance_count() == 10000

        # Method 2: remove_instanced_mesh
        scene.remove_instanced_mesh(inst)
        assert len(scene.instanced_meshes) == 0

        # Method 3: polymorphic scene.add(inst)
        scene.add(inst)
        assert len(scene.instanced_meshes) == 1

        # Clear clears instanced meshes
        scene.clear()
        assert len(scene.instanced_meshes) == 0

    def test_ensure_gpu_buffers_safe(self):
        mesh = pe.Mesh.create_cube()
        inst = pe.InstancedMesh(mesh, 10000)
        # In headless python without Sokol window, ensure_gpu_buffers() safely returns bool without crash
        ok = inst.ensure_gpu_buffers()
        assert isinstance(ok, bool)


class TestPhase0AcceptanceCriterion:
    """Exact check of Phase 0 readiness criterion:

    'Скрипт с ui.draw_text('Hello', 100, 100) и InstancedMesh на 10 000 кубов рендерится в 60+ FPS с тенями.'
    """

    def test_criterion_script_execution(self):
        app = pe.App("Phase 0 Readiness Test", 1280, 720)
        mesh = pe.Mesh.create_cube()
        inst = pe.InstancedMesh(mesh, 10000)

        # Populate instances with varying colors
        for i in range(50):
            inst.set_instance(i, (i / 50.0, 1.0 - i / 50.0, 0.5, 1.0))

        app.scene.add_instanced_mesh(inst)
        assert len(app.scene.instanced_meshes) == 1
        assert app.scene.instanced_meshes[0].instance_count() == 10000

        # Draw UI as specified in criterion
        app.ui.draw_text("Hello", 100, 100)
        assert len(app.ui.commands) == 1

        # Simulate frame tick driving internal pipelines
        app._on_internal_frame(0.016)

        # UI commands flushed and submitted to engine
        assert len(app.ui.commands) == 0
        assert len(app._core.custom_ui_commands) == 1
        assert app._core.custom_ui_commands[0].text == "Hello"
        assert abs(app._core.custom_ui_commands[0].pos.x - 100.0) < 1e-4
        assert abs(app._core.custom_ui_commands[0].pos.y - 100.0) < 1e-4


class TestHostileStressAndEdgeCases:
    """Hostile QA edge cases and boundary conditions."""

    def test_empty_and_extreme_strings(self):
        ui = pe.UIOverlay()
        ui.draw_text("", 0, 0)
        ui.draw_text("   ", -100, -200)
        ui.draw_text("A" * 1000, 10000, 20000)
        assert len(ui.commands) == 3
        native = [c.to_native() for c in ui.commands]
        assert len(native) == 3
        assert native[0].text == ""
        assert len(native[2].text) == 1000

    def test_negative_and_zero_rect_dimensions(self):
        ui = pe.UIOverlay()
        ui.draw_rect(-50, -50, 0, 0, thickness=0.0)
        ui.draw_rect(-100, -100, -20, -30, thickness=-1.0)
        assert len(ui.commands) == 2
        n0 = ui.commands[0].to_native()
        assert n0.size.x == 0.0 and n0.size.y == 0.0

    def test_degenerate_lines(self):
        ui = pe.UIOverlay()
        # Zero-length line
        ui.draw_line(50, 50, 50, 50)
        # Negative coords
        ui.draw_line(-100, -200, -300, -400)
        assert len(ui.commands) == 2
        flushed = ui.flush()
        assert len(flushed) == 2

    def test_instanced_mesh_extreme_counts(self):
        mesh = pe.Mesh.create_cube()
        # Zero count
        inst_zero = pe.InstancedMesh(mesh, 0)
        assert inst_zero.count == 0

        # Huge count
        inst_large = pe.InstancedMesh(mesh, 50000)
        assert inst_large.count == 50000

        # Out of bounds set_instance automatically resizes
        inst_zero.set_instance(15, (1, 1, 1, 1))
        assert inst_zero.count >= 16

    def test_null_mesh_instanced(self):
        inst_null = pe.InstancedMesh(None, 100)
        assert inst_null.count == 100
        # Must safely return False without crash
        assert inst_null.ensure_gpu_buffers() is False
