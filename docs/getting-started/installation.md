# Comprehensive Installation Guide

This guide covers everything required to build, install, and verify the **Velocity 3D Engine** from source across **Windows**, **Linux**, and **macOS** for **Python 3.10 through 3.13**.

Velocity uses modern modern build infrastructure powered by **scikit-build-core**, **nanobind v2.4+**, **CMake >= 3.24**, and the **Ninja** build system to achieve near-instant incremental builds and clean Python wheel packaging.

---

## 📋 System Prerequisites

Before building the engine, ensure your operating system has a modern C++20 compiler and required platform graphics development headers installed.

=== ":material-microsoft-windows: Windows"

    ### 1. C++20 Compiler (MSVC 2022)
    * Install **[Visual Studio 2022](https://visualstudio.microsoft.com/)** (Community, Professional, or Enterprise) or the lightweight **[Visual Studio 2022 Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022)**.
    * In the Visual Studio Installer, select the **Desktop development with C++** workload.
    * Verify that the following optional components are checked:
        * **MSVC v143 - VS 2022 C++ x64/x86 build tools**
        * **Windows 10 SDK** (or **Windows 11 SDK**)
        * **C++ CMake tools for Windows**

    ### 2. Python 3.10 – 3.13 (64-bit)
    * Download Python from [python.org](https://www.python.org/downloads/windows/).
    * Ensure the checkbox **"Add Python to PATH"** is selected during installation.
    * Verify your Python architecture in PowerShell:
        ```powershell
        python -c "import platform; print(platform.architecture()[0])"
        # Must output: 64bit
        ```

    ### 3. Git for Windows
    * Install [Git for Windows](https://git-scm.com/download/win).

=== ":material-linux: Linux"

    ### 1. Compiler & Platform Headers
    Velocity Engine on Linux targets the **OpenGL 3.3+ Core** profile (`SOKOL_GLCORE`) and requires modern X11 development headers.

    === "Ubuntu / Debian (22.04 LTS or newer)"
        ```bash
        sudo apt-get update
        sudo apt-get install -y \
            build-essential \
            gcc-12 g++-12 \
            cmake \
            ninja-build \
            git \
            python3-dev \
            python3-pip \
            python3-venv \
            libx11-dev \
            libxcursor-dev \
            libxi-dev \
            libxinerama-dev \
            libxrandr-dev \
            libgl1-mesa-dev \
            libasound2-dev
        ```
        Ensure GCC 12+ is set as default:
        ```bash
        sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-12 100 --slave /usr/bin/g++ g++ /usr/bin/g++-12
        ```

    === "Fedora (38 or newer)"
        ```bash
        sudo dnf groupinstall -y "Development Tools" "C Development Tools and Libraries"
        sudo dnf install -y \
            gcc-c++ \
            cmake \
            ninja-build \
            git \
            python3-devel \
            python3-pip \
            libX11-devel \
            libXcursor-devel \
            libXi-devel \
            libXinerama-devel \
            libXrandr-devel \
            mesa-libGL-devel \
            alsa-lib-devel
        ```

    === "Arch Linux"
        ```bash
        sudo pacman -Syu --needed \
            base-devel \
            gcc \
            cmake \
            ninja \
            git \
            python \
            python-pip \
            libx11 \
            libxcursor \
            libxi \
            libxinerama \
            libxrandr \
            mesa \
            alsa-lib
        ```

=== ":material-apple: macOS"

    ### 1. Apple Xcode Command Line Tools
    Velocity on macOS targets the **Metal** backend (`SOKOL_METAL`) with native Cocoa windowing.
    ```bash
    xcode-select --install
    ```

    ### 2. Homebrew Packages
    Install CMake, Ninja, and Python using [Homebrew](https://brew.sh/):
    ```bash
    brew install cmake ninja git python@3.12
    ```
    Ensure Homebrew's Python is active in your terminal shell (`which python3`).

---

## 📦 Step-by-Step Installation

### Step 1: Clone the Repository

Clone the project repository to your local drive:

```bash
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine
```

### Step 2: Create a Clean Virtual Environment

Always isolate the engine's development dependencies inside a dedicated virtual environment:

=== ":material-microsoft-windows: Windows (PowerShell)"
    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    ```

=== ":material-microsoft-windows: Windows (Command Prompt)"
    ```cmd
    python -m venv .venv
    .\.venv\Scripts\activate.bat
    ```

=== ":material-linux: Linux / :material-apple: macOS (Bash/Zsh)"
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

### Step 3: Install Build Prerequisites

Upgrade `pip` and install the compilation toolchain requirements:

```bash
pip install --upgrade pip setuptools wheel
pip install scikit-build-core nanobind ninja pytest numpy
```

---

## 🔨 Build Methods

You can build and install Velocity 3D Engine using either the Python package manager (**Method A**, recommended for Python developers) or directly via CMake (**Method B**, recommended for C++ engine developers).

### Method A: Python Editable Mode (Recommended)

Editable mode links your local `python/VelocityEngine` package directly to your virtual environment while compiling the C++20 native extension `_VelocityEngine_core`:

```bash
pip install -e . --no-build-isolation -v
```

> [!NOTE] Why `--no-build-isolation`?
> Passing `--no-build-isolation` instructs `pip` to use the already installed `nanobind` and `scikit-build-core` packages directly inside your active virtual environment, avoiding repeated redundant downloads and speeding up re-compilation.

During the build process:
1. `scikit-build-core` invokes CMake with the Ninja generator.
2. CMake compiles the static library `velocity_engine_core` (Sokol GFX, GLM math, ImGui, miniaudio, cgltf).
3. Nanobind generates the native Python shared module:
    * **Windows**: `python/VelocityEngine/_VelocityEngine_core.cp313-win_amd64.pyd`
    * **Linux**: `python/VelocityEngine/_VelocityEngine_core.cpython-312-x86_64-linux-gnu.so`
    * **macOS**: `python/VelocityEngine/_VelocityEngine_core.cpython-312-darwin.so`
4. Post-build hooks automatically mirror the compiled extension into `python/velocity/` and `python/pielosyty/` for backward compatibility.

---

### Method B: Standalone CMake & Ninja Build

For developers working directly on the C++20 core engine headers and source files, building via standalone CMake gives you full control over IDE integration and build configurations:

```bash
# 1. Generate the build tree using Ninja in Release mode
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release

# 2. Compile all targets in parallel
cmake --build build --config Release -j
```

To expose the compiled module to your Python interpreter when using Method B:

=== "Windows (PowerShell)"
    ```powershell
    $env:PYTHONPATH = "$PWD\python;$env:PYTHONPATH"
    ```

=== "Linux / macOS (Bash)"
    ```bash
    export PYTHONPATH="$PWD/python:$PYTHONPATH"
    ```

---

## ✅ Verifying Your Installation

### 1. Interactive Smoke Test

Open an interactive Python shell and verify that the module initializes and loads the underlying native hardware backend:

```python
import VelocityEngine as ve

print(f"Engine Version: {ve.__version__}")
print(f"Math Primitives: Vec3={ve.Vec3(1, 2, 3)}, Quat={ve.Quat()}")

# Verify App & Scene instantiation
app = ve.App(title="Smoke Test", width=320, height=240)
print(f"Active Scene: {app.scene}")
print("Velocity 3D Engine initialized successfully!")
```

Expected output:
```text
Engine Version: 0.2.0-beta
Math Primitives: Vec3=Vec3(1.00, 2.00, 3.00), Quat=Quat(1.00, 0.00, 0.00, 0.00)
Active Scene: <Scene at 0x...>
Velocity 3D Engine initialized successfully!
```

### 2. Running Automated Pytest Suites

Velocity 3D Engine includes over 420 automated unit, integration, and stress tests. Execute the test suite to ensure 100% operational health:

```bash
pytest tests/ -q
```

Expected result:
```text
....................................................................... [ 16%]
....................................................................... [ 33%]
....................................................................... [ 50%]
....................................................................... [ 67%]
....................................................................... [ 84%]
....................................................................    [100%]
424 passed in 4.12s
```

---

## ⚙️ Advanced CMake Configuration Options

When customizing the build via `cmake -B build` or through `pyproject.toml`, you can pass the following CMake definitions:

| CMake Definition | Default | Values | Description |
| :--- | :--- | :--- | :--- |
| `CMAKE_BUILD_TYPE` | `Release` | `Debug`, `Release`, `RelWithDebInfo` | Sets C++ compiler optimization levels and debug symbols. |
| `CMAKE_CXX_STANDARD` | `20` | `20`, `23` | C++ standard version required (minimum C++20). |
| `Python_EXECUTABLE` | System | Path to `python.exe` | Explicitly targets a specific Python interpreter. |
| `SOKOL_D3D11` | Auto (Win32) | Defined on Windows | Activates Direct3D 11 graphics pipeline. |
| `SOKOL_GLCORE` | Auto (Linux) | Defined on Linux | Activates OpenGL 3.3+ Core profile graphics pipeline. |
| `SOKOL_METAL` | Auto (Apple) | Defined on macOS | Activates Apple Metal graphics pipeline. |

Example command building in `RelWithDebInfo` mode with verbose output:

```bash
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=RelWithDebInfo -DCMAKE_VERBOSE_MAKEFILE=ON
cmake --build build -j
```

---

## 🛠️ Common Installation Issues

### Issue 1: "No CMAKE_CXX_COMPILER could be found"
* **Cause**: On Windows, CMake cannot find `cl.exe` because Visual Studio 2022 C++ build tools are not installed or your terminal was not launched with MSVC environment variables.
* **Fix**:
    1. Open the **Visual Studio Installer** and ensure **Desktop development with C++** is installed.
    2. Open your terminal from the **x64 Native Tools Command Prompt for VS 2022**, or execute:
       ```cmd
       "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"
       ```

### Issue 2: "fatal error C1128: number of sections exceeded object file format limit"
* **Cause**: Complex C++20 template instantiations in nanobind bindings can exceed standard COFF 65,536 section limits.
* **Fix**: The repository's `CMakeLists.txt` automatically includes `/bigobj` and `/MP` for MSVC. If invoking custom compiler commands manually, always append the `/bigobj` flag.

### Issue 3: Missing X11 or OpenGL headers on Linux (`GL/gl.h: No such file`)
* **Cause**: Linux distributions do not bundle development header packages by default.
* **Fix**: Run `sudo apt-get install libgl1-mesa-dev libx11-dev libxcursor-dev` on Debian/Ubuntu, or `sudo dnf install mesa-libGL-devel libX11-devel` on Fedora.

For more in-depth solutions to runtime and graphics backend issues, visit the **[Troubleshooting Guide](troubleshooting.md)**.
