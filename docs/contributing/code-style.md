# Code Style & Conventions

To maintain a clean, readable, and consistent codebase, all contributors must adhere to the style conventions detailed in this guide.

---

## C++20 Coding Standards

### 1. General Principles
- **Modern C++20 Standard**: Utilize modern language features including concepts, designated initializers, `std::span`, `std::string_view`, structured bindings, and `<ranges>`.
- **Strict RAII (Resource Acquisition Is Initialization)**: Never use raw `malloc`/`free` or manual pointer allocations without an explicit owning wrapper. GPU handles, textures, and audio streams must be managed by smart pointers or RAII handle classes.
- **Ownership Semantics**:
  - Exclusive ownership: `std::unique_ptr<T>`
  - Shared hierarchy nodes: `std::shared_ptr<T>`
  - Non-owning observer references: `T*`, `const T&`, or `std::weak_ptr<T>` (to break cyclic graph references).

---

### 2. Naming Conventions

| Entity | Style | Example | Notes |
|:---|:---|:---|:---|
| **Classes & Structs** | `PascalCase` | `StandardMaterial`, `EngineApp` | Nouns or noun phrases |
| **Methods & Functions** | `snake_case` | `set_position()`, `load_model()` | Verbs or verb phrases |
| **Member Variables** | `snake_case_` | `position_`, `is_running_` | Always include a trailing underscore |
| **Local Variables** | `snake_case` | `delta_time`, `target_matrix` | Clear, concise names |
| **Constants & Enums** | `PascalCase` / `SCREAMING_SNAKE` | `SideMode::Front`, `MAX_LIGHTS` | Scoped `enum class` preferred |
| **Namespaces** | `snake_case` | `engine`, `engine::math` | Single words preferred |
| **Template Parameters** | `PascalCase` | `typename T`, `typename VertexType` | Single capital letter or descriptive |

---

### 3. Header Organization & Includes
Every header file in `core/include/engine/` must start with `#pragma once`.

Include orders should follow:
1. Primary matching header (if implementing in `.cpp`)
2. Standard C++ library headers (`<vector>`, `<memory>`, `<string>`, `<cmath>`)
3. Third-party library headers (`<glm/glm.hpp>`, `sokol_gfx.h`, `imgui.h`)
4. Internal engine headers (`"engine/node3d.hpp"`, `"engine/material.hpp"`)

```cpp
#pragma once

#include <vector>
#include <memory>
#include <string>

#include <glm/glm.hpp>
#include "sokol_gfx.h"

#include "engine/node3d.hpp"
#include "engine/material.hpp"

namespace engine {

class SkinnedMesh : public Entity {
public:
    SkinnedMesh(std::shared_ptr<Mesh> mesh, std::shared_ptr<Material> mat);
    virtual ~SkinnedMesh() = default;

    void bind(std::shared_ptr<Skeleton> skeleton, const glm::mat4& bind_matrix);
    void compute_cpu_skinning();

private:
    std::shared_ptr<Skeleton> skeleton_{nullptr};
    glm::mat4 bind_matrix_{1.0f};
};

} // namespace engine
```

---

## Python Coding Standards

### 1. General Principles
- **PEP 8 Compliance**: Code must pass `flake8` without errors.
- **Line Length**: Soft limit of 100 characters.
- **Type Annotations**: All public functions, methods, and class attributes must provide full PEP-484 / PEP-561 type hints.

---

### 2. Naming Conventions

| Entity | Style | Example |
|:---|:---|:---|
| **Classes** | `PascalCase` | `FirstPersonController`, `OrbitController` |
| **Functions & Methods** | `snake_case` | `create_sphere()`, `on_update()` |
| **Variables & Attributes** | `snake_case` | `move_speed`, `is_grounded` |
| **Constants** | `SCREAMING_SNAKE_CASE` | `WARM_WHITE`, `DEFAULT_FOV` |
| **Private Members** | `_leading_underscore` | `self._core`, `self._update_callback` |

---

### 3. Avoiding Circular Reference Leaks
When binding Python instance methods to C++ callback hooks, **never create strong circular reference loops**. Always use `weakref`:

```python
import weakref

# CORRECT: Using weakref to prevent memory leaks
weak_self = weakref.ref(self)

def _proxy_update(dt: float) -> None:
    s = weak_self()
    if s is not None:
        s._on_frame(dt)

self._core.set_update_callback(_proxy_update)
```

---

### 4. Type Stub (`.pyi`) Maintenance
Whenever a new C++ class, method, or property is exported via `nanobind` in `bindings/`, you **must** update the corresponding type stubs:
- `python/VelocityEngine/__init__.pyi`
- `python/VelocityEngine/_VelocityEngine_core.pyi`

This guarantees that IDEs (VS Code Pylance, PyCharm, Neovim) provide immediate auto-completion, parameter hints, and static type validation for developers using VelocityEngine.
