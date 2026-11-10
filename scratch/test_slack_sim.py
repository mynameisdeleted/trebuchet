import bpy
import math
import mathutils

def run_test(slack_amount_m=0.030, marble_x=-0.040):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    
    # Import OBJ
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
    for o in [floor_obj, trough]:
        if o:
            bpy.ops.object.select_all(action='DESELECT')
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            bpy.ops.rigidbody.object_add()
            o.rigid_body.type = 'PASSIVE'
            o.rigid_body.collision_shape = 'BOX'
            o.rigid_body.friction = 0.16
            o.rigid_body.collision_collections[0] = True
            o.rigid_body.collision_collections[1] = False

    cw = bpy.data.objects.get('Screwed_Counterweight_748g')
    bolt = bpy.data.objects.get('Counterweight_Mount_Bolt_38')
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
    cw.rigid_body.mass = 2.00
    cw.rigid_body.linear_damping = 0.03
    cw.rigid_body.angular_damping = 0.04
    cw.rigid_body.collision_collections[0] = False
    cw.rigid_body.collision_collections[1] = False

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
    
    # Use 10 deg pin angle
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

    # Articulated rope segments (16)
    num_segments = 16
    line_vec = p_pouch - p_tip
    straight_dist = line_vec.length
    # Target rope length with slack:
    L_rope = straight_dist + slack_amount_m
    seg_len = L_rope / num_segments
    seg_mass_kg = 0.004 / (2 * num_segments)
    
    # Place segments along a gentle curve or with slack
    line1_segs, line2_segs = [], []
    line1_joints, line2_joints = [], []
    
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

    # Segments placement along line_vec
    for i in range(num_segments):
        frac_mid = (i + 0.5) / num_segments
        p_seg = p_tip + frac_mid * line_vec
        for seg_list, coll_layer in [(line1_segs, 1), (line2_segs, 1)]:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.0013, depth=seg_len,
                location=p_seg, rotation=(0.0, math.radians(90.0), 0.0)
            )
            s = bpy.context.active_object
            bpy.ops.rigidbody.object_add()
            s.rigid_body.type = 'ACTIVE'
            s.rigid_body.collision_shape = 'CAPSULE'
            s.rigid_body.use_margin = True
            s.rigid_body.collision_margin = 0.0005
            s.rigid_body.friction = 0.40
            s.rigid_body.restitution = 0.20
            s.rigid_body.mass = seg_mass_kg
            s.rigid_body.linear_damping = 0.35
            s.rigid_body.angular_damping = 0.45
            s.rigid_body.collision_collections[0] = False
            s.rigid_body.collision_collections[1] = True
            seg_list.append(s)

    # Line 1 Joints: Arm Tip -> seg 0 -> ... -> Pouch
    # If slack_amount_m > 0, the pouch joint can be a SLIDER or GENERIC_6DOF with linear limit = slack_amount_m!
    j1_0 = create_sling_joint("Joint_Arm_Line1_0", arm, line1_segs[0], p_tip)
    for i in range(1, num_segments):
        loc_i = p_tip + (i / num_segments) * line_vec
        create_sling_joint(f"Joint_Line1_{i-1}_{i}", line1_segs[i-1], line1_segs[i], loc_i)
    
    # Pouch joint with slack option
    if slack_amount_m > 0:
        # Use SLIDER or 6DOF on pouch joint with linear limit = slack_amount_m
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_pouch)
        j1_pouch_emp = bpy.context.active_object
        bpy.ops.rigidbody.constraint_add()
        c_p = j1_pouch_emp.rigid_body_constraint
        c_p.type = 'SLIDER'
        c_p.object1 = line1_segs[-1]
        c_p.object2 = pouch
        # Align slider with -X (so pouch can slide towards -X by slack_amount_m)
        j1_pouch_emp.rotation_euler = (0.0, 0.0, math.pi)
        c_p.use_limit_lin_x = True
        c_p.limit_lin_x_lower = 0.0
        c_p.limit_lin_x_upper = slack_amount_m
        c_p.disable_collisions = True
    else:
        create_sling_joint("Joint_Line1_Pouch", line1_segs[-1], pouch, p_pouch)

    # Line 2 Joints: Loop -> seg 0 -> ... -> Pouch
    create_sling_joint("Joint_Loop_Line2_0", loop_obj, line2_segs[0], p_tip)
    for i in range(1, num_segments):
        loc_i = p_tip + (i / num_segments) * line_vec
        create_sling_joint(f"Joint_Line2_{i-1}_{i}", line2_segs[i-1], line2_segs[i], loc_i)
    
    if slack_amount_m > 0:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_pouch)
        j2_pouch_emp = bpy.context.active_object
        bpy.ops.rigidbody.constraint_add()
        c_p2 = j2_pouch_emp.rigid_body_constraint
        c_p2.type = 'SLIDER'
        c_p2.object1 = line2_segs[-1]
        c_p2.object2 = pouch
        j2_pouch_emp.rotation_euler = (0.0, 0.0, math.pi)
        c_p2.use_limit_lin_x = True
        c_p2.limit_lin_x_lower = 0.0
        c_p2.limit_lin_x_upper = slack_amount_m
        c_p2.disable_collisions = True
    else:
        create_sling_joint("Joint_Line2_Pouch", line2_segs[-1], pouch, p_pouch)

    # Joint M
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_pouch)
    jm = bpy.context.active_object
    bpy.ops.rigidbody.constraint_add()
    jm.rigid_body_constraint.type = 'POINT'
    jm.rigid_body_constraint.object1 = pouch
    jm.rigid_body_constraint.object2 = marble

    # Simulate and monitor frames 1-15
    tip_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    print(f"\n--- Testing marble_x={marble_x:.3f}, slack={slack_amount_m*1000:.1f}mm ---")
    print("Frame | Arm Tip X, Z | Loop Dist from Tip | Marble X | Marble Vx (m/s) | Loop on pin?")
    
    prev_m_x = None
    for f in range(1, 16):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        tip_w = arm.evaluated_get(dg).matrix_world @ tip_local
        loop_w = loop_obj.evaluated_get(dg).matrix_world.translation
        m_w = marble.evaluated_get(dg).matrix_world.translation
        
        loop_dist = (loop_w - tip_w).length * 1000.0
        vx = (m_w.x - prev_m_x) * 60.0 if prev_m_x is not None else 0.0
        prev_m_x = m_w.x
        
        pin_status = "SAFE (near base)" if loop_dist < 20.0 else ("MID PIN" if loop_dist < 40.0 else "DANGER (near tip!)")
        print(f"{f:5d} | ({tip_w.x:6.3f}, {tip_w.z:6.3f}) | {loop_dist:6.2f} mm | {m_w.x:6.3f} | {vx:7.2f} | {pin_status}")

if __name__ == '__main__':
    # Test 1: Baseline (marble_x = 0.0, slack = 0)
    run_test(slack_amount_m=0.0, marble_x=0.0)
    # Test 2: Moving marble closer to arm (marble_x = -0.040, slack = 0)
    run_test(slack_amount_m=0.0, marble_x=-0.040)
    # Test 3: Moving marble closer with linear slack limit (marble_x = -0.040, slack = 25mm)
    run_test(slack_amount_m=0.025, marble_x=-0.040)
