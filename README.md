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
│   │   ├── mesh.hpp          # Класс Mesh и структура Vertex (position, normal, color)
│   │   ├── entity.hpp        # Класс Entity / Node (Transform, Mesh, Color, Visibility)
│   │   ├── scene.hpp         # Контейнер Scene для сущностей и освещения
│   │   ├── input.hpp         # InputManager и перечисление клавиш Key
│   │   └── app.hpp           # Класс EngineApp и окно
│   └── src/
│       ├── mesh.cpp          # Создание буферов геометрии (куб с нормалями)
│       ├── scene.cpp         # Управление сущностями и ленивая привязка мешей
│       ├── input.cpp         # Менеджер клавиатуры и мыши
│       ├── app.cpp           # Шейдеры освещения Blinn-Phong, цикл сцены и обработка ввода
│       └── sokol_impl.cpp    # Трансляционный юнит реализаций Sokol
├── bindings/                 # Связующий слой Nanobind
│   └── bindings.cpp          # Экспорт C++ классов в Python-модуль _engine_core
├── python/                   # Высокоуровневый пакет Python
│   └── engine/
│       ├── __init__.py       # Экспорт фасада App, Key, Transform, Camera, Scene, Entity и т.д.
│       ├── app.py            # Фасад App со свойствами scene, camera, input
│       └── py.typed          # Маркер типизации PEP 561
├── third_party/              # Внешние зависимости
│   ├── sokol/                # sokol_app.h, sokol_gfx.h, sokol_glue.h, sokol_log.h
│   └── glm/                  # Заголовочная библиотека OpenGL Mathematics
└── examples/                 # Примеры и тесты
    ├── 01_window.py          # Milestone 1: Базовое окно с заливкой фона (#1a1a24)
    ├── 02_rotating_cube.py   # Milestone 2: 3D вращающийся куб с Z-буфером и on_update(dt)
    └── 03_scene_lighting.py  # Milestone 3: Граф сцены, множественные сущности, Blinn-Phong и ввод
```

---

## Архитектура Milestone 3

1. **Граф сцены и сущности (`Scene`, `Entity`, `Transform`):**
   - Вынос геометрии и материалов в отдельные объекты `Entity`.
   - `Transform`: независимые координаты `position`, углы поворота `rotation` (в градусах), масштаб `scale`, матрицы `model_matrix()` и `normal_matrix()`.
   - Сцена `Scene`: обход сущностей с динамической отрисовкой `sg_draw` под собственной матрицей MVP.
   - Метод `app.scene.create_cube(color=(r, g, b, a))` для быстрого спавна примитивов.

2. **Освещение Blinn-Phong и нормали вершин:**
   - 24 вершины куба дополнены нормалями для каждой из 6 граней.
   - Нормали трансформируются через матрицу нормалей $\left(M^{-1}\right)^T$ (`normal_matrix`), сохраняя ортогональность при неравномерном масштабировании.
   - Шейдер реализует модель Blinn-Phong:
     - Направленный источник света `DirectionalLight` (вектор направления, интенсивность, диффузный цвет).
     - Фоновая составляющая `ambient` для предотвращения абсолютно черных теней.
     - Зеркальные блики (Specular) по вектору полупути $H = \text{normalize}(L + V)$.

3. **Камера (`Camera`):**
   - Управление положением `position`, точкой направления `target`, вектором `up`.
   - Методы навигации: `move_forward(dist)`, `move_right(dist)`, `move_up(dist)`.
   - Автоматический расчет матриц View и Perspective Projection.

4. **Система ввода (`InputManager` & `Key`):**
   - Перехват событий клавиатуры и мыши через `sokol_app`.
   - Методы `is_key_down(Key.W)`, `is_key_pressed(Key.SPACE)`, `is_key_released(...)`.
   - Отслеживание положения курсора `mouse_x`, `mouse_y` и относительного смещения `mouse_dx`, `mouse_dy`.

---

## Сборка и установка

```bash
# Установка в текущее venv окружение в режиме редактирования:
pip install -e . --no-build-isolation
```

---

## Запуск примеров

### 1. Интерактивная сцена с освещением и управлением (Milestone 3)
```bash
python examples/03_scene_lighting.py
```
**Управление:**
- `W / S`: Перемещение камеры вперед / назад
- `A / D`: Перемещение камеры влево / вправо
- `Стрелки ВВЕРХ / ВНИЗ`: Перемещение красного куба по вертикали
- `Стрелки ВЛЕВО / ВПРАВО`: Перемещение красного куба по горизонтали
- `ESC`: Выход из приложения
