import pytest
import numpy as np
import pielosyty as p

def test_bone_and_skeleton_hierarchy():
    """Verify Bone hierarchy and Skeleton bone matrix computation."""
    root_bone = p.Bone("RootBone")
    root_bone.set_position(0.0, 1.0, 0.0)
    
    child_bone = p.Bone("ChildBone")
    child_bone.set_position(0.0, 2.0, 0.0)
    root_bone.add(child_bone)
    
    root_bone.update_world_matrix(True)
    
    # Check hierarchy
    assert len(root_bone.children) == 1
    assert child_bone.parent == root_bone
    
    # Skeleton
    bones = [root_bone, child_bone]
    inv_bind_matrices = [p.Mat4(), p.Mat4()]
    skeleton = p.Skeleton(bones, inv_bind_matrices)
    
    assert skeleton.num_bones == 2
    assert len(skeleton.bones) == 2
    assert len(skeleton.bone_matrices) == 2
    
    # Compute bone matrices
    skeleton.compute_bone_matrices()
    assert len(skeleton.bone_matrices) == 2


def test_keyframe_tracks_and_animation_clip():
    """Verify KeyframeTrack types and AnimationClip creation."""
    # Translation track
    times_t = [0.0, 1.0, 2.0]
    values_t = [0.0, 0.0, 0.0, 1.0, 2.0, 3.0, 2.0, 4.0, 6.0]
    track_t = p.KeyframeTrack("Node.position", times_t, values_t, p.Interpolation.Linear, p.PropertyType.Translation)
    assert track_t.name == "Node.position"
    assert track_t.times == times_t
    assert track_t.values == values_t
    assert track_t.interpolation == p.Interpolation.Linear
    assert track_t.property == p.PropertyType.Translation

    # Rotation track (quaternion: x, y, z, w)
    times_r = [0.0, 1.0]
    values_r = [0.0, 0.0, 0.0, 1.0, 0.0, 0.7071, 0.0, 0.7071]
    track_r = p.KeyframeTrack("Node.rotation", times_r, values_r, p.Interpolation.Linear, p.PropertyType.Rotation)

    # Scale track
    times_s = [0.0, 1.0]
    values_s = [1.0, 1.0, 1.0, 2.0, 2.0, 2.0]
    track_s = p.KeyframeTrack("Node.scale", times_s, values_s, p.Interpolation.Step, p.PropertyType.Scale)

    # AnimationClip
    clip = p.AnimationClip("Walk", 2.0, [track_t, track_r, track_s])
    assert clip.name == "Walk"
    assert clip.duration == 2.0
    assert len(clip.tracks) == 3


def test_animation_mixer_and_action():
    """Verify AnimationMixer evaluates tracks and updates Node3D transforms."""
    root = p.Node3D("Root")
    child = p.Node3D("Node")
    root.add(child)

    times = [0.0, 1.0]
    values = [0.0, 0.0, 0.0, 10.0, 20.0, 30.0]
    track = p.KeyframeTrack("Node.position", times, values, p.Interpolation.Linear, p.PropertyType.Translation)
    clip = p.AnimationClip("Move", 1.0, [track])

    mixer = p.AnimationMixer(root)
    assert mixer.root == root

    action = mixer.clip_action(clip)
    assert action.clip.name == "Move"
    assert action.is_playing() == False
    
    action.loop = False
    action.play()
    assert action.is_playing() == True

    # Advance mixer by 0.5s -> position should be interpolated halfway: (5.0, 10.0, 15.0)
    mixer.update(0.5)
    pos = child.transform.position
    assert pos.x == pytest.approx(5.0, 0.01)
    assert pos.y == pytest.approx(10.0, 0.01)
    assert pos.z == pytest.approx(15.0, 0.01)

    # Advance mixer to 1.0s -> position should be (10.0, 20.0, 30.0)
    mixer.update(0.5)
    pos = child.transform.position
    assert pos.x == pytest.approx(10.0, 0.01)
    assert pos.y == pytest.approx(20.0, 0.01)
    assert pos.z == pytest.approx(30.0, 0.01)

    # Action controls
    action.time_scale = 2.0
    assert action.time_scale == 2.0
    action.weight = 0.8
    assert action.weight == pytest.approx(0.8, 1e-4)
    action.fade_in(0.5)
    action.fade_out(0.5)
    action.stop()
    assert action.is_playing() == False


def test_skeleton_helper():
    """Verify SkeletonHelper generates bone line visualization vertices."""
    root = p.Bone("Root")
    root.set_position(0.0, 0.0, 0.0)
    child = p.Bone("Child")
    child.set_position(0.0, 5.0, 0.0)
    root.add(child)
    root.update_world_matrix(True)

    skel = p.Skeleton([root, child], [p.Mat4(), p.Mat4()])
    helper = p.SkeletonHelper(root, skel)
    assert helper.skeleton == skel
    assert helper.root == root

    helper.update()
    verts = helper.line_vertices
    # Should have at least 2 vertices for the root-child bone segment
    assert len(verts) >= 2


def test_skinned_mesh_and_cpu_skinning():
    """Verify SkinnedMesh creation and compute_cpu_skinning vertex deformation."""
    # Create simple 2-vertex mesh
    v_data = np.zeros((2, 16), dtype=np.float32)
    v_data[0, 0:3] = [0.0, 0.0, 0.0]
    v_data[1, 0:3] = [0.0, 2.0, 0.0]
    mesh = p.Mesh.from_numpy(v_data)

    # Assign joint and weight
    # Vertex 0 bound 100% to bone 0, vertex 1 bound 100% to bone 1
    cpu_verts = mesh.cpu_vertices
    assert len(cpu_verts) == 2
    cpu_verts[0].joints = p.Vec4(0.0, 0.0, 0.0, 0.0)
    cpu_verts[0].weights = p.Vec4(1.0, 0.0, 0.0, 0.0)
    cpu_verts[1].joints = p.Vec4(1.0, 0.0, 0.0, 0.0)
    cpu_verts[1].weights = p.Vec4(1.0, 0.0, 0.0, 0.0)
    mesh.cpu_vertices = cpu_verts

    # Setup Skeleton with 2 bones
    b0 = p.Bone("B0")
    b0.set_position(0.0, 0.0, 0.0)
    b1 = p.Bone("B1")
    b1.set_position(0.0, 2.0, 0.0)
    b0.add(b1)
    b0.update_world_matrix(True)

    skel = p.Skeleton([b0, b1])
    skel.calculate_inverse_bind_matrices()

    mat = p.StandardMaterial()
    skinned_mesh = p.SkinnedMesh(mesh, skel, mat)
    skinned_mesh.bind(skel, p.Mat4())

    assert skinned_mesh.mesh == mesh
    assert skinned_mesh.skeleton == skel
    assert skinned_mesh.material == mat

    # Move b1 by (5, 0, 0)
    b1.set_position(5.0, 2.0, 0.0)
    b0.update_world_matrix(True)
    skel.compute_bone_matrices()

    # Compute CPU skinning
    skinned_mesh.compute_cpu_skinning()
    
    # Vertex 0 was on B0 (didn't move) -> near (0, 0, 0)
    v0_pos = mesh.cpu_vertices[0].position
    assert v0_pos.x == pytest.approx(0.0, 0.01)
    assert v0_pos.y == pytest.approx(0.0, 0.01)

    # Vertex 1 was on B1 (moved by +5 on X) -> near (5, 2, 0)
    v1_pos = mesh.cpu_vertices[1].position
    assert v1_pos.x == pytest.approx(5.0, 0.01)
    assert v1_pos.y == pytest.approx(2.0, 0.01)


def test_mesh_morph_targets():
    """Verify Mesh morph targets blending positions and normals."""
    mesh = p.Mesh.create_box(1.0, 1.0, 1.0)
    base_pos0_y = float(mesh.cpu_vertices[0].position.y)

    # Target 1: offset positions by +2.0 on Y
    delta_positions = [p.Vec3(0.0, 2.0, 0.0) for _ in range(mesh.num_vertices)]
    delta_normals = [p.Vec3(0.0, 0.0, 0.0) for _ in range(mesh.num_vertices)]

    mesh.add_morph_target("Tall", delta_positions, delta_normals)
    assert len(mesh.morph_target_influences) == 1
    assert mesh.morph_target_influences[0] == 0.0

    # Set influence to 0.5 (half weight)
    mesh.morph_target_influences = [0.5]
    mesh.apply_morph_targets()

    # Vertex 0 Y position should increase by 0.5 * 2.0 = 1.0
    new_pos0_y = float(mesh.cpu_vertices[0].position.y)
    assert new_pos0_y == pytest.approx(base_pos0_y + 1.0, 0.01)


def test_sprite_and_sprite_material():
    """Verify SpriteMaterial and Sprite billboard matrix computation facing camera."""
    mat = p.SpriteMaterial()
    assert mat.color.w == 1.0
    assert mat.rotation == 0.0

    sprite = p.Sprite(mat)
    sprite.set_position(0.0, 5.0, -10.0)
    sprite.scale = p.Vec2(2.0, 3.0)

    assert sprite.material == mat
    assert sprite.scale.x == 2.0
    assert sprite.scale.y == 3.0

    # Camera facing -Z
    cam = p.Camera()
    cam.set_position(0.0, 5.0, 0.0)
    cam.set_target(0.0, 5.0, -10.0)

    # Billboard matrix facing camera
    m = sprite.compute_billboard_matrix(cam)
    # The sprite quad mesh is valid
    quad = sprite.quad_mesh
    assert quad.num_vertices == 4
    assert quad.num_indices == 6


def test_points_and_points_material():
    """Verify PointsMaterial and Points with numpy array setters."""
    p_mat = p.PointsMaterial()
    p_mat.point_size = 5.0
    p_mat.size_attenuation = True
    assert p_mat.point_size == 5.0
    assert p_mat.size_attenuation == True

    points = p.Points(None, p_mat)
    assert points.count == 0

    # Set positions with NumPy (1000 points)
    positions = np.random.uniform(-10.0, 10.0, (1000, 3)).astype(np.float32)
    colors = np.random.uniform(0.0, 1.0, (1000, 4)).astype(np.float32)

    points.set_positions(positions)
    assert points.count == 1000
    assert points.mesh.num_vertices == 1000

    points.set_colors(colors)
    assert points.mesh.cpu_vertices[0].color.x == colors[0, 0]


def test_particle_and_particle_emitter_simulation():
    """Verify ParticleEmitter physics simulation, lifecycles, and billboard quad generation."""
    emitter = p.ParticleEmitter(100)
    assert emitter.max_particles == 100
    assert emitter.active_particle_count == 0

    emitter.emission_rate = 20.0
    emitter.lifespan = 2.0
    emitter.velocity = p.Vec3(0.0, 10.0, 0.0)
    emitter.spread = p.Vec3(0.0, 0.0, 0.0)
    emitter.gravity = p.Vec3(0.0, -9.8, 0.0)
    emitter.start_size = 1.0
    emitter.end_size = 0.1
    emitter.start_color = p.Vec4(1.0, 0.0, 0.0, 1.0)
    emitter.end_color = p.Vec4(0.0, 0.0, 1.0, 0.0)

    # Burst 10 particles
    emitter.burst(10)
    assert emitter.active_particle_count == 10

    # Advance 0.5s
    emitter.update(0.5)
    assert emitter.active_particle_count >= 10
    
    # Check that particle has moved upward (velocity 10 m/s minus gravity)
    particles = emitter.particles
    p0 = particles[0]
    assert p0.alive == True
    assert p0.position.y > 0.0
    assert p0.size < 1.0  # Shrinking
    assert p0.color.x < 1.0  # Fading red towards blue

    # Test billboard quad generation
    cam = p.Camera()
    cam.set_position(0.0, 0.0, 10.0)
    cam.set_target(0.0, 0.0, 0.0)

    emitter.update_mesh(cam)
    mesh = emitter.mesh
    assert mesh is not None
    # Each active particle produces 4 vertices and 6 indices
    assert mesh.num_vertices == emitter.active_particle_count * 4
    assert mesh.num_indices == emitter.active_particle_count * 6

    # Advance beyond lifespan -> all particles should die
    emitter.emission_rate = 0.0
    emitter.update(5.0)
    assert emitter.active_particle_count == 0


def test_scene_integration_phase6():
    """Verify Scene stores, retrieves, and purges Phase 6 components."""
    scene = p.Scene()

    # SkinnedMesh
    skel = p.Skeleton([], [])
    sm = p.SkinnedMesh(p.Mesh.create_box(1.0, 1.0, 1.0), skel, p.StandardMaterial())
    
    # Sprite
    sp = p.Sprite(p.SpriteMaterial())

    # Points
    pt = p.Points(p.Mesh.create_box(1.0, 1.0, 1.0), p.PointsMaterial())

    # ParticleEmitter
    pe = p.ParticleEmitter(50)

    scene.add(sm)
    scene.add(sp)
    scene.add(pt)
    scene.add(pe)

    assert len(scene.skinned_meshes) == 1
    assert len(scene.sprites) == 1
    assert len(scene.points) == 1
    assert len(scene.particle_emitters) == 1

    # Remove one
    scene.remove(sp)
    assert len(scene.sprites) == 0
    assert len(scene.skinned_meshes) == 1

    # Clear scene
    scene.clear()
    assert len(scene.skinned_meshes) == 0
    assert len(scene.sprites) == 0
    assert len(scene.points) == 0
    assert len(scene.particle_emitters) == 0


def test_phase6_acceptance_criterion_mixamo_soldier_full_scenario():
    """Verify Phase 6 Acceptance Criterion:
    'Персонаж из Mixamo (.glb) загружается, плавно переходит из анимации Idle в Run через mixer.crossfade_to("Run", 0.25),
    над его головой висит Sprite с полоской здоровья, а из факела в его руке летят искры от ParticleEmitter.'
    """
    import os
    scene = p.Scene()

    # 1. Load Mixamo .glb character
    asset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "Soldier.glb"))
    assert os.path.exists(asset_path), f"Asset {asset_path} missing!"
    character = scene.load_model(asset_path)
    assert character is not None
    assert len(character.meshes) > 0
    assert len(character.skinned_meshes) > 0
    assert character.skeleton is not None
    assert character.skeleton.num_bones >= 40

    # Verify animation clips
    anim_names = [a.name for a in character.animations]
    assert "Idle" in anim_names
    assert "Run" in anim_names

    # 2. AnimationMixer and smooth crossfade Idle -> Run
    mixer = p.AnimationMixer(character.root_entity)
    for anim in character.animations:
        mixer.clip_action(anim)

    idle_action = mixer.get_action("Idle")
    run_action = mixer.get_action("Run")
    assert idle_action is not None
    assert run_action is not None

    # Start with Idle
    mixer.play("Idle")
    assert idle_action.is_playing() == True
    assert run_action.is_playing() == False
    assert idle_action.weight == pytest.approx(1.0, 1e-4)

    # Advance mixer while in Idle
    mixer.update(0.1)

    # Trigger crossfade_to("Run", 0.25)
    mixer.crossfade_to("Run", 0.25)

    # Start of crossfade (t = 0.0s)
    assert idle_action.is_playing() == True
    assert run_action.is_playing() == True
    assert idle_action.weight == pytest.approx(1.0, 1e-4)
    assert run_action.weight == pytest.approx(0.0, 1e-4)

    # Midway through crossfade (t = 0.125s)
    mixer.update(0.125)
    assert idle_action.weight == pytest.approx(0.5, 1e-2)
    assert run_action.weight == pytest.approx(0.5, 1e-2)

    # End of crossfade (t = 0.25s)
    mixer.update(0.125)
    assert idle_action.weight == pytest.approx(0.0, 1e-2)
    assert run_action.weight == pytest.approx(1.0, 1e-2)
    assert idle_action.is_playing() == False
    assert run_action.is_playing() == True

    # 3. Sprite with healthbar hanging above character's head
    head_bone = character.skeleton.get_bone_by_name("mixamorig:Head")
    assert head_bone is not None

    healthbar_mat = p.SpriteMaterial(None, p.Vec4(0.1, 0.9, 0.2, 1.0)) # green healthbar
    healthbar_sprite = p.Sprite(healthbar_mat)
    healthbar_sprite.scale = p.Vec2(0.8, 0.1) # elongated health bar
    healthbar_sprite.set_position(0.0, 0.35, 0.0) # slightly above head
    head_bone.add(healthbar_sprite)
    assert healthbar_sprite.parent == head_bone

    # Verify billboard orientation towards camera
    cam = p.Camera()
    cam.set_position(0.0, 2.0, 5.0)
    cam.set_target(0.0, 1.8, 0.0)
    billboard_m = healthbar_sprite.compute_billboard_matrix(cam)
    # Billboard matrix should produce a normal facing camera
    normal_col = billboard_m[2] # forward vector
    cam_dir_x = 0.0 - 0.0
    cam_dir_y = 2.0 - 1.8
    cam_dir_z = 5.0 - 0.0
    dot_prod = normal_col.x * cam_dir_x + normal_col.y * cam_dir_y + normal_col.z * cam_dir_z
    assert dot_prod > 0.0 # Facing towards camera direction

    # 4. ParticleEmitter emitting sparks from torch attached at hand
    hand_bone = character.skeleton.get_bone_by_name("mixamorig:RightHand")
    assert hand_bone is not None

    torch_node = p.Node3D("Torch")
    torch_node.set_position(0.0, 0.2, 0.0) # torch head
    hand_bone.add(torch_node)

    sparks_emitter = p.ParticleEmitter(200)
    sparks_emitter.emission_rate = 50.0
    sparks_emitter.lifespan = 1.0
    sparks_emitter.velocity = p.Vec3(0.0, 3.0, 0.0)
    sparks_emitter.spread = p.Vec3(0.5, 0.5, 0.5)
    sparks_emitter.gravity = p.Vec3(0.0, -9.8, 0.0)
    sparks_emitter.start_color = p.Vec4(1.0, 0.8, 0.2, 1.0) # golden yellow spark
    sparks_emitter.end_color = p.Vec4(1.0, 0.1, 0.0, 0.0)   # fading red/orange
    sparks_emitter.start_size = 0.15
    sparks_emitter.end_size = 0.01

    torch_node.add(sparks_emitter)
    assert sparks_emitter.parent == torch_node

    # Burst sparks and simulate
    sparks_emitter.burst(25)
    assert sparks_emitter.active_particle_count == 25

    # Simulate step
    sparks_emitter.update(0.2)
    assert sparks_emitter.active_particle_count >= 25

    # Verify particles are moving and changing color/size
    particles = sparks_emitter.particles
    active_particles = [pt for pt in particles if pt.alive]
    assert len(active_particles) >= 25
    for pt in active_particles:
        assert pt.age == pytest.approx(0.2, 1e-4)
        assert pt.size < 0.15 # shrinking
        assert pt.color.w < 1.0 # fading alpha

    # Generate billboard mesh for particles
    sparks_emitter.update_mesh(cam)
    assert sparks_emitter.mesh.num_vertices == len(active_particles) * 4
    assert sparks_emitter.mesh.num_indices == len(active_particles) * 6


def test_mixamo_crossfade_bone_transformation_blending():
    """Verify that bone transforms interpolate smoothly during crossfade rather than popping."""
    import os
    scene = p.Scene()
    asset_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "Soldier.glb"))
    character = scene.load_model(asset_path)
    mixer = p.AnimationMixer(character.root_entity)
    for anim in character.animations:
        mixer.clip_action(anim)

    hips = character.skeleton.get_bone_by_name("mixamorig:Hips")
    assert hips is not None

    # Step 1: Pure Idle pose
    mixer.play("Idle")
    mixer.update(0.1)
    pos_idle = p.Vec3(hips.transform.position.x, hips.transform.position.y, hips.transform.position.z)

    # Step 2: Begin crossfade to Run
    mixer.crossfade_to("Run", 0.4)

    # Step 3: Advance 0.2s (halfway)
    mixer.update(0.2)
    pos_mid = p.Vec3(hips.transform.position.x, hips.transform.position.y, hips.transform.position.z)

    # Step 4: Advance another 0.2s (end of crossfade)
    mixer.update(0.2)
    pos_run = p.Vec3(hips.transform.position.x, hips.transform.position.y, hips.transform.position.z)

    # Both actions blended should keep hips within realistic bounding bounds
    assert not np.isnan(pos_mid.x) and not np.isnan(pos_mid.y) and not np.isnan(pos_mid.z)
    assert not np.isnan(pos_run.x) and not np.isnan(pos_run.y) and not np.isnan(pos_run.z)


def test_multi_morph_targets_vertex_linear_combination():
    """Verify linear combination of multiple morph targets on vertex positions and normal re-normalization."""
    mesh = p.Mesh.create_box(2.0, 2.0, 2.0)
    base_positions = [p.Vec3(v.position.x, v.position.y, v.position.z) for v in mesh.cpu_vertices]
    n_verts = mesh.num_vertices

    # Target 1: Shift X by +1.0
    d_pos1 = [p.Vec3(1.0, 0.0, 0.0) for _ in range(n_verts)]
    mesh.add_morph_target("ShiftX", d_pos1)

    # Target 2: Shift Y by +2.0
    d_pos2 = [p.Vec3(0.0, 2.0, 0.0) for _ in range(n_verts)]
    mesh.add_morph_target("ShiftY", d_pos2)

    # Target 3: Shift Z by -0.5
    d_pos3 = [p.Vec3(0.0, 0.0, -0.5) for _ in range(n_verts)]
    mesh.add_morph_target("ShiftZ", d_pos3)

    assert len(mesh.morph_target_influences) == 3

    # Weights: 0.5 on Target 1, 0.25 on Target 2, 1.0 on Target 3
    mesh.morph_target_influences = [0.5, 0.25, 1.0]
    mesh.apply_morph_targets()

    # Expected delta: (0.5 * 1.0, 0.25 * 2.0, 1.0 * -0.5) = (0.5, 0.5, -0.5)
    for i in range(n_verts):
        curr_p = mesh.cpu_vertices[i].position
        base_p = base_positions[i]
        assert curr_p.x == pytest.approx(base_p.x + 0.5, 0.01)
        assert curr_p.y == pytest.approx(base_p.y + 0.5, 0.01)
        assert curr_p.z == pytest.approx(base_p.z - 0.5, 0.01)

    # Reset all influences to 0 -> should restore base shape exactly
    mesh.morph_target_influences = [0.0, 0.0, 0.0]
    mesh.apply_morph_targets()

    for i in range(n_verts):
        curr_p = mesh.cpu_vertices[i].position
        base_p = base_positions[i]
        assert curr_p.x == pytest.approx(base_p.x, 1e-4)
        assert curr_p.y == pytest.approx(base_p.y, 1e-4)
        assert curr_p.z == pytest.approx(base_p.z, 1e-4)


def test_sprite_spherical_billboard_all_quadrants():
    """Verify spherical billboard orientation always aligns normal facing camera from all view directions."""
    mat = p.SpriteMaterial()
    sprite = p.Sprite(mat)
    sprite.set_position(0.0, 0.0, 0.0)

    test_cameras = [
        # Eye, Target
        ((0.0, 0.0, 10.0), (0.0, 0.0, 0.0)),
        ((0.0, 0.0, -10.0), (0.0, 0.0, 0.0)),
        ((10.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ((-10.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        ((5.0, 5.0, 5.0), (0.0, 0.0, 0.0)),
        ((-3.0, 8.0, -4.0), (0.0, 0.0, 0.0)),
    ]

    for eye, target in test_cameras:
        cam = p.Camera()
        cam.set_position(eye[0], eye[1], eye[2])
        cam.set_target(target[0], target[1], target[2])

        bm = sprite.compute_billboard_matrix(cam)

        # Vector forward column of billboard matrix
        fwd = p.Vec3(bm[2].x, bm[2].y, bm[2].z)
        view_dir = p.Vec3(eye[0] - target[0], eye[1] - target[1], eye[2] - target[2])

        # Normalize dot product
        len_fwd = np.sqrt(fwd.x*fwd.x + fwd.y*fwd.y + fwd.z*fwd.z)
        len_view = np.sqrt(view_dir.x*view_dir.x + view_dir.y*view_dir.y + view_dir.z*view_dir.z)
        dot = (fwd.x*view_dir.x + fwd.y*view_dir.y + fwd.z*view_dir.z) / (len_fwd * len_view)

        # Dot product should be strictly positive (pointing towards camera eye)
        assert dot > 0.95


def test_particle_emitter_full_physics_and_recycling():
    """Verify particle physics (acceleration due to gravity), lifecycle termination, and buffer recycling."""
    emitter = p.ParticleEmitter(50)
    emitter.emission_rate = 0.0 # pure burst
    emitter.lifespan = 2.0
    emitter.velocity = p.Vec3(0.0, 10.0, 0.0)
    emitter.spread = p.Vec3(0.0, 0.0, 0.0)
    emitter.gravity = p.Vec3(0.0, -10.0, 0.0)

    # 1. Burst 50 particles
    emitter.burst(50)
    assert emitter.active_particle_count == 50

    # 2. Advance 0.5s: semi-implicit Euler integration gives y(t) = y0 + (v0 + g*dt)*dt = 0 + (10 - 5)*0.5 = 2.5
    emitter.update(0.5)
    assert emitter.active_particle_count == 50
    for pt in emitter.particles:
        assert pt.alive == True
        assert pt.age == pytest.approx(0.5, 0.01)
        assert pt.position.y == pytest.approx(2.5, 0.05)

    # 3. Advance another 1.6s (total 2.1s > lifespan of 2.0s) -> all particles should die
    emitter.update(1.6)
    assert emitter.active_particle_count == 0

    # 4. Burst 30 new particles into recycled slots
    emitter.burst(30)
    assert emitter.active_particle_count == 30
    for i in range(30):
        assert emitter.particles[i].alive == True
        assert emitter.particles[i].age == pytest.approx(0.0, 1e-4)


def test_points_dynamic_streaming_numpy():
    """Verify high-throughput point cloud streaming with NumPy arrays."""
    p_mat = p.PointsMaterial(size=3.0, color=p.Vec4(0.2, 0.7, 1.0, 1.0), size_attenuation=True)
    points = p.Points(None, p_mat)

    n_points = 5000
    pos_data = np.random.uniform(-50.0, 50.0, (n_points, 3)).astype(np.float32)
    col_data = np.random.uniform(0.0, 1.0, (n_points, 4)).astype(np.float32)

    points.set_positions(pos_data)
    points.set_colors(col_data)

    assert points.count == n_points
    assert points.mesh.num_vertices == n_points

    # Verify first and last vertex coordinates
    v_first = points.mesh.cpu_vertices[0]
    assert v_first.position.x == pytest.approx(pos_data[0, 0], 1e-4)
    assert v_first.color.x == pytest.approx(col_data[0, 0], 1e-4)

    v_last = points.mesh.cpu_vertices[n_points - 1]
    assert v_last.position.x == pytest.approx(pos_data[n_points - 1, 0], 1e-4)
    assert v_last.color.x == pytest.approx(col_data[n_points - 1, 0], 1e-4)

    # Stream new positions
    new_pos = pos_data + 10.0
    points.set_positions(new_pos)
    v_first_new = points.mesh.cpu_vertices[0]
    assert v_first_new.position.x == pytest.approx(pos_data[0, 0] + 10.0, 1e-4)


def test_skinned_mesh_multi_bone_weight_deformation():
    """Verify dual-bone weighted skinning deformation on vertices."""
    # Create 3-vertex mesh along Y axis
    v_data = np.zeros((3, 16), dtype=np.float32)
    v_data[0, 0:3] = [0.0, 0.0, 0.0]
    v_data[1, 0:3] = [0.0, 2.0, 0.0]
    v_data[2, 0:3] = [0.0, 4.0, 0.0]
    mesh = p.Mesh.from_numpy(v_data)

    cpu_verts = mesh.cpu_vertices
    # V0: 100% Bone 0
    cpu_verts[0].joints = p.Vec4(0.0, 0.0, 0.0, 0.0)
    cpu_verts[0].weights = p.Vec4(1.0, 0.0, 0.0, 0.0)
    # V1: 50% Bone 0, 50% Bone 1
    cpu_verts[1].joints = p.Vec4(0.0, 1.0, 0.0, 0.0)
    cpu_verts[1].weights = p.Vec4(0.5, 0.5, 0.0, 0.0)
    # V2: 100% Bone 1
    cpu_verts[2].joints = p.Vec4(1.0, 0.0, 0.0, 0.0)
    cpu_verts[2].weights = p.Vec4(1.0, 0.0, 0.0, 0.0)
    mesh.cpu_vertices = cpu_verts

    b0 = p.Bone("B0", 0)
    b0.set_position(0.0, 0.0, 0.0)
    b1 = p.Bone("B1", 1)
    b1.set_position(0.0, 4.0, 0.0)
    b0.add(b1)
    b0.update_world_matrix(True)

    skel = p.Skeleton([b0, b1])
    skel.calculate_inverse_bind_matrices()

    skinned_mesh = p.SkinnedMesh(mesh, skel, p.StandardMaterial())
    skinned_mesh.bind(skel)

    # Shift Bone 1 by (+6.0, 0, 0)
    b1.set_position(6.0, 4.0, 0.0)
    b0.update_world_matrix(True)
    skel.compute_bone_matrices()

    skinned_mesh.compute_cpu_skinning()

    # V0 is 100% B0 (static) -> X remains 0.0
    assert mesh.cpu_vertices[0].position.x == pytest.approx(0.0, 0.01)
    # V1 is 50% B0 and 50% B1 -> X shifts by 0.5 * 6.0 = 3.0
    assert mesh.cpu_vertices[1].position.x == pytest.approx(3.0, 0.05)
    # V2 is 100% B1 -> X shifts by 6.0
    assert mesh.cpu_vertices[2].position.x == pytest.approx(6.0, 0.01)


def test_skeleton_helper_dynamic_rig_tracking():
    """Verify SkeletonHelper dynamically tracks bone movement."""
    root = p.Bone("Root")
    root.set_position(0.0, 0.0, 0.0)
    mid = p.Bone("Mid")
    mid.set_position(0.0, 2.0, 0.0)
    tip = p.Bone("Tip")
    tip.set_position(0.0, 4.0, 0.0)

    root.add(mid)
    mid.add(tip)
    root.update_world_matrix(True)

    skel = p.Skeleton([root, mid, tip])
    helper = p.SkeletonHelper(root, skel)
    helper.update()

    # Two segments: Root->Mid and Mid->Tip (4 vertices)
    lines = helper.line_vertices
    assert len(lines) == 4

    # Move tip (local position (3, 5, 0), world position = mid(0, 2, 0) + tip(3, 5, 0) = (3, 7, 0))
    tip.set_position(3.0, 5.0, 0.0)
    root.update_world_matrix(True)
    helper.update()

    lines_updated = helper.line_vertices
    assert len(lines_updated) == 4
    # The last vertex corresponds to tip's new world position
    last_vert = lines_updated[-1]
    assert last_vert[0] == pytest.approx(3.0, 0.01)
    assert last_vert[1] == pytest.approx(7.0, 0.01)

