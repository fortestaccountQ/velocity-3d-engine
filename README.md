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
│   │   ├── physics.hpp       # Физические структуры AABB, Ray, RaycastHit
│   │   ├── model.hpp         # Класс Model (контейнер иерархии glTF с root_entity и дочерними мешами)
│   │   ├── model_loader.hpp  # Класс ModelLoader (парсинг glTF/GLB через cgltf и текстур через stb_image)
│   │   ├── entity.hpp        # Класс Entity / Node (Transform, Parent, local_matrix, world matrices, Mesh, Material)
│   │   ├── scene.hpp         # Контейнер Scene для сущностей, текстур, загрузки моделей, освещения и raycast
│   │   ├── input.hpp         # InputManager и перечисление клавиш Key
│   │   └── app.hpp           # Класс EngineApp, окно и захват курсора мыши
│   └── src/
│       ├── texture.cpp       # Управление текстурами GPU (sg_image, sg_sampler, sg_view, stb_image)
│       ├── mesh.cpp          # Создание буферов геометрии (куб с UV, плоскость/пол Plane)
│       ├── model_loader.cpp  # Реализация загрузки glTF 2.0 / GLB (cgltf + stb_image memory buffer)
│       ├── scene.cpp         # Управление сущностями, материалами, load_model и raycast
│       ├── input.cpp         # Менеджер клавиатуры, мыши и блокировка курсора
│       ├── app.cpp           # Шейдеры PBR-lite, конвейер sokol_gfx, цикл сцены и обработка ввода
│       └── sokol_impl.cpp    # Трансляционный юнит реализаций Sokol
├── bindings/                 # Связующий слой Nanobind
│   └── bindings.cpp          # Экспорт C++ классов в Python-модуль _engine_core
├── python/                   # Высокоуровневый пакет Python
│   └── engine/
│       ├── __init__.py       # Экспорт фасада App, Texture, Material, Camera, Scene, Entity, Model, Mesh, AABB, Ray, FirstPersonController
│       ├── app.py            # Фасад App со свойствами scene, camera, input, load_texture, set_mouse_locked
│       ├── controller.py     # Игровой контроллер от первого лица (FPS Controller, AABB коллизии, прыжок)
│       └── py.typed          # Маркер типизации PEP 561
├── third_party/              # Внешние зависимости
│   ├── sokol/                # sokol_app.h, sokol_gfx.h, sokol_glue.h, sokol_log.h
│   ├── glm/                  # Заголовочная библиотека OpenGL Mathematics
│   ├── stb/                  # stb_image.h (загрузка растровых изображений из файлов и памяти)
│   └── cgltf/                # cgltf.h (single-header C99 парсер glTF 2.0 / GLB)
├── assets/                   # Тестовые 3D-модели
│   ├── duck.glb              # Модель утки (12.6k индексов, встроенная текстура 512x512)
│   ├── box_textured.glb      # Текстурированный куб с UV разверткой
│   └── avocado.glb           # Детализированная модель авокадо с PBR-сканом
├── examples/                 # Примеры и тесты
│   ├── 01_window.py          # Milestone 1: Базовое окно с заливкой фона (#1a1a24)
│   ├── 02_rotating_cube.py   # Milestone 2: 3D вращающийся куб с Z-буфером и on_update(dt)
│   ├── 03_scene_lighting.py  # Milestone 3: Граф сцены, множественные сущности, Blinn-Phong и ввод
│   ├── 04_textured_material.py # Milestone 4: Текстуры, материалы PBR Metallic-Roughness, пол и 3 куба
│   ├── 05_load_model.py      # Milestone 5: Загрузка glTF 2.0 / GLB с иерархией, текстурами и анимацией
│   └── 06_playable_demo.py   # Milestone 6: Интерактивная 3D-игра от первого лица с коллизиями и Raycast
├── game_main.py              # Автономная точка входа для сборки в бинарный дистрибутив
└── package_game.py           # Скрипт сборки автономного .exe дистрибутива через PyInstaller

---

## Архитектура Milestone 5 (glTF 2.0 / GLB Model Loading)

1. **Интеграция C99-парсера `cgltf`:**
   - Высокопроизводительный однозаголовочный парсер `cgltf.h` без сторонних зависимостей.
   - Поддержка форматов `.gltf` (JSON + внешние бинарные буферы и текстуры) и `.glb` (монолитные бинарные контейнеры со встроенным чанком данных).

2. **Загрузчик геометрии и материалов (`ModelLoader`):**
   - **Атрибуты вершин:** Чтение позиций (`POSITION`), нормалей (`NORMAL`), текстурных координат (`TEXCOORD_0`) и цветов вершин (`COLOR_0`). При отсутствии нормалей генерируется дефолтный вектор $(0, 1, 0)$.
   - **Индексы треугольников:** Поддержка 8-битных, 16-битных (`uint16_t`) и автоматическое преобразование безындексной геометрии.
   - **Встроенные текстуры GLB:** Декодирование изображений напрямую из памяти (`bufferView`) через `stbi_load_from_memory` в 4-канальный RGBA8 без записи временных файлов на диск.
   - **Факторы PBR Metallic-Roughness:** Извлечение параметров `baseColorFactor`, `roughnessFactor` и `metallicFactor` из встроенных определений материалов glTF.

3. **Иерархия узлов и граф сцены (`Model` & `Entity`):**
   - Узлы сцены glTF сохраняют взаимную иерархию через указатель `parent`.
   - Поддержка локальных матриц узлов glTF (`local_matrix`) и локальных пользовательских трансформаций (`transform`).
   - Расчет финальных мировых матриц: $M_{\text{world}} = M_{\text{parent}} \cdot (M_{\text{transform}} \cdot M_{\text{local}})$, а также матриц нормалей $\left(M_{\text{world}}^{-1}\right)^T$.
   - Корректная обработка вспомогательных/трансформационных узлов без привязанных мешей (пропуск рендеринга без лишних полигонов).
   - Класс `Model` предоставляет доступ к корневому `root_entity`, списку всех сгенерированных мешей `meshes`, и единому свойству `transform` для перемещения, масштабирования и вращения всей модели целиком.

4. **Python API:**
   ```python
   # Загрузка модели из glTF / GLB:
   model = app.scene.load_model("assets/duck.glb")
   model.transform.position = (0.0, 0.0, 0.0)
   model.transform.scale = (1.0, 1.0, 1.0)
   model.transform.rotation.y += 25.0 * dt
   ```

---

## Архитектура Milestone 6 (First-Person Controller, AABB Physics & Standalone Packaging)

1. **Захват мыши и свободный обзор (Mouse Capture & FPS Camera):**
   - Управление указателем мыши на уровне Sokol: `sapp_lock_mouse(true)` и `sapp_show_mouse(false)`.
   - Векторное вращение камеры Pitch (ограничение от -89° до +89°) и Yaw по смещениям мыши `mouse_dx` / `mouse_dy`.
   - Экспорт в Python: `app.set_mouse_locked(True)`, переключение курсора по клавише `TAB`.

2. **C++ Физический движок (AABB Collisions & Raycast):**
   - Структура `AABB`: расчет локального объема меша по вершинам (`Mesh::calculate_aabb()`), трансформация в мировой объем с учетом масштаба и поворота (`Entity::world_aabb()`).
   - Тестирование пересечений объемов методом разделяющих осей (`AABB::intersects()`).
   - Математика луча `Ray`: быстрый тест пересечения луча с AABB (`Ray::intersect_aabb()`).
   - Функция сцены `Scene::raycast(ray, max_distance)`: находит ближайший интерактивный объект и точную точку соударения `point`.

3. **Игровой контроллер игрока (`FirstPersonController`):**
   - Перемещение на `W/A/S/D` относительно горизонтальной проекции взгляда камеры.
   - Вертикальная гравитация и прыжок по `Space`.
   - Раздельное поосевое разрешение коллизий (позволяет скользить вдоль стен и стоять на препятствиях/полу).

4. **Автономная сборка в исполняемый дистрибутив (.exe):**
   - Скрипт `package_game.py` на базе PyInstaller упаковывает Python runtime, скомпилированный `.pyd` модуль движка, графические шейдеры и папку `assets/` в автономный каталог `dist/MyEngineGame/`.
   - Готовый исполняемый файл `dist/MyEngineGame/MyEngineGame.exe` запускается в Windows без установленного Python и сторонних библиотек.

---

## Сборка и установка

```bash
# Установка в текущее venv окружение в режиме редактирования:
pip install -e . --no-build-isolation

# Сборка автономного исполняемого файла игры (.exe):
python package_game.py
```

---

## Запуск примеров и игры

### Интерактивная 3D-игра от первого лица (Milestone 6)
```bash
# Запуск через Python:
python examples/06_playable_demo.py

# Или запуск собранного автономного бинарника:
.\dist\MyEngineGame\MyEngineGame.exe
```
**Управление:**
- **Мышь:** Свободный круговой обзор (курсор заблокирован).
- **W / A / S / D:** Перемещение игрока с проверкой коллизий со стенами и объектами.
- **Space:** Прыжок с физической гравитацией.
- **Left Shift:** Спринт (ускорение бега).
- **ЛКМ (Клик):** Raycast-взаимодействие с объектами сцены (подпрыгивание утки/коробки/авокадо и подсветка).
- **TAB:** Переключение захвата мыши.
- **ESC:** Выход из игры.

### Загрузка 3D-моделей glTF 2.0 / GLB (Milestone 5)
```bash
python examples/05_load_model.py
```
**Сцена демонстрирует:**
- **Центр:** Знаменитая утка `duck.glb` (12 636 индексов, встроенная текстура 512×512).
- **Слева:** Текстурированный куб `box_textured.glb` с разверткой UV.
- **Справа:** Высокополигональная фотограмметрическая модель авокадо `avocado.glb` с PBR-сканом.
- Текстурированную плоскость пола с перспективной сеткой.
- Вращающийся источник освещения и интерактивную камеру (W/S/A/D).

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
