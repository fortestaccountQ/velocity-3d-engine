# Velocity 3D Engine

[ [English](../../README.md) | [Русский](README_ru.md) | [中文](README_zh.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | **Deutsch** | [日本語](README_ja.md) | [Português](README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../../LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)](#project-status)

<a id="project-status"></a>
> [!WARNING]
> ### ⚠️ Projektstatus: Frühe Alpha / In Entwicklung (Work-in-Progress)
> Diese Engine befindet sich derzeit in einer **frühen experimentellen Alpha-Phase**. Sie dient als aktiver architektonischer Machbarkeitsnachweis (Proof-of-Concept) und technisches Fundament. Viele Subsysteme durchlaufen intensive Iterationen, APIs unterliegen bahnbrechenden Änderungen (Breaking Changes), und bedeutende Modernisierungen, Refaktorierungen sowie Optimierungen sind geplant. **Sie ist noch nicht einsatzbereit für die Produktion.** Dennoch ist ein solides Kernfundament (C++20, Sokol GFX, nanobind, PBR, Skelettanimation und eine vollständige Testsuite) etabliert und funktionsfähig.

---

## 🌐 Dokumentation & Übersetzungen

Die Dokumentation der Velocity 3D Engine ist in den offiziellen UN-Sprachen und wichtigen Weltsprachen verfügbar:

| Language | Document | Language | Document |
|:---|:---|:---|:---|
| 🇬🇧 **English** | [README.md](../../README.md) *(Original)* | 🇸🇦 **العربية** | [README_ar.md](README_ar.md) |
| 🇷🇺 **Русский** | [README_ru.md](README_ru.md) | 🇩🇪 **Deutsch** | [README_de.md](README_de.md) |
| 🇨🇳 **简体中文** | [README_zh.md](README_zh.md) | 🇯🇵 **日本語** | [README_ja.md](README_ja.md) |
| 🇪🇸 **Español** | [README_es.md](README_es.md) | 🇧🇷 **Português** | [README_pt.md](README_pt.md) |
| 🇫🇷 **Français** | [README_fr.md](README_fr.md) | | |

---

## 🌟 Highlights

**Velocity 3D Engine** kombiniert die unverfälschte Rendering-Leistung von modernem C++20 und [Sokol GFX](https://github.com/floooh/sokol) mit der ergonomischen Ausdruckskraft von Python über [nanobind](https://github.com/wjakob/nanobind).

- **Hochleistungskern**: Geschrieben in modernem C++20 mit leichtgewichtigen Zero-Overhead-Abstraktionen, GLM-Mathematik und Sokol GFX (Direct3D 11, Metal, OpenGL).
- **Pythonische Ergonomie**: Vollständige Python-Bindings mit PEP-484 / PEP-561 `.pyi`-Typstubs für IDE-Autovervollständigung. Unterstützt Operatorüberladung, Kontextmanager und Vektorentpackung (Unpacking).
- **Physikbasiertes Rendering (PBR)**: Metallic-Roughness-Workflow (Cook-Torrance GGX-Mikrofacetten-Glanzlicht, Lambertianische diffuse Streuung, Sobel-Normal-Mapping, Ambient Occlusion und Emissive-Maps).
- **Skelettanimationssystem**: glTF 2.0-Skelett-Loader mit Bone-Hierarchie-Propagation, inversen Bind-Matrizen, CPU-Linear-Blend-Skinning und Multi-Clip-Animationsblending.
- **Post-Processing-Pipeline**: Modularer `EffectComposer` mit Unterstützung für Multi-Pass-Post-Processing: HDR-Gaußscher Bloom, ACES/Reinhard-Tonemapping, Vignette und benutzerdefinierte GLSL/HLSL-Vollbild-Shader-Pässe.
- **Instanziertes Rendering**: Hochdurchsatz-`InstancedMesh`-Pipeline zur Darstellung von zehntausenden dynamischen Instanzen (z. B. Asteroidenfelder, Wälder) mit individuellen 4x4-Transformationsmatrizen und Instanz-Farbtönungen (Tint Colors).
- **2D-HUD & Overlay-Queue**: Integrierte orthografische 2D-Rendering-Queue mit integriertem Bitmap-Font-Atlas für On-Screen-Debug-Statistiken, Lebensanzeigen und Fadenkreuze.
- **Raumklang (Spatial Audio)**: Integrierte Audio-Engine auf Basis von `miniaudio` für Soundeffekte, räumliche 3D-Dämpfung und Hintergrundambiente.
- **100 % automatisierte Testabdeckung**: Umfassende Suite von über 420 automatisierten Unit-, Integrations- und Stresstests zur Verifizierung von Speichersicherheit, Handle-Lebenszyklen und Rendering-Mathematik.

---

## 🎮 Enthaltene spielbare Demos

Das Repository enthält zwei vollständige, eigenständige Demo-Spiele im Verzeichnis [`games/`](../../games/), die die Fähigkeiten der Engine demonstrieren:

### 1. Dungeon Crawler (`games/dungeon_crawler.py`)
Ein Third-Person-Action-RPG in einer dunklen unterirdischen Krypta:
- **Animierter Spielercharakter**: Vollständiges animiertes glTF-Rittermodell mit Knochenhierarchie und Fortbewegungsanimationen.
- **Modulare Bewaffnung**: Benutzerdefiniertes 3D-modelliertes Breitschwert mit vergoldeter Parierstange, Knauf und an der Hüfte befestigter Lederscheide.
- **Prozedurale PBR-Materialien**: Hochauflösende Quadersteinwände, normal-gemappte Steinplattenböden und eisenbeschlagene Schatztruhen aus dunkler Eiche.
- **RPG-HUD**: Echtzeit-Lebens- und Ausdauerbalken, Zähler für gesammeltes Gold, Schlüssel und Relikte sowie Minikarten-Overlay.
- **Audio & Atmosphäre**: Atmosphärischer Dungeon-Soundtrack, Schrittgeräusche, Interaktionssounds für Truhen und dynamisches Fackellicht.

```powershell
python games/dungeon_crawler.py
```

### 2. Space Combat Arena (`games/space_combat_arena.py`)
Eine rasante 6DOF-Weltraumkampfsimulation:
- **Sternenjäger-Flugmodell**: Trägheitsphysik mit 6 Freiheitsgraden (6DOF), Nick-, Gier-, Rollbewegungen und Booster-Beschleunigung.
- **Asteroidengürtel**: Prozedural generiertes instanziiertes Asteroidenfeld mit verschiedenen Skalierungen und Rotationen, gerendert über `InstancedMesh`.
- **Kosmische Umgebung**: Deep-Space-Nebel-Skybox, volumetrische Partikelschubdüsen und Laserprojektilphysik.
- **Cockpit-Avionik**: Sci-Fi-Flug-HUD mit Geschwindigkeitsmesser, Boost-Kondensatoranzeige, Hüllen- und Schildmonitoren sowie 2D-Radarerfassung.

```powershell
python games/space_combat_arena.py
```

---

## 📂 Repository-Struktur

```text
velocity-3d-engine/
├── assets/                     # 3D glTF/GLB-Modelle, Texturen und Normal-Maps
│   ├── textures/               # PBR-Diffuse-, Normal- und RGBA-Textur-Maps
│   ├── Soldier.glb             # Animiertes geriggtes Charaktermodell
│   └── DamagedHelmet.glb       # Referenz-glTF-PBR-Testmodell
├── bindings/                   # nanobind C++ -> Python Bindings
│   ├── bindings.cpp            # Primärer Moduleinstiegspunkt
│   ├── bind_app.cpp            # Anwendungslebenszyklus und Fensterverwaltung
│   ├── bind_geometry.cpp       # Meshes, Kurven, Punkte, instanziierte Geometrie
│   ├── bind_materials.cpp      # PBR-, Unlit- und benutzerdefinierte Shader-Materialien
│   ├── bind_math.cpp           # Vec2/3/4, Quat, Euler, Mat3/4, Ray, Frustum
│   ├── bind_postprocess.cpp    # EffectComposer und Post-Processing-Pässe
│   └── bind_scene.cpp          # Scene, Entity, Node3D, Lichtquellen, Kameras
├── core/                       # Kernimplementierung der Engine in C++20
│   ├── include/engine/         # Öffentliche Header-Dateien
│   └── src/                    # Engine-Quelldateien
├── examples/                   # 13 funktionsfokussierte Anschauungsbeispiele
│   ├── 01_hello_pbr.py         # Grundlegendes PBR-Kugel-Setup
│   ├── 02_dynamic_lights_bloom.py # Dynamische Punktlichter und Bloom-Pass
│   ├── 03_skeletal_character.py # Laden von glTF-Skelettanimationen
│   ├── 04_numpy_wave_surface.py # Prozedurale Mesh-Deformation via NumPy
│   ├── 05_custom_shader_water.py # Benutzerdefinierter Vollbild-Shader-Pass
│   ├── 06_render_to_texture_portal.py # Render-Targets und Portal-Rendering
│   ├── 07_particles_and_sprites.py # Partikelsysteme und 3D-Billboard-Sprites
│   ├── 08_instanced_forest.py  # Hochdichtes instanziiertes Rendering
│   └── ...                     # Weitere interaktive Demos
├── games/                      # Spielbare eigenständige Spiele (Dungeon & Space)
├── python/                     # Python-Paketimplementierungen & Typ-Stubs
│   ├── VelocityEngine/         # Primäres Engine-Paket
│   ├── velocity/               # Pythonischer Alias in Kleinbuchstaben
│   └── pielosyty/              # Abwärtskompatibilitäts-Aliasschicht
├── scripts/                    # Hilfswerkzeuge und Tools zur prozeduralen Texturgenerierung
├── tests/                      # 420+ automatisierte pytest-Test-Suiten
├── third_party/                # Eingebundene Abhängigkeiten (Sokol, GLM, ImGui, miniaudio)
├── CMakeLists.txt              # Primäres CMake-Build-System
└── pyproject.toml              # Scikit-build-core Python-Paketierungskonfiguration
```

---

## 🛠️ Erstellung & Installation

### Voraussetzungen

- **CMake**: `>= 3.24`
- **C++20-Compiler**:
  - Windows: MSVC 2022 (v143) oder Clang-CL
  - Linux: GCC `>= 12` oder Clang `>= 15`
  - macOS: Apple Clang `>= 14`
- **Python**: `>= 3.10`
- **Build-Tool**: Ninja (empfohlen) oder MSBuild

### 1. Erstellen und Installieren über Python (Editable-Modus)

```powershell
# Repository klonen
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# Build-Abhängigkeiten installieren
pip install scikit-build-core nanobind ninja pytest numpy

# C++-Kern kompilieren und Python-Bindings installieren
pip install -e . --no-build-isolation
```

### 2. Direkt über CMake erstellen

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. Automatisierte Tests ausführen

```powershell
pytest tests -q
```

---

## 💡 Schnellstart-Beispiel

```python
import VelocityEngine as ve

# 1. Anwendung initialisieren
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. Kamera einrichten
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. Direktionales & Umgebungslicht hinzufügen
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. PBR-Material & Mesh erstellen
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. Anwendungsschleife ausführen
app.run()
```

---

## 🗺️ Roadmap & Bekannte Einschränkungen

Als frühe Alpha sind mehrere wichtige architektonische Verbesserungen geplant:

- [ ] **GPU Compute Skinning**: Umstellung vom derzeitigen CPU-Linear-Blend-Skinning auf GPU-Vertex-Shader- / Compute-Shader-Berechnung für hohe Anzahlen von Skelett-Meshes.
- [ ] **Kaskadierte Schattenkarten (CSM)**: Unterstützung von direktionalen Mehrfach-Frustum-Kaskaden für Open-World-Außenszenen.
- [ ] **Shader-Kreuzkompilierung**: Formalisierung der automatisierten Offline-Übersetzung von GLSL/HLSL/MSL via `sokol-shdc`.
- [ ] **Physik-Engine-Integration**: Integration von Jolt Physics oder PhysX für Starrkörpersimulation und Kollisionsreaktion.
- [ ] **Vulkan- & WebGPU-Backends**: Hinzufügen von Vulkan- und WebAssembly/WebGPU-Zielen unter Verwendung von Sokol GFX.

---

## 📄 Lizenz

Dieses Projekt ist unter der [MIT-Lizenz](../../LICENSE) lizenziert.
Drittanbieter-Bibliotheken in [`third_party/`](../../third_party/) unterliegen ihren jeweiligen Open-Source-Lizenzen (Sokol: zlib/libpng, GLM: Happy Bunny / MIT, ImGui: MIT, miniaudio: Public Domain / MIT-0).
