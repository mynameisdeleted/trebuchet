#!/usr/bin/env python3
import bpy
import math
import os
import mathutils
import time

def test():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'METERS'
    scene.render.fps = 60
    TOTAL_FRAMES = 180

    # Import OBJ
    obj_path = os.path.abspath("Trebuchet_3ft.obj")
    bpy.ops.wm.obj_import(filepath=obj_path, up_axis='Z', forward_axis='Y')
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.scale = (0.001, 0.001, 0.001)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    old_lace = bpy.data.objects.get('Leather_ShoeLace_Sling_15_5in')
    if old_lace:
        bpy.data.objects.remove(old_lace, do_unlink=True)

    # Floor & Trough
    bpy.ops.mesh.primitive_plane_add(size=100.0, location=(0.0, 0.0, 0.0))
    floor_obj = bpy.context.active_object
    bpy.ops.rigidbody.world_add()
    world = scene.rigidbody_world
    world.substeps_per_frame = 20
    world.solver_iterations = 50

    bpy.ops.rigidbody.object_add()
    floor_obj.rigid_body.type = 'PASSIVE'
    floor_obj.rigid_body.friction = 0.35
    floor_obj.rigid_body.collision_collections[0] = True

    trough = bpy.data.objects.get('Marble_Guide_Trough')
    if trough:
        bpy.ops.object.select_all(action='DESELECT')
        trough.select_set(True)
        bpy.context.view_layer.objects.active = trough
        bpy.ops.rigidbody.object_add()
        trough.rigid_body.type = 'PASSIVE'
        trough.rigid_body.collision_shape = 'CONVEX_HULL'
        trough.rigid_body.use_margin = True
        trough.rigid_body.collision_margin = 0.0005
        trough.rigid_body.friction = 0.16
        trough.rigid_body.collision_collections[0] = True

    # Arm & CW
    arm = bpy.data.objects.get('Swing_Stick_Arm_40in')
    cw = bpy.data.objects.get('Screwed_Counterweight_748g')
    bolt = bpy.data.objects.get('Counterweight_Mount_Bolt_38')
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
    cw.rigid_body.mass = 2.0
    cw.rigid_body.linear_damping = 0.03
    cw.rigid_body.angular_damping = 0.04
    cw.rigid_body.collision_collections[0] = False
    cw.rigid_body.collision_collections[1] = False

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
    arm.rigid_body.collision_shape = 'CONVEX_HULL'
    arm.rigid_body.use_margin = True
    arm.rigid_body.collision_margin = 0.001
    arm.rigid_body.friction = 0.40
    arm.rigid_body.restitution = 0.25
    arm.rigid_body.mass = 0.30
    arm.rigid_body.linear_damping = 0.04
    arm.rigid_body.angular_damping = 0.06
    arm.rigid_body.collision_collections[0] = False
    arm.rigid_body.collision_collections[1] = True

    # Axle
    bpy.ops.mesh.primitive_cube_add(size=0.01, location=(0.0, 0.0, 0.762))
    axle_anchor = bpy.context.active_object
    bpy.ops.rigidbody.object_add()
    axle_anchor.rigid_body.type = 'PASSIVE'
    axle_anchor.rigid_body.collision_collections[0] = False
    axle_anchor.rigid_body.collision_collections[1] = False

    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0.0, 0.0, 0.762))
    hinge_empty = bpy.context.active_object
    bpy.ops.rigidbody.constraint_add()
    con = hinge_empty.rigid_body_constraint
    con.type = 'HINGE'
    con.object1 = axle_anchor
    con.object2 = arm
    con.disable_collisions = True
    hinge_empty.rotation_euler = (math.radians(90.0), 0.0, 0.0)

    # CW fixed to arm
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=cw.location)
    cw_fix = bpy.context.active_object
    bpy.ops.rigidbody.constraint_add()
    cw_fix.rigid_body_constraint.type = 'FIXED'
    cw_fix.rigid_body_constraint.object1 = arm
    cw_fix.rigid_body_constraint.object2 = cw
    cw_fix.rigid_body_constraint.disable_collisions = True

    # Marble
    marble = bpy.data.objects.get('Glass_Marble_16mm')
    bpy.ops.object.select_all(action='DESELECT')
    marble.select_set(True)
    bpy.context.view_layer.objects.active = marble
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    marble.location = mathutils.Vector((0.0, 0.0, 0.0593))
    bpy.ops.rigidbody.object_add()
    marble.rigid_body.type = 'ACTIVE'
    marble.rigid_body.collision_shape = 'SPHERE'
    marble.rigid_body.use_margin = True
    marble.rigid_body.collision_margin = 0.0005
    marble.rigid_body.mass = 0.020
    marble.rigid_body.friction = 0.35
    marble.rigid_body.linear_damping = 0.08
    marble.rigid_body.angular_damping = 0.30
    marble.rigid_body.restitution = 0.25
    marble.rigid_body.collision_collections[0] = True
    marble.rigid_body.collision_collections[1] = False

    # Pouch
    p_tip = mathutils.Vector((-0.3922, 0.0, 0.0627))
    p_pouch = mathutils.Vector((0.0000, 0.0, 0.0593))

    pouch = bpy.data.objects.get('Cloth_Sling_Pouch')
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
    pouch.rigid_body.mass = 0.010
    pouch.rigid_body.linear_damping = 0.70
    pouch.rigid_body.angular_damping = 0.70
    pouch.rigid_body.collision_collections[0] = False
    pouch.rigid_body.collision_collections[1] = True

    # Pin vector
    p_pin_tip = mathutils.Vector((-0.4311, 0.0, 0.0348))
    pin_vec = p_pin_tip - p_tip
    pin_len = pin_vec.length
    pin_dir = pin_vec.normalized()

    # PHYSICAL SLING STRING LOOP (Torus active rigid body on pin)
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
    bpy.ops.rigidbody.object_add()
    loop_obj.rigid_body.type = 'ACTIVE'
    loop_obj.rigid_body.mass = 0.003
    loop_obj.rigid_body.collision_shape = 'CONVEX_HULL'
    loop_obj.rigid_body.use_margin = True
    loop_obj.rigid_body.collision_margin = 0.0005
    loop_obj.rigid_body.linear_damping = 0.25
    loop_obj.rigid_body.angular_damping = 0.25
    loop_obj.rigid_body.collision_collections[0] = False
    loop_obj.rigid_body.collision_collections[1] = True

    # Slider constraint between arm and loop
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

    # Segments
    num_segments = 16
    line_vec = p_pouch - p_tip
    L_total = line_vec.length
    seg_len = L_total / num_segments
    seg_mass_kg = 0.00025
    rot_cyl = (0.0, math.radians(90.0), 0.0)

    line1_segs = []
    line2_segs = []
    line1_joints = []
    line2_joints = []

    for i in range(num_segments):
        frac_mid = (i + 0.5) / num_segments
        p_seg = p_tip + frac_mid * line_vec

        bpy.ops.mesh.primitive_cylinder_add(radius=0.0013, depth=seg_len, location=p_seg, rotation=rot_cyl)
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
        s1.rigid_body.linear_damping = 0.25
        s1.rigid_body.angular_damping = 0.35
        s1.rigid_body.collision_collections[0] = False
        s1.rigid_body.collision_collections[1] = True
        s1.hide_render = True
        line1_segs.append(s1)

        bpy.ops.mesh.primitive_cylinder_add(radius=0.0013, depth=seg_len, location=p_seg, rotation=rot_cyl)
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
        s2.rigid_body.linear_damping = 0.25
        s2.rigid_body.angular_damping = 0.35
        s2.rigid_body.collision_collections[0] = False
        s2.rigid_body.collision_collections[1] = True
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

    # Line 1: Arm Tip -> segs -> Pouch
    j1_0 = create_sling_joint("Joint_Arm_Line1_0", arm, line1_segs[0], p_tip)
    line1_joints.append(j1_0)
    for i in range(1, num_segments):
        loc_i = p_tip + (i / num_segments) * line_vec
        ji = create_sling_joint(f"Joint_Line1_{i-1}_{i}", line1_segs[i-1], line1_segs[i], loc_i)
        line1_joints.append(ji)
    j1_N = create_sling_joint("Joint_Line1_Pouch", line1_segs[-1], pouch, p_pouch)
    line1_joints.append(j1_N)

    # Line 2: LOOP -> seg 0 -> seg 1 ... -> seg N-1 -> Pouch!
    # (Anchor is directly to the physical loop on the pin!)
    j2_loop = create_sling_joint("Joint_Loop_Line2_0", loop_obj, line2_segs[0], p_tip)
    line2_joints.append(j2_loop)
    for i in range(1, num_segments):
        loc_i = p_tip + (i / num_segments) * line_vec
        ji = create_sling_joint(f"Joint_Line2_{i-1}_{i}", line2_segs[i-1], line2_segs[i], loc_i)
        line2_joints.append(ji)
    j2_N = create_sling_joint("Joint_Line2_Pouch", line2_segs[-1], pouch, p_pouch)
    line2_joints.append(j2_N)

    # Pouch <-> Marble
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_pouch)
    jm = bpy.context.active_object
    jm.name = "Joint_Pouch_Marble"
    bpy.ops.rigidbody.constraint_add()
    jm.rigid_body_constraint.type = 'POINT'
    jm.rigid_body_constraint.object1 = pouch
    jm.rigid_body_constraint.object2 = marble

    pin_base_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    pin_dir_local = pin_dir.copy()

    # Step simulation
    released = False
    dynamic_release_frame = 28
    print("Running simulation with physical loop slider...")
    for f in range(1, TOTAL_FRAMES + 1):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()

        if not released and f > 15:
            arm_eval = arm.evaluated_get(dg)
            m_eval = marble.evaluated_get(dg)
            l_eval = loop_obj.evaluated_get(dg)
            mat_arm = arm_eval.matrix_world
            p_base_w = mat_arm @ pin_base_local
            p_dir_w = (mat_arm.to_3x3() @ pin_dir_local).normalized()
            m_loc = m_eval.matrix_world.translation
            l_loc = l_eval.matrix_world.translation

            T_vec = (m_loc - p_base_w).normalized()
            dot_val = T_vec.dot(p_dir_w)
            rot_deg = math.degrees(arm_eval.matrix_world.to_euler().y)
            loop_slide = (l_loc - p_base_w).dot(p_dir_w)

            if rot_deg > 85.0 and dot_val > 0.80:
                released = True
                dynamic_release_frame = f
                sc.enabled = False
                jm.rigid_body_constraint.enabled = False
                print(f">>> RELEASE at Frame {f}: arm_rot={rot_deg:.2f}°, dot={dot_val:.4f}, loop_slide={loop_slide*1000:.1f}mm <<<")

        if f in [1, 15, 20, 25, 28, 29, 30, 60, 90, 150, 180]:
            arm_eval = arm.evaluated_get(dg)
            m_eval = marble.evaluated_get(dg)
            l_eval = loop_obj.evaluated_get(dg)
            s2_0_eval = line2_segs[0].evaluated_get(dg)
            l_pos = l_eval.matrix_world.translation
            s2_pos = s2_0_eval.matrix_world.translation
            m_pos = m_eval.matrix_world.translation
            dist_loop_rope = (l_pos - s2_pos).length
            print(f"F{f:3d}: loop=({l_pos.x:.3f}, {l_pos.z:.3f}), s2_0=({s2_pos.x:.3f}, {s2_pos.z:.3f}), dist={dist_loop_rope*1000:.2f}mm, marble=({m_pos.x:.2f}, {m_pos.z:.2f})")

    print("Test completed successfully!")

if __name__ == '__main__':
    test()
