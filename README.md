# Modular 3D Engine (C++20 + Sokol + GLM + Nanobind + Python)

Модульный гибридный 3D-движок с высокопроизводительным ядром на C++20 и удобным Python-фасадом, спроектированный с учетом будущей компиляции под WebAssembly (Emscripten / Pyodide).

---

## Архитектура проекта

```
3d_render/
├── CMakeLists.txt            # Конфигурация мультиплатформенной сборки (Windows/Linux/macOS/Wasm)
├── pyproject.toml            # Метаданные пакета и интеграция scikit-build-core + nanobind
├── README.md                 # Документация архитектуры и инструкция
├── .gitignore                # Исключения временных и бинарных файлов
├── core/                     # Исходный код C++20 ядра
│   ├── include/engine/
│   │   ├── transform.hpp     # Класс Transform (position, rotation, scale, model_matrix, normal_matrix)
│   │   ├── camera.hpp        # Класс Camera (View, Projection, ViewProjection, управление положением)
│   │   ├── light.hpp         # Структура DirectionalLight (direction, color, ambient, intensity, shininess)
│   │   ├── texture.hpp       # Класс Texture (загрузка PNG/JPG/BMP через stb_image, GPU-текстуры, checkerboard)
│   │   ├── material.hpp      # Класс Material (albedo map, base color, roughness, metallic, uv_scale)
│   │   ├── mesh.hpp          # Класс Mesh и структура Vertex (position, normal, uv, color)
│   │   ├── entity.hpp        # Класс Entity / Node (Transform, Mesh, Material, Visibility)
│   │   ├── scene.hpp         # Контейнер Scene для сущностей, текстур и освещения
│   │   ├── input.hpp         # InputManager и перечисление клавиш Key
│   │   └── app.hpp           # Класс EngineApp и окно
│   └── src/
│       ├── texture.cpp       # Управление текстурами GPU (sg_image, sg_sampler, sg_view, stb_image)
│       ├── mesh.cpp          # Создание буферов геометрии (куб с UV, плоскость/пол Plane)
│       ├── scene.cpp         # Управление сущностями, материалами и ленивой привязкой мешей
│       ├── input.cpp         # Менеджер клавиатуры и мыши
│       ├── app.cpp           # Шейдеры PBR-lite, конвейер sokol_gfx, цикл сцены и обработка ввода
│       └── sokol_impl.cpp    # Трансляционный юнит реализаций Sokol
├── bindings/                 # Связующий слой Nanobind
│   └── bindings.cpp          # Экспорт C++ классов в Python-модуль _engine_core
├── python/                   # Высокоуровневый пакет Python
│   └── engine/
│       ├── __init__.py       # Экспорт фасада App, Texture, Material, Camera, Scene, Entity и т.д.
│       ├── app.py            # Фасад App со свойствами scene, camera, input, load_texture, create_checkerboard_texture
│       └── py.typed          # Маркер типизации PEP 561
├── third_party/              # Внешние зависимости
│   ├── sokol/                # sokol_app.h, sokol_gfx.h, sokol_glue.h, sokol_log.h
│   ├── glm/                  # Заголовочная библиотека OpenGL Mathematics
│   └── stb/                  # stb_image.h (загрузка изображений PNG/JPG/BMP)
└── examples/                 # Примеры и тесты
    ├── 01_window.py          # Milestone 1: Базовое окно с заливкой фона (#1a1a24)
    ├── 02_rotating_cube.py   # Milestone 2: 3D вращающийся куб с Z-буфером и on_update(dt)
    ├── 03_scene_lighting.py  # Milestone 3: Граф сцены, множественные сущности, Blinn-Phong и ввод
    └── 04_textured_material.py # Milestone 4: Текстуры, материалы PBR Metallic-Roughness, пол и 3 куба
```

---

## Архитектура Milestone 4 (Textures, Materials & PBR Foundation)

1. **Текстурный конвейер (`Texture` & `stb_image`):**
   - Загрузка растровых изображений (PNG, JPG, BMP) из файлов через `stb_image.h` с преобразованием в 4-канальный RGBA8.
   - Создание GPU-объектов `sg_image` и `sg_sampler` с поддержкой линейной фильтрации (`SG_FILTER_LINEAR`) и режимов повторения (`SG_WRAP_REPEAT`).
   - Встроенный процедурный генератор текстуры «шахматная доска» (checkerboard) с настраиваемыми размерами сетки и палитрой, служащий надежным фоллбэком при отсутствии внешних текстур.

2. **Геометрия с UV-координатами и новые примитивы (`Mesh`):**
   - Расширение вершинной структуры `Vertex`: `position` (vec3), `normal` (vec3), `uv` (vec2), `color` (vec4).
   - Точные текстурные развертки $[0, 1]$ для всех 6 граней базового куба (24 вершины).
   - Фабрика плоскости `app.scene.create_plane(size=16.0, uv_tiling=8.0, material=...)` для полов и стен.

3. **Система материалов (`Material`):**
   - Связывает текстуру альбедо (`Texture`), базовый цвет (`base_color`), шероховатость (`roughness` $\in [0, 1]$), металличность (`metallic` $\in [0, 1]$) и масштаб UV (`uv_scale`).
   - Управление свойствами материала напрямую из Python-кода без перезагрузки конвейера.

4. **Физически-ориентированный конвейер (PBR-lite Metallic-Roughness):**
   - Мультиплатформенные шейдеры (Direct3D 11 HLSL, Metal MSL, GLSL / WebGL).
   - Модуляция диффузного цвета текстурой альбедо и базовым оттенком.
   - Аппроксимация Френеля (Schlick): $F_0$ интерполируется между диэлектриком (0.04) и цветом альбедо в зависимости от показателя металличности `metallic`.
   - Зеркальное отражение по модели Blinn-Phong/GGX-lite, регулируемое показателем шероховатости `roughness` и интенсивностью направленного источника.
   - Корректная интерполяция рассеянного света `ambient`.

---

## Сборка и установка

```bash
# Установка в текущее venv окружение в режиме редактирования:
pip install -e . --no-build-isolation
```

---

## Запуск примеров

### Текстуры и материалы PBR-lite (Milestone 4)
```bash
python examples/04_textured_material.py
```
**Сцена демонстрирует:**
- Текстурированную плоскость пола с процедурным тайлингом checkerboard.
- 3 куба с контрастными физическими материалами:
  - **Матовый красный** (`roughness=0.85, metallic=0.05`).
  - **Зеркальное золото** (`roughness=0.18, metallic=0.92`).
  - **Глянцевый изумруд** (`roughness=0.25, metallic=0.40`).
- Динамически вращающийся направленный свет, демонстрирующий зеркальные блики.
- Полный интерактивный полет камеры клавишами `W / S / A / D`.
