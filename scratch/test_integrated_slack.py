import sys
sys.path.insert(0, '/home/steve/src/trebuchet')
sys.path.insert(0, '/home/steve/src/trebuchet/scratch')

import bpy, math, mathutils, time
from slack_geometry import generate_slack_sling_path

# Let's write the complete sim builder test with slack curve
def test_sim_with_slack(marble_x=-0.035, slack_m=0.020):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    
    bpy.ops.wm.obj_import(filepath='/home/steve/src/trebuchet/Trebuchet_3ft.obj', forward_axis='Y', up_axis='Z')
    
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.time_scale = 1.0
    rbw.substeps_per_frame = 20
    rbw.solver_iterations = 50
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = 60

    floor_obj = bpy.data.objects.get('Workshop_Floor')
    trough = bpy.data.objects.get('Marble_Guide_Trough')
    
    # Floor
    bpy.ops.mesh.primitive_plane_add(size=200.0, location=(50.0, 0.0, 0.0))
    floor_obj = bpy.context.active_object
    bpy.ops.rigidbody.object_add()
    floor_obj.rigid_body.type = 'PASSIVE'
    floor_obj.rigid_body.friction = 0.35
    floor_obj.rigid_body.collision_collections[0] = True
    
    # Trough
    trough = bpy.data.objects.get('Marble_Guide_Trough')
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
    trough.rigid_body.friction = 0.16
    trough.rigid_body.collision_collections[0] = True

    # CW
    cw = bpy.data.objects.get('Screwed_Counterweight_748g')
    bolt = bpy.data.objects.get('Counterweight_Mount_Bolt_38')
    bpy.ops.object.select_all(action='DESELECT')
    cw.select_set(True)
    bolt.select_set(True)
    bpy.context.view_layer.objects.active = cw
    bpy.ops.object.join()
    cw.name = "Counterweight_Assembly"
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bpy.ops.rigidbody.object_add()
    cw.rigid_body.type = 'ACTIVE'
    cw.rigid_body.mass = 2.00
    cw.rigid_body.linear_damping = 0.03
    cw.rigid_body.angular_damping = 0.04
    cw.rigid_body.collision_collections[0] = False
    cw.rigid_body.collision_collections[1] = False

    # Arm & Pin
    arm = bpy.data.objects.get('Swing_Stick_Arm_40in')
    pin_obj = bpy.data.objects.get('Sling_Release_Pin_45deg')
    p_tip = mathutils.Vector((-0.3922, 0.0, 0.0627))
    pivot_w = mathutils.Vector((0.0, 0.0, 0.762))
    arm_axis_w = (p_tip - pivot_w).normalized()
    p_pin_ref = mathutils.Vector((-0.4311, 0.0, 0.0348))
    pin_vec_ref = p_pin_ref - p_tip
    pin_len = pin_vec_ref.length
    pin_dir_ref = pin_vec_ref.normalized()
    comp_along = pin_dir_ref.dot(arm_axis_w)
    norm_w = (pin_dir_ref - comp_along * arm_axis_w).normalized()
    rad = math.radians(10.0)
    pin_dir = (math.cos(rad) * arm_axis_w + math.sin(rad) * norm_w).normalized()
    p_pin_tip = p_tip + pin_len * pin_dir

    if pin_obj:
        bpy.data.objects.remove(pin_obj, do_unlink=True)
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.00238, depth=pin_len,
        location=p_tip + 0.5 * pin_len * pin_dir,
        rotation=mathutils.Vector((0, 0, 1)).rotation_difference(pin_dir).to_euler()
    )
    pin_obj = bpy.context.active_object
    pin_obj.name = "Sling_Release_Pin"

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
    hinge_empty.rigid_body_constraint.type = 'HINGE'
    hinge_empty.rigid_body_constraint.object1 = axle_anchor
    hinge_empty.rigid_body_constraint.object2 = arm
    hinge_empty.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    hinge_empty.rigid_body_constraint.disable_collisions = True

    # CW Fixed
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=cw.location)
    cw_fix = bpy.context.active_object
    bpy.ops.rigidbody.constraint_add()
    cw_fix.rigid_body_constraint.type = 'FIXED'
    cw_fix.rigid_body_constraint.object1 = arm
    cw_fix.rigid_body_constraint.object2 = cw
    cw_fix.rigid_body_constraint.disable_collisions = True

    # Marble at marble_x
    marble = bpy.data.objects.get('Glass_Marble_16mm')
    bpy.ops.object.select_all(action='DESELECT')
    marble.select_set(True)
    bpy.context.view_layer.objects.active = marble
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    marble.location = mathutils.Vector((marble_x, 0.0, 0.0593))
    bpy.ops.rigidbody.object_add()
    marble.rigid_body.type = 'ACTIVE'
    marble.rigid_body.collision_shape = 'SPHERE'
    marble.rigid_body.mass = 0.020
    marble.rigid_body.friction = 0.35
    marble.rigid_body.linear_damping = 0.08
    marble.rigid_body.angular_damping = 0.30
    marble.rigid_body.restitution = 0.25
    marble.rigid_body.collision_collections[0] = True
    marble.rigid_body.collision_collections[1] = False

    # Pouch at marble_x
    p_pouch = mathutils.Vector((marble_x, 0.0, 0.0593))
    pouch = bpy.data.objects.get('Cloth_Sling_Pouch')
    bpy.ops.object.select_all(action='DESELECT')
    pouch.select_set(True)
    bpy.context.view_layer.objects.active = pouch
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    pouch.location = p_pouch
    bpy.ops.rigidbody.object_add()
    pouch.rigid_body.type = 'ACTIVE'
    pouch.rigid_body.collision_shape = 'CONVEX_HULL'
    pouch.rigid_body.friction = 0.45
    pouch.rigid_body.restitution = 0.20
    pouch.rigid_body.mass = 0.010
    pouch.rigid_body.linear_damping = 0.70
    pouch.rigid_body.angular_damping = 0.70
    pouch.rigid_body.collision_collections[0] = False
    pouch.rigid_body.collision_collections[1] = True

    # Physical Loop
    q_torus = mathutils.Vector((0, 0, 1)).rotation_difference(pin_dir)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0055, minor_radius=0.0013,
        major_segments=24, minor_segments=8,
        location=p_tip, rotation=q_torus.to_euler()
    )
    loop_obj = bpy.context.active_object
    loop_obj.name = "Sling_String_Loop"
    bpy.ops.rigidbody.object_add()
    loop_obj.rigid_body.type = 'ACTIVE'
    loop_obj.rigid_body.mass = 0.003
    loop_obj.rigid_body.collision_shape = 'CONVEX_HULL'
    loop_obj.rigid_body.collision_margin = 0.0005
    loop_obj.rigid_body.linear_damping = 0.25
    loop_obj.rigid_body.angular_damping = 0.25
    loop_obj.rigid_body.collision_collections[0] = False
    loop_obj.rigid_body.collision_collections[1] = True

    # Slider constraint
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

    # Multi-Segment Chains with SLACK
    num_segments = 16
    # Line 1: from p_tip + (0, -0.008, 0) to p_pouch + (0, -0.008, 0)
    p1_start = p_tip + mathutils.Vector((0.0, -0.008, 0.0))
    p1_end   = p_pouch + mathutils.Vector((0.0, -0.008, 0.0))
    path1 = generate_slack_sling_path(p1_start, p1_end, num_segments, slack_m=slack_m, n_waves=2)

    # Line 2: from p_tip + (0, 0.008, 0) to p_pouch + (0, 0.008, 0)
    p2_start = p_tip + mathutils.Vector((0.0, 0.008, 0.0))
    p2_end   = p_pouch + mathutils.Vector((0.0, 0.008, 0.0))
    path2 = generate_slack_sling_path(p2_start, p2_end, num_segments, slack_m=slack_m, n_waves=2)

    seg_mass_kg = 0.004 / (2 * num_segments)
    
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

    # Build Line 1
    line1_segs = []
    for i in range(num_segments):
        mid = path1['seg_centers'][i]
        rot = path1['seg_rotations'][i]
        slen = path1['seg_len']
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0013, depth=slen, location=mid, rotation=rot)
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
        s1.rigid_body.linear_damping = 0.35
        s1.rigid_body.angular_damping = 0.45
        s1.rigid_body.collision_collections[0] = False
        s1.rigid_body.collision_collections[1] = True
        line1_segs.append(s1)

    create_sling_joint("Joint_Arm_Line1_0", arm, line1_segs[0], path1['joint_locs'][0])
    for i in range(1, num_segments):
        create_sling_joint(f"Joint_Line1_{i-1}_{i}", line1_segs[i-1], line1_segs[i], path1['joint_locs'][i])
    create_sling_joint("Joint_Line1_Pouch", line1_segs[-1], pouch, path1['joint_locs'][-1])

    # Build Line 2
    line2_segs = []
    for i in range(num_segments):
        mid = path2['seg_centers'][i]
        rot = path2['seg_rotations'][i]
        slen = path2['seg_len']
        bpy.ops.mesh.primitive_cylinder_add(radius=0.0013, depth=slen, location=mid, rotation=rot)
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
        s2.rigid_body.linear_damping = 0.35
        s2.rigid_body.angular_damping = 0.45
        s2.rigid_body.collision_collections[0] = False
        s2.rigid_body.collision_collections[1] = True
        line2_segs.append(s2)

    create_sling_joint("Joint_Loop_Line2_0", loop_obj, line2_segs[0], path2['joint_locs'][0])
    for i in range(1, num_segments):
        create_sling_joint(f"Joint_Line2_{i-1}_{i}", line2_segs[i-1], line2_segs[i], path2['joint_locs'][i])
    create_sling_joint("Joint_Line2_Pouch", line2_segs[-1], pouch, path2['joint_locs'][-1])

    # Joint M
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_pouch)
    jm = bpy.context.active_object
    bpy.ops.rigidbody.constraint_add()
    jm.rigid_body_constraint.type = 'POINT'
    jm.rigid_body_constraint.object1 = pouch
    jm.rigid_body_constraint.object2 = marble

    # Dynamic release setup
    pin_base_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    pin_dir_local = pin_dir.copy()

    tip_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    print(f"\n=======================================================")
    print(f"Results for marble_x={marble_x:.3f} m, slack={slack_m*1000:.1f} mm")
    print(f"=======================================================")
    print("Frame | Arm Tip (m/s) | Loop Dist from Tip | Marble X | Marble Vx (m/s) | Status")
    
    prev_m_x = None
    prev_tip = None
    released = False
    
    for f in range(1, 45):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        tip_w = arm.evaluated_get(dg).matrix_world @ tip_local
        loop_w = loop_obj.evaluated_get(dg).matrix_world.translation
        m_w = marble.evaluated_get(dg).matrix_world.translation
        
        loop_dist = (loop_w - tip_w).length * 1000.0
        m_vx = (m_w.x - prev_m_x) * 60.0 if prev_m_x is not None else 0.0
        tip_vx = (tip_w - prev_tip).length * 60.0 if prev_tip is not None else 0.0
        prev_m_x = m_w.x
        prev_tip = tip_w.copy()
        
        # Dynamic release check
        arm_eval = arm.evaluated_get(dg)
        mat_arm = arm_eval.matrix_world
        p_base_w = mat_arm @ pin_base_local
        p_dir_w = (mat_arm.to_3x3() @ pin_dir_local).normalized()
        T_vec = (m_w - p_base_w).normalized()
        dot_val = T_vec.dot(p_dir_w)
        rot_deg = math.degrees(arm_eval.matrix_world.to_euler().y)
        
        if not released and f > 15:
            if rot_deg > 85.0 and dot_val > 0.80:
                released = True
                sc.enabled = False
                jm.rigid_body_constraint.enabled = False
                print(f"  >>> Dynamic Release at Frame {f} (arm={rot_deg:.1f}°, dot={dot_val:.4f}, marble_vx={m_vx:.2f} m/s) <<<")
        
        if f <= 15 or f in [20, 25, 30, 31, 32, 33, 34, 35, 40]:
            pin_status = "SAFE (at base)" if loop_dist < 10.0 else ("MID PIN" if loop_dist < 35.0 else "DANGER (near tip!)")
            print(f"{f:5d} | {tip_vx:11.2f} | {loop_dist:16.2f} mm | {m_w.x:8.3f} | {m_vx:13.2f} | {pin_status}")

if __name__ == '__main__':
    # Test marble moved by 35mm with 15mm slack
    test_sim_with_slack(marble_x=-0.035, slack_m=0.015)
