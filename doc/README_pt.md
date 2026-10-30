# Velocity 3D Engine

[ [English](../README.md) | [Русский](README_ru.md) | [中文](README_zh.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | [Deutsch](README_de.md) | [日本語](README_ja.md) | [Português](README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)]()

> [!WARNING]
> ### ⚠️ Status do Projeto: Alfa Inicial / Em Desenvolvimento (WIP)
> Este motor está atualmente em um estágio **alfa experimental inicial**. É uma prova de conceito arquitetural ativa e uma base técnica. Muitos subsistemas estão passando por intensa iteração, as APIs estão sujeitas a alterações que quebram compatibilidade, e modernizações, refatorações e otimizações significativas estão planejadas. **Ainda não está pronto para produção.** No entanto, uma base sólida (C++20, Sokol GFX, nanobind, PBR, animação esquelética e suíte completa de testes) está estabelecida e funcional.

---

## 🌟 Destaques

O **Velocity 3D Engine** combina o desempenho bruto de renderização do moderno C++20 e [Sokol GFX](https://github.com/floooh/sokol) com a expressividade ergonômica do Python via [nanobind](https://github.com/wjakob/nanobind).

- **Núcleo de Alto Desempenho**: Escrito em C++20 moderno com abstrações leves de sobrecarga zero (zero-overhead), matemática GLM e Sokol GFX (Direct3D 11, Metal, OpenGL).
- **Ergonomia Pythônica**: Bindings completos para Python com stubs de tipo `.pyi` compatíveis com PEP-484 / PEP-561 para autocompletar em IDEs. Suporte a sobrecarga de operadores, gerenciadores de contexto e desempacotamento de vetores.
- **Renderização Baseada em Física (PBR)**: Fluxo de trabalho metálico-rugosidade (especular microfaceta Cook-Torrance GGX, difusão Lambertiana, mapeamento de normais Sobel, oclusão de ambiente e mapas emissivos).
- **Sistema de Animação Esquelética**: Carregador esquelético glTF 2.0 com propagação de hierarquia de juntas, matrizes de pose inversa (inverse bind matrices), skinning por mistura linear na CPU e mesclagem de animações multi-clip.
- **Pipeline de Pós-Processamento**: `EffectComposer` modular com suporte a pós-processamento multi-pass: Bloom gaussiano HDR, mapeamento de tons (tonemapping) ACES/Reinhard, vinheta e passes de shaders de tela cheia personalizados em GLSL/HLSL.
- **Renderização Instanciada**: Pipeline `InstancedMesh` de alto rendimento capaz de renderizar dezenas de milhares de instâncias dinâmicas (por exemplo, campos de asteroides, florestas) com matrizes de transformação 4x4 individuais e cores de tonalidade por instância.
- **Fila de HUD 2D e Overlays**: Fila integrada de renderização ortográfica 2D com atlas de fontes bitmap embutido para estatísticas de depuração na tela, barras de vida e miras.
- **Áudio Espacial**: Motor de áudio integrado desenvolvido com `miniaudio` para efeitos sonoros, atenuação espacial 3D e ambiência de fundo.
- **Cobertura de Testes 100% Automatizada**: Suíte abrangente de mais de 420 testes automatizados unitários, de integração e de estresse, verificando a segurança de memória, o ciclo de vida de handles e a matemática de renderização.

---

## 🎮 Demonstrações Jogáveis Incluídas

O repositório inclui dois jogos de demonstração completos e independentes no diretório [`games/`](../games/) que demonstram os recursos do motor:

### 1. Dungeon Crawler (`games/dungeon_crawler.py`)
Um RPG de ação em terceira pessoa ambientado em uma cripta subterrânea escura:
- **Personagem do Jogador Animado**: Modelo completo de cavaleiro animado em glTF com hierarquia óssea e animações de locomoção.
- **Armamento Modular**: Espada larga modelada em 3D personalizada com guarda dourada, pomo e bainha de couro presa ao quadril.
- **Materiais PBR Procedurais**: Paredes de alvenaria de silhar de alta resolução, pisos de lajotas com mapeamento de normais e baús de tesouro de carvalho escuro com tiras de ferro.
- **HUD de RPG**: Barras de vida e estamina em tempo real, contadores de ouro, chaves e relíquias coletadas, e cartão de minimapa.
- **Áudio e Ambiência**: Trilha sonora atmosférica de masmorra, efeitos sonoros de passos, sons de interação com baús e iluminação por chamas de tochas.

```powershell
python games/dungeon_crawler.py
```

### 2. Space Combat Arena (`games/space_combat_arena.py`)
Uma simulação de combate de voo espacial 6DOF em alta velocidade:
- **Modelo de Voo de Caça Estelar**: Física inercial de 6 graus de liberdade com arfagem (pitch), guinada (yaw), rolagem (roll) e aceleração de propulsores.
- **Cinturão de Asteroides**: Campo de asteroides instanciado gerado proceduralmente com escalas e rotações diversas, renderizado via `InstancedMesh`.
- **Ambiente Cósmico**: Skybox de nebulosa no espaço profundo, propulsores com partículas volumétricas e física de projéteis laser.
- **Aviônica do Cockpit**: HUD de voo sci-fi com velocímetro, medidor do capacitor de propulsão, monitores de casco e escudo, e rastreamento por radar 2D.

```powershell
python games/space_combat_arena.py
```

---

## 📂 Estrutura do Repositório

```text
velocity-3d-engine/
├── assets/                     # Modelos glTF/GLB 3D, texturas e mapas de normais
│   ├── textures/               # Mapas de textura PBR difusa, normais e RGBA
│   ├── Soldier.glb             # Modelo de personagem animado com rig
│   └── DamagedHelmet.glb       # Modelo de teste PBR de referência glTF
├── bindings/                   # Bindings nanobind C++ -> Python
│   ├── bindings.cpp            # Ponto de entrada principal do módulo
│   ├── bind_app.cpp            # Ciclo de vida da aplicação e gerenciamento de janelas
│   ├── bind_geometry.cpp       # Malhas, curvas, pontos, geometria instanciada
│   ├── bind_materials.cpp      # Materiais PBR, unlit e shaders personalizados
│   ├── bind_math.cpp           # Vec2/3/4, Quat, Euler, Mat3/4, Ray, Frustum
│   ├── bind_postprocess.cpp    # EffectComposer e passes de pós-processamento
│   └── bind_scene.cpp          # Scene, Entity, Node3D, luzes, câmeras
├── core/                       # Implementação do núcleo do motor em C++20
│   ├── include/engine/         # Arquivos de cabeçalho públicos
│   └── src/                    # Arquivos de código-fonte do motor
├── examples/                   # 13 exemplos educacionais focados em recursos
│   ├── 01_hello_pbr.py         # Configuração básica de esfera PBR
│   ├── 02_dynamic_lights_bloom.py # Luzes pontuais dinâmicas e passe de bloom
│   ├── 03_skeletal_character.py # Carregamento de animação esquelética glTF
│   ├── 04_numpy_wave_surface.py # Deformação procedural de malha via NumPy
│   ├── 05_custom_shader_water.py # Passe de shader de tela cheia personalizado
│   ├── 06_render_to_texture_portal.py # Render targets e renderização de portais
│   ├── 07_particles_and_sprites.py # Sistemas de partículas e sprites 3D billboard
│   ├── 08_instanced_forest.py  # Renderização instanciada de alta densidade
│   └── ...                     # Demonstrações interativas adicionais
├── games/                      # Jogos independentes jogáveis (Dungeon & Space)
├── python/                     # Implementações do pacote Python e stubs de tipo
│   ├── VelocityEngine/         # Pacote principal do motor
│   ├── velocity/               # Alias pythônico em letras minúsculas
│   └── pielosyty/              # Camada de alias para compatibilidade com versões anteriores
├── scripts/                    # Utilitários e ferramentas de geração de textura procedural
├── tests/                      # Mais de 420 suítes de testes automatizados com pytest
├── third_party/                # Dependências integradas (Sokol, GLM, ImGui, miniaudio)
├── CMakeLists.txt              # Sistema de compilação principal do CMake
└── pyproject.toml              # Configuração de empacotamento Python com scikit-build-core
```

---

## 🛠️ Compilação e Instalação

### Pré-requisitos

- **CMake**: `>= 3.24`
- **Compilador C++20**:
  - Windows: MSVC 2022 (v143) ou Clang-CL
  - Linux: GCC `>= 12` ou Clang `>= 15`
  - macOS: Apple Clang `>= 14`
- **Python**: `>= 3.10`
- **Ferramenta de Compilação**: Ninja (recomendado) ou MSBuild

### 1. Compilar e Instalar via Python (Modo Editável)

```powershell
# Clonar o repositório
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# Instalar dependências de compilação
pip install scikit-build-core nanobind ninja pytest numpy

# Compilar o núcleo em C++ e instalar os bindings de Python
pip install -e . --no-build-isolation
```

### 2. Compilar via CMake Diretamente

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. Executar Testes Automatizados

```powershell
pytest tests -q
```

---

## 💡 Exemplo de Início Rápido

```python
import VelocityEngine as ve

# 1. Inicializar a aplicação
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. Configurar a câmera
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. Adicionar iluminação direcional e ambiente
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. Criar material PBR e malha
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. Executar o loop da aplicação
app.run()
```

---

## 🗺️ Roteiro de Desenvolvimento e Limitações Conhecidas

Por ser um estágio alfa inicial, várias melhorias arquiteturais importantes estão planejadas:

- [ ] **GPU Compute Skinning**: Migrar do atual skinning por mistura linear na CPU para avaliação em vertex shader / compute shader na GPU para grandes quantidades de malhas esqueléticas.
- [ ] **Cascaded Shadow Maps (CSM)**: Suporte a cascatas direcionais de múltiplos frustums para cenas externas de mundo aberto.
- [ ] **Compilação Cruzada de Shaders**: Formalizar a tradução automatizada offline de GLSL/HLSL/MSL via `sokol-shdc`.
- [ ] **Integração de Motor de Física**: Integrar Jolt Physics ou PhysX para simulação de corpos rígidos e resposta a colisões.
- [ ] **Backends Vulkan e WebGPU**: Adicionar alvos Vulkan e WebAssembly/WebGPU utilizando Sokol GFX.

---

## 📄 Licença

Este projeto está licenciado sob a [Licença MIT](../LICENSE).
As bibliotecas de terceiros em [`third_party/`](../third_party/) estão sujeitas às suas respectivas licenças de código aberto (Sokol: zlib/libpng, GLM: Happy Bunny / MIT, ImGui: MIT, miniaudio: Domínio Público / MIT-0).
