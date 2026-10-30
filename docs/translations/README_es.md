# Velocity 3D Engine

[ [English](../../README.md) | [Русский](README_ru.md) | [中文](README_zh.md) | **Español** | [Français](README_fr.md) | [العربية](README_ar.md) | [Deutsch](README_de.md) | [日本語](README_ja.md) | [Português](README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../../LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)](#project-status)

<a id="project-status"></a>
> [!WARNING]
> ### ⚠️ Estado del proyecto: Alfa temprana / En desarrollo (WIP)
> Este motor se encuentra actualmente en una fase **alfa experimental temprana**. Es una prueba de concepto arquitectónica activa y una base técnica. Muchos subsistemas están experimentando una intensa iteración, las API están sujetas a cambios incompatibles, y se prevén importantes modernizaciones, refactorizaciones y optimizaciones. **Aún no está listo para producción.** Sin embargo, se ha establecido una base central sólida y funcional (C++20, Sokol GFX, nanobind, PBR, animación esquelética y suite completa de pruebas).

---

## 🌐 Documentación y traducciones

La documentación de Velocity 3D Engine está disponible en los idiomas oficiales de la ONU y los principales idiomas globales:

| Language | Document | Language | Document |
|:---|:---|:---|:---|
| 🇬🇧 **English** | [README.md](../../README.md) *(Original)* | 🇸🇦 **العربية** | [README_ar.md](README_ar.md) |
| 🇷🇺 **Русский** | [README_ru.md](README_ru.md) | 🇩🇪 **Deutsch** | [README_de.md](README_de.md) |
| 🇨🇳 **简体中文** | [README_zh.md](README_zh.md) | 🇯🇵 **日本語** | [README_ja.md](README_ja.md) |
| 🇪🇸 **Español** | [README_es.md](README_es.md) | 🇧🇷 **Português** | [README_pt.md](README_pt.md) |
| 🇫🇷 **Français** | [README_fr.md](README_fr.md) | | |

---

## 🌟 Características destacadas

**Velocity 3D Engine** combina el rendimiento de renderizado en bruto del moderno C++20 y [Sokol GFX](https://github.com/floooh/sokol) con la expresividad ergonómica de Python a través de [nanobind](https://github.com/wjakob/nanobind).

- **Núcleo de alto rendimiento**: Escrito en C++20 moderno con abstracciones ligeras de cero sobrecarga, matemáticas GLM y Sokol GFX (Direct3D 11, Metal, OpenGL).
- **Ergonomía pythónica**: Enlaces (bindings) de Python completos con stubs de tipos `.pyi` compatibles con PEP-484 / PEP-561 para autocompletado en IDEs. Admite sobrecarga de operadores, gestores de contexto y desempaquetado de vectores.
- **Renderizado basado en la física (PBR)**: Flujo de trabajo metálico-rugosidad (especular de microfacetas Cook-Torrance GGX, difusión Lambertiana, mapeo de normales Sobel, oclusión ambiental y mapas emisivos).
- **Sistema de animación esquelética**: Cargador esquelético glTF 2.0 con propagación de jerarquía articular, matrices de pose inversa (inverse bind matrices), skinning por mezcla lineal en CPU y mezcla de animaciones multi-clip.
- **Canal de postprocesamiento**: `EffectComposer` modular compatible con postprocesamiento multipase: Bloom gaussiano HDR, mapeo tonal (tonemapping) ACES/Reinhard, viñeteado y pases de sombreadores personalizados a pantalla completa en GLSL/HLSL.
- **Renderizado instanciado**: Pipeline de `InstancedMesh` de alto rendimiento capaz de renderizar decenas de miles de instancias dinámicas (p. ej., campos de asteroides, bosques) con matrices de transformación 4x4 individuales y colores de tinte por instancia.
- **Cola de superposición y HUD 2D**: Cola de renderizado 2D ortográfico integrada con atlas de fuentes de mapa de bits incorporado para estadísticas de depuración en pantalla, indicadores de salud y puntos de mira.
- **Audio espacial**: Motor de audio integrado impulsado por `miniaudio` para efectos de sonido, atenuación espacial 3D y ambiente de fondo.
- **Cobertura de pruebas 100% automatizada**: Conjunto completo de más de 420 pruebas unitarias, de integración y de estrés automatizadas que verifican la seguridad de la memoria, los ciclos de vida de los identificadores (handles) y las operaciones matemáticas de renderizado.

---

## 🎮 Demos jugables incluidas

El repositorio incluye dos juegos de demostración completos e independientes en el directorio [`games/`](../../games/) que demuestran las capacidades del motor:

### 1. Dungeon Crawler (`games/dungeon_crawler.py`)
Un RPG de acción en tercera persona ambientado en una oscura cripta subterránea:
- **Personaje animado del jugador**: Modelo de caballero animado glTF completo con jerarquía ósea y animaciones de locomoción.
- **Armamento modular**: Espada ancha modelada en 3D personalizada con guarda dorada, pomo y vaina de cuero sujeta a la cadera.
- **Materiales PBR procedimentales**: Paredes de sillería de alta resolución, suelos de losas con mapeo de normales y cofres del tesoro de roble oscuro reforzados con hierro.
- **HUD de RPG**: Barras de vida y resistencia en tiempo real, contadores de oro, llaves y reliquias recogidas, y tarjeta de minimapa.
- **Audio y ambiente**: Banda sonora atmosférica de mazmorra, efectos de pasos, sonidos de interacción con cofres e iluminación por llamas de antorchas.

```powershell
python games/dungeon_crawler.py
```

### 2. Space Combat Arena (`games/space_combat_arena.py`)
Una simulación de combate de vuelo espacial 6DOF de alta velocidad:
- **Modelo de vuelo de caza espacial**: Física inercial de 6 grados de libertad con cabeceo (pitch), guiñada (yaw), alabeo (roll) y aceleración por propulsores.
- **Cinturón de asteroides**: Campo de asteroides instanciado generado procedimentalmente con diversas escalas y rotaciones renderizado mediante `InstancedMesh`.
- **Entorno cósmico**: Skybox de nebulosa del espacio profundo, propulsores de partículas volumétricas y física de proyectiles láser.
- **Aviónica de cabina**: HUD de vuelo de ciencia ficción con velocímetro, indicador de condensador de impulso, monitores de casco y escudo, y seguimiento por radar 2D.

```powershell
python games/space_combat_arena.py
```

---

## 📂 Estructura del repositorio

```text
velocity-3d-engine/
├── assets/                     # Modelos glTF/GLB 3D, texturas y mapas de normales
│   ├── textures/               # Mapas de texturas PBR difusas, de normales y RGBA
│   ├── Soldier.glb             # Modelo de personaje animado y con rig
│   └── DamagedHelmet.glb       # Modelo de prueba PBR de referencia glTF
├── bindings/                   # Enlaces nanobind C++ -> Python
│   ├── bindings.cpp            # Punto de entrada principal del módulo
│   ├── bind_app.cpp            # Ciclo de vida de la aplicación y gestión de ventanas
│   ├── bind_geometry.cpp       # Mallas, curvas, puntos, geometría instanciada
│   ├── bind_materials.cpp      # Materiales PBR, unlit y de sombreadores personalizados
│   ├── bind_math.cpp           # Vec2/3/4, Quat, Euler, Mat3/4, Ray, Frustum
│   ├── bind_postprocess.cpp    # EffectComposer y pases de postprocesamiento
│   └── bind_scene.cpp          # Scene, Entity, Node3D, luces, cámaras
├── core/                       # Implementación del núcleo del motor en C++20
│   ├── include/engine/         # Archivos de cabecera públicos
│   └── src/                    # Archivos fuente del motor
├── examples/                   # 13 ejemplos educativos orientados a características
│   ├── 01_hello_pbr.py         # Configuración básica de esfera PBR
│   ├── 02_dynamic_lights_bloom.py # Luces puntuales dinámicas y pase de bloom
│   ├── 03_skeletal_character.py # Carga de animación esquelética glTF
│   ├── 04_numpy_wave_surface.py # Deformación procedimental de mallas vía NumPy
│   ├── 05_custom_shader_water.py # Pase de sombreador personalizado a pantalla completa
│   ├── 06_render_to_texture_portal.py # Objetivos de renderizado y renderizado de portales
│   ├── 07_particles_and_sprites.py # Sistemas de partículas y sprites 3D billboard
│   ├── 08_instanced_forest.py  # Renderizado instanciado de alta densidad
│   └── ...                     # Muestras interactivas adicionales
├── games/                      # Juegos independientes jugables (Dungeon & Space)
├── python/                     # Implementaciones del paquete Python y stubs de tipos
│   ├── VelocityEngine/         # Paquete principal del motor
│   ├── velocity/               # Alias pythónico en minúsculas
│   └── pielosyty/              # Capa de alias para compatibilidad retrospectiva
├── scripts/                    # Utilidades y herramientas de generación de texturas procedimentales
├── tests/                      # Más de 420 suites de pruebas automatizadas con pytest
├── third_party/                # Dependencias integradas (Sokol, GLM, ImGui, miniaudio)
├── CMakeLists.txt              # Sistema de compilación principal de CMake
└── pyproject.toml              # Configuración de empaquetado de Python con scikit-build-core
```

---

## 🛠️ Compilación e instalación

### Requisitos previos

- **CMake**: `>= 3.24`
- **Compilador C++20**:
  - Windows: MSVC 2022 (v143) o Clang-CL
  - Linux: GCC `>= 12` o Clang `>= 15`
  - macOS: Apple Clang `>= 14`
- **Python**: `>= 3.10`
- **Herramienta de compilación**: Ninja (recomendado) o MSBuild

### 1. Compilar e instalar a través de Python (Modo editable)

```powershell
# Clonar el repositorio
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# Instalar dependencias de compilación
pip install scikit-build-core nanobind ninja pytest numpy

# Compilar el núcleo de C++ e instalar los bindings de Python
pip install -e . --no-build-isolation
```

### 2. Compilar mediante CMake directamente

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. Ejecutar pruebas automatizadas

```powershell
pytest tests -q
```

---

## 💡 Ejemplo de inicio rápido

```python
import VelocityEngine as ve

# 1. Inicializar la aplicación
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. Configurar la cámara
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. Añadir iluminación direccional y ambiental
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. Crear material PBR y malla
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. Ejecutar el bucle de la aplicación
app.run()
```

---

## 🗺️ Hoja de ruta y limitaciones conocidas

Al ser una fase alfa temprana, se han planificado varias mejoras arquitectónicas clave:

- [ ] **GPU Compute Skinning**: Migrar del actual skinning por mezcla lineal en CPU a la evaluación en vertex shaders / compute shaders de la GPU para grandes cantidades de mallas esqueléticas.
- [ ] **Cascaded Shadow Maps (CSM)**: Soporte para cascadas direccionales de múltiples frustums para escenas exteriores de mundo abierto.
- [ ] **Compilación cruzada de sombreadores**: Formalizar la traducción automatizada sin conexión (offline) de GLSL/HLSL/MSL mediante `sokol-shdc`.
- [ ] **Integración de motor de física**: Integrar Jolt Physics o PhysX para simulación de cuerpos rígidos y respuesta de colisiones.
- [ ] **Backends Vulkan y WebGPU**: Añadir objetivos Vulkan y WebAssembly/WebGPU utilizando Sokol GFX.

---

## 📄 Licencia

Este proyecto está bajo la [Licencia MIT](../../LICENSE).
Las bibliotecas de terceros en [`third_party/`](../../third_party/) están sujetas a sus respectivas licencias de código abierto (Sokol: zlib/libpng, GLM: Happy Bunny / MIT, ImGui: MIT, miniaudio: Dominio Público / MIT-0).
