"""Milestone 1 Test: Basic window with Sokol GFX clear color."""

import sys
from pathlib import Path

# Ensure 'python' package dir is available if running directly from repo root
repo_root = Path(__file__).resolve().parent.parent
python_pkg_dir = repo_root / "python"
if str(python_pkg_dir) not in sys.path:
    sys.path.insert(0, str(python_pkg_dir))

import engine


def main():
    print("=" * 60)
    print(" Engine Core PoC: Milestone 1 - Sokol GFX + Nanobind Window")
    print("=" * 60)
    print("Window Configuration: 800x600, Clear Color: #1a1a24 (dark blue)")
    print("Press ESC or close the window to exit.")
    print("=" * 60)

    # Initialize app with title, size, and clear color #1a1a24
    app = engine.App(
        title="Engine Core PoC",
        width=800,
        height=600,
        clear_color=[0.102, 0.102, 0.141, 1.0],
    )

    print(f"App title: {app.title}")
    print(f"App size:  {app.width}x{app.height}")
    print(f"App color: {app.get_clear_color()}")

    # Run the native Sokol event and rendering loop
    app.run()

    print("Native application loop exited cleanly.")


if __name__ == "__main__":
    main()
