# Audio System & 3D Spatial Sound

Velocity 3D Engine integrates a high-performance, low-latency audio subsystem powered by the native [miniaudio](https://miniaud.io/) library. The engine supports non-directional 2D audio cues, full 3D spatialized positional sound with distance attenuation, real-time procedural sound synthesis (eliminating asset load dependencies for core gameplay actions), and concurrent voice pools.

```mermaid
flowchart TD
    subgraph GameApp["Application & Game Logic"]
        PyCode["Python Script (VelocityEngine as ve)"]
        FPSCtrl["FirstPersonController / Camera"]
    end

    subgraph AudioEngine["Velocity AudioManager (Native C++20)"]
        Listener["Audio Listener\n(Position, Forward, Up)"]
        VoicePool["Voice Pools (POOL_SIZE = 4)\nRound-Robin Concurrency"]
        Synth["Procedural Sound Synthesis\n(PCM Waveform Generators)"]
        FileLoader["Audio File Streaming\n(WAV, MP3, FLAC)"]
    end

    subgraph MiniaudioLayer["miniaudio Subsystem"]
        MA_Engine["ma_engine (Mixing & Spatialization)"]
        MA_Spatial["Inverse Attenuation\nMin/Max Distance Clamping"]
        MA_Device["Hardware Audio Device (WASAPI / CoreAudio / ALSA)"]
    end

    PyCode -->|play_jump / play_footstep| VoicePool
    PyCode -->|play_hit_3d(world_pos)| MA_Spatial
    PyCode -->|play_sound_file(path)| FileLoader
    FPSCtrl -->|update_listener(pos, fwd, up)| Listener
    Listener --> MA_Engine
    VoicePool --> MA_Engine
    Synth --> VoicePool
    FileLoader --> MA_Engine
    MA_Spatial --> MA_Engine
    MA_Engine --> MA_Device
```

---

## 1. Conceptual Overview & Acoustics Theory

### 1.1 2D Audio Cues vs. 3D Spatial Sound

Audio cues in game engines fall into two distinct perceptual categories:

1. **2D Stereo (Non-Directional) Cues**:
   - Audio is sent directly to the left and right speakers without panning or attenuation.
   - Typical use cases: Background music (BGM), user interface clicks, menu popups, narration, and local character actions like the player's own footsteps and jump grunts.
   - In Velocity, 2D cues have spatialization explicitly disabled (`ma_sound_set_spatialization_enabled(&sound, MA_FALSE)`).

2. **3D Spatialized (Positional) Sound**:
   - Audio emits from a discrete point in 3D world coordinates $\mathbf{P}_{\text{emitter}} = (x_e, y_e, z_e)$.
   - The sound engine calculates directional panning, phase differences (interaural time differences, ITD), and distance attenuation relative to the listener's head position $\mathbf{P}_{\text{listener}}$ and orientation vectors $(\mathbf{f}_{\text{listener}}, \mathbf{u}_{\text{listener}})$.
   - Typical use cases: Enemy footsteps, bullet impacts, ricochets, ambient torches, waterfalls, vehicle engines, and explosion blasts.

### 1.2 Distance Attenuation Physics

As an acoustic pressure wave expands spherically outward from a point source, sound intensity obeys the **inverse-square law**:

$$I(d) \propto \frac{1}{d^2}$$

However, human auditory perception of loudness is logarithmic (measured in decibels, $\text{dB}$). For perceptually natural roll-off without unnatural harshness, Velocity configures an **inverse distance attenuation model**:

$$\text{Gain}(d) = \frac{d_{\text{min}}}{d_{\text{min}} + \alpha \cdot \max(0, d - d_{\text{min}})}$$

Where:
- $d = \|\mathbf{P}_{\text{emitter}} - \mathbf{P}_{\text{listener}}\|$ is the Euclidean distance between sound source and camera/listener.
- $d_{\text{min}}$ is the inner distance threshold within which the sound plays at maximum volume ($1.0$). In Velocity, default $d_{\text{min}} = 1.5\,\text{m}$.
- $d_{\text{max}}$ is the cutoff threshold beyond which sound attenuates to silence or minimum audibility. In Velocity, default $d_{\text{max}} = 35.0\,\text{m}$.
- $\alpha$ is the attenuation roll-off factor (typically $1.0$).

```text
Volume Gain
  1.0 |-----------------\
      |                  \  Inverse Attenuation Curve
  0.5 |                   \---
      |                       \-----
  0.0 |                             \--------------|
      +-------------------+------------------------+---> Distance (m)
      0                d_min (1.5m)            d_max (35.0m)
```

### 1.3 Listener Synchronization with Camera Pose

Spatial audio perception requires the virtual ears (the listener) to match the player's camera position and view frustum orientation exactly.

In Velocity, every frame inside the native `EngineApp::render_frame()` pipeline, the listener is synchronized immediately before the Python tick callback:

```cpp
// Executed natively every frame in core/src/app.cpp
audio_.update_listener(camera_.position, camera_.forward(), camera_.up);
```

The listener vectors are:
1. **Position** $\mathbf{p} = (x, y, z)$: The world-space origin of the camera eye.
2. **Forward Direction** $\mathbf{f}$: Unit vector pointing in the camera's line of sight ($-\mathbf{z}$ in view space).
3. **Up Direction** $\mathbf{u}$: Unit vector indicating camera vertical orientation ($+\mathbf{y}$ in world space).

When a sound plays at $\mathbf{P}$, the relative vector $\mathbf{v} = \mathbf{P} - \mathbf{p}$ is projected onto the listener's local coordinate frame $(\mathbf{r}, \mathbf{u}, \mathbf{f})$ (where $\mathbf{r} = \mathbf{f} \times \mathbf{u}$ is the listener's right ear vector) to calculate stereo balance and attenuation.

---

## 2. Procedural Sound Synthesis

Velocity 3D Engine includes built-in procedural sound synthesis. This means gameplay actions (jumping, footsteps, bullet/raycast impacts) generate real-time audio waveforms purely via mathematical functions, with zero external `.wav` or `.mp3` dependencies.

All procedural sounds are generated at standard CD quality ($44,100\,\text{Hz}$, 16-bit signed PCM mono).

### 2.1 Low-Frequency Footstep Thud

The footstep generator simulates the impact of a foot against a hard surface using a rapid downward pitch sweep combined with a sharp exponential decay envelope and subtle contact noise:

$$\text{sample}(t) = \left( 0.85 \cdot \sin(2\pi \cdot f(t) \cdot t) + 0.15 \cdot \text{noise}(t) \right) \cdot \exp(-55.0 \cdot t) \cdot A$$

- **Duration**: $0.065\,\text{seconds}$ ($2,866$ samples).
- **Pitch Sweep**: Frequency glides down from $130\,\text{Hz}$ to $40\,\text{Hz}$:
  $$f(t) = 130.0 - 90.0 \cdot \left(\frac{t}{\text{duration}}\right)$$
- **Envelope**: Rapid exponential falloff $\exp(-55t)$ produces a crisp physical thud.
- **Surface Texture**: Pseudo-random white noise in range $[-0.15, +0.15]$ simulates sole/ground friction.

### 2.2 Upward Jump Whoosh

The jump sound synthesizes the aerodynamic upward leap of a character through frequency ramp-up shaped by a parabolic bell envelope:

$$\text{sample}(t) = \sin(2\pi \cdot f(t) \cdot t) \cdot \sin\left(\pi \frac{t}{\text{duration}}\right) \cdot A$$

- **Duration**: $0.14\,\text{seconds}$ ($6,174$ samples).
- **Frequency Ramp**: Frequency sweeps upward from $140\,\text{Hz}$ to $460\,\text{Hz}$:
  $$f(t) = 140.0 + 320.0 \cdot \left(\frac{t}{\text{duration}}\right)$$
- **Envelope**: Smooth half-sine bell curve $\sin(\pi \cdot t / \text{duration})$ eliminates onset/offset speaker clicks.

### 2.3 3D Raycast Hit Chime

When a raycast or projectile hits an object, Velocity generates a harmonic two-note musical chime spatialized at the exact 3D contact point:

$$\text{sample}(t) = 0.65 \cdot \left( \sin(2\pi \cdot 660 \cdot t) + 0.6 \cdot \sin(2\pi \cdot 880 \cdot t) \right) \cdot \exp(-18.0 \cdot t) \cdot A$$

- **Duration**: $0.22\,\text{seconds}$ ($9,702$ samples).
- **Harmonics**: An E5 note ($660\,\text{Hz}$) coupled with an A5 note ($880\,\text{Hz}$) forming a clean perfect fourth interval.
- **Exponential Tail**: $\exp(-18t)$ provides a sustained, metallic, rewarding feedback ring.

---

## 3. Sound Pools & Voice Concurrency

A major pitfall in real-time game audio is **voice starvation** and **playback cutoff**. If a player sprints and generates footsteps every $0.25$ seconds while the footstep sound lasts $0.065$ seconds, calling `play()` on a single audio handle will either abort the playing sound abruptly (causing audible clicks) or fail to start.

To solve this, Velocity implements **Round-Robin Sound Pools**:

```cpp
struct AudioManager::Impl {
    static constexpr size_t POOL_SIZE = 4;
    ma_sound footstep_sounds[POOL_SIZE]{};
    size_t footstep_idx{0};

    ma_sound jump_sounds[POOL_SIZE]{};
    size_t jump_idx{0};

    ma_sound hit_sounds[POOL_SIZE]{};
    size_t hit_idx{0};
};
```

When an audio event triggers:
1. The engine retrieves the sound voice at `current_index`.
2. Advances the index: `current_index = (current_index + 1) % POOL_SIZE`.
3. For positional sounds, updates the 3D emitter coordinates: `ma_sound_set_position(&snd, x, y, z)`.
4. Seeks the PCM stream back to sample frame 0: `ma_sound_seek_to_pcm_frame(&snd, 0)`.
5. Starts playback: `ma_sound_start(&snd)`.

With a `POOL_SIZE` of 4, up to four distinct hit chimes, jump whooshes, or footsteps can ring out simultaneously without canceling each other out.

---

## 4. Core Engine Classes & Methods

### 4.1 Python API (`VelocityEngine.AudioManager`)

| Class / Method | Signature | Description |
| :--- | :--- | :--- |
| `app.audio` | `-> AudioManager` | Accesses the engine's primary audio manager singleton attached to `App`. |
| `play_footstep()` | `() -> None` | Triggers a 2D non-directional procedural footstep sound using round-robin pooling. |
| `play_jump()` | `() -> None` | Triggers a 2D non-directional procedural jump whoosh sound. |
| `play_hit_3d()` | `(world_pos: Vec3 \| tuple[float, float, float]) -> None` | Triggers a 3D spatialized harmonic chime at the designated world position. |
| `play_sound_file()` | `(filepath: str, volume: float = 1.0) -> None` | Loads and streams an external audio file (`.wav`, `.mp3`, `.flac`). |
| `play_sound()` | `(name: str, *args, **kwargs) -> Any` | Ergonomic Python wrapper dispatching to jump, footstep, hit, or file based on string name. |

### 4.2 C++ Native Core API (`engine::AudioManager`)

| C++ Method | Description |
| :--- | :--- |
| `bool init()` | Initializes the `ma_engine` backend, pre-computes PCM buffers, and allocates sound pools. |
| `void shutdown()` | Safely stops all playing voices, frees audio buffers, and uninitializes the miniaudio engine. |
| `bool is_initialized() const` | Returns `true` if the audio device is active and healthy. |
| `void update_listener(pos, fwd, up)` | Updates miniaudio listener position, forward vector, and up vector in world space. |
| `void play_footstep()` | Selects next pooled footstep voice and plays from frame 0. |
| `void play_jump()` | Selects next pooled jump voice and plays from frame 0. |
| `void play_hit_3d(const glm::vec3& pos)` | Sets 3D emitter coordinates on next pooled hit voice and starts playback. |
| `void play_sound_file(path, vol)` | Initializes a one-shot `ma_sound` from disk and starts playback at designated volume. |

---

## 5. Runnable Code Examples

### 5.1 Interactive 3D Spatial Audio Sandbox

The following self-contained script creates a 3D scene with an orbiting sound emitter. As the sound source revolves around the camera, spatial panning and distance attenuation can be heard dynamically.

```python
"""Velocity 3D Engine: Interactive 3D Spatial Audio Demo."""

import math
import VelocityEngine as ve


def main():
    # 1. Initialize Engine Application
    app = ve.App(
        title="Velocity 3D Engine - 3D Spatial Audio Demo",
        width=1280,
        height=720,
        clear_color=(0.08, 0.12, 0.18, 1.0),
    )

    # 2. Camera Setup (Listener position)
    app.camera.set_position(0.0, 1.8, -5.0)
    app.camera.set_yaw_pitch(90.0, -10.0)

    # 3. Environment & Lighting
    scene = app.scene
    scene.set_sun(direction=(0.5, -1.0, 0.4), color=(1.0, 0.95, 0.9), intensity=1.2)

    # Ground reference grid
    ground = scene.create_plane(size=30.0)
    ground_mat = ve.Material.plastic(roughness=0.8, color=(0.15, 0.20, 0.25))
    ground.material = ground_mat

    # Visual representation of the audio listener (Player)
    listener_marker = scene.create_cube()
    listener_marker.transform.scale = (0.4, 1.6, 0.4)
    listener_marker.transform.position = (0.0, 0.8, 0.0)
    listener_marker.material = ve.Material.metal(roughness=0.2, color=(0.2, 0.8, 0.4))

    # Visual representation of the orbiting 3D audio emitter
    sound_orb = scene.create_sphere(radius=0.4)
    sound_mat = ve.Material.gold(roughness=0.1)
    sound_orb.material = sound_mat

    # 4. State tracking
    audio_timer = 0.0
    orbit_angle = 0.0
    orbit_radius = 4.5

    # 5. UI Overlay
    app.ui.draw_text("Velocity 3D Engine - Spatial Audio Sandbox", (20, 20), size=18, color=ve.WHITE)
    app.ui.draw_text("Gold Sphere: Orbiting 3D Sound Source | Green Pillar: Listener", (20, 48), size=14, color=ve.CYAN)
    app.ui.draw_text("[SPACE] Trigger Jump (2D) | [F] Trigger Footstep (2D) | [LMB] 3D Hit Chime", (20, 74), size=13, color=ve.YELLOW)
    app.ui.show_stats(True)

    def on_frame(dt: float):
        nonlocal audio_timer, orbit_angle

        # Rotate sound emitter in a circle around the listener
        orbit_angle += dt * 1.2
        emitter_x = math.cos(orbit_angle) * orbit_radius
        emitter_z = math.sin(orbit_angle) * orbit_radius
        emitter_y = 1.0 + math.sin(orbit_angle * 2.0) * 0.5
        sound_orb.transform.position = (emitter_x, emitter_y, emitter_z)

        # Pulse periodic 3D hit chime at emitter location
        audio_timer += dt
        if audio_timer >= 0.65:
            audio_timer = 0.0
            # Play spatial chime in 3D world space
            app.audio.play_hit_3d((emitter_x, emitter_y, emitter_z))

        # Handle user input triggers for 2D cues
        input_mgr = app.input
        if input_mgr.is_key_just_pressed(ve.Key.SPACE):
            app.audio.play_jump()
        if input_mgr.is_key_just_pressed(ve.Key.F):
            app.audio.play_footstep()
        if input_mgr.is_mouse_button_just_pressed(ve.MouseButton.LEFT):
            # Play chime at current orb position
            app.audio.play_sound("hit", (emitter_x, emitter_y, emitter_z))

    app.set_update_callback(on_frame)
    app.run()


if __name__ == "__main__":
    main()
```

### 5.2 Raycast Shooting Range with 3D Spatial Audio

This example illustrates raycast shooting against interactive 3D targets. When a target is hit, a 3D chime is played at the exact hit point, providing directional auditory feedback.

```python
"""Velocity 3D Engine: Raycast Shooting Range with 3D Spatial Audio."""

import random
import VelocityEngine as ve


def main():
    app = ve.App(
        title="Velocity - Target Shooting Audio Demo",
        width=1280,
        height=720,
    )

    # 1. First-Person Camera Setup
    camera = app.camera
    camera.set_position(0.0, 1.7, -4.0)
    camera.set_yaw_pitch(90.0, 0.0)

    # 2. Lighting
    scene = app.scene
    scene.set_sun(direction=(0.3, -1.0, 0.5), color=ve.WARM_WHITE, intensity=1.4)

    # 3. Spawn 3D Targets
    targets = []
    rng = random.Random(1337)
    for i in range(8):
        box = scene.create_cube()
        tx = rng.uniform(-6.0, 6.0)
        ty = rng.uniform(0.8, 3.5)
        tz = rng.uniform(4.0, 12.0)
        box.transform.position = (tx, ty, tz)
        box.transform.scale = (0.8, 0.8, 0.8)
        box.material = ve.Material.plastic(roughness=0.3, color=(0.9, 0.2, 0.2))
        targets.append(box)

    score = 0

    # 4. Setup HUD & Crosshair
    app.set_hud_title("Audio Target Range")
    app.show_hud = True
    app.set_hud_score(0)
    app.set_hud_hint("[LMB] Shoot   [TAB] Lock Mouse   [ESC] Exit")

    def on_update(dt: float):
        nonlocal score
        input_mgr = app.input

        # Lock mouse on click
        if input_mgr.is_mouse_button_just_pressed(ve.MouseButton.LEFT):
            if not input_mgr.is_mouse_locked():
                input_mgr.set_mouse_locked(True)

            # Fire Ray from center of screen (Camera forward ray)
            ray = camera.screen_to_ray(app.width // 2, app.height // 2, app.width, app.height)
            hit = scene.raycast(ray)

            if hit.has_hit:
                # 3D spatial chime at exact impact point
                app.audio.play_hit_3d(hit.point)

                # Flash target gold
                score += 100
                app.set_hud_score(score)

                # Visual hit effect
                if hit.entity:
                    hit.entity.material.base_color = (1.0, 0.85, 0.2, 1.0)
            else:
                # Empty shot whoosh
                app.audio.play_jump()

    app.set_update_callback(on_update)
    app.run()


if __name__ == "__main__":
    main()
```

---

## 6. Common Pitfalls & Best Practices

### 6.1 Audio Initialization Sequence

> [!IMPORTANT]
> The `AudioManager` initializes automatically during `app.init()` or `ve.App(...)` construction. Attempting to call `play_hit_3d` or `play_footstep` on an uninitialized native manager is safely protected by an internal `if (!is_initialized()) return;` check, but no audio will be emitted. Always verify that your application constructor has completed before calling audio playback methods.

### 6.2 Coordinate System Alignment

> [!WARNING]
> Positional audio depends strictly on the camera pose. Velocity automatically feeds `camera.position`, `camera.forward()`, and `camera.up` into `ma_engine_listener_set_*` once per frame. If you manually move or rotate an entity acting as the camera without updating the engine's main camera (`app.camera`), spatial panning will sound rotated or inverted.

### 6.3 Volume and Clipping Prevention

When playing multiple sound sources simultaneously (e.g., machine gun impacts or multiple explosions), sound amplitudes sum together. If total amplitude exceeds $1.0$ (or $\pm 32,767$ in 16-bit PCM), digital clipping (harsh distortion) occurs.

**Best Practice**:
- Keep individual sound effect volumes between $0.6$ and $0.85$.
- Keep spatial sounds clamped within a realistic distance window ($d_{\text{min}} = 1.5\,\text{m}$, $d_{\text{max}} = 35.0\,\text{m}$).

### 6.4 Audio File Paths

When loading external files via `play_sound_file(filepath)`:
- Always resolve paths relative to `Path(__file__).resolve().parent` or `app.asset_path(...)` to prevent `FileNotFoundError` when launching scripts from different terminal working directories.
- Supported file formats out of the box: **WAV (uncompressed PCM)**, **MP3**, and **FLAC**.
