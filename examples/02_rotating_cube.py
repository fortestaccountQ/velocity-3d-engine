"""Milestone 2 Test: 3D Rotating Cube with Depth Test and Python Frame Callbacks."""

import sys
from pathlib import Path

# Ensure 'python' package dir is available if running directly from repo root
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import engine


def main():
    print("=" * 65)
    print(" Engine 3D: Milestone 2 - Rotating Cube with Z-Buffer & Callbacks")
    print("=" * 65)
    print("Rendering: Sokol GFX 3D Pipeline (D3D11 / GL / Metal / WebGL2)")
    print("Depth Test: SG_COMPAREFUNC_LESS_EQUAL (Z-Buffer Enabled)")
    print("Controls: Rotating continuously via Python @app.on_update(dt)")
    print("Press ESC or close the window to exit.")
    print("=" * 65)

    # 1. Initialize window with dark-blue clear color (#1a1a24)
    app = engine.App(
        title="Engine 3D: Rotating Cube (Milestone 2)",
        width=800,
        height=600,
        clear_color=[0.102, 0.102, 0.141, 1.0],
    )

    # Initial rotation
    app.rotation_x = 20.0
    app.rotation_y = 30.0

    frame_count = 0
    total_time = 0.0

    # 2. Register Python per-frame update callback with dt
    @app.on_update
    def update(dt: float):
        nonlocal frame_count, total_time
        frame_count += 1
        total_time += dt

        # Continuous rotation based on elapsed delta time (in degrees/sec)
        app.rotation_x += 45.0 * dt
        app.rotation_y += 60.0 * dt

        # Periodic log output to demonstrate live Python frame execution
        if frame_count % 120 == 0:
            fps = 1.0 / dt if dt > 0 else 0.0
            print(
                f"[Frame {frame_count:04d}] dt={dt*1000.0:5.2f}ms (~{fps:4.1f} FPS) | "
                f"rot_x={app.rotation_x % 360.0:5.1f}°, rot_y={app.rotation_y % 360.0:5.1f}°"
            )

    # 3. Launch native event and rendering loop
    app.run()

    print("Rotating cube demo exited cleanly.")


if __name__ == "__main__":
    main()
