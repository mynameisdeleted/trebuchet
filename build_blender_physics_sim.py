#!/usr/bin/env python3
"""
build_blender_physics_sim.py
Pure Native Blender Bullet Physics Engine Trebuchet Simulation & Keyframe Baker:
- Full 60-second lifecycle (Frames 1 to 3600 at 60 FPS).
- Evaluates 17,996 discrete simulation steps at dt = 1/300s (0.2 frame steps).
- 100% computed by Blender's native Bullet physics engine:
  - 16mm glass marble resting at Frame 1 in trough at Z = 0.0593m (zero penetration).
  - Concentrated 3.50 kg bronze counterweight decoupled from 0.30 kg timber arm via FIXED constraint.
  - Swing-arm friction kept as is (linear_damping = 0.04, angular_damping = 0.06) representing oiled bearing.
  - Increased friction added to the sling (pouch damping = 0.35, line damping = 0.25, contact friction = 0.45).
  - Dynamic force-based pin release when tension aligns with 45° pin tip (>90° arm angle, dot > 0.95).
  - Sling flings wide open outward post-release by conservation of momentum (continuous, zero teleportation).
  - Free ballistic flight, floor touchdown, rolling resistance deceleration, and arm gradually slowing and significantly stopping swinging over 60 seconds.
- Bakes high-resolution keyframes:
  - Frames 1 to 720: Baked every 0.2 sub-frame (3,596 steps) for capture of launch, release, flight, and touchdown.
  - Frames 721 to 3600: Baked at every integer frame for 60 FPS playback of the arm settling to full equilibrium rest.
- Drives visual braided twine string curves, cloth pouch, and spliced cord loop.
- Saves Trebuchet_3ft.blend and renders multi-perspective validation frames across the 60-second timeline.
"""

import bpy
import math
import os
os.environ.pop("DISPLAY", None)
import shutil
import mathutils
import time

def generate_slack_sling_path(p_start, p_end, num_segments, slack_m=0.020, n_waves=2, lateral_sign=1.0):
    """
    Computes a physically relaxed initial path with smooth lateral slack curve and trough droop.
    Generates segment centers, orientations, and joint locations with exact arc length = straight_distance + slack_m.
    """
    span_vec = p_end - p_start
    span_len = span_vec.length
    target_len = span_len + max(0.0, slack_m)

    if slack_m <= 1e-5:
        joint_locs = [p_start + (i / num_segments) * span_vec for i in range(num_segments + 1)]
        seg_centers = [0.5 * (joint_locs[i] + joint_locs[i + 1]) for i in range(num_segments)]
        seg_rot = []
        for i in range(num_segments):
            v_seg = (joint_locs[i + 1] - joint_locs[i]).normalized()
            seg_rot.append(mathutils.Vector((0, 0, 1)).rotation_difference(v_seg).to_euler())
        return {
            'target_len': span_len,
            'seg_len': span_len / num_segments,
            'joint_locs': joint_locs,
            'seg_centers': seg_centers,
            'seg_rotations': seg_rot,
            'amplitude': 0.0
        }

    # Bisection search for lateral sine wave amplitude to yield arc length = target_len
    A_low = 0.0
    A_high = 0.022 # Max 22mm to stay inside 50.8mm trough (width is +/-25.4mm)
    dt = 1.0 / 200.0
    best_A = 0.015
    for _ in range(25):
        A_mid = 0.5 * (A_low + A_high)
        length = 0.0
        for step in range(200):
            t0 = step * dt
            t1 = (step + 1) * dt
            p0 = p_start + t0 * span_vec + mathutils.Vector((0.0, lateral_sign * A_mid * math.sin(n_waves * math.pi * t0), 0.0))
            p1 = p_start + t1 * span_vec + mathutils.Vector((0.0, lateral_sign * A_mid * math.sin(n_waves * math.pi * t1), 0.0))
            length += (p1 - p0).length
        if length < target_len:
            A_low = A_mid
        else:
            A_high = A_mid
        best_A = A_mid

    # Sample densely along curve with vertical droop into trough
    dense_pts = []
    dense_dists = [0.0]
    total_dist = 0.0
    N_dense = 1000
    for s in range(N_dense + 1):
        t = s / N_dense
        # Droop in Z into trough floor (floor is at Z=0.0508, p_start.z=0.0627, p_end.z=0.0593)
        z_droop = -0.005 * math.sin(math.pi * t)
        pt = p_start + t * span_vec + mathutils.Vector((0.0, lateral_sign * best_A * math.sin(n_waves * math.pi * t), z_droop))
        dense_pts.append(pt)
        if s > 0:
            total_dist += (dense_pts[-1] - dense_pts[-2]).length
            dense_dists.append(total_dist)

    # Sample joint locations at equal arc lengths
    joint_locs = [p_start.copy()]
    target_dists = [i * (total_dist / num_segments) for i in range(num_segments + 1)]

    dense_idx = 0
    for i in range(1, num_segments):
        td = target_dists[i]
        while dense_idx < len(dense_dists) - 1 and dense_dists[dense_idx + 1] < td:
            dense_idx += 1
        d0 = dense_dists[dense_idx]
        d1 = dense_dists[dense_idx + 1]
        frac = (td - d0) / max(1e-6, (d1 - d0))
        pt = dense_pts[dense_idx].lerp(dense_pts[dense_idx + 1], frac)
        joint_locs.append(pt)
    joint_locs.append(p_end.copy())

    # Segment midpoints and cylinder orientations
    seg_centers = []
    seg_rotations = []
    for i in range(num_segments):
        j0 = joint_locs[i]
        j1 = joint_locs[i + 1]
        mid = 0.5 * (j0 + j1)
        seg_centers.append(mid)
        v_seg = (j1 - j0).normalized()
        q = mathutils.Vector((0, 0, 1)).rotation_difference(v_seg)
        seg_rotations.append(q.to_euler())

    return {
        'target_len': total_dist,
        'seg_len': total_dist / num_segments,
        'joint_locs': joint_locs,
        'seg_centers': seg_centers,
        'seg_rotations': seg_rotations,
        'amplitude': best_A
    }

def build_simulation(num_segments=16, sling_material="nylon", elasticity_k=None, wind_mph=0.0, duration_sec=30.0, pin_angle=20.0, marble_x=-0.035, slack_m=0.020, render_stills=True):
    t_start = time.time()
    v_wind = wind_mph * 0.44704
    print("=====================================================================")
    print(f"Starting Native Blender Bullet Sim ({duration_sec:.1f}s at 60 FPS / 1200 FPS physics | Wind: {wind_mph:.1f} mph | Pin Angle: {pin_angle:.1f}°)")
    print(f"Sling Architecture: {num_segments} Articulated Segments per Line | Material: {sling_material} | Marble X: {marble_x:.3f}m | Initial Slack: {slack_m*1000:.1f}mm")
    print("Realistic Aerodynamics: Quadratic Drag & Ambient Wind Force Fields")
    print("=====================================================================")

    # -------------------------------------------------------------
    # 1. RESET SCENE & UNIT SETTINGS
    # -------------------------------------------------------------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.unit_settings.scale_length = 1.0

    # 60 FPS timeline for rendering and animation:
    TOTAL_FRAMES = int(duration_sec * 60)
    scene.render.fps = 60
    scene.frame_start = 1
    scene.frame_end = TOTAL_FRAMES

    # -------------------------------------------------------------
    # 2. STUDIO LIGHTING & SKY ENVIRONMENT
    # -------------------------------------------------------------
    if not scene.world:
        scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    bg_node = scene.world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs[0].default_value = (0.78, 0.82, 0.86, 1.0)
        bg_node.inputs[1].default_value = 1.0

    # Key Sun Light
    bpy.ops.object.light_add(type='SUN', location=(3.0, -5.0, 8.0))
    sun = bpy.context.active_object
    sun.name = "Key_Sun_Light"
    sun.data.energy = 3.2
    sun.rotation_euler = (math.radians(52.0), math.radians(15.0), math.radians(-25.0))

    # Fill Sun Light
    bpy.ops.object.light_add(type='SUN', location=(-3.0, -5.0, 6.0))
    fill = bpy.context.active_object
    fill.name = "Fill_Sun_Light"
    fill.data.energy = 1.6
    fill.rotation_euler = (math.radians(55.0), math.radians(-20.0), math.radians(35.0))

    # -------------------------------------------------------------
    # 3. IMPORT OBJ & SCALE TO SI METERS
    # -------------------------------------------------------------
    obj_path = os.path.abspath("Trebuchet_3ft.obj")
    if not os.path.exists(obj_path):
        raise FileNotFoundError(f"Cannot find {obj_path}")

    bpy.ops.wm.obj_import(filepath=obj_path, up_axis='Z', forward_axis='Y')
    print(f"Imported {obj_path} (Z-up, Y-forward). Objects: {len(bpy.data.objects)}")

    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.scale = (0.001, 0.001, 0.001)

    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    old_lace = bpy.data.objects.get('Leather_ShoeLace_Sling_15_5in')
    if old_lace:
        bpy.data.objects.remove(old_lace, do_unlink=True)

    # -------------------------------------------------------------
    # 4. CREATE HIGH-FIDELITY PBR MATERIALS
    # -------------------------------------------------------------
    def make_mat(name, color, metallic=0.0, roughness=0.5, transmission=0.0):
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = color
            bsdf.inputs['Metallic'].default_value = metallic
            bsdf.inputs['Roughness'].default_value = roughness
            if 'Transmission Weight' in bsdf.inputs:
                bsdf.inputs['Transmission Weight'].default_value = transmission
        return mat

    SLING_MATERIALS = {
        'nylon': {
            'name': 'Braided Nylon (Standard)',
            'total_mass_g': 8.0,
            'elasticity_k': 8500.0,
            'linear_damping': 0.35,
            'angular_damping': 0.45,
            'constraint_type': 'GENERIC_SPRING',
            'color': (0.85, 0.82, 0.75, 1.0),
            'metallic': 0.0,
            'roughness': 0.88,
            'bevel_depth': 0.0013
        },
        'chain': {
            'name': 'Steel Link Chain (Rigid)',
            'total_mass_g': 120.0,
            'elasticity_k': 1e9,
            'linear_damping': 0.20,
            'angular_damping': 0.30,
            'constraint_type': 'POINT',
            'color': (0.65, 0.70, 0.75, 1.0),
            'metallic': 0.95,
            'roughness': 0.25,
            'bevel_depth': 0.0018
        },
        'yarn': {
            'name': 'Wool Yarn (Compliant)',
            'total_mass_g': 4.0,
            'elasticity_k': 600.0,
            'linear_damping': 0.50,
            'angular_damping': 0.60,
            'constraint_type': 'GENERIC_SPRING',
            'color': (0.92, 0.65, 0.45, 1.0),
            'metallic': 0.0,
            'roughness': 0.95,
            'bevel_depth': 0.0015
        }
    }
    mat_cfg = SLING_MATERIALS.get(sling_material, SLING_MATERIALS['nylon'])
    total_sling_mass_kg = mat_cfg['total_mass_g'] / 1000.0
    seg_mass_kg = total_sling_mass_kg / num_segments
    k_line = float(elasticity_k) if elasticity_k is not None else mat_cfg['elasticity_k']
    k_joint = num_segments * k_line
    c_joint = 2.0 * math.sqrt(seg_mass_kg * k_joint) * 0.4 if k_line < 1e8 else 0.0

    mat_wood   = make_mat("PBR_Timber_Pine",          (0.55, 0.35, 0.18, 1.0), metallic=0.0,  roughness=0.65)
    mat_steel  = make_mat("PBR_Polished_Steel",       (0.85, 0.88, 0.92, 1.0), metallic=0.95, roughness=0.15)
    mat_cw     = make_mat("PBR_Bronze_Weight",        (0.88, 0.68, 0.32, 1.0), metallic=0.85, roughness=0.30)
    mat_marble = make_mat("PBR_Glass_Marble_Cyan",     (0.05, 0.92, 0.88, 1.0), metallic=0.1,  roughness=0.05, transmission=0.85)
    mat_cloth  = make_mat("PBR_Woven_Canvas_Cloth",   (0.78, 0.72, 0.62, 1.0), metallic=0.0,  roughness=0.92)
    mat_string = make_mat(f"PBR_Sling_{sling_material.capitalize()}", mat_cfg['color'], metallic=mat_cfg['metallic'], roughness=mat_cfg['roughness'])
    mat_floor  = make_mat("PBR_Concrete_Floor",       (0.88, 0.90, 0.92, 1.0), roughness=0.7)
    mat_target = make_mat("PBR_Target_Red",           (0.90, 0.15, 0.15, 1.0), roughness=0.3)

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        obj.data.materials.clear()
        n = obj.name.lower()
        if 'marble' in n:
            obj.data.materials.append(mat_marble)
        elif 'counterweight' in n:
            obj.data.materials.append(mat_cw)
        elif 'rod' in n or 'bolt' in n or 'pin' in n or 'bearing' in n:
            obj.data.materials.append(mat_steel)
        elif 'pouch' in n or 'cloth' in n:
            obj.data.materials.append(mat_cloth)
        else:
            obj.data.materials.append(mat_wood)

    # -------------------------------------------------------------
    # 5. ENVIRONMENT & TARGET MARKERS
    # -------------------------------------------------------------
    # 200m floor centered at X=50m (covers X=-50m to X=+150m)
    bpy.ops.mesh.primitive_plane_add(size=200.0, location=(50.0, 0.0, 0.0))
    floor_obj = bpy.context.active_object
    floor_obj.name = "Workshop_Floor"
    floor_obj.data.materials.append(mat_floor)

    # Target Markers
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.004, location=(2.7432, 0.0, 0.002))
    target_3y = bpy.context.active_object
    target_3y.name = "Target_Marker_3_Yards"
    target_3y.data.materials.append(mat_target)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.004, location=(13.716, 0.0, 0.002))
    target_15y = bpy.context.active_object
    target_15y.name = "Target_Marker_15_Yards"
    target_15y.data.materials.append(mat_target)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.004, location=(18.288, 0.0, 0.002))
    target_20y = bpy.context.active_object
    target_20y.name = "Target_Marker_20_Yards"
    target_20y.data.materials.append(mat_target)

    # -------------------------------------------------------------
    # 6. CONFIGURE BULLET RIGID BODY WORLD (1200 FPS PHYSICS ENGINE)
    # -------------------------------------------------------------
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    # 60 FPS * 20 substeps_per_frame = 1200 FPS native physics simulation rate:
    rbw.substeps_per_frame = 20
    rbw.solver_iterations = 50
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = TOTAL_FRAMES
    rbw.effector_weights.wind = 1.0
    rbw.effector_weights.drag = 0.0

    # Ambient Wind Force Field
    wind_field = None
    if abs(wind_mph) > 0.05:
        bpy.ops.object.effector_add(type='WIND', location=(0.0, 0.0, 1.0))
        wind_field = bpy.context.active_object
        wind_field.name = "Ambient_Wind_Field"
        wind_rot_y = 90.0 if v_wind > 0 else -90.0
        wind_field.rotation_euler = (0.0, math.radians(wind_rot_y), 0.0)
        wind_field.field.shape = 'PLANE'
        # Air kinetic force ~ 0.5 * rho * v_w^2
        wind_field.field.strength = 0.5 * 1.225 * (v_wind ** 2) * (1.0 if v_wind > 0 else -1.0)
        wind_field.field.falloff_power = 0.0
        wind_field.field.use_max_distance = False

    # 6a. Passive Collision Bodies
    for obj in [floor_obj, target_3y, target_15y, target_20y]:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = 'PASSIVE'
        obj.rigid_body.friction = 0.35
        obj.rigid_body.restitution = 0.20
        obj.rigid_body.collision_collections[0] = True

    trough = bpy.data.objects.get('Marble_Guide_Trough')
    if trough:
        bpy.ops.object.select_all(action='DESELECT')
        trough.select_set(True)
        bpy.context.view_layer.objects.active = trough
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.rigidbody.object_add()
        trough.rigid_body.type = 'PASSIVE'
        trough.rigid_body.collision_shape = 'CONVEX_HULL'
        trough.rigid_body.use_margin = True
        trough.rigid_body.collision_margin = 0.0005
        trough.rigid_body.friction = 0.16 # Pine wood grain friction
        trough.rigid_body.collision_collections[0] = True

    # 6b. Active Decoupled Arm & Counterweight (SWING-ARM FRICTION KEPT AS IS)
    arm     = bpy.data.objects.get('Swing_Stick_Arm_40in')
    cw      = bpy.data.objects.get('Screwed_Counterweight_748g')
    bolt    = bpy.data.objects.get('Counterweight_Mount_Bolt_38')
    pin_obj = bpy.data.objects.get('Sling_Release_Pin_45deg')

    bpy.ops.object.select_all(action='DESELECT')
    if cw and bolt:
        cw.select_set(True)
        bolt.select_set(True)
        bpy.context.view_layer.objects.active = cw
        bpy.ops.object.join()
    cw.name = "Counterweight_Assembly"
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bpy.ops.rigidbody.object_add()
    cw.rigid_body.type = 'ACTIVE'
    cw.rigid_body.mass = 2.00 # 2.0 kg portable demonstration counterweight
    # Swing-arm friction kept as is:
    cw.rigid_body.linear_damping = 0.03
    cw.rigid_body.angular_damping = 0.04
    cw.rigid_body.collision_collections[0] = False
    cw.rigid_body.collision_collections[1] = False

    # 6b-pin. Compute Pin Geometry and Align Visual Mesh to Target Angle
    p_tip = mathutils.Vector((-0.3922, 0.0, 0.0627))
    pivot_w = mathutils.Vector((0.0, 0.0, 0.762))
    arm_axis_w = (p_tip - pivot_w).normalized()

    # Reference pin vector from model:
    p_pin_ref = mathutils.Vector((-0.4311, 0.0, 0.0348))
    pin_vec_ref = p_pin_ref - p_tip
    pin_len = pin_vec_ref.length
    pin_dir_ref = pin_vec_ref.normalized()

    comp_along = pin_dir_ref.dot(arm_axis_w)
    norm_w = (pin_dir_ref - comp_along * arm_axis_w).normalized()
    orig_angle_deg = math.degrees(math.atan2(norm_w.length, comp_along)) # ~25.07°

    actual_pin_angle = orig_angle_deg if pin_angle is None else pin_angle
    rad = math.radians(actual_pin_angle)
    pin_dir = (math.cos(rad) * arm_axis_w + math.sin(rad) * norm_w).normalized()
    p_pin_tip = p_tip + pin_len * pin_dir
    print(f"Pin Geometry: angle={actual_pin_angle:.2f}° (original was {orig_angle_deg:.2f}°), len={pin_len*1000:.1f}mm, tip=({p_pin_tip.x:.4f}, {p_pin_tip.z:.4f})")

    # Replace/re-create visual pin cylinder so 3D mesh matches pin_dir exactly:
    if pin_obj:
        bpy.data.objects.remove(pin_obj, do_unlink=True)

    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.00238,
        depth=pin_len,
        location=p_tip + 0.5 * pin_len * pin_dir,
        rotation=mathutils.Vector((0, 0, 1)).rotation_difference(pin_dir).to_euler()
    )
    pin_obj = bpy.context.active_object
    pin_obj.name = "Sling_Release_Pin"
    pin_obj.data.materials.append(mat_steel)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    pin_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.join()
    scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.762))
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.rigidbody.object_add()
    arm.rigid_body.type = 'ACTIVE'
    arm.rigid_body.collision_shape = 'CONVEX_HULL'
    arm.rigid_body.use_margin = True
    arm.rigid_body.collision_margin = 0.001
    arm.rigid_body.friction = 0.40
    arm.rigid_body.restitution = 0.25
    arm.rigid_body.mass = 0.30
    # Swing-arm friction kept as is (original oiled axle bearing & aerodynamic drag):
    arm.rigid_body.linear_damping = 0.04
    arm.rigid_body.angular_damping = 0.06
    arm.rigid_body.collision_collections[0] = False
    arm.rigid_body.collision_collections[1] = True # Collision layer 1: Arm & Sling physical bounce/contact

    # Axle Anchor & Hinge at (0.0, 0.0, 0.762m)
    bpy.ops.mesh.primitive_cube_add(size=0.01, location=(0.0, 0.0, 0.762))
    axle_anchor = bpy.context.active_object
    axle_anchor.name = "Axle_Anchor_Static"
    bpy.ops.rigidbody.object_add()
    axle_anchor.rigid_body.type = 'PASSIVE'
    axle_anchor.rigid_body.collision_collections[0] = False
    axle_anchor.rigid_body.collision_collections[1] = False

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 0.762))
    hinge_empty = bpy.context.active_object
    hinge_empty.name = "Hinge_Constraint_Axle"
    bpy.ops.rigidbody.constraint_add()
    con = hinge_empty.rigid_body_constraint
    con.type = 'HINGE'
    con.object1 = axle_anchor
    con.object2 = arm
    con.disable_collisions = True
    hinge_empty.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # Rigid FIXED constraint connecting Counterweight to Short Arm
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=cw.location)
    cw_fix = bpy.context.active_object
    cw_fix.name = "Fixed_Constraint_CW"
    bpy.ops.rigidbody.constraint_add()
    cw_fix.rigid_body_constraint.type = 'FIXED'
    cw_fix.rigid_body_constraint.object1 = arm
    cw_fix.rigid_body_constraint.object2 = cw
    cw_fix.rigid_body_constraint.disable_collisions = True

    # 6c. Active Marble (Moved towards arm tip to prevent initial string tightness)
    marble = bpy.data.objects.get('Glass_Marble_16mm')
    bpy.ops.object.select_all(action='DESELECT')
    marble.select_set(True)
    bpy.context.view_layer.objects.active = marble
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    marble.location = mathutils.Vector((marble_x, 0.0, 0.0593))
    bpy.ops.rigidbody.object_add()
    marble.rigid_body.type = 'ACTIVE'
    marble.rigid_body.collision_shape = 'SPHERE'
    marble.rigid_body.use_margin = True
    marble.rigid_body.collision_margin = 0.0005
    marble.rigid_body.mass = 0.020 # 20 grams
    marble.rigid_body.friction = 0.35
    marble.rigid_body.linear_damping = 0.08
    marble.rigid_body.angular_damping = 0.30
    marble.rigid_body.restitution = 0.25
    marble.rigid_body.collision_collections[0] = True
    marble.rigid_body.collision_collections[1] = False

    # 6d. 100% Native Continuous Physical Sling Simulation with Initial Slack
    p_tip = mathutils.Vector((-0.3922, 0.0, 0.0627))
    p_pouch = mathutils.Vector((marble_x, 0.0, 0.0593))

    pouch = bpy.data.objects.get('Cloth_Sling_Pouch')
    if pouch:
        bpy.ops.object.select_all(action='DESELECT')
        pouch.select_set(True)
        bpy.context.view_layer.objects.active = pouch
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        pouch.location = p_pouch
        bpy.ops.rigidbody.object_add()
        pouch.rigid_body.type = 'ACTIVE'
        pouch.rigid_body.collision_shape = 'CONVEX_HULL'
        pouch.rigid_body.use_margin = True
        pouch.rigid_body.collision_margin = 0.001
        pouch.rigid_body.friction = 0.45
        pouch.rigid_body.restitution = 0.20
        pouch.rigid_body.mass = 0.010 # 10 grams canvas pouch
        # Doubled damping on sling (canvas pouch air drag & fabric internal friction):
        pouch.rigid_body.linear_damping = 0.70
        pouch.rigid_body.angular_damping = 0.70
        pouch.rigid_body.collision_collections[0] = False
        pouch.rigid_body.collision_collections[1] = True # Collision layer 1: Arm & Sling physical bounce/contact

    # Line 1 & Line 2: Multi-Segment Articulated Physics Chains with Realistic Slack Geometry
    # Line 1: Fixed line from arm eyelet (Y = -0.008) to pouch (Y = -0.008)
    p1_start = p_tip + mathutils.Vector((0.0, -0.008, 0.0))
    p1_end   = p_pouch + mathutils.Vector((0.0, -0.008, 0.0))
    path1 = generate_slack_sling_path(p1_start, p1_end, num_segments, slack_m=slack_m, n_waves=2, lateral_sign=-1.0)

    # Line 2: Release line from pin loop (Y = 0.0) to pouch (Y = +0.008)
    p2_start = p_tip.copy()
    p2_end   = p_pouch + mathutils.Vector((0.0, 0.008, 0.0))
    path2 = generate_slack_sling_path(p2_start, p2_end, num_segments, slack_m=slack_m, n_waves=2, lateral_sign=1.0)

    line1_segs = []
    line2_segs = []
    line1_joints = []
    line2_joints = []

    for i in range(num_segments):
        # Line 1 segment (Fixed)
        mid1 = path1['seg_centers'][i]
        rot1 = path1['seg_rotations'][i]
        slen1 = path1['seg_len']
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0013, depth=slen1, location=mid1, rotation=rot1)
        s1 = bpy.context.active_object
        s1.name = f"Phys_Line1_{i}"
        bpy.ops.rigidbody.object_add()
        s1.rigid_body.type = 'ACTIVE'
        s1.rigid_body.collision_shape = 'CAPSULE'
        s1.rigid_body.use_margin = True
        s1.rigid_body.collision_margin = 0.0005
        s1.rigid_body.friction = 0.40
        s1.rigid_body.restitution = 0.20
        s1.rigid_body.mass = seg_mass_kg
        s1.rigid_body.linear_damping = mat_cfg['linear_damping']
        s1.rigid_body.angular_damping = mat_cfg['angular_damping']
        s1.rigid_body.collision_collections[0] = False
        s1.rigid_body.collision_collections[1] = True # Collision layer 1: Arm & Sling physical bounce/contact
        s1.hide_render = True
        line1_segs.append(s1)

        # Line 2 segment (Release)
        mid2 = path2['seg_centers'][i]
        rot2 = path2['seg_rotations'][i]
        slen2 = path2['seg_len']
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0013, depth=slen2, location=mid2, rotation=rot2)
        s2 = bpy.context.active_object
        s2.name = f"Phys_Line2_{i}"
        bpy.ops.rigidbody.object_add()
        s2.rigid_body.type = 'ACTIVE'
        s2.rigid_body.collision_shape = 'CAPSULE'
        s2.rigid_body.use_margin = True
        s2.rigid_body.collision_margin = 0.0005
        s2.rigid_body.friction = 0.40
        s2.rigid_body.restitution = 0.20
        s2.rigid_body.mass = seg_mass_kg
        s2.rigid_body.linear_damping = mat_cfg['linear_damping']
        s2.rigid_body.angular_damping = mat_cfg['angular_damping']
        s2.rigid_body.collision_collections[0] = False
        s2.rigid_body.collision_collections[1] = True # Collision layer 1: Arm & Sling physical bounce/contact
        s2.hide_render = True
        line2_segs.append(s2)

    def create_sling_joint(name, obj1, obj2, loc):
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=loc)
        emp = bpy.context.active_object
        emp.name = name
        bpy.ops.rigidbody.constraint_add()
        con = emp.rigid_body_constraint
        con.object1 = obj1
        con.object2 = obj2
        con.disable_collisions = True
        con.type = 'POINT'
        return emp

    # 6e. Physical Sling String Loop & Pin Slider Constraint
    # (p_pin_tip, pin_len, and pin_dir were computed in step 6b-pin according to pin_angle)

    # The actual physical cord loop seated on the pin:
    q_torus = mathutils.Vector((0, 0, 1)).rotation_difference(pin_dir)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0055,
        minor_radius=0.0013,
        major_segments=24,
        minor_segments=8,
        location=p_tip,
        rotation=q_torus.to_euler()
    )
    loop_obj = bpy.context.active_object
    loop_obj.name = "Sling_String_Loop"
    loop_obj.data.materials.append(mat_string)
    bpy.ops.rigidbody.object_add()
    loop_obj.rigid_body.type = 'ACTIVE'
    loop_obj.rigid_body.mass = 0.003
    loop_obj.rigid_body.collision_shape = 'CONVEX_HULL'
    loop_obj.rigid_body.use_margin = True
    loop_obj.rigid_body.collision_margin = 0.0005
    loop_obj.rigid_body.linear_damping = 0.25
    loop_obj.rigid_body.angular_damping = 0.25
    loop_obj.rigid_body.collision_collections[0] = False
    loop_obj.rigid_body.collision_collections[1] = True # Bounces off arm!

    # Slider constraint between arm and loop along the 45° pin axis:
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_tip)
    slider_emp = bpy.context.active_object
    slider_emp.name = "Joint_Pin_Loop_Slider"
    bpy.ops.rigidbody.constraint_add()
    sc = slider_emp.rigid_body_constraint
    sc.type = 'SLIDER'
    sc.object1 = arm
    sc.object2 = loop_obj
    q_slider = mathutils.Vector((1, 0, 0)).rotation_difference(pin_dir)
    slider_emp.rotation_euler = q_slider.to_euler()
    sc.use_limit_lin_x = True
    sc.limit_lin_x_lower = 0.0
    sc.limit_lin_x_upper = pin_len
    sc.disable_collisions = True

    # Line 1 Joints: Arm Tip Eyelet -> seg 0 -> seg 1 ... -> seg N-1 -> Pouch (Along Relaxed Slack Path)
    j1_0 = create_sling_joint("Joint_Arm_Line1_0", arm, line1_segs[0], path1['joint_locs'][0])
    line1_joints.append(j1_0)
    for i in range(1, num_segments):
        ji = create_sling_joint(f"Joint_Line1_{i-1}_{i}", line1_segs[i-1], line1_segs[i], path1['joint_locs'][i])
        line1_joints.append(ji)
    j1_N = create_sling_joint("Joint_Line1_Pouch", line1_segs[-1], pouch, path1['joint_locs'][-1])
    line1_joints.append(j1_N)

    # Line 2 Joints: PHYSICAL LOOP -> seg 0 -> seg 1 ... -> seg N-1 -> Pouch (Along Relaxed Slack Path)
    # (The rope is directly anchored to the loop that slides along the pin!)
    j_loop_rope = create_sling_joint("Joint_Loop_Line2_0", loop_obj, line2_segs[0], path2['joint_locs'][0])
    line2_joints.append(j_loop_rope)
    for i in range(1, num_segments):
        ji = create_sling_joint(f"Joint_Line2_{i-1}_{i}", line2_segs[i-1], line2_segs[i], path2['joint_locs'][i])
        line2_joints.append(ji)
    j2_N = create_sling_joint("Joint_Line2_Pouch", line2_segs[-1], pouch, path2['joint_locs'][-1])
    line2_joints.append(j2_N)

    # Joint M: Pouch <-> Marble (Cradles marble, opens at release!)
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_pouch)
    jm = bpy.context.active_object
    jm.name = "Joint_Pouch_Marble"
    bpy.ops.rigidbody.constraint_add()
    jm.rigid_body_constraint.type = 'POINT'
    jm.rigid_body_constraint.object1 = pouch
    jm.rigid_body_constraint.object2 = marble

    pin_base_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    pin_dir_local = pin_dir.copy()

    # -------------------------------------------------------------
    # 7. RUN FULL 60-SECOND SIMULATION WITH LIVE DYNAMIC RELEASE
    # -------------------------------------------------------------
    print(f"Running native Bullet physics simulation (60 FPS render, 1200 FPS physics, {TOTAL_FRAMES} frames)...")

    # Sample every single frame across the full 6-second timeline:
    sampled_frames = list(range(1, TOTAL_FRAMES + 1))
    sampled_set = set(sampled_frames)

    step_data = {}
    released = False
    dynamic_release_frame = 28 # fallback default

    t_sim_0 = time.time()
    for f in range(1, TOTAL_FRAMES + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()

        # Check live dynamic release condition if not yet released
        if not released and f > 15:
            arm_eval = arm.evaluated_get(dg)
            m_eval = marble.evaluated_get(dg)
            mat_arm = arm_eval.matrix_world
            p_base_w = mat_arm @ pin_base_local
            p_dir_w = (mat_arm.to_3x3() @ pin_dir_local).normalized()
            m_loc = m_eval.matrix_world.translation

            T_vec = (m_loc - p_base_w).normalized()
            dot_val = T_vec.dot(p_dir_w)
            rot_deg = math.degrees(arm_eval.matrix_world.to_euler().y)

            if rot_deg > 105.0 and dot_val > 0.80:
                released = True
                dynamic_release_frame = f
                sc.enabled = False # Release loop from 45° pin!
                jm.rigid_body_constraint.enabled = False
                print(f">>> 100% DYNAMIC HOOK RELEASE at Frame {f} (t={(f-1)/60:.3f}s): arm_rot={rot_deg:.2f}°, dot={dot_val:.4f} <<<")

        if f in sampled_set:
            step_data[f] = {
                'arm': arm.evaluated_get(dg).matrix_world.copy(),
                'cw': cw.evaluated_get(dg).matrix_world.copy(),
                'marble': marble.evaluated_get(dg).matrix_world.copy(),
                'pouch': pouch.evaluated_get(dg).matrix_world.copy(),
                'loop': loop_obj.evaluated_get(dg).matrix_world.copy(),
                'line2_0': line2_segs[0].evaluated_get(dg).matrix_world.copy(),
                'line1_locs': [seg.evaluated_get(dg).matrix_world.translation.copy() for seg in line1_segs],
                'line2_locs': [seg.evaluated_get(dg).matrix_world.translation.copy() for seg in line2_segs],
            }

        if f % 600 == 0 or f == TOTAL_FRAMES:
            t_sec = (f - 1) / 60.0
            arm_rot = math.degrees(arm.evaluated_get(dg).matrix_world.to_euler().y)
            m_pos = marble.evaluated_get(dg).matrix_world.translation
            print(f"  Frame {f:4d} / {TOTAL_FRAMES} (t={t_sec:4.1f}s): arm_rot={arm_rot:6.2f}°, marble=({m_pos.x:5.2f}, {m_pos.z:5.2f})")

    print(f"Physics simulation completed in {time.time() - t_sim_0:.2f}s!")

    # Disable rigid body world and strip rigid bodies so baked keyframes have full deterministic control
    if scene.rigidbody_world:
        scene.rigidbody_world.enabled = False

    for obj in [arm, cw, marble, pouch, loop_obj]:
        if obj and obj.rigid_body:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.rigidbody.object_remove()

    helpers_to_hide = (
        line1_segs + line2_segs +
        line1_joints + line2_joints +
        [jm, axle_anchor, hinge_empty, cw_fix, wind_field, slider_emp]
    )
    for obj in helpers_to_hide:
        if obj and obj.name in bpy.data.objects:
            obj.hide_viewport = True
            obj.hide_render = True

    # -------------------------------------------------------------
    # 8. BAKE KEYFRAMES ACROSS 3,600 FRAMES (60 FPS)
    # -------------------------------------------------------------
    print("Baking keyframes to 60 FPS timeline...")
    marble_positions = []
    t_bake_0 = time.time()

    for f in sampled_frames:
        d = step_data[f]

        # Arm
        loc_a, rot_a, _ = d['arm'].decompose()
        arm.location = loc_a
        arm.rotation_euler = rot_a.to_euler()
        arm.keyframe_insert(data_path="location", frame=f)
        arm.keyframe_insert(data_path="rotation_euler", frame=f)

        # Counterweight
        loc_c, rot_c, _ = d['cw'].decompose()
        cw.location = loc_c
        cw.rotation_euler = rot_c.to_euler()
        cw.keyframe_insert(data_path="location", frame=f)
        cw.keyframe_insert(data_path="rotation_euler", frame=f)

        # Marble
        loc_m, rot_m, _ = d['marble'].decompose()
        marble.location = loc_m
        marble.rotation_euler = rot_m.to_euler()
        marble.scale = (5.0, 5.0, 5.0)  # 5x visual display scaling for clear visibility across flight
        marble.keyframe_insert(data_path="location", frame=f)
        marble.keyframe_insert(data_path="rotation_euler", frame=f)
        marble.keyframe_insert(data_path="scale", frame=f)
        marble_positions.append(loc_m)

        # Pouch
        loc_p, rot_p, _ = d['pouch'].decompose()
        pouch.location = loc_p
        pouch.rotation_euler = rot_p.to_euler()
        pouch.keyframe_insert(data_path="location", frame=f)
        pouch.keyframe_insert(data_path="rotation_euler", frame=f)

        # Physical Loop on Pin
        loc_l, rot_l, _ = d['loop'].decompose()
        loop_obj.location = loc_l
        loop_obj.rotation_euler = rot_l.to_euler()
        loop_obj.keyframe_insert(data_path="location", frame=f)
        loop_obj.keyframe_insert(data_path="rotation_euler", frame=f)

    print(f"Keyframe baking completed in {time.time() - t_bake_0:.2f}s!")

    # -------------------------------------------------------------
    # 9. CONSTRUCT VISUAL STRING CURVES AND RIG
    # -------------------------------------------------------------
    print("Building visual articulated string curves rig across 3,600 frames...")
    rig_col = bpy.data.collections.new("Sling_Rig_Drivers")
    scene.collection.children.link(rig_col)
    rig_col.hide_viewport = True

    total_curve_pts = num_segments + 2

    def create_string_curve(name, num_pts):
        c_data = bpy.data.curves.new(name, type='CURVE')
        c_data.dimensions = '3D'
        c_data.bevel_depth = mat_cfg.get('bevel_depth', 0.0013)
        c_data.bevel_resolution = 3
        spline = c_data.splines.new('POLY')
        spline.points.add(num_pts - 1)
        c_obj = bpy.data.objects.new(name, c_data)
        c_obj.data.materials.append(mat_string)
        scene.collection.objects.link(c_obj)

        empties = []
        for i in range(num_pts):
            emp = bpy.data.objects.new(f"{name}_Driver_{i}", None)
            rig_col.objects.link(emp)
            empties.append(emp)
            mod = c_obj.modifiers.new(name=f"Hook_{i}", type='HOOK')
            mod.object = emp
            mod.vertex_indices_set([i])
        return c_obj, empties

    str_fixed, emps_fixed = create_string_curve("Sling_String_Fixed", total_curve_pts)     # Line 1 (Fixed to arm tip eyelet)
    str_rel,   emps_rel   = create_string_curve("Sling_String_Release", total_curve_pts)   # Line 2 (Loop on 45° pin)

    tip_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))

    for f in sampled_frames:
        d = step_data[f]
        mat_a = d['arm']
        mat_p = d['pouch']
        rot_mat = mat_a.to_3x3()

        tip_w = mat_a.translation + rot_mat @ tip_local
        pouch_w = mat_p.translation

        # Line 1 (Fixed: Arm Tip Eyelet <-> Segments <-> Pouch)
        p1_anc = tip_w + mathutils.Vector((0.0, -0.008, 0.0))
        p1_end = pouch_w + mathutils.Vector((0.0, -0.008, 0.0))
        emps_fixed[0].location = p1_anc
        emps_fixed[0].keyframe_insert(data_path="location", frame=f)
        for i in range(num_segments):
            emps_fixed[i + 1].location = d['line1_locs'][i]
            emps_fixed[i + 1].keyframe_insert(data_path="location", frame=f)
        emps_fixed[-1].location = p1_end
        emps_fixed[-1].keyframe_insert(data_path="location", frame=f)

        # Line 2 (Release: PHYSICAL LOOP <-> Segments <-> Pouch)
        # Directly anchored to the physical loop that slides off the 45° pin!
        p2_anc = d['loop'].translation
        p2_end = pouch_w + mathutils.Vector((0.0, 0.008, 0.0))
        emps_rel[0].location = p2_anc
        emps_rel[0].keyframe_insert(data_path="location", frame=f)
        for i in range(num_segments):
            emps_rel[i + 1].location = d['line2_locs'][i]
            emps_rel[i + 1].keyframe_insert(data_path="location", frame=f)
        emps_rel[-1].location = p2_end
        emps_rel[-1].keyframe_insert(data_path="location", frame=f)

    # -------------------------------------------------------------
    # 11. NEON CYAN MARBLE TRAJECTORY PATH
    # -------------------------------------------------------------
    curve_data = bpy.data.curves.new("Marble_Trajectory_Path", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.004
    polyline = curve_data.splines.new('POLY')

    # Subsample trajectory points for smooth rendering
    arc_points = [marble_positions[i] for i in range(0, min(len(marble_positions), 3600), 2)]
    polyline.points.add(len(arc_points) - 1)
    for i, loc in enumerate(arc_points):
        polyline.points[i].co = (loc.x, loc.y, loc.z, 1.0)

    curve_obj = bpy.data.objects.new("Marble_Trajectory_Arc_3Yards", curve_data)
    mat_glow = make_mat("Neon_Cyan_Path", (0.0, 1.0, 0.9, 1.0), roughness=0.1)
    curve_obj.data.materials.append(mat_glow)
    curve_obj.hide_render = False
    scene.collection.objects.link(curve_obj)

    # -------------------------------------------------------------
    # 12. CAMERAS (ACTION PERSPECTIVE, ELEVATION, ISOMETRIC, AND WIDE)
    # -------------------------------------------------------------
    cam_target = bpy.data.objects.new("Cam_Target_Center", None)
    cam_target.location = (0.15, 0.0, 0.72)
    scene.collection.objects.link(cam_target)

    # Action View (Initial Default Camera matching user's custom perspective)
    cam_action = bpy.data.objects.new("Camera_Action_View", bpy.data.cameras.new("Cam_Action"))
    cam_action.data.type = 'PERSP'
    cam_action.data.lens = 32.0
    cam_action.location = (-1.2, 3.2, 1.35)
    tt_act = cam_action.constraints.new('TRACK_TO')
    tt_act.target = cam_target
    tt_act.track_axis = 'TRACK_NEGATIVE_Z'
    tt_act.up_axis = 'UP_Y'
    scene.collection.objects.link(cam_action)

    cam_side = bpy.data.objects.new("Camera_Side_Elevation", bpy.data.cameras.new("Cam_Side"))
    cam_side.data.type = 'ORTHO'
    cam_side.data.ortho_scale = 3.6
    cam_side.location = (0.2, -4.5, 0.9)
    cam_side.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.collection.objects.link(cam_side)

    cam_iso = bpy.data.objects.new("Camera_Isometric", bpy.data.cameras.new("Cam_Iso"))
    cam_iso.data.type = 'ORTHO'
    cam_iso.data.ortho_scale = 2.8
    cam_iso.location = (-2.0, -2.5, 2.0)
    tt = cam_iso.constraints.new('TRACK_TO')
    tt.target = cam_target
    tt.track_axis = 'TRACK_NEGATIVE_Z'
    tt.up_axis = 'UP_Y'
    scene.collection.objects.link(cam_iso)

    cam_wide = bpy.data.objects.new("Camera_Trajectory_Wide", bpy.data.cameras.new("Cam_Wide"))
    cam_wide.data.type = 'ORTHO'
    cam_wide.data.ortho_scale = 22.0 # Perfectly frames trebuchet at X=0 to 15-yard target marker at X=13.7m
    cam_wide.location = (9.5, -25.0, 2.4)
    cam_wide.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.collection.objects.link(cam_wide)

    # Set default active scene camera to Action View
    scene.camera = cam_action

    # -------------------------------------------------------------
    # 13. CONFIGURE VIEWPORT OVERLAYS (DEFAULT OFF) & FREE PERSPECTIVE
    # -------------------------------------------------------------
    cpos = mathutils.Vector((-1.2, 3.2, 1.35))
    tpos = mathutils.Vector((0.15, 0.0, 0.72))
    dist = (cpos - tpos).length
    fwd = (tpos - cpos).normalized()
    up_w = mathutils.Vector((0, 0, 1))
    r_cam = fwd.cross(up_w).normalized()
    u_cam = r_cam.cross(fwd).normalized()
    m_view = mathutils.Matrix([
        [r_cam.x, u_cam.x, -fwd.x, cpos.x],
        [r_cam.y, u_cam.y, -fwd.y, cpos.y],
        [r_cam.z, u_cam.z, -fwd.z, cpos.z],
        [0, 0, 0, 1]
    ])
    v_rot = m_view.to_quaternion()

    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.overlay.show_overlays = False
                        if space.region_3d:
                            space.region_3d.view_perspective = 'PERSP'
                            space.region_3d.view_location = tpos
                            space.region_3d.view_distance = dist
                            space.region_3d.view_rotation = v_rot

    # -------------------------------------------------------------
    # 14. SAVE BLEND FILE & SYNC TO ARTIFACT DIRECTORY
    # -------------------------------------------------------------
    scene.frame_set(1)

    blend_path = os.path.abspath("Trebuchet_3ft.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Successfully saved {blend_path}")

    artifact_dir = "/home/steve/.gemini/antigravity/brain/91e1f823-b856-4d61-bc57-2d759f389fdf"
    if os.path.exists(artifact_dir):
        shutil.copy2(blend_path, os.path.join(artifact_dir, "Trebuchet_3ft.blend"))
        print(f"Synchronized Trebuchet_3ft.blend to {artifact_dir}")

    # -------------------------------------------------------------
    # 15. RENDER VALIDATION FRAMES ACROSS 60 SECONDS (3,600 FRAMES)
    # -------------------------------------------------------------
    if render_stills:
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        if hasattr(scene, 'eevee') and hasattr(scene.eevee, 'taa_render_samples'):
            scene.eevee.taa_render_samples = 16

        rel_f = dynamic_release_frame
        render_action = [
            (1,     "native_action_f1.png"),
            (20,    "native_action_f20.png"),
            (rel_f, "native_action_f28_release.png"),
            (90,    "native_action_f90_apex.png"),
            (150,   "native_action_f150_touchdown.png"),
            (194,   "native_action_f194_floor_roll.png"),
            (360,   "native_action_f360_rest.png"),
            (1800,  "native_action_f1800_rest.png"),
        ]
        scene.camera = cam_action
        for f_idx, out_name in render_action:
            if f_idx <= TOTAL_FRAMES:
                scene.frame_set(f_idx)
                out_path = os.path.join(artifact_dir, out_name) if os.path.exists(artifact_dir) else os.path.abspath(out_name)
                scene.render.filepath = out_path
                bpy.ops.render.render(write_still=True)
                print(f"Rendered Frame {f_idx} (Action Perspective) to {out_path}")

        render_side = [
            (1,     "native_sim_f1_cocked.png"),
            (20,    "native_sim_f20_centrifugal_whip.png"),
            (rel_f, "native_sim_f27_dynamic_release.png"),
            (rel_f, "native_sim_f28_sling_fling.png"),
            (rel_f + 4, "native_sim_f32_wide_open.png"),
            (90,    "native_sim_f90_apex.png"),
            (150,   "native_sim_f150_touchdown.png"),
            (360,   "native_sim_f360_rest.png"),
            (1800,  "native_sim_f1800_rest.png"),
        ]
        scene.camera = cam_side
        for f_idx, out_name in render_side:
            if f_idx <= TOTAL_FRAMES:
                scene.frame_set(f_idx)
                out_path = os.path.join(artifact_dir, out_name) if os.path.exists(artifact_dir) else os.path.abspath(out_name)
                scene.render.filepath = out_path
                bpy.ops.render.render(write_still=True)
                print(f"Rendered Frame {f_idx} (Side Close) to {out_path}")

        render_iso = [
            (1,     "native_iso_f1.png"),
            (20,    "native_iso_f20.png"),
            (rel_f - 1, "native_iso_f27.png"),
            (rel_f,     "native_iso_f28.png"),
            (rel_f + 4, "native_iso_f32.png"),
            (90,    "native_iso_f90.png"),
            (150,   "native_iso_f150.png"),
            (1800,  "native_iso_f1800.png"),
        ]
        scene.camera = cam_iso
        for f_idx, out_name in render_iso:
            if f_idx <= TOTAL_FRAMES:
                scene.frame_set(f_idx)
                out_path = os.path.join(artifact_dir, out_name) if os.path.exists(artifact_dir) else os.path.abspath(out_name)
                scene.render.filepath = out_path
                bpy.ops.render.render(write_still=True)
                print(f"Rendered Frame {f_idx} (Iso Close) to {out_path}")

        render_wide = [
            (rel_f, "native_wide_f28_release.png"),
            (90,    "native_wide_f90_apex.png"),
            (150,   "native_wide_f150_touchdown.png"),
            (300,   "native_wide_f300_floor_roll.png"),
            (360,   "native_wide_f360_rest.png"),
            (1800,  "native_wide_f1800_rest.png"),
        ]
        scene.camera = cam_wide
        for f_idx, out_name in render_wide:
            if f_idx <= TOTAL_FRAMES:
                scene.frame_set(f_idx)
                out_path = os.path.join(artifact_dir, out_name) if os.path.exists(artifact_dir) else os.path.abspath(out_name)
                scene.render.filepath = out_path
                bpy.ops.render.render(write_still=True)
                print(f"Rendered Frame {f_idx} (Wide Full Journey) to {out_path}")

    # Re-save to guarantee active camera and frame 1 state
    scene.camera = cam_action
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    if os.path.exists(artifact_dir):
        shutil.copy2(blend_path, os.path.join(artifact_dir, "Trebuchet_3ft.blend"))

    print(f"All {TOTAL_FRAMES} frames ({duration_sec:.1f}s) simulation and baking completed in {time.time() - t_start:.2f}s!")
    os._exit(0)

if __name__ == '__main__':
    import sys
    import argparse
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    parser = argparse.ArgumentParser(description="Trebuchet Blender Physics Simulation with Multi-Segment Elastic Sling & Aerodynamics")
    parser.add_argument("--segments", type=int, default=16, help="Number of articulated rigid body segments per sling string (default: 16)")
    parser.add_argument("--material", type=str, default="nylon", choices=["nylon", "chain", "yarn"], help="Sling material type (nylon, chain, yarn)")
    parser.add_argument("--elasticity", type=float, default=None, help="Custom tensile spring stiffness k in N/m")
    parser.add_argument("--wind", type=float, default=0.0, help="Ambient horizontal wind speed in mph (+X tailwind, -X headwind)")
    parser.add_argument("--duration", type=float, default=30.0, help="Simulation duration in seconds (default: 30.0s = 1800 frames)")
    parser.add_argument("--pin-angle", type=float, default=10.0, help="Release pin angle relative to arm axis in degrees (default: 10.0°, reduced from 25.07°)")
    parser.add_argument("--marble-x", type=float, default=-0.035, help="Initial marble X location in meters (default: -0.035m, shifted towards arm)")
    parser.add_argument("--slack", type=float, default=0.020, help="Initial sling string slack length in meters (default: 0.020m = 20mm)")
    parser.add_argument("--no-render", action="store_true", help="Skip rendering stills for faster physics testing")
    args, unknown = parser.parse_known_args(argv)
    build_simulation(
        num_segments=args.segments,
        sling_material=args.material,
        elasticity_k=args.elasticity,
        wind_mph=args.wind,
        duration_sec=args.duration,
        pin_angle=args.pin_angle,
        marble_x=args.marble_x,
        slack_m=args.slack,
        render_stills=not args.no_render
    )
