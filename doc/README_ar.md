# Velocity 3D Engine

[ [English](../README.md) | [Русский](README_ru.md) | [中文](README_zh.md) | [Español](README_es.md) | [Français](README_fr.md) | [العربية](README_ar.md) | [Deutsch](README_de.md) | [日本語](README_ja.md) | [Português](README_pt.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](../LICENSE)
[![C++ Standard](https://img.shields.io/badge/C%2B%2B-20-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B20)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-Early%20Alpha%20%2F%20WIP-orange.svg)]()

> [!WARNING]
> ### ⚠️ حالة المشروع: مرحلة ألفا المبكرة / قيد التطوير (WIP)
> يمر هذا المحرك حالياً بمرحلة **ألفا تجريبية مبكرة**. وهو يمثل إثبات مفهوم معماري نشط وأساساً تقنياً. تخضع العديد من الأنظمة الفرعية لتطوير مكثف، وواجهات برمجة التطبيقات (APIs) عرضة لتغييرات جذرية غير متوافقة مع الإصدارات السابقة، كما تم التخطيط لإجراء تحديثات هيكلية كبيرة وإعادة هيكلة برمجية (Refactoring) وتحسينات واسعة النطاق في الأداء. **المحرك غير جاهز للإنتاج بعد.** ومع ذلك، فإن النواة الأساسية الصلبة (C++20 و Sokol GFX و nanobind و PBR والتحريك الهيكلي وحزمة اختبارات شاملة) قد تم إرساؤها بالفعل وهي تعمل بكفاءة.

---

## 🌟 أبرز المميزات

يجمع **Velocity 3D Engine** بين الأداء الفائق للتصيير في C++20 الحديثة و [Sokol GFX](https://github.com/floooh/sokol) والتعبيرية البرمجية السلسة للغة بايثون عبر [nanobind](https://github.com/wjakob/nanobind).

- **نواة عالية الأداء**: مكتوبة بلغة C++20 الحديثة مع تجريدات خفيفة منعدمة التكلفة الإضافية (zero-overhead)، ومعادلات GLM الرياضية، ومكتبة Sokol GFX (تدعم Direct3D 11 و Metal و OpenGL).
- **مرونة بايثونية مريحة**: روابط برمجية كاملة لبايثون مع نصوص تعريف الأنواع (type stubs) وفق معايير PEP-484 / PEP-561 بصيغة `.pyi` للإكمال التلقائي في بيئات التطوير (IDE). دعم كامل للتحميل الزائد للعوامل (operator overloading)، ومديري السياق (context managers)، وتفكيك المتجهات.
- **التصيير المعتمد على الفيزياء (PBR)**: مسار عمل المعدن والخشونة (Metallic-Roughness Workflow) مع الإضاءة اللامعة للأسطح المجهرية Cook-Torrance GGX، والانتشار اللامبرتي (Lambertian diffuse)، وتخطيط النواظم عبر سوبل (Sobel normal mapping)، وتظليل الانسداد المحيطي (Ambient Occlusion)، وخرائط الانبعاث اللوني (Emissive maps).
- **نظام التحريك الهيكلي**: أداة تحميل الهياكل العظمية glTF 2.0 مع نشر التسلسل الهرمي للمفاصل، ومصفوفات الربط المعكوسة (inverse bind matrices)، والتدبيج الخطي على وحدة المعالجة المركزية (CPU linear blend skinning)، ومزج المقاطع الحركية المتعددة.
- **مسار معالجة ما بعد التصيير**: وحدة `EffectComposer` معيارية تدعم المعالجة متعددة المراحل: توهج غاوسي عالي المدى الديناميكي (HDR Gaussian Bloom)، وتعيين النغمات (tonemapping) عبر ACES/Reinhard، والتظليل المحيطي (vignette)، ومراحل تظليل مخصصة للشاشة بالكامل عبر GLSL/HLSL.
- **التصيير بالنسخ المتعددة (Instanced Rendering)**: مسار `InstancedMesh` عالي الإنتاجية قادر على تصيير عشرات الآلاف من النسخ الديناميكية (مثل حقول الكويكبات والغابات) بمصفوفات تحويل 4x4 وألوان تظليل فردية لكل نسخة.
- **طابور واجهة المستخدم والشاشات التراكبية ثنائية الأبعاد**: طابور تصيير إملائي (orthographic) مدمج ثنائي الأبعاد مع أطلس خطوط نقطية مدمج لعرض إحصائيات التنقيح على الشاشة، وأشرطة الصحة، ومؤشرات التصويب.
- **الصوت المكاني**: محرك صوتي مدمج مدعوم بـ `miniaudio` للمؤثرات الصوتية، والتخميد المكاني ثلاثي الأبعاد، والأصوات البيئية المحيطة.
- **تغطية اختبارية مؤتمتة بنسبة 100%**: حزمة شاملة تضم أكثر من 420 اختبار وحدة واختبار تكامل وضغط مؤتمت للتحقق من أمان الذاكرة، ودورات حياة المقابض (handles)، وعمليات التصيير الرياضية.

---

## 🎮 العروض التجريبية القابلة للعب المضمنة

يتضمن المستودع لعبتين تجريبيتين كاملتين ومستقلتين في دليل [`games/`](../games/) توضحان إمكانيات المحرك:

### 1. زاحف الزنزانة (`games/dungeon_crawler.py`)
لعبة تقمص أدوار وحركة من منظور الشخص الثالث تدور أحداثها في سرداب مظلم تحت الأرض:
- **شخصية لاعب متحركة**: نموذج فارس متحرك كامل بتنسيق glTF مع تسلسل هرمي للعظام وحركات تنقل متكاملة.
- **ترسانة أسلحة معيارية**: سيف عريض مخصص مصمم ثلاثي الأبعاد مع واقٍ مطلي بالذهب ومقبض وغمد جلدي مثبت على الحزام.
- **مواد PBR إجرائية**: جدران حجرية منحوتة عالية الدقة، وأرضيات مرصوفة مع خرائط النواظم، وصناديق كنوز من خشب البلوط الداكن مدعمة بالحديد.
- **واجهة مستخدم RPG HUD**: أشرطة حية للصحة والقدرة على التحمل (stamina)، وعدادات للذهب والمفاتيح والآثار المجمعة، ولوحة خريطة مصغرة.
- **الصوتيات والأجواء البيئية**: موسيقى تصويرية غامرة للزنزانة، وأصوات خطوات الأقدام، وتأثيرات صوتية للتفاعل مع الصناديق، وإضاءة ديناميكية لشعلات النار.

```powershell
python games/dungeon_crawler.py
```

### 2. ساحة القتال الفضائي (`games/space_combat_arena.py`)
محاكاة معارك طيران فضائي فائقة السرعة بست درجات حرية (6DOF):
- **نموذج طيران المقاتلة الفضائية**: فيزياء قصور ذاتي بست درجات حرية تشمل الانحدار (pitch)، والانعراج (yaw)، والتمايل (roll)، وتسارع المعزز النفاث.
- **حزام الكويكبات**: حقل كويكبات مولد إجرائياً باستخدام تقنية النسخ المتعددة بمقاييس ودورانات متنوعة يتم تصييرها عبر `InstancedMesh`.
- **البيئة الكونية**: سماء كونية (Skybox) بسديم الفضاء السحيق، ودوافع جزيئية حجمية، وفيزياء مقذوفات الليزر.
- **إلكترونيات قمرة القيادة**: واجهة عرض خيال علمي تتضمن مقياس السرعة، ومكثف التعزيز، وشاشات مراقبة الهيكل والدروع، وتتبع راداري ثنائي الأبعاد.

```powershell
python games/space_combat_arena.py
```

---

## 📂 هيكل المستودع

```text
velocity-3d-engine/
├── assets/                     # نماذج ثلاثية الأبعاد glTF/GLB وقوامات وخرائط النواظم
│   ├── textures/               # خرائط قوام PBR الانتشاري والنواظم و RGBA
│   ├── Soldier.glb             # نموذج شخصية متحركة مجهزة بهيكل عظمي (rigged)
│   └── DamagedHelmet.glb       # نموذج glTF مرجعي لاختبار تصيير PBR
├── bindings/                   # روابط nanobind بين C++ و Python
│   ├── bindings.cpp            # نقطة الدخول الأساسية للوحدة
│   ├── bind_app.cpp            # دورة حياة التطبيق وإدارة النوافذ
│   ├── bind_geometry.cpp       # الشبكات والمنحنيات والنقاط والهندسة المنسوخة
│   ├── bind_materials.cpp      # مواد PBR والمواد غير المضاءة ومظللات الشيدر المخصصة
│   ├── bind_math.cpp           # Vec2/3/4 و Quat و Euler و Mat3/4 و Ray و Frustum
│   ├── bind_postprocess.cpp    # وحدة EffectComposer ومراحل معالجة ما بعد التصيير
│   └── bind_scene.cpp          # المشهد (Scene) والكيانات والإضاءات والكاميرات
├── core/                       # التنفيذ البرمجي لنواة المحرك بلغة C++20
│   ├── include/engine/         # ملفات الترويسة العامة (Headers)
│   └── src/                    # ملفات المصدر للمحرك
├── examples/                   # 13 مثالاً تعليمياً يركز على الميزات الفردية
│   ├── 01_hello_pbr.py         # إعداد كرة PBR أساسية
│   ├── 02_dynamic_lights_bloom.py # أضواء نقطية ديناميكية وتمرير التوهج (bloom)
│   ├── 03_skeletal_character.py # تحميل الرسوم المتحركة الهيكلية glTF
│   ├── 04_numpy_wave_surface.py # تشويه إجرائي للشبكة باستخدام NumPy
│   ├── 05_custom_shader_water.py # تمرير تظليل مخصص للشاشة بالكامل
│   ├── 06_render_to_texture_portal.py # أهداف التصيير وتصيير البوابات (Portals)
│   ├── 07_particles_and_sprites.py # أنظمة الجسيمات ومجسمات اللوحات الإعلانية ثلاثية الأبعاد
│   ├── 08_instanced_forest.py  # تصيير بالنسخ المتعدد عالي الكثافة
│   └── ...                     # عروض تفاعلية إضافية
├── games/                      # ألعاب تجريبية قائمة بذاتها قابلة للعب (Dungeon و Space)
├── python/                     # حزم بايثون البرمجية وملفات تعريف الأنواع (Type Stubs)
│   ├── VelocityEngine/         # الحزمة الأساسية للمحرك
│   ├── velocity/               # اسم مستعار لبايثون بأحرف صغيرة
│   └── pielosyty/              # طبقة الأسماء المستعارة للتوافق مع الإصدارات السابقة
├── scripts/                    # أدوات مساعدة وتوليد إجرائي للقوامات
├── tests/                      # أكثر من 420 حزمة اختبارات مؤتمتة عبر pytest
├── third_party/                # المكتبات التابعة الخارجية (Sokol و GLM و ImGui و miniaudio)
├── CMakeLists.txt              # نظام البناء الأساسي عبر CMake
└── pyproject.toml              # تهيئة حزم بايثون باستخدام scikit-build-core
```

---

## 🛠️ البناء والتثبيت

### المتطلبات الأساسية

- **CMake**: `>= 3.24`
- **مترجم C++20**:
  - Windows: MSVC 2022 (v143) أو Clang-CL
  - Linux: GCC `>= 12` أو Clang `>= 15`
  - macOS: Apple Clang `>= 14`
- **Python**: `>= 3.10`
- **أداة البناء**: Ninja (موصى بها) أو MSBuild

### 1. البناء والتثبيت عبر بايثون (وضع التطوير التحريري)

```powershell
# استنساخ المستودع
git clone https://github.com/fortestaccountQ/velocity-3d-engine.git
cd velocity-3d-engine

# تثبيت متطلبات البناء
pip install scikit-build-core nanobind ninja pytest numpy

# ترجمة نواة C++ وتثبيت روابط بايثون
pip install -e . --no-build-isolation
```

### 2. البناء المباشر عبر CMake

```powershell
cmake -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### 3. تشغيل الاختبارات المؤتمتة

```powershell
pytest tests -q
```

---

## 💡 مثال البدء السريع

```python
import VelocityEngine as ve

# 1. تهيئة التطبيق
app = ve.App(
    title="Velocity 3D Engine - Quickstart",
    width=1280,
    height=720,
    clear_color=(0.08, 0.09, 0.12, 1.0)
)

# 2. إعداد الكاميرا
camera = app.camera
camera.set_position(0.0, 2.0, 5.0)
camera.look_at(ve.Vec3(0.0, 0.5, 0.0))

# 3. إضافة إضاءة اتجاهية ومحيطية
app.scene.set_ambient_light(ve.Vec3(0.05, 0.05, 0.07))
sun = ve.DirectionalLight(
    color=ve.Vec3(1.0, 0.95, 0.8),
    intensity=2.5,
    direction=ve.Vec3(-0.5, -1.0, -0.5)
)
app.scene.add_light(sun)

# 4. إنشاء مادة PBR وشبكة هندسية
mat = ve.StandardMaterial()
mat.base_color = ve.Vec4(0.9, 0.2, 0.2, 1.0)
mat.roughness = 0.25
mat.metallic = 0.8

mesh = ve.Mesh.create_sphere(radius=1.0, rings=32, sectors=32)
entity = ve.Entity(mesh=mesh, material=mat)
app.scene.add_entity(entity)

# 5. تشغيل حلقة التطبيق
app.run()
```

---

## 🗺️ خطة التطوير والقيود المعروفة

نظراً لكون المشروع في مرحلة ألفا المبكرة، فإنه من المخطط تنفيذ العديد من التحسينات المعمارية الرئيسية:

- [ ] **التدبيج الحسابي عبر معالج الرسومات (GPU Compute Skinning)**: الانتقال من التدبيج الخطي الحالي على وحدة المعالجة المركزية (CPU) إلى المعالجة عبر مظلل الرؤوس/المظلل الحسابي لوحدة معالجة الرسومات لدعم أعداد هائلة من الشبكات الهيكلية.
- [ ] **خرائط الظلال المتتالية (CSM)**: دعم التتالي الاتجاهي متعدد الأهرامات (multi-frustum) للمشاهد الخارجية في العوالم المفتوحة.
- [ ] **الترجمة المتقاطعة للمظللات (Shader Cross-Compilation)**: إضفاء الطابع الرسمي على الترجمة التلقائية دون اتصال بالإنترنت لـ GLSL/HLSL/MSL عبر `sokol-shdc`.
- [ ] **دمج محرك الفيزياء**: دمج Jolt Physics أو PhysX لمحاكاة الأجسام الصلبة والاستجابة للتصادمات.
- [ ] **واجهات Vulkan و WebGPU الخلفية**: إضافة أهداف Vulkan و WebAssembly/WebGPU باستخدام Sokol GFX.

---

## 📄 الترخيص

هذا المشروع مرخص بموجب [رخصة MIT](../LICENSE).
تخضع مكتبات الطرف الثالث الموجودة في [`third_party/`](../third_party/) لتراخيص المصدر المفتوح الخاصة بكل منها (Sokol: zlib/libpng، و GLM: Happy Bunny / MIT، و ImGui: MIT، و miniaudio: Public Domain / MIT-0).
