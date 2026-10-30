# Velocity 3D Engine

[ [English](../README.md) | [Русский](README_ru.md) | [中文](README_zh.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | [Deutsch](README_de.md) | [日本語](README_ja.md) | [Português](README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)]()

> [!WARNING]
> ### ⚠️ 项目状态：早期 Alpha / 进行中 (Work-in-Progress)
> 本引擎目前处于**早期实验性 Alpha** 阶段。它是活跃的架构概念验证和技术基石。许多子系统正在经历密集迭代，API 可能会发生破坏性变更，并且计划进行重大现代化、重构与性能优化。**目前尚不适用于生产环境。** 然而，坚实的核心基础（C++20、Sokol GFX、nanobind、PBR、骨骼动画以及完整的测试套件）已建立并具备完整功能。

---

## 🌟 特性亮点

**Velocity 3D Engine** 结合了现代 C++20 与 [Sokol GFX](https://github.com/floooh/sokol) 的纯粹渲染性能，以及通过 [nanobind](https://github.com/wjakob/nanobind) 带来的 Python 人体工程学表现力。

- **高性能核心 (High-Performance Core)**: 基于现代 C++20 编写，具备轻量级零开销抽象、GLM 数学库与 Sokol GFX（Direct3D 11、Metal、OpenGL）。
- **Pythonic 人体工程学 (Pythonic Ergonomics)**: 具备完整的 Python 绑定，提供用于 IDE 自动补全的 PEP-484 / PEP-561 `.pyi` 类型存根。支持运算符重载、上下文管理器以及向量解包。
- **基于物理的渲染 (PBR)**: 金属-粗糙度工作流（Cook-Torrance GGX 微表面镜面反射、朗伯漫反射、Sobel 法线贴图、环境光遮蔽及自发光贴图）。
- **骨骼动画系统 (Skeletal Animation System)**: glTF 2.0 骨骼加载器，支持关节层级传播、逆绑定矩阵、CPU 线性混合蒙皮 (Linear Blend Skinning) 以及多动画片段混合。
- **后处理管线 (Post-Processing Pipeline)**: 模块化 `EffectComposer`，支持多通道后处理：HDR 高斯泛光 (Gaussian Bloom)、ACES/Reinhard 色调映射、暗角 (vignette) 以及自定义 GLSL/HLSL 全屏着色器通道。
- **实例化渲染 (Instanced Rendering)**: 高吞吐量的 `InstancedMesh` 管线，能够渲染数万个动态实例（例如小行星带、森林），并支持独立的 4x4 变换矩阵与实例色调 (tint colors)。
- **2D HUD 与叠加队列 (2D HUD & Overlay Queue)**: 集成正交 2D 渲染队列，内置用于屏幕调试统计、生命条和准星的位图字体图集。
- **空间音频 (Spatial Audio)**: 集成由 `miniaudio` 驱动的音频引擎，用于音效、3D 空间衰减与环境背景声。
- **100% 自动化测试覆盖率 (100% Automated Test Coverage)**: 包含 420+ 个自动化单元测试、集成测试与压力测试的全面套件，验证内存安全、句柄生命周期以及渲染数学计算。

---

## 🎮 内置可玩演示

本仓库在 [`games/`](../games/) 目录中包含了两个独立的完整演示游戏，用于展示本引擎的各项能力：

### 1. 地牢探险 (`games/dungeon_crawler.py`)
设定在黑暗地下墓穴中的第三人称动作 RPG：
- **动画角色模型**: 完整的 glTF 动画骑士模型，带有骨骼层级与移动动画。
- **模块化武器装备**: 自定义 3D 建模的阔剑，带有镀金护手、剑柄圆头，以及佩戴在腰部的皮革剑鞘。
- **程序化 PBR 材质**: 高分辨率琢石砌体墙面、法线贴图石板地面以及深色橡木包铁宝箱。
- **RPG HUD**: 实时生命值与耐力条、金币收集、钥匙、圣物计数器以及小地图卡片。
- **音频与环境氛围**: 大气磅礴的地牢原声配乐、脚步声提示、宝箱互动音效以及火把火焰光照。

```powershell
python games/dungeon_crawler.py
```

### 2. 太空战斗竞技场 (`games/space_combat_arena.py`)
高速 6 自由度 (6DOF) 太空飞行战斗模拟：
- **星际战机飞行模型**: 6 自由度惯性物理，支持俯仰 (pitch)、偏航 (yaw)、滚转 (roll) 以及推进器加速。
- **小行星带**: 通过 `InstancedMesh` 渲染的程序化生成实例化小行星场，具备多样化的尺度与旋转。
- **宇宙环境**: 深空星云天空盒、体积粒子推进器以及激光射弹物理。
- **座舱航电设备**: 科幻飞行 HUD，配备速度计、推进电容仪表、舰体与护盾监视器以及 2D 雷达追踪。

```powershell
python games/space_combat_arena.py
```

---

## 📂 仓库结构

```text
velocity-3d-engine/
├── assets/                     # 3D glTF/GLB 模型、纹理与法线贴图
│   ├── textures/               # PBR 漫反射、法线和 RGBA 纹理贴图
│   ├── Soldier.glb             # 带绑定的骨骼动画角色模型
│   └── DamagedHelmet.glb       # 参考 glTF PBR 测试模型
├── bindings/                   # nanobind C++ -> Python 绑定
│   ├── bindings.cpp            # 主模块入口
│   ├── bind_app.cpp            # 应用程序生命周期与窗口管理
│   ├── bind_geometry.cpp       # 网格、曲线、点、实例化几何体
│   ├── bind_materials.cpp      # PBR、无光照 (unlit) 与自定义着色器材质
│   ├── bind_math.cpp           # Vec2/3/4、Quat、Euler、Mat3/4、Ray、Frustum
│   ├── bind_postprocess.cpp    # EffectComposer 与后处理通道
│   └── bind_scene.cpp          # Scene、Entity、Node3D、光源、相机
├── core/                       # 核心 C++20 引擎实现
│   ├── include/engine/         # 公共头文件
│   └── src/                    # 引擎源文件
├── examples/                   # 13 个聚焦功能的教学示例
│   ├── 01_hello_pbr.py         # 基础 PBR 球体设置
│   ├── 02_dynamic_lights_bloom.py # 动态点光源与 Bloom 泛光通道
│   ├── 03_skeletal_character.py # glTF 骨骼动画加载
│   ├── 04_numpy_wave_surface.py # 通过 NumPy 进行程序化网格形变
│   ├── 05_custom_shader_water.py # 自定义全屏着色器通道
│   ├── 06_render_to_texture_portal.py # 渲染目标与传送门渲染
│   ├── 07_particles_and_sprites.py # 粒子系统与 3D 公告板精灵
│   ├── 08_instanced_forest.py  # 高密度实例化渲染
│   └── ...                     # 更多交互式展示示例
├── games/                      # 可玩的独立游戏（地牢探险与太空战斗）
├── python/                     # Python 软件包实现与类型存根
│   ├── VelocityEngine/         # 主引擎包
│   ├── velocity/               # Pythonic 小写别名
│   └── pielosyty/              # 向后兼容别名层
├── scripts/                    # 实用工具与程序化纹理生成工具
├── tests/                      # 420+ 个自动化 pytest 测试套件
├── third_party/                # 第三方依赖库 (Sokol, GLM, ImGui, miniaudio)
├── CMakeLists.txt              # 主 CMake 构建系统
└── pyproject.toml              # Scikit-build-core Python 打包配置
```

---

## 🛠️ 构建与安装

### 前置依赖

- **CMake**: `>= 3.24`
- **C++20 编译器**:
  - Windows: MSVC 2022 (v143) 或 Clang-CL
  - Linux: GCC `>= 12` 或 Clang `>= 15`
  - macOS: Apple Clang `>= 14`
- **Python**: `>= 3.10`
- **构建工具**: Ninja（推荐）或 MSBuild

### 1. 通过 Python 构建并安装（可编辑模式）

```powershell
# 克隆仓库
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# 安装构建依赖
pip install scikit-build-core nanobind ninja pytest numpy

# 编译 C++ 核心并安装 Python 绑定
pip install -e . --no-build-isolation
```

### 2. 直接通过 CMake 构建

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. 运行自动化测试

```powershell
pytest tests -q
```

---

## 💡 快速入门示例

```python
import VelocityEngine as ve

# 1. 初始化应用程序
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. 设置相机
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. 添加方向光与环境光
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. 创建 PBR 材质与网格
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. 运行应用程序循环
app.run()
```

---

## 🗺️ 路线图与已知限制

作为早期 Alpha 版本，计划进行多项关键架构改进：

- [ ] **GPU 计算蒙皮 (GPU Compute Skinning)**: 从当前的 CPU 线性混合蒙皮迁移至 GPU 顶点着色器 / 计算着色器求值，以支持高数量骨骼网格。
- [ ] **级联阴影贴图 (CSM)**: 支持用于开放世界室外场景的多视锥方向光级联阴影。
- [ ] **着色器跨平台编译 (Shader Cross-Compilation)**: 通过 `sokol-shdc` 实现自动化的离线 GLSL/HLSL/MSL 转换流程。
- [ ] **物理引擎集成 (Physics Engine Integration)**: 集成 Jolt Physics 或 PhysX 以支持刚体模拟与碰撞响应。
- [ ] **Vulkan 与 WebGPU 后端 (Vulkan & WebGPU Backends)**: 利用 Sokol GFX 增加 Vulkan 和 WebAssembly/WebGPU 支持目标。

---

## 📄 许可证

本项目基于 [MIT 许可证](../LICENSE) 开源。
[`third_party/`](../third_party/) 中的第三方库遵循其各自的开源许可证（Sokol: zlib/libpng，GLM: Happy Bunny / MIT，ImGui: MIT，miniaudio: Public Domain / MIT-0）。
