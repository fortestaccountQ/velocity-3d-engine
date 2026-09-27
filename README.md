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
│   │   └── app.hpp           # Класс EngineApp, структуры Vertex, WindowConfig, математика GLM
│   └── src/
│       ├── app.cpp           # 3D пайплайн, шейдеры, Z-буфер, расчет MVP и цикл событий
│       └── sokol_impl.cpp    # Трансляционный юнит реализаций Sokol
├── bindings/                 # Связующий слой Nanobind
│   └── bindings.cpp          # Экспорт C++ класса в Python-модуль _engine_core
├── python/                   # Высокоуровневый пакет Python
│   └── engine/
│       ├── __init__.py       # Экспорт фасада engine.App
│       ├── app.py            # Фасад App, декоратор @app.on_update, фасад TransformFacade
│       └── py.typed          # Маркер типизации PEP 561
├── third_party/              # Внешние зависимости
│   ├── sokol/                # sokol_app.h, sokol_gfx.h, sokol_glue.h, sokol_log.h
│   └── glm/                  # Заголовочная библиотека OpenGL Mathematics
└── examples/                 # Примеры и тесты
    ├── 01_window.py          # Milestone 1: Базовое окно с заливкой фона темно-синим цветом (#1a1a24)
    └── 02_rotating_cube.py   # Milestone 2: 3D вращающийся куб с Z-буфером и Python-колбэком on_update(dt)
```

---

## Возможности Milestone 2

1. **Математическая библиотека GLM (C++20):**
   - Вычисление матриц проекции (`glm::perspective`), вида (`glm::lookAt`) и модели (`glm::translate`, `glm::rotate`, `glm::scale`) для формирования матрицы MVP на каждом кадре.
   - Автоматическая адаптация aspect ratio при изменении размеров окна.

2. **Графический 3D-конвейер Sokol GFX:**
   - Кроссплатформенная шейдерная программа (HLSL для Direct3D 11, GLSL 330 для OpenGL Core, GLSL 300 es для WebGL2/GLES3, MSL для Metal).
   - Включение аппаратного буфера глубины (Z-буфер):
     - `depth.compare = SG_COMPAREFUNC_LESS_EQUAL`
     - `depth.write_enabled = true`
     - Очистка `pass.action.depth.load_action = SG_LOADACTION_CLEAR` со значением `1.0f`.
   - VBO и EBO для 3D-куба: 24 вершины с уникальными цветами граней и 36 индексов.

3. **Двусторонний мост кадров (Python Callbacks & GIL):**
   - Расчет дельты времени (`dt`) с субмиллисекундной точностью через `std::chrono::steady_clock`.
   - Безопасный захват Python GIL (`nanobind::gil_scoped_acquire`) при вызове Python-функции из кадрового цикла C++.
   - Удобный декоратор `@app.on_update` и метод `app.set_update_callback(fn)`.
   - Автоматическая очистка ссылок в блоке `finally` для предотвращения циклических утечек памяти.

4. **Управление трансформациями из Python:**
   - Прямой доступ к свойствам вращения: `app.rotation_x`, `app.rotation_y`, `app.rotation_z`.
   - Прямой доступ к координатам: `app.position_x`, `app.position_y`, `app.position_z`.
   - Фасад `app.transform` с методами `set_rotation()`, `set_position()`, `set_scale()`.

---

## Сборка и установка

### 1. Требования
- Python 3.10+
- CMake 3.24+
- Компилятор C++20: MSVC (Visual Studio 2022 / Build Tools) на Windows, GCC 11+ / Clang 13+ на Linux, Xcode/AppleClang на macOS.
- Пакеты Python: `pip install nanobind scikit-build-core ninja cmake`

### 2. Сборка через pip (Рекомендуемый способ)
```bash
# Установка в текущее окружение (в режиме редактирования)
pip install -e . --no-build-isolation

# Или обычная установка:
pip install . --no-build-isolation
```

### 3. Прямая сборка через CMake
#### Windows (MSVC):
```cmd
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

#### Linux:
```bash
sudo apt-get install libx11-dev libxi-dev libxcursor-dev libgl1-mesa-dev
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
```

---

## Запуск примеров

### Milestone 1: Базовое окно
```bash
python examples/01_window.py
```

### Milestone 2: 3D вращающийся куб с Z-буфером
```bash
python examples/02_rotating_cube.py
```

Код скрипта:
```python
import engine

app = engine.App(title="3D Rotating Cube", width=800, height=600)


@app.on_update
def update(dt: float):
  # Непрерывное вращение куба по осям X и Y
  app.rotation_x += 45.0 * dt
  app.rotation_y += 60.0 * dt


app.run()
```
Куб непрерывно вращается, грани корректно перекрывают друг друга благодаря аппаратному Z-буферу, а частота кадров и дельта времени обрабатываются в Python без задержек. Для выхода нажмите клавишу **ESC** или закройте окно.
