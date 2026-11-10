import bpy
import math
import mathutils
import time

def test_pin_angle(pin_angle_deg):
    # Set up scene
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 60
    
    # Reset
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.frame_start = 1
    scene.frame_end = 60
    
    # Import OBJ
    obj_path = "/home/steve/src/trebuchet/Trebuchet_3ft.obj"
    bpy.ops.wm.obj_import(filepath=obj_path, forward_axis='Y', up_axis='Z')
    
    # Configure Rigid Body World
    bpy.ops.rigidbody.world_add()
    rbw = scene.rigidbody_world
    rbw.time_scale = 1.0
    rbw.substeps_per_frame = 20 # 1200 FPS
    rbw.solver_iterations = 40
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
    bpy.context.view_layer.objects.active = cw
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

    # Marble
    marble = bpy.data.objects.get('Glass_Marble_16mm')
    bpy.ops.object.select_all(action='DESELECT')
    marble.select_set(True)
    bpy.context.view_layer.objects.active = marble
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bpy.ops.rigidbody.object_add()
    marble.rigid_body.type = 'ACTIVE'
    marble.rigid_body.collision_shape = 'SPHERE'
    marble.rigid_body.mass = 0.020
    marble.rigid_body.friction = 0.12
    marble.rigid_body.restitution = 0.25
    marble.rigid_body.linear_damping = 0.08
    marble.rigid_body.angular_damping = 0.30
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
    pouch.rigid_body.friction = 0.45
    pouch.rigid_body.restitution = 0.20
    pouch.rigid_body.mass = 0.010
    pouch.rigid_body.linear_damping = 0.70
    pouch.rigid_body.angular_damping = 0.70
    pouch.rigid_body.collision_collections[0] = False
    pouch.rigid_body.collision_collections[1] = True

    # Articulated rope segments (16)
    num_segments = 16
    line_vec = p_pouch - p_tip
    L_total = line_vec.length
    seg_len = L_total / num_segments
    seg_mass_kg = 0.004 / (2 * num_segments)
    
    line1_segs, line2_segs = [], []
    for i in range(num_segments):
        frac_mid = (i + 0.5) / num_segments
        p_seg = p_tip + frac_mid * line_vec
        for seg_list, coll_layer in [(line1_segs, 1), (line2_segs, 1)]:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=0.001, depth=seg_len,
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

    # Compute pin direction based on pin_angle_deg relative to arm axis
    # Arm vector from pivot (0,0,0.762) to tip:
    pivot_w = mathutils.Vector((0.0, 0.0, 0.762))
    arm_axis_w = (p_tip - pivot_w).normalized()
    fwd_w = mathutils.Vector((-arm_axis_w.z, 0.0, arm_axis_w.x))
    if fwd_w.x < 0: fwd_w = -fwd_w
    
    # pin_angle_deg < 0 means tilted backward
    rad = math.radians(pin_angle_deg)
    pin_dir = (math.cos(rad) * arm_axis_w + math.sin(rad) * fwd_w).normalized()
    pin_len = 0.04787
    p_pin_tip = p_tip + pin_len * pin_dir

    # Physical Loop
    q_torus = mathutils.Vector((0, 0, 1)).rotation_difference(pin_dir)
    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.0055, minor_radius=0.0013,
        major_segments=24, minor_segments=8,
        location=p_tip, rotation=q_torus.to_euler()
    )
    loop_obj = bpy.context.active_object
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

    # Slider constraint along pin_dir
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_tip)
    slider_emp = bpy.context.active_object
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

    # Connect Line 1 (Arm Tip -> Line1 -> Pouch)
    create_sling_joint("Joint_Arm_Line1_0", arm, line1_segs[0], p_tip)
    for i in range(1, num_segments):
        create_sling_joint(f"Joint_Line1_{i-1}_{i}", line1_segs[i-1], line1_segs[i], p_tip + (i/num_segments)*line_vec)
    create_sling_joint("Joint_Line1_Pouch", line1_segs[-1], pouch, p_pouch)

    # Connect Line 2 (Loop -> Line2 -> Pouch)
    create_sling_joint("Joint_Loop_Line2_0", loop_obj, line2_segs[0], p_tip)
    for i in range(1, num_segments):
        create_sling_joint(f"Joint_Line2_{i-1}_{i}", line2_segs[i-1], line2_segs[i], p_tip + (i/num_segments)*line_vec)
    create_sling_joint("Joint_Line2_Pouch", line2_segs[-1], pouch, p_pouch)

    # Joint M
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=p_pouch)
    jm = bpy.context.active_object
    bpy.ops.rigidbody.constraint_add()
    jm.rigid_body_constraint.type = 'POINT'
    jm.rigid_body_constraint.object1 = pouch
    jm.rigid_body_constraint.object2 = marble

    # Local pin coordinates
    pin_base_local = mathutils.Vector((-0.3922, 0.0, 0.0627 - 0.762))
    # In arm local space:
    pin_dir_local = pin_dir # at frame 1, arm is at rest

    # Step simulation
    released = False
    release_info = None

    prev_marble_pos = None
    for f in range(1, 60):
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
        if f >= 25 and f <= 40:
            print(f"  f={f:2d}: rot={rot_deg:6.1f}°, dot={dot_val:6.3f}")

        if not released and f > 15:
            if rot_deg > 85.0 and dot_val > 0.80:
                released = True
                sc.enabled = False
                jm.rigid_body_constraint.enabled = False
                
                # velocity
                if prev_marble_pos:
                    vx = (m_loc.x - prev_marble_pos.x) * 60.0
                    vz = (m_loc.z - prev_marble_pos.z) * 60.0
                    spd = math.hypot(vx, vz)
                    launch_ang = math.degrees(math.atan2(vz, vx))
                else:
                    spd, launch_ang = 0, 0
                release_info = {
                    'frame': f,
                    'arm_rot': rot_deg,
                    'dot': dot_val,
                    'speed': spd,
                    'launch_angle': launch_ang,
                    'x': m_loc.x,
                    'z': m_loc.z
                }
                print(f"RELEASE at Frame {f}: arm_rot={rot_deg:.1f}°, dot={dot_val:.4f}, spd={spd:.2f} m/s, ang={launch_ang:.1f}°, pos=({m_loc.x:.2f}, {m_loc.z:.2f})")
        
        prev_marble_pos = m_loc.copy()
        
    return release_info

print("Testing angle variations:")
for ang in [-25.07, -20.0, -15.0, -12.0, -10.0]:
    print(f"\n--- Testing Angle {ang:+.2f}° ---")
    info = test_pin_angle(ang)
    print(f"Result for {ang}°: {info}")
