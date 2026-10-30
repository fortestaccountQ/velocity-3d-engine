# Troubleshooting & Diagnostics

This guide provides authoritative solutions for common compilation errors, graphics driver quirks, hardware limitations, and runtime issues encountered when working with the **Velocity 3D Engine**.

---

## 🩺 System Diagnostic Health Check

If you encounter unexpected crashes, blank screens, or import failures, run the following diagnostic script to inspect your Python runtime, C++ extension linkage, and GPU backend:

```python
"""Velocity 3D Engine - System Diagnostics."""

from __future__ import annotations
import sys
import platform


def run_diagnostics() -> None:
    print("=" * 60)
    print(" Velocity 3D Engine: Environment Diagnostics")
    print("=" * 60)
    print(f"OS:             {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"Python Version: {platform.python_version()} ({platform.architecture()[0]})")
    print(f"Executable:     {sys.executable}")

    try:
        import VelocityEngine as ve
        print(f"Engine Module:  LOADED (Version: {ve.__version__})")
        print(f"Package Path:   {ve.__file__}")

        # Test App Initialization
        app = ve.App(title="Diagnostic Window", width=320, height=240)
        print(f"Active Scene:   {app.scene}")
        print(f"Active Camera:  {app.camera}")
        print("Backend Status: OK (Direct3D 11 / Metal / OpenGL Core functional)")
    except ImportError as err:
        print(f"Engine Module:  FAILED TO IMPORT ({err})")
    except Exception as err:
        print(f"Engine Runtime: ERROR ({err})")
    print("=" * 60)


if __name__ == "__main__":
    run_diagnostics()
```

---

## 🔨 1. Compilation & Build Issues

### "No CMAKE_CXX_COMPILER could be found"
* **Operating System**: Windows
* **Root Cause**: CMake cannot locate the Microsoft Visual C++ compiler (`cl.exe`). This occurs when Visual Studio 2022 is installed without the C++ desktop workload, or when running commands from a standard terminal without MSVC environment paths configured.
* **Resolution**:
    1. Open the **Visual Studio Installer** and verify that **Desktop development with C++** is checked.
    2. Launch your command prompt from the **x64 Native Tools Command Prompt for VS 2022**, or load the compiler paths into your existing PowerShell session:
       ```powershell
       & "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
       ```

---

### "fatal error C1128: number of sections exceeded object file format limit"
* **Operating System**: Windows (MSVC)
* **Root Cause**: Extensive C++20 template instantiations in nanobind and GLM can exceed the default COFF object file limit of 65,536 sections.
* **Resolution**:
    * Ensure `/bigobj` is passed to MSVC. In `CMakeLists.txt`, Velocity automatically sets:
      ```cmake
      if (MSVC)
          add_compile_options(/MP /bigobj)
      endif()
      ```
    * If building custom extensions or standalone translation units, always add `/bigobj` to your compiler flags.

---

### "ModuleNotFoundError: No module named '_VelocityEngine_core'"
* **Operating System**: All platforms
* **Root Cause**: Python cannot find the compiled native shared library (`.pyd` on Windows, `.so` on Linux/macOS) in `python/VelocityEngine/`.
* **Resolution**:
    * Compile the native extension in editable mode using:
      ```bash
      pip install -e . --no-build-isolation
      ```
    * If building directly with CMake, ensure the compiled library is copied to `python/VelocityEngine/` and add `python` to your `PYTHONPATH`:
      ```bash
      # Linux / macOS
      export PYTHONPATH="$PWD/python:$PYTHONPATH"
      # Windows PowerShell
      $env:PYTHONPATH = "$PWD\python;$env:PYTHONPATH"
      ```

---

## 🖥️ 2. Graphics Backend & Hardware Compatibility

### Direct3D 11 vs OpenGL Core vs Metal: Depth Buffer Range
* **Architecture Detail**:
    * Historically, OpenGL uses a normalized device coordinate (NDC) depth range of `[-1.0, 1.0]`, whereas Direct3D 11, Metal, and Vulkan use `[0.0, 1.0]`.
    * This discrepancy often causes clipping or inverted projection bugs when porting shaders across platforms.
* **Velocity Solution**:
    * Velocity enforces **zero-to-one depth** uniformly across all platforms by compiling GLM with:
      ```cmake
      add_compile_definitions(GLM_FORCE_DEPTH_ZERO_TO_ONE)
      ```
    * Depth testing uses `SG_COMPAREFUNC_LESS_EQUAL` with clear depth set to `1.0`. All projection matrices produce standard `[0.0, 1.0]` Z coordinates regardless of whether you are running on Direct3D 11 (Windows), Metal (macOS), or OpenGL Core (Linux).

---

### Coordinate System & Handedness
* **Conventions**:
    * Velocity 3D Engine uses a **Right-Handed Cartesian** coordinate system:
        * **+X**: Points Right.
        * **+Y**: Points Up.
        * **-Z**: Points Forward (into the screen / camera viewing direction).
    * When placing cameras, looking at a point in the negative Z direction aligns with forward motion:
      ```python
      app.camera.set_position(0.0, 2.0, 5.0)
      app.camera.look_at(ve.Vec3(0.0, 0.0, 0.0))  # Forward direction is -Z
      ```

---

### Headless Environments & CI Testing (Blank Screen / Crash)
* **Root Cause**: Attempting to launch a graphical window inside a headless Docker container, Linux server, or GitHub Actions runner without an active X11 display or GPU driver will cause `sokol_app` to fail.
* **Resolution**:
    * Run test suites in headless test mode using pytest:
      ```bash
      pytest tests/ -q
      ```
    * On Linux without a physical GPU, install `xvfb` and `mesa-utils`:
      ```bash
      sudo apt-get install -y xvfb libgl1-mesa-dri
      xvfb-run -s "-screen 0 1280x720x24" python examples/01_hello_pbr.py --test
      ```

---

## 📐 3. Geometry, Buffers & Index Limits

### The 65,535 Vertex Index Limit (`uint16_t`)
> [!CAUTION] Hard Sokol GFX Index Buffer Limit
> By default, Sokol GFX index buffers in standard pipelines use 16-bit unsigned integers (`uint16_t`). This imposes a hard limit of **65,535 vertices** per single mesh draw call.

* **Symptom**:
    * Generating a high-density terrain grid or loading an unoptimized 3D scan with > 65,535 vertices causes distorted triangles, vertex index wrapping, or assertions:
      ```text
      sokol_gfx assertion failed: _sg_validate_draw()
      ```
* **Resolution**:
    1. **Procedural Grid Resolution Limit**: When generating procedural planes or wave grids, do not exceed a resolution of **180x180**:
       $$\text{Vertices} = 180 \times 180 = 32,400 < 65,535$$
    2. **Mesh Chunking**: For large open-world landscapes or complex models exceeding 65,535 vertices, split the geometry into multiple chunks or sub-meshes:
       ```python
       # Subdivide terrain into distinct chunks of 128x128 vertices
       chunk_00 = ve.Mesh.create_plane(width=50, depth=50, u_segments=128, v_segments=128)
       chunk_01 = ve.Mesh.create_plane(width=50, depth=50, u_segments=128, v_segments=128)
       chunk_01.transform.set_position(50.0, 0.0, 0.0)
       ```

---

## ⚡ 4. Dynamic Buffers & GPU Memory Hazards

### Updating Mesh Vertices on CPU (Waves & Skinning)
* **Symptom**: Modifying vertex coordinates at runtime on a static mesh generates an assertion or fails to update on the GPU:
  ```text
  sokol_gfx: SG_USAGE_IMMUTABLE buffer update forbidden
  ```
* **Root Cause**:
    * Static meshes default to `SG_USAGE_IMMUTABLE` for optimal GPU caching and memory bandwidth. Immutable buffers cannot be updated after initial allocation.
* **Resolution**:
    * Mark the mesh as dynamic **before** creating or updating GPU buffers by calling `mesh.mark_dynamic()`. This configures the underlying GPU buffer with `SG_USAGE_DYNAMIC` or `SG_USAGE_STREAM`:

```python
import VelocityEngine as ve

# 1. Create procedural plane mesh
plane = ve.Mesh.create_plane(width=20.0, depth=20.0, u_segments=100, v_segments=100)

# 2. CRITICAL: Mark mesh buffer usage as dynamic
plane.mark_dynamic()

# 3. Create entity and add to scene
entity = ve.Entity(mesh=plane, material=ve.StandardMaterial())
app.scene.add_entity(entity)

# 4. Safely deform vertices per frame on the CPU
@app.on_update
def animate_waves(dt: float) -> None:
    # Update vertex positions and upload to GPU
    plane.update_dynamic_vertices()
```

---

## 🐍 5. Python GIL & Performance Considerations

While Velocity's core renderer and math calculations run in compiled C++20, Python code executed inside `@app.on_update` runs under the Python Global Interpreter Lock (GIL).

### Best Practices for 60+ FPS Gameplay Loops

1. **Avoid Python Loop Vertex Iteration**:
    * Never iterate through thousands of vertices using Python `for v in vertices:` loops on every frame.
    * Use **NumPy vectorized operations** or custom vertex shaders instead:
      ```python
      # Vectorized NumPy approach (sub-millisecond)
      heights = np.sin(x_coords * 0.5 + time) * np.cos(z_coords * 0.5 + time)
      mesh.set_height_array(heights)
      ```
2. **Use `InstancedMesh` for High Entity Counts**:
    * Rendering 10,000 individual `ve.Entity` objects creates 10,000 separate scene graph traversals and draw calls.
    * Instead, use a single **`ve.InstancedMesh`** to draw up to **50,000+** instances in one draw call:
      ```python
      # Draw 10,000 trees in a single GPU draw call
      forest = ve.InstancedMesh(base_mesh=tree_mesh, base_material=tree_material, capacity=10000)
      for i in range(10000):
          forest.set_instance(i, transform_matrix, tint_color)
      app.scene.add_entity(forest)
      ```
3. **Nanobind Zero-Overhead Calls**:
    * Nanobind releases the Python GIL during heavy native C++ scene rendering, allowing background worker threads or streaming audio threads to run concurrently without stutter.

---

## 🔊 6. Audio Device & Miniaudio Diagnostics

### Silent Audio or Crash on Remote Desktops / Virtual Machines
* **Symptom**: `AudioManager` logs a warning or fails to produce sound when executing remotely or in a VM.
* **Root Cause**: Virtualized environments frequently lack a physical audio output endpoint, causing `ma_device_init` in `miniaudio` to report `MA_NO_DEVICE`.
* **Resolution**:
    * Velocity's `AudioManager` automatically detects missing output endpoints and gracefully falls back to a dummy silent backend without crashing the game loop.
    * If audio is required in Windows Remote Desktop (RDP), enable remote audio playback in your RDP connection settings (*Local Resources -> Remote Audio -> Play on this computer*).

---

## 🔍 Need Further Assistance?

If your issue is not covered here:

1. Search the **[GitHub Issues](https://github.com/fortestaccountQ/velocity-3d-engine/issues)** tracker for reported bugs and solutions.
2. Join the developer discussions on our community channels.
3. Review the complete **[API Reference](../api-reference/python/app.md)** for detailed function signatures and contracts.
