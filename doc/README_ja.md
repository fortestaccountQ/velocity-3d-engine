# Velocity 3D Engine

[ [English](../README.md) | [Русский](README_ru.md) | [中文](README_zh.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | [Deutsch](README_de.md) | [日本語](README_ja.md) | [Português](README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)]()

> [!WARNING]
> ### ⚠️ プロジェクトステータス：初期アルファ版 / 開発中 (Work-in-Progress)
> 本エンジンは現在、**初期の実験的アルファ版**段階にあります。活発なアーキテクチャの概念実証および技術基盤として開発されています。多くのサブシステムが精力的なイテレーションの途上にあり、API には破壊的変更が生じる可能性があり、大幅な近代化、リファクタリング、および最適化が計画されています。**現時点ではプロダクション対応（実運用向け）ではありません。** ただし、堅牢なコア基盤（C++20、Sokol GFX、nanobind、PBR、スキニングアニメーション、および完全なテストスイート）はすでに確立され、正常に機能しています。

---

## 🌟 主な特徴

**Velocity 3D Engine** は、モダン C++20 と [Sokol GFX](https://github.com/floooh/sokol) による圧倒的なレンダリングパフォーマンスに、[nanobind](https://github.com/wjakob/nanobind) を介した Python のエルゴノミックな表現力を融合させています。

- **高性能コア (High-Performance Core)**: モダン C++20 で記述され、軽量なゼロオーバーヘッド抽象化、GLM 数学ライブラリ、および Sokol GFX (Direct3D 11、Metal、OpenGL) を採用。
- **Pythonic なエルゴノミクス (Pythonic Ergonomics)**: IDE の自動補完に対応する PEP-484 / PEP-561 `.pyi` 型スタブを備えた完全な Python バインディング。演算子オーバーロード、コンテキストマネージャー、ベクトルアンパックをサポート。
- **物理ベースレンダリング (PBR)**: メタリック・ラフネスワークフロー (Cook-Torrance GGX 微小面鏡面反射、ランバート拡散反射、Sobel 法線マッピング、アンビエントオクルージョン、およびエミッシブマップ)。
- **スキニングアニメーションシステム (Skeletal Animation System)**: 関節階層の伝播、逆バインド行列、CPU リニアブレンドスキニング、マルチクリップアニメーションブレンディングに対応した glTF 2.0 スケルトンローダー。
- **ポストプロセスパイプライン (Post-Processing Pipeline)**: マルチパス・ポストプロセスをサポートするモジュール式 `EffectComposer`: HDR ガウスブルーム (Gaussian Bloom)、ACES/Reinhard トーンマッピング、周辺減光 (vignette)、およびカスタム GLSL/HLSL フルスクリーンシェーダーパス。
- **インスタンスレンダリング (Instanced Rendering)**: 個別の 4x4 変換行列とインスタンスカラーティントを備えた数万単位の動的インスタンス（小惑星群や森林など）を描画可能な高スループット `InstancedMesh` パイプライン。
- **2D HUD & オーバーレイキュー (2D HUD & Overlay Queue)**: 画面上のデバッグ統計、ヘルスゲージ、照準器用のビットマップフォントアトラスを内蔵した直交 2D レンダリングキューを統合。
- **空間オーディオ (Spatial Audio)**: 効果音、3D 空間減衰、環境音のための `miniaudio` を採用した統合オーディオエンジン。
- **100% 自動テストカバレッジ (100% Automated Test Coverage)**: メモリ安全性、ハンドルライフサイクル、およびレンダリング計算を検証する 420 以上のユニット・統合・ストレステストからなる包括的な自動テストスイート。

---

## 🎮 収録プレイアブルデモ

本リポジトリの [`games/`](../games/) ディレクトリには、エンジンの機能を実証する 2 つの完全なスタンドアロンデモゲームが含まれています：

### 1. ダンジョンクローラー (`games/dungeon_crawler.py`)
薄暗い地下墓地を舞台にした三人称アクション RPG：
- **アニメーション対応プレイヤーキャラクター**: ボーン階層とロコモーションアニメーションを備えた完全な glTF ナイトモデル。
- **モジュラー武器**: 金色の鍔、柄頭、腰に帯びた革の鞘を備えたカスタム 3D モデルのブロードソード。
- **プロシージャル PBR マテリアル**: 高解像度の切石積み壁、法線マップが適用された敷石の床、黒オークと鉄バンドの宝箱。
- **RPG HUD**: リアルタイムの体力・スタミナバー、獲得ゴールド、鍵、レリックのカウンター、およびミニマップカード。
- **オーディオ & 環境音**: 雰囲気豊かなダンジョンサウンドトラック、足音キュー、宝箱のインタラクション音、松明の炎のライティング。

```powershell
python games/dungeon_crawler.py
```

### 2. スペースコンバットアリーナ (`games/space_combat_arena.py`)
ハイスピードな 6 自由度 (6DOF) 宇宙戦闘フライトシミュレーション：
- **スターファイター飛行モデル**: ピッチ、ヨー、ロール、ブースター加速を備えた 6 自由度慣性物理。
- **小惑星帯**: `InstancedMesh` によって描画される、多様なスケールと回転を持つプロシージャル生成されたインスタンス化小惑星群。
- **宇宙環境**: 深宇宙の星雲スカイボックス、ボリュメトリック粒子スラスター、レーザー弾の物理挙動。
- **コックピットアビオニクス**: 速度計、ブーストキャパシタゲージ、船体およびシールドモニター、2D レーダートラッキングを備えた SF フライト HUD。

```powershell
python games/space_combat_arena.py
```

---

## 📂 リポジトリ構成

```text
velocity-3d-engine/
├── assets/                     # 3D glTF/GLB モデル、テクスチャ、法線マップ
│   ├── textures/               # PBR ディフューズ、法線、RGBA テクスチャマップ
│   ├── Soldier.glb             # リグ付きアニメーションキャラクターモデル
│   └── DamagedHelmet.glb       # リファレンス glTF PBR テストモデル
├── bindings/                   # nanobind C++ -> Python バインディング
│   ├── bindings.cpp            # プライマリモジュールエントリポイント
│   ├── bind_app.cpp            # アプリケーションライフサイクルおよびウィンドウ管理
│   ├── bind_geometry.cpp       # メッシュ、曲線、点、インスタンス化ジオメトリ
│   ├── bind_materials.cpp      # PBR、Unlit、カスタムシェーダーマテリアル
│   ├── bind_math.cpp           # Vec2/3/4、Quat、Euler、Mat3/4、Ray、Frustum
│   ├── bind_postprocess.cpp    # EffectComposer およびポストプロセスパス
│   └── bind_scene.cpp          # Scene、Entity、Node3D、ライト、カメラ
├── core/                       # コア C++20 エンジン実装
│   ├── include/engine/         # パブリックヘッダーファイル
│   └── src/                    # エンジンソースファイル
├── examples/                   # 13 個の機能特化型学習サンプル
│   ├── 01_hello_pbr.py         # 基本的な PBR スフィアのセットアップ
│   ├── 02_dynamic_lights_bloom.py # 動的点光源とブルームパス
│   ├── 03_skeletal_character.py # glTF スキニングアニメーション読み込み
│   ├── 04_numpy_wave_surface.py # NumPy によるプロシージャルメッシュ変形
│   ├── 05_custom_shader_water.py # カスタムフルスクリーンシェーダーパス
│   ├── 06_render_to_texture_portal.py # レンダーターゲットとポータルレンダリング
│   ├── 07_particles_and_sprites.py # パーティクルシステムと 3D ビルボードスプライト
│   ├── 08_instanced_forest.py  # 高密度インスタンスレンダリング
│   └── ...                     # その他のインタラクティブなデモ
├── games/                      # プレイ可能なスタンドアロンゲーム（ダンジョン & 宇宙）
├── python/                     # Python パッケージ実装 & 型スタブ
│   ├── VelocityEngine/         # メインエンジンパッケージ
│   ├── velocity/               # Pythonic な小文字エイリアス
│   └── pielosyty/              # 後方互換性エイリアスレイヤー
├── scripts/                    # ユーティリティ & プロシージャルテクスチャ生成ツール
├── tests/                      # 420 以上の自動 pytest テストスイート
├── third_party/                # ベンダー依存関係 (Sokol, GLM, ImGui, miniaudio)
├── CMakeLists.txt              # メイン CMake ビルドシステム
└── pyproject.toml              # Scikit-build-core Python パッケージング設定
```

---

## 🛠️ ビルドとインストール

### 前提条件

- **CMake**: `>= 3.24`
- **C++20 コンパイラ**:
  - Windows: MSVC 2022 (v143) または Clang-CL
  - Linux: GCC `>= 12` または Clang `>= 15`
  - macOS: Apple Clang `>= 14`
- **Python**: `>= 3.10`
- **ビルドツール**: Ninja (推奨) または MSBuild

### 1. Python 経由でのビルドとインストール（編集可能モード）

```powershell
# リポジトリのクローン
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# ビルド依存関係のインストール
pip install scikit-build-core nanobind ninja pytest numpy

# C++ コアのコンパイルと Python バインディングのインストール
pip install -e . --no-build-isolation
```

### 2. CMake による直接ビルド

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. 自動テストの実行

```powershell
pytest tests -q
```

---

## 💡 クイックスタート例

```python
import VelocityEngine as ve

# 1. アプリケーションの初期化
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. カメラのセットアップ
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. ディレクショナルライトと環境光の追加
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. PBR マテリアルとメッシュの作成
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. アプリケーションループの実行
app.run()
```

---

## 🗺️ ロードマップと既知の制限事項

初期アルファ版のため、いくつかの重要なアーキテクチャ上の改善が計画されています：

- [ ] **GPU コンピュートスキニング (GPU Compute Skinning)**: 大量のスケルトンメッシュに対応するため、現在の CPU リニアブレンドスキニングから GPU 頂点シェーダー / コンピュートシェーダー評価へ移行。
- [ ] **カスケードシャドウマップ (CSM)**: オープンワールドの屋外シーン向けにマルチ錐台ディレクショナルカスケードをサポート。
- [ ] **シェーダークロスコンパイル (Shader Cross-Compilation)**: `sokol-shdc` による自動化されたオフライン GLSL/HLSL/MSL 変換を正式導入。
- [ ] **物理エンジンの統合 (Physics Engine Integration)**: 剛体シミュレーションと衝突応答のために Jolt Physics または PhysX を統合。
- [ ] **Vulkan & WebGPU バックエンド (Vulkan & WebGPU Backends)**: Sokol GFX を使用した Vulkan および WebAssembly/WebGPU ターゲットを追加。

---

## 📄 ライセンス

本プロジェクトは [MIT ライセンス](../LICENSE) の下で公開されています。
[`third_party/`](../third_party/) 内のサードパーティ製ライブラリは、それぞれのオープンソースライセンスに準拠します (Sokol: zlib/libpng、GLM: Happy Bunny / MIT、ImGui: MIT、miniaudio: Public Domain / MIT-0)。
