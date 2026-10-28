"""Example A: 12-line Model Viewer (Three.js Parity Manifesto)."""
import sys
from pathlib import Path
from VelocityEngine import App, OrbitController, Color, WARM_WHITE

duck_path = str(Path(__file__).resolve().parent.parent / "assets" / "duck.glb")
app = App("VelocityEngine - 12-Line Model Viewer", width=1280, height=720, clear_color="#181a20")
app.camera = OrbitController(target=(0.0, 0.8, 0.0), distance=3.5, min_distance=1.0, max_distance=20.0)
app.scene.set_sun(direction=(-1.0, -2.0, -1.0), color=WARM_WHITE, intensity=1.5)
app.scene.create_grid(size=30.0, step=1.0, color=Color.from_hex("#333842"))
duck = app.scene.load_model(duck_path)
app.ui.draw_text("VelocityEngine | OrbitController | duck.glb", (24, 24), size=20, color=WARM_WHITE)
app.ui.show_stats(True)
if "--test" in sys.argv:
    app.on_update(lambda dt: app.close())
if __name__ == "__main__":
    app.run()
