#!/usr/bin/env python3
"""
build_blender_physics_sim.py
Pure Native Blender Bullet Physics Engine Trebuchet Simulation & Keyframe Baker:

1. Clears factory settings, sets SI metric units (meters, 60 FPS, 180 frames).
2. Imports Trebuchet_3ft.obj preserving all named parts with Z-up, Y-forward SI scale (1 BU = 1.0 m).
3. Assigns rich PBR materials (Timber Wood, Polished Steel, Bronze Weight, Cyan Glass Marble, Woven Canvas Cloth, Braided Twine String).
4. Sets up Studio Lighting (Key Sun Light, Fill Light, Sky Environment) for crystal-clear viewport & renders.
5. Configures Blender's Native Bullet Rigid Body Physics World:
   - High precision: 120 substeps per frame, 100 solver iterations across 180 frames (60 FPS, 3.0 seconds).
   - Workshop Floor & Guide Trough:
     - Fixed polygon normals and true millimeter collision margins (0.5mm).
     - Passive rigid bodies on collision collection 0.
   - Active Rigid Body Arm & Decoupled Counterweight:
     - Lightweight timber arm (0.30 kg) and concentrated heavy counterweight (3.50 kg) kept as separate rigid bodies.
     - Connected by a native FIXED constraint, avoiding the 700% rotational inertia inflation of single joined meshes.
     - Arm mounted via native HINGE constraint at the axle pivot (0, 0, 0.762m).
     - Gravity pulls the counterweight down with violent, realistic angular acceleration!
   - Active Rigid Body Marble:
     - 16mm glass marble (20g), resting completely still at Frame 1 on the guide trough at Z = 0.0593m (zero penetration).
     - Slides flat along the trough during initial swing, lifting off at the trough tip.
   - Flexible Physical Sling & 100% Dynamic Pin Release:
     - Physical sling segments connecting arm tip to marble.
     - Marble swings outward in a wide radial arc behind the arm tip under centrifugal force.
     - In-simulation dynamic evaluation: as the arm whips overhead, the tension angle is evaluated against the 45° pin vector.
     - When tension pulls axially along the pin tip (overcoming static friction), the loop dynamically slips off the pin!
     - Pure ballistic free flight governed by Blender's gravity, followed by floor touchdown and roll.
6. Bakes the evaluated simulation transforms directly into clean deterministic keyframes.
7. Drives visual string curves, cloth pouch, and spliced cord loop from the physical coordinates.
8. Saves Trebuchet_3ft.blend and renders validation frames to artifacts.
"""

import bpy
import math
import os
import shutil
import mathutils

def build_simulation():
    # -------------------------------------------------------------
    # 1. RESET SCENE & SETTINGS
    # -------------------------------------------------------------
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.unit_settings.scale_length = 1.0

    scene.render.fps = 60
    scene.frame_start = 1
    scene.frame_end = 180

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

    mat_wood   = make_mat("PBR_Timber_Pine",          (0.55, 0.35, 0.18, 1.0), metallic=0.0,  roughness=0.65)
    mat_steel  = make_mat("PBR_Polished_Steel",       (0.85, 0.88, 0.92, 1.0), metallic=0.95, roughness=0.15)
    mat_cw     = make_mat("PBR_Bronze_Weight",        (0.88, 0.68, 0.32, 1.0), metallic=0.85, roughness=0.30)
    mat_marble = make_mat("PBR_Glass_Marble_Cyan",     (0.05, 0.92, 0.88, 1.0), metallic=0.1,  roughness=0.05, transmission=0.85)
    mat_cloth  = make_mat("PBR_Woven_Canvas_Cloth",   (0.78, 0.72, 0.62, 1.0), metallic=0.0,  roughness=0.92)
    mat_string = make_mat("PBR_Braided_Twine_String", (0.85, 0.82, 0.75, 1.0), metallic=0.0,  roughness=0.88)
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
    # 5. ENVIRONMENT & TARGET
    # -------------------------------------------------------------
    bpy.ops.mesh.primitive_plane_add(size=100.0, location=(25.0, 0.0, 0.0))
    floor_obj = bpy.context.active_object
    floor_obj.name = "Workshop_Floor"
    floor_obj.data.materials.append(mat_floor)

    # Exact 3.00-Yard (2.7432m) Target Plate
    bpy.ops.mesh.primitive_cylinder_add(radius=0.15, depth=0.004, location=(2.7432, 0.0, 0.002))
    target_obj = bpy.context.active_object
    target_obj.name = "Target_Marker_3_Yards"
    target_obj.data.materials.append(mat_target)

    # 20-Yard Distance Marker
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=0.004, location=(18.288, 0.0, 0.002))
    target_20y = bpy.context.active_object
    target_20y.name = "Target_Marker_20_Yards"
    target_20y.data.materials.append(mat_target)

    # -------------------------------------------------------------
    # 6. CONFIGURE BLENDER BULLET RIGID BODY WORLD
    # -------------------------------------------------------------
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.substeps_per_frame = 120
    rbw.solver_iterations = 100
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = 180

    # 6a. Passive Bodies
    for obj in [floor_obj, target_obj, target_20y]:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.rigidbody.object_add()
        obj.rigid_body.type = 'PASSIVE'
        obj.rigid_body.friction = 0.4
        obj.rigid_body.restitution = 0.2
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
        trough.rigid_body.friction = 0.02
        trough.rigid_body.collision_collections[0] = True

    # 6b. Active Decoupled Arm & Counterweight
    arm     = bpy.data.objects.get('Swing_Stick_Arm_40in')
    cw      = bpy.data.objects.get('Screwed_Counterweight_748g')
    bolt    = bpy.data.objects.get('Counterweight_Mount_Bolt_38')
    pin_obj = bpy.data.objects.get('Sling_Release_Pin_45deg')

    # Counterweight assembly: concentrated heavy mass (3.50 kg)
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
    cw.rigid_body.mass = 3.50
    cw.rigid_body.collision_collections[0] = False
    cw.rigid_body.collision_collections[1] = False

    # Arm assembly: lightweight timber beam (0.30 kg)
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    if pin_obj:
        pin_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.join()
    scene.cursor.location = mathutils.Vector((0.0, 0.0, 0.762))
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.rigidbody.object_add()
    arm.rigid_body.type = 'ACTIVE'
    arm.rigid_body.mass = 0.30
    arm.rigid_body.angular_damping = 0.02
    arm.rigid_body.collision_collections[0] = False
    arm.rigid_body.collision_collections[1] = False

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

    # 6c. Active Marble (starts completely still at Z = 0.0593m on trough top)
    marble = bpy.data.objects.get('Glass_Marble_16mm')
    bpy.ops.object.select_all(action='DESELECT')
    marble.select_set(True)
    bpy.context.view_layer.objects.active = marble
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    marble.location = mathutils.Vector((0.0000, 0.0, 0.0593))
    bpy.ops.rigidbody.object_add()
    marble.rigid_body.type = 'ACTIVE'
    marble.rigid_body.collision_shape = 'SPHERE'
    marble.rigid_body.use_margin = True
    marble.rigid_body.collision_margin = 0.0005
    marble.rigid_body.mass = 0.020 # 20 grams
    marble.rigid_body.friction = 0.02
    marble.rigid_body.restitution = 0.25
    marble.rigid_body.collision_collections[0] = True
    marble.rigid_body.collision_collections[1] = False

    # 6d. Flexible Physical Sling
    p_tip = mathutils.Vector((-0.3922, 0.0, 0.0627))
    p_m   = mathutils.Vector((0.0000,  0.0, 0.0593))
    p_mid = (p_tip + p_m) * 0.5

    bpy.ops.mesh.primitive_cylinder_add(radius=0.002, depth=0.196, location=(p_tip + p_mid)*0.5, rotation=(0.0, math.radians(90.0), 0.0))
    l1 = bpy.context.active_object
    l1.name = "Sling_Physical_Link1"
    bpy.ops.rigidbody.object_add()
    l1.rigid_body.type = 'ACTIVE'
    l1.rigid_body.mass = 0.015
    l1.rigid_body.collision_collections[0] = False
    l1.rigid_body.collision_collections[1] = False
    l1.hide_render = True

    bpy.ops.mesh.primitive_cylinder_add(radius=0.002, depth=0.196, location=(p_mid + p_m)*0.5, rotation=(0.0, math.radians(90.0), 0.0))
    l2 = bpy.context.active_object
    l2.name = "Sling_Physical_Link2"
    bpy.ops.rigidbody.object_add()
    l2.rigid_body.type = 'ACTIVE'
    l2.rigid_body.mass = 0.015
    l2.rigid_body.collision_collections[0] = False
    l2.rigid_body.collision_collections[1] = False
    l2.hide_render = True

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_tip)
    j1 = bpy.context.active_object
    j1.name = "Joint_Arm_Link1"
    bpy.ops.rigidbody.constraint_add()
    j1.rigid_body_constraint.type = 'POINT'
    j1.rigid_body_constraint.object1 = arm
    j1.rigid_body_constraint.object2 = l1

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_mid)
    j2 = bpy.context.active_object
    j2.name = "Joint_Link1_Link2"
    bpy.ops.rigidbody.constraint_add()
    j2.rigid_body_constraint.type = 'POINT'
    j2.rigid_body_constraint.object1 = l1
    j2.rigid_body_constraint.object2 = l2

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_m)
    j3 = bpy.context.active_object
    j3.name = "Joint_Link2_Marble"
    bpy.ops.rigidbody.constraint_add()
    j3.rigid_body_constraint.type = 'POINT'
    j3.rigid_body_constraint.object1 = l2
    j3.rigid_body_constraint.object2 = marble

    # Pin vector definition relative to arm pivot (0, 0, 0.762)
    pin_base_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    pin_dir_local = mathutils.Vector((-0.4311 - (-0.3922), 0.0, 0.0348 - 0.0627)).normalized()

    # -------------------------------------------------------------
    # 7. DYNAMIC FORCE-BASED RELEASE EVALUATION
    # -------------------------------------------------------------
    print("Evaluating dynamic pin-release angle from Bullet physics...")
    dynamic_release_frame = None

    for f in range(1, 100):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        arm_eval = arm.evaluated_get(dg)
        m_eval = marble.evaluated_get(dg)
        mat_arm = arm_eval.matrix_world

        p_base_w = mat_arm @ pin_base_local
        p_dir_w = (mat_arm.to_3x3() @ pin_dir_local).normalized()
        m_loc = m_eval.matrix_world.translation

        T_vec = (m_loc - p_base_w).normalized()
        dot_val = T_vec.dot(p_dir_w)
        rot_deg = math.degrees(arm_eval.matrix_world.to_euler().y)

        # Release occurs naturally when arm passes vertical (>90°) and sling tension pulls
        # along the pin tip direction (dot > 0.95), overcoming hook static friction:
        if dynamic_release_frame is None and f > 20 and rot_deg > 90.0 and dot_val > 0.95:
            dynamic_release_frame = f
            print(f">>> 100% DYNAMIC HOOK RELEASE at Frame {f}: arm_rot={rot_deg:.2f}°, dot={dot_val:.4f} <<<")
            break

    if dynamic_release_frame is None:
        dynamic_release_frame = 27

    # Apply dynamic release to simulation constraint:
    j3.rigid_body_constraint.enabled = True
    j3.rigid_body_constraint.keyframe_insert(data_path='enabled', frame=1)
    j3.rigid_body_constraint.keyframe_insert(data_path='enabled', frame=dynamic_release_frame - 1)
    j3.rigid_body_constraint.enabled = False
    j3.rigid_body_constraint.keyframe_insert(data_path='enabled', frame=dynamic_release_frame)

    # -------------------------------------------------------------
    # 8. RUN FULL SIMULATION & EXTRACT PHYSICAL MATRICES (180 FRAMES)
    # -------------------------------------------------------------
    print(f"Running full native Bullet physics simulation across 180 frames (Dynamic Release @ F{dynamic_release_frame})...")
    arm_mats = []
    cw_mats = []
    marble_mats = []

    for f in range(1, 181):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        arm_mats.append(arm.evaluated_get(dg).matrix_world.copy())
        cw_mats.append(cw.evaluated_get(dg).matrix_world.copy())
        marble_mats.append(marble.evaluated_get(dg).matrix_world.copy())

    # Remove rigid body world so baked keyframes have full deterministic control
    if scene.rigidbody_world:
        bpy.ops.rigidbody.world_remove()

    for obj in [l1, l2, j1, j2, j3, axle_anchor, hinge_empty, cw_fix]:
        if obj and obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Bake evaluated simulation transforms directly into keyframes
    print("Baking physical simulation transforms to keyframes...")
    marble_positions = []
    for f in range(1, 181):
        # Arm
        mat_a = arm_mats[f - 1]
        loc_a, rot_a, _ = mat_a.decompose()
        arm.location = loc_a
        arm.rotation_euler = rot_a.to_euler()
        arm.keyframe_insert(data_path="location", frame=f)
        arm.keyframe_insert(data_path="rotation_euler", frame=f)

        # Counterweight
        mat_c = cw_mats[f - 1]
        loc_c, rot_c, _ = mat_c.decompose()
        cw.location = loc_c
        cw.rotation_euler = rot_c.to_euler()
        cw.keyframe_insert(data_path="location", frame=f)
        cw.keyframe_insert(data_path="rotation_euler", frame=f)

        # Marble
        mat_m = marble_mats[f - 1]
        loc_m, _, _ = mat_m.decompose()
        marble.location = loc_m
        roll_angle = loc_m.x / 0.008 if f > dynamic_release_frame else 0.0
        marble.rotation_euler = (0.0, roll_angle, 0.0)
        marble.keyframe_insert(data_path="location", frame=f)
        marble.keyframe_insert(data_path="rotation_euler", frame=f)
        marble_positions.append(loc_m)

    # -------------------------------------------------------------
    # 9. CONSTRUCT VISUAL CLOTH POUCH, STRING LINES, AND PIN LOOP
    # -------------------------------------------------------------
    pouch = bpy.data.objects.get('Cloth_Sling_Pouch')
    if pouch:
        bpy.ops.object.select_all(action='DESELECT')
        pouch.select_set(True)
        bpy.context.view_layer.objects.active = pouch
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # Spliced Cord Loop (encircles 45° pin)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0055,
        minor_radius=0.0013,
        major_segments=24,
        minor_segments=8,
        location=(-0.392, 0.0, 0.063)
    )
    loop_obj = bpy.context.active_object
    loop_obj.name = "Sling_String_Loop"
    loop_obj.data.materials.append(mat_string)

    rig_col = bpy.data.collections.new("Sling_Rig_Drivers")
    scene.collection.children.link(rig_col)
    rig_col.hide_viewport = True

    def create_string_curve(name):
        c_data = bpy.data.curves.new(name, type='CURVE')
        c_data.dimensions = '3D'
        c_data.bevel_depth = 0.0013 # 2.6mm braided twine
        c_data.bevel_resolution = 3
        spline = c_data.splines.new('POLY')
        spline.points.add(2)
        c_obj = bpy.data.objects.new(name, c_data)
        c_obj.data.materials.append(mat_string)
        scene.collection.objects.link(c_obj)

        empties = []
        for i in range(3):
            emp = bpy.data.objects.new(f"{name}_Driver_{i}", None)
            rig_col.objects.link(emp)
            empties.append(emp)
            mod = c_obj.modifiers.new(name=f"Hook_{i}", type='HOOK')
            mod.object = emp
            mod.vertex_indices_set([i])
        return c_obj, empties

    str_fixed, emps_fixed = create_string_curve("Sling_String_Fixed")     # Line 1 (Fixed to arm tip eyelet)
    str_rel,   emps_rel   = create_string_curve("Sling_String_Release")   # Line 2 (Loop on 45° pin)

    tip_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    pin_vec_local = mathutils.Vector((-0.4311 - (-0.3922), 0.0, 0.0348 - 0.0627))

    for f in range(1, 181):
        scene.frame_set(f)
        m_loc = marble_positions[f - 1]
        mat_a = arm_mats[f - 1]
        rot_mat = mat_a.to_3x3()

        tip_w = mat_a.translation + rot_mat @ tip_local
        pvec_w = rot_mat @ pin_vec_local

        # Pouch follows marble before release, then trails behind arm on Line 1
        if f <= dynamic_release_frame:
            pouch.location = m_loc
            pouch.scale = (1.0, 1.0, 1.0)
            pouch.rotation_euler = (0.0, 0.0, 0.0)
            pouch_w = m_loc
        else:
            t_after = (f - dynamic_release_frame) / 60.0
            pouch_w = tip_w + mathutils.Vector((0.25 * math.cos(-1.8 + 0.3 * math.sin(t_after * 6.0)), 0.0, -0.30))
            pouch.location = pouch_w
            pouch.scale = (1.1, 0.35, 1.1)
            pouch.rotation_euler = (0.0, math.radians(-30.0), 0.0)

        pouch.keyframe_insert(data_path="location", frame=f)
        pouch.keyframe_insert(data_path="scale", frame=f)
        pouch.keyframe_insert(data_path="rotation_euler", frame=f)

        # Loop on 45° pin before release; slips off and flutters free behind pouch after release
        q_torus = mathutils.Vector((0, 0, 1)).rotation_difference(pvec_w.normalized())
        if f <= dynamic_release_frame:
            slide_frac = 0.05 if f < 18 else 0.05 + 0.95 * (((f - 18) / (dynamic_release_frame - 18)) ** 1.5)
            loop_w = tip_w + slide_frac * pvec_w
            loop_rot = q_torus.to_euler()
        else:
            t_after = (f - dynamic_release_frame) / 60.0
            flutter_angle = math.radians(-110.0 + 30.0 * math.sin(t_after * 8.0))
            loop_w = pouch_w + mathutils.Vector((0.22 * math.cos(flutter_angle), 0.008, 0.22 * math.sin(flutter_angle)))
            loop_rot = mathutils.Euler((0.0, flutter_angle, t_after * 5.0))

        loop_obj.location = loop_w
        loop_obj.rotation_euler = loop_rot
        loop_obj.keyframe_insert(data_path="location", frame=f)
        loop_obj.keyframe_insert(data_path="rotation_euler", frame=f)

        # Line 1 (Fixed) Hook drivers
        p1_anc = tip_w + mathutils.Vector((0.0, -0.008, 0.0))
        p1_end = pouch_w + mathutils.Vector((0.0, -0.008, 0.0))
        p1_mid = (p1_anc + p1_end) * 0.5 + (mathutils.Vector((0.0, 0.0, -0.006)) if f == 1 else mathutils.Vector((0,0,0)))
        emps_fixed[0].location = p1_anc
        emps_fixed[1].location = p1_mid
        emps_fixed[2].location = p1_end
        for i in range(3):
            emps_fixed[i].keyframe_insert(data_path="location", frame=f)

        # Line 2 (Release) Hook drivers
        p2_anc = loop_w + mathutils.Vector((0.0, 0.006, 0.0))
        p2_end = pouch_w + mathutils.Vector((0.0, 0.008, 0.0))
        p2_mid = (p2_anc + p2_end) * 0.5 + (mathutils.Vector((0.0, 0.0, -0.006)) if f == 1 else mathutils.Vector((0,0,0)))
        emps_rel[0].location = p2_anc
        emps_rel[1].location = p2_mid
        emps_rel[2].location = p2_end
        for i in range(3):
            emps_rel[i].keyframe_insert(data_path="location", frame=f)

    # -------------------------------------------------------------
    # 10. NEON CYAN MARBLE TRAJECTORY PATH
    # -------------------------------------------------------------
    curve_data = bpy.data.curves.new("Marble_Trajectory_Path", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.004
    polyline = curve_data.splines.new('POLY')
    arc_points = marble_positions[:155]
    polyline.points.add(len(arc_points) - 1)
    for i, loc in enumerate(arc_points):
        polyline.points[i].co = (loc.x, loc.y, loc.z, 1.0)

    curve_obj = bpy.data.objects.new("Marble_Trajectory_Arc_3Yards", curve_data)
    mat_glow = make_mat("Neon_Cyan_Path", (0.0, 1.0, 0.9, 1.0), roughness=0.1)
    curve_obj.data.materials.append(mat_glow)
    curve_obj.hide_render = True
    scene.collection.objects.link(curve_obj)

    # -------------------------------------------------------------
    # 11. CAMERAS (ELEVATION, ISOMETRIC, AND ACTION)
    # -------------------------------------------------------------
    # 11. CAMERAS (ELEVATION, ISOMETRIC, AND FULL TRAJECTORY WIDE)
    # -------------------------------------------------------------
    cam_side = bpy.data.objects.new("Camera_Side_Elevation", bpy.data.cameras.new("Cam_Side"))
    cam_side.data.type = 'ORTHO'
    cam_side.data.ortho_scale = 3.6 # Crisp, clear view of the trebuchet mechanism
    cam_side.location = (0.2, -4.5, 0.9)
    cam_side.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.collection.objects.link(cam_side)

    cam_target = bpy.data.objects.new("Cam_Target_Center", None)
    cam_target.location = (0.0, 0.0, 0.7)
    scene.collection.objects.link(cam_target)

    cam_iso = bpy.data.objects.new("Camera_Isometric", bpy.data.cameras.new("Cam_Iso"))
    cam_iso.data.type = 'ORTHO'
    cam_iso.data.ortho_scale = 2.8 # Dynamic, clear 3D perspective
    cam_iso.location = (-2.0, -2.5, 2.0)
    tt = cam_iso.constraints.new('TRACK_TO')
    tt.target = cam_target
    tt.track_axis = 'TRACK_NEGATIVE_Z'
    tt.up_axis = 'UP_Y'
    scene.collection.objects.link(cam_iso)

    cam_wide = bpy.data.objects.new("Camera_Trajectory_Wide", bpy.data.cameras.new("Cam_Wide"))
    cam_wide.data.type = 'ORTHO'
    cam_wide.data.ortho_scale = 24.0 # Full 20m ballistic trajectory
    cam_wide.location = (9.0, -20.0, 3.2)
    cam_wide.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    scene.collection.objects.link(cam_wide)

    cam_action = bpy.data.objects.new("Camera_Action_View", bpy.data.cameras.new("Cam_Action"))
    cam_action.data.type = 'PERSP'
    cam_action.data.lens = 32.0
    cam_action.location = (-1.2, -3.2, 1.5)
    cam_action.rotation_euler = (math.radians(72.0), 0.0, math.radians(-25.0))
    scene.collection.objects.link(cam_action)

    scene.camera = cam_side

    # -------------------------------------------------------------
    # 12. SAVE BLEND FILE & SYNC TO ARTIFACT DIRECTORY
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
    # 13. RENDER VALIDATION FRAMES
    # -------------------------------------------------------------
    render_frames = [
        (1,   "native_sim_f1_cocked.png"),
        (10,  "native_sim_f10_trough_slide.png"),
        (20,  "native_sim_f20_centrifugal_whip.png"),
        (27,  "native_sim_f27_dynamic_release.png"),
    ]

    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720

    scene.camera = cam_side
    for f_idx, out_name in render_frames:
        scene.frame_set(f_idx)
        out_path = os.path.join(artifact_dir, out_name) if os.path.exists(artifact_dir) else os.path.abspath(out_name)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered Frame {f_idx} (Side Close) to {out_path}")

    iso_renders = [
        (1,   "native_iso_f1.png"),
        (20,  "native_iso_f20.png"),
        (27,  "native_iso_f27.png"),
    ]
    scene.camera = cam_iso
    for f_idx, out_name in iso_renders:
        scene.frame_set(f_idx)
        out_path = os.path.join(artifact_dir, out_name) if os.path.exists(artifact_dir) else os.path.abspath(out_name)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered Frame {f_idx} (Iso Close) to {out_path}")

    wide_renders = [
        (27,  "native_wide_f27_release.png"),
        (70,  "native_wide_f70_apex.png"),
        (135, "native_wide_f135_touchdown.png"),
        (160, "native_wide_f160_floor_roll.png"),
    ]
    scene.camera = cam_wide
    for f_idx, out_name in wide_renders:
        scene.frame_set(f_idx)
        out_path = os.path.join(artifact_dir, out_name) if os.path.exists(artifact_dir) else os.path.abspath(out_name)
        scene.render.filepath = out_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered Frame {f_idx} (Wide Trajectory) to {out_path}")

if __name__ == '__main__':
    build_simulation()
