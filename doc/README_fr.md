# Velocity 3D Engine

[ [English](../README.md) | [Русский](README_ru.md) | [中文](README_zh.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | [Deutsch](README_de.md) | [日本語](README_ja.md) | [Português](README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)]()

> [!WARNING]
> ### ⚠️ Statut du projet : Alpha précoce / En cours de développement (WIP)
> Ce moteur est actuellement à un stade **alpha expérimental précoce**. Il constitue une preuve de concept architecturale active et un socle technique. De nombreux sous-systèmes font l'objet d'itérations intensives, les API sont susceptibles de subir des modifications majeures (breaking changes), et d'importants travaux de modernisation, de refactorisation et d'optimisation sont prévus. **Il n'est pas encore prêt pour la production.** Cependant, un cœur solide (C++20, Sokol GFX, nanobind, PBR, animation squelettique et suite complète de tests) est d'ores et déjà établi et fonctionnel.

---

## 🌟 Points forts

**Velocity 3D Engine** associe les performances de rendu pures du C++20 moderne et de [Sokol GFX](https://github.com/floooh/sokol) à l'ergonomie expressive de Python via [nanobind](https://github.com/wjakob/nanobind).

- **Cœur haute performance** : Écrit en C++20 moderne avec des abstractions légères sans surcoût (zero-overhead), des mathématiques GLM et Sokol GFX (Direct3D 11, Metal, OpenGL).
- **Ergonomie Pythonique** : Liaisons Python complètes avec stubs de types `.pyi` conformes PEP-484 / PEP-561 pour l'autocomplétion dans les IDE. Prise en charge de la surcharge d'opérateurs, des gestionnaires de contexte et du déballage de vecteurs.
- **Rendu basé sur la physique (PBR)** : Flux de travail métal-rugosité (spéculaire microfacettes Cook-Torrance GGX, diffusion lambertienne, placage de normales Sobel, occlusion ambiante et cartes d'émission).
- **Système d'animation squelettique** : Chargeur de squelettes glTF 2.0 avec propagation de la hiérarchie des articulations, matrices de liaison inverses (inverse bind matrices), skinning linéaire sur CPU (linear blend skinning) et mélange de clips d'animation multiples.
- **Pipeline de post-traitement** : `EffectComposer` modulaire prenant en charge le post-traitement multi-passes : Bloom gaussien HDR, mappage tonal (tonemapping) ACES/Reinhard, vignettage et passes de shaders plein écran GLSL/HLSL personnalisées.
- **Rendu instancié (Instanced Rendering)** : Pipeline `InstancedMesh` à haut débit capable de restituer des dizaines de milliers d'instances dynamiques (ex. champs d'astéroïdes, forêts) avec des matrices de transformation 4x4 individuelles et des teintes de couleur par instance.
- **Queue d'overlay & HUD 2D** : File d'attente de rendu orthographique 2D intégrée avec atlas de polices matricielles (bitmap font) intégré pour l'affichage de statistiques de débogage, de jauges de santé et de réticules à l'écran.
- **Audio spatialisé** : Moteur audio intégré propulsé par `miniaudio` pour les effets sonores, l'atténuation 3D spatiale et l'ambiance sonore d'arrière-plan.
- **Couverture de tests 100 % automatisée** : Suite exhaustive de plus de 420 tests unitaires, d'intégration et de stress automatisés validant la sécurité mémoire, le cycle de vie des handles et les calculs mathématiques de rendu.

---

## 🎮 Démos jouables incluses

Le dépôt comprend deux jeux de démonstration complets et autonomes dans le répertoire [`games/`](../games/), démontrant les capacités du moteur :

### 1. Dungeon Crawler (`games/dungeon_crawler.py`)
Un action-RPG à la troisième personne se déroulant dans une crypte souterraine sombre :
- **Personnage joueur animé** : Modèle de chevalier animé glTF complet avec hiérarchie osseuse et animations de déplacement.
- **Armement modulaire** : Épée bâtarde (broadsword) modélisée en 3D sur mesure avec garde dorée, pommeau et fourreau en cuir attaché à la hanche.
- **Matériaux PBR procéduraux** : Murs en maçonnerie de pierre de taille haute résolution, sols en dalles avec relief de normales et coffres au trésor en chêne sombre cerclés de fer.
- **HUD RPG** : Barres de santé et d'endurance en temps réel, compteurs d'or, de clés et de reliques collectés, et carte de mini-map.
- **Audio & Ambiance** : Bande-son atmosphérique de donjon, bruits de pas, effets sonores d'interaction avec les coffres et éclairage dynamique de flammes de torches.

```powershell
python games/dungeon_crawler.py
```

### 2. Space Combat Arena (`games/space_combat_arena.py`)
Une simulation de combat spatial à 6 degrés de liberté (6DOF) à haute vitesse :
- **Modèle de vol de chasseur spatial** : Physique inertielle à 6 degrés de liberté avec tangage, lacet, roulis et accélération par postcombustion (booster).
- **Ceinture d'astéroïdes** : Champ d'astéroïdes instancié généré de manière procédurale avec des échelles et des rotations variées, rendu via `InstancedMesh`.
- **Environnement cosmique** : Skybox de nébuleuse de l'espace profond, propulseurs à particules volumétriques et physique de projectiles laser.
- **Avionique de cockpit** : HUD de vol de science-fiction avec indicateur de vitesse, jauge de condensateur de boost, moniteurs de coque et de bouclier, et suivi radar 2D.

```powershell
python games/space_combat_arena.py
```

---

## 📂 Structure du dépôt

```text
velocity-3d-engine/
├── assets/                     # Modèles 3D glTF/GLB, textures et cartes de normales
│   ├── textures/               # Cartes de textures PBR diffuses, normales et RGBA
│   ├── Soldier.glb             # Modèle de personnage animé et gréé (rigged)
│   └── DamagedHelmet.glb       # Modèle de test de référence PBR glTF
├── bindings/                   # Liaisons nanobind C++ -> Python
│   ├── bindings.cpp            # Point d'entrée principal du module
│   ├── bind_app.cpp            # Cycle de vie de l'application et gestion des fenêtres
│   ├── bind_geometry.cpp       # Maillages, courbes, points, géométrie instanciée
│   ├── bind_materials.cpp      # Matériaux PBR, unlit et shaders personnalisés
│   ├── bind_math.cpp           # Vec2/3/4, Quat, Euler, Mat3/4, Ray, Frustum
│   ├── bind_postprocess.cpp    # EffectComposer et passes de post-traitement
│   └── bind_scene.cpp          # Scene, Entity, Node3D, lumières, caméras
├── core/                       # Implémentation du cœur du moteur en C++20
│   ├── include/engine/         # Fichiers d'en-tête publics
│   └── src/                    # Fichiers sources du moteur
├── examples/                   # 13 exemples pédagogiques ciblés par fonctionnalité
│   ├── 01_hello_pbr.py         # Configuration basique d'une sphère PBR
│   ├── 02_dynamic_lights_bloom.py # Lumières ponctuelles dynamiques et passe de bloom
│   ├── 03_skeletal_character.py # Chargement d'animations squelettiques glTF
│   ├── 04_numpy_wave_surface.py # Déformation procédurale de maillage via NumPy
│   ├── 05_custom_shader_water.py # Passe de shader plein écran personnalisée
│   ├── 06_render_to_texture_portal.py # Cibles de rendu et rendu de portail
│   ├── 07_particles_and_sprites.py # Systèmes de particules et sprites 3D billboard
│   ├── 08_instanced_forest.py  # Rendu instancié à haute densité
│   └── ...                     # Démonstrations interactives supplémentaires
├── games/                      # Jeux autonomes jouables (Dungeon & Space)
├── python/                     # Implémentations de packages Python & stubs de types
│   ├── VelocityEngine/         # Package principal du moteur
│   ├── velocity/               # Alias pythonique en minuscules
│   └── pielosyty/              # Couche d'alias pour rétrocompatibilité
├── scripts/                    # Outils utilitaires et de génération procédurale de textures
├── tests/                      # Plus de 420 suites de tests automatisés pytest
├── third_party/                # Dépendances tierces (Sokol, GLM, ImGui, miniaudio)
├── CMakeLists.txt              # Système de build principal CMake
└── pyproject.toml              # Configuration d'empaquetage Python scikit-build-core
```

---

## 🛠️ Compilation & Installation

### Prérequis

- **CMake** : `>= 3.24`
- **Compilateur C++20** :
  - Windows : MSVC 2022 (v143) ou Clang-CL
  - Linux : GCC `>= 12` ou Clang `>= 15`
  - macOS : Apple Clang `>= 14`
- **Python** : `>= 3.10`
- **Outil de compilation** : Ninja (recommandé) ou MSBuild

### 1. Compilation et installation via Python (Mode éditable)

```powershell
# Cloner le dépôt
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# Installer les dépendances de compilation
pip install scikit-build-core nanobind ninja pytest numpy

# Compiler le cœur C++ et installer les liaisons Python
pip install -e . --no-build-isolation
```

### 2. Compilation directe via CMake

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. Exécution des tests automatisés

```powershell
pytest tests -q
```

---

## 💡 Exemple de démarrage rapide

```python
import VelocityEngine as ve

# 1. Initialiser l'application
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. Configurer la caméra
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. Ajouter un éclairage directionnel et ambiant
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. Créer un matériau PBR et un maillage
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. Lancer la boucle d'application
app.run()
```

---

## 🗺️ Feuille de route & Limitations connues

En tant qu'alpha précoce, plusieurs améliorations architecturales clés sont prévues :

- [ ] **Skinning sur GPU Compute** : Migration du skinning linéaire sur CPU actuel vers une évaluation par vertex shader / compute shader sur GPU pour les scènes avec un nombre élevé de maillages squelettiques.
- [ ] **Cascades de cartes d'ombres (CSM)** : Prise en charge de cascades directionnelles multi-frustums pour les scènes extérieures en monde ouvert.
- [ ] **Transcompilation de shaders** : Formalisation de la conversion hors ligne automatisée GLSL/HLSL/MSL via `sokol-shdc`.
- [ ] **Intégration d'un moteur physique** : Intégration de Jolt Physics ou PhysX pour la simulation de corps rigides et la gestion des collisions.
- [ ] **Backends Vulkan & WebGPU** : Ajout de cibles Vulkan et WebAssembly/WebGPU via Sokol GFX.

---

## 📄 Licence

Ce projet est sous licence [MIT](../LICENSE).
Les bibliothèques tierces dans [`third_party/`](../third_party/) sont soumises à leurs licences open source respectives (Sokol : zlib/libpng, GLM : Happy Bunny / MIT, ImGui : MIT, miniaudio : Domaine Public / MIT-0).
