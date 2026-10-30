# Hardware Instancing & Level of Detail (LOD)

Rendering complex virtual worlds featuring dense forests, asteroid belts, crowds, or debris requires minimizing GPU draw calls and eliminating redundant geometric processing. 

Velocity 3D Engine delivers two complementary acceleration systems:
1. **GPU Hardware Instancing (`InstancedMesh`)**: Renders tens of thousands of dynamic instances in a **single draw call** with per-instance 3D transforms and colors.
2. **Level of Detail (`LOD`) & View-Frustum Culling**: Dynamically substitutes high-poly meshes with simplified proxies based on distance, and culls objects entirely outside the camera frustum.

```mermaid
flowchart TD
    subgraph SceneManagement["Scene Graph & Camera"]
        Camera["Camera (Position & View-Projection Matrix)"]
        FrustumCull["Frustum Culler (6 Normalized Halfspace Planes)"]
        LODManager["LOD Controller (Distance Evaluation)"]
    end

    subgraph Geometry["Instanced & Dynamic Geometry"]
        IMesh["InstancedMesh (1 Base Mesh + N Instance Transforms)"]
        LODGroup["LOD Node (Tier 0 High / Tier 1 Med / Tier 2 Low)"]
    end

    subgraph GPUExecution["Sokol GFX Single-Pass Submission"]
        InstVBuf["Instance Buffer (SG_USAGE_STREAM / SG_VERTEXSTEP_PER_INSTANCE)\nMatrix 4x4 (64B) + Color RGBA (16B)"]
        DrawCall["Single Draw Call: sg_draw(0, num_indices, instance_count)"]
    end

    Camera -->|Extract 6 Planes| FrustumCull
    Camera -->|Distance d = ||P - C||| LODManager
    FrustumCull -->|AABB Intersection| LODGroup
    LODManager -->|Set Tier Visibility| LODGroup
    IMesh -->|Upload Instance Transforms| InstVBuf
    InstVBuf --> DrawCall
```

---

## 1. Hardware Instancing Pipeline

### 1.1 The Draw Call Bottleneck

In a traditional rendering pipeline, issuing a separate draw call for each of 50,000 trees requires:
- 50,000 CPU-to-GPU API state changes.
- 50,000 uniform buffer uploads for individual model matrices.
- Massive CPU driver overhead, degrading framerates below 10 FPS even on high-end GPUs.

**Hardware Instancing** solves this by storing the shared base geometry (vertices, normals, UVs, tangents) in static vertex/index buffers once, while storing per-instance variable attributes (position, rotation, scale, tint) in a contiguous secondary **Instance Buffer**.

```text
Static Mesh Buffer (Uploaded Once):
[ V0 ][ V1 ][ V2 ] ... [ Vn ] (Cube / Cylinder / Mesh Geometry)

Instance Buffer (Uploaded per Batch / Frame):
[ Instance 0: Mat4 (64B) | Color (16B) ] -> 80 bytes
[ Instance 1: Mat4 (64B) | Color (16B) ] -> 80 bytes
[ Instance 2: Mat4 (64B) | Color (16B) ] -> 80 bytes
...
[ Instance N: Mat4 (64B) | Color (16B) ] -> 80 bytes
```

### 1.2 GPU Vertex Layout & Memory Stride

In Velocity, `InstanceData` is packed into an 80-byte memory structure:

```cpp
struct InstanceData {
    glm::mat4 model_matrix{1.0f}; // 64 bytes (4 x vec4 columns)
    glm::vec4 color{1.0f};        // 16 bytes (RGBA float)
};
```

In the Sokol GFX pipeline layout, the instance attributes are declared with `step_func = SG_VERTEXSTEP_PER_INSTANCE`:

- `attrs[5]`: Model Matrix Column 0 (`SG_VERTEXFORMAT_FLOAT4`)
- `attrs[6]`: Model Matrix Column 1 (`SG_VERTEXFORMAT_FLOAT4`)
- `attrs[7]`: Model Matrix Column 2 (`SG_VERTEXFORMAT_FLOAT4`)
- `attrs[8]`: Model Matrix Column 3 (`SG_VERTEXFORMAT_FLOAT4`)
- `attrs[9]`: Instance Base Color (`SG_VERTEXFORMAT_FLOAT4`)

When `sg_draw(0, base_indices_count, instance_count)` executes, the GPU vertex shader processes all instances in parallel on hardware compute units, applying each instance's world matrix without CPU intervention.

---

## 2. Level of Detail (LOD) Architecture

### 2.1 Geometric Simplification & Distance Evaluation

Objects far from the camera subtend only a few pixels on the screen. Rendering a 20,000-polygon model at a distance of 150 meters wastes rasterization and geometry shading bandwidth without visual improvement.

The `LOD` system organizes multiple child `Node3D` representations sorted ascending by threshold distance:

$$\text{Tier}(d) = \max \left\{ i \;\middle|\; d \ge \text{Tier}_i.\text{distance} \right\}$$

```text
Distance from Camera:
0m                     30m                       80m                     250m
|-----------------------|-------------------------|------------------------|
  Tier 0 (High-Poly)       Tier 1 (Medium-Poly)       Tier 2 (Low-Poly Proxy)
  3,840 Triangles          512 Triangles              48 Triangles
```

### 2.2 Smooth Switching & Hysteresis

When `lod.update_lod(camera_position)` is called, the Euclidean distance $d = \|\mathbf{P}_{\text{world}} - \mathbf{P}_{\text{camera}}\|$ is calculated:

```cpp
void LOD::update_lod(const glm::vec3& camera_position) {
    if (levels_.empty()) return;
    float dist = glm::distance(world_position(), camera_position);

    int best_index = 0;
    for (size_t i = 0; i < levels_.size(); ++i) {
        if (dist >= levels_[i].distance) {
            best_index = static_cast<int>(i);
        }
    }

    current_level_index_ = best_index;
    for (size_t i = 0; i < levels_.size(); ++i) {
        if (levels_[i].node) {
            levels_[i].node->visible = (static_cast<int>(i) == best_index);
        }
    }
}
```

Only the single active tier has its `visible` flag set to `true`. Inactive tiers are skipped during render traversal with zero GPU cost.

---

## 3. View-Frustum Culling Mathematics

### 3.1 Extracting the 6 Frustum Planes (Gribb-Hartmann Algorithm)

The camera's viewing frustum is a truncated pyramid bounded by 6 planes: **Left**, **Right**, **Bottom**, **Top**, **Near**, and **Far**.

Given the combined View-Projection matrix $\mathbf{M} = \mathbf{P} \cdot \mathbf{V}$:

$$\mathbf{M} = \begin{bmatrix}
m_{00} & m_{01} & m_{02} & m_{03} \\
m_{10} & m_{11} & m_{12} & m_{13} \\
m_{20} & m_{21} & m_{22} & m_{23} \\
m_{30} & m_{31} & m_{32} & m_{33}
\end{bmatrix}$$

Each plane equation $Ax + By + Cz + D = 0$ is extracted directly from the row combinations of $\mathbf{M}$:

| Plane | Unnormalized Normal $(A, B, C)$ | Unnormalized Constant $D$ |
| :--- | :--- | :--- |
| **Left** | $(m_{30} + m_{00},\; m_{31} + m_{01},\; m_{32} + m_{02})$ | $m_{33} + m_{03}$ |
| **Right** | $(m_{30} - m_{00},\; m_{31} - m_{01},\; m_{32} - m_{02})$ | $m_{33} - m_{03}$ |
| **Bottom** | $(m_{30} + m_{10},\; m_{31} + m_{11},\; m_{32} + m_{12})$ | $m_{33} + m_{13}$ |
| **Top** | $(m_{30} - m_{10},\; m_{31} - m_{11},\; m_{32} - m_{12})$ | $m_{33} - m_{13}$ |
| **Near** | $(m_{30} + m_{20},\; m_{31} + m_{21},\; m_{32} + m_{22})$ | $m_{33} + m_{23}$ |
| **Far** | $(m_{30} - m_{20},\; m_{31} - m_{21},\; m_{32} - m_{22})$ | $m_{33} - m_{23}$ |

Every plane is normalized by dividing by its normal vector magnitude:

$$\mathbf{n}' = \frac{\mathbf{n}}{\|\mathbf{n}\|}, \quad D' = \frac{D}{\|\mathbf{n}\|}$$

### 3.2 Axis-Aligned Bounding Box (AABB) Intersection

Testing all 8 corners of an AABB against 6 planes requires 48 plane-dot products. Velocity optimizes this test using the **P-vertex (Positive Vertex)** method, reducing the calculation to at most 6 dot products:

For each plane with normal $\mathbf{n} = (n_x, n_y, n_z)$ and AABB bounded by $[\mathbf{P}_{\text{min}}, \mathbf{P}_{\text{max}}]$, find the vertex $\mathbf{P}_{\text{pos}}$ that lies furthest in the positive direction of the plane normal:

$$P_{\text{pos}, x} = \begin{cases} P_{\text{max}, x} & \text{if } n_x \ge 0 \\ P_{\text{min}, x} & \text{if } n_x < 0 \end{cases}$$

$$P_{\text{pos}, y} = \begin{cases} P_{\text{max}, y} & \text{if } n_y \ge 0 \\ P_{\text{min}, y} & \text{if } n_y < 0 \end{cases}$$

$$P_{\text{pos}, z} = \begin{cases} P_{\text{max}, z} & \text{if } n_z \ge 0 \\ P_{\text{min}, z} & \text{if } n_z < 0 \end{cases}$$

If $\mathbf{n} \cdot \mathbf{P}_{\text{pos}} + D < 0$, the entire bounding box lies completely outside that plane's half-space and is **culled immediately**:

```cpp
bool Frustum::intersects_aabb(const glm::vec3& min_p, const glm::vec3& max_p) const {
    for (const auto& plane : planes) {
        glm::vec3 positive = min_p;
        if (plane.normal.x >= 0) positive.x = max_p.x;
        if (plane.normal.y >= 0) positive.y = max_p.y;
        if (plane.normal.z >= 0) positive.z = max_p.z;
        if (plane.distance_to_point(positive) < 0.0f) return false;
    }
    return true;
}
```

---

## 4. Core Engine Classes & Methods

### 4.1 InstancedMesh API

| Class / Method | Signature | Description |
| :--- | :--- | :--- |
| `InstancedMesh(mesh, count)` | `(mesh: Mesh, count: int = 0)` | Constructs an instanced mesh container referencing a base geometry and allocating instance slots. |
| `set_instance_count(count)` | `(count: int) -> None` | Resizes the internal instance array and prepares GPU stream buffers. |
| `instance_count()` / `.count` | `-> int` | Returns the number of allocated instances. |
| `set_instance_transform()` | `(idx, px, py, pz, rx=0, ry=0, rz=0, sx=1, sy=1, sz=1, color=(1,1,1,1))` | Convenience method computing translation, Euler rotation, scale matrix, and tint for an instance. |
| `set_instance(idx, matrix, color)` | `(idx: int, matrix: Mat4, color: tuple) -> None` | Explicitly assigns a 4x4 model matrix and RGBA color tuple to the designated instance. |
| `set_color_at(idx, color)` | `(idx: int, color: tuple) -> None` | Updates the tint color of an instance while preserving its existing model transform. |
| `set_matrix_at(idx, matrix)` | `(idx: int, matrix: Mat4) -> None` | Updates the 4x4 transform of an instance while preserving its color. |
| `ensure_gpu_buffers()` | `() -> bool` | Flushes CPU instance array data to the GPU `SG_USAGE_STREAM` instance buffer. |

### 4.2 LOD & Frustum API

| Class / Method | Signature | Description |
| :--- | :--- | :--- |
| `LOD(name)` | `(name: str = "LOD")` | Creates an LOD group node in the scene graph. |
| `add_level(node, distance)` | `(node: Node3D, distance: float) -> None` | Registers a child node to be displayed when camera distance exceeds or equals `distance`. |
| `update_lod(cam_pos)` | `(camera_position: Vec3 \| tuple) -> None` | Evaluates camera distance and toggles child node visibility. |
| `current_level_index()` | `-> int` | Returns the zero-based index of the currently active LOD tier. |
| `Frustum()` | `()` | Constructs a view-frustum container holding 6 bounding planes. |
| `set_from_projection_matrix(mat)` | `(matrix: Mat4) -> None` | Extracts normalized planes from a 4x4 View-Projection matrix. |
| `intersects_aabb(min_p, max_p)` | `(min: Vec3, max: Vec3) -> bool` | Fast P-vertex intersection test returning `True` if the AABB overlaps the frustum. |
| `intersects_sphere(center, radius)` | `(center: Vec3, radius: float) -> bool` | Fast sphere intersection test against the 6 frustum planes. |
| `app.stats` / `RenderStats` | `-> RenderStats` | Tracks per-frame metrics: `draw_calls`, `culled_objects`, `total_triangles`, `total_instances`. |

---

## 5. Runnable Code Examples

### 5.1 Massive 50,000-Instance Animated Forest

This self-contained script spawns 35,000 pine trees and 15,000 granite boulders rendered concurrently in **2 single draw calls** at 60+ FPS, featuring procedural color variation and camera flight.

```python
"""Velocity 3D Engine: 50,000 Instanced Forest with Orbit Flight."""

import random
import math
import VelocityEngine as ve


def main():
    app = ve.App(
        title="Velocity - 50,000 Hardware Instanced Forest",
        width=1280,
        height=720,
        clear_color=(0.10, 0.15, 0.22, 1.0),
    )

    # 1. Camera Setup
    camera = app.camera
    camera.set_position(0.0, 35.0, -90.0)
    camera.set_yaw_pitch(90.0, -22.0)

    # 2. Lighting
    scene = app.scene
    scene.set_sun(direction=(-0.6, -1.2, -0.5), color=ve.WARM_WHITE, intensity=1.5)

    # 3. Ground Terrain
    ground = scene.create_plane(size=300.0)
    ground_mat = ve.Material.plastic(roughness=0.9, color=(0.12, 0.22, 0.10))
    ground.material = ground_mat

    # 4. 35,000 Pine Trees via InstancedMesh (1 Draw Call)
    tree_mesh = ve.Mesh.create_cylinder(radius=0.6, height=4.5, segments=8)
    tree_inst = ve.InstancedMesh(tree_mesh, 35000)

    rng = random.Random(42)
    spread = 130.0

    print("Generating 35,000 Tree Instances...")
    for i in range(35000):
        tx = rng.uniform(-spread, spread)
        tz = rng.uniform(-spread, spread)
        scale_y = rng.uniform(0.7, 1.4)
        rot_y = rng.uniform(0.0, 360.0)

        # Procedural pine greens: deep forest to bright emerald
        r = rng.uniform(0.04, 0.15)
        g = rng.uniform(0.35, 0.75)
        b = rng.uniform(0.08, 0.20)

        tree_inst.set_instance_transform(
            i,
            px=tx, py=scale_y * 2.25, pz=tz,
            rx=0.0, ry=rot_y, rz=0.0,
            sx=1.0, sy=scale_y, sz=1.0,
            color=(r, g, b, 1.0)
        )

    scene.add_instanced_mesh(tree_inst)

    # 5. 15,000 Granite Rocks via InstancedMesh (1 Draw Call)
    rock_mesh = ve.Mesh.create_box(1.2, 0.8, 1.4)
    rock_inst = ve.InstancedMesh(rock_mesh, 15000)

    print("Generating 15,000 Rock Instances...")
    for i in range(15000):
        rx = rng.uniform(-spread, spread)
        rz = rng.uniform(-spread, spread)
        scale = rng.uniform(0.4, 1.2)
        rot_y = rng.uniform(0.0, 360.0)

        # Granite slate grey
        grey = rng.uniform(0.25, 0.55)
        rock_inst.set_instance_transform(
            i,
            px=rx, py=scale * 0.4, pz=rz,
            rx=rng.uniform(-10, 10), ry=rot_y, rz=rng.uniform(-10, 10),
            sx=scale, sy=scale, sz=scale,
            color=(grey, grey, grey * 0.95, 1.0)
        )

    scene.add_instanced_mesh(rock_inst)

    # 6. UI Overlay
    app.ui.draw_text("Velocity 3D Engine - 50,000 Hardware Instances", (20, 20), size=18, color=ve.WHITE)
    app.ui.draw_text("35,000 Trees + 15,000 Rocks rendered in 2 Draw Calls", (20, 48), size=14, color=ve.CYAN)
    app.ui.show_stats(True)

    flight_angle = 0.0

    def on_frame(dt: float):
        nonlocal flight_angle
        flight_angle += dt * 0.25

        # Fly cinematic circle over the forest
        cam_x = math.cos(flight_angle) * 95.0
        cam_z = math.sin(flight_angle) * 95.0
        camera.set_position(cam_x, 38.0, cam_z)
        camera.look_at((0.0, 5.0, 0.0))

    app.set_update_callback(on_frame)
    app.run()


if __name__ == "__main__":
    main()
```

### 5.2 Multi-Tier LOD Hero Asset Switching

This example demonstrates an interactive LOD entity that automatically toggles between High, Medium, and Low geometric tiers based on camera distance.

```python
"""Velocity 3D Engine: Multi-Tier Level of Detail (LOD) Showcase."""

import math
import VelocityEngine as ve


def main():
    app = ve.App(
        title="Velocity - Multi-Tier LOD System",
        width=1280,
        height=720,
        clear_color=(0.08, 0.12, 0.16, 1.0),
    )

    scene = app.scene
    scene.set_sun(direction=(0.5, -1.0, 0.5), color=ve.WHITE, intensity=1.5)

    # 1. Create Multi-Tier LOD Node
    lod = ve.LOD("HeroMonument_LOD")

    # Tier 0: High Detail (< 15 meters) - 64 segments
    high_node = scene.create_entity("LOD_High")
    high_node.mesh = ve.Mesh.create_cylinder(radius=1.5, height=8.0, segments=64)
    high_node.material = ve.Material.gold(roughness=0.15)

    # Tier 1: Medium Detail (15 - 45 meters) - 16 segments
    med_node = scene.create_entity("LOD_Med")
    med_node.mesh = ve.Mesh.create_cylinder(radius=1.5, height=8.0, segments=16)
    med_node.material = ve.Material.gold(roughness=0.35)

    # Tier 2: Low Detail (> 45 meters) - 6 segments
    low_node = scene.create_entity("LOD_Low")
    low_node.mesh = ve.Mesh.create_cylinder(radius=1.5, height=8.0, segments=6)
    low_node.material = ve.Material.gold(roughness=0.60)

    # Register distance thresholds (sorted ascending by distance)
    lod.add_level(high_node, distance=0.0)
    lod.add_level(med_node, distance=15.0)
    lod.add_level(low_node, distance=45.0)

    lod.transform.position = (0.0, 4.0, 0.0)
    scene.add(lod)

    # 2. Camera Dolly Animation
    camera = app.camera
    dolly_timer = 0.0

    tier_names = ["Tier 0: High Poly (64 seg)", "Tier 1: Med Poly (16 seg)", "Tier 2: Low Poly (6 seg)"]

    def update(dt: float):
        nonlocal dolly_timer
        dolly_timer += dt * 0.5

        # Move camera smoothly between 5m and 65m distance
        distance = 35.0 + math.sin(dolly_timer) * 30.0
        camera.set_position(0.0, 5.0, -distance)
        camera.look_at((0.0, 4.0, 0.0))

        # Evaluate LOD distance against camera position
        cam_pos = camera.position
        lod.update_lod((cam_pos.x, cam_pos.y, cam_pos.z))

        # Update HUD feedback
        active_idx = lod.current_level_index()
        active_name = tier_names[active_idx] if 0 <= active_idx < len(tier_names) else "Unknown"

        app.ui.clear()
        app.ui.draw_text("Velocity 3D Engine - Level of Detail (LOD) Demonstration", (20, 20), size=18, color=ve.WHITE)
        app.ui.draw_text(f"Camera Distance: {distance:.1f} m", (20, 48), size=15, color=ve.CYAN)
        app.ui.draw_text(f"Active Tier: {active_name}", (20, 72), size=15, color=ve.YELLOW)
        app.ui.show_stats(True)

    app.set_update_callback(update)
    app.run()


if __name__ == "__main__":
    main()
```

---

## 6. Common Pitfalls & Best Practices

### 6.1 Base Mesh Index Buffer Limit (65,535 Vertices)

> [!CAUTION]
> The Sokol GFX backend for standard index buffers uses 16-bit indices (`uint16_t`). The base mesh supplied to `InstancedMesh(base_mesh)` **must never exceed 65,535 vertices**. If your model has more vertices, split it into sub-meshes before instancing.

### 6.2 CPU Transform Loops vs. Static Instances

When populating large instances ($N > 20,000$):
- Do not call `set_instance_transform` every frame from Python unless instances are actually moving. Calling Python functions in a 50,000-iteration loop introduces an avoidable 15–20 ms CPU interpreter overhead.
- For static geometry (rocks, trees, buildings), configure transforms once during level load. The GPU maintains the instance buffer in VRAM with zero CPU per-frame cost.

### 6.3 Frustum Culling AABB Margins

> [!TIP]
> When testing animated or rotating objects against the camera frustum using `Frustum.intersects_aabb`, ensure the bounding box encapsulates the object across its complete rotational arc. If the AABB is too tight, the geometry may pop out of existence near screen edges. Use `model.world_aabb()` or expand the box by $10\%$ to prevent visual popping.
